#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
setup.py - Video Downloader Packaging Configuration
Using cx_Freeze to package as Windows executable
"""

import sys
import os
from cx_Freeze import setup, Executable

# Determine base path
base_path = os.path.dirname(os.path.abspath(__file__))

# Include files and directories
include_files = [
    # Configuration files
    (os.path.join(base_path, "src", "config.py"), "src/config.py"),
    
    # Core modules
    (os.path.join(base_path, "src", "video_downloader.py"), "src/video_downloader.py"),
    (os.path.join(base_path, "src", "optimized_video_downloader.py"), "src/optimized_video_downloader.py"),
    (os.path.join(base_path, "src", "main_downloader.py"), "src/main_downloader.py"),
    
    # GUI module
    (os.path.join(base_path, "src", "video_downloader_gui.py"), "src/video_downloader_gui.py"),
    
    # Package init
    (os.path.join(base_path, "src", "__init__.py"), "src/__init__.py"),
    
    # Create downloads directory
    (os.path.join(base_path, "downloads"), "downloads") if os.path.exists(os.path.join(base_path, "downloads")) else None,
]

# Filter out None values
include_files = [f for f in include_files if f is not None]

# Required packages
packages = [
    "os",
    "sys",
    "subprocess",
    "logging",
    "threading",
    "time",
    "json",
    "base64",
    "urllib.parse",
    "datetime",
    "argparse",
    "typing",
    "requests",
    "tkinter",
    "tkinter.ttk",
    "tkinter.scrolledtext",
    "tkinter.messagebox",
    "tkinter.filedialog"
]

# Modules to exclude (reduce file size)
excludes = [
    "matplotlib",
    "numpy",
    "pandas",
    "scipy",
    "PIL",
    "cv2",
    "tensorflow",
    "torch",
    "sklearn",
    "jupyter",
    "notebook",
    "IPython",
    "selenium",  # Temporarily exclude selenium to reduce size
    "webdriver_manager"
]

# Build options
build_exe_options = {
    "packages": packages,
    "excludes": excludes,
    "include_files": include_files,
    "optimize": 2,
    "include_msvcrt": True,
    "build_exe": "build/video_downloader_v2",
    "zip_include_packages": ["*"],
    "zip_exclude_packages": [],
}

# Executable configuration
executables = [
    Executable(
        script="src/main_downloader.py",
        base=None,  # Use console mode
        target_name="video_downloader.exe",
        icon=None,  # Can add icon file path
        copyright="Copyright (C) 2024 Video Downloader",
        shortcut_name="Video Downloader",
        shortcut_dir="DesktopFolder"
    ),
    
    # GUI版本（如果需要无控制台窗口）
    Executable(
        script="src/main_downloader.py",
        base="Win32GUI" if sys.platform == "win32" else None,
        target_name="video_downloader_gui.exe",
        icon=None,
        copyright="Copyright (C) 2024 Video Downloader",
        shortcut_name="Video Downloader (GUI)",
        shortcut_dir="DesktopFolder"
    )
]

# 安装配置
setup(
    name="VideoDownloader",
    version="2.0.0",
    description="Multi-site Video Downloader - Supports Bilibili, Sohu Video, etc.",
    long_description="""
Video Downloader v2.0

Features:
• Support for multiple video websites (Bilibili, Sohu Video, YouTube, etc.)
• Graphical user interface and command line interface
• Multi-threaded concurrent downloads
• Smart retry mechanism
• Configuration management
• Detailed download reports

Usage:
1. Double-click video_downloader.exe to start interactive mode
2. Use --gui parameter to launch graphical interface
3. Use --urls parameter for batch downloads

System Requirements:
• Windows 10 or higher
• Requires yt-dlp installation (program will auto-check)
    """,
    author="Video Downloader Team",
    author_email="support@videodownloader.com",
    url="https://github.com/videodownloader/videodownloader",
    license="MIT",
    
    options={
        "build_exe": build_exe_options
    },
    
    executables=executables
)

# 打包后的说明
print("""
🎉 Packaging configuration complete!

📦 Build command:
  python setup.py build

📁 Output directory:
  build/video_downloader_v2/

📋 Included files:
  • video_downloader.exe (console version)
  • video_downloader_gui.exe (GUI version)
  • All necessary Python modules and configuration files

💡 Usage tips:
  1. Ensure cx_Freeze is installed: pip install cx_Freeze
  2. Ensure yt-dlp is installed: pip install yt-dlp
  3. After running the build command, executables will be in the build directory
  4. You can distribute the entire build/video_downloader_v2 directory to users

⚠️ Notes:
  • On first run, the program will check if yt-dlp is available
  • If dependencies are missing, the program will prompt user to install
  • It's recommended to test the executable on target systems
""")