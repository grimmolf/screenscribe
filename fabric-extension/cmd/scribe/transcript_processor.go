package main

import (
	"fmt"
	"regexp"
	"sort"
	"strings"
	"unicode"
)

// TranscriptProcessor handles preprocessing of transcript data for strategy extraction
type TranscriptProcessor struct {
	MaxTokens        int
	FillerWords      []string
	TimestampPattern *regexp.Regexp
}

// NewTranscriptProcessor creates a new transcript processor with default settings
func NewTranscriptProcessor() *TranscriptProcessor {
	return &TranscriptProcessor{
		MaxTokens: 10000, // Max tokens as specified in PRP
		FillerWords: []string{
			"um", "uh", "uhm", "er", "ah", "eh", "like", "you know", "so",
			"basically", "actually", "literally", "kind of", "sort of",
		},
		TimestampPattern: regexp.MustCompile(`\[\d{2}:\d{2}:\d{2}\]|\[\d{2}:\d{2}\]`),
	}
}

// ProcessedTranscript contains the cleaned transcript and extracted metadata
type ProcessedTranscript struct {
	CleanText         string                 `json:"clean_text"`
	Segments          []TranscriptSegment    `json:"segments"`
	Keywords          map[float64][]string   `json:"keywords"` // timestamp -> keywords
	TradingTerms      []string               `json:"trading_terms"`
	PriceReferences   []PriceReference       `json:"price_references"`
	IndicatorMentions []IndicatorMention     `json:"indicator_mentions"`
	TokenCount        int                    `json:"token_count"`
	OriginalDuration  float64                `json:"original_duration"`
}

// PriceReference represents a price mentioned in the transcript
type PriceReference struct {
	Price     string  `json:"price"`
	Timestamp float64 `json:"timestamp"`
	Context   string  `json:"context"`
}

// IndicatorMention represents a technical indicator mentioned in the transcript
type IndicatorMention struct {
	Indicator string  `json:"indicator"`
	Timestamp float64 `json:"timestamp"`
	Context   string  `json:"context"`
	Normalized string `json:"normalized"`
}

// ProcessTranscript cleans and analyzes a transcript for trading strategy extraction
func (tp *TranscriptProcessor) ProcessTranscript(transcript TranscriptOutput) *ProcessedTranscript {
	result := &ProcessedTranscript{
		Keywords:          make(map[float64][]string),
		TradingTerms:      []string{},
		PriceReferences:   []PriceReference{},
		IndicatorMentions: []IndicatorMention{},
		OriginalDuration:  transcript.Duration,
	}

	// Clean and process each segment
	var cleanSegments []string
	for _, segment := range transcript.Segments {
		cleanText := tp.cleanSegmentText(segment.Text)
		if cleanText != "" {
			cleanSegments = append(cleanSegments, cleanText)
			
			// Extract keywords from this segment
			keywords := tp.extractKeywords(cleanText)
			if len(keywords) > 0 {
				result.Keywords[segment.Start] = keywords
			}
			
			// Extract price references
			prices := tp.extractPriceReferences(segment.Text, segment.Start)
			result.PriceReferences = append(result.PriceReferences, prices...)
			
			// Extract indicator mentions
			indicators := tp.extractIndicatorMentions(segment.Text, segment.Start)
			result.IndicatorMentions = append(result.IndicatorMentions, indicators...)
		}
		
		// Store cleaned segment
		cleanSegment := TranscriptSegment{
			ID:    segment.ID,
			Start: segment.Start,
			End:   segment.End,
			Text:  cleanText,
		}
		result.Segments = append(result.Segments, cleanSegment)
	}

	// Join all clean segments
	result.CleanText = strings.Join(cleanSegments, " ")
	
	// Truncate if exceeds token limit
	result.CleanText = tp.truncateToTokenLimit(result.CleanText)
	result.TokenCount = tp.estimateTokenCount(result.CleanText)
	
	// Extract overall trading terms
	result.TradingTerms = tp.extractTradingTerms(result.CleanText)

	return result
}

// cleanSegmentText removes timestamps, filler words, and normalizes text
func (tp *TranscriptProcessor) cleanSegmentText(text string) string {
	// Remove timestamps
	cleaned := tp.TimestampPattern.ReplaceAllString(text, "")
	
	// Convert to lowercase for processing
	words := strings.Fields(strings.ToLower(cleaned))
	var cleanWords []string
	
	for _, word := range words {
		// Remove punctuation for comparison
		cleanWord := strings.TrimFunc(word, unicode.IsPunct)
		
		// Skip filler words
		if tp.isFillerWord(cleanWord) {
			continue
		}
		
		// Skip very short words (likely artifacts)
		if len(cleanWord) < 2 {
			continue
		}
		
		cleanWords = append(cleanWords, word) // Keep original case and punctuation
	}
	
	result := strings.Join(cleanWords, " ")
	
	// Fix common transcription errors
	result = tp.fixTranscriptionErrors(result)
	
	return strings.TrimSpace(result)
}

// isFillerWord checks if a word is in the filler words list
func (tp *TranscriptProcessor) isFillerWord(word string) bool {
	for _, filler := range tp.FillerWords {
		if word == filler {
			return true
		}
	}
	return false
}

// fixTranscriptionErrors corrects common transcription mistakes
func (tp *TranscriptProcessor) fixTranscriptionErrors(text string) string {
	corrections := map[string]string{
		// Common trading term corrections
		"v wap":           "VWAP",
		"v w a p":         "VWAP",
		"volume weighted": "VWAP",
		"mac d":           "MACD",
		"m a c d":         "MACD",
		"r s i":           "RSI",
		"relative strength": "RSI",
		"exponential moving": "exponential moving average",
		"simple moving":     "simple moving average",
		"bollinger band":    "Bollinger Bands",
		"fibonacci":         "Fibonacci",
		"stochastic":        "stochastic",
		
		// Price-related corrections
		"dollars":     "dollars",
		"buck":        "dollar",
		"bucks":       "dollars",
		"k":           "thousand",
		"grand":       "thousand",
		
		// Common mispronunciations
		"support level": "support",
		"resistance level": "resistance",
		"trend line":    "trendline",
		"break out":     "breakout",
		"break down":    "breakdown",
	}

	result := text
	for incorrect, correct := range corrections {
		// Case-insensitive replacement
		pattern := regexp.MustCompile(`(?i)\b` + regexp.QuoteMeta(incorrect) + `\b`)
		result = pattern.ReplaceAllString(result, correct)
	}

	return result
}

// extractKeywords extracts trading-relevant keywords from text
func (tp *TranscriptProcessor) extractKeywords(text string) []string {
	tradingKeywords := map[string]bool{
		// Entry/Exit terms
		"entry": true, "enter": true, "buy": true, "sell": true, "exit": true, 
		"close": true, "position": true, "long": true, "short": true,
		
		// Price action
		"breakout": true, "breakdown": true, "bounce": true, "rejection": true, 
		"pullback": true, "reversal": true, "continuation": true,
		
		// Levels and zones
		"support": true, "resistance": true, "level": true, "zone": true, 
		"area": true, "range": true, "channel": true,
		
		// Indicators
		"vwap": true, "ema": true, "sma": true, "rsi": true, "macd": true, 
		"bollinger": true, "stochastic": true, "fibonacci": true,
		
		// Chart patterns
		"flag": true, "triangle": true, "wedge": true, "pennant": true,
		"cup": true, "handle": true, "head": true, "shoulders": true,
		
		// Risk management
		"stop": true, "target": true, "risk": true, "reward": true, "size": true,
		"loss": true, "profit": true, "ratio": true,
		
		// Market structure
		"trend": true, "uptrend": true, "downtrend": true, "sideways": true,
		"bull": true, "bear": true, "market": true, "volume": true,
	}

	var keywords []string
	words := strings.Fields(strings.ToLower(text))
	
	for _, word := range words {
		cleanWord := strings.TrimFunc(word, unicode.IsPunct)
		if tradingKeywords[cleanWord] {
			keywords = append(keywords, cleanWord)
		}
	}
	
	// Remove duplicates
	uniqueKeywords := make(map[string]bool)
	var result []string
	for _, keyword := range keywords {
		if !uniqueKeywords[keyword] {
			result = append(result, keyword)
			uniqueKeywords[keyword] = true
		}
	}
	
	return result
}

// extractPriceReferences finds price mentions in the transcript
func (tp *TranscriptProcessor) extractPriceReferences(text string, timestamp float64) []PriceReference {
	var prices []PriceReference
	
	// Price patterns
	patterns := []*regexp.Regexp{
		regexp.MustCompile(`\$(\d+(?:\.\d{2})?)`),                    // $123.45
		regexp.MustCompile(`(\d+(?:\.\d{2})?)\s*dollars?`),           // 123.45 dollars
		regexp.MustCompile(`(\d+(?:\.\d{2})?)\s*bucks?`),             // 123.45 bucks
		regexp.MustCompile(`(\d+)\s*k(?:\s|$)`),                      // 123k
		regexp.MustCompile(`(\d+(?:\.\d+)?)\s*thousand`),             // 123.5 thousand
	}
	
	for _, pattern := range patterns {
		matches := pattern.FindAllStringSubmatch(text, -1)
		for _, match := range matches {
			if len(match) > 1 {
				// Get context (surrounding words)
				context := tp.extractContext(text, match[0], 10)
				
				prices = append(prices, PriceReference{
					Price:     match[1],
					Timestamp: timestamp,
					Context:   context,
				})
			}
		}
	}
	
	return prices
}

// extractIndicatorMentions finds technical indicator references
func (tp *TranscriptProcessor) extractIndicatorMentions(text string, timestamp float64) []IndicatorMention {
	var indicators []IndicatorMention
	
	indicatorPatterns := map[string]*regexp.Regexp{
		"VWAP":        regexp.MustCompile(`(?i)\b(vwap|v[-\s]?wap|volume\s+weighted)\b`),
		"EMA":         regexp.MustCompile(`(?i)\b(ema|exponential\s+moving\s+average)\b`),
		"SMA":         regexp.MustCompile(`(?i)\b(sma|simple\s+moving\s+average)\b`),
		"RSI":         regexp.MustCompile(`(?i)\b(rsi|relative\s+strength\s+index?)\b`),
		"MACD":        regexp.MustCompile(`(?i)\b(macd|mac[-\s]?d|moving\s+average\s+convergence)\b`),
		"Bollinger":   regexp.MustCompile(`(?i)\b(bollinger\s*bands?|bb)\b`),
		"Stochastic":  regexp.MustCompile(`(?i)\b(stochastic|stoch)\b`),
		"Fibonacci":   regexp.MustCompile(`(?i)\b(fibonacci|fib)\b`),
	}
	
	for normalized, pattern := range indicatorPatterns {
		matches := pattern.FindAllStringSubmatch(text, -1)
		for _, match := range matches {
			context := tp.extractContext(text, match[0], 15)
			
			indicators = append(indicators, IndicatorMention{
				Indicator:  match[0],
				Timestamp:  timestamp,
				Context:    context,
				Normalized: normalized,
			})
		}
	}
	
	return indicators
}

// extractContext gets surrounding words for context
func (tp *TranscriptProcessor) extractContext(text, match string, maxWords int) string {
	words := strings.Fields(text)
	matchIndex := -1
	
	// Find the match
	for i, word := range words {
		if strings.Contains(word, strings.Fields(match)[0]) {
			matchIndex = i
			break
		}
	}
	
	if matchIndex == -1 {
		return match
	}
	
	// Get context window
	start := matchIndex - maxWords/2
	if start < 0 {
		start = 0
	}
	
	end := matchIndex + maxWords/2
	if end >= len(words) {
		end = len(words) - 1
	}
	
	contextWords := words[start : end+1]
	return strings.Join(contextWords, " ")
}

// extractTradingTerms finds all trading terms in the text
func (tp *TranscriptProcessor) extractTradingTerms(text string) []string {
	termFreq := make(map[string]int)
	
	// Define comprehensive trading vocabulary
	tradingVocab := []string{
		"breakout", "breakdown", "support", "resistance", "trend", "volume",
		"entry", "exit", "stop", "target", "risk", "reward", "position",
		"long", "short", "buy", "sell", "bullish", "bearish",
		"vwap", "ema", "sma", "rsi", "macd", "bollinger", "stochastic",
		"fibonacci", "pivot", "level", "zone", "channel", "pattern",
		"candle", "candlestick", "doji", "hammer", "engulfing",
		"flag", "triangle", "wedge", "pennant", "cup", "handle",
		"consolidation", "accumulation", "distribution", "squeeze",
		"momentum", "divergence", "convergence", "oscillator",
	}
	
	textLower := strings.ToLower(text)
	for _, term := range tradingVocab {
		count := strings.Count(textLower, term)
		if count > 0 {
			termFreq[term] = count
		}
	}
	
	// Sort by frequency
	type termCount struct {
		term  string
		count int
	}
	
	var terms []termCount
	for term, count := range termFreq {
		terms = append(terms, termCount{term, count})
	}
	
	sort.Slice(terms, func(i, j int) bool {
		return terms[i].count > terms[j].count
	})
	
	// Return top terms
	var result []string
	maxTerms := 20
	for i, tc := range terms {
		if i >= maxTerms {
			break
		}
		result = append(result, tc.term)
	}
	
	return result
}

// truncateToTokenLimit truncates text to stay within token limit
func (tp *TranscriptProcessor) truncateToTokenLimit(text string) string {
	estimatedTokens := tp.estimateTokenCount(text)
	if estimatedTokens <= tp.MaxTokens {
		return text
	}
	
	// Truncate by sentences to maintain coherence
	sentences := tp.splitIntoSentences(text)
	var result []string
	currentTokens := 0
	
	for _, sentence := range sentences {
		sentenceTokens := tp.estimateTokenCount(sentence)
		if currentTokens+sentenceTokens > tp.MaxTokens {
			break
		}
		result = append(result, sentence)
		currentTokens += sentenceTokens
	}
	
	return strings.Join(result, " ")
}

// estimateTokenCount provides rough token count estimation
func (tp *TranscriptProcessor) estimateTokenCount(text string) int {
	// Rough estimation: ~4 characters per token on average
	return len(text) / 4
}

// splitIntoSentences splits text into sentences
func (tp *TranscriptProcessor) splitIntoSentences(text string) []string {
	// Simple sentence splitting on periods, exclamation marks, and question marks
	sentenceEnders := regexp.MustCompile(`[.!?]+\s+`)
	sentences := sentenceEnders.Split(text, -1)
	
	var result []string
	for _, sentence := range sentences {
		trimmed := strings.TrimSpace(sentence)
		if len(trimmed) > 10 { // Filter out very short fragments
			result = append(result, trimmed)
		}
	}
	
	return result
}

// PrepareForFabric formats the processed transcript for Fabric input
func (tp *TranscriptProcessor) PrepareForFabric(processed *ProcessedTranscript) string {
	var sections []string
	
	// Add clean transcript
	sections = append(sections, "=== TRANSCRIPT ===")
	sections = append(sections, processed.CleanText)
	sections = append(sections, "")
	
	// Add key trading terms if found
	if len(processed.TradingTerms) > 0 {
		sections = append(sections, "=== KEY TRADING TERMS ===")
		sections = append(sections, strings.Join(processed.TradingTerms, ", "))
		sections = append(sections, "")
	}
	
	// Add price references if found
	if len(processed.PriceReferences) > 0 {
		sections = append(sections, "=== PRICE REFERENCES ===")
		for _, price := range processed.PriceReferences {
			sections = append(sections, fmt.Sprintf("- %s at %.1fs: %s", 
				price.Price, price.Timestamp, price.Context))
		}
		sections = append(sections, "")
	}
	
	// Add indicator mentions if found
	if len(processed.IndicatorMentions) > 0 {
		sections = append(sections, "=== INDICATORS MENTIONED ===")
		for _, indicator := range processed.IndicatorMentions {
			sections = append(sections, fmt.Sprintf("- %s (%s) at %.1fs: %s", 
				indicator.Normalized, indicator.Indicator, indicator.Timestamp, indicator.Context))
		}
		sections = append(sections, "")
	}
	
	return strings.Join(sections, "\n")
}