"""Command line interface for video conversion"""

import argparse
import sys
import os
from typing import Optional
from .core import convert_video, check_ffmpeg


def parse_args() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Convert various video formats to MP4"
    )
    

    
    # Required arguments (only required if not using --check-ffmpeg)
    parser.add_argument(
        "input_file",
        nargs="?",
        help="Path to input video file"
    )
    
    parser.add_argument(
        "output_file",
        nargs="?",
        help="Path to output MP4 file (default: input_file.mp4)"
    )
    
    # Conversion options
    parser.add_argument(
        "--codec",
        default="libx264",
        help="Video codec (default: libx264)"
    )
    
    parser.add_argument(
        "--preset",
        default="medium",
        choices=["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow", "placebo"],
        help="Encoding preset (default: medium)"
    )
    
    parser.add_argument(
        "--crf",
        type=int,
        default=23,
        help="Constant Rate Factor (default: 23)"
    )
    
    parser.add_argument(
        "--audio-codec",
        default="aac",
        help="Audio codec (default: aac)"
    )
    
    parser.add_argument(
        "--audio-bitrate",
        default="128k",
        help="Audio bitrate (default: 128k)"
    )
    
    parser.add_argument(
        "--resolution",
        help="Video resolution (e.g., 1920x1080)"
    )
    
    # Utility commands
    parser.add_argument(
        "--check-ffmpeg",
        action="store_true",
        help="Check if FFmpeg is installed"
    )
    
    return parser.parse_args()


def progress_callback(update: dict):
    """Callback for progress updates in CLI"""
    status = update.get("status")
    
    if status == "progress":
        progress = update.get("progress", 0)
        sys.stdout.write(f"\rProgress: {progress}% ")
        sys.stdout.flush()
    elif status == "completed":
        print("\nConversion completed successfully!")
        print(f"Output file: {update.get('output')}")
    elif status == "error":
        print(f"\nError: {update.get('message')}")


def main() -> int:
    """Main CLI function"""
    args = parse_args()
    
    # Check FFmpeg availability
    if args.check_ffmpeg:
        is_available = check_ffmpeg()
        if is_available:
            print("✓ FFmpeg is installed and accessible")
            return 0
        else:
            print("✗ FFmpeg is not installed or not in PATH")
            print("Please install FFmpeg and add it to your system PATH")
            return 1
    
    # Validate input file
    if not args.input_file:
        print("Error: input_file is required")
        return 1
    
    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' does not exist")
        return 1
    
    # Determine output file if not specified
    if not args.output_file:
        base_name = os.path.splitext(args.input_file)[0]
        args.output_file = f"{base_name}.mp4"
    
    # Check FFmpeg before conversion
    if not check_ffmpeg():
        print("Error: FFmpeg is not installed or not in PATH")
        print("Please install FFmpeg and add it to your system PATH")
        return 1
    
    # Build conversion options
    options = {
        "codec": args.codec,
        "preset": args.preset,
        "crf": args.crf,
        "audio_codec": args.audio_codec,
        "audio_bitrate": args.audio_bitrate,
        "resolution": args.resolution
    }
    
    # Remove None values
    options = {k: v for k, v in options.items() if v is not None}
    
    print(f"Converting {args.input_file} to {args.output_file}...")
    print(f"Options: {options}")
    
    # Run conversion
    success = convert_video(
        args.input_file,
        args.output_file,
        progress_callback=progress_callback,
        **options
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
