package main

import (
	"encoding/json"
	"fmt"
	"math"
	"regexp"
	"sort"
	"strings"
	"time"
)

// CaptionProcessor handles preprocessing of video frame captions for trading strategy extraction
type CaptionProcessor struct {
	MaxCaptionLength  int
	MergeTimeWindow   float64 // seconds
	IndicatorAliases  map[string][]string
	FrameSelector     *FrameSelector
	TranscriptProc    *TranscriptProcessor
}

// NewCaptionProcessor creates a new caption processor with default settings
func NewCaptionProcessor() *CaptionProcessor {
	return &CaptionProcessor{
		MaxCaptionLength: 120, // Max chars per caption as per PRP
		MergeTimeWindow:  2.0, // 2 seconds window for merging duplicates
		IndicatorAliases: map[string][]string{
			"VWAP":     {"WAP", "VWAP", "V-WAP", "Volume Weighted", "VOLUME WEIGHTED"},
			"EMA":      {"EMA", "Exponential MA", "Exp Moving Avg", "EXPONENTIAL"},
			"RSI":      {"RSI", "Relative Strength", "R.S.I", "R S I"},
			"MACD":     {"MACD", "MAC-D", "MAC D", "Moving Average Convergence"},
			"SMA":      {"SMA", "Simple MA", "Moving Avg", "SIMPLE MA"},
			"Bollinger": {"BB", "Bollinger", "B-Bands", "Bollinger Bands", "BOLLINGER"},
			"Stoch":    {"Stoch", "Stochastic", "Stoch RSI", "STOCHASTIC"},
			"Support":  {"Support", "Supp", "S/R", "Support Level", "SUPPORT"},
			"Resistance": {"Resistance", "Resist", "R", "Resistance Level", "RESISTANCE"},
			"Volume":   {"Vol", "Volume", "V", "VOL", "VOLUME"},
		},
		FrameSelector:  NewFrameSelector(),
		TranscriptProc: NewTranscriptProcessor(),
	}
}

// ProcessedCaptions contains processed and optimized caption data
type ProcessedCaptions struct {
	SourceFile       string          `json:"source_file"`
	ProcessedFrames  []FrameCaption  `json:"frames"`
	KeyFrames        []FrameCaption  `json:"key_frames"`
	FastPass         []FrameCaption  `json:"fast_pass,omitempty"`
	RichPass         []FrameCaption  `json:"rich_pass,omitempty"`
	TotalFrames      int             `json:"total_frames"`
	ProcessedCount   int             `json:"processed_frames_count"`
	TokenOptimized   bool            `json:"token_optimized"`
	ProcessingStats  ProcessingStats `json:"processing_stats"`
}

// ProcessingStats tracks processing metrics
type ProcessingStats struct {
	OriginalCaptionLength int     `json:"original_caption_length"`
	CompressedLength      int     `json:"compressed_length"`
	CompressionRatio      float64 `json:"compression_ratio"`
	IndicatorsNormalized  int     `json:"indicators_normalized"`
	DuplicatesRemoved     int     `json:"duplicates_removed"`
	ProcessingTimeMs      int64   `json:"processing_time_ms"`
}

// ProcessCaptions performs comprehensive caption processing for trading strategy extraction
func (cp *CaptionProcessor) ProcessCaptions(captions CaptionsOutput, transcript *TranscriptOutput, maxTokens int) (*ProcessedCaptions, error) {
	startTime := time.Now()
	stats := ProcessingStats{}
	
	// Step 1: Normalize and clean captions
	processedFrames := cp.normalizeCaptions(captions.Frames, &stats)
	
	// Step 2: Remove duplicates and merge similar frames
	mergedFrames := cp.mergeAndDeduplicate(processedFrames, &stats)
	
	// Step 3: Select key frames using frame selector
	var keyFrames []FrameCaption
	if transcript != nil {
		keyFrames = cp.FrameSelector.SelectKeyFrames(mergedFrames, *transcript, 12)
	} else {
		// Fallback selection without transcript
		keyFrames = cp.selectKeyFramesFallback(mergedFrames, 12)
	}
	
	// Step 4: Token optimization
	tokenOptimized := false
	if cp.estimateTokenUsage(keyFrames) > maxTokens {
		keyFrames = cp.optimizeForTokens(keyFrames, maxTokens)
		tokenOptimized = true
	}
	
	// Step 5: Separate fast/rich passes if both exist
	fastPass, richPass := cp.separatePassTypes(processedFrames)
	
	// Calculate final stats
	stats.ProcessingTimeMs = time.Since(startTime).Milliseconds()
	stats.CompressionRatio = float64(stats.CompressedLength) / float64(stats.OriginalCaptionLength)
	
	return &ProcessedCaptions{
		SourceFile:      captions.SourceFile,
		ProcessedFrames: mergedFrames,
		KeyFrames:       keyFrames,
		FastPass:        fastPass,
		RichPass:        richPass,
		TotalFrames:     captions.TotalFrames,
		ProcessedCount:  len(mergedFrames),
		TokenOptimized:  tokenOptimized,
		ProcessingStats: stats,
	}, nil
}

// normalizeCaptions cleans and normalizes caption text and OCR data
func (cp *CaptionProcessor) normalizeCaptions(frames []FrameCaption, stats *ProcessingStats) []FrameCaption {
	var processed []FrameCaption
	originalLength := 0
	compressedLength := 0
	indicatorsNormalized := 0
	
	for _, frame := range frames {
		originalLength += len(frame.Caption) + len(frame.OCR)
		
		// Process caption text
		processedCaption := cp.processCaption(frame.Caption)
		
		// Process OCR text with indicator normalization
		processedOCR, normalized := cp.normalizeOCRText(frame.OCR)
		if normalized {
			indicatorsNormalized++
		}
		
		// Truncate to max length while preserving sentence boundaries
		if len(processedCaption) > cp.MaxCaptionLength {
			processedCaption = cp.truncateToSentenceBoundary(processedCaption, cp.MaxCaptionLength)
		}
		
		compressedLength += len(processedCaption) + len(processedOCR)
		
		processed = append(processed, FrameCaption{
			Frame:      frame.Frame,
			Timestamp:  frame.Timestamp,
			Caption:    processedCaption,
			OCR:        processedOCR,
			Model:      frame.Model,
			Confidence: frame.Confidence,
			Source:     frame.Source,
		})
	}
	
	stats.OriginalCaptionLength = originalLength
	stats.CompressedLength = compressedLength
	stats.IndicatorsNormalized = indicatorsNormalized
	
	return processed
}

// processCaption cleans and optimizes caption text
func (cp *CaptionProcessor) processCaption(caption string) string {
	// Remove common artifacts and redundant phrases
	cleaned := strings.TrimSpace(caption)
	
	// Remove redundant phrases
	redundantPhrases := []string{
		"this image shows", "the image displays", "in this image", "we can see",
		"there is", "there are", "it shows", "showing", "displays",
	}
	
	for _, phrase := range redundantPhrases {
		pattern := regexp.MustCompile(`(?i)\b` + regexp.QuoteMeta(phrase) + `\b,?\s*`)
		cleaned = pattern.ReplaceAllString(cleaned, "")
	}
	
	// Normalize trading terms
	cleaned = cp.normalizeTradingTerms(cleaned)
	
	// Fix capitalization for better readability
	cleaned = cp.fixCapitalization(cleaned)
	
	// Remove extra whitespace
	cleaned = regexp.MustCompile(`\s+`).ReplaceAllString(cleaned, " ")
	
	return strings.TrimSpace(cleaned)
}

// normalizeOCRText processes OCR text with indicator alias normalization
func (cp *CaptionProcessor) normalizeOCRText(ocrText string) (string, bool) {
	if ocrText == "" {
		return "", false
	}
	
	normalized := strings.TrimSpace(ocrText)
	indicatorNormalized := false
	
	// Apply indicator alias normalization
	for standard, aliases := range cp.IndicatorAliases {
		for _, alias := range aliases {
			if alias == standard {
				continue // Skip the standard form itself
			}
			
			// Case-insensitive replacement
			pattern := regexp.MustCompile(`(?i)\b` + regexp.QuoteMeta(alias) + `\b`)
			if pattern.MatchString(normalized) {
				normalized = pattern.ReplaceAllString(normalized, standard)
				indicatorNormalized = true
			}
		}
	}
	
	// Clean up common OCR errors
	normalized = cp.fixOCRErrors(normalized)
	
	// Remove duplicate whitespace
	normalized = regexp.MustCompile(`\s+`).ReplaceAllString(normalized, " ")
	
	return strings.TrimSpace(normalized), indicatorNormalized
}

// normalizeTradingTerms standardizes trading terminology
func (cp *CaptionProcessor) normalizeTradingTerms(text string) string {
	termMappings := map[string]string{
		"bullish":     "bull",
		"bearish":     "bear", 
		"uptrend":     "up trend",
		"downtrend":   "down trend",
		"breakout":    "break out",
		"breakdown":   "break down",
		"candlestick": "candle",
		"trendline":   "trend line",
	}
	
	result := text
	for original, normalized := range termMappings {
		pattern := regexp.MustCompile(`(?i)\b` + regexp.QuoteMeta(original) + `\b`)
		result = pattern.ReplaceAllString(result, normalized)
	}
	
	return result
}

// fixCapitalization improves text readability
func (cp *CaptionProcessor) fixCapitalization(text string) string {
	// Capitalize first letter of sentences
	sentences := regexp.MustCompile(`[.!?]+\s+`).Split(text, -1)
	var fixed []string
	
	for _, sentence := range sentences {
		trimmed := strings.TrimSpace(sentence)
		if len(trimmed) > 0 {
			// Capitalize first letter
			runes := []rune(trimmed)
			runes[0] = []rune(strings.ToUpper(string(runes[0])))[0]
			fixed = append(fixed, string(runes))
		}
	}
	
	return strings.Join(fixed, ". ")
}

// fixOCRErrors corrects common OCR recognition mistakes
func (cp *CaptionProcessor) fixOCRErrors(ocrText string) string {
	corrections := map[string]string{
		// Number/letter confusion
		"0": "O", "1": "I", "5": "S", "8": "B",
		// Common symbol mistakes
		"|": "I", "!": "1", "@": "A",
		// Spacing issues
		"S P Y": "SPY", "Q Q Q": "QQQ", "V W A P": "VWAP",
		"R S I": "RSI", "M A C D": "MACD",
	}
	
	result := ocrText
	for incorrect, correct := range corrections {
		// Only replace if it's not part of a larger word
		pattern := regexp.MustCompile(`\b` + regexp.QuoteMeta(incorrect) + `\b`)
		result = pattern.ReplaceAllString(result, correct)
	}
	
	return result
}

// truncateToSentenceBoundary truncates text at sentence boundary
func (cp *CaptionProcessor) truncateToSentenceBoundary(text string, maxLength int) string {
	if len(text) <= maxLength {
		return text
	}
	
	// Find the last sentence boundary before maxLength
	truncated := text[:maxLength]
	lastPeriod := strings.LastIndex(truncated, ".")
	lastExclamation := strings.LastIndex(truncated, "!")
	lastQuestion := strings.LastIndex(truncated, "?")
	
	lastSentenceEnd := lastPeriod
	if lastExclamation > lastSentenceEnd {
		lastSentenceEnd = lastExclamation
	}
	if lastQuestion > lastSentenceEnd {
		lastSentenceEnd = lastQuestion
	}
	
	if lastSentenceEnd > maxLength/2 { // Only truncate if we keep at least half
		return text[:lastSentenceEnd+1]
	}
	
	// Fallback: truncate at word boundary
	words := strings.Fields(truncated)
	return strings.Join(words[:len(words)-1], " ") + "..."
}

// mergeAndDeduplicate removes duplicate frames and merges similar captions
func (cp *CaptionProcessor) mergeAndDeduplicate(frames []FrameCaption, stats *ProcessingStats) []FrameCaption {
	if len(frames) == 0 {
		return frames
	}
	
	// Sort by timestamp
	sort.Slice(frames, func(i, j int) bool {
		return frames[i].Timestamp < frames[j].Timestamp
	})
	
	var merged []FrameCaption
	duplicatesRemoved := 0
	
	for _, current := range frames {
		shouldMerge := false
		mergeIndex := -1
		
		// Check if this frame should be merged with a recent frame
		for j := len(merged) - 1; j >= 0; j-- {
			if math.Abs(current.Timestamp-merged[j].Timestamp) > cp.MergeTimeWindow {
				break // Too far back in time
			}
			
			// Check similarity
			if cp.areSimilarCaptions(current, merged[j]) {
				shouldMerge = true
				mergeIndex = j
				break
			}
		}
		
		if shouldMerge && mergeIndex >= 0 {
			// Merge with existing frame
			merged[mergeIndex] = cp.mergeCaptions(merged[mergeIndex], current)
			duplicatesRemoved++
		} else {
			// Add as new frame
			merged = append(merged, current)
		}
	}
	
	stats.DuplicatesRemoved = duplicatesRemoved
	return merged
}

// areSimilarCaptions determines if two captions are similar enough to merge
func (cp *CaptionProcessor) areSimilarCaptions(a, b FrameCaption) bool {
	// Check OCR similarity first (more reliable)
	if a.OCR != "" && b.OCR != "" {
		return cp.textSimilarity(a.OCR, b.OCR) > 0.8
	}
	
	// Check caption similarity
	return cp.textSimilarity(a.Caption, b.Caption) > 0.7
}

// textSimilarity calculates similarity between two text strings (simple implementation)
func (cp *CaptionProcessor) textSimilarity(a, b string) float64 {
	if a == b {
		return 1.0
	}
	
	wordsA := strings.Fields(strings.ToLower(a))
	wordsB := strings.Fields(strings.ToLower(b))
	
	if len(wordsA) == 0 || len(wordsB) == 0 {
		return 0.0
	}
	
	// Simple word overlap similarity
	wordSetA := make(map[string]bool)
	for _, word := range wordsA {
		wordSetA[word] = true
	}
	
	overlap := 0
	for _, word := range wordsB {
		if wordSetA[word] {
			overlap++
		}
	}
	
	// Jaccard similarity
	union := len(wordsA) + len(wordsB) - overlap
	if union == 0 {
		return 0.0
	}
	
	return float64(overlap) / float64(union)
}

// mergeCaptions combines two similar captions
func (cp *CaptionProcessor) mergeCaptions(a, b FrameCaption) FrameCaption {
	// Use the higher confidence caption as base
	base := a
	other := b
	if b.Confidence > a.Confidence {
		base = b
		other = a
	}
	
	// Merge OCR text if both have it
	mergedOCR := base.OCR
	if base.OCR != other.OCR && other.OCR != "" {
		if len(other.OCR) > len(base.OCR) {
			mergedOCR = other.OCR
		}
	}
	
	// Use average timestamp
	avgTimestamp := (a.Timestamp + b.Timestamp) / 2.0
	
	return FrameCaption{
		Frame:      base.Frame,
		Timestamp:  avgTimestamp,
		Caption:    base.Caption,
		OCR:        mergedOCR,
		Model:      base.Model,
		Confidence: math.Max(a.Confidence, b.Confidence),
		Source:     base.Source,
	}
}

// selectKeyFramesFallback selects key frames without transcript analysis
func (cp *CaptionProcessor) selectKeyFramesFallback(frames []FrameCaption, maxFrames int) []FrameCaption {
	if len(frames) <= maxFrames {
		return frames
	}
	
	// Score frames by confidence and content richness
	type scoredFrame struct {
		frame FrameCaption
		score float64
	}
	
	var scored []scoredFrame
	for _, frame := range frames {
		score := frame.Confidence * 0.6 // Base on confidence
		
		// Bonus for OCR content
		if frame.OCR != "" {
			score += 0.2
		}
		
		// Bonus for trading terms in caption
		tradingTermCount := cp.countTradingTerms(frame.Caption)
		score += float64(tradingTermCount) * 0.1
		
		scored = append(scored, scoredFrame{frame, score})
	}
	
	// Sort by score
	sort.Slice(scored, func(i, j int) bool {
		return scored[i].score > scored[j].score
	})
	
	// Select top frames with temporal distribution
	var selected []FrameCaption
	for i := 0; i < maxFrames && i < len(scored); i++ {
		selected = append(selected, scored[i].frame)
	}
	
	// Sort selected frames by timestamp
	sort.Slice(selected, func(i, j int) bool {
		return selected[i].Timestamp < selected[j].Timestamp
	})
	
	return selected
}

// countTradingTerms counts trading-related terms in text
func (cp *CaptionProcessor) countTradingTerms(text string) int {
	tradingTerms := []string{
		"chart", "candle", "volume", "price", "trend", "support", "resistance",
		"breakout", "pattern", "indicator", "moving", "average", "rsi", "macd",
	}
	
	textLower := strings.ToLower(text)
	count := 0
	for _, term := range tradingTerms {
		if strings.Contains(textLower, term) {
			count++
		}
	}
	return count
}

// estimateTokenUsage estimates token usage for caption data
func (cp *CaptionProcessor) estimateTokenUsage(frames []FrameCaption) int {
	totalChars := 0
	for _, frame := range frames {
		totalChars += len(frame.Caption) + len(frame.OCR)
	}
	// Rough estimation: 4 characters per token on average
	return totalChars / 4
}

// optimizeForTokens reduces caption data to fit within token limits
func (cp *CaptionProcessor) optimizeForTokens(frames []FrameCaption, maxTokens int) []FrameCaption {
	currentTokens := cp.estimateTokenUsage(frames)
	if currentTokens <= maxTokens {
		return frames
	}
	
	// Strategy 1: Reduce frame count
	reductionRatio := float64(maxTokens) / float64(currentTokens)
	targetFrames := int(float64(len(frames)) * reductionRatio * 0.8) // 80% to be safe
	
	if targetFrames < len(frames) {
		// Keep highest confidence frames
		sort.Slice(frames, func(i, j int) bool {
			return frames[i].Confidence > frames[j].Confidence
		})
		frames = frames[:targetFrames]
	}
	
	// Strategy 2: Truncate captions further if still too many tokens
	currentTokens = cp.estimateTokenUsage(frames)
	if currentTokens > maxTokens {
		reductionRatio = float64(maxTokens) / float64(currentTokens)
		newMaxLength := int(float64(cp.MaxCaptionLength) * reductionRatio)
		
		for i := range frames {
			if len(frames[i].Caption) > newMaxLength {
				frames[i].Caption = cp.truncateToSentenceBoundary(frames[i].Caption, newMaxLength)
			}
		}
	}
	
	return frames
}

// separatePassTypes separates frames by processing pass type
func (cp *CaptionProcessor) separatePassTypes(frames []FrameCaption) ([]FrameCaption, []FrameCaption) {
	var fast, rich []FrameCaption
	
	for _, frame := range frames {
		if frame.Source == "fast" {
			fast = append(fast, frame)
		} else if frame.Source == "rich" {
			rich = append(rich, frame)
		}
	}
	
	return fast, rich
}

// PrepareForFabric formats processed captions for Fabric input
func (cp *CaptionProcessor) PrepareForFabric(processed *ProcessedCaptions) (string, error) {
	// Create compact JSON structure for Fabric
	fabricData := map[string]interface{}{
		"source_file": processed.SourceFile,
		"frames":      processed.KeyFrames,
		"stats": map[string]interface{}{
			"total_frames":       processed.TotalFrames,
			"key_frames":         len(processed.KeyFrames),
			"compression_ratio":  processed.ProcessingStats.CompressionRatio,
			"token_optimized":   processed.TokenOptimized,
		},
	}
	
	// Convert to compact JSON
	jsonBytes, err := json.Marshal(fabricData)
	if err != nil {
		return "", fmt.Errorf("failed to marshal caption data: %w", err)
	}
	
	return string(jsonBytes), nil
}