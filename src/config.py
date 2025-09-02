#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video Downloader Configuration

Centralized configuration management for all supported sites and system settings.
"""

import os
from typing import Dict, List

class DownloaderConfig:
    """Video downloader configuration class"""
    
    BASE_CONFIG = {
        'download_dir': 'downloads',
        'max_retries': 3,
        'timeout': 180,
        'max_concurrent_downloads': 3,
        'log_level': 'INFO',
        'log_file': 'downloader.log'
    }
    
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    ]
    
    SITE_CONFIGS = {
        'bilibili': {
            'name': 'Bilibili',
            'domain': 'bilibili.com',
            'base_url': 'https://www.bilibili.com',
            'referer': 'https://www.bilibili.com/',
            'supported': True,
            'formats': {
                'high_quality': ['100024+30280', '100023+30232', '100022+30216'],
                'medium_quality': ['80+30280', '64+30216', '32+30216'],
                'low_quality': ['16+30216', 'worst']
            },
            'cookies_required': False,
            'login_required': False,
            'rate_limit': 1.0,  # 秒
            'output_template': 'bilibili_%(title)s.%(ext)s',
            'extra_args': [
                '--write-info-json',
                '--write-thumbnail'
            ]
        },
        
        'sohu': {
            'name': 'Sohu Video',
            'domain': 'sohu.com',
            'base_url': 'https://tv.sohu.com',
            'referer': 'https://tv.sohu.com/',
            'supported': True,
            'formats': {
                'high_quality': ['best'],
                'medium_quality': ['720p', '480p'],
                'low_quality': ['360p', 'worst']
            },
            'cookies_required': False,
            'login_required': False,
            'rate_limit': 2.0,
            'output_template': 'sohu_%(title)s.%(ext)s',
            'url_decode_required': True,
            'extra_args': []
        },
        
        '360kan': {
            'name': '360kan Video',
            'domain': '360kan.com',
            'base_url': 'https://tv.360kan.com',
            'referer': 'https://tv.360kan.com/',
            'supported': False,  # Not supported by yt-dlp
            'formats': {
                'high_quality': ['best'],
                'medium_quality': ['720p', '480p'],
                'low_quality': ['360p', 'worst']
            },
            'cookies_required': False,
            'login_required': False,
            'rate_limit': 2.0,
            'output_template': '360kan_%(title)s.%(ext)s',
            'selenium_required': True,
            'extra_args': []
        },
        
        'youtube': {
            'name': 'YouTube',
            'domain': 'youtube.com',
            'base_url': 'https://www.youtube.com',
            'referer': 'https://www.youtube.com/',
            'supported': True,
            'formats': {
                'high_quality': ['best[height<=1080]', 'best[height<=720]'],
                'medium_quality': ['best[height<=480]', 'best[height<=360]'],
                'low_quality': ['worst']
            },
            'cookies_required': False,
            'login_required': False,
            'rate_limit': 1.0,
            'output_template': 'youtube_%(title)s.%(ext)s',
            'extra_args': [
                '--write-info-json',
                '--write-thumbnail',
                '--write-description'
            ]
        }
    }
    
    YTDLP_CONFIG = {
        'default_format': 'best',
        'extract_flat': False,
        'writeinfojson': False,
        'writethumbnail': False,
        'writesubtitles': False,
        'writeautomaticsub': False,
        'ignoreerrors': True,
        'no_warnings': False,
        'extractaudio': False,
        'audioformat': 'mp3',
        'audioquality': '192',
        'embed_subs': False,
        'writesubtitles': False
    }
    
    SELENIUM_CONFIG = {
        'headless': True,
        'window_size': (1920, 1080),
        'page_load_timeout': 30,
        'implicit_wait': 10,
        'chrome_options': [
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--disable-extensions',
            '--disable-plugins',
            '--disable-images',
            '--disable-javascript'
        ]
    }
    
    ERROR_CONFIG = {
        'max_retries': 3,
        'retry_delay': 2.0,
        'timeout_errors': [
            'TimeoutError',
            'subprocess.TimeoutExpired',
            'requests.exceptions.Timeout'
        ],
        'network_errors': [
            'ConnectionError',
            'requests.exceptions.ConnectionError',
            'urllib3.exceptions.NewConnectionError'
        ],
        'recoverable_errors': [
            'HTTP Error 429',
            'HTTP Error 503',
            'HTTP Error 502'
        ]
    }
    
    FILE_CONFIG = {
        'allowed_extensions': ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v'],
        'audio_extensions': ['.mp3', '.aac', '.m4a', '.ogg', '.wav', '.flac'],
        'max_filename_length': 200,
        'sanitize_filename': True,
        'create_subdirs': True,
        'subdir_pattern': '%Y-%m-%d',
        'duplicate_handling': 'skip'  # Options: skip, overwrite, rename
    }
    
    PERFORMANCE_CONFIG = {
        'concurrent_downloads': 3,
        'chunk_size': 1024 * 1024,  # 1MB
        'buffer_size': 8192,
        'connection_pool_size': 10,
        'dns_cache_timeout': 300
    }
    
    @classmethod
    def get_site_config(cls, site_name: str) -> Dict:
        """获取指定网站的配置"""
        return cls.SITE_CONFIGS.get(site_name, {})
    
    @classmethod
    def get_supported_sites(cls) -> List[str]:
        """获取支持的网站列表"""
        return [site for site, config in cls.SITE_CONFIGS.items() if config.get('supported', False)]
    
    @classmethod
    def detect_site(cls, url: str) -> str:
        """检测URL对应的网站"""
        for site, config in cls.SITE_CONFIGS.items():
            if config['domain'] in url:
                return site
        return 'unknown'
    
    @classmethod
    def get_user_agent(cls, index: int = 0) -> str:
        """获取用户代理"""
        return cls.USER_AGENTS[index % len(cls.USER_AGENTS)]
    
    @classmethod
    def get_download_dir(cls) -> str:
        """获取下载目录"""
        download_dir = cls.BASE_CONFIG['download_dir']
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
        return download_dir
    
    @classmethod
    def get_log_config(cls) -> Dict:
        """获取日志配置"""
        return {
            'level': cls.BASE_CONFIG['log_level'],
            'filename': os.path.join(cls.get_download_dir(), cls.BASE_CONFIG['log_file']),
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }
    
    @classmethod
    def validate_config(cls) -> bool:
        """验证配置的有效性"""
        try:
            # 检查必要的目录
            download_dir = cls.get_download_dir()
            if not os.access(download_dir, os.W_OK):
                print(f"警告: 下载目录 {download_dir} 不可写")
                return False
            
            # 检查网站配置
            for site, config in cls.SITE_CONFIGS.items():
                required_keys = ['name', 'domain', 'base_url', 'referer', 'supported']
                for key in required_keys:
                    if key not in config:
                        print(f"错误: 网站 {site} 缺少配置项 {key}")
                        return False
            
            print("✅ 配置验证通过")
            return True
            
        except Exception as e:
            print(f"❌ 配置验证失败: {e}")
            return False
    
    @classmethod
    def print_config_summary(cls):
        """打印配置摘要"""
        print("=" * 60)
        print("视频下载器配置摘要")
        print("=" * 60)
        print(f"下载目录: {cls.get_download_dir()}")
        print(f"最大重试次数: {cls.BASE_CONFIG['max_retries']}")
        print(f"超时时间: {cls.BASE_CONFIG['timeout']}秒")
        print(f"最大并发下载: {cls.BASE_CONFIG['max_concurrent_downloads']}")
        print()
        
        print("支持的网站:")
        for site in cls.get_supported_sites():
            config = cls.get_site_config(site)
            print(f"  ✅ {config['name']} ({config['domain']})")
        
        print("\n不支持的网站:")
        for site, config in cls.SITE_CONFIGS.items():
            if not config.get('supported', False):
                reason = "需要Selenium" if config.get('selenium_required') else "yt-dlp不支持"
                print(f"  ❌ {config['name']} ({config['domain']}) - {reason}")
        
        print("\n" + "=" * 60)

# 配置验证和初始化
if __name__ == "__main__":
    print("=== 视频下载器配置模块 ===")
    DownloaderConfig.print_config_summary()
    DownloaderConfig.validate_config()