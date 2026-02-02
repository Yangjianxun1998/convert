#!/usr/bin/env python3
"""Test script for video2mp4 package"""

from video2mp4 import convert_video, check_ffmpeg, start_server
import sys

def test_ffmpeg_check():
    """Test FFmpeg availability check"""
    print("测试FFmpeg检查...")
    is_available = check_ffmpeg()
    print(f"FFmpeg可用: {is_available}")
    return is_available

def test_api_import():
    """Test API import"""
    print("\n测试API导入...")
    print(f"convert_video 函数: {callable(convert_video)}")
    print(f"check_ffmpeg 函数: {callable(check_ffmpeg)}")
    print(f"start_server 函数: {callable(start_server)}")
    print("API导入测试通过!")

def main():
    """Main test function"""
    print("测试 video2mp4 包...")
    print("=" * 50)
    
    # 测试API导入
    test_api_import()
    
    # 测试FFmpeg检查
    if not test_ffmpeg_check():
        print("FFmpeg 未安装，部分测试将跳过")
    
    print("=" * 50)
    print("包测试完成!")

if __name__ == "__main__":
    main()
