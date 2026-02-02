"""WebSocket server for real-time progress updates"""

import asyncio
import json
import websockets
import logging
import os
from typing import Dict, Set, Optional
from .core import convert_video

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WebSocketServer:
    """WebSocket server for video conversion progress updates"""

    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.active_connections: Set[websockets.WebSocketServerProtocol] = set()
        self.tasks: Dict[str, asyncio.Task] = {}
        self.uploads: Dict[str, Dict] = {}  # 存储上传状态
        self.upload_dir = "uploads"  # 上传文件存储目录
        # 创建上传目录
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir, exist_ok=True)

    async def handle_connection(self, websocket: websockets.WebSocketServerProtocol):
        """Handle incoming WebSocket connections"""
        self.active_connections.add(websocket)
        logger.info(f"New connection established from {websocket.remote_address}")

        try:
            async for message in websocket:
                await self.process_message(websocket, message)
        except websockets.ConnectionClosed as e:
            logger.info(f"Connection closed from {websocket.remote_address}: {e}")
        except Exception as e:
            logger.error(f"Error handling connection from {websocket.remote_address}: {e}")
        finally:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)

    async def process_message(self, websocket: websockets.WebSocketServerProtocol, message: str):
        """Process incoming WebSocket messages"""
        try:
            data = json.loads(message)
            action = data.get("action")
            logger.debug(f"Received message from {websocket.remote_address}: {action}")

            if action == "convert":
                await self.handle_convert_request(websocket, data)
            elif action == "check_ffmpeg":
                await self.handle_check_ffmpeg(websocket)
            elif action == "cancel":
                await self.handle_cancel_request(websocket, data)
            elif action == "upload":
                await self.handle_upload(websocket, data)
            elif action == "upload_chunk":
                await self.handle_upload_chunk(websocket, data)
            elif action == "upload_complete":
                await self.handle_upload_complete(websocket, data)
            else:
                error_msg = f"Unknown action: {action}"
                logger.warning(error_msg)
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": error_msg
                }))
        except json.JSONDecodeError:
            error_msg = "Invalid JSON format"
            logger.warning(f"Invalid JSON from {websocket.remote_address}")
            await websocket.send(json.dumps({
                "type": "error",
                "message": error_msg
            }))
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error processing message from {websocket.remote_address}: {error_msg}")
            await websocket.send(json.dumps({
                "type": "error",
                "message": error_msg
            }))

    async def handle_check_ffmpeg(self, websocket: websockets.WebSocketServerProtocol):
        """Handle FFmpeg check request"""
        from .core import check_ffmpeg
        is_available = check_ffmpeg()
        await websocket.send(json.dumps({
            "type": "ffmpeg_check",
            "available": is_available,
            "message": "FFmpeg is available" if is_available else "FFmpeg is not installed or not in PATH"
        }))

    async def handle_convert_request(self, websocket: websockets.WebSocketServerProtocol, data: Dict):
        """Handle video conversion request"""
        input_file = data.get("input_file")
        output_file = data.get("output_file")
        options = data.get("options", {})

        if not input_file or not output_file:
            await websocket.send(json.dumps({
                "type": "error",
                "message": "Missing input_file or output_file"
            }))
            return

        task_id = f"{id(websocket)}_{len(self.tasks)}"
        
        async def progress_callback(update: Dict):
            """Callback to send progress updates via WebSocket"""
            try:
                await websocket.send(json.dumps({
                    "type": "progress",
                    "task_id": task_id,
                    **update
                }))
            except websockets.ConnectionClosed:
                pass

        # Create and start conversion task
        task = asyncio.create_task(
            self.run_conversion(input_file, output_file, progress_callback, options)
        )
        self.tasks[task_id] = task

        # Send task ID to client
        await websocket.send(json.dumps({
            "type": "task_started",
            "task_id": task_id,
            "message": "Conversion task started"
        }))

    async def run_conversion(self, input_file: str, output_file: str, callback, options: Dict):
        """Run video conversion in a separate task"""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: convert_video(input_file, output_file, callback, **options)
        )
        return result

    async def handle_cancel_request(self, websocket: websockets.WebSocketServerProtocol, data: Dict):
        """Handle conversion cancellation request"""
        task_id = data.get("task_id")
        if task_id in self.tasks:
            task = self.tasks.pop(task_id)
            task.cancel()
            await websocket.send(json.dumps({
                "type": "task_cancelled",
                "task_id": task_id,
                "message": "Conversion task cancelled"
            }))
        else:
            await websocket.send(json.dumps({
                "type": "error",
                "message": f"Task {task_id} not found"
            }))

    async def handle_upload(self, websocket: websockets.WebSocketServerProtocol, data: Dict):
        """Handle file upload initialization"""
        file_name = data.get("file_name")
        file_size = data.get("file_size", 0)
        
        if not file_name:
            await websocket.send(json.dumps({
                "type": "error",
                "message": "Missing file_name"
            }))
            return
        
        # Generate unique upload ID
        upload_id = f"{id(websocket)}_{len(self.uploads)}"
        file_path = os.path.join(self.upload_dir, file_name)
        
        # Initialize upload state
        self.uploads[upload_id] = {
            "file_name": file_name,
            "file_path": file_path,
            "file_size": file_size,
            "uploaded_size": 0,
            "file_handle": None
        }
        
        # Create file for writing
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            # Open file in binary write mode
            file_handle = open(file_path, 'wb')
            self.uploads[upload_id]["file_handle"] = file_handle
            
            await websocket.send(json.dumps({
                "type": "upload_init",
                "upload_id": upload_id,
                "message": "Upload initialized successfully"
            }))
        except Exception as e:
            logger.error(f"Error initializing upload: {e}")
            await websocket.send(json.dumps({
                "type": "error",
                "message": f"Failed to initialize upload: {str(e)}"
            }))

    async def handle_upload_chunk(self, websocket: websockets.WebSocketServerProtocol, data: Dict):
        """Handle file chunk upload"""
        upload_id = data.get("upload_id")
        chunk = data.get("chunk")
        offset = data.get("offset", 0)
        
        if not upload_id or not chunk:
            await websocket.send(json.dumps({
                "type": "error",
                "message": "Missing upload_id or chunk"
            }))
            return
        
        if upload_id not in self.uploads:
            await websocket.send(json.dumps({
                "type": "error",
                "message": f"Upload {upload_id} not found"
            }))
            return
        
        upload_state = self.uploads[upload_id]
        file_handle = upload_state.get("file_handle")
        
        if not file_handle:
            await websocket.send(json.dumps({
                "type": "error",
                "message": "Upload not properly initialized"
            }))
            return
        
        try:
            # Convert base64 chunk to bytes
            import base64
            chunk_data = base64.b64decode(chunk)
            
            # Write chunk to file
            file_handle.write(chunk_data)
            
            # Update uploaded size
            upload_state["uploaded_size"] += len(chunk_data)
            
            # Calculate progress
            file_size = upload_state.get("file_size", 1)
            progress = min(100, int((upload_state["uploaded_size"] / file_size) * 100))
            
            # Send progress update
            await websocket.send(json.dumps({
                "type": "upload_progress",
                "upload_id": upload_id,
                "progress": progress,
                "uploaded": upload_state["uploaded_size"],
                "total": file_size
            }))
        except Exception as e:
            logger.error(f"Error handling upload chunk: {e}")
            await websocket.send(json.dumps({
                "type": "error",
                "message": f"Failed to process upload chunk: {str(e)}"
            }))

    async def handle_upload_complete(self, websocket: websockets.WebSocketServerProtocol, data: Dict):
        """Handle upload completion"""
        upload_id = data.get("upload_id")
        
        if not upload_id:
            await websocket.send(json.dumps({
                "type": "error",
                "message": "Missing upload_id"
            }))
            return
        
        if upload_id not in self.uploads:
            await websocket.send(json.dumps({
                "type": "error",
                "message": f"Upload {upload_id} not found"
            }))
            return
        
        upload_state = self.uploads[upload_id]
        file_handle = upload_state.get("file_handle")
        
        try:
            # Close file handle if open
            if file_handle:
                file_handle.close()
                upload_state["file_handle"] = None
            
            # Get file path
            file_path = upload_state.get("file_path")
            file_name = upload_state.get("file_name")
            
            # Verify file exists and has content
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                await websocket.send(json.dumps({
                    "type": "upload_complete",
                    "upload_id": upload_id,
                    "file_path": file_path,
                    "file_name": file_name,
                    "message": "File uploaded successfully"
                }))
            else:
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Uploaded file is empty or does not exist"
                }))
        except Exception as e:
            logger.error(f"Error completing upload: {e}")
            await websocket.send(json.dumps({
                "type": "error",
                "message": f"Failed to complete upload: {str(e)}"
            }))
        finally:
            # Clean up upload state
            if upload_id in self.uploads:
                # Ensure file handle is closed
                if self.uploads[upload_id].get("file_handle"):
                    try:
                        self.uploads[upload_id]["file_handle"].close()
                    except:
                        pass
                del self.uploads[upload_id]

    async def broadcast(self, message: Dict):
        """Broadcast message to all connected clients"""
        if self.active_connections:
            message_json = json.dumps(message)
            disconnected = []
            for connection in self.active_connections:
                try:
                    await connection.send(message_json)
                except websockets.ConnectionClosed:
                    disconnected.append(connection)

            # Remove disconnected clients
            for connection in disconnected:
                self.active_connections.remove(connection)

    async def start(self):
        """Start the WebSocket server"""
        async with websockets.serve(
            self.handle_connection,
            self.host,
            self.port
        ) as server:
            print(f"WebSocket server started at ws://{self.host}:{self.port}")
            print("Waiting for connections...")
            await server.serve_forever()


def start_server(host: str = "localhost", port: int = 8765):
    """Start the WebSocket server"""
    server = WebSocketServer(host, port)
    asyncio.run(server.start())


if __name__ == "__main__":
    start_server()
