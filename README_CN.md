# 视频下载器

一个功能强大的多平台视频下载工具，支持包括哔哩哔哩、百度百科、搜狐视频、360kan和品善在内的多个视频网站。

## 功能特性

- **多平台支持**：支持从哔哩哔哩、百度百科、搜狐视频、360kan和品善等等下载视频
- **图形界面**：基于tkinter构建的用户友好图形界面
- **命令行支持**：支持命令行界面进行自动化下载
- **智能解析**：智能视频URL解析和提取
- **断点续传**：支持恢复中断的下载
- **进度显示**：实时下载进度显示和详细日志记录
- **错误处理**：强大的错误处理和重试机制
- **格式选择**：自动选择最佳质量，支持备选选项
- **音视频合并**：自动合并分离的音频和视频流

## 系统要求

- Python 3.7 或更高版本
- Windows、macOS 或 Linux
- FFmpeg（项目中已包含）
- Chrome 浏览器（用于基于Selenium的提取）

## 安装说明

1. **克隆仓库**：
   ```bash
   git clone https://github.com/your-username/video-downloader.git
   cd video-downloader
   ```

2. **安装依赖**：
   ```bash
   pip install -r requirements.txt
   ```

3. **运行应用程序**：
   
   **图形界面版本**：
   ```bash
   python src/video_downloader_gui.py
   ```
   
   **命令行版本**：
   ```bash
   python src/video_downloader.py <视频URL>
   ```

## 程序截图

### 图形界面展示

![GUI启动界面](docs/images/gui-startup-interface.png)
*主应用程序界面，包含URL输入和下载选项*

![下载进度界面](docs/images/download-progress-interface.png)
*下载进度显示，包含实时状态更新*

## 使用方法

### 图形界面

1. 启动GUI应用程序
2. 在输入框中粘贴或输入视频URL
3. 选择下载目录
4. 点击"下载"开始下载过程
5. 在日志区域监控进度

### 命令行界面

```bash
# 下载单个视频
python src/video_downloader.py "https://www.bilibili.com/video/BV1234567890"

# 指定自定义下载目录
python src/video_downloader.py "https://www.bilibili.com/video/BV1234567890" --output ./downloads
```

### 支持的网站

| 网站 | 状态 | 备注 |
|------|------|------|
| 哔哩哔哩 | ✅ 支持 | 完全支持音视频合并 |
| 百度百科 | ✅ 支持 | 从百科页面提取视频 |
| 搜狐视频 | ✅ 支持 | 标准视频下载 |
| 360kan | ⚠️ 有限支持 | 某些视频需要Selenium |
| 品善 | ✅ 支持 | 教育内容平台 |
| YouTube | ✅ 支持 | 通过yt-dlp集成 |

## 项目结构

```
video-downloader/
├── src/                    # 源代码
│   ├── __init__.py        # 包初始化
│   ├── video_downloader.py # 核心下载逻辑
│   ├── video_downloader_gui.py # GUI界面
│   ├── config.py          # 配置设置
│   ├── main_downloader.py # 主入口点
│   └── optimized_video_downloader.py # 优化版本
├── docs/                   # 文档
│   └── images/            # 项目截图
├── tests/                  # 测试文件
├── examples/              # 使用示例
├── scripts/               # 实用脚本
├── ffmpeg/                # FFmpeg二进制文件
├── requirements.txt       # Python依赖
├── setup.py              # 包设置
├── LICENSE               # 许可证文件
├── README.md             # 英文说明文件
└── README_CN.md          # 中文说明文件（本文件）
```

## 配置说明

应用程序在`src/config.py`中使用集中配置系统。您可以自定义：

- 下载目录
- 质量偏好
- 重试设置
- 超时值
- 用户代理
- 站点特定设置

## 依赖项

### 核心依赖
- `yt-dlp`：视频提取和下载
- `requests`：HTTP请求
- `beautifulsoup4`：HTML解析
- `selenium`：复杂网站的Web自动化
- `tqdm`：进度条

### GUI依赖
- `tkinter`：GUI框架（Python自带）

### 可选依赖
- `webdriver-manager`：自动Chrome驱动管理
- `cx-Freeze`：用于构建可执行文件

## 构建可执行文件

创建独立可执行文件：

```bash
python setup.py build
```

这将在`build/`目录中创建可执行文件。

## 故障排除

### 常见问题

1. **找不到FFmpeg**：确保FFmpeg在您的PATH中或使用包含的二进制文件
2. **Chrome驱动问题**：更新Chrome浏览器或使用webdriver-manager
3. **网络超时**：检查您的网络连接和防火墙设置
4. **权限错误**：为下载目录运行适当的权限

### 日志记录

详细日志保存到`downloads/downloader.log`。检查此文件以获取调试信息。

## 贡献

1. Fork 仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 打开Pull Request

## 许可证

本项目采用MIT许可证 - 详见[LICENSE](LICENSE)文件。

## 免责声明

此工具仅供教育和个人使用。请尊重您下载网站的服务条款，并确保您有权下载内容。

## 致谢

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) 提供优秀的视频提取库
- [FFmpeg](https://ffmpeg.org/) 提供视频处理功能
- 所有帮助改进此项目的贡献者

## 支持

如果您遇到任何问题或有疑问，请：

1. 查看[故障排除部分](#故障排除)
2. 搜索现有[issues](https://github.com/your-username/video-downloader/issues)
3. 创建包含详细信息的新issue

---

**如果您觉得这个仓库有帮助，请给它一个星标！** ⭐