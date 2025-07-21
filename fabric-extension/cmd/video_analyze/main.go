package main

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	"github.com/spf13/cobra"
)

// TranscriptSegment represents a transcript segment with timing
type TranscriptSegment struct {
	ID    int     `json:"id"`
	Start float64 `json:"start"`
	End   float64 `json:"end"`
	Text  string  `json:"text"`
}

// TranscriptOutput represents the complete transcription result
type TranscriptOutput struct {
	Text       string             `json:"text"`
	Segments   []TranscriptSegment `json:"segments"`
	Language   string             `json:"language"`
	Duration   float64            `json:"duration"`
	Backend    string             `json:"backend"`
	SourceFile string             `json:"source_file"`
	Model      string             `json:"model"`
	Timestamp  float64            `json:"timestamp"`
}

// FrameData represents a single extracted frame
type FrameData struct {
	FrameNumber int    `json:"frame_number"`
	Timestamp   int    `json:"timestamp"`
	Data        string `json:"data,omitempty"`
	Path        string `json:"path,omitempty"`
}

// FrameOutput represents the complete frame extraction result
type FrameOutput struct {
	SourceFile    string      `json:"source_file"`
	Duration      float64     `json:"duration"`
	FrameInterval int         `json:"frame_interval"`
	FrameCount    int         `json:"frame_count"`
	FrameSize     string      `json:"frame_size"`
	Timestamp     int64       `json:"timestamp"`
	Frames        []FrameData `json:"frames"`
}

// VideoMetadata represents basic video information
type VideoMetadata struct {
	SourceFile    string  `json:"source_file"`
	Duration      float64 `json:"duration"`
	ProcessedAt   int64   `json:"processed_at"`
	WhisperModel  string  `json:"whisper_model"`
	WhisperBackend string  `json:"whisper_backend"`
	FrameInterval int     `json:"frame_interval"`
	FrameCount    int     `json:"frame_count"`
}

// VideoAnalysisInput represents the complete input for Fabric patterns
type VideoAnalysisInput struct {
	Transcript TranscriptOutput `json:"transcript"`
	Frames     FrameOutput      `json:"frames"`
	Metadata   VideoMetadata    `json:"metadata"`
}

var (
	whisperModel   string
	whisperBackend string
	frameInterval  int
	frameFormat    string
	maxFrames      int
	frameQuality   int
	frameResize    string
	skipTranscript bool
	skipFrames     bool
	verbose        bool
)

var rootCmd = &cobra.Command{
	Use:   "video_analyze [video_file]",
	Short: "Combined video analysis helper for Fabric integration",
	Long: `A comprehensive Fabric helper tool that extracts both transcript and frames
from videos for complete analysis.

This tool orchestrates both whisper_transcribe and video_frames to provide
complete video analysis data that can be piped to Fabric patterns.

Examples:
  video_analyze video.mp4 | fabric -p analyze_video_content
  video_analyze --whisper-model large lecture.mp4 | fabric -p summarize_lecture
  video_analyze --frame-interval 60 tutorial.mp4 | fabric -p extract_code_from_video
  video_analyze --skip-frames audio.mp3 | fabric -p summarize_audio
  
Trading-specific examples:
  video_analyze trading_tutorial.mp4 | fabric -p analyze_trading_video
  video_analyze --frame-interval 45 chart_analysis.mp4 | fabric -p extract_technical_analysis`,
	Args: cobra.ExactArgs(1),
	RunE: analyzeVideo,
}

func init() {
	// Whisper options
	rootCmd.Flags().StringVar(&whisperModel, "whisper-model", "base", "Whisper model size (tiny, base, small, medium, large)")
	rootCmd.Flags().StringVar(&whisperBackend, "whisper-backend", "auto", "Whisper backend (auto, mlx, faster-whisper, openai-whisper)")
	
	// Frame extraction options
	rootCmd.Flags().IntVar(&frameInterval, "frame-interval", 30, "Frame extraction interval in seconds")
	rootCmd.Flags().StringVar(&frameFormat, "frame-format", "base64", "Frame output format (base64, paths, both)")
	rootCmd.Flags().IntVar(&maxFrames, "max-frames", 50, "Maximum frames to extract")
	rootCmd.Flags().IntVar(&frameQuality, "frame-quality", 2, "Frame JPEG quality 1-5")
	rootCmd.Flags().StringVar(&frameResize, "frame-resize", "320x240", "Frame resize dimensions")
	
	// Processing options
	rootCmd.Flags().BoolVar(&skipTranscript, "skip-transcript", false, "Skip transcript extraction (frames only)")
	rootCmd.Flags().BoolVar(&skipFrames, "skip-frames", false, "Skip frame extraction (transcript only)")
	rootCmd.Flags().BoolVarP(&verbose, "verbose", "v", false, "Verbose output")
}

func analyzeVideo(cmd *cobra.Command, args []string) error {
	videoFile := args[0]

	// Check if file exists
	if _, err := os.Stat(videoFile); os.IsNotExist(err) {
		return fmt.Errorf("file not found: %s", videoFile)
	}

	// Cannot skip both transcript and frames
	if skipTranscript && skipFrames {
		return fmt.Errorf("cannot skip both transcript and frames")
	}

	var transcriptResult TranscriptOutput
	var frameResult FrameOutput
	var err error

	// Extract transcript if not skipped
	if !skipTranscript {
		if verbose {
			fmt.Fprintf(os.Stderr, "Extracting transcript...\n")
		}
		
		transcriptResult, err = runWhisperTranscribe(videoFile)
		if err != nil {
			return fmt.Errorf("transcript extraction failed: %v", err)
		}
		
		if verbose {
			fmt.Fprintf(os.Stderr, "Transcript extracted: %d segments\n", len(transcriptResult.Segments))
		}
	}

	// Extract frames if not skipped
	if !skipFrames {
		if verbose {
			fmt.Fprintf(os.Stderr, "Extracting frames...\n")
		}
		
		frameResult, err = runVideoFrames(videoFile)
		if err != nil {
			return fmt.Errorf("frame extraction failed: %v", err)
		}
		
		if verbose {
			fmt.Fprintf(os.Stderr, "Frames extracted: %d frames\n", frameResult.FrameCount)
		}
	}

	// Combine results
	analysis := VideoAnalysisInput{
		Transcript: transcriptResult,
		Frames:     frameResult,
		Metadata: VideoMetadata{
			SourceFile:     videoFile,
			Duration:       transcriptResult.Duration,
			ProcessedAt:    time.Now().Unix(),
			WhisperModel:   whisperModel,
			WhisperBackend: transcriptResult.Backend,
			FrameInterval:  frameInterval,
			FrameCount:     frameResult.FrameCount,
		},
	}

	// Output JSON for Fabric
	output, err := json.MarshalIndent(analysis, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to generate JSON output: %v", err)
	}

	fmt.Print(string(output))
	
	if verbose {
		fmt.Fprintf(os.Stderr, "Analysis complete\n")
	}

	return nil
}

func runWhisperTranscribe(videoFile string) (TranscriptOutput, error) {
	var result TranscriptOutput

	// Find whisper_transcribe executable
	whisperCmd, err := findExecutable("whisper_transcribe")
	if err != nil {
		return result, fmt.Errorf("whisper_transcribe not found: %v", err)
	}

	// Build command arguments
	args := []string{videoFile}
	
	if whisperModel != "base" {
		args = append(args, "--model", whisperModel)
	}
	
	if whisperBackend != "auto" {
		args = append(args, "--backend", whisperBackend)
	}
	
	if verbose {
		args = append(args, "--verbose")
	}

	// Execute whisper_transcribe
	cmd := exec.Command(whisperCmd, args...)
	cmd.Stderr = os.Stderr
	
	output, err := cmd.Output()
	if err != nil {
		return result, fmt.Errorf("whisper_transcribe execution failed: %v", err)
	}

	// Parse JSON output
	if err := json.Unmarshal(output, &result); err != nil {
		return result, fmt.Errorf("failed to parse whisper_transcribe output: %v", err)
	}

	return result, nil
}

func runVideoFrames(videoFile string) (FrameOutput, error) {
	var result FrameOutput

	// Find video_frames executable
	framesCmd, err := findExecutable("video_frames")
	if err != nil {
		return result, fmt.Errorf("video_frames not found: %v", err)
	}

	// Build command arguments
	args := []string{videoFile}
	
	if frameInterval != 30 {
		args = append(args, "--interval", strconv.Itoa(frameInterval))
	}
	
	if frameFormat != "base64" {
		args = append(args, "--format", frameFormat)
	}
	
	if maxFrames != 50 {
		args = append(args, "--max-frames", strconv.Itoa(maxFrames))
	}
	
	if frameQuality != 2 {
		args = append(args, "--quality", strconv.Itoa(frameQuality))
	}
	
	if frameResize != "320x240" {
		args = append(args, "--resize", frameResize)
	}
	
	if verbose {
		args = append(args, "--verbose")
	}

	// Execute video_frames
	cmd := exec.Command(framesCmd, args...)
	cmd.Stderr = os.Stderr
	
	output, err := cmd.Output()
	if err != nil {
		return result, fmt.Errorf("video_frames execution failed: %v", err)
	}

	// Parse JSON output
	if err := json.Unmarshal(output, &result); err != nil {
		return result, fmt.Errorf("failed to parse video_frames output: %v", err)
	}

	return result, nil
}

func findExecutable(name string) (string, error) {
	// Try to find the executable in various locations
	possiblePaths := []string{
		// In PATH
		name,
		// In same directory as current executable
		filepath.Join(filepath.Dir(os.Args[0]), name),
		// Common installation locations
		"/usr/local/bin/" + name,
		"/usr/bin/" + name,
		// User's home directory
		filepath.Join(os.Getenv("HOME"), ".local", "bin", name),
	}

	// Also try GOPATH if available
	if goPath := os.Getenv("GOPATH"); goPath != "" {
		possiblePaths = append(possiblePaths, 
			filepath.Join(goPath, "bin", name))
	}

	// Check each possible path
	for _, path := range possiblePaths {
		if _, err := os.Stat(path); err == nil {
			return path, nil
		}
	}

	// Try using which command
	cmd := exec.Command("which", name)
	if output, err := cmd.Output(); err == nil {
		path := strings.TrimSpace(string(output))
		if path != "" {
			return path, nil
		}
	}

	return "", fmt.Errorf("%s not found in any expected location", name)
}

func main() {
	if err := rootCmd.Execute(); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
}