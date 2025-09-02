#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频下载器主程序 - 最终版本
整合所有功能，支持多网站、GUI和命令行模式
"""

import sys
import os
import argparse
import logging
from typing import List, Optional

# 导入配置
from config import DownloaderConfig

# 导入核心功能
try:
    from optimized_video_downloader import OptimizedVideoDownloader
except ImportError:
    print("警告: 无法导入优化下载器，将使用基础功能")
    OptimizedVideoDownloader = None

try:
    from video_downloader_gui import VideoDownloaderGUI
except ImportError:
    print("警告: 无法导入GUI模块")
    VideoDownloaderGUI = None

class MainDownloader:
    """主下载器类"""
    
    def __init__(self):
        self.config = DownloaderConfig()
        self.setup_logging()
        self.logger = logging.getLogger('MainDownloader')
    
    def setup_logging(self):
        """设置日志"""
        log_config = self.config.get_log_config()
        logging.basicConfig(
            level=getattr(logging, log_config['level']),
            format=log_config['format'],
            datefmt=log_config['datefmt'],
            handlers=[
                logging.FileHandler(log_config['filename'], encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
    
    def print_banner(self):
        """打印程序横幅"""
        banner = """
╔══════════════════════════════════════════════════════════════╗
║                    视频下载器 v2.0                          ║
║                  多网站支持 | 智能下载                      ║
╚══════════════════════════════════════════════════════════════╝
        """
        print(banner)
        print(f"支持的网站: {', '.join(self.config.get_supported_sites())}")
        print(f"下载目录: {self.config.get_download_dir()}")
        print()
    
    def run_gui_mode(self):
        """运行GUI模式"""
        if VideoDownloaderGUI is None:
            print("❌ GUI模块不可用，请检查tkinter安装")
            return False
        
        try:
            self.logger.info("启动GUI模式")
            import tkinter as tk
            root = tk.Tk()
            app = VideoDownloaderGUI(root)
            root.mainloop()
            return True
        except Exception as e:
            self.logger.error(f"GUI模式启动失败: {e}")
            print(f"❌ GUI启动失败: {e}")
            return False
    
    def run_cli_mode(self, urls: List[str], quality: str = 'high'):
        """运行命令行模式"""
        if not urls:
            print("❌ 请提供要下载的视频URL")
            return False
        
        if OptimizedVideoDownloader is None:
            print("❌ 优化下载器不可用")
            return False
        
        try:
            self.logger.info(f"启动命令行模式，下载 {len(urls)} 个视频")
            
            downloader = OptimizedVideoDownloader()
            
            # 设置质量偏好
            if quality in ['high', 'medium', 'low']:
                print(f"📺 质量设置: {quality}")
            
            print(f"🚀 开始下载 {len(urls)} 个视频...")
            report = downloader.download_multiple_videos(urls)
            
            # 显示结果
            success_rate = report.get('success_rate', 0)
            if success_rate > 50:
                print(f"✅ 下载完成！成功率: {success_rate:.1f}%")
            else:
                print(f"⚠️ 下载完成，但成功率较低: {success_rate:.1f}%")
            
            return True
            
        except Exception as e:
            self.logger.error(f"命令行模式执行失败: {e}")
            print(f"❌ 下载失败: {e}")
            return False
    
    def run_interactive_mode(self):
        """运行交互模式"""
        print("🎯 交互模式 - 输入 'help' 查看帮助，输入 'quit' 退出")
        
        while True:
            try:
                user_input = input("\n请输入命令或视频URL: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 再见！")
                    break
                
                if user_input.lower() == 'help':
                    self.show_help()
                    continue
                
                if user_input.lower() == 'config':
                    self.config.print_config_summary()
                    continue
                
                if user_input.lower() == 'gui':
                    self.run_gui_mode()
                    continue
                
                # 检测是否为URL
                if any(domain in user_input for domain in ['bilibili.com', 'sohu.com', '360kan.com', 'youtube.com']):
                    print(f"🔍 检测到视频URL: {self.config.detect_site(user_input)}")
                    self.run_cli_mode([user_input])
                else:
                    print("❓ 无法识别的命令或URL，输入 'help' 查看帮助")
                    
            except KeyboardInterrupt:
                print("\n👋 用户中断，退出程序")
                break
            except Exception as e:
                self.logger.error(f"交互模式错误: {e}")
                print(f"❌ 发生错误: {e}")
    
    def show_help(self):
        """显示帮助信息"""
        help_text = """
📖 视频下载器帮助

🎯 交互命令:
  help     - 显示此帮助信息
  config   - 显示配置信息
  gui      - 启动图形界面
  quit     - 退出程序

🔗 支持的网站:
  • Bilibili (bilibili.com)
  • 搜狐视频 (sohu.com)
  • YouTube (youtube.com)
  • 360看视频 (360kan.com) - 部分支持

💡 使用示例:
  直接粘贴视频URL即可开始下载
  例如: https://www.bilibili.com/video/BV1234567890

⚙️ 命令行参数:
  --gui           启动图形界面
  --urls URL1 URL2 下载指定URL
  --quality high  设置下载质量 (high/medium/low)
  --interactive   启动交互模式
        """
        print(help_text)
    
    def run(self, args: Optional[argparse.Namespace] = None):
        """主运行方法"""
        self.print_banner()
        
        # 验证配置
        if not self.config.validate_config():
            print("❌ 配置验证失败，程序退出")
            return False
        
        if args is None:
            # 默认启动交互模式
            self.run_interactive_mode()
            return True
        
        # 根据参数选择模式
        if args.gui:
            return self.run_gui_mode()
        elif args.urls:
            return self.run_cli_mode(args.urls, args.quality)
        elif args.interactive:
            self.run_interactive_mode()
            return True
        else:
            # 默认交互模式
            self.run_interactive_mode()
            return True

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='视频下载器 - 支持多网站视频下载',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main_downloader.py --gui
  python main_downloader.py --urls "https://www.bilibili.com/video/BV1234567890"
  python main_downloader.py --interactive
  python main_downloader.py  # 默认交互模式
        """
    )
    
    parser.add_argument(
        '--gui', 
        action='store_true',
        help='启动图形用户界面'
    )
    
    parser.add_argument(
        '--urls',
        nargs='+',
        help='要下载的视频URL列表'
    )
    
    parser.add_argument(
        '--quality',
        choices=['high', 'medium', 'low'],
        default='high',
        help='下载质量设置 (默认: high)'
    )
    
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='启动交互模式'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='视频下载器 v2.0'
    )
    
    return parser.parse_args()

def main():
    """主函数"""
    try:
        # 解析命令行参数
        args = parse_arguments()
        
        # 创建主下载器
        downloader = MainDownloader()
        
        # 运行程序
        success = downloader.run(args)
        
        # 退出码
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n👋 用户中断，程序退出")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 程序异常: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()