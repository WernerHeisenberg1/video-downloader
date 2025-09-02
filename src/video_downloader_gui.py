#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video Downloader - GUI Version

Graphical user interface for the multi-platform video downloader.
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
import queue
import time
from video_downloader import VideoDownloader, VideoDownloadError


class VideoDownloaderGUI:
    """Main GUI class for the video downloader"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Video Downloader v1.0")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        try:
            # self.root.iconbitmap('icon.ico')
            pass
        except:
            pass
        
        self.download_dir = tk.StringVar(value=str(Path.home() / "Downloads"))
        self.url_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready")
        self.progress_var = tk.DoubleVar()
        
        self.downloader = None
        self.download_thread = None
        self.is_downloading = False
        
        self.message_queue = queue.Queue()
        
        self.create_widgets()
        
        self.process_queue()
    
    def create_widgets(self):
        """Create GUI components"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        title_label = ttk.Label(main_frame, text="Video Downloader", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        url_frame = ttk.LabelFrame(main_frame, text="Video URL", padding="10")
        url_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        url_frame.columnconfigure(0, weight=1)
        
        self.url_entry = ttk.Entry(url_frame, textvariable=self.url_var, font=("Arial", 10))
        self.url_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        self.url_entry.bind('<Control-v>', self.paste_url_shortcut)
        self.url_entry.bind('<Control-a>', self.select_all_url)
        
        self.url_entry.bind('<Button-3>', self.show_context_menu)
        
        paste_btn = ttk.Button(url_frame, text="Paste", command=self.paste_url)
        paste_btn.grid(row=0, column=1)
        
        example_label = ttk.Label(url_frame, text="Supported: Baidu Baike, Sohu Video, 360kan, Bilibili, Pinshan", 
                                 font=("Arial", 8), foreground="gray")
        example_label.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))
        
        dir_frame = ttk.LabelFrame(main_frame, text="Download Directory", padding="10")
        dir_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        dir_frame.columnconfigure(0, weight=1)
        
        # 目录显示
        self.dir_entry = ttk.Entry(dir_frame, textvariable=self.download_dir, 
                                  font=("Arial", 10), state="readonly")
        self.dir_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # 浏览按钮
        browse_btn = ttk.Button(dir_frame, text="浏览", command=self.browse_directory)
        browse_btn.grid(row=0, column=1)
        
        # 控制按钮区域
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=3, column=0, columnspan=3, pady=(0, 10))
        
        # 下载按钮
        self.download_btn = ttk.Button(control_frame, text="开始下载", 
                                      command=self.start_download, style="Accent.TButton")
        self.download_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 停止按钮
        self.stop_btn = ttk.Button(control_frame, text="停止下载", 
                                  command=self.stop_download, state="disabled")
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 清空按钮
        clear_btn = ttk.Button(control_frame, text="清空", command=self.clear_all)
        clear_btn.pack(side=tk.LEFT)
        
        # 进度区域
        progress_frame = ttk.LabelFrame(main_frame, text="下载进度", padding="10")
        progress_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        # 状态标签
        self.status_label = ttk.Label(progress_frame, textvariable=self.status_var)
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        # 进度条
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                           maximum=100, mode='determinate')
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="日志信息", padding="10")
        log_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1)
        
        # 日志文本框
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, font=("Consolas", 9))
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 底部信息
        info_frame = ttk.Frame(main_frame)
        info_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E))
        
        info_label = ttk.Label(info_frame, text="支持网站: 百度百科、搜狐视频、360kan、哔哩哔哩、品善网", 
                              font=("Arial", 8), foreground="gray")
        info_label.pack(side=tk.LEFT)
        
        # 预设示例URL
        self.url_var.set("http://baike.baidu.com/l/KNsfn5W8")
    
    def paste_url(self):
        """粘贴剪贴板内容到URL输入框"""
        try:
            clipboard_content = self.root.clipboard_get()
            self.url_var.set(clipboard_content.strip())
            self.log_message("已粘贴剪贴板内容")
        except tk.TclError:
            self.log_message("剪贴板为空或无法访问")
    
    def paste_url_shortcut(self, event):
        """Ctrl+V快捷键粘贴"""
        self.paste_url()
        return 'break'  # 阻止默认行为
    
    def select_all_url(self, event):
        """Ctrl+A全选URL文本"""
        self.url_entry.select_range(0, tk.END)
        return 'break'
    
    def show_context_menu(self, event):
        """显示右键菜单"""
        context_menu = tk.Menu(self.root, tearoff=0)
        context_menu.add_command(label="复制", command=self.copy_url)
        context_menu.add_command(label="粘贴", command=self.paste_url)
        context_menu.add_command(label="全选", command=lambda: self.url_entry.select_range(0, tk.END))
        context_menu.add_separator()
        context_menu.add_command(label="清空", command=lambda: self.url_var.set(""))
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def copy_url(self):
        """复制URL到剪贴板"""
        try:
            url = self.url_var.get()
            if url:
                self.root.clipboard_clear()
                self.root.clipboard_append(url)
                self.log_message("已复制URL到剪贴板")
            else:
                self.log_message("URL为空，无法复制")
        except Exception as e:
            self.log_message(f"复制失败: {str(e)}")
    
    def browse_directory(self):
        """浏览选择下载目录"""
        directory = filedialog.askdirectory(initialdir=self.download_dir.get())
        if directory:
            self.download_dir.set(directory)
            self.log_message(f"下载目录已设置为: {directory}")
    
    def clear_all(self):
        """清空所有输入和日志"""
        if not self.is_downloading:
            self.url_var.set("")
            self.log_text.delete(1.0, tk.END)
            self.status_var.set("就绪")
            self.progress_var.set(0)
            self.log_message("已清空所有内容")
        else:
            messagebox.showwarning("警告", "下载进行中，无法清空")
    
    def log_message(self, message):
        """添加日志消息"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def start_download(self):
        """开始下载"""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("错误", "请输入视频链接")
            return
        
        if not url.startswith(('http://', 'https://')):
            messagebox.showerror("错误", "请输入完整的URL（包含http://或https://）")
            return
        
        download_dir = self.download_dir.get()
        if not os.path.exists(download_dir):
            try:
                os.makedirs(download_dir)
            except Exception as e:
                messagebox.showerror("错误", f"无法创建下载目录: {str(e)}")
                return
        
        # 禁用下载按钮，启用停止按钮
        self.download_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.is_downloading = True
        
        # 重置进度
        self.progress_var.set(0)
        self.status_var.set("准备下载...")
        
        # 启动下载线程
        self.download_thread = threading.Thread(target=self.download_worker, args=(url, download_dir))
        self.download_thread.daemon = True
        self.download_thread.start()
        
        self.log_message(f"开始下载: {url}")
    
    def stop_download(self):
        """停止下载"""
        self.is_downloading = False
        self.status_var.set("正在停止...")
        self.log_message("用户请求停止下载")
        
        # 等待线程结束
        if self.download_thread and self.download_thread.is_alive():
            self.download_thread.join(timeout=2)
        
        self.reset_ui_state()
    
    def reset_ui_state(self):
        """重置UI状态"""
        self.download_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.is_downloading = False
        self.status_var.set("就绪")
    
    def download_worker(self, url, download_dir):
        """下载工作线程"""
        try:
            # 创建下载器实例
            self.downloader = VideoDownloader(download_dir=download_dir)
            
            # 发送状态更新
            self.message_queue.put(("status", "正在解析视频链接..."))
            self.message_queue.put(("progress", 10))
            
            # 检查是否被停止
            if not self.is_downloading:
                return
            
            # 开始下载
            success = self.downloader.download_video(url)
            
            if success:
                self.message_queue.put(("status", "下载完成！"))
                self.message_queue.put(("progress", 100))
                self.message_queue.put(("log", "✅ 下载成功完成"))
                self.message_queue.put(("success", f"视频已保存到: {download_dir}"))
            else:
                self.message_queue.put(("status", "下载失败"))
                self.message_queue.put(("progress", 0))
                self.message_queue.put(("log", "❌ 下载失败，请查看日志了解详情"))
                self.message_queue.put(("error", "下载失败，可能是链接无效或网络问题"))
        
        except Exception as e:
            self.message_queue.put(("status", "下载出错"))
            self.message_queue.put(("progress", 0))
            self.message_queue.put(("log", f"❌ 下载过程中出现错误: {str(e)}"))
            self.message_queue.put(("error", f"下载错误: {str(e)}"))
        
        finally:
            self.message_queue.put(("reset", None))
    
    def process_queue(self):
        """处理消息队列"""
        try:
            while True:
                message_type, data = self.message_queue.get_nowait()
                
                if message_type == "status":
                    self.status_var.set(data)
                elif message_type == "progress":
                    self.progress_var.set(data)
                elif message_type == "log":
                    self.log_message(data)
                elif message_type == "success":
                    messagebox.showinfo("成功", data)
                elif message_type == "error":
                    messagebox.showerror("错误", data)
                elif message_type == "reset":
                    self.reset_ui_state()
        
        except queue.Empty:
            pass
        
        # 继续处理队列
        self.root.after(100, self.process_queue)


def main():
    """主函数"""
    # 创建主窗口
    root = tk.Tk()
    
    # 设置主题（如果支持的话）
    try:
        style = ttk.Style()
        # 尝试使用现代主题
        available_themes = style.theme_names()
        if 'vista' in available_themes:
            style.theme_use('vista')
        elif 'clam' in available_themes:
            style.theme_use('clam')
    except:
        pass
    
    # 创建应用实例
    app = VideoDownloaderGUI(root)
    
    # 设置窗口关闭事件
    def on_closing():
        if app.is_downloading:
            if messagebox.askokcancel("退出", "下载正在进行中，确定要退出吗？"):
                app.stop_download()
                root.destroy()
        else:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # 启动主循环
    root.mainloop()


if __name__ == "__main__":
    main()