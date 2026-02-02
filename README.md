# video2mp4

一个用于将各种视频格式转换为MP4的Python包，通过WebSocket提供实时进度更新。

## 功能特性

- 🎯 使用FFmpeg将任何视频格式转换为MP4
- 🔄 通过WebSocket提供实时进度更新
- 📦 命令行界面，使用方便
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
