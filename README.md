# 🎥 3D深度相机数据采集系统

一个现代化的3D深度相机数据采集程序，支持Intel RealSense和USB相机，具有美观的用户界面和完整的数据管理功能。

## ✨ 特性

- 🎨 **现代化界面设计** - 采用卡片式布局，美观易用
- 📷 **多相机支持** - 支持Intel RealSense和USB相机
- 🌊 **深度数据采集** - 实时RGB和深度图像采集
- 💾 **智能数据管理** - 自动会话管理和文件组织
- 🔊 **音频反馈** - 拍摄过程中的语音提示
- 📊 **多种拍摄模式** - 支持10张和20张连拍模式
- 🔍 **实时调试信息** - 详细的系统状态显示

## 🖼️ 界面预览

程序采用现代化的卡片式设计，包含：
- 左侧控制面板：相机设置、控制按钮、调试信息
- 右侧显示区域：RGB图像和深度图像实时预览
- 底部状态栏：系统状态和会话信息

## 📋 系统要求

- **操作系统**: Windows 10/11, macOS, Linux
- **Python版本**: 3.12
- **内存**: 建议4GB以上
- **存储**: 至少1GB可用空间
- **相机**: Intel RealSense系列或USB相机

## 🚀 快速开始

### 1. 环境准备

#### 使用Conda创建环境（推荐）

```bash
# 创建新的conda环境
conda create -n camera_system python=3.12

# 激活环境
conda activate camera_system

# 安装基础依赖
conda install -c conda-forge opencv numpy pillow pygame

# 安装tkinter（如果需要）
conda install tk

# 安装Intel RealSense SDK（可选）
pip install pyrealsense2
```

#### 使用pip安装（备选方案）

```bash
# 创建虚拟环境
python -m venv camera_env

# 激活虚拟环境
# Windows:
camera_env\Scripts\activate
# macOS/Linux:
source camera_env/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 依赖包列表

创建 `requirements.txt` 文件：

```txt
opencv-python>=4.8.1
numpy>=1.24.0
Pillow>=10.0.0
pygame>=2.5.0
pyrealsense2>=2.55.0
```

### 3. 音频文件准备

在项目根目录创建音频文件（可选）：
- `OK.wav` - 拍摄确认音效
- `Change.wav` - 模式切换音效
- `LastOne.wav` - 最后一张提示音
- `Next.wav` - 下一组提示音

### 4. 运行程序

```bash
# 确保在正确的环境中
conda activate camera_system

# 运行程序
python Camera.py
```

## 📖 使用说明

### 基本操作流程

1. **启动程序** - 运行 `python Camera.py`
2. **选择相机** - 在控制面板选择相机类型和设备
3. **配置参数** - 设置分辨率和帧率
4. **测试相机** - 点击"测试相机"确认设备正常
5. **启动采集** - 点击"启动相机"开始实时预览
6. **选择模式** - 选择10张或20张拍摄模式
7. **开始拍摄** - 点击"拍摄保存"进行数据采集

### 界面功能说明

#### 控制面板
- **📷 相机类型**: 选择自动检测、Intel RealSense或USB相机
- **🔌 相机设备**: 选择具体的相机设备
- **📐 分辨率**: 设置图像分辨率
- **⚡ 帧率**: 设置采集帧率

#### 控制按钮
- **🔄 刷新设备**: 重新检测可用相机
- **🧪 测试相机**: 测试选中的相机设备
- **▶️ 启动相机**: 开始相机预览
- **⏹️ 停止相机**: 停止相机并结束会话
- **📸 拍摄保存**: 保存当前帧的RGB和深度数据

#### 拍摄模式
- **20张模式**: 连续拍摄20张，第10张时提示切换
- **10张模式**: 连续拍摄10张，第5张时提示切换

#### 文件管理
- **📂 当前会话**: 打开当前会话文件夹
- **📋 所有会话**: 打开会话列表文件夹

## 📁 数据结构

程序会在项目目录下创建 `deepdata` 文件夹：

```
deepdata/
├── sessions/           # 会话数据
│   └── session_YYYYMMDD_HHMMSS/
│       ├── rgb/        # RGB图像
│       ├── depth/      # 深度数据(.npy)
│       ├── depth_vis/  # 深度可视化图像
│       ├── metadata/   # 元数据文件
│       └── session_info.json
├── exports/           # 导出数据
└── temp/             # 临时文件
```

### 数据文件说明

- **RGB图像**: PNG格式，原始彩色图像
- **深度数据**: NPY格式，原始深度数组
- **深度可视化**: PNG格式，彩色深度图
- **元数据**: JSON格式，包含拍摄参数和时间戳
- **会话信息**: JSON格式，会话统计和配置信息

## 🔧 配置选项

### 相机参数配置

程序支持多种分辨率和帧率组合：

- **分辨率选项**: 320x240, 640x480, 800x600, 1024x768, 1280x720, 1920x1080
- **帧率选项**: 15fps, 30fps, 60fps

### Intel RealSense配置

对于RealSense相机，程序会自动配置：
- 深度流: 640x480, Z16格式, 30fps
- 彩色流: 640x480, BGR8格式, 30fps
- 自动对齐深度和彩色图像

## 🐛 故障排除

### 常见问题

1. **相机无法检测**
   - 检查相机连接
   - 确认驱动程序已安装
   - 尝试不同的USB端口

2. **RealSense相机问题**
   - 安装Intel RealSense SDK
   - 检查pyrealsense2包版本
   - 确认相机固件更新

3. **音频文件错误**
   - 检查音频文件路径
   - 确认pygame正确安装
   - 音频文件为可选功能

4. **界面显示问题**
   - 检查tkinter安装
   - 确认系统支持GUI显示
   - 尝试更新显卡驱动

### 调试信息

程序提供详细的调试信息，包括：
- 相机检测结果
- 设备配置状态
- 拍摄操作日志
- 错误信息和警告

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## 📄 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 提交GitHub Issue
- 发送邮件至项目维护者

---

**享受您的3D数据采集之旅！** 🚀
