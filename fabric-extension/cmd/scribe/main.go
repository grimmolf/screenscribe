package main

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
	"time"

	"github.com/spf13/cobra"
)

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

// Global flags
var verbose bool

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
  scribe uninstall   # Remove scribe from system`,
	Version: "2.0.0",
}

func init() {
	rootCmd.PersistentFlags().BoolVarP(&verbose, "verbose", "v", false, "Verbose output")
	
	// Add subcommands
	rootCmd.AddCommand(analyzeCmd)
	rootCmd.AddCommand(transcribeCmd)
	rootCmd.AddCommand(framesCmd)
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
)

var analyzeCmd = &cobra.Command{
	Use:   "analyze [video_file_or_youtube_url]",
	Short: "Complete video analysis with transcript and frames",
	Long: `Performs comprehensive video analysis by extracting both transcript and frames
from videos for complete analysis. Supports local files and YouTube URLs.

This command orchestrates both transcription and frame extraction to provide
complete video analysis data that can be piped to Fabric patterns.

Examples:
  scribe analyze video.mp4 | fabric -p analyze_video_content
  scribe analyze --whisper-model large lecture.mp4 | fabric -p summarize_lecture
  scribe analyze --frame-interval 60 tutorial.mp4 | fabric -p extract_code_from_video
  scribe analyze --skip-frames audio.mp3 | fabric -p summarize_audio

YouTube examples:
  scribe analyze "https://www.youtube.com/watch?v=VIDEO_ID" | fabric -p analyze_video_content
  scribe analyze --youtube-transcript "https://youtu.be/VIDEO_ID" | fabric -p summarize_lecture
  scribe analyze --frame-interval 120 "https://youtube.com/watch?v=VIDEO_ID" | fabric -p extract_code_from_video
  
Trading-specific examples:
  scribe analyze trading_tutorial.mp4 | fabric -p analyze_trading_video
  scribe analyze --frame-interval 45 chart_analysis.mp4 | fabric -p extract_technical_analysis`,
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

func runTranscribe(cmd *cobra.Command, args []string) error {
	videoFile := args[0]

	// Check if file exists
	if _, err := os.Stat(videoFile); os.IsNotExist(err) {
		return fmt.Errorf("file not found: %s", videoFile)
	}

	// Find the Python wrapper script
	scriptPath, err := findWhisperScript()
	if err != nil {
		return fmt.Errorf("could not find whisper_wrapper.py: %v", err)
	}

	// Build command arguments
	cmdArgs := []string{scriptPath, videoFile}
	
	if transcribeModel != "base" {
		cmdArgs = append(cmdArgs, "--model", transcribeModel)
	}
	
	if transcribeLanguage != "" {
		cmdArgs = append(cmdArgs, "--language", transcribeLanguage)
	}
	
	if transcribeBackend != "auto" {
		cmdArgs = append(cmdArgs, "--backend", transcribeBackend)
	}
	
	if verbose {
		cmdArgs = append(cmdArgs, "--verbose")
	}

	// Execute the Python wrapper
	cmd2 := exec.Command("python3", cmdArgs...)
	cmd2.Stderr = os.Stderr
	
	output, err := cmd2.Output()
	if err != nil {
		return fmt.Errorf("transcription failed: %v", err)
	}

	// Parse and validate JSON output
	var result TranscriptOutput
	if err := json.Unmarshal(output, &result); err != nil {
		// If JSON parsing fails, output the raw result (might be error message)
		fmt.Print(string(output))
		return nil
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
	var result TranscriptOutput

	// Find whisper_wrapper script
	scriptPath, err := findWhisperScript()
	if err != nil {
		return result, fmt.Errorf("whisper_wrapper.py not found: %v", err)
	}

	// Build command arguments
	args := []string{scriptPath, videoFile}
	
	if whisperModel != "base" {
		args = append(args, "--model", whisperModel)
	}
	
	if whisperBackend != "auto" {
		args = append(args, "--backend", whisperBackend)
	}
	
	if verbose {
		args = append(args, "--verbose")
	}

	// Execute whisper_wrapper
	cmd := exec.Command("python3", args...)
	cmd.Stderr = os.Stderr
	
	output, err := cmd.Output()
	if err != nil {
		return result, fmt.Errorf("whisper transcription failed: %v", err)
	}

	// Parse JSON output
	if err := json.Unmarshal(output, &result); err != nil {
		return result, fmt.Errorf("failed to parse whisper output: %v", err)
	}

	return result, nil
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

func findWhisperScript() (string, error) {
	// Try to find the whisper_wrapper.py script in various locations
	possiblePaths := []string{
		// Relative to current executable
		filepath.Join(filepath.Dir(os.Args[0]), "..", "scripts", "whisper_wrapper.py"),
		// In the same directory as executable
		filepath.Join(filepath.Dir(os.Args[0]), "whisper_wrapper.py"),
		// In PATH
		"whisper_wrapper.py",
		// Common installation locations
		"/usr/local/bin/whisper_wrapper.py",
		"/usr/bin/whisper_wrapper.py",
		// User's home directory
		filepath.Join(os.Getenv("HOME"), ".local", "bin", "whisper_wrapper.py"),
	}

	// Also try to find it relative to the Go module
	if goPath := os.Getenv("GOPATH"); goPath != "" {
		possiblePaths = append(possiblePaths, 
			filepath.Join(goPath, "src", "github.com", "screenscribe", "fabric-extension", "scripts", "whisper_wrapper.py"))
	}

	for _, path := range possiblePaths {
		if _, err := os.Stat(path); err == nil {
			return path, nil
		}
	}

	// Try to find using which/where command
	cmd := exec.Command("which", "whisper_wrapper.py")
	if output, err := cmd.Output(); err == nil {
		path := strings.TrimSpace(string(output))
		if path != "" {
			return path, nil
		}
	}

	return "", fmt.Errorf("whisper_wrapper.py not found in any expected location")
}

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