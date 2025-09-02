#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video Downloader Package

A powerful Python video downloader that supports multiple video platforms.
"""

__version__ = "1.0.0"
__author__ = "Video Downloader Team"
__email__ = "contact@example.com"
__description__ = "Multi-platform video downloader with GUI and CLI support"

from .video_downloader import VideoDownloader
from .config import DownloaderConfig

__all__ = [
    'VideoDownloader',
    'DownloaderConfig',
    '__version__',
    '__author__',
    '__email__',
    '__description__'
]