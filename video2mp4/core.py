"""Core video conversion functionality"""

import os
import subprocess
import json
import asyncio
from typing import Dict, Optional, Callable


def check_ffmpeg() -> bool:
    """Check if FFmpeg is installed and accessible"""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            check=True
        )
        return "ffmpeg version" in result.stdout
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def get_video_duration(input_file: str) -> float:
    """Get video duration using FFprobe"""
    try:
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            input_file
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        info = json.loads(result.stdout)
        return float(info["format"]["duration"])
    except Exception:
        return 0.0


def convert_video(
    input_file: str,
    output_file: str,
    progress_callback: Optional[Callable[[Dict], None]] = None,
    **kwargs
) -> bool:
    """
    Convert video to MP4 format
    
    Args:
        input_file: Path to input video file
        output_file: Path to output MP4 file
        progress_callback: Callback function for progress updates
        **kwargs: Additional conversion parameters
            - codec: Video codec (default: libx264)
            - preset: Encoding preset (default: medium)
            - crf: Constant Rate Factor (default: 23)
            - audio_codec: Audio codec (default: aac)
            - audio_bitrate: Audio bitrate (default: 128k)
            - resolution: Video resolution (e.g., "1920x1080")
    """
    """Handle both sync and async progress callbacks"""
    original_callback = progress_callback
    
    def call_callback(update):
        if original_callback:
            try:
                # Check if it's a coroutine function
                if hasattr(original_callback, '__call__') and asyncio.iscoroutinefunction(original_callback):
                    asyncio.run(original_callback(update))
                else:
                    original_callback(update)
            except Exception as e:
                print(f"Error calling progress callback: {e}")
    
    # Replace progress_callback with our wrapper
    progress_callback = call_callback
    # Validate inputs
    if not input_file:
        if progress_callback:
            progress_callback({"status": "error", "message": "Input file path is required"})
        return False
    
    if not output_file:
        if progress_callback:
            progress_callback({"status": "error", "message": "Output file path is required"})
        return False
    
    # Check FFmpeg availability
    if not check_ffmpeg():
        if progress_callback:
            progress_callback({"status": "error", "message": "FFmpeg not found. Please install FFmpeg and add it to system PATH"})
        return False

    # Check input file existence
    if not os.path.exists(input_file):
        if progress_callback:
            progress_callback({"status": "error", "message": f"Input file not found: {input_file}"})
        return False
    
    # Check input file is a regular file
    if not os.path.isfile(input_file):
        if progress_callback:
            progress_callback({"status": "error", "message": f"Input path is not a file: {input_file}"})
        return False
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            if progress_callback:
                progress_callback({"status": "error", "message": f"Failed to create output directory: {str(e)}"})
            return False
    
    # Ensure output file is in current directory for HTTP access
    if not output_dir:
        output_file = os.path.join(os.getcwd(), output_file)

    # Default parameters
    codec = kwargs.get("codec", "libx264")
    preset = kwargs.get("preset", "medium")
    crf = kwargs.get("crf", "23")
    audio_codec = kwargs.get("audio_codec", "aac")
    audio_bitrate = kwargs.get("audio_bitrate", "128k")
    resolution = kwargs.get("resolution")

    # Build FFmpeg command
    cmd = [
        "ffmpeg",
        "-i", input_file,
        "-c:v", codec,
        "-preset", preset,
        "-crf", str(crf),
        "-c:a", audio_codec,
        "-b:a", audio_bitrate,
        "-y",  # Overwrite output file
        "-progress", "pipe:1",  # Output progress to stdout
        "-hide_banner",
        "-loglevel", "error"
    ]

    # Add resolution if specified
    if resolution:
        cmd.extend(["-vf", f"scale={resolution}"])

    cmd.append(output_file)

    # Get video duration for progress calculation
    duration = get_video_duration(input_file)

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Process progress output
        for line in process.stdout:
            line = line.strip()
            if line.startswith("out_time_ms="):
                try:
                    time_ms = int(line.split("=")[1])
                    time_sec = time_ms / 1000000
                    if duration > 0:
                        progress = min(100, int((time_sec / duration) * 100))
                    else:
                        progress = 0
                    
                    if progress_callback:
                        progress_callback({
                            "status": "progress",
                            "progress": progress,
                            "time": time_sec,
                            "duration": duration
                        })
                except ValueError:
                    pass

        # Wait for process to complete
        stdout, stderr = process.communicate()
        returncode = process.returncode

        if returncode == 0:
            if progress_callback:
                progress_callback({"status": "completed", "output": output_file})
            return True
        else:
            if progress_callback:
                progress_callback({"status": "error", "message": stderr})
            return False

    except Exception as e:
        if progress_callback:
            progress_callback({"status": "error", "message": str(e)})
        return False
