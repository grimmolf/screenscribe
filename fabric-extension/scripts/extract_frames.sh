#!/bin/bash
#
# Frame extraction script for Fabric integration
# Extracts frames from video at specified intervals and outputs JSON
#

set -e

# Default values
INTERVAL=30
OUTPUT_FORMAT="base64"
MAX_FRAMES=50
QUALITY=2  # 1=highest, 5=lowest
RESIZE="320x240"

# Function to show usage
usage() {
    cat << EOF
Usage: $0 [OPTIONS] VIDEO_FILE

Extract frames from video and output JSON for Fabric processing.

OPTIONS:
    -i, --interval SECONDS    Frame extraction interval (default: 30)
    -f, --format FORMAT       Output format: base64, paths, or both (default: base64)
    -m, --max-frames NUM      Maximum number of frames to extract (default: 50)
    -q, --quality LEVEL       JPEG quality 1-5, 1=best, 5=worst (default: 2)
    -r, --resize WxH          Resize frames to WxH (default: 320x240)
    -v, --verbose             Verbose output
    -h, --help                Show this help

EXAMPLES:
    $0 video.mp4
    $0 -i 45 -f both video.mp4
    $0 --interval 60 --max-frames 20 lecture.mov

OUTPUT:
    JSON object with frame data for piping to Fabric patterns
EOF
}

# Function to get video metadata
get_video_info() {
    local video_file="$1"
    
    ffprobe -v quiet -print_format json -show_streams -show_format "$video_file" 2>/dev/null | \
        jq -r '.format.duration // .streams[0].duration // "0"'
}

# Function to extract frames
extract_frames() {
    local video_file="$1"
    local output_dir="$2"
    local interval="$3"
    local max_frames="$4"
    local quality="$5"
    local resize="$6"
    local verbose="$7"
    
    # Calculate quality setting for ffmpeg (inverted scale)
    local ffmpeg_quality=$((6 - quality))
    
    if [[ "$verbose" == "true" ]]; then
        echo "Extracting frames every ${interval}s, max ${max_frames} frames..." >&2
    fi
    
    # Extract frames using ffmpeg
    ffmpeg -i "$video_file" \
        -vf "fps=1/${interval},scale=${resize}" \
        -q:v $ffmpeg_quality \
        -frames:v $max_frames \
        "$output_dir/frame_%04d.jpg" \
        -y 2>/dev/null || {
        echo "Error: Failed to extract frames from $video_file" >&2
        return 1
    }
    
    # Count extracted frames
    ls "$output_dir"/frame_*.jpg 2>/dev/null | wc -l | tr -d ' '
}

# Function to convert frame to base64
frame_to_base64() {
    local frame_path="$1"
    base64 < "$frame_path"
}

# Function to get frame timestamp
get_frame_timestamp() {
    local frame_number="$1"
    local interval="$2"
    
    echo "$(( (frame_number - 1) * interval ))"
}

# Main processing function
process_video() {
    local video_file="$1"
    local interval="$2"
    local output_format="$3"
    local max_frames="$4"
    local quality="$5"
    local resize="$6"
    local verbose="$7"
    
    # Create temporary directory
    local temp_dir
    temp_dir=$(mktemp -d)
    trap "rm -rf '$temp_dir'" EXIT
    
    # Get video duration
    local duration
    duration=$(get_video_info "$video_file")
    
    if [[ "$verbose" == "true" ]]; then
        echo "Video duration: ${duration}s" >&2
    fi
    
    # Extract frames
    local frame_count
    frame_count=$(extract_frames "$video_file" "$temp_dir" "$interval" "$max_frames" "$quality" "$resize" "$verbose")
    
    if [[ "$frame_count" -eq 0 ]]; then
        echo "Error: No frames extracted" >&2
        exit 1
    fi
    
    if [[ "$verbose" == "true" ]]; then
        echo "Extracted $frame_count frames" >&2
    fi
    
    # Start JSON output
    echo "{"
    echo "  \"source_file\": \"$video_file\","
    echo "  \"duration\": $duration,"
    echo "  \"frame_interval\": $interval,"
    echo "  \"frame_count\": $frame_count,"
    echo "  \"frame_size\": \"$resize\","
    echo "  \"timestamp\": $(date +%s),"
    echo "  \"frames\": ["
    
    # Process each frame
    local first_frame=true
    for frame_path in "$temp_dir"/frame_*.jpg; do
        if [[ ! -f "$frame_path" ]]; then
            continue
        fi
        
        # Extract frame number from filename
        local frame_filename
        frame_filename=$(basename "$frame_path")
        local frame_number
        frame_number=$(echo "$frame_filename" | sed 's/frame_0*\([0-9]*\)\.jpg/\1/')
        
        # Calculate timestamp
        local timestamp
        timestamp=$(get_frame_timestamp "$frame_number" "$interval")
        
        # Add comma separator (except for first frame)
        if [[ "$first_frame" != "true" ]]; then
            echo ","
        fi
        first_frame=false
        
        # Output frame data
        echo "    {"
        echo "      \"frame_number\": $frame_number,"
        echo "      \"timestamp\": $timestamp,"
        
        case "$output_format" in
            "base64")
                local base64_data
                base64_data=$(frame_to_base64 "$frame_path")
                echo "      \"data\": \"$base64_data\""
                ;;
            "paths")
                echo "      \"path\": \"$frame_path\""
                ;;
            "both")
                local base64_data
                base64_data=$(frame_to_base64 "$frame_path")
                echo "      \"data\": \"$base64_data\","
                echo "      \"path\": \"$frame_path\""
                ;;
        esac
        
        echo -n "    }"
    done
    
    echo ""
    echo "  ]"
    echo "}"
}

# Parse command line arguments
VERBOSE=false
while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--interval)
            INTERVAL="$2"
            shift 2
            ;;
        -f|--format)
            OUTPUT_FORMAT="$2"
            shift 2
            ;;
        -m|--max-frames)
            MAX_FRAMES="$2"
            shift 2
            ;;
        -q|--quality)
            QUALITY="$2"
            shift 2
            ;;
        -r|--resize)
            RESIZE="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        -*)
            echo "Unknown option: $1" >&2
            usage
            exit 1
            ;;
        *)
            VIDEO_FILE="$1"
            shift
            ;;
    esac
done

# Validate arguments
if [[ -z "$VIDEO_FILE" ]]; then
    echo "Error: Video file required" >&2
    usage
    exit 1
fi

if [[ ! -f "$VIDEO_FILE" ]]; then
    echo "Error: Video file not found: $VIDEO_FILE" >&2
    exit 1
fi

# Check for required tools
if ! command -v ffmpeg >/dev/null 2>&1; then
    echo "Error: ffmpeg not found. Please install ffmpeg." >&2
    exit 1
fi

if ! command -v ffprobe >/dev/null 2>&1; then
    echo "Error: ffprobe not found. Please install ffmpeg." >&2
    exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
    echo "Error: jq not found. Please install jq." >&2
    exit 1
fi

# Validate format
if [[ "$OUTPUT_FORMAT" != "base64" && "$OUTPUT_FORMAT" != "paths" && "$OUTPUT_FORMAT" != "both" ]]; then
    echo "Error: Invalid format. Must be 'base64', 'paths', or 'both'" >&2
    exit 1
fi

# Process the video
process_video "$VIDEO_FILE" "$INTERVAL" "$OUTPUT_FORMAT" "$MAX_FRAMES" "$QUALITY" "$RESIZE" "$VERBOSE"