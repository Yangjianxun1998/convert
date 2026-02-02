# video2mp4

一个用于将各种视频格式转换为MP4的Python包，通过WebSocket提供实时进度更新。

## 功能特性

- 🎯 使用FFmpeg将任何视频格式转换为MP4
- 🔄 通过WebSocket提供实时进度更新
- � 支持文件上传功能，带上传进度反馈
- �📦 命令行界面，使用方便
- 🐍 Python API，可集成到其他项目中
- ⚙️ 可自定义转换参数
- 📊 支持批量转换
- 🛠️ FFmpeg可用性检查

## 安装

### 前提条件

- Python 3.7 或更高版本
- 已安装FFmpeg并添加到系统PATH

### 安装包

```bash
pip install video2mp4
```

## 使用方法

### 命令行界面

#### 检查FFmpeg是否安装

```bash
video2mp4 --check-ffmpeg
```

#### 转换视频文件

```bash
video2mp4 input_video.avi output_video.mp4
```

#### 使用自定义选项转换

```bash
video2mp4 input_video.mkv output_video.mp4 --preset fast --crf 20 --resolution 1920x1080
```

### WebSocket服务器

启动WebSocket服务器：

```bash
video2mp4-server
```

服务器将在 `ws://localhost:8765` 启动

#### 上传功能使用示例

以下是一个使用WebSocket上传文件并获取上传进度的完整示例：

```javascript
// 示例：使用WebSocket上传文件并获取进度
const ws = new WebSocket('ws://localhost:8765');

ws.onopen = () => {
  console.log('WebSocket connected');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received message:', data);
  
  if (data.type === 'upload_init') {
    // 上传初始化成功，开始上传文件块
    uploadFileChunks(data.upload_id);
  } else if (data.type === 'upload_progress') {
    // 上传进度更新
    console.log(`Upload progress: ${data.progress}%`);
    // 可以在这里更新UI进度条
  } else if (data.type === 'upload_complete') {
    // 上传完成，可以开始转换
    console.log('Upload completed:', data.file_path);
    // 开始转换视频
    startConversion(data.file_path);
  } else if (data.type === 'error') {
    // 错误处理
    console.error('Error:', data.message);
  }
};

// 初始化上传
function initUpload(file) {
  ws.send(JSON.stringify({
    action: 'upload',
    file_name: file.name,
    file_size: file.size
  }));
}

// 上传文件块
async function uploadFileChunks(uploadId) {
  const file = document.getElementById('fileInput').files[0];
  const chunkSize = 1024 * 1024; // 1MB chunks
  let offset = 0;
  
  while (offset < file.size) {
    const chunk = file.slice(offset, offset + chunkSize);
    const reader = new FileReader();
    
    await new Promise((resolve) => {
      reader.onload = (e) => {
        const base64Chunk = e.target.result.split(',')[1]; // 移除data URL前缀
        ws.send(JSON.stringify({
          action: 'upload_chunk',
          upload_id: uploadId,
          chunk: base64Chunk,
          offset: offset
        }));
        offset += chunkSize;
        resolve();
      };
      reader.readAsDataURL(chunk);
    });
  }
  
  // 上传完成
  ws.send(JSON.stringify({
    action: 'upload_complete',
    upload_id: uploadId
  }));
}

// 开始转换
function startConversion(filePath) {
  ws.send(JSON.stringify({
    action: 'convert',
    input_file: filePath,
    output_file: filePath.replace(/\.[^/.]+$/, '') + '_converted.mp4',
    options: {
      preset: 'medium',
      crf: 23
    }
  }));
}

// 示例：监听文件选择
const fileInput = document.getElementById('fileInput');
fileInput.addEventListener('change', (e) => {
  const file = e.target.files[0];
  if (file) {
    initUpload(file);
  }
});
```

这个示例展示了：
1. 如何初始化上传并获取上传ID
2. 如何分块上传文件并处理每块的上传
3. 如何接收并显示上传进度更新
4. 如何在上传完成后开始视频转换

通过这种方式，你可以为用户提供完整的上传进度反馈，提升用户体验。

### Python API

#### 基本用法

```python
from video2mp4 import convert_video, check_ffmpeg

# 检查FFmpeg是否可用
if check_ffmpeg():
    print("FFmpeg已就绪!")
else:
    print("请先安装FFmpeg。")

# 转换视频
def progress_callback(update):
    if update['status'] == 'progress':
        print(f"进度: {update['progress']}%")
    elif update['status'] == 'completed':
        print(f"转换完成: {update['output']}")
    elif update['status'] == 'error':
        print(f"错误: {update['message']}")

convert_video(
    'input_video.avi',
    'output_video.mp4',
    progress_callback=progress_callback,
    preset='fast',
    crf=23
)
```

#### 启动WebSocket服务器

```python
from video2mp4 import start_server

# 在自定义主机和端口上启动服务器
start_server(host='0.0.0.0', port=8765)
```

## WebSocket协议

### 客户端到服务器消息

#### 检查FFmpeg

```json
{
  "action": "check_ffmpeg"
}
```

#### 转换视频

```json
{
  "action": "convert",
  "input_file": "/path/to/input/video.avi",
  "output_file": "/path/to/output/video.mp4",
  "options": {
    "preset": "medium",
    "crf": 23,
    "resolution": "1920x1080"
  }
}
```

#### 取消转换

```json
{
  "action": "cancel",
  "task_id": "task_123"
}
```

#### 初始化上传

```json
{
  "action": "upload",
  "file_name": "video.mp4",
  "file_size": 10485760
}
```

#### 上传文件块

```json
{
  "action": "upload_chunk",
  "upload_id": "upload_123",
  "chunk": "base64_encoded_chunk_data",
  "offset": 0
}
```

#### 上传完成

```json
{
  "action": "upload_complete",
  "upload_id": "upload_123"
}
```

### 服务器到客户端消息

#### 进度更新

```json
{
  "type": "progress",
  "task_id": "task_123",
  "status": "progress",
  "progress": 45,
  "time": 12.5,
  "duration": 27.8
}
```

#### 任务开始

```json
{
  "type": "task_started",
  "task_id": "task_123",
  "message": "Conversion task started"
}
```

#### 任务完成

```json
{
  "type": "progress",
  "task_id": "task_123",
  "status": "completed",
  "output": "/path/to/output/video.mp4"
}
```

#### 错误消息

```json
{
  "type": "error",
  "message": "Error description"
}
```

#### 上传初始化响应

```json
{
  "type": "upload_init",
  "upload_id": "upload_123",
  "message": "Upload initialized successfully"
}
```

#### 上传进度更新

```json
{
  "type": "upload_progress",
  "upload_id": "upload_123",
  "progress": 45,
  "uploaded": 4613734,
  "total": 10485760
}
```

#### 上传完成响应

```json
{
  "type": "upload_complete",
  "upload_id": "upload_123",
  "file_path": "/path/to/uploads/video.mp4",
  "file_name": "video.mp4",
  "message": "File uploaded successfully"
}
```

## 转换选项

| 选项 | 描述 | 默认值 |
|--------|-------------|---------|
| codec | 视频编解码器 | libx264 |
| preset | 编码速度/质量预设 | medium |
| crf | 恒定速率因子 (0-51, 值越小质量越好) | 23 |
| audio_codec | 音频编解码器 | aac |
| audio_bitrate | 音频比特率 | 128k |
| resolution | 视频分辨率 (例如：1920x1080) | 原始分辨率 |

## 贡献

欢迎贡献！请随时提交Pull Request。

## 许可证

本项目采用MIT许可证 - 详情请参阅 [LICENSE](LICENSE) 文件。
