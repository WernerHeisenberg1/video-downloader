#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multi-platform Video Downloader

A powerful video downloader supporting multiple platforms including
Bilibili, Baidu Baike, Pinshan, Sohu, and 360kan.
"""

import os
import re
import sys
import time
import json
import logging
import requests
from urllib.parse import urlparse, urljoin, parse_qs
from pathlib import Path
from typing import Optional, Dict, Any
from tqdm import tqdm
from bs4 import BeautifulSoup
import traceback
import yt_dlp
import subprocess
import base64
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import glob

MOVIEPY_AVAILABLE = False
VideoFileClip = None
AudioFileClip = None


class VideoDownloadError(Exception):
    """Base exception for video download errors"""
    pass


class NetworkError(VideoDownloadError):
    """Network related errors"""
    pass


class ParseError(VideoDownloadError):
    """Video parsing errors"""
    pass


class FileError(VideoDownloadError):
    """File operation errors"""
    pass


class UnsupportedSiteError(VideoDownloadError):
    """Unsupported website errors"""
    pass


class VideoDownloader:
    """Main video downloader class supporting multiple platforms"""
    
    def __init__(self, download_dir: str = "downloads"):
        """
        Initialize the video downloader
        
        Args:
            download_dir: Directory to save downloaded videos
        """
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
        
        self.setup_logging()
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        self.supported_sites = {
            'baike.baidu.com': self._extract_baidu_video,
            'bilibili.com': self._extract_bilibili_video,
            'pinshan.com': self._extract_pinshan_video,
            'sohu.com': self._extract_sohu_video,
            '360kan.com': self._extract_360kan_video
        }
    
    def setup_logging(self):
        """Setup logging system"""
        log_dir = self.download_dir
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / "downloader.log"
        
        # 清除现有的处理器
        logger = logging.getLogger()
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        logging.basicConfig(
            level=logging.DEBUG,
            handlers=[file_handler, console_handler]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Logging system initialized, log file: {log_file}")

    def download_video(self, url: str) -> bool:
        """
        Main entry point for video downloading
        
        Args:
            url: Video page URL
            
        Returns:
            bool: Whether download was successful
        """
        try:
            self.logger.info(f"Starting to process video link: {url}")
            
            if not self._validate_url(url):
                raise ValueError(f"Invalid URL format: {url}")
            
            if self._download_video_with_ytdlp(url):
                return True
            
            self.logger.info("yt-dlp download failed, trying manual parsing")
            
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            
            handler = None
            for site, func in self.supported_sites.items():
                if site in domain:
                    handler = func
                    break
            
            if not handler:
                raise UnsupportedSiteError(f"Unsupported website: {domain}")
            
            self.logger.debug(f"Using handler for parsing: {handler.__name__}")
            video_info = handler(url)
            if not video_info:
                raise ParseError("Unable to extract video information")
            
            self.logger.debug(f"Extracted video info: {video_info.get('title', 'Unknown')}")
            
            return self._download_file(video_info)
            
        except UnsupportedSiteError as e:
            self.logger.error(str(e))
            return False
        except ParseError as e:
            self.logger.error(f"Parse error: {str(e)}")
            return False
        except NetworkError as e:
            self.logger.error(f"Network error: {str(e)}")
            return False
        except FileError as e:
            self.logger.error(f"File error: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Unknown error: {str(e)}")
            self.logger.debug(f"Error details: {traceback.format_exc()}")
            return False
    
    def _download_video_with_ytdlp(self, url: str) -> bool:
        """
        直接使用yt-dlp下载视频
        
        Args:
            url: 视频页面URL
            
        Returns:
            bool: 下载是否成功
        """
        try:
            self.logger.info(f"尝试使用yt-dlp下载: {url}")
            
            # 配置yt-dlp选项 - 下载合并的mp4视频文件
            ffmpeg_path = Path(__file__).parent / 'ffmpeg' / 'ffmpeg-8.0-essentials_build' / 'bin' / 'ffmpeg.exe'
            
            ydl_opts = {
                'outtmpl': str(self.download_dir / '%(title)s.%(ext)s'),
                # 改进的格式选择策略：针对Bilibili优化
                'format': 'best[ext=mp4][acodec!=none]/30032+30280/(best[height<=720]/best)+(bestaudio[ext=m4a]/bestaudio)/best',
                'merge_output_format': 'mp4',  # 强制合并输出为mp4格式
                'quiet': True,
                'no_warnings': True,
                'writeinfojson': False,
                'writesubtitles': False,
                'writeautomaticsub': False,
                'extract_flat': False,
                'noplaylist': True,  # 关键：只下载单个视频，不下载播放列表
                'playlist_items': '1',  # 额外保险：只下载第一个项目
                'cookiefile': None,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'ffmpeg_location': str(ffmpeg_path) if ffmpeg_path.exists() else None,  # 指定ffmpeg路径
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }],
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    # 记录下载前的文件数量
                    files_before = set(f.name for f in self.download_dir.glob('*') if f.is_file() and not f.name.endswith('.log'))
                    
                    # 直接下载，不先提取信息
                    ydl.download([url])
                    
                    # 记录下载后的文件数量
                    files_after = set(f.name for f in self.download_dir.glob('*') if f.is_file() and not f.name.endswith('.log'))
                    new_files = files_after - files_before
                    
                    if new_files:
                        self.logger.info(f"yt-dlp下载成功: {url}，新增文件: {list(new_files)}")
                        
                        # 检查是否需要合并视频和音频文件
                        self._post_process_downloaded_files()
                        
                        return True
                    else:
                        self.logger.error(f"yt-dlp下载失败: {url}，没有新文件生成")
                        return False
                        
                except yt_dlp.DownloadError as e:
                    self.logger.debug(f"yt-dlp下载错误: {str(e)}")
                    return False
                except Exception as e:
                    self.logger.debug(f"yt-dlp其他错误: {str(e)}")
                    return False
                    
        except Exception as e:
            self.logger.debug(f"yt-dlp初始化失败: {str(e)}")
            return False

    def _validate_url(self, url: str) -> bool:
        """
        验证URL格式
        
        Args:
            url: 待验证的URL
            
        Returns:
            bool: URL是否有效
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    def _extract_bilibili_video(self, url: str) -> Optional[Dict[str, Any]]:
        """
        提取B站视频信息
        
        Args:
            url: B站视频页面URL
            
        Returns:
            视频信息字典或None
        """
        try:
            self.logger.debug(f"开始解析B站链接: {url}")
            
            # 使用yt-dlp提取视频信息
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/bestvideo+bestaudio/best',  # 优先合并最佳视频和音频
                'merge_output_format': 'mp4',  # 强制合并输出为mp4格式
                'writeinfojson': False,
                'writesubtitles': False,
                'writeautomaticsub': False,
                'noplaylist': True,  # 关键：只提取单个视频信息，不提取播放列表
                'playlist_items': '1',  # 额外保险：只提取第一个项目
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    info = ydl.extract_info(url, download=False)
                    
                    if not info:
                        raise ParseError("无法提取视频信息")
                    
                    # 获取视频URL
                    video_url = info.get('url')
                    if not video_url:
                        # 尝试从formats中获取
                        formats = info.get('formats', [])
                        for fmt in formats:
                            if fmt.get('ext') == 'mp4' and fmt.get('url'):
                                video_url = fmt['url']
                                break
                        
                        if not video_url and formats:
                            video_url = formats[0].get('url')
                    
                    if not video_url:
                        raise ParseError("无法获取视频下载链接")
                    
                    # 获取标题
                    title = info.get('title', 'bilibili_video')
                    title = self._sanitize_filename(title)
                    
                    return {
                        'title': title,
                        'url': video_url,
                        'ext': 'mp4'
                    }
                    
                except Exception as e:
                    self.logger.error(f"yt-dlp解析失败: {str(e)}")
                    raise ParseError(f"B站视频解析失败: {str(e)}")
            
        except ParseError:
            raise
        except Exception as e:
            self.logger.error(f"解析B站视频失败: {str(e)}")
            raise ParseError(f"无法解析B站视频: {str(e)}")
    
    def _extract_pinshan_video(self, url: str) -> Optional[Dict[str, Any]]:
        """
        提取品善网视频信息
        
        Args:
            url: 品善网视频页面URL
            
        Returns:
            视频信息字典或None
        """
        try:
            self.logger.debug(f"开始解析品善网链接: {url}")
            
            # 先尝试yt-dlp
            try:
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': False,
                    'format': 'worst[height<=720]/worst',
                    'writeinfojson': False,
                    'writesubtitles': False,
                    'writeautomaticsub': False,
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    
                    if info and info.get('url'):
                        title = info.get('title', 'pinshan_video')
                        title = self._sanitize_filename(title)
                        
                        return {
                            'title': title,
                            'url': info['url'],
                            'ext': 'mp4'
                        }
            except Exception as e:
                self.logger.debug(f"yt-dlp解析品善网失败，尝试手动解析: {str(e)}")
            
            # 手动解析品善网页面
            return self._manual_extract_pinshan(url)
            
        except ParseError:
            raise
        except Exception as e:
            self.logger.error(f"解析品善网视频失败: {str(e)}")
            raise ParseError(f"无法解析品善网视频: {str(e)}")
    
    def _extract_baidu_video(self, url: str) -> Optional[Dict[str, Any]]:
        """
        提取百度百科视频信息
        
        Args:
            url: 百度百科视频页面URL
            
        Returns:
            视频信息字典或None
        """
        try:
            self.logger.debug(f"开始解析百度百科链接: {url}")
            
            # 先尝试yt-dlp
            try:
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': False,
                    'format': 'worst[height<=720]/worst',
                    'writeinfojson': False,
                    'writesubtitles': False,
                    'writeautomaticsub': False,
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    
                    if info and info.get('url'):
                        title = info.get('title', 'baidu_video')
                        title = self._sanitize_filename(title)
                        
                        return {
                            'title': title,
                            'url': info['url'],
                            'ext': 'mp4'
                        }
            except Exception as e:
                self.logger.debug(f"yt-dlp解析百度百科失败，尝试手动解析: {str(e)}")
            
            # 手动解析百度百科页面
            return self._manual_extract_baidu(url)
            
        except NetworkError:
            raise
        except Exception as e:
            self.logger.error(f"解析百度百科视频失败: {str(e)}")
            raise ParseError(f"无法解析百度百科视频: {str(e)}")
    
    def _manual_extract_pinshan(self, url: str) -> Optional[Dict[str, Any]]:
        """
        手动解析品善网视频
        
        Args:
            url: 品善网视频页面URL
            
        Returns:
            视频信息字典或None
        """
        try:
            self.logger.debug("开始手动解析品善网页面")
            
            # 发送请求获取页面内容
            try:
                response = requests.get(url, headers=self.headers, timeout=30)
                response.raise_for_status()
                response.encoding = 'utf-8'
            except requests.exceptions.Timeout:
                raise NetworkError("请求超时")
            except requests.exceptions.ConnectionError:
                raise NetworkError("连接失败")
            except requests.exceptions.HTTPError as e:
                raise NetworkError(f"HTTP错误: {e.response.status_code}")
            
            self.logger.debug(f"页面请求成功，状态码: {response.status_code}")
            
            # 解析HTML
            try:
                soup = BeautifulSoup(response.text, 'html.parser')
            except Exception as e:
                raise ParseError(f"HTML解析失败: {str(e)}")
            
            # 查找视频相关元素
            video_urls = []
            
            # 方法1: 查找video标签
            video_tags = soup.find_all('video')
            for video in video_tags:
                src = video.get('src')
                if src:
                    if not src.startswith('http'):
                        src = urljoin(url, src)
                    video_urls.append(src)
                    self.logger.debug(f"找到video标签源: {src}")
            
            # 方法2: 查找source标签
            source_tags = soup.find_all('source')
            for source in source_tags:
                src = source.get('src')
                if src:
                    if not src.startswith('http'):
                        src = urljoin(url, src)
                    video_urls.append(src)
                    self.logger.debug(f"找到source标签源: {src}")
            
            # 方法3: 在JavaScript中查找视频URL
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    # 查找常见的视频URL模式
                    patterns = [
                        r'["\']([^"\'\']*\.mp4[^"\'\']*)["\']',
                        r'["\']([^"\'\']*\.flv[^"\'\']*)["\']',
                        r'["\']([^"\'\']*\.m3u8[^"\'\']*)["\']',
                        r'src[\s]*:[\s]*["\']([^"\'\']+)["\']',
                        r'url[\s]*:[\s]*["\']([^"\'\']+)["\']'
                    ]
                    
                    for pattern in patterns:
                        matches = re.findall(pattern, script.string)
                        for match in matches:
                            if any(ext in match.lower() for ext in ['.mp4', '.flv', '.m3u8']):
                                if not match.startswith('http'):
                                    match = urljoin(url, match)
                                video_urls.append(match)
                                self.logger.debug(f"在脚本中找到视频链接: {match}")
            
            # 方法4: 在页面文本中查找视频URL
            page_text = response.text
            video_patterns = [
                r'https?://[^\s"\'>]+\.mp4[^\s"\'>]*',
                r'https?://[^\s"\'>]+\.flv[^\s"\'>]*',
                r'https?://[^\s"\'>]+\.m3u8[^\s"\'>]*'
            ]
            
            for pattern in video_patterns:
                matches = re.findall(pattern, page_text)
                for match in matches:
                    video_urls.append(match)
                    self.logger.debug(f"在页面中找到视频链接: {match}")
            
            # 如果找到视频URL，返回第一个有效的
            for video_url in video_urls:
                if self._is_valid_video_url(video_url):
                    # 获取页面标题作为文件名
                    title = "pinshan_video"
                    title_tag = soup.find('title')
                    if title_tag and title_tag.string:
                        title = self._sanitize_filename(title_tag.string.strip())
                    
                    # 从URL推断文件扩展名
                    ext = 'mp4'
                    if '.' in video_url:
                        ext = video_url.split('.')[-1].split('?')[0].lower()
                        if ext not in ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'm4v', 'm3u8']:
                            ext = 'mp4'
                    
                    return {
                        'title': title,
                        'url': video_url,
                        'ext': ext
                    }
            
            self.logger.debug("未找到有效的视频URL")
            raise ParseError("页面中未找到视频内容")
            
        except NetworkError:
            raise
        except ParseError:
            raise
        except Exception as e:
            self.logger.error(f"手动解析品善网失败: {str(e)}")
            raise ParseError(f"解析失败: {str(e)}")
    
    def _manual_extract_baidu(self, url: str) -> Optional[Dict[str, Any]]:
        """
        手动解析百度百科视频
        
        Args:
            url: 百度百科视频页面URL
            
        Returns:
            视频信息字典或None
        """
        try:
            self.logger.debug("开始手动解析百度百科页面")
            
            # 发送请求获取页面内容，允许重定向
            try:
                response = requests.get(url, headers=self.headers, timeout=30, allow_redirects=True)
                response.raise_for_status()
                response.encoding = 'utf-8'
            except requests.exceptions.Timeout:
                raise NetworkError("请求超时")
            except requests.exceptions.ConnectionError:
                raise NetworkError("连接失败")
            except requests.exceptions.HTTPError as e:
                raise NetworkError(f"HTTP错误: {e.response.status_code}")
            
            final_url = response.url
            self.logger.debug(f"页面请求成功，状态码: {response.status_code}，最终URL: {final_url}")
            
            # 检查是否是错误页面
            if "你找的视频出错啦" in response.text or "抱歉" in response.text or "error" in response.text.lower():
                self.logger.debug("检测到百度百科错误页面")
                raise ParseError("该百度百科链接指向的视频不存在或已被删除")
            
            # 解析HTML
            try:
                soup = BeautifulSoup(response.text, 'html.parser')
            except Exception as e:
                raise ParseError(f"HTML解析失败: {str(e)}")
            
            # 查找视频相关元素
            video_urls = []
            
            # 方法1: 查找video标签
            video_tags = soup.find_all('video')
            for video in video_tags:
                src = video.get('src')
                if src:
                    if not src.startswith('http'):
                        src = urljoin(url, src)
                    video_urls.append(src)
                    self.logger.debug(f"找到video标签源: {src}")
            
            # 方法2: 查找source标签
            source_tags = soup.find_all('source')
            for source in source_tags:
                src = source.get('src')
                if src:
                    if not src.startswith('http'):
                        src = urljoin(url, src)
                    video_urls.append(src)
                    self.logger.debug(f"找到source标签源: {src}")
            
            # 方法3: 在页面文本中查找视频URL
            page_text = response.text
            # 查找.mp4结尾的URL
            mp4_pattern = r'https?://[^\s"\'>]+\.mp4[^\s"\'>]*'
            mp4_urls = re.findall(mp4_pattern, page_text)
            for mp4_url in mp4_urls:
                video_urls.append(mp4_url)
                self.logger.debug(f"在页面中找到mp4链接: {mp4_url}")
            
            # 方法4: 查找PAGE_DATA中的视频信息
            page_data_pattern = r'window\.PAGE_DATA\s*=\s*({.*?});'
            page_data_match = re.search(page_data_pattern, page_text)
            if page_data_match:
                try:
                    page_data = json.loads(page_data_match.group(1))
                    self.logger.debug(f"找到PAGE_DATA: {page_data}")
                    
                    # 尝试从PAGE_DATA中提取视频ID，然后构造API请求
                    if 'secondId' in page_data and 'lemmaId' in page_data:
                        second_id = page_data['secondId']
                        lemma_id = page_data['lemmaId']
                        
                        # 尝试构造百度百科视频API URL
                        api_url = f"https://baike.baidu.com/api/videoinfo?secondId={second_id}&lemmaId={lemma_id}"
                        self.logger.debug(f"尝试API请求: {api_url}")
                        
                        api_response = requests.get(api_url, headers=self.headers, timeout=10)
                        if api_response.status_code == 200:
                            api_data = api_response.json()
                            if 'data' in api_data and 'videoUrl' in api_data['data']:
                                video_url = api_data['data']['videoUrl']
                                if self._is_valid_video_url(video_url):
                                    video_urls.append(video_url)
                except Exception as e:
                    self.logger.debug(f"解析PAGE_DATA失败: {str(e)}")
            
            # 方法5: 查找script标签中的其他视频URL模式
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    text = script.string
                    # 查找各种视频URL模式
                    patterns = [
                        r'"(https?://[^"]+\.mp4[^"]*)"',
                        r"'(https?://[^']+\.mp4[^']*)'",
                        r'videoUrl["\']?\s*[:=]\s*["\']?(https?://[^"\'>\s]+)["\'>\s]',
                        r'src["\']?\s*[:=]\s*["\']?(https?://[^"\'>\s]+\.mp4[^"\'>\s]*)["\'>\s]',
                    ]
                    
                    for pattern in patterns:
                        matches = re.findall(pattern, text)
                        for match in matches:
                            if self._is_valid_video_url(match):
                                video_urls.append(match)
                                self.logger.debug(f"在脚本中找到视频链接: {match}")
            
            # 如果找到视频URL，返回第一个有效的
            for video_url in video_urls:
                if self._is_valid_video_url(video_url):
                    # 获取页面标题作为文件名
                    title = "baidu_video"
                    title_tag = soup.find('title')
                    if title_tag and title_tag.string:
                        title = self._sanitize_filename(title_tag.string.strip())
                    
                    # 从URL推断文件扩展名
                    ext = 'mp4'
                    if '.' in video_url:
                        ext = video_url.split('.')[-1].split('?')[0].lower()
                        if ext not in ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'm4v']:
                            ext = 'mp4'
                    
                    return {
                        'title': title,
                        'url': video_url,
                        'ext': ext
                    }
            
            self.logger.debug("未找到有效的视频URL")
            raise ParseError("页面中未找到视频内容")
            
        except NetworkError:
            raise
        except ParseError:
            raise
        except Exception as e:
            self.logger.error(f"手动解析百度百科失败: {str(e)}")
            raise ParseError(f"解析失败: {str(e)}")

    def _is_valid_video_url(self, url: str) -> bool:
        """
        检查URL是否为有效的视频URL
        
        Args:
            url: 待检查的URL
            
        Returns:
            bool: 是否为有效的视频URL
        """
        if not url or len(url) < 10:
            return False
        
        # 检查是否包含视频文件扩展名
        video_extensions = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.m3u8', '.ts']
        url_lower = url.lower()
        
        for ext in video_extensions:
            if ext in url_lower:
                return True
        
        # 检查是否包含视频相关关键词
        video_keywords = ['video', 'mp4', 'stream', 'media', 'play', 'watch', 'v=']
        for keyword in video_keywords:
            if keyword in url_lower:
                return True
        
        # 如果URL看起来像视频链接，也认为是有效的
        if url.startswith('http') and len(url) > 20:
            return True
        
        return False

    def _sanitize_filename(self, filename: str) -> str:
        """
        清理文件名，移除非法字符
        
        Args:
            filename: 原始文件名
            
        Returns:
            str: 清理后的文件名
        """
        # 移除非法字符
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        # 限制长度
        if len(filename) > 100:
            filename = filename[:100]
        return filename.strip()

    def _download_file(self, video_info: Dict[str, Any]) -> bool:
        """
        下载视频文件
        
        Args:
            video_info: 视频信息字典
            
        Returns:
            bool: 下载是否成功
        """
        try:
            video_url = video_info['url']
            title = video_info['title']
            ext = video_info.get('ext', 'mp4')
            
            # 构建文件名
            filename = f"{title}.{ext}"
            filepath = self.download_dir / filename
            
            # 如果文件已存在，添加序号
            counter = 1
            original_filepath = filepath
            while filepath.exists():
                name_part = original_filepath.stem
                ext_part = original_filepath.suffix
                filepath = self.download_dir / f"{name_part}_{counter}{ext_part}"
                counter += 1
            
            self.logger.info(f"开始下载: {filename}")
            self.logger.debug(f"视频URL: {video_url}")
            
            # 尝试直接下载
            try:
                response = requests.get(video_url, headers=self.headers, stream=True, timeout=30)
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                
                with open(filepath, 'wb') as f:
                    if total_size > 0:
                        with tqdm(total=total_size, unit='B', unit_scale=True, desc=filename) as pbar:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                                    pbar.update(len(chunk))
                    else:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                
                self.logger.info(f"下载完成: {filepath}")
                return True
                
            except Exception as e:
                self.logger.debug(f"直接下载失败，尝试使用yt-dlp: {str(e)}")
                
                # 如果直接下载失败，尝试使用yt-dlp下载
                return self._download_with_ytdlp(video_url, filepath)
            
        except Exception as e:
            self.logger.error(f"下载失败: {str(e)}")
            return False
    
    def _extract_sohu_video(self, url: str) -> Optional[Dict[str, Any]]:
        """
        提取搜狐视频信息
        
        Args:
            url: 搜狐视频URL
            
        Returns:
            Dict: 视频信息字典或None
        """
        try:
            self.logger.info(f"开始解析搜狐视频: {url}")
            
            # 提取视频ID
            video_id = self._extract_sohu_video_id(url)
            if not video_id:
                self.logger.error("无法提取搜狐视频ID")
                return None
            
            self.logger.info(f"提取到视频ID: {video_id}")
            
            # 尝试使用yt-dlp直接下载
            if self._try_ytdlp_download_sohu(url, f"sohu_{video_id}"):
                return {
                    'title': f'搜狐视频_{video_id}',
                    'url': url,
                    'video_id': video_id,
                    'site': 'sohu',
                    'download_method': 'ytdlp'
                }
            
            # 使用Selenium获取视频源
            video_url = self._selenium_extract_sohu(url, video_id)
            if video_url:
                return {
                    'title': f'搜狐视频_{video_id}',
                    'url': video_url,
                    'video_id': video_id,
                    'site': 'sohu',
                    'download_method': 'selenium'
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"搜狐视频解析失败: {str(e)}")
            return None
    
    def _extract_360kan_video(self, url: str) -> Optional[Dict[str, Any]]:
        """
        提取360kan视频信息
        
        Args:
            url: 360kan视频URL
            
        Returns:
            Dict: 视频信息字典或None
        """
        try:
            self.logger.info(f"开始解析360kan视频: {url}")
            
            # 解析URL参数
            parsed_url = urlparse(url)
            params = parse_qs(parsed_url.query)
            video_id = params.get('id', [None])[0]
            
            if not video_id:
                self.logger.error("无法提取360kan视频ID")
                return None
            
            self.logger.info(f"提取到视频ID: {video_id}")
            
            # 尝试使用yt-dlp直接下载
            if self._try_ytdlp_download_sohu(url, f"360kan_{video_id}"):
                return {
                    'title': f'360kan视频_{video_id}',
                    'url': url,
                    'video_id': video_id,
                    'site': '360kan',
                    'download_method': 'ytdlp'
                }
            
            # 通过Selenium获取乐视iframe中的视频
            video_url = self._selenium_extract_360kan(url, video_id)
            if video_url:
                return {
                    'title': f'360kan视频_{video_id}',
                    'url': video_url,
                    'video_id': video_id,
                    'site': '360kan',
                    'download_method': 'selenium'
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"360kan视频解析失败: {str(e)}")
            return None
    
    def _extract_sohu_video_id(self, url: str) -> Optional[str]:
        """
        提取搜狐视频ID
        
        Args:
            url: 搜狐视频URL
            
        Returns:
            str: 视频ID或None
        """
        try:
            if '.html' in url:
                encoded_part = url.split('/')[-1].replace('.html', '')
                decoded_bytes = base64.b64decode(encoded_part)
                decoded_url = decoded_bytes.decode('utf-8')
                self.logger.info(f"解码后的URL: {decoded_url}")
                
                # 提取视频ID
                vid_match = re.search(r'/(\d+)\.shtml', decoded_url)
                if vid_match:
                    return vid_match.group(1)
            
            return None
        except Exception as e:
            self.logger.error(f"提取搜狐视频ID失败: {str(e)}")
            return None
    
    def _try_ytdlp_download_sohu(self, url: str, filename_prefix: str) -> bool:
        """
        尝试使用yt-dlp下载搜狐/360kan视频
        
        Args:
            url: 视频URL
            filename_prefix: 文件名前缀
            
        Returns:
            bool: 下载是否成功
        """
        try:
            self.logger.info(f"尝试使用yt-dlp下载视频...")
            
            # 构建yt-dlp命令
            output_template = str(self.download_dir / f"{filename_prefix}_%(title)s.%(ext)s")
            cmd = [
                'yt-dlp',
                '--output', output_template,
                '--format', 'best[ext=mp4]/best',
                '--no-playlist',
                '--no-warnings',
                url
            ]
            
            # 执行命令
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.logger.info(f"yt-dlp下载成功")
                return True
            else:
                self.logger.warning(f"yt-dlp下载失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("yt-dlp下载超时")
            return False
        except FileNotFoundError:
            self.logger.warning("yt-dlp未安装，跳过此方法")
            return False
        except Exception as e:
            self.logger.error(f"yt-dlp下载异常: {str(e)}")
            return False
    
    def _selenium_extract_sohu(self, url: str, video_id: str) -> Optional[str]:
        """
        使用Selenium提取搜狐视频源
        
        Args:
            url: 搜狐视频URL
            video_id: 视频ID
            
        Returns:
            str: 视频源URL或None
        """
        self.logger.info("使用Selenium获取搜狐视频源...")
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        driver = None
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # 访问页面
            driver.get(url)
            
            # 等待页面加载
            self.logger.info("等待页面加载...")
            time.sleep(10)
            
            # 查找视频元素
            video_elements = driver.find_elements(By.TAG_NAME, 'video')
            self.logger.info(f"找到 {len(video_elements)} 个video元素")
            
            for video in video_elements:
                src = video.get_attribute('src')
                if src and src.startswith('http'):
                    self.logger.info(f"找到视频源: {src}")
                    return src
            
            # 如果没有找到video元素，尝试查找页面中的视频URL
            page_source = driver.page_source
            video_urls = re.findall(r'https?://[^\s"]+\.mp4[^\s"]*', page_source)
            
            if video_urls:
                self.logger.info(f"页面源码中找到 {len(video_urls)} 个视频URL")
                return video_urls[0]  # 返回第一个找到的视频URL
            
            return None
            
        except Exception as e:
            self.logger.error(f"Selenium提取搜狐视频失败: {str(e)}")
            return None
        finally:
            if driver:
                driver.quit()
    
    def _selenium_extract_360kan(self, url: str, video_id: str) -> Optional[str]:
        """
        使用Selenium提取360kan视频源（实际是乐视视频）
        
        Args:
            url: 360kan视频URL
            video_id: 视频ID
            
        Returns:
            str: 视频源URL或None
        """
        self.logger.info("使用Selenium获取360kan视频源...")
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        driver = None
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # 访问页面
            driver.get(url)
            
            # 等待页面加载
            self.logger.info("等待页面加载...")
            time.sleep(10)
            
            # 查找iframe（根据分析结果，视频在乐视iframe中）
            iframes = driver.find_elements(By.TAG_NAME, 'iframe')
            self.logger.info(f"找到 {len(iframes)} 个iframe元素")
            
            for iframe in iframes:
                src = iframe.get_attribute('src')
                if src and 'le.com' in src:
                    self.logger.info(f"找到乐视iframe: {src}")
                    
                    # 进入iframe分析
                    try:
                        driver.switch_to.frame(iframe)
                        time.sleep(8)  # 等待iframe内容加载
                        
                        # 查找视频元素
                        video_elements = driver.find_elements(By.TAG_NAME, 'video')
                        self.logger.info(f"iframe中找到 {len(video_elements)} 个video元素")
                        
                        for video in video_elements:
                            video_src = video.get_attribute('src')
                            if video_src and video_src.startswith('http'):
                                self.logger.info(f"iframe中找到视频源: {video_src[:100]}...")
                                return video_src
                        
                        # 如果没有找到video元素，查找页面源码中的视频URL
                        iframe_source = driver.page_source
                        video_urls = re.findall(r'https?://[^\s"]+\.mp4[^\s"]*', iframe_source)
                        
                        if video_urls:
                            self.logger.info(f"iframe源码中找到 {len(video_urls)} 个视频URL")
                            return video_urls[0]  # 返回第一个找到的视频URL
                        
                        driver.switch_to.default_content()
                        
                    except Exception as e:
                        self.logger.warning(f"iframe分析失败: {str(e)}")
                        driver.switch_to.default_content()
            
            return None
            
        except Exception as e:
            self.logger.error(f"Selenium提取360kan视频失败: {str(e)}")
            return None
        finally:
            if driver:
                driver.quit()
    
    def _download_with_ytdlp(self, url: str, filepath: Path) -> bool:
        """
        使用yt-dlp下载视频
        
        Args:
            url: 视频URL
            filepath: 保存路径
            
        Returns:
            bool: 下载是否成功
        """
        try:
            self.logger.debug(f"使用yt-dlp下载: {url}")
            
            # 配置yt-dlp选项
            ydl_opts = {
                'outtmpl': str(filepath.with_suffix('')) + '.%(ext)s',
                # 不指定format，让yt-dlp自动选择最佳格式
                'quiet': True,
                'no_warnings': True,
                'noplaylist': True,  # 关键：只下载单个视频，不下载播放列表
                'playlist_items': '1',  # 额外保险：只下载第一个项目
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # 检查文件是否下载成功
            downloaded_files = list(filepath.parent.glob(f"{filepath.stem}.*"))
            if downloaded_files:
                self.logger.info(f"yt-dlp下载完成: {downloaded_files[0]}")
                
                # 检查是否需要合并视频和音频文件
                self._post_process_downloaded_files()
                
                return True
            else:
                self.logger.error("yt-dlp下载失败，未找到下载的文件")
                return False
                
        except Exception as e:
            self.logger.error(f"yt-dlp下载失败: {str(e)}")
            return False
    
    def _post_process_downloaded_files(self):
        """
        后处理下载的文件，合并分离的视频和音频文件，并验证音频质量
        """
        try:
            # 查找可能的视频和音频文件
            video_files = []
            audio_files = []
            mp4_files = []
            
            # 搜索所有相关文件
            all_files = list(self.download_dir.glob("*"))
            
            for file_path in all_files:
                if file_path.is_file() and not file_path.name.endswith('.log'):
                    file_ext = file_path.suffix.lower()
                    if file_ext in ['.mp4', '.mkv', '.webm', '.avi'] and '.f' in file_path.name:
                        video_files.append(str(file_path))
                    elif file_ext in ['.m4a', '.mp3', '.aac', '.wav'] and '.f' in file_path.name:
                        audio_files.append(str(file_path))
                    elif file_ext == '.mp4' and '.f' not in file_path.name:
                        mp4_files.append(str(file_path))
            
            self.logger.debug(f"找到视频文件: {video_files}")
            self.logger.debug(f"找到音频文件: {audio_files}")
            self.logger.debug(f"找到MP4文件: {mp4_files}")
            
            # 如果同时有视频和音频文件，尝试合并
            if len(video_files) >= 1 and len(audio_files) >= 1:
                # 找到匹配的视频和音频文件对
                for video_file in video_files:
                    video_base = Path(video_file).stem.split('.f')[0]
                    for audio_file in audio_files:
                        audio_base = Path(audio_file).stem.split('.f')[0]
                        if video_base == audio_base:
                            merged_file = self._merge_video_audio(video_file, audio_file, video_base)
                            if merged_file:
                                mp4_files.append(merged_file)
                            break
            
            # 验证和修复所有MP4文件的音频
            for mp4_file in mp4_files:
                self._verify_and_fix_audio(mp4_file)
            
        except Exception as e:
            self.logger.warning(f"后处理文件失败: {str(e)}")
    
    def _merge_video_audio(self, video_path: str, audio_path: str, filename_stem: str):
        """
        使用ffmpeg合并视频和音频文件
        
        Args:
            video_path: 视频文件路径
            audio_path: 音频文件路径
            filename_stem: 输出文件名前缀
            
        Returns:
            str: 合并后的文件路径，失败时返回None
        """
        try:
            self.logger.info(f"开始使用ffmpeg合并视频和音频文件...")
            
            # 输出文件路径
            output_path = self.download_dir / f"{filename_stem}_merged.mp4"
            
            # 构建ffmpeg命令 - 使用本地ffmpeg可执行文件
            ffmpeg_path = self.download_dir.parent / 'ffmpeg' / 'ffmpeg-8.0-essentials_build' / 'bin' / 'ffmpeg.exe'
            cmd = [
                str(ffmpeg_path),
                '-i', video_path,
                '-i', audio_path,
                '-c:v', 'copy',  # 复制视频流，不重新编码
                '-c:a', 'aac',   # 音频编码为aac
                '-b:a', '128k',  # 设置音频比特率
                '-ar', '44100',  # 设置采样率
                '-ac', '2',      # 设置声道数
                '-strict', 'experimental',
                '-y',  # 覆盖输出文件
                str(output_path)
            ]
            
            # 执行ffmpeg命令
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.logger.info(f"合并完成: {output_path}")
                
                # 删除原始的分离文件
                try:
                    os.remove(video_path)
                    os.remove(audio_path)
                    self.logger.debug("已删除原始分离文件")
                except Exception as e:
                    self.logger.warning(f"删除原始文件失败: {str(e)}")
                    
                return str(output_path)
            else:
                self.logger.error(f"ffmpeg合并失败: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            self.logger.error("ffmpeg合并超时")
            return None
        except FileNotFoundError:
            self.logger.warning("ffmpeg未安装，无法合并视频和音频文件")
            return None
        except Exception as e:
            self.logger.error(f"合并视频音频失败: {str(e)}")
            return None
    
    def _verify_and_fix_audio(self, mp4_file: str):
        """
        验证MP4文件的音频流，如果有问题则自动修复
        
        Args:
            mp4_file: MP4文件路径
        """
        try:
            self.logger.info(f"验证音频流: {mp4_file}")
            
            # 使用ffprobe检查音频流
            ffprobe_path = self.download_dir.parent / 'ffmpeg' / 'ffmpeg-8.0-essentials_build' / 'bin' / 'ffprobe.exe'
            
            # 检查是否有音频流
            cmd_check = [
                str(ffprobe_path),
                '-v', 'error',
                '-select_streams', 'a:0',
                '-show_entries', 'stream=codec_name,sample_rate,channels,bit_rate',
                '-of', 'csv=p=0',
                mp4_file
            ]
            
            result = subprocess.run(cmd_check, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0 or not result.stdout.strip():
                self.logger.warning(f"文件 {mp4_file} 没有音频流或音频流损坏")
                return
            
            # 解析音频流信息
            audio_info = result.stdout.strip().split(',')
            if len(audio_info) < 3:
                self.logger.warning(f"无法解析音频流信息: {mp4_file}")
                return
                
            codec_name = audio_info[0]
            sample_rate = audio_info[1] if len(audio_info) > 1 else '0'
            channels = audio_info[2] if len(audio_info) > 2 else '0'
            bit_rate = audio_info[3] if len(audio_info) > 3 else '0'
            
            self.logger.debug(f"音频信息 - 编码: {codec_name}, 采样率: {sample_rate}, 声道: {channels}, 比特率: {bit_rate}")
            
            # 检查是否需要修复
            needs_fix = False
            
            # 检查比特率是否过低
            try:
                bit_rate_int = int(bit_rate)
                if bit_rate_int < 64000:  # 比特率低于64kbps
                    needs_fix = True
                    self.logger.info(f"音频比特率过低 ({bit_rate_int}), 需要修复")
            except (ValueError, TypeError):
                needs_fix = True
                self.logger.info("无法获取音频比特率，需要修复")
            
            # 检查采样率
            try:
                sample_rate_int = int(sample_rate)
                if sample_rate_int < 22050:  # 采样率过低
                    needs_fix = True
                    self.logger.info(f"音频采样率过低 ({sample_rate_int}), 需要修复")
            except (ValueError, TypeError):
                pass
            
            # 如果需要修复，重新编码音频
            if needs_fix:
                self._fix_audio_stream(mp4_file)
            else:
                self.logger.info(f"音频流正常: {mp4_file}")
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"音频验证超时: {mp4_file}")
        except FileNotFoundError:
            self.logger.warning("ffprobe未找到，跳过音频验证")
        except Exception as e:
            self.logger.error(f"音频验证失败: {str(e)}")
    
    def _fix_audio_stream(self, mp4_file: str):
        """
        修复MP4文件的音频流
        
        Args:
            mp4_file: MP4文件路径
        """
        try:
            self.logger.info(f"修复音频流: {mp4_file}")
            
            # 生成修复后的文件名
            file_path = Path(mp4_file)
            fixed_file = file_path.parent / f"{file_path.stem}_fixed_audio.mp4"
            
            # 使用ffmpeg重新编码音频
            ffmpeg_path = self.download_dir.parent / 'ffmpeg' / 'ffmpeg-8.0-essentials_build' / 'bin' / 'ffmpeg.exe'
            cmd = [
                str(ffmpeg_path),
                '-i', mp4_file,
                '-c:v', 'copy',  # 复制视频流
                '-c:a', 'aac',   # 重新编码音频为AAC
                '-b:a', '128k',  # 设置音频比特率为128k
                '-ar', '44100',  # 设置采样率为44.1kHz
                '-ac', '2',      # 设置为立体声
                '-y',            # 覆盖输出文件
                str(fixed_file)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.logger.info(f"音频修复完成: {fixed_file}")
                
                # 替换原文件
                try:
                    os.remove(mp4_file)
                    os.rename(str(fixed_file), mp4_file)
                    self.logger.info(f"已替换原文件: {mp4_file}")
                except Exception as e:
                    self.logger.warning(f"替换文件失败: {str(e)}")
            else:
                self.logger.error(f"音频修复失败: {result.stderr}")
                # 删除失败的输出文件
                if fixed_file.exists():
                    try:
                        os.remove(str(fixed_file))
                    except Exception:
                        pass
                        
        except subprocess.TimeoutExpired:
            self.logger.error(f"音频修复超时: {mp4_file}")
        except Exception as e:
            self.logger.error(f"音频修复失败: {str(e)}")


def main():
    """主函数"""
    print("=== 视频下载工具 ===")
    print("支持的网站: 百度百科")
    print()
    
    downloader = VideoDownloader()
    
    while True:
        try:
            url = input("请输入视频链接 (输入 'quit' 退出): ").strip()
            
            if url.lower() in ['quit', 'exit', 'q']:
                print("再见！")
                break
            
            if not url:
                print("请输入有效的URL")
                continue
            
            if not url.startswith(('http://', 'https://')):
                print("请输入完整的URL（包含http://或https://）")
                continue
            
            print(f"\n开始下载: {url}")
            success = downloader.download_video(url)
            
            if success:
                print("✅ 下载成功！")
            else:
                print("❌ 下载失败，请查看日志了解详情")
            
            print("-" * 50)
            
        except KeyboardInterrupt:
            print("\n用户中断，退出程序")
            break
        except VideoDownloadError as e:
            print(f"下载错误: {str(e)}")
        except Exception as e:
            print(f"未知错误: {str(e)}")


if __name__ == "__main__":
    main()