package main

import (
	"math"
	"regexp"
	"sort"
	"strings"
)

// FrameSelector implements intelligent frame selection for trading strategy extraction
type FrameSelector struct {
	TranscriptKeywords map[float64][]string  // timestamp -> keywords
	OCRConfidence     map[string]float64     // frame -> confidence
	SceneChanges      map[string]float64     // frame -> delta
	IndicatorAliases  map[string][]string    // normalized -> aliases
}

// NewFrameSelector creates a new frame selector with trading indicator aliases
func NewFrameSelector() *FrameSelector {
	return &FrameSelector{
		TranscriptKeywords: make(map[float64][]string),
		OCRConfidence:     make(map[string]float64),
		SceneChanges:      make(map[string]float64),
		IndicatorAliases: map[string][]string{
			"VWAP":     {"WAP", "VWAP", "V-WAP", "Volume Weighted"},
			"EMA":      {"EMA", "Exponential MA", "Exp Moving Avg"},
			"RSI":      {"RSI", "Relative Strength", "R.S.I"},
			"MACD":     {"MACD", "MAC-D", "Moving Average Convergence"},
			"SMA":      {"SMA", "Simple MA", "Moving Avg"},
			"Bollinger": {"BB", "Bollinger", "B-Bands", "Bollinger Bands"},
			"Stoch":    {"Stoch", "Stochastic", "Stoch RSI"},
			"Support":  {"Support", "Supp", "S/R", "Support Level"},
			"Resistance": {"Resistance", "Resist", "R", "Resistance Level"},
		},
	}
}

// FrameScore represents a frame with its selection score and metadata
type FrameScore struct {
	Frame      FrameCaption
	Score      float64
	Reason     string
	Timestamp  float64
	Priority   int // 1 = highest, 3 = lowest
}

// SelectKeyFrames selects the most relevant frames using the algorithm specified in the PRP
func (fs *FrameSelector) SelectKeyFrames(captions []FrameCaption, transcript TranscriptOutput, maxFrames int) []FrameCaption {
	if maxFrames <= 0 {
		maxFrames = 12 // Default from PRP
	}

	// Step 1: Extract keywords from transcript
	fs.extractTranscriptKeywords(transcript)

	// Step 2: Score all frames
	var scoredFrames []FrameScore
	for _, caption := range captions {
		score := fs.scoreFrame(caption, transcript.Duration)
		if score.Score > 0 {
			scoredFrames = append(scoredFrames, score)
		}
	}

	// Step 3: Sort by priority then score
	sort.Slice(scoredFrames, func(i, j int) bool {
		if scoredFrames[i].Priority == scoredFrames[j].Priority {
			return scoredFrames[i].Score > scoredFrames[j].Score
		}
		return scoredFrames[i].Priority < scoredFrames[j].Priority
	})

	// Step 4: Select frames with deduplication
	selected := fs.selectWithDeduplication(scoredFrames, maxFrames, transcript.Duration)

	// Step 5: Return frame captions in chronological order
	sort.Slice(selected, func(i, j int) bool {
		return selected[i].Timestamp < selected[j].Timestamp
	})

	var result []FrameCaption
	for _, scored := range selected {
		result = append(result, scored.Frame)
	}

	return result
}

// extractTranscriptKeywords extracts keywords from transcript segments with timestamps
func (fs *FrameSelector) extractTranscriptKeywords(transcript TranscriptOutput) {
	tradingKeywords := []string{
		// Entry/Exit terms
		"entry", "enter", "buy", "sell", "exit", "close", "position",
		// Price action
		"breakout", "breakdown", "bounce", "rejection", "pullback",
		// Levels
		"support", "resistance", "level", "zone", "area",
		// Indicators
		"vwap", "ema", "sma", "rsi", "macd", "bollinger", "stochastic",
		// Chart patterns
		"flag", "triangle", "wedge", "channel", "trendline",
		// Risk management
		"stop", "target", "risk", "reward", "size",
	}

	for _, segment := range transcript.Segments {
		var keywords []string
		text := strings.ToLower(segment.Text)
		
		for _, keyword := range tradingKeywords {
			if strings.Contains(text, keyword) {
				keywords = append(keywords, keyword)
			}
		}
		
		// Also extract price mentions
		pricePattern := regexp.MustCompile(`\$?(\d+\.?\d*)\s*(dollars?|cents?|k|thousand|mil|million)?`)
		matches := pricePattern.FindAllString(text, -1)
		for _, match := range matches {
			keywords = append(keywords, "price:"+match)
		}
		
		if len(keywords) > 0 {
			fs.TranscriptKeywords[segment.Start] = keywords
		}
	}
}

// scoreFrame calculates a composite score for a frame based on multiple criteria
func (fs *FrameSelector) scoreFrame(caption FrameCaption, videoDuration float64) FrameScore {
	var score float64
	var reasons []string
	priority := 3 // Default to lowest priority

	// Priority 1: Frames mentioned in transcript by timestamp (±3s window)
	transcriptScore := fs.getTranscriptRelevanceScore(caption.Timestamp)
	if transcriptScore > 0 {
		priority = 1
		score += transcriptScore * 100 // High weight for transcript relevance
		reasons = append(reasons, "transcript-mentioned")
	}

	// Priority 2: Frames with high OCR confidence containing indicators
	ocrScore := fs.getOCRIndicatorScore(caption)
	if ocrScore > 0.8 {
		if priority > 2 {
			priority = 2
		}
		score += ocrScore * 50 // Medium-high weight for OCR indicators
		reasons = append(reasons, "indicator-detected")
	}

	// Priority 3: Scene change detection (simulated based on caption content change)
	sceneScore := fs.getSceneChangeScore(caption)
	if sceneScore > 0.3 {
		if priority > 2 {
			priority = 2
		}
		score += sceneScore * 30 // Medium weight for scene changes
		reasons = append(reasons, "scene-change")
	}

	// Additional scoring factors
	
	// Content relevance (trading terms in caption)
	contentScore := fs.getContentRelevanceScore(caption.Caption)
	score += contentScore * 20
	if contentScore > 0.5 {
		reasons = append(reasons, "trading-content")
	}

	// Temporal distribution bonus (prefer frames spread across video)
	temporalScore := fs.getTemporalDistributionScore(caption.Timestamp, videoDuration)
	score += temporalScore * 10

	return FrameScore{
		Frame:     caption,
		Score:     score,
		Reason:    strings.Join(reasons, ","),
		Timestamp: caption.Timestamp,
		Priority:  priority,
	}
}

// getTranscriptRelevanceScore returns score based on proximity to transcript keywords
func (fs *FrameSelector) getTranscriptRelevanceScore(timestamp float64) float64 {
	maxScore := 0.0
	
	for transcriptTime, keywords := range fs.TranscriptKeywords {
		// ±3 second window as specified in PRP
		if math.Abs(timestamp-transcriptTime) <= 3.0 {
			keywordScore := float64(len(keywords)) / 10.0 // Normalize by keyword count
			if keywordScore > maxScore {
				maxScore = keywordScore
			}
		}
	}
	
	return math.Min(maxScore, 1.0)
}

// getOCRIndicatorScore analyzes OCR text for trading indicators
func (fs *FrameSelector) getOCRIndicatorScore(caption FrameCaption) float64 {
	if caption.OCR == "" {
		return 0.0
	}

	ocrText := strings.ToUpper(caption.OCR)
	indicatorCount := 0
	
	for _, aliases := range fs.IndicatorAliases {
		for _, alias := range aliases {
			if strings.Contains(ocrText, strings.ToUpper(alias)) {
				indicatorCount++
				break // Count each indicator type only once
			}
		}
	}

	// Also look for price levels
	pricePattern := regexp.MustCompile(`\d+\.?\d*`)
	priceMatches := pricePattern.FindAllString(ocrText, -1)
	
	score := float64(indicatorCount) * 0.3 // 0.3 per indicator
	if len(priceMatches) > 0 {
		score += 0.2 // Bonus for price information
	}
	
	// High confidence bonus
	if caption.Confidence > 0.8 {
		score *= 1.2
	}

	return math.Min(score, 1.0)
}

// getSceneChangeScore estimates scene change magnitude (simplified implementation)
func (fs *FrameSelector) getSceneChangeScore(caption FrameCaption) float64 {
	// In a real implementation, this would analyze actual image differences
	// For now, we use caption length and content variety as proxies
	
	captionLength := len(caption.Caption)
	words := strings.Fields(caption.Caption)
	
	// Longer, more detailed captions often indicate scene changes
	lengthScore := math.Min(float64(captionLength)/200.0, 0.5)
	
	// Variety in words (simple heuristic)
	uniqueWords := make(map[string]bool)
	for _, word := range words {
		uniqueWords[strings.ToLower(word)] = true
	}
	varietyScore := math.Min(float64(len(uniqueWords))/float64(len(words)), 0.5)
	
	return lengthScore + varietyScore
}

// getContentRelevanceScore analyzes caption text for trading relevance
func (fs *FrameSelector) getContentRelevanceScore(caption string) float64 {
	tradingTerms := []string{
		"chart", "candlestick", "candle", "bar", "volume", "price", "trend",
		"support", "resistance", "breakout", "pattern", "indicator", "moving",
		"average", "rsi", "macd", "bollinger", "stochastic", "fibonacci",
		"trade", "buy", "sell", "long", "short", "bull", "bear",
	}

	captionLower := strings.ToLower(caption)
	matchCount := 0
	
	for _, term := range tradingTerms {
		if strings.Contains(captionLower, term) {
			matchCount++
		}
	}

	return math.Min(float64(matchCount)/10.0, 1.0)
}

// getTemporalDistributionScore provides bonus for frames spread across video duration
func (fs *FrameSelector) getTemporalDistributionScore(timestamp, duration float64) float64 {
	if duration <= 0 {
		return 0.0
	}
	
	// Prefer frames from different parts of the video
	position := timestamp / duration
	
	// Give higher scores to frames in beginning, middle, and end
	if position < 0.1 || (position > 0.4 && position < 0.6) || position > 0.9 {
		return 1.0
	} else if position < 0.3 || position > 0.7 {
		return 0.5
	}
	
	return 0.2
}

// selectWithDeduplication selects frames while avoiding duplicates within 2 seconds
func (fs *FrameSelector) selectWithDeduplication(scoredFrames []FrameScore, maxFrames int, videoDuration float64) []FrameScore {
	var selected []FrameScore
	const minTimeDiff = 2.0 // 2 seconds minimum between selected frames

	for _, candidate := range scoredFrames {
		if len(selected) >= maxFrames {
			break
		}

		// Check if too close to already selected frames
		tooClose := false
		for _, existing := range selected {
			if math.Abs(candidate.Timestamp-existing.Timestamp) < minTimeDiff {
				tooClose = true
				break
			}
		}

		if !tooClose {
			selected = append(selected, candidate)
		}
	}

	// If we don't have enough frames, try to ensure temporal distribution
	if len(selected) < maxFrames && len(scoredFrames) > len(selected) {
		selected = fs.ensureTemporalDistribution(selected, scoredFrames, maxFrames, videoDuration)
	}

	return selected
}

// ensureTemporalDistribution ensures frames are distributed across the video timeline
func (fs *FrameSelector) ensureTemporalDistribution(selected []FrameScore, allFrames []FrameScore, maxFrames int, videoDuration float64) []FrameScore {
	// Calculate time segments
	numSegments := int(math.Min(float64(maxFrames), 6)) // Max 6 segments
	segmentDuration := videoDuration / float64(numSegments)
	
	// Create segment buckets
	segmentFrames := make([][]FrameScore, numSegments)
	
	for _, frame := range allFrames {
		segment := int(frame.Timestamp / segmentDuration)
		if segment >= numSegments {
			segment = numSegments - 1
		}
		segmentFrames[segment] = append(segmentFrames[segment], frame)
	}

	// Sort frames in each segment by score
	for i := range segmentFrames {
		sort.Slice(segmentFrames[i], func(j, k int) bool {
			return segmentFrames[i][j].Score > segmentFrames[i][k].Score
		})
	}

	// Fill missing segments if we have space
	for i := 0; i < numSegments && len(selected) < maxFrames; i++ {
		if len(segmentFrames[i]) == 0 {
			continue
		}
		
		// Check if this segment is already represented
		segmentRepresented := false
		segmentStart := float64(i) * segmentDuration
		segmentEnd := segmentStart + segmentDuration
		
		for _, existing := range selected {
			if existing.Timestamp >= segmentStart && existing.Timestamp < segmentEnd {
				segmentRepresented = true
				break
			}
		}
		
		// Add best frame from this segment if not represented
		if !segmentRepresented {
			bestFrame := segmentFrames[i][0]
			// Check deduplication constraint
			tooClose := false
			for _, existing := range selected {
				if math.Abs(bestFrame.Timestamp-existing.Timestamp) < 2.0 {
					tooClose = true
					break
				}
			}
			if !tooClose {
				selected = append(selected, bestFrame)
			}
		}
	}

	return selected
}

// NormalizeIndicatorText normalizes OCR text using the indicator aliases
func (fs *FrameSelector) NormalizeIndicatorText(ocrText string) string {
	if ocrText == "" {
		return ""
	}

	result := ocrText
	upperText := strings.ToUpper(ocrText)

	for standard, aliases := range fs.IndicatorAliases {
		for _, alias := range aliases {
			upperAlias := strings.ToUpper(alias)
			if upperAlias != strings.ToUpper(standard) && strings.Contains(upperText, upperAlias) {
				// Replace the alias with the standard form
				pattern := regexp.MustCompile(`(?i)\b` + regexp.QuoteMeta(alias) + `\b`)
				result = pattern.ReplaceAllString(result, standard)
			}
		}
	}

	return result
}