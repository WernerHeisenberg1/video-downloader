#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化的视频下载器 - 整合所有功能
支持多网站、多线程、智能重试
"""

import subprocess
import logging
import os
import requests
import base64
import threading
import time
import json
from datetime import datetime
from urllib.parse import urlparse
from typing import Dict, List, Optional, Tuple

class VideoDownloaderConfig:
    """下载器配置类"""
    
    def __init__(self):
        self.download_dir = "downloads"
        self.max_retries = 3
        self.timeout = 180
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
        self.supported_sites = {
            'bilibili': {
                'domain': 'bilibili.com',
                'referer': 'https://www.bilibili.com/',
                'formats': ['100024+30280', '100023+30232', '100022+30216']
            },
            'sohu': {
                'domain': 'sohu.com',
                'referer': 'https://tv.sohu.com/',
                'formats': ['best', 'worst']
            },
            '360kan': {
                'domain': '360kan.com',
                'referer': 'https://tv.360kan.com/',
                'formats': ['best', 'worst']
            }
        }

class DownloadResult:
    """下载结果类"""
    
    def __init__(self, url: str, site: str):
        self.url = url
        self.site = site
        self.status = 'pending'  # pending, success, failed, error
        self.files = []
        self.error_message = ''
        self.download_time = 0
        self.file_size = 0
    
    def to_dict(self) -> Dict:
        return {
            'url': self.url,
            'site': self.site,
            'status': self.status,
            'files': self.files,
            'error_message': self.error_message,
            'download_time': self.download_time,
            'file_size': self.file_size
        }

class SiteHandler:
    """网站处理器基类"""
    
    def __init__(self, config: VideoDownloaderConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def detect_site(self, url: str) -> str:
        """检测网站类型"""
        for site, info in self.config.supported_sites.items():
            if info['domain'] in url:
                return site
        return 'unknown'
    
    def download(self, url: str, result: DownloadResult) -> bool:
        """下载视频 - 子类需要实现"""
        raise NotImplementedError

class BilibiliHandler(SiteHandler):
    """Bilibili处理器"""
    
    def download(self, url: str, result: DownloadResult) -> bool:
        """下载Bilibili视频"""
        site_config = self.config.supported_sites['bilibili']
        
        for format_str in site_config['formats']:
            try:
                cmd = [
                    'yt-dlp',
                    '--format', format_str,
                    '--output', f'{self.config.download_dir}/bilibili_opt_%(title)s.%(ext)s',
                    '--user-agent', self.config.user_agents[0],
                    '--referer', site_config['referer'],
                    url
                ]
                
                start_time = time.time()
                process_result = subprocess.run(
                    cmd, capture_output=True, text=True, 
                    timeout=self.config.timeout
                )
                result.download_time = time.time() - start_time
                
                if process_result.returncode == 0:
                    result.status = 'success'
                    self.logger.info(f"Bilibili下载成功: {format_str}")
                    return True
                else:
                    self.logger.warning(f"Bilibili格式 {format_str} 失败: {process_result.stderr}")
                    
            except subprocess.TimeoutExpired:
                result.error_message = f"下载超时 (>{self.config.timeout}s)"
                self.logger.error(f"Bilibili下载超时: {format_str}")
            except Exception as e:
                result.error_message = str(e)
                self.logger.error(f"Bilibili下载异常: {e}")
        
        result.status = 'failed'
        return False

class SohuHandler(SiteHandler):
    """搜狐视频处理器"""
    
    def decode_url(self, url: str) -> Optional[str]:
        """解码搜狐视频URL"""
        try:
            parsed = urlparse(url)
            if '.html' in parsed.path:
                encoded_part = parsed.path.split('/')[-1].replace('.html', '')
                decoded = base64.b64decode(encoded_part + '==').decode('utf-8')
                self.logger.info(f"搜狐URL解码: {decoded}")
                return decoded
        except Exception as e:
            self.logger.error(f"搜狐URL解码失败: {e}")
        return None
    
    def download(self, url: str, result: DownloadResult) -> bool:
        """下载搜狐视频"""
        # 先解码URL
        decoded_info = self.decode_url(url)
        
        site_config = self.config.supported_sites['sohu']
        
        for format_str in site_config['formats']:
            try:
                cmd = [
                    'yt-dlp',
                    '--format', format_str,
                    '--output', f'{self.config.download_dir}/sohu_opt_%(title)s.%(ext)s',
                    '--user-agent', self.config.user_agents[0],
                    '--referer', site_config['referer'],
                    url
                ]
                
                start_time = time.time()
                process_result = subprocess.run(
                    cmd, capture_output=True, text=True,
                    timeout=self.config.timeout
                )
                result.download_time = time.time() - start_time
                
                if process_result.returncode == 0:
                    result.status = 'success'
                    self.logger.info(f"搜狐下载成功: {format_str}")
                    return True
                else:
                    self.logger.warning(f"搜狐格式 {format_str} 失败: {process_result.stderr}")
                    
            except subprocess.TimeoutExpired:
                result.error_message = f"下载超时 (>{self.config.timeout}s)"
                self.logger.error(f"搜狐下载超时: {format_str}")
            except Exception as e:
                result.error_message = str(e)
                self.logger.error(f"搜狐下载异常: {e}")
        
        result.status = 'failed'
        return False

class Kan360Handler(SiteHandler):
    """360看视频处理器"""
    
    def download(self, url: str, result: DownloadResult) -> bool:
        """下载360看视频"""
        site_config = self.config.supported_sites['360kan']
        
        for format_str in site_config['formats']:
            try:
                cmd = [
                    'yt-dlp',
                    '--format', format_str,
                    '--output', f'{self.config.download_dir}/360kan_opt_%(title)s.%(ext)s',
                    '--user-agent', self.config.user_agents[0],
                    '--referer', site_config['referer'],
                    url
                ]
                
                start_time = time.time()
                process_result = subprocess.run(
                    cmd, capture_output=True, text=True,
                    timeout=self.config.timeout
                )
                result.download_time = time.time() - start_time
                
                if process_result.returncode == 0:
                    result.status = 'success'
                    self.logger.info(f"360看下载成功: {format_str}")
                    return True
                else:
                    self.logger.warning(f"360看格式 {format_str} 失败: {process_result.stderr}")
                    
            except subprocess.TimeoutExpired:
                result.error_message = f"下载超时 (>{self.config.timeout}s)"
                self.logger.error(f"360看下载超时: {format_str}")
            except Exception as e:
                result.error_message = str(e)
                self.logger.error(f"360看下载异常: {e}")
        
        result.status = 'failed'
        return False

class OptimizedVideoDownloader:
    """优化的视频下载器主类"""
    
    def __init__(self):
        self.config = VideoDownloaderConfig()
        self.setup_logging()
        self.setup_handlers()
        self.results: List[DownloadResult] = []
        self.create_download_dir()
    
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'{self.config.download_dir}/optimized_downloader.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('OptimizedVideoDownloader')
    
    def setup_handlers(self):
        """设置网站处理器"""
        self.handlers = {
            'bilibili': BilibiliHandler(self.config),
            'sohu': SohuHandler(self.config),
            '360kan': Kan360Handler(self.config)
        }
    
    def create_download_dir(self):
        """创建下载目录"""
        if not os.path.exists(self.config.download_dir):
            os.makedirs(self.config.download_dir)
    
    def detect_site(self, url: str) -> str:
        """检测网站类型"""
        for site, info in self.config.supported_sites.items():
            if info['domain'] in url:
                return site
        return 'unknown'
    
    def download_single_video(self, url: str, thread_id: int = 0) -> DownloadResult:
        """下载单个视频"""
        site = self.detect_site(url)
        result = DownloadResult(url, site)
        
        self.logger.info(f"[线程{thread_id}] 开始下载: {site} - {url[:50]}...")
        
        if site == 'unknown':
            result.status = 'failed'
            result.error_message = '不支持的网站类型'
            self.logger.error(f"[线程{thread_id}] 不支持的网站: {url}")
            return result
        
        handler = self.handlers.get(site)
        if handler:
            success = handler.download(url, result)
            if success:
                self.logger.info(f"[线程{thread_id}] 下载成功: {site}")
            else:
                self.logger.error(f"[线程{thread_id}] 下载失败: {site} - {result.error_message}")
        else:
            result.status = 'failed'
            result.error_message = f'没有找到 {site} 的处理器'
        
        return result
    
    def download_multiple_videos(self, urls: List[str]) -> Dict:
        """多线程下载多个视频"""
        self.logger.info(f"开始批量下载 {len(urls)} 个视频")
        start_time = time.time()
        
        threads = []
        results = []
        
        def download_worker(url: str, thread_id: int):
            result = self.download_single_video(url, thread_id)
            results.append(result)
        
        # 启动线程
        for i, url in enumerate(urls, 1):
            thread = threading.Thread(
                target=download_worker,
                args=(url, i)
            )
            threads.append(thread)
            thread.start()
            time.sleep(0.5)  # 避免同时启动过多线程
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        self.results.extend(results)
        total_time = time.time() - start_time
        
        return self.generate_summary_report(total_time)
    
    def generate_summary_report(self, total_time: float) -> Dict:
        """生成总结报告"""
        success_count = sum(1 for r in self.results if r.status == 'success')
        failed_count = len(self.results) - success_count
        
        report = {
            'total_videos': len(self.results),
            'success_count': success_count,
            'failed_count': failed_count,
            'success_rate': success_count / len(self.results) * 100 if self.results else 0,
            'total_time': total_time,
            'results': [r.to_dict() for r in self.results]
        }
        
        # 打印报告
        print("\n" + "="*80)
        print("优化下载器执行报告")
        print("="*80)
        print(f"总视频数: {report['total_videos']}")
        print(f"成功下载: {report['success_count']}")
        print(f"下载失败: {report['failed_count']}")
        print(f"成功率: {report['success_rate']:.1f}%")
        print(f"总耗时: {report['total_time']:.2f}秒")
        print()
        
        # 详细结果
        for result in self.results:
            status_icon = "✅" if result.status == 'success' else "❌"
            print(f"{status_icon} {result.site}: {result.url[:50]}...")
            if result.error_message:
                print(f"   错误: {result.error_message}")
        
        # 文件统计
        self.list_downloaded_files()
        
        return report
    
    def list_downloaded_files(self):
        """列出下载的文件"""
        if os.path.exists(self.config.download_dir):
            files = [f for f in os.listdir(self.config.download_dir) 
                    if any(keyword in f.lower() for keyword in ['opt_', 'bilibili', 'sohu', '360kan'])]
            
            if files:
                print(f"\n📁 优化下载器文件 ({len(files)} 个):")
                total_size = 0
                for file in sorted(files):
                    file_path = os.path.join(self.config.download_dir, file)
                    if os.path.isfile(file_path):
                        size = os.path.getsize(file_path) / (1024 * 1024)  # MB
                        total_size += size
                        print(f"  📹 {file} ({size:.2f} MB)")
                print(f"\n总大小: {total_size:.2f} MB")
            else:
                print("\n❌ 没有找到优化下载器的文件")
    
    def save_report(self, report: Dict, filename: str = None):
        """保存报告到文件"""
        if filename is None:
            filename = f'{self.config.download_dir}/download_report_{int(time.time())}.json'
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"报告已保存到: {filename}")

def main():
    """主函数"""
    # 用户提供的三个目标链接
    target_urls = [
        "https://tv.360kan.com/player?id=1f1f43f6e7d3755b3074b7ffc6cd9a4a&q=%E8%B5%B6%E5%9C%A9%E5%BD%92%E6%9D%A5%E9%98%BF%E5%93%A9%E5%93%A9&src=player-relate&srcg=mohe-short_video-new&sid=8be59ee954e642168e0c81bb1ebeade5",
        "https://www.bilibili.com/video/BV1fp4y1m7Fz?t=113.5",
        "https://tv.sohu.com/v/dXMvMzM4NDQ5OTcwLzE1ODk3MzM2OC5zaHRtbA==.html"
    ]
    
    print("=== 优化视频下载器 ===")
    print(f"开始时间: {datetime.now()}")
    print(f"目标链接数: {len(target_urls)}")
    print()
    
    downloader = OptimizedVideoDownloader()
    report = downloader.download_multiple_videos(target_urls)
    
    # 保存报告
    downloader.save_report(report)
    
    print("\n=== 优化下载器执行完成 ===")

if __name__ == "__main__":
    main()