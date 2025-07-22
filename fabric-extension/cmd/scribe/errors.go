package main

import (
	"fmt"
	"os"
	"strings"
)

// Custom error types for comprehensive error handling as specified in PRP

// CaptionError represents errors during caption generation
type CaptionError struct {
	Frame   string
	Model   string
	Attempt int
	Err     error
}

func (e *CaptionError) Error() string {
	return fmt.Sprintf("caption error for frame %s with model %s (attempt %d): %v", e.Frame, e.Model, e.Attempt, e.Err)
}

func (e *CaptionError) Unwrap() error {
	return e.Err
}

// OllamaUnavailableError represents when Ollama service is not available
type OllamaUnavailableError struct {
	URL   string
	Model string
	Err   error
}

func (e *OllamaUnavailableError) Error() string {
	return fmt.Sprintf("Ollama unavailable at %s for model %s: %v", e.URL, e.Model, e.Err)
}

func (e *OllamaUnavailableError) Unwrap() error {
	return e.Err
}

// ModelNotFoundError represents when a required model is not available
type ModelNotFoundError struct {
	Model    string
	Available []string
}

func (e *ModelNotFoundError) Error() string {
	return fmt.Sprintf("model %s not found. Available models: %s", e.Model, strings.Join(e.Available, ", "))
}

// ProcessingTimeoutError represents timeout during processing
type ProcessingTimeoutError struct {
	Operation string
	Duration  string
	MaxTime   string
}

func (e *ProcessingTimeoutError) Error() string {
	return fmt.Sprintf("operation %s timed out after %s (max: %s)", e.Operation, e.Duration, e.MaxTime)
}

// TokenLimitExceededError represents when content exceeds token limits
type TokenLimitExceededError struct {
	CurrentTokens int
	MaxTokens     int
	Component     string
}

func (e *TokenLimitExceededError) Error() string {
	return fmt.Sprintf("%s token limit exceeded: %d tokens (max: %d)", e.Component, e.CurrentTokens, e.MaxTokens)
}

// ValidationError represents validation failures
type ValidationError struct {
	Field   string
	Value   interface{}
	Reason  string
}

func (e *ValidationError) Error() string {
	return fmt.Sprintf("validation failed for %s (%v): %s", e.Field, e.Value, e.Reason)
}

// ErrorRecovery provides error recovery and diagnostic information
type ErrorRecovery struct {
	Operation    string
	AttemptCount int
	Errors       []error
	Recoverable  bool
	Suggestions  []string
}

// NewErrorRecovery creates a new error recovery handler
func NewErrorRecovery(operation string) *ErrorRecovery {
	return &ErrorRecovery{
		Operation:   operation,
		Errors:      make([]error, 0),
		Suggestions: make([]string, 0),
		Recoverable: true,
	}
}

// AddError adds an error to the recovery handler
func (er *ErrorRecovery) AddError(err error) {
	er.Errors = append(er.Errors, err)
	er.AttemptCount++
	
	// Add context-specific suggestions
	er.addSuggestionsForError(err)
}

// addSuggestionsForError adds recovery suggestions based on error type
func (er *ErrorRecovery) addSuggestionsForError(err error) {
	switch e := err.(type) {
	case *OllamaUnavailableError:
		er.Suggestions = append(er.Suggestions, 
			"Start Ollama service: ollama serve",
			"Check Ollama is running: curl "+e.URL+"/api/tags",
			"Install required model: ollama pull "+e.Model)
			
	case *ModelNotFoundError:
		er.Suggestions = append(er.Suggestions,
			"Pull the required model: ollama pull "+e.Model,
			"List available models: ollama list",
			"Use an available model from: "+strings.Join(e.Available, ", "))
			
	case *ProcessingTimeoutError:
		er.Suggestions = append(er.Suggestions,
			"Reduce frame interval: --frame-interval 60",
			"Use faster model: --captions-model moondream:1.8b",
			"Reduce max frames: --max-frames 25",
			"Increase workers for parallel processing: --captions-workers 8")
			
	case *TokenLimitExceededError:
		er.Suggestions = append(er.Suggestions,
			"Reduce frame count: --max-frames 30",
			"Use shorter frame intervals: --frame-interval 45",
			"Skip frames for audio-only: --skip-frames")
			
	default:
		// Generic suggestions
		if strings.Contains(err.Error(), "connection") {
			er.Suggestions = append(er.Suggestions, "Check network connectivity and firewall settings")
		}
		if strings.Contains(err.Error(), "timeout") {
			er.Suggestions = append(er.Suggestions, "Increase timeout or reduce processing load")
		}
		if strings.Contains(err.Error(), "memory") || strings.Contains(err.Error(), "out of memory") {
			er.Suggestions = append(er.Suggestions, 
				"Reduce memory usage with smaller models or fewer workers",
				"Close other applications to free memory")
		}
	}
}

// ShouldRetry determines if operation should be retried
func (er *ErrorRecovery) ShouldRetry(maxAttempts int) bool {
	if er.AttemptCount >= maxAttempts {
		er.Recoverable = false
		return false
	}
	
	// Don't retry certain unrecoverable errors
	for _, err := range er.Errors {
		if _, ok := err.(*ValidationError); ok {
			er.Recoverable = false
			return false
		}
		if _, ok := err.(*ModelNotFoundError); ok {
			er.Recoverable = false
			return false
		}
	}
	
	return er.Recoverable
}

// GetDiagnosticInfo returns diagnostic information for debugging
func (er *ErrorRecovery) GetDiagnosticInfo() map[string]interface{} {
	errorMessages := make([]string, len(er.Errors))
	for i, err := range er.Errors {
		errorMessages[i] = err.Error()
	}
	
	return map[string]interface{}{
		"operation":     er.Operation,
		"attempt_count": er.AttemptCount,
		"errors":        errorMessages,
		"recoverable":   er.Recoverable,
		"suggestions":   er.Suggestions,
	}
}

// CreateDiagnosticMessage creates a user-friendly diagnostic message
func (er *ErrorRecovery) CreateDiagnosticMessage() string {
	if len(er.Errors) == 0 {
		return "Operation completed successfully"
	}
	
	var builder strings.Builder
	builder.WriteString(fmt.Sprintf("❌ %s failed after %d attempts\n\n", er.Operation, er.AttemptCount))
	
	// Show most recent error
	if len(er.Errors) > 0 {
		builder.WriteString("Latest error:\n")
		builder.WriteString(fmt.Sprintf("  %v\n\n", er.Errors[len(er.Errors)-1]))
	}
	
	// Show suggestions if available
	if len(er.Suggestions) > 0 {
		builder.WriteString("💡 Suggested solutions:\n")
		for _, suggestion := range er.Suggestions {
			builder.WriteString(fmt.Sprintf("  • %s\n", suggestion))
		}
		builder.WriteString("\n")
	}
	
	// Show fallback options
	if er.Operation == "Caption Generation" {
		builder.WriteString("🔄 Fallback options:\n")
		builder.WriteString("  • Continue without captions: remove --generate-captions flag\n")
		builder.WriteString("  • Use transcript-only analysis: add --skip-frames flag\n")
		builder.WriteString("  • Try different model: --captions-model moondream:1.8b\n")
	}
	
	return builder.String()
}

// GracefulFallback provides fallback behavior for failed operations
type GracefulFallback struct {
	OriginalOperation string
	FallbackStrategy  string
	Success           bool
	Message           string
}

// AttemptCaptionFallback attempts graceful fallback for caption generation failures
func AttemptCaptionFallback(err error, frameCount int, hasTranscript bool) *GracefulFallback {
	fallback := &GracefulFallback{
		OriginalOperation: "Caption Generation",
	}
	
	switch e := err.(type) {
	case *OllamaUnavailableError:
		if hasTranscript {
			fallback.FallbackStrategy = "Transcript-only analysis"
			fallback.Success = true
			fallback.Message = "Ollama unavailable, continuing with transcript-only analysis"
		} else {
			fallback.FallbackStrategy = "Frame metadata only"
			fallback.Success = true
			fallback.Message = "Ollama unavailable, using frame metadata without captions"
		}
		
	case *ModelNotFoundError:
		fallback.FallbackStrategy = "Alternative model suggestion"
		fallback.Success = false
		fallback.Message = fmt.Sprintf("Model not found. Try: ollama pull %s", e.Model)
		
	case *ProcessingTimeoutError:
		if frameCount > 25 {
			fallback.FallbackStrategy = "Reduced frame processing"
			fallback.Success = true
			fallback.Message = "Processing timeout, suggest reducing frame count (--max-frames 25)"
		} else {
			fallback.FallbackStrategy = "Skip captions"
			fallback.Success = true
			fallback.Message = "Processing timeout, continuing without captions"
		}
		
	case *TokenLimitExceededError:
		fallback.FallbackStrategy = "Content reduction"
		fallback.Success = true
		fallback.Message = "Token limit exceeded, reducing content and retrying"
		
	default:
		// Generic fallback
		if hasTranscript {
			fallback.FallbackStrategy = "Transcript-only analysis"
			fallback.Success = true
			fallback.Message = "Caption generation failed, falling back to transcript-only analysis"
		} else {
			fallback.FallbackStrategy = "Basic frame analysis"
			fallback.Success = true
			fallback.Message = "Caption generation failed, using basic frame metadata"
		}
	}
	
	return fallback
}

// ValidateConfiguration validates configuration parameters
func ValidateConfiguration() []error {
	var errors []error
	
	// Validate model names (basic validation)
	if captionsModelFlag == "" {
		errors = append(errors, &ValidationError{
			Field:  "captions-model",
			Value:  captionsModelFlag,
			Reason: "model name cannot be empty",
		})
	}
	
	// Validate worker counts
	if analyzeCaptionWorkers < 1 || analyzeCaptionWorkers > 16 {
		errors = append(errors, &ValidationError{
			Field:  "captions-workers", 
			Value:  analyzeCaptionWorkers,
			Reason: "worker count must be between 1 and 16",
		})
	}
	
	// Validate frame limits
	if maxFrames < 1 || maxFrames > 200 {
		errors = append(errors, &ValidationError{
			Field:  "max-frames",
			Value:  maxFrames,
			Reason: "frame count must be between 1 and 200",
		})
	}
	
	// Validate URL format
	if ollamaURL != "" && !strings.HasPrefix(ollamaURL, "http") {
		errors = append(errors, &ValidationError{
			Field:  "ollama-url",
			Value:  ollamaURL,
			Reason: "URL must start with http:// or https://",
		})
	}
	
	return errors
}

// RecoverFromPanic recovers from panics during processing
func RecoverFromPanic(operation string) {
	if r := recover(); r != nil {
		fmt.Fprintf(os.Stderr, "⚠️  Panic during %s: %v\n", operation, r)
		fmt.Fprintf(os.Stderr, "The operation failed unexpectedly but the program will continue.\n")
		fmt.Fprintf(os.Stderr, "Consider reducing processing parameters or checking system resources.\n")
	}
}