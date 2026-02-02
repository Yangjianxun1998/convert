"""Video to MP4 converter package"""

__version__ = "0.1.0"
__author__ = "Video Converter Team"
__description__ = "Convert various video formats to MP4 with WebSocket progress updates"

from .core import convert_video, check_ffmpeg
from .websocket_server import start_server
from .cli import main

__all__ = [
    "convert_video",
    "check_ffmpeg",
    "start_server",
    "main"
]
