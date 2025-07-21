package main

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"

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

var (
	model    string
	language string
	backend  string
	verbose  bool
)

var rootCmd = &cobra.Command{
	Use:   "whisper_transcribe [video_file]",
	Short: "Whisper transcription helper for Fabric integration",
	Long: `A Fabric helper tool that transcribes video/audio files using Whisper.
	
This tool integrates with the Fabric AI framework by outputting JSON
that can be piped to Fabric patterns for video analysis.

Examples:
  whisper_transcribe video.mp4 | fabric -p analyze_video_content
  whisper_transcribe --model large lecture.mp4 | fabric -p summarize_lecture
  whisper_transcribe --backend mlx tutorial.mp4 | fabric -p extract_code_from_video`,
	Args: cobra.ExactArgs(1),
	RunE: transcribeVideo,
}

func init() {
	rootCmd.Flags().StringVarP(&model, "model", "m", "base", "Whisper model size (tiny, base, small, medium, large, large-v2, large-v3)")
	rootCmd.Flags().StringVarP(&language, "language", "l", "", "Force specific language (optional)")
	rootCmd.Flags().StringVar(&backend, "backend", "auto", "Transcription backend (auto, mlx, faster-whisper, openai-whisper)")
	rootCmd.Flags().BoolVarP(&verbose, "verbose", "v", false, "Verbose output")
}

func transcribeVideo(cmd *cobra.Command, args []string) error {
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
	
	if model != "base" {
		cmdArgs = append(cmdArgs, "--model", model)
	}
	
	if language != "" {
		cmdArgs = append(cmdArgs, "--language", language)
	}
	
	if backend != "auto" {
		cmdArgs = append(cmdArgs, "--backend", backend)
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

func main() {
	if err := rootCmd.Execute(); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
}