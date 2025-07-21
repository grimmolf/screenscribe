package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"

	"github.com/spf13/cobra"
)

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

var (
	interval   int
	format     string
	maxFrames  int
	quality    int
	resize     string
	verbose    bool
)

var rootCmd = &cobra.Command{
	Use:   "video_frames [video_file]",
	Short: "Frame extraction helper for Fabric integration",
	Long: `A Fabric helper tool that extracts frames from videos at specified intervals.
	
This tool integrates with the Fabric AI framework by outputting JSON
that can be piped to Fabric patterns for video analysis.

Examples:
  video_frames video.mp4 | fabric -p analyze_frames
  video_frames --interval 60 lecture.mp4 | fabric -p extract_visual_content
  video_frames --format both tutorial.mp4 | fabric -p analyze_video_content`,
	Args: cobra.ExactArgs(1),
	RunE: extractFrames,
}

func init() {
	rootCmd.Flags().IntVarP(&interval, "interval", "i", 30, "Frame extraction interval in seconds")
	rootCmd.Flags().StringVarP(&format, "format", "f", "base64", "Output format: base64, paths, or both")
	rootCmd.Flags().IntVarP(&maxFrames, "max-frames", "m", 50, "Maximum number of frames to extract")
	rootCmd.Flags().IntVarP(&quality, "quality", "q", 2, "JPEG quality 1-5, 1=best, 5=worst")
	rootCmd.Flags().StringVarP(&resize, "resize", "r", "320x240", "Resize frames to WxH")
	rootCmd.Flags().BoolVarP(&verbose, "verbose", "v", false, "Verbose output")
}

func extractFrames(cmd *cobra.Command, args []string) error {
	videoFile := args[0]

	// Check if file exists
	if _, err := os.Stat(videoFile); os.IsNotExist(err) {
		return fmt.Errorf("file not found: %s", videoFile)
	}

	// Validate format
	if format != "base64" && format != "paths" && format != "both" {
		return fmt.Errorf("invalid format '%s'. Must be 'base64', 'paths', or 'both'", format)
	}

	// Find the frame extraction script
	scriptPath, err := findFrameScript()
	if err != nil {
		return fmt.Errorf("could not find extract_frames.sh: %v", err)
	}

	// Build command arguments
	cmdArgs := []string{scriptPath}
	
	if interval != 30 {
		cmdArgs = append(cmdArgs, "--interval", strconv.Itoa(interval))
	}
	
	if format != "base64" {
		cmdArgs = append(cmdArgs, "--format", format)
	}
	
	if maxFrames != 50 {
		cmdArgs = append(cmdArgs, "--max-frames", strconv.Itoa(maxFrames))
	}
	
	if quality != 2 {
		cmdArgs = append(cmdArgs, "--quality", strconv.Itoa(quality))
	}
	
	if resize != "320x240" {
		cmdArgs = append(cmdArgs, "--resize", resize)
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

func main() {
	if err := rootCmd.Execute(); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
}