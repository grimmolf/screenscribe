package main

import (
	"bytes"
	"context"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"math"
	"net/http"
	"os"
	"sync"
	"time"
)

// OllamaClient handles communication with Ollama API
type OllamaClient struct {
	BaseURL    string
	HTTPClient *http.Client
	Models     map[string]bool // cached model availability
	modelMutex sync.RWMutex
	maxRetries int
	pool       *http.Client
}

// OllamaGenerateRequest represents a request to the Ollama generate API
type OllamaGenerateRequest struct {
	Model   string   `json:"model"`
	Prompt  string   `json:"prompt"`
	Images  []string `json:"images,omitempty"`
	Stream  bool     `json:"stream"`
	Options struct {
		NumCtx      int     `json:"num_ctx,omitempty"`
		Temperature float64 `json:"temperature,omitempty"`
	} `json:"options,omitempty"`
}

// OllamaGenerateResponse represents the response from Ollama generate API
type OllamaGenerateResponse struct {
	Model     string `json:"model"`
	Response  string `json:"response"`
	Done      bool   `json:"done"`
	Context   []int  `json:"context,omitempty"`
	TotalTime int64  `json:"total_duration,omitempty"`
}

// OllamaListResponse represents the response from Ollama list API
type OllamaListResponse struct {
	Models []struct {
		Name       string `json:"name"`
		ModifiedAt string `json:"modified_at"`
		Size       int64  `json:"size"`
	} `json:"models"`
}

// FrameCaption represents a caption for a video frame with metadata
type FrameCaption struct {
	Frame      string  `json:"frame"`
	Timestamp  float64 `json:"timestamp"`
	Caption    string  `json:"caption"`
	OCR        string  `json:"ocr,omitempty"`
	Model      string  `json:"model"`
	Confidence float64 `json:"confidence"`
	Source     string  `json:"source"` // "fast" or "rich"
}

// CaptionsOutput represents the JSON output structure for captions
type CaptionsOutput struct {
	SourceFile    string         `json:"source_file"`
	ProcessedAt   int64          `json:"processed_at"`
	TotalFrames   int            `json:"total_frames"`
	ProcessedTime float64        `json:"processed_time_seconds"`
	Models        []string       `json:"models_used"`
	Frames        []FrameCaption `json:"frames"`
}

// NewOllamaClient creates a new Ollama client with connection pooling
func NewOllamaClient(baseURL string) *OllamaClient {
	return &OllamaClient{
		BaseURL: baseURL,
		HTTPClient: &http.Client{
			Timeout: 60 * time.Second,
			Transport: &http.Transport{
				MaxIdleConns:        10,
				IdleConnTimeout:     30 * time.Second,
				DisableCompression:  false,
				MaxIdleConnsPerHost: 10,
			},
		},
		Models:     make(map[string]bool),
		maxRetries: 3,
	}
}

// IsModelAvailable checks if a specific model is available in Ollama
func (c *OllamaClient) IsModelAvailable(ctx context.Context, model string) (bool, error) {
	// Check cache first
	c.modelMutex.RLock()
	if available, exists := c.Models[model]; exists {
		c.modelMutex.RUnlock()
		return available, nil
	}
	c.modelMutex.RUnlock()

	// Query Ollama API
	url := c.BaseURL + "/api/tags"
	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return false, &OllamaUnavailableError{
			URL:   c.BaseURL,
			Model: model,
			Err:   fmt.Errorf("failed to create request: %w", err),
		}
	}

	resp, err := c.HTTPClient.Do(req)
	if err != nil {
		return false, &OllamaUnavailableError{
			URL:   c.BaseURL,
			Model: model,
			Err:   fmt.Errorf("failed to query Ollama: %w", err),
		}
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return false, &OllamaUnavailableError{
			URL:   c.BaseURL,
			Model: model,
			Err:   fmt.Errorf("Ollama API returned status %d", resp.StatusCode),
		}
	}

	var listResp OllamaListResponse
	if err := json.NewDecoder(resp.Body).Decode(&listResp); err != nil {
		return false, &OllamaUnavailableError{
			URL:   c.BaseURL,
			Model: model,
			Err:   fmt.Errorf("failed to decode response: %w", err),
		}
	}

	// Update cache
	c.modelMutex.Lock()
	defer c.modelMutex.Unlock()
	
	// Mark all models as unavailable first
	for existingModel := range c.Models {
		c.Models[existingModel] = false
	}
	
	// Collect available models for error reporting
	var availableModels []string
	for _, modelInfo := range listResp.Models {
		c.Models[modelInfo.Name] = true
		availableModels = append(availableModels, modelInfo.Name)
		if modelInfo.Name == model {
			return true, nil
		}
	}
	
	c.Models[model] = false
	
	// Return model not found error with available alternatives
	return false, &ModelNotFoundError{
		Model:     model,
		Available: availableModels,
	}
}

// CaptionImage generates a caption for an image using the specified model
func (c *OllamaClient) CaptionImage(ctx context.Context, imageData []byte, model string, prompt string) (*FrameCaption, error) {
	// Encode image to base64
	imageB64 := base64.StdEncoding.EncodeToString(imageData)
	
	// Default prompt for trading charts
	if prompt == "" {
		prompt = "Describe this trading chart image. Focus on any visible indicators, price levels, candlestick patterns, and text visible on the screen. Be concise but include specific details like numbers, indicator names, and chart patterns."
	}

	// Prepare request
	request := OllamaGenerateRequest{
		Model:  model,
		Prompt: prompt,
		Images: []string{imageB64},
		Stream: false,
	}
	request.Options.NumCtx = 4096
	request.Options.Temperature = 0.7

	var response *OllamaGenerateResponse
	var err error
	
	// Retry logic with exponential backoff
	for attempt := 0; attempt <= c.maxRetries; attempt++ {
		response, err = c.generateWithRetry(ctx, request)
		if err == nil {
			break
		}
		
		if attempt < c.maxRetries {
			// Exponential backoff: 1s, 2s, 4s
			backoff := time.Duration(math.Pow(2, float64(attempt))) * time.Second
			select {
			case <-ctx.Done():
				return nil, ctx.Err()
			case <-time.After(backoff):
				// Continue to next retry
			}
		}
	}

	if err != nil {
		return nil, fmt.Errorf("failed after %d retries: %w", c.maxRetries, err)
	}

	// Create frame caption
	caption := &FrameCaption{
		Caption:    response.Response,
		Model:      model,
		Confidence: calculateConfidence(response.Response, model),
		Source:     getSourceType(model),
	}

	// Extract OCR text if available (basic implementation)
	if ocrText := extractOCRText(response.Response); ocrText != "" {
		caption.OCR = ocrText
	}

	return caption, nil
}

// generateWithRetry performs a single generate request with timeout handling
func (c *OllamaClient) generateWithRetry(ctx context.Context, request OllamaGenerateRequest) (*OllamaGenerateResponse, error) {
	reqBody, err := json.Marshal(request)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	url := c.BaseURL + "/api/generate"
	req, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewBuffer(reqBody))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")

	resp, err := c.HTTPClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API returned status %d: %s", resp.StatusCode, string(body))
	}

	var response OllamaGenerateResponse
	if err := json.NewDecoder(resp.Body).Decode(&response); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &response, nil
}

// CaptionFramesParallel processes multiple frames in parallel with progress tracking
func (c *OllamaClient) CaptionFramesParallel(ctx context.Context, frames []FrameData, model string, maxWorkers int) ([]FrameCaption, error) {
	// Check if model is available
	available, err := c.IsModelAvailable(ctx, model)
	if err != nil {
		return nil, fmt.Errorf("failed to check model availability: %w", err)
	}
	if !available {
		return nil, fmt.Errorf("model %s is not available in Ollama", model)
	}

	if maxWorkers <= 0 {
		maxWorkers = 4 // Default to 4 workers
	}

	// Create channels for work distribution
	frameChan := make(chan FrameData, len(frames))
	resultChan := make(chan captionResult, len(frames))
	
	// Start workers
	var wg sync.WaitGroup
	for i := 0; i < maxWorkers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			c.captionWorker(ctx, frameChan, resultChan, model)
		}()
	}

	// Send frames to workers
	go func() {
		defer close(frameChan)
		for _, frame := range frames {
			select {
			case frameChan <- frame:
			case <-ctx.Done():
				return
			}
		}
	}()

	// Close result channel when workers finish
	go func() {
		wg.Wait()
		close(resultChan)
	}()

	// Collect results
	var results []FrameCaption
	var errors []error
	
	for result := range resultChan {
		if result.err != nil {
			errors = append(errors, fmt.Errorf("frame %s: %w", result.frameID, result.err))
		} else {
			results = append(results, result.caption)
		}
	}

	// Return partial results even if some frames failed
	if len(errors) > 0 && len(results) == 0 {
		return nil, fmt.Errorf("all frames failed: %v", errors[0])
	}

	return results, nil
}

// captionResult holds the result of captioning a single frame
type captionResult struct {
	frameID string
	caption FrameCaption
	err     error
}

// captionWorker processes frames from the channel
func (c *OllamaClient) captionWorker(ctx context.Context, frameChan <-chan FrameData, resultChan chan<- captionResult, model string) {
	for {
		select {
		case frame, ok := <-frameChan:
			if !ok {
				return
			}
			
			// Decode frame data
			var imageData []byte
			var err error
			
			if frame.Data != "" {
				// Base64 encoded data
				imageData, err = base64.StdEncoding.DecodeString(frame.Data)
			} else if frame.Path != "" {
				// File path - read from disk
				imageData, err = readImageFile(frame.Path)
			} else {
				err = fmt.Errorf("no image data or path provided")
			}

			if err != nil {
				resultChan <- captionResult{
					frameID: fmt.Sprintf("frame_%d", frame.FrameNumber),
					err:     err,
				}
				continue
			}

			// Generate caption
			caption, err := c.CaptionImage(ctx, imageData, model, "")
			if err != nil {
				resultChan <- captionResult{
					frameID: fmt.Sprintf("frame_%d", frame.FrameNumber),
					err:     err,
				}
				continue
			}

			// Set frame metadata
			caption.Frame = fmt.Sprintf("frame_%04d.jpg", frame.FrameNumber)
			caption.Timestamp = float64(frame.Timestamp)

			resultChan <- captionResult{
				frameID: fmt.Sprintf("frame_%d", frame.FrameNumber),
				caption: *caption,
			}

		case <-ctx.Done():
			return
		}
	}
}

// Helper functions

// calculateConfidence estimates confidence based on response content and model
func calculateConfidence(response string, model string) float64 {
	// Simple heuristic based on response length and content
	baseConfidence := 0.7
	
	// Longer responses typically indicate more detailed analysis
	if len(response) > 100 {
		baseConfidence += 0.1
	}
	
	// Check for trading-specific terms
	tradingTerms := []string{"chart", "candlestick", "volume", "price", "support", "resistance", "trend", "indicator"}
	termCount := 0
	for _, term := range tradingTerms {
		if bytes.Contains([]byte(response), []byte(term)) {
			termCount++
		}
	}
	
	// Boost confidence for trading-relevant content
	if termCount > 0 {
		baseConfidence += float64(termCount) * 0.05
	}
	
	// Model-specific adjustments
	switch {
	case bytes.Contains([]byte(model), []byte("moondream")):
		baseConfidence *= 0.9 // Fast but slightly less accurate
	case bytes.Contains([]byte(model), []byte("qwen2.5vl:72b")):
		baseConfidence *= 1.1 // Larger model, higher confidence
	}
	
	// Cap at 0.95
	if baseConfidence > 0.95 {
		baseConfidence = 0.95
	}
	
	return baseConfidence
}

// getSourceType returns the source type based on model name
func getSourceType(model string) string {
	if bytes.Contains([]byte(model), []byte("moondream")) {
		return "fast"
	}
	return "rich"
}

// extractOCRText attempts to extract text elements from the caption
func extractOCRText(caption string) string {
	// Simple extraction of potential OCR text
	// Look for patterns like prices, indicators, etc.
	// This is a basic implementation - could be enhanced with regex patterns
	
	// For now, return empty string - OCR extraction would need more sophisticated logic
	return ""
}

// readImageFile reads an image file from disk
func readImageFile(path string) ([]byte, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("failed to read image file %s: %w", path, err)
	}
	return data, nil
}