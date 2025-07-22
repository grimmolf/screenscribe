package main

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"runtime"
	"strconv"
	"strings"
	"time"

	"github.com/spf13/cobra"
)

// Helper function to convert Go bool to Python bool string
func pythonBool(b bool) string {
	if b {
		return "True"
	}
	return "False"
}

// Common data structures shared across subcommands
type TranscriptSegment struct {
	ID    int     `json:"id"`
	Start float64 `json:"start"`
	End   float64 `json:"end"`
	Text  string  `json:"text"`
}

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

type FrameData struct {
	FrameNumber int    `json:"frame_number"`
	Timestamp   int    `json:"timestamp"`
	Data        string `json:"data,omitempty"`
	Path        string `json:"path,omitempty"`
}

type FrameOutput struct {
	SourceFile    string      `json:"source_file"`
	Duration      float64     `json:"duration"`
	FrameInterval int         `json:"frame_interval"`
	FrameCount    int         `json:"frame_count"`
	FrameSize     string      `json:"frame_size"`
	Timestamp     int64       `json:"timestamp"`
	Frames        []FrameData `json:"frames"`
}

type VideoMetadata struct {
	SourceFile     string  `json:"source_file"`
	Duration       float64 `json:"duration"`
	ProcessedAt    int64   `json:"processed_at"`
	WhisperModel   string  `json:"whisper_model"`
	WhisperBackend string  `json:"whisper_backend"`
	FrameInterval  int     `json:"frame_interval"`
	FrameCount     int     `json:"frame_count"`
}

type VideoAnalysisInput struct {
	Transcript TranscriptOutput `json:"transcript"`
	Frames     FrameOutput      `json:"frames"`
	Metadata   VideoMetadata    `json:"metadata"`
}

// Version information (set at build time)
var (
	Version   = "dev"
	GitCommit = "unknown"
	BuildDate = "unknown"
)

// Global flags
var (
	verbose      bool
	updateFlag   bool
	uninstallFlag bool
)

// Root command
var rootCmd = &cobra.Command{
	Use:   "scribe",
	Short: "AI-powered video analysis tool for the Fabric framework",
	Long: `scribe is a comprehensive video analysis tool that extracts transcripts,
analyzes visual content, and creates structured notes using AI.

Perfect for lectures, meetings, tutorials, and any video content you want to 
reference later. Integrates seamlessly with the Fabric AI framework.

Examples:
  scribe analyze video.mp4 | fabric -p analyze_video_content
  scribe transcribe --model large lecture.mp4 | fabric -p summarize_lecture
  scribe frames --interval 60 tutorial.mp4 | fabric -p extract_visual_content

YouTube examples:
  scribe analyze "https://www.youtube.com/watch?v=VIDEO_ID" | fabric -p analyze_video_content
  scribe analyze --youtube-transcript "https://youtu.be/VIDEO_ID" | fabric -p summarize_lecture

Management:
  scribe update      # Update scribe from GitHub
  scribe --update    # Update scribe from GitHub (flag form)
  scribe uninstall   # Remove scribe from system
  scribe --uninstall # Remove scribe from system (flag form)`,
	Version: getVersionString(),
	RunE: func(cmd *cobra.Command, args []string) error {
		// Handle --update flag (but not if --help is also specified)
		if updateFlag && !cmd.Flags().Changed("help") {
			return runUpdate()
		}
		// Handle --uninstall flag (but not if --help is also specified)
		if uninstallFlag && !cmd.Flags().Changed("help") {
			return runUninstall()
		}
		// If no subcommand and no flags, show help
		return cmd.Help()
	},
}

// getVersionString returns a formatted version string
func getVersionString() string {
	if Version == "dev" {
		return fmt.Sprintf("%s (commit: %s, built: %s)", Version, GitCommit, BuildDate)
	}
	return Version
}

// versionCmd provides detailed version information
var versionCmd = &cobra.Command{
	Use:   "version",
	Short: "Show version information",
	Long:  `Display detailed version information including git commit and build date.`,
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Printf("scribe version %s\n", Version)
		fmt.Printf("Git commit: %s\n", GitCommit)
		fmt.Printf("Build date: %s\n", BuildDate)
	},
}

func init() {
	rootCmd.PersistentFlags().BoolVarP(&verbose, "verbose", "v", false, "Verbose output")
	rootCmd.Flags().BoolVar(&updateFlag, "update", false, "Update scribe tools from GitHub")
	rootCmd.Flags().BoolVar(&uninstallFlag, "uninstall", false, "Remove scribe tools from system")
	
	// Add subcommands
	rootCmd.AddCommand(analyzeCmd)
	rootCmd.AddCommand(transcribeCmd)
	rootCmd.AddCommand(framesCmd)
	rootCmd.AddCommand(captionsCmd)
	rootCmd.AddCommand(versionCmd)
	rootCmd.AddCommand(updateCmd)
	rootCmd.AddCommand(uninstallCmd)
}

// Analyze subcommand (replaces video_analyze)
var (
	whisperModel      string
	whisperBackend    string
	frameInterval     int
	frameFormat       string
	maxFrames         int
	frameQuality      int
	frameResize       string
	skipTranscript    bool
	skipFrames        bool
	youtubeTranscript bool
	// Caption generation options
	generateCaptions     bool
	captionsModelFlag    string
	ollamaURL            string
	analyzeCaptionWorkers int
	twoPassCaptions      bool
	richModelFlag        string
)

var analyzeCmd = &cobra.Command{
	Use:   "analyze [video_file_or_youtube_url]",
	Short: "Complete video analysis with transcript and frames",
	Long: `Performs comprehensive video analysis by extracting both transcript and frames
from videos for complete analysis. Supports local files and YouTube URLs.

This command orchestrates transcription and frame extraction, with optional 
visual caption generation using Ollama vision models for enhanced analysis.

Examples:
  scribe analyze video.mp4 | fabric -p analyze_video_content
  scribe analyze --whisper-model large lecture.mp4 | fabric -p summarize_lecture
  scribe analyze --frame-interval 60 tutorial.mp4 | fabric -p extract_code_from_video
  scribe analyze --skip-frames audio.mp3 | fabric -p summarize_audio

YouTube examples:
  scribe analyze "https://www.youtube.com/watch?v=VIDEO_ID" | fabric -p analyze_video_content
  scribe analyze --youtube-transcript "https://youtu.be/VIDEO_ID" | fabric -p summarize_lecture
  scribe analyze --frame-interval 120 "https://youtube.com/watch?v=VIDEO_ID" | fabric -p extract_code_from_video
  
Trading strategy extraction with captions:
  scribe analyze --generate-captions trading_video.mp4 | fabric -p extract_trading_strategy
  scribe analyze --generate-captions --captions-two-pass chart_analysis.mp4 | fabric -p extract_trading_strategy
  scribe analyze --generate-captions --captions-model qwen2.5vl:7b trading_course.mp4 | fabric -p extract_trading_strategy`,
	Args: cobra.ExactArgs(1),
	RunE: runAnalyze,
}

func init() {
	// Whisper options
	analyzeCmd.Flags().StringVar(&whisperModel, "whisper-model", "base", "Whisper model size (tiny, base, small, medium, large)")
	analyzeCmd.Flags().StringVar(&whisperBackend, "whisper-backend", "auto", "Whisper backend (auto, mlx, faster-whisper, openai-whisper)")
	
	// Frame extraction options
	analyzeCmd.Flags().IntVar(&frameInterval, "frame-interval", 30, "Frame extraction interval in seconds")
	analyzeCmd.Flags().StringVar(&frameFormat, "frame-format", "base64", "Frame output format (base64, paths, both)")
	analyzeCmd.Flags().IntVar(&maxFrames, "max-frames", 50, "Maximum frames to extract")
	analyzeCmd.Flags().IntVar(&frameQuality, "frame-quality", 2, "Frame JPEG quality 1-5")
	analyzeCmd.Flags().StringVar(&frameResize, "frame-resize", "320x240", "Frame resize dimensions")
	
	// Processing options
	analyzeCmd.Flags().BoolVar(&skipTranscript, "skip-transcript", false, "Skip transcript extraction (frames only)")
	analyzeCmd.Flags().BoolVar(&skipFrames, "skip-frames", false, "Skip frame extraction (transcript only)")
	analyzeCmd.Flags().BoolVar(&youtubeTranscript, "youtube-transcript", false, "Use YouTube's native transcript instead of Whisper (YouTube URLs only)")
	
	// Caption generation options
	analyzeCmd.Flags().BoolVar(&generateCaptions, "generate-captions", false, "Generate visual captions using Ollama (requires Ollama)")
	analyzeCmd.Flags().StringVar(&captionsModelFlag, "captions-model", "moondream:1.8b", "Ollama model for caption generation")
	analyzeCmd.Flags().StringVar(&ollamaURL, "ollama-url", "http://localhost:11434", "Ollama API URL")
	analyzeCmd.Flags().IntVar(&analyzeCaptionWorkers, "captions-workers", 4, "Number of parallel caption workers")
	analyzeCmd.Flags().BoolVar(&twoPassCaptions, "captions-two-pass", false, "Use two-pass caption generation (fast + rich models)")
	analyzeCmd.Flags().StringVar(&richModelFlag, "captions-rich-model", "qwen2.5vl:7b", "Rich model for two-pass captioning")
}

// Transcribe subcommand (replaces whisper_transcribe)
var (
	transcribeModel    string
	transcribeLanguage string
	transcribeBackend  string
)

var transcribeCmd = &cobra.Command{
	Use:   "transcribe [video_file]",
	Short: "Extract transcript from video using Whisper",
	Long: `Transcribes video/audio files using Whisper AI models with support for
multiple backends including MLX for Apple Silicon GPU acceleration.

This command integrates with the Fabric AI framework by outputting JSON
that can be piped to Fabric patterns for video analysis.

Examples:
  scribe transcribe video.mp4 | fabric -p analyze_video_content
  scribe transcribe --model large lecture.mp4 | fabric -p summarize_lecture
  scribe transcribe --backend mlx tutorial.mp4 | fabric -p extract_code_from_video`,
	Args: cobra.ExactArgs(1),
	RunE: runTranscribe,
}

func init() {
	transcribeCmd.Flags().StringVar(&transcribeModel, "model", "base", "Whisper model size (tiny, base, small, medium, large, large-v2, large-v3)")
	transcribeCmd.Flags().StringVar(&transcribeLanguage, "language", "", "Force specific language (optional)")
	transcribeCmd.Flags().StringVar(&transcribeBackend, "backend", "auto", "Transcription backend (auto, mlx, faster-whisper, openai-whisper)")
}

// Frames subcommand (replaces video_frames)
var (
	framesInterval  int
	framesFormat    string
	framesMaxFrames int
	framesQuality   int
	framesResize    string
)

var framesCmd = &cobra.Command{
	Use:   "frames [video_file]",
	Short: "Extract frames from video at specified intervals",
	Long: `Extracts frames from videos at specified intervals for visual analysis.
Supports various output formats and quality settings.

This command integrates with the Fabric AI framework by outputting JSON
that can be piped to Fabric patterns for video analysis.

Examples:
  scribe frames video.mp4 | fabric -p analyze_frames
  scribe frames --interval 60 lecture.mp4 | fabric -p extract_visual_content
  scribe frames --format both tutorial.mp4 | fabric -p analyze_video_content`,
	Args: cobra.ExactArgs(1),
	RunE: runFrames,
}

func init() {
	framesCmd.Flags().IntVar(&framesInterval, "interval", 30, "Frame extraction interval in seconds")
	framesCmd.Flags().StringVar(&framesFormat, "format", "base64", "Output format: base64, paths, or both")
	framesCmd.Flags().IntVar(&framesMaxFrames, "max-frames", 50, "Maximum number of frames to extract")
	framesCmd.Flags().IntVar(&framesQuality, "quality", 2, "JPEG quality 1-5, 1=best, 5=worst")
	framesCmd.Flags().StringVar(&framesResize, "resize", "320x240", "Resize frames to WxH")
}

// Captions subcommand - generates visual captions using Ollama vision models
var (
	captionsModel       string
	captionsOllamaURL   string
	captionsWorkers     int
	captionsTwoPass     bool
	captionsRichModel   string
	captionsFrameData   string
)

var captionsCmd = &cobra.Command{
	Use:   "captions [frame_json_or_video_file]",
	Short: "Generate captions for video frames using Ollama vision models",
	Long: `Generates descriptive captions for video frames using Ollama vision models.
Can process frame JSON from 'scribe frames' or extract frames from video directly.

This command integrates with Ollama to provide visual analysis of trading charts,
technical indicators, and other visual content in videos. Supports both fast
(moondream) and rich (qwen2.5vl) vision models.

Examples:
  # Process frames from JSON
  scribe frames video.mp4 | scribe captions

  # Two-pass processing (fast + rich models)
  scribe captions --two-pass video.mp4

  # Custom model and workers
  scribe captions --model qwen2.5vl:7b --workers 2 video.mp4

  # Complete trading strategy extraction workflow  
  scribe analyze video.mp4 > analysis.json
  scribe captions --frame-data analysis.json | fabric -p extract_trading_strategy`,
	Args: cobra.MaximumNArgs(1),
	RunE: runCaptions,
}

func init() {
	captionsCmd.Flags().StringVar(&captionsModel, "model", "moondream:1.8b", "Ollama vision model to use")
	captionsCmd.Flags().StringVar(&captionsOllamaURL, "ollama-url", "http://localhost:11434", "Ollama API URL")
	captionsCmd.Flags().IntVar(&captionsWorkers, "workers", 4, "Number of parallel workers")
	captionsCmd.Flags().BoolVar(&captionsTwoPass, "two-pass", false, "Use two-pass processing (fast + rich models)")
	captionsCmd.Flags().StringVar(&captionsRichModel, "rich-model", "qwen2.5vl:7b", "Rich model for two-pass processing")
	captionsCmd.Flags().StringVar(&captionsFrameData, "frame-data", "", "JSON file containing frame data")
}

// Update subcommand
var updateCmd = &cobra.Command{
	Use:   "update",
	Short: "Update screenscribe tools from GitHub",
	Long: `Downloads and installs the latest version of screenscribe from GitHub.

This will update the main scribe binary, backend scripts, and Fabric patterns
to the latest versions available on the main branch.

Example:
  scribe update`,
	RunE: func(cmd *cobra.Command, args []string) error {
		return runUpdate()
	},
}

// Uninstall subcommand
var uninstallCmd = &cobra.Command{
	Use:   "uninstall",
	Short: "Remove screenscribe tools from system",
	Long: `Removes scribe tools and Fabric patterns from the system.

This will remove the scribe binary, backend scripts, and associated
Fabric patterns from common installation directories.

Example:
  scribe uninstall`,
	RunE: func(cmd *cobra.Command, args []string) error {
		return runUninstall()
	},
}

// Implementation functions
func runAnalyze(cmd *cobra.Command, args []string) error {
	input := args[0]
	var videoFile string
	var isYoutube bool = isYouTubeURL(input)

	// Handle YouTube URLs
	if isYoutube {
		if verbose {
			fmt.Fprintf(os.Stderr, "Detected YouTube URL: %s\n", input)
		}
		
		// For YouTube transcript mode, we still need the video file for frames
		if youtubeTranscript && !skipFrames {
			// Download video for frame extraction
			if verbose {
				fmt.Fprintf(os.Stderr, "Downloading video for frame extraction...\n")
			}
			var err error
			videoFile, err = handleYouTubeURL(input, false) // Download video
			if err != nil {
				return fmt.Errorf("YouTube video download failed: %v", err)
			}
		} else if !youtubeTranscript {
			// Download video for both transcript and frames
			if verbose {
				fmt.Fprintf(os.Stderr, "Downloading video...\n")
			}
			var err error
			videoFile, err = handleYouTubeURL(input, false) // Download video
			if err != nil {
				return fmt.Errorf("YouTube video download failed: %v", err)
			}
		}
		// If skipFrames and youtubeTranscript, we don't need to download the video
	} else {
		// Regular file handling
		videoFile = input
		// Check if file exists
		if _, err := os.Stat(videoFile); os.IsNotExist(err) {
			return fmt.Errorf("file not found: %s", videoFile)
		}
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
		if isYoutube && youtubeTranscript {
			// Use YouTube's native transcript
			if verbose {
				fmt.Fprintf(os.Stderr, "Extracting YouTube transcript...\n")
			}
			
			transcriptResult, err = runYouTubeTranscribe(input)
			if err != nil {
				return fmt.Errorf("YouTube transcript extraction failed: %v", err)
			}
		} else {
			// Use Whisper transcription
			if verbose {
				fmt.Fprintf(os.Stderr, "Extracting transcript with Whisper...\n")
			}
			
			transcriptResult, err = runWhisperTranscribe(videoFile)
			if err != nil {
				return fmt.Errorf("transcript extraction failed: %v", err)
			}
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

	// Generate captions if requested
	var captionsResult *ProcessedCaptions
	if generateCaptions && !skipFrames && frameResult.FrameCount > 0 {
		if verbose {
			fmt.Fprintf(os.Stderr, "Generating visual captions with Ollama...\n")
		}
		
		captions, err := generateCaptionsForFrames(frameResult, transcriptResult)
		if err != nil {
			// Attempt graceful fallback
			fallback := AttemptCaptionFallback(err, frameResult.FrameCount, len(transcriptResult.Segments) > 0)
			
			if fallback.Success {
				if verbose {
					fmt.Fprintf(os.Stderr, "⚠️  %s\n", fallback.Message)
					fmt.Fprintf(os.Stderr, "Continuing with fallback strategy: %s\n", fallback.FallbackStrategy)
				}
				// Continue without captions but with fallback strategy noted
			} else {
				// Create error recovery for diagnostic info
				recovery := NewErrorRecovery("Caption Generation")
				recovery.AddError(err)
				
				if verbose {
					fmt.Fprintf(os.Stderr, "❌ Caption generation failed:\n")
					fmt.Fprintf(os.Stderr, "%s", recovery.CreateDiagnosticMessage())
				}
				
				// For non-verbose mode, show concise error
				if !verbose {
					fmt.Fprintf(os.Stderr, "Warning: Caption generation failed - %v\n", err)
				}
			}
		} else {
			captionsResult = captions
			if verbose {
				fmt.Fprintf(os.Stderr, "✅ Captions generated: %d key frames selected\n", len(captions.KeyFrames))
			}
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

	// Add captions to output if generated
	if captionsResult != nil {
		// Create extended analysis structure for trading strategy extraction
		extendedAnalysis := createTradingAnalysisOutput(analysis, *captionsResult)
		
		// Output extended JSON for Fabric pattern processing
		output, err := json.MarshalIndent(extendedAnalysis, "", "  ")
		if err != nil {
			return fmt.Errorf("failed to generate extended JSON output: %v", err)
		}
		
		fmt.Print(string(output))
	} else {
		// Output standard JSON for regular Fabric patterns
		output, err := json.MarshalIndent(analysis, "", "  ")
		if err != nil {
			return fmt.Errorf("failed to generate JSON output: %v", err)
		}
		
		fmt.Print(string(output))
	}

	if verbose {
		fmt.Fprintf(os.Stderr, "Analysis complete\n")
	}

	return nil
}

// TradingAnalysisOutput extends VideoAnalysisInput with caption data for trading strategy extraction
type TradingAnalysisOutput struct {
	Transcript TranscriptOutput    `json:"transcript"`
	Frames     FrameOutput        `json:"frames"`
	Captions   *ProcessedCaptions `json:"captions,omitempty"`
	Metadata   VideoMetadata      `json:"metadata"`
}

// generateCaptionsForFrames generates captions for video frames using Ollama
func generateCaptionsForFrames(frameResult FrameOutput, transcriptResult TranscriptOutput) (*ProcessedCaptions, error) {
	// Initialize error recovery
	recovery := NewErrorRecovery("Caption Generation")
	defer RecoverFromPanic("Caption Generation")
	
	// Validate configuration
	if validationErrors := ValidateConfiguration(); len(validationErrors) > 0 {
		for _, err := range validationErrors {
			recovery.AddError(err)
		}
		return nil, fmt.Errorf("configuration validation failed: %v", validationErrors[0])
	}
	
	// Initialize Ollama client
	client := NewOllamaClient(ollamaURL)
	
	// Check if model is available with timeout
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	
	available, err := client.IsModelAvailable(ctx, captionsModelFlag)
	if err != nil {
		recovery.AddError(err)
		return nil, err // Return the specific error type for fallback handling
	}
	if !available {
		err := &ModelNotFoundError{Model: captionsModelFlag, Available: []string{}}
		recovery.AddError(err)
		return nil, err
	}

	// Generate captions for all frames with timeout
	ctx, cancel = context.WithTimeout(context.Background(), 5*time.Minute)
	defer cancel()
	
	captions, err := client.CaptionFramesParallel(ctx, frameResult.Frames, captionsModelFlag, analyzeCaptionWorkers)
	if err != nil {
		recovery.AddError(err)
		
		// Check for timeout
		if ctx.Err() == context.DeadlineExceeded {
			timeoutErr := &ProcessingTimeoutError{
				Operation: "Caption Generation",
				Duration:  "5 minutes",
				MaxTime:   "5 minutes",
			}
			recovery.AddError(timeoutErr)
			return nil, timeoutErr
		}
		
		return nil, fmt.Errorf("caption generation failed: %w", err)
	}

	// Two-pass processing if enabled
	if twoPassCaptions && richModelFlag != captionsModelFlag {
		richAvailable, err := client.IsModelAvailable(ctx, richModelFlag)
		if err == nil && richAvailable {
			// Select key frames for rich processing
			frameSelector := NewFrameSelector()
			keyFrameData := frameSelector.SelectKeyFrames(captions, transcriptResult, 12)
			
			if len(keyFrameData) > 0 {
				// Convert back to FrameData for rich processing
				var keyFrames []FrameData
				for _, caption := range keyFrameData {
					// Find corresponding FrameData
					for _, frame := range frameResult.Frames {
						if fmt.Sprintf("frame_%04d.jpg", frame.FrameNumber) == caption.Frame {
							keyFrames = append(keyFrames, frame)
							break
						}
					}
				}
				
				if len(keyFrames) > 0 {
					richCaptions, err := client.CaptionFramesParallel(ctx, keyFrames, richModelFlag, analyzeCaptionWorkers/2)
					if err == nil {
						// Merge rich captions back
						captions = mergeRichCaptions(captions, richCaptions)
					}
				}
			}
		}
	}

	// Process captions using CaptionProcessor
	processor := NewCaptionProcessor()
	captionsOutput := CaptionsOutput{
		SourceFile:    frameResult.SourceFile,
		ProcessedAt:   time.Now().Unix(),
		TotalFrames:   frameResult.FrameCount,
		ProcessedTime: 0, // Will be set by processor
		Models:        []string{captionsModelFlag},
		Frames:        captions,
	}

	if twoPassCaptions {
		captionsOutput.Models = append(captionsOutput.Models, richModelFlag)
	}

	// Process captions for trading strategy extraction
	processed, err := processor.ProcessCaptions(captionsOutput, &transcriptResult, 4000) // 4K token limit for captions
	if err != nil {
		return nil, fmt.Errorf("caption processing failed: %w", err)
	}

	return processed, nil
}

// createTradingAnalysisOutput creates extended output structure for trading analysis
func createTradingAnalysisOutput(analysis VideoAnalysisInput, captions ProcessedCaptions) TradingAnalysisOutput {
	return TradingAnalysisOutput{
		Transcript: analysis.Transcript,
		Frames:     analysis.Frames,
		Captions:   &captions,
		Metadata:   analysis.Metadata,
	}
}

func runTranscribe(cmd *cobra.Command, args []string) error {
	videoFile := args[0]

	// Check if file exists
	if _, err := os.Stat(videoFile); os.IsNotExist(err) {
		return fmt.Errorf("file not found: %s", videoFile)
	}

	// Set global variables for transcription functions to use
	whisperModel = transcribeModel
	whisperBackend = transcribeBackend

	// Use the new Go-native transcription
	result, err := runWhisperTranscribe(videoFile)
	if err != nil {
		return fmt.Errorf("transcription failed: %v", err)
	}

	// Convert result to JSON and output
	output, err := json.MarshalIndent(result, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal output: %v", err)
	}

	// Output the JSON to stdout for piping to Fabric
	fmt.Print(string(output))
	
	return nil
}

func runFrames(cmd *cobra.Command, args []string) error {
	videoFile := args[0]

	// Check if file exists
	if _, err := os.Stat(videoFile); os.IsNotExist(err) {
		return fmt.Errorf("file not found: %s", videoFile)
	}

	// Validate format
	if framesFormat != "base64" && framesFormat != "paths" && framesFormat != "both" {
		return fmt.Errorf("invalid format '%s'. Must be 'base64', 'paths', or 'both'", framesFormat)
	}

	// Find the frame extraction script
	scriptPath, err := findFrameScript()
	if err != nil {
		return fmt.Errorf("could not find extract_frames.sh: %v", err)
	}

	// Build command arguments
	cmdArgs := []string{scriptPath}
	
	if framesInterval != 30 {
		cmdArgs = append(cmdArgs, "--interval", strconv.Itoa(framesInterval))
	}
	
	if framesFormat != "base64" {
		cmdArgs = append(cmdArgs, "--format", framesFormat)
	}
	
	if framesMaxFrames != 50 {
		cmdArgs = append(cmdArgs, "--max-frames", strconv.Itoa(framesMaxFrames))
	}
	
	if framesQuality != 2 {
		cmdArgs = append(cmdArgs, "--quality", strconv.Itoa(framesQuality))
	}
	
	if framesResize != "320x240" {
		cmdArgs = append(cmdArgs, "--resize", framesResize)
	}
	
	if verbose {
		cmdArgs = append(cmdArgs, "--verbose")
	}
	
	// Add video file as last argument
	cmdArgs = append(cmdArgs, videoFile)

	// Execute the shell script
	cmd2 := exec.Command("bash", cmdArgs...)
	cmd2.Stderr = os.Stderr
	
	output, err := cmd2.Output()
	if err != nil {
		return fmt.Errorf("frame extraction failed: %v", err)
	}

	// Output the JSON to stdout for piping to Fabric
	fmt.Print(string(output))
	
	return nil
}

// Helper functions (reused from video_analyze)
func isYouTubeURL(input string) bool {
	// Common YouTube URL patterns
	patterns := []string{
		`^https?://(www\.)?youtube\.com/watch\?v=`,
		`^https?://(www\.)?youtu\.be/`,
		`^https?://(www\.)?youtube\.com/embed/`,
		`^https?://(www\.)?youtube\.com/v/`,
		`^https?://(m\.)?youtube\.com/watch\?v=`,
	}
	
	for _, pattern := range patterns {
		matched, _ := regexp.MatchString(pattern, input)
		if matched {
			return true
		}
	}
	return false
}

func handleYouTubeURL(url string, useYouTubeTranscript bool) (string, error) {
	// Find youtube_helper executable
	youtubeCmd, err := findExecutable("youtube_helper.py")
	if err != nil {
		return "", fmt.Errorf("youtube_helper.py not found: %v\n\nTo use YouTube URLs, ensure yt-dlp is installed:\n  pip install yt-dlp\n\nIf you see this error, yt-dlp may need additional configuration or the URL may be invalid.", err)
	}

	// Build command arguments
	args := []string{url}
	
	if useYouTubeTranscript {
		args = append(args, "--transcript-only")
	}
	
	if verbose {
		args = append(args, "--verbose")
	}

	// Execute youtube_helper
	cmd := exec.Command("python3", append([]string{youtubeCmd}, args...)...)
	cmd.Stderr = os.Stderr
	
	output, err := cmd.Output()
	if err != nil {
		// Enhanced error message with yt-dlp troubleshooting
		return "", fmt.Errorf("YouTube processing failed: %v\n\nTroubleshooting steps:\n1. Install yt-dlp: pip install yt-dlp\n2. Update yt-dlp: pip install --upgrade yt-dlp\n3. Check URL validity: %s\n4. If using --youtube-transcript, ensure the video has captions available", err, url)
	}
	
	return strings.TrimSpace(string(output)), nil
}

func runWhisperTranscribe(videoFile string) (TranscriptOutput, error) {
	// Choose transcription backend based on platform and preference
	switch whisperBackend {
	case "mlx":
		return runMLXWhisperTranscribe(videoFile)
	case "faster-whisper":
		return runFasterWhisperTranscribe(videoFile)
	case "openai-whisper":
		return runOpenAIWhisperTranscribe(videoFile)
	default: // auto
		return runAutoWhisperTranscribe(videoFile)
	}
}

// runMLXWhisperTranscribe runs MLX Whisper for Apple Silicon GPU acceleration
func runMLXWhisperTranscribe(videoFile string) (TranscriptOutput, error) {
	var result TranscriptOutput

	// MLX whisper model mapping to HuggingFace repositories
	mlxModelMap := map[string]string{
		"tiny":     "mlx-community/whisper-tiny-mlx",
		"base":     "mlx-community/whisper-base-mlx",
		"small":    "mlx-community/whisper-small-mlx",
		"medium":   "mlx-community/whisper-medium-mlx",
		"large":    "mlx-community/whisper-large-v3-turbo", // Use fastest large model
		"large-v2": "mlx-community/whisper-large-v2-mlx",
		"large-v3": "mlx-community/whisper-large-v3-turbo", // Use fastest v3 model
	}

	modelRepo, exists := mlxModelMap[whisperModel]
	if !exists {
		modelRepo = mlxModelMap["base"] // fallback to base
	}

	// Build Python command to call MLX whisper directly
	pythonScript := fmt.Sprintf(`
import mlx_whisper
import json
import sys
import time

try:
	start_time = time.time()
	result = mlx_whisper.transcribe(
		"%s",
		path_or_hf_repo="%s",
		word_timestamps=True
	)
	
	# Format segments
	segments_list = []
	if "segments" in result:
		for i, segment in enumerate(result["segments"]):
			segment_dict = {
				"id": i,
				"start": segment.get("start", 0),
				"end": segment.get("end", 0),
				"text": segment.get("text", "").strip()
			}
			segments_list.append(segment_dict)
	
	output = {
		"text": result.get("text", ""),
		"segments": segments_list,
		"language": result.get("language", "unknown"),
		"duration": segments_list[-1]["end"] if segments_list else 0,
		"backend": "mlx-whisper",
		"source_file": "%s",
		"model": "%s",
		"timestamp": time.time()
	}
	
	if %s:
		print(f"MLX Whisper: Processed in {time.time() - start_time:.1f}s, {len(segments_list)} segments", file=sys.stderr)
	
	print(json.dumps(output, indent=2, ensure_ascii=False))

except ImportError as e:
	print(f"Error: MLX Whisper not available: {e}", file=sys.stderr)
	sys.exit(1)
except Exception as e:
	error_msg = str(e)
	if "Repository Not Found" in error_msg or "401 Client Error" in error_msg:
		print(f"Error: MLX model download failed: {error_msg}", file=sys.stderr)
		print("Try installing models with: python3 -c \"import mlx_whisper; mlx_whisper.transcribe('test.mp4', path_or_hf_repo='mlx-community/whisper-base-mlx')\"", file=sys.stderr)
	else:
		print(f"Error: MLX Whisper transcription failed: {e}", file=sys.stderr)
	sys.exit(1)
`, videoFile, modelRepo, videoFile, whisperModel, pythonBool(verbose))

	// Execute the Python script
	cmd := exec.Command("python3", "-c", pythonScript)
	if verbose {
		cmd.Stderr = os.Stderr
	}

	output, err := cmd.Output()
	if err != nil {
		return result, fmt.Errorf("MLX whisper transcription failed: %v", err)
	}

	// Parse JSON output
	if err := json.Unmarshal(output, &result); err != nil {
		return result, fmt.Errorf("failed to parse MLX whisper output: %v", err)
	}

	return result, nil
}

// runFasterWhisperTranscribe runs faster-whisper backend
func runFasterWhisperTranscribe(videoFile string) (TranscriptOutput, error) {
	var result TranscriptOutput

	pythonScript := fmt.Sprintf(`
import json
import sys
import time
import platform

try:
	from faster_whisper import WhisperModel
	
	# Configure device and compute type based on platform
	device = "auto"
	
	# Use appropriate compute type for Apple Silicon
	if platform.system() == "Darwin" and platform.machine() == "arm64":
		compute_type = "int8"  # On Apple Silicon, use int8 for faster-whisper
	else:
		compute_type = "float16"  # On other platforms, float16 works fine
	
	start_time = time.time()
	whisper_model = WhisperModel("%s", device=device, compute_type=compute_type)
	
	segments, info = whisper_model.transcribe(
		"%s",
		vad_filter=True,
		vad_parameters=dict(min_silence_duration_ms=500)
	)
	
	# Convert segments to list
	segments_list = []
	full_text = ""
	
	for i, segment in enumerate(segments):
		segment_dict = {
			"id": i,
			"start": segment.start,
			"end": segment.end,
			"text": segment.text.strip()
		}
		segments_list.append(segment_dict)
		full_text += segment.text.strip() + " "
	
	output = {
		"text": full_text.strip(),
		"segments": segments_list,
		"language": info.language,
		"duration": segments_list[-1]["end"] if segments_list else 0,
		"backend": "faster-whisper",
		"source_file": "%s",
		"model": "%s",
		"timestamp": time.time()
	}
	
	if %s:
		print(f"Faster Whisper: Processed in {time.time() - start_time:.1f}s, {len(segments_list)} segments", file=sys.stderr)
	
	print(json.dumps(output, indent=2, ensure_ascii=False))

except ImportError:
	print("Error: faster-whisper not available", file=sys.stderr)
	sys.exit(1)
except Exception as e:
	print(f"Error: Faster whisper transcription failed: {e}", file=sys.stderr)
	sys.exit(1)
`, whisperModel, videoFile, videoFile, whisperModel, pythonBool(verbose))

	// Execute the Python script
	cmd := exec.Command("python3", "-c", pythonScript)
	if verbose {
		cmd.Stderr = os.Stderr
	}

	output, err := cmd.Output()
	if err != nil {
		return result, fmt.Errorf("faster-whisper transcription failed: %v", err)
	}

	// Parse JSON output
	if err := json.Unmarshal(output, &result); err != nil {
		return result, fmt.Errorf("failed to parse faster-whisper output: %v", err)
	}

	return result, nil
}

// runOpenAIWhisperTranscribe runs original OpenAI Whisper (fallback)
func runOpenAIWhisperTranscribe(videoFile string) (TranscriptOutput, error) {
	var result TranscriptOutput

	pythonScript := fmt.Sprintf(`
import json
import sys
import time

try:
	import whisper
	
	start_time = time.time()
	whisper_model = whisper.load_model("%s")
	result = whisper_model.transcribe("%s")
	
	output = {
		"text": result["text"],
		"segments": result["segments"],
		"language": result["language"],
		"duration": result["segments"][-1]["end"] if result["segments"] else 0,
		"backend": "openai-whisper",
		"source_file": "%s",
		"model": "%s", 
		"timestamp": time.time()
	}
	
	if %s:
		print(f"OpenAI Whisper: Processed in {time.time() - start_time:.1f}s, {len(result['segments'])} segments", file=sys.stderr)
	
	print(json.dumps(output, indent=2, ensure_ascii=False))

except ImportError:
	print("Error: openai-whisper not available", file=sys.stderr)
	sys.exit(1)
except Exception as e:
	print(f"Error: OpenAI whisper transcription failed: {e}", file=sys.stderr)
	sys.exit(1)
`, whisperModel, videoFile, videoFile, whisperModel, pythonBool(verbose))

	// Execute the Python script
	cmd := exec.Command("python3", "-c", pythonScript)
	if verbose {
		cmd.Stderr = os.Stderr
	}

	output, err := cmd.Output()
	if err != nil {
		return result, fmt.Errorf("OpenAI whisper transcription failed: %v", err)
	}

	// Parse JSON output
	if err := json.Unmarshal(output, &result); err != nil {
		return result, fmt.Errorf("failed to parse OpenAI whisper output: %v", err)
	}

	return result, nil
}

// runAutoWhisperTranscribe auto-selects best transcription backend for current platform
func runAutoWhisperTranscribe(videoFile string) (TranscriptOutput, error) {
	// Try MLX first on Apple Silicon for best performance
	if runtime.GOOS == "darwin" && runtime.GOARCH == "arm64" {
		result, err := runMLXWhisperTranscribe(videoFile)
		if err == nil {
			return result, nil
		}
		if verbose {
			fmt.Fprintf(os.Stderr, "MLX failed, falling back to faster-whisper: %v\n", err)
		}
	}
	
	// Fall back to faster-whisper (works on all platforms)
	result, err := runFasterWhisperTranscribe(videoFile)
	if err == nil {
		return result, nil
	}
	if verbose {
		fmt.Fprintf(os.Stderr, "Faster-whisper failed, falling back to OpenAI whisper: %v\n", err)
	}
	
	// Final fallback to OpenAI Whisper
	return runOpenAIWhisperTranscribe(videoFile)
}

func runYouTubeTranscribe(youtubeURL string) (TranscriptOutput, error) {
	var result TranscriptOutput

	// Find youtube_helper executable
	youtubeCmd, err := findExecutable("youtube_helper.py")
	if err != nil {
		return result, fmt.Errorf("youtube_helper.py not found: %v\n\nTo use YouTube transcripts, ensure yt-dlp is installed:\n  pip install yt-dlp", err)
	}

	// Build command arguments for transcript extraction
	args := []string{youtubeURL, "--transcript-only"}
	
	if verbose {
		args = append(args, "--verbose")
	}

	// Execute youtube_helper for transcript extraction
	cmd := exec.Command("python3", append([]string{youtubeCmd}, args...)...)
	cmd.Stderr = os.Stderr
	
	output, err := cmd.Output()
	if err != nil {
		return result, fmt.Errorf("YouTube transcript extraction failed: %v\n\nPossible causes:\n1. Video has no captions/transcript available\n2. yt-dlp needs updating: pip install --upgrade yt-dlp\n3. YouTube URL is invalid or private\n4. Network connectivity issues", err)
	}

	// Parse JSON output
	if err := json.Unmarshal(output, &result); err != nil {
		return result, fmt.Errorf("failed to parse YouTube transcript output: %v", err)
	}

	// Set backend identifier
	result.Backend = "youtube-transcript"

	return result, nil
}

func runVideoFrames(videoFile string) (FrameOutput, error) {
	var result FrameOutput

	// Find extract_frames script
	scriptPath, err := findFrameScript()
	if err != nil {
		return result, fmt.Errorf("extract_frames.sh not found: %v", err)
	}

	// Build command arguments
	args := []string{scriptPath}
	
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
	
	// Add video file as last argument
	args = append(args, videoFile)

	// Execute extract_frames script
	cmd := exec.Command("bash", args...)
	cmd.Stderr = os.Stderr
	
	output, err := cmd.Output()
	if err != nil {
		return result, fmt.Errorf("frame extraction failed: %v", err)
	}

	// Parse JSON output
	if err := json.Unmarshal(output, &result); err != nil {
		return result, fmt.Errorf("failed to parse frame extraction output: %v", err)
	}

	return result, nil
}

func runCaptions(cmd *cobra.Command, args []string) error {
	startTime := time.Now()
	
	// Initialize Ollama client
	client := NewOllamaClient(captionsOllamaURL)
	
	var frames []FrameData
	var sourceFile string
	var err error

	// Determine input source
	if len(args) == 1 {
		input := args[0]
		
		// Check if input is a JSON file or video file
		if filepath.Ext(input) == ".json" || captionsFrameData != "" {
			// Load frames from JSON
			var jsonPath string
			if captionsFrameData != "" {
				jsonPath = captionsFrameData
			} else {
				jsonPath = input
			}
			
			frames, sourceFile, err = loadFramesFromJSON(jsonPath)
			if err != nil {
				return fmt.Errorf("failed to load frames from JSON: %v", err)
			}
		} else {
			// Extract frames from video first
			if verbose {
				fmt.Fprintf(os.Stderr, "Extracting frames from video: %s\n", input)
			}
			
			frameResult, err := runVideoFrames(input)
			if err != nil {
				return fmt.Errorf("frame extraction failed: %v", err)
			}
			
			frames = frameResult.Frames
			sourceFile = input
		}
	} else {
		// Read from stdin (frame JSON)
		if verbose {
			fmt.Fprintf(os.Stderr, "Reading frame data from stdin\n")
		}
		
		frames, sourceFile, err = loadFramesFromStdin()
		if err != nil {
			return fmt.Errorf("failed to read frames from stdin: %v", err)
		}
	}

	if len(frames) == 0 {
		return fmt.Errorf("no frames to process")
	}

	if verbose {
		fmt.Fprintf(os.Stderr, "Processing %d frames with model: %s\n", len(frames), captionsModel)
	}

	// Check if Ollama is available
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	
	available, err := client.IsModelAvailable(ctx, captionsModel)
	if err != nil {
		return fmt.Errorf("failed to check Ollama availability: %v", err)
	}
	if !available {
		return fmt.Errorf("model %s is not available in Ollama. Please run: ollama pull %s", captionsModel, captionsModel)
	}

	// Process frames with progress tracking
	ctx = context.Background()
	if verbose {
		fmt.Fprintf(os.Stderr, "Starting caption generation with %d workers...\n", captionsWorkers)
	}
	
	captions, err := client.CaptionFramesParallel(ctx, frames, captionsModel, captionsWorkers)
	if err != nil {
		return fmt.Errorf("caption generation failed: %v", err)
	}

	// Two-pass processing if enabled
	if captionsTwoPass && captionsRichModel != captionsModel {
		if verbose {
			fmt.Fprintf(os.Stderr, "Starting rich pass with model: %s\n", captionsRichModel)
		}
		
		// Check if rich model is available
		available, err := client.IsModelAvailable(ctx, captionsRichModel)
		if err != nil {
			fmt.Fprintf(os.Stderr, "Warning: Failed to check rich model availability: %v\n", err)
		} else if available {
			// Select key frames for rich processing (limit to top 25% by confidence)
			keyFrames := selectKeyFramesForRichPass(frames, captions, 0.25)
			
			if len(keyFrames) > 0 {
				richCaptions, err := client.CaptionFramesParallel(ctx, keyFrames, captionsRichModel, captionsWorkers/2)
				if err != nil {
					fmt.Fprintf(os.Stderr, "Warning: Rich pass failed: %v\n", err)
				} else {
					// Merge rich captions back
					captions = mergeRichCaptions(captions, richCaptions)
					if verbose {
						fmt.Fprintf(os.Stderr, "Rich pass completed for %d key frames\n", len(richCaptions))
					}
				}
			}
		} else {
			fmt.Fprintf(os.Stderr, "Warning: Rich model %s not available, skipping two-pass\n", captionsRichModel)
		}
	}

	// Create output
	output := CaptionsOutput{
		SourceFile:    sourceFile,
		ProcessedAt:   time.Now().Unix(),
		TotalFrames:   len(frames),
		ProcessedTime: time.Since(startTime).Seconds(),
		Models:        []string{captionsModel},
		Frames:        captions,
	}
	
	if captionsTwoPass {
		output.Models = append(output.Models, captionsRichModel)
	}

	// Output JSON
	jsonOutput, err := json.MarshalIndent(output, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal output: %v", err)
	}

	fmt.Print(string(jsonOutput))
	
	if verbose {
		fmt.Fprintf(os.Stderr, "Caption generation completed in %.2f seconds\n", time.Since(startTime).Seconds())
	}

	return nil
}

// loadFramesFromJSON loads frame data from a JSON file
func loadFramesFromJSON(jsonPath string) ([]FrameData, string, error) {
	data, err := os.ReadFile(jsonPath)
	if err != nil {
		return nil, "", fmt.Errorf("failed to read JSON file: %v", err)
	}

	// Try to parse as FrameOutput first
	var frameOutput FrameOutput
	if err := json.Unmarshal(data, &frameOutput); err == nil {
		return frameOutput.Frames, frameOutput.SourceFile, nil
	}

	// Try to parse as VideoAnalysisInput
	var analysisInput VideoAnalysisInput
	if err := json.Unmarshal(data, &analysisInput); err == nil {
		return analysisInput.Frames.Frames, analysisInput.Frames.SourceFile, nil
	}

	return nil, "", fmt.Errorf("unable to parse JSON as frame data")
}

// loadFramesFromStdin loads frame data from stdin
func loadFramesFromStdin() ([]FrameData, string, error) {
	data, err := io.ReadAll(os.Stdin)
	if err != nil {
		return nil, "", fmt.Errorf("failed to read from stdin: %v", err)
	}

	// Try to parse as FrameOutput first
	var frameOutput FrameOutput
	if err := json.Unmarshal(data, &frameOutput); err == nil {
		return frameOutput.Frames, frameOutput.SourceFile, nil
	}

	// Try to parse as VideoAnalysisInput  
	var analysisInput VideoAnalysisInput
	if err := json.Unmarshal(data, &analysisInput); err == nil {
		return analysisInput.Frames.Frames, analysisInput.Frames.SourceFile, nil
	}

	return nil, "", fmt.Errorf("unable to parse stdin as frame data")
}

// selectKeyFramesForRichPass selects the most important frames for rich processing
func selectKeyFramesForRichPass(frames []FrameData, captions []FrameCaption, topPercentage float64) []FrameData {
	if len(captions) == 0 {
		return []FrameData{}
	}

	// Create a map for quick lookup
	captionMap := make(map[string]FrameCaption)
	for _, caption := range captions {
		captionMap[caption.Frame] = caption
	}

	// Sort frames by caption confidence
	type frameWithConfidence struct {
		frame      FrameData
		confidence float64
	}
	
	var framesWithConf []frameWithConfidence
	for _, frame := range frames {
		frameKey := fmt.Sprintf("frame_%04d.jpg", frame.FrameNumber)
		if caption, exists := captionMap[frameKey]; exists {
			framesWithConf = append(framesWithConf, frameWithConfidence{
				frame:      frame,
				confidence: caption.Confidence,
			})
		}
	}

	// Sort by confidence descending
	for i := 0; i < len(framesWithConf)-1; i++ {
		for j := i + 1; j < len(framesWithConf); j++ {
			if framesWithConf[i].confidence < framesWithConf[j].confidence {
				framesWithConf[i], framesWithConf[j] = framesWithConf[j], framesWithConf[i]
			}
		}
	}

	// Select top percentage
	numSelected := int(float64(len(framesWithConf)) * topPercentage)
	if numSelected < 1 {
		numSelected = 1
	}
	if numSelected > len(framesWithConf) {
		numSelected = len(framesWithConf)
	}

	var selectedFrames []FrameData
	for i := 0; i < numSelected; i++ {
		selectedFrames = append(selectedFrames, framesWithConf[i].frame)
	}

	return selectedFrames
}

// mergeRichCaptions merges rich captions back into the main caption set
func mergeRichCaptions(fastCaptions []FrameCaption, richCaptions []FrameCaption) []FrameCaption {
	// Create a map for quick lookup of rich captions
	richMap := make(map[string]FrameCaption)
	for _, richCaption := range richCaptions {
		richMap[richCaption.Frame] = richCaption
	}

	// Replace fast captions with rich ones where available
	var merged []FrameCaption
	for _, fastCaption := range fastCaptions {
		if richCaption, exists := richMap[fastCaption.Frame]; exists {
			merged = append(merged, richCaption)
		} else {
			merged = append(merged, fastCaption)
		}
	}

	return merged
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

// findWhisperScript function removed - now using native Go MLX implementation

func findFrameScript() (string, error) {
	// Try to find the extract_frames.sh script in various locations
	possiblePaths := []string{
		// Relative to current executable
		filepath.Join(filepath.Dir(os.Args[0]), "..", "scripts", "extract_frames.sh"),
		// In the same directory as executable
		filepath.Join(filepath.Dir(os.Args[0]), "extract_frames.sh"),
		// In PATH
		"extract_frames.sh",
		// Common installation locations
		"/usr/local/bin/extract_frames.sh",
		"/usr/bin/extract_frames.sh",
		// User's home directory
		filepath.Join(os.Getenv("HOME"), ".local", "bin", "extract_frames.sh"),
	}

	// Also try to find it relative to the Go module
	if goPath := os.Getenv("GOPATH"); goPath != "" {
		possiblePaths = append(possiblePaths, 
			filepath.Join(goPath, "src", "github.com", "screenscribe", "fabric-extension", "scripts", "extract_frames.sh"))
	}

	for _, path := range possiblePaths {
		if _, err := os.Stat(path); err == nil {
			return path, nil
		}
	}

	// Try to find using which command
	cmd := exec.Command("which", "extract_frames.sh")
	if output, err := cmd.Output(); err == nil {
		path := strings.TrimSpace(string(output))
		if path != "" {
			return path, nil
		}
	}

	return "", fmt.Errorf("extract_frames.sh not found in any expected location")
}

func runUpdate() error {
	fmt.Println("🔄 Updating scribe tools from GitHub...")
	
	// Create temporary directory for download
	tmpDir, err := os.MkdirTemp("", "screenscribe-update-*")
	if err != nil {
		return fmt.Errorf("failed to create temp directory: %v", err)
	}
	defer os.RemoveAll(tmpDir)
	
	// Download the repository
	repoURL := "https://github.com/grimmolf/screenscribe/archive/main.zip"
	zipPath := filepath.Join(tmpDir, "screenscribe.zip")
	
	fmt.Println("📥 Downloading latest version...")
	resp, err := http.Get(repoURL)
	if err != nil {
		return fmt.Errorf("failed to download repository: %v", err)
	}
	defer resp.Body.Close()
	
	zipFile, err := os.Create(zipPath)
	if err != nil {
		return fmt.Errorf("failed to create zip file: %v", err)
	}
	defer zipFile.Close()
	
	_, err = io.Copy(zipFile, resp.Body)
	if err != nil {
		return fmt.Errorf("failed to save zip file: %v", err)
	}
	zipFile.Close()
	
	// Extract the zip
	fmt.Println("📦 Extracting...")
	cmd := exec.Command("unzip", "-q", zipPath, "-d", tmpDir)
	if err := cmd.Run(); err != nil {
		return fmt.Errorf("failed to extract zip: %v", err)
	}
	
	// Change to the extracted directory
	fabricDir := filepath.Join(tmpDir, "screenscribe-main", "fabric-extension")
	if _, err := os.Stat(fabricDir); os.IsNotExist(err) {
		return fmt.Errorf("fabric-extension directory not found in downloaded archive")
	}
	
	// Build and install
	fmt.Println("🔨 Building updated tools...")
	makeCmd := exec.Command("make", "build")
	makeCmd.Dir = fabricDir
	makeCmd.Stdout = os.Stdout
	makeCmd.Stderr = os.Stderr
	if err := makeCmd.Run(); err != nil {
		return fmt.Errorf("build failed: %v", err)
	}
	
	fmt.Println("📁 Installing to ~/.local/bin/...")
	installCmd := exec.Command("make", "install")
	installCmd.Dir = fabricDir
	installCmd.Stdout = os.Stdout
	installCmd.Stderr = os.Stderr
	if err := installCmd.Run(); err != nil {
		return fmt.Errorf("installation failed: %v", err)
	}
	
	// Copy patterns
	patternsDir := filepath.Join(fabricDir, "patterns")
	fabricPatternsDir := filepath.Join(os.Getenv("HOME"), ".config", "fabric", "patterns")
	
	if _, err := os.Stat(patternsDir); err == nil {
		fmt.Println("🧩 Updating Fabric patterns...")
		copyCmd := exec.Command("cp", "-r", patternsDir+"/.", fabricPatternsDir+"/")
		if err := copyCmd.Run(); err != nil {
			fmt.Printf("⚠️  Warning: Failed to copy patterns: %v\n", err)
		}
	}
	
	fmt.Println("✅ Update completed successfully!")
	fmt.Println("💡 You may need to restart your terminal or run: hash -r")
	
	return nil
}

func runUninstall() error {
	fmt.Println("🗑️  Uninstalling scribe tools...")
	
	// List of tools to remove
	tools := []string{
		"scribe",
		"whisper_wrapper.py",
		"extract_frames.sh",
		"youtube_helper.py",
	}
	
	// Installation directories to check
	binDirs := []string{
		filepath.Join(os.Getenv("HOME"), ".local", "bin"),
		"/usr/local/bin",
		"/usr/bin",
	}
	
	removed := false
	for _, binDir := range binDirs {
		for _, tool := range tools {
			toolPath := filepath.Join(binDir, tool)
			if _, err := os.Stat(toolPath); err == nil {
				fmt.Printf("🗑️  Removing %s\n", toolPath)
				if err := os.Remove(toolPath); err != nil {
					fmt.Printf("⚠️  Warning: Failed to remove %s: %v\n", toolPath, err)
				} else {
					removed = true
				}
			}
		}
	}
	
	// Remove Fabric patterns
	fabricPatternsDir := filepath.Join(os.Getenv("HOME"), ".config", "fabric", "patterns")
	videoPatterns := []string{
		"analyze_video_content",
		"extract_code_from_video", 
		"analyze_trading_video",
		"extract_technical_analysis",
		"extract_trading_strategy",
		"analyze_market_commentary",
	}
	
	for _, pattern := range videoPatterns {
		patternDir := filepath.Join(fabricPatternsDir, pattern)
		if _, err := os.Stat(patternDir); err == nil {
			fmt.Printf("🧩 Removing Fabric pattern: %s\n", pattern)
			if err := os.RemoveAll(patternDir); err != nil {
				fmt.Printf("⚠️  Warning: Failed to remove pattern %s: %v\n", pattern, err)
			} else {
				removed = true
			}
		}
	}
	
	if removed {
		fmt.Println("✅ Uninstallation completed!")
		fmt.Println("💡 You may need to restart your terminal or run: hash -r")
	} else {
		fmt.Println("ℹ️  No scribe tools found to remove")
	}
	
	return nil
}

func main() {
	if err := rootCmd.Execute(); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
}