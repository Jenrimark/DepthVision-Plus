#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
3D深度相机数据采集程序 - 美化版
专门优化USB 2.0相机支持，现代化界面设计
作者: Assistant
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import cv2
import numpy as np
import os
import threading
import time
from datetime import datetime
from PIL import Image, ImageTk, ImageDraw, ImageFont
import json
import sys
import pygame

# 尝试导入pyrealsense2库
try:
    import pyrealsense2 as rs

    REALSENSE_AVAILABLE = True
except ImportError:
    REALSENSE_AVAILABLE = False
    print("警告: pyrealsense2 库未安装，将使用OpenCV模式")


class DepthCameraGUI:
    def __init__(self, root):
        pygame.mixer.init()
        self.root = root
        self.root.title("🎥 3D深度相机数据采集系统 - 美化版")
        self.root.geometry("1400x900")
        self.root.resizable(True, True)

        # 设置现代化主题和样式
        self.setup_modern_theme()

        # 设置窗口图标和背景
        self.setup_window_style()

        # 初始化变量
        self.pictureSaveNumber = 0
        self.pictureSaveMode = -1
        self.camera_running = False
        self.camera_type = "opencv"
        self.pipeline = None
        self.cap = None
        self.current_rgb_frame = None
        self.current_depth_frame = None
        self.save_counter = 0
        self.camera_index = 0
        self.available_cameras = []
        self.current_session_path = None
        self.session_start_time = None

        # 创建deepdata文件夹
        self.create_deepdata_folder()

        # 检测可用相机
        self.detect_available_cameras()

        # 初始化GUI
        self.init_gui()

        # 尝试检测相机类型
        self.detect_camera_type()

    def setup_modern_theme(self):
        """设置现代化主题"""
        style = ttk.Style()

        # 设置主题
        try:
            style.theme_use('clam')  # 使用clam主题作为基础
        except:
            pass

        # 定义颜色方案
        self.colors = {
            'primary': '#2E86AB',      # 主色调 - 蓝色
            'secondary': '#A23B72',    # 次要色 - 紫红色
            'accent': '#F18F01',       # 强调色 - 橙色
            'success': '#C73E1D',      # 成功色 - 红色
            'background': '#F5F5F5',   # 背景色 - 浅灰
            'surface': '#FFFFFF',      # 表面色 - 白色
            'text': '#2C3E50',         # 文本色 - 深灰蓝
            'text_light': '#7F8C8D',   # 浅文本色
            'border': '#BDC3C7'        # 边框色
        }

        # 配置样式
        style.configure('Title.TLabel',
                       font=('Microsoft YaHei UI', 16, 'bold'),
                       foreground=self.colors['primary'])

        style.configure('Heading.TLabel',
                       font=('Microsoft YaHei UI', 12, 'bold'),
                       foreground=self.colors['text'])

        style.configure('Info.TLabel',
                       font=('Microsoft YaHei UI', 10),
                       foreground=self.colors['text_light'])

        # 按钮样式
        style.configure('Primary.TButton',
                       font=('Microsoft YaHei UI', 10, 'bold'),
                       foreground='white')

        style.configure('Success.TButton',
                       font=('Microsoft YaHei UI', 10, 'bold'),
                       foreground='white')

        style.configure('Accent.TButton',
                       font=('Microsoft YaHei UI', 10, 'bold'),
                       foreground='white')

        # LabelFrame样式
        style.configure('Card.TLabelframe',
                       relief='flat',
                       borderwidth=1)

        style.configure('Card.TLabelframe.Label',
                       font=('Microsoft YaHei UI', 11, 'bold'),
                       foreground=self.colors['primary'])

    def setup_window_style(self):
        """设置窗口样式"""
        # 设置窗口背景色
        self.root.configure(bg=self.colors['background'])

        # 尝试设置窗口图标（如果有的话）
        try:
            # 这里可以设置自定义图标
            pass
        except:
            pass

    def detect_available_cameras(self):
        """检测所有可用的相机设备"""
        self.available_cameras = []
        print("正在检测可用相机...")

        # 检测多个相机索引
        for i in range(5):  # 检测索引0-4
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                # 尝试读取一帧来确认相机真正可用
                ret, frame = cap.read()
                if ret:
                    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    self.available_cameras.append({
                        'index': i,
                        'name': f"相机 {i} ({int(width)}x{int(height)}@{int(fps)}fps)",
                        'width': int(width),
                        'height': int(height),
                        'fps': int(fps)
                    })
                    print(f"发现相机 {i}: {int(width)}x{int(height)}@{int(fps)}fps")
                cap.release()

        if not self.available_cameras:
            print("未发现可用的相机设备")
        else:
            print(f"总共发现 {len(self.available_cameras)} 个相机设备")

    def create_deepdata_folder(self):
        """创建deepdata主文件夹"""
        self.deepdata_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "deepdata")
        if not os.path.exists(self.deepdata_path):
            os.makedirs(self.deepdata_path)
            print(f"已创建文件夹: {self.deepdata_path}")

        # 创建子文件夹结构
        subfolders = ['sessions', 'exports', 'temp']
        for folder in subfolders:
            folder_path = os.path.join(self.deepdata_path, folder)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
                print(f"已创建子文件夹: {folder_path}")

    def create_session_folder(self):
        """创建新的会话文件夹"""
        self.session_start_time = datetime.now()
        session_name = f"session_{self.session_start_time.strftime('%Y%m%d_%H%M%S')}"
        self.current_session_path = os.path.join(self.deepdata_path, "sessions", session_name)

        # 创建会话文件夹及其子文件夹
        session_subfolders = ['rgb', 'depth', 'depth_vis', 'metadata']
        for folder in session_subfolders:
            folder_path = os.path.join(self.current_session_path, folder)
            os.makedirs(folder_path, exist_ok=True)

        # 创建会话信息文件
        session_info = {
            "session_name": session_name,
            "start_time": self.session_start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "camera_type": self.camera_type,
            "camera_index": getattr(self, 'camera_index', 0),
            "resolution": getattr(self, 'resolution_var', None) and self.resolution_var.get(),
            "fps": getattr(self, 'fps_var', None) and self.fps_var.get(),
        }

        session_info_path = os.path.join(self.current_session_path, "session_info.json")
        with open(session_info_path, 'w', encoding='utf-8') as f:
            json.dump(session_info, f, indent=2, ensure_ascii=False)

        self.log_debug(f"创建新会话: {session_name}")

        # 更新会话显示
        if hasattr(self, 'session_var'):
            self.session_var.set(session_name)

        return self.current_session_path

    def init_gui(self):
        """初始化现代化GUI界面"""
        # 创建主容器
        main_container = tk.Frame(self.root, bg=self.colors['background'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 标题区域
        self.create_title_section(main_container)

        # 主要内容区域
        content_frame = tk.Frame(main_container, bg=self.colors['background'])
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 0))

        # 左侧控制面板
        left_panel = tk.Frame(content_frame, bg=self.colors['background'])
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))

        # 右侧显示区域
        right_panel = tk.Frame(content_frame, bg=self.colors['background'])
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 创建各个区域
        self.create_control_panel(left_panel)
        self.create_display_area(right_panel)
        self.create_status_bar(main_container)

    def create_title_section(self, parent):
        """创建标题区域"""
        title_frame = tk.Frame(parent, bg=self.colors['background'])
        title_frame.pack(fill=tk.X, pady=(0, 10))

        # 主标题
        title_label = tk.Label(title_frame,
                              text="🎥 3D深度相机数据采集系统",
                              font=('Microsoft YaHei UI', 20, 'bold'),
                              fg=self.colors['primary'],
                              bg=self.colors['background'])
        title_label.pack(side=tk.LEFT)

        # 版本信息
        version_label = tk.Label(title_frame,
                                text="v2.0 美化版",
                                font=('Microsoft YaHei UI', 10),
                                fg=self.colors['text_light'],
                                bg=self.colors['background'])
        version_label.pack(side=tk.RIGHT, pady=(10, 0))

    def create_control_panel(self, parent):
        """创建现代化控制面板"""
        # 控制面板主框架 - 调整宽度
        control_frame = self.create_card_frame(parent, "🎛️ 控制面板", width=380)

        # 相机设置区域
        self.create_camera_settings(control_frame)

        # 按钮区域
        self.create_control_buttons(control_frame)

        # 调试信息区域
        self.create_debug_area(control_frame)

    def create_card_frame(self, parent, title, width=None, height=None):
        """创建卡片样式的框架"""
        # 外层容器
        card_container = tk.Frame(parent, bg=self.colors['background'])
        card_container.pack(fill=tk.X, pady=(0, 15))

        if width:
            card_container.configure(width=width)
        if height:
            card_container.configure(height=height)

        # 卡片框架
        card_frame = tk.Frame(card_container,
                             bg=self.colors['surface'],
                             relief='flat',
                             bd=1)
        card_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # 添加阴影效果
        shadow_frame = tk.Frame(card_container,
                               bg='#E0E0E0',
                               height=2)
        shadow_frame.place(x=4, y=4, relwidth=1, relheight=1)
        card_frame.lift()

        # 标题
        if title:
            title_frame = tk.Frame(card_frame, bg=self.colors['surface'])
            title_frame.pack(fill=tk.X, padx=15, pady=(15, 10))

            title_label = tk.Label(title_frame,
                                  text=title,
                                  font=('Microsoft YaHei UI', 12, 'bold'),
                                  fg=self.colors['primary'],
                                  bg=self.colors['surface'])
            title_label.pack(side=tk.LEFT)

            # 分隔线
            separator = tk.Frame(card_frame, height=1, bg=self.colors['border'])
            separator.pack(fill=tk.X, padx=15)

        # 内容区域
        content_frame = tk.Frame(card_frame, bg=self.colors['surface'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        return content_frame

    def create_camera_settings(self, parent):
        """创建相机设置区域"""
        settings_frame = tk.Frame(parent, bg=self.colors['surface'])
        settings_frame.pack(fill=tk.X, pady=(0, 25))

        # 使用网格布局来更好地对齐
        settings_frame.grid_columnconfigure(1, weight=1)

        # 相机类型选择
        tk.Label(settings_frame, text="📷 相机类型:",
                font=('Microsoft YaHei UI', 10, 'bold'),
                fg=self.colors['text'], bg=self.colors['surface']).grid(row=0, column=0, sticky='w', pady=(0, 12))

        self.camera_type_var = tk.StringVar(value="自动检测")
        camera_combo = ttk.Combobox(settings_frame, textvariable=self.camera_type_var,
                                    values=["自动检测", "Intel RealSense", "USB相机"],
                                    state="readonly", width=18)
        camera_combo.grid(row=0, column=1, sticky='e', pady=(0, 12), padx=(10, 0))

        # 相机设备选择
        tk.Label(settings_frame, text="🔌 相机设备:",
                font=('Microsoft YaHei UI', 10, 'bold'),
                fg=self.colors['text'], bg=self.colors['surface']).grid(row=1, column=0, sticky='w', pady=(0, 12))

        self.camera_device_var = tk.StringVar()
        self.camera_device_combo = ttk.Combobox(settings_frame, textvariable=self.camera_device_var,
                                                state="readonly", width=18)
        self.camera_device_combo.grid(row=1, column=1, sticky='e', pady=(0, 12), padx=(10, 0))

        # 更新相机设备列表
        self.update_camera_device_list()

        # 分辨率设置
        tk.Label(settings_frame, text="📐 分辨率:",
                font=('Microsoft YaHei UI', 10, 'bold'),
                fg=self.colors['text'], bg=self.colors['surface']).grid(row=2, column=0, sticky='w', pady=(0, 12))

        self.resolution_var = tk.StringVar(value="640x480")
        resolution_combo = ttk.Combobox(settings_frame, textvariable=self.resolution_var,
                                        values=["320x240", "640x480", "800x600", "1024x768", "1280x720", "1920x1080"],
                                        state="readonly", width=18)
        resolution_combo.grid(row=2, column=1, sticky='e', pady=(0, 12), padx=(10, 0))

        # 帧率设置
        tk.Label(settings_frame, text="⚡ 帧率:",
                font=('Microsoft YaHei UI', 10, 'bold'),
                fg=self.colors['text'], bg=self.colors['surface']).grid(row=3, column=0, sticky='w')

        self.fps_var = tk.StringVar(value="30")
        fps_combo = ttk.Combobox(settings_frame, textvariable=self.fps_var,
                                 values=["15", "30", "60"],
                                 state="readonly", width=18)
        fps_combo.grid(row=3, column=1, sticky='e', padx=(10, 0))

    def create_control_buttons(self, parent):
        """创建控制按钮区域"""
        # 主要控制按钮区域
        main_buttons_frame = tk.Frame(parent, bg=self.colors['surface'])
        main_buttons_frame.pack(fill=tk.X, pady=(0, 20))

        # 使用网格布局让按钮更整齐
        main_buttons_frame.grid_columnconfigure(0, weight=1)
        main_buttons_frame.grid_columnconfigure(1, weight=1)

        # 第一行：刷新和测试按钮
        self.refresh_btn = self.create_modern_button(main_buttons_frame, "🔄 刷新设备",
                                                    self.refresh_cameras, 'info')
        self.refresh_btn.grid(row=0, column=0, sticky='ew', padx=(0, 4), pady=(0, 8))

        self.test_btn = self.create_modern_button(main_buttons_frame, "🧪 测试相机",
                                                 self.test_camera, 'info')
        self.test_btn.grid(row=0, column=1, sticky='ew', padx=(4, 0), pady=(0, 8))

        # 第二行：启动和停止按钮
        self.start_btn = self.create_modern_button(main_buttons_frame, "▶️ 启动相机",
                                                  self.start_camera, 'success')
        self.start_btn.grid(row=1, column=0, sticky='ew', padx=(0, 4), pady=(0, 8))

        self.stop_btn = self.create_modern_button(main_buttons_frame, "⏹️ 停止相机",
                                                 self.stop_camera, 'danger', state='disabled')
        self.stop_btn.grid(row=1, column=1, sticky='ew', padx=(4, 0), pady=(0, 8))

        # 第三行：拍摄按钮（跨两列）
        self.capture_btn = self.create_modern_button(main_buttons_frame, "📸 拍摄保存",
                                                    self.capture_and_save, 'primary', state='disabled')
        self.capture_btn.grid(row=2, column=0, columnspan=2, sticky='ew', pady=(0, 8))

        # 模式选择区域
        mode_frame = tk.Frame(parent, bg=self.colors['surface'])
        mode_frame.pack(fill=tk.X, pady=(0, 20))

        mode_label = tk.Label(mode_frame, text="📊 拍摄模式:",
                             font=('Microsoft YaHei UI', 10, 'bold'),
                             fg=self.colors['text'], bg=self.colors['surface'])
        mode_label.pack(anchor=tk.W, pady=(0, 10))

        mode_buttons_frame = tk.Frame(mode_frame, bg=self.colors['surface'])
        mode_buttons_frame.pack(fill=tk.X)
        mode_buttons_frame.grid_columnconfigure(0, weight=1)
        mode_buttons_frame.grid_columnconfigure(1, weight=1)

        self.mode1Btn = self.create_modern_button(mode_buttons_frame, "20张模式",
                                                 self.changeMode1, 'accent')
        self.mode1Btn.grid(row=0, column=0, sticky='ew', padx=(0, 4))

        self.mode2Btn = self.create_modern_button(mode_buttons_frame, "10张模式",
                                                 self.changeMode2, 'accent')
        self.mode2Btn.grid(row=0, column=1, sticky='ew', padx=(4, 0))

        # 文件夹操作区域
        folder_frame = tk.Frame(parent, bg=self.colors['surface'])
        folder_frame.pack(fill=tk.X)

        folder_label = tk.Label(folder_frame, text="📁 文件管理:",
                               font=('Microsoft YaHei UI', 10, 'bold'),
                               fg=self.colors['text'], bg=self.colors['surface'])
        folder_label.pack(anchor=tk.W, pady=(0, 10))

        folder_buttons_frame = tk.Frame(folder_frame, bg=self.colors['surface'])
        folder_buttons_frame.pack(fill=tk.X)
        folder_buttons_frame.grid_columnconfigure(0, weight=1)
        folder_buttons_frame.grid_columnconfigure(1, weight=1)

        self.open_folder_btn = self.create_modern_button(folder_buttons_frame, "📂 当前会话",
                                                        self.open_deepdata_folder, 'info')
        self.open_folder_btn.grid(row=0, column=0, sticky='ew', padx=(0, 4))

        self.open_sessions_btn = self.create_modern_button(folder_buttons_frame, "📋 所有会话",
                                                          self.open_sessions_folder, 'info')
        self.open_sessions_btn.grid(row=0, column=1, sticky='ew', padx=(4, 0))

    def create_modern_button(self, parent, text, command, style='default', state='normal', width=None):
        """创建现代化按钮"""
        # 按钮颜色配置
        button_colors = {
            'primary': {'bg': self.colors['primary'], 'fg': 'white', 'hover': '#1E5F7A'},
            'success': {'bg': '#27AE60', 'fg': 'white', 'hover': '#1E8449'},
            'danger': {'bg': '#E74C3C', 'fg': 'white', 'hover': '#C0392B'},
            'accent': {'bg': self.colors['accent'], 'fg': 'white', 'hover': '#D17A01'},
            'info': {'bg': '#3498DB', 'fg': 'white', 'hover': '#2980B9'},
            'default': {'bg': self.colors['surface'], 'fg': self.colors['text'], 'hover': '#EAEAEA'}
        }

        color_config = button_colors.get(style, button_colors['default'])

        button = tk.Button(parent,
                          text=text,
                          command=command,
                          font=('Microsoft YaHei UI', 9, 'bold'),
                          bg=color_config['bg'],
                          fg=color_config['fg'],
                          relief='flat',
                          bd=0,
                          padx=15,
                          pady=8,
                          cursor='hand2',
                          state=state)

        if width:
            button.configure(width=width)

        # 添加悬停效果
        def on_enter(e):
            if button['state'] != 'disabled':
                button.configure(bg=color_config['hover'])

        def on_leave(e):
            if button['state'] != 'disabled':
                button.configure(bg=color_config['bg'])

        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)

        return button

    def create_debug_area(self, parent):
        """创建调试信息区域"""
        debug_frame = tk.Frame(parent, bg=self.colors['surface'])
        debug_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        # 标题
        debug_label = tk.Label(debug_frame, text="🔍 调试信息:",
                              font=('Microsoft YaHei UI', 10, 'bold'),
                              fg=self.colors['text'], bg=self.colors['surface'])
        debug_label.pack(anchor=tk.W, pady=(0, 10))

        # 文本框容器
        text_container = tk.Frame(debug_frame, bg=self.colors['surface'])
        text_container.pack(fill=tk.BOTH, expand=True)

        self.debug_text = tk.Text(text_container,
                                 height=6,  # 减少高度
                                 wrap=tk.WORD,
                                 font=('Consolas', 9),
                                 bg='#F8F9FA',
                                 fg=self.colors['text'],
                                 relief='flat',
                                 bd=1,
                                 padx=10,
                                 pady=8,
                                 selectbackground=self.colors['primary'],
                                 selectforeground='white')

        debug_scrollbar = ttk.Scrollbar(text_container, orient="vertical",
                                       command=self.debug_text.yview)
        self.debug_text.configure(yscrollcommand=debug_scrollbar.set)

        self.debug_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        debug_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def create_display_area(self, parent):
        """创建显示区域"""
        display_container = tk.Frame(parent, bg=self.colors['background'])
        display_container.pack(fill=tk.BOTH, expand=True)

        # 创建两个显示卡片的容器
        left_container = tk.Frame(display_container, bg=self.colors['background'])
        left_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        right_container = tk.Frame(display_container, bg=self.colors['background'])
        right_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # RGB图像显示卡片
        rgb_card_frame = tk.Frame(left_container,
                                 bg=self.colors['surface'],
                                 relief='flat', bd=1)
        rgb_card_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # RGB卡片阴影
        rgb_shadow = tk.Frame(left_container, bg='#E0E0E0')
        rgb_shadow.place(x=4, y=4, relwidth=1, relheight=1)
        rgb_card_frame.lift()

        # RGB标题
        rgb_title_frame = tk.Frame(rgb_card_frame, bg=self.colors['surface'])
        rgb_title_frame.pack(fill=tk.X, padx=15, pady=(15, 10))

        rgb_title = tk.Label(rgb_title_frame,
                            text="📷 RGB图像",
                            font=('Microsoft YaHei UI', 12, 'bold'),
                            fg=self.colors['primary'],
                            bg=self.colors['surface'])
        rgb_title.pack(side=tk.LEFT)

        # RGB分隔线
        rgb_separator = tk.Frame(rgb_card_frame, height=1, bg=self.colors['border'])
        rgb_separator.pack(fill=tk.X, padx=15)

        # RGB图像显示区域
        rgb_display_frame = tk.Frame(rgb_card_frame, bg=self.colors['surface'])
        rgb_display_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        self.rgb_label = tk.Label(rgb_display_frame,
                                 text="RGB图像将在此显示\n📸",
                                 font=('Microsoft YaHei UI', 14),
                                 fg=self.colors['text_light'],
                                 bg='#FAFAFA',
                                 relief='flat',
                                 bd=1)
        self.rgb_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 深度图像显示卡片
        depth_card_frame = tk.Frame(right_container,
                                   bg=self.colors['surface'],
                                   relief='flat', bd=1)
        depth_card_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # 深度卡片阴影
        depth_shadow = tk.Frame(right_container, bg='#E0E0E0')
        depth_shadow.place(x=4, y=4, relwidth=1, relheight=1)
        depth_card_frame.lift()

        # 深度标题
        depth_title_frame = tk.Frame(depth_card_frame, bg=self.colors['surface'])
        depth_title_frame.pack(fill=tk.X, padx=15, pady=(15, 10))

        depth_title = tk.Label(depth_title_frame,
                              text="🌊 深度图像",
                              font=('Microsoft YaHei UI', 12, 'bold'),
                              fg=self.colors['primary'],
                              bg=self.colors['surface'])
        depth_title.pack(side=tk.LEFT)

        # 深度分隔线
        depth_separator = tk.Frame(depth_card_frame, height=1, bg=self.colors['border'])
        depth_separator.pack(fill=tk.X, padx=15)

        # 深度图像显示区域
        depth_display_frame = tk.Frame(depth_card_frame, bg=self.colors['surface'])
        depth_display_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        self.depth_label = tk.Label(depth_display_frame,
                                   text="深度图像将在此显示\n🌊",
                                   font=('Microsoft YaHei UI', 14),
                                   fg=self.colors['text_light'],
                                   bg='#FAFAFA',
                                   relief='flat',
                                   bd=1)
        self.depth_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def create_status_bar(self, parent):
        """创建状态栏"""
        status_container = tk.Frame(parent, bg=self.colors['background'])
        status_container.pack(fill=tk.X, pady=(20, 0))

        # 状态栏卡片
        status_card = tk.Frame(status_container,
                              bg=self.colors['surface'],
                              relief='flat',
                              bd=1)
        status_card.pack(fill=tk.X, padx=2, pady=2)

        # 添加阴影
        shadow = tk.Frame(status_container, bg='#E0E0E0', height=2)
        shadow.place(x=4, y=4, relwidth=1, height=50)
        status_card.lift()

        # 状态信息容器
        status_info = tk.Frame(status_card, bg=self.colors['surface'])
        status_info.pack(fill=tk.X, padx=20, pady=15)

        # 第一行：状态和计数器
        row1 = tk.Frame(status_info, bg=self.colors['surface'])
        row1.pack(fill=tk.X, pady=(0, 8))

        # 状态信息
        status_frame = tk.Frame(row1, bg=self.colors['surface'])
        status_frame.pack(side=tk.LEFT)

        tk.Label(status_frame, text="📊 状态:",
                font=('Microsoft YaHei UI', 10, 'bold'),
                fg=self.colors['text'], bg=self.colors['surface']).pack(side=tk.LEFT)

        self.status_var = tk.StringVar(value="🟢 就绪")
        self.status_label = tk.Label(status_frame, textvariable=self.status_var,
                                    font=('Microsoft YaHei UI', 10),
                                    fg=self.colors['primary'], bg=self.colors['surface'])
        self.status_label.pack(side=tk.LEFT, padx=(8, 0))

        # 保存计数器
        counter_frame = tk.Frame(row1, bg=self.colors['surface'])
        counter_frame.pack(side=tk.RIGHT)

        tk.Label(counter_frame, text="💾 已保存:",
                font=('Microsoft YaHei UI', 10, 'bold'),
                fg=self.colors['text'], bg=self.colors['surface']).pack(side=tk.LEFT)

        self.counter_var = tk.StringVar(value="0")
        counter_label = tk.Label(counter_frame, textvariable=self.counter_var,
                                font=('Microsoft YaHei UI', 10, 'bold'),
                                fg=self.colors['accent'], bg=self.colors['surface'])
        counter_label.pack(side=tk.LEFT, padx=(8, 0))

        # 第二行：会话信息
        row2 = tk.Frame(status_info, bg=self.colors['surface'])
        row2.pack(fill=tk.X)

        tk.Label(row2, text="📁 当前会话:",
                font=('Microsoft YaHei UI', 10, 'bold'),
                fg=self.colors['text'], bg=self.colors['surface']).pack(side=tk.LEFT)

        self.session_var = tk.StringVar(value="未开始")
        self.session_label = tk.Label(row2, textvariable=self.session_var,
                                     font=('Microsoft YaHei UI', 10),
                                     fg=self.colors['secondary'], bg=self.colors['surface'])
        self.session_label.pack(side=tk.LEFT, padx=(8, 0))

    def changeMode1(self):
        self.pictureSaveNumber = 20
        self.pictureSaveMode = 0

    def changeMode2(self):
        self.pictureSaveNumber = 10
        self.pictureSaveMode = 1

    def log_debug(self, message):
        """添加调试信息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.debug_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.debug_text.see(tk.END)
        print(f"[{timestamp}] {message}")

    def update_camera_device_list(self):
        """更新相机设备列表"""
        camera_names = [cam['name'] for cam in self.available_cameras]
        if camera_names:
            self.camera_device_combo['values'] = camera_names
            self.camera_device_combo.set(camera_names[0])
        else:
            self.camera_device_combo['values'] = ["无可用设备"]
            self.camera_device_combo.set("无可用设备")

    def refresh_cameras(self):
        """刷新相机设备列表"""
        self.log_debug("正在刷新相机设备列表...")
        self.detect_available_cameras()
        self.update_camera_device_list()
        self.log_debug(f"发现 {len(self.available_cameras)} 个相机设备")

    def test_camera(self):
        """测试选中的相机"""
        if not self.available_cameras:
            self.log_debug("错误: 没有可用的相机设备")
            return

        selected_name = self.camera_device_var.get()
        camera_index = next((cam['index'] for cam in self.available_cameras if cam['name'] == selected_name), 0)

        self.log_debug(f"正在测试相机 {camera_index}...")

        try:
            cap = cv2.VideoCapture(camera_index)
            if not cap.isOpened():
                self.log_debug(f"错误: 无法打开相机 {camera_index}")
                return

            # 设置分辨率
            resolution = self.resolution_var.get().split('x')
            width, height = int(resolution[0]), int(resolution[1])

            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            cap.set(cv2.CAP_PROP_FPS, int(self.fps_var.get()))

            # 读取几帧来测试
            for i in range(5):
                ret, frame = cap.read()
                if not ret:
                    self.log_debug(f"警告: 第{i + 1}帧读取失败")
                    break
                time.sleep(0.1)

            if ret:
                actual_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                actual_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                actual_fps = cap.get(cv2.CAP_PROP_FPS)

                self.log_debug(f"相机 {camera_index} 测试成功!")
                self.log_debug(f"实际分辨率: {int(actual_width)}x{int(actual_height)}")
                self.log_debug(f"实际帧率: {int(actual_fps)}fps")
                self.log_debug(f"图像格式: {frame.shape}")
            else:
                self.log_debug(f"错误: 相机 {camera_index} 无法读取图像")

            cap.release()

        except Exception as e:
            self.log_debug(f"相机测试异常: {str(e)}")

    def detect_camera_type(self):
        """检测相机类型"""
        if REALSENSE_AVAILABLE:
            try:
                pipeline = rs.pipeline()
                config = rs.config()
                pipeline_wrapper = rs.pipeline_wrapper(pipeline)
                pipeline_profile = config.resolve(pipeline_wrapper)

                if pipeline_profile:
                    self.camera_type = "realsense"
                    self.camera_type_var.set("Intel RealSense")
                    self.log_debug("检测到Intel RealSense相机")
                    return
            except:
                pass

        if self.available_cameras:
            self.camera_type = "opencv"
            self.camera_type_var.set("USB相机")
            self.log_debug(f"检测到 {len(self.available_cameras)} 个USB相机")
        else:
            self.log_debug("未检测到相机")

    def start_camera(self):
        """启动相机"""
        if self.camera_running:
            return

        if not self.available_cameras and self.camera_type_var.get() != "Intel RealSense":
            self.log_debug("错误: 没有可用的相机设备")
            messagebox.showerror("错误", "没有可用的相机设备，请先刷新设备列表")
            return

        selected_type = self.camera_type_var.get()

        try:
            if selected_type == "Intel RealSense":
                if self.start_realsense_camera():
                    self.camera_running = True
                    self.log_debug("RealSense相机启动成功")
                else:
                    raise Exception("无法启动RealSense相机")
            else:
                # 获取选中的相机索引
                selected_name = self.camera_device_var.get()
                self.camera_index = next(
                    (cam['index'] for cam in self.available_cameras if cam['name'] == selected_name), 0)

                if self.start_opencv_camera():
                    self.camera_running = True
                    self.log_debug(f"USB相机 {self.camera_index} 启动成功")
                else:
                    raise Exception(f"无法启动USB相机 {self.camera_index}")

            # 创建新的会话文件夹
            self.create_session_folder()

            # 更新按钮状态
            self.start_btn.config(state="disabled")
            self.stop_btn.config(state="normal")
            self.capture_btn.config(state="normal")
            self.test_btn.config(state="disabled")

            self.status_var.set("🟢 相机运行中")

            # 启动更新线程
            self.update_thread = threading.Thread(target=self.update_frames, daemon=True)
            self.update_thread.start()

        except Exception as e:
            self.log_debug(f"启动相机失败: {str(e)}")
            messagebox.showerror("错误", f"启动相机失败: {str(e)}")

    def start_realsense_camera(self):
        """启动RealSense相机"""
        if not REALSENSE_AVAILABLE:
            return False

        try:
            self.pipeline = rs.pipeline()
            config = rs.config()

            config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
            config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

            self.pipeline.start(config)
            self.align = rs.align(rs.stream.color)

            return True
        except Exception as e:
            self.log_debug(f"RealSense启动失败: {e}")
            return False

    def start_opencv_camera(self):
        """启动OpenCV相机"""
        try:
            self.log_debug(f"正在启动相机 {self.camera_index}...")

            # 尝试多种后端
            backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]

            for backend in backends:
                self.log_debug(f"尝试使用后端: {backend}")
                self.cap = cv2.VideoCapture(self.camera_index, backend)

                if self.cap.isOpened():
                    self.log_debug(f"成功使用后端 {backend} 打开相机")
                    break
                else:
                    self.log_debug(f"后端 {backend} 打开相机失败")
                    if self.cap:
                        self.cap.release()
                        self.cap = None

            if not self.cap or not self.cap.isOpened():
                self.log_debug("所有后端都无法打开相机")
                return False

            # 设置相机参数
            resolution = self.resolution_var.get().split('x')
            width, height = int(resolution[0]), int(resolution[1])
            fps = int(self.fps_var.get())

            self.log_debug(f"设置分辨率: {width}x{height}")
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            self.cap.set(cv2.CAP_PROP_FPS, fps)

            # 设置缓冲区大小以减少延迟
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            # 验证设置
            actual_width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            actual_height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            actual_fps = self.cap.get(cv2.CAP_PROP_FPS)

            self.log_debug(f"实际设置 - 分辨率: {int(actual_width)}x{int(actual_height)}, 帧率: {int(actual_fps)}")

            # 测试读取
            ret, frame = self.cap.read()
            if not ret:
                self.log_debug("错误: 无法读取相机图像")
                return False

            self.log_debug(f"读取测试成功，图像尺寸: {frame.shape}")
            return True

        except Exception as e:
            self.log_debug(f"OpenCV相机启动异常: {e}")
            return False

    def stop_camera(self):
        """停止相机"""
        self.camera_running = False

        # 更新会话结束信息
        if self.current_session_path and self.session_start_time:
            self.finalize_session()

        if self.pipeline:
            try:
                self.pipeline.stop()
                self.log_debug("RealSense相机已停止")
            except:
                pass
            self.pipeline = None

        if self.cap:
            try:
                self.cap.release()
                self.log_debug("USB相机已停止")
            except:
                pass
            self.cap = None

        # 更新按钮状态
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.capture_btn.config(state="disabled")
        self.test_btn.config(state="normal")

        # 清空显示
        self.rgb_label.config(image="", text="RGB图像将在此显示\n📸")
        self.depth_label.config(image="", text="深度图像将在此显示\n🌊")

        # 重置计数器和会话信息
        self.save_counter = 0
        self.counter_var.set("0")
        self.session_var.set("未开始")
        self.current_session_path = None

        self.status_var.set("🔴 相机已停止")

    def finalize_session(self):
        """结束会话，更新会话信息"""
        try:
            session_info_path = os.path.join(self.current_session_path, "session_info.json")
            if os.path.exists(session_info_path):
                with open(session_info_path, 'r', encoding='utf-8') as f:
                    session_info = json.load(f)

                # 更新结束时间和统计信息
                end_time = datetime.now()
                session_info.update({
                    "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "duration_seconds": int((end_time - self.session_start_time).total_seconds()),
                    "total_captures": self.save_counter,
                    "session_completed": True
                })

                with open(session_info_path, 'w', encoding='utf-8') as f:
                    json.dump(session_info, f, indent=2, ensure_ascii=False)

                self.log_debug(f"会话已结束，共拍摄 {self.save_counter} 张图像")
        except Exception as e:
            self.log_debug(f"结束会话时出错: {str(e)}")

    def update_frames(self):
        """更新图像帧"""
        frame_count = 0
        last_fps_time = time.time()

        while self.camera_running:
            try:
                if self.pipeline:  # RealSense模式
                    frames = self.pipeline.wait_for_frames()
                    aligned_frames = self.align.process(frames)

                    color_frame = aligned_frames.get_color_frame()
                    depth_frame = aligned_frames.get_depth_frame()

                    if color_frame and depth_frame:
                        self.current_rgb_frame = np.asanyarray(color_frame.get_data())
                        depth_image = np.asanyarray(depth_frame.get_data())

                        depth_colormap = cv2.applyColorMap(
                            cv2.convertScaleAbs(depth_image, alpha=0.03),
                            cv2.COLORMAP_JET
                        )
                        self.current_depth_frame = depth_image

                        self.update_display(self.current_rgb_frame, depth_colormap)

                elif self.cap:  # OpenCV模式
                    ret, frame = self.cap.read()
                    if ret:
                        self.current_rgb_frame = frame

                        # 创建深度估计图像
                        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                        # 使用边缘检测来模拟深度信息
                        edges = cv2.Canny(gray, 50, 150)
                        depth_simulation = 255 - edges  # 反转边缘，边缘处深度较小

                        # 应用高斯模糊来平滑深度图
                        depth_simulation = cv2.GaussianBlur(depth_simulation, (5, 5), 0)

                        depth_colormap = cv2.applyColorMap(depth_simulation, cv2.COLORMAP_JET)
                        self.current_depth_frame = depth_simulation

                        self.update_display(frame, depth_colormap)

                        # 计算实际帧率
                        frame_count += 1
                        if frame_count % 30 == 0:
                            current_time = time.time()
                            actual_fps = 30 / (current_time - last_fps_time)
                            last_fps_time = current_time
                            self.status_var.set(f"🟢 相机运行中 - 实际帧率: {actual_fps:.1f} FPS")
                    else:
                        self.log_debug("读取帧失败")
                        break

                time.sleep(0.033)  # ~30 FPS

            except Exception as e:
                self.log_debug(f"更新帧错误: {e}")
                break

    def update_display(self, rgb_frame, depth_colormap):
        """更新GUI显示"""
        try:
            # 获取显示区域的实际大小
            display_width, display_height = 400, 300

            # 处理RGB图像
            rgb_resized = cv2.resize(rgb_frame, (display_width, display_height))
            rgb_image = cv2.cvtColor(rgb_resized, cv2.COLOR_BGR2RGB)
            rgb_pil = Image.fromarray(rgb_image)

            # 添加圆角效果
            rgb_pil = self.add_rounded_corners(rgb_pil, 10)
            rgb_photo = ImageTk.PhotoImage(rgb_pil)

            # 处理深度图像
            depth_resized = cv2.resize(depth_colormap, (display_width, display_height))
            depth_image = cv2.cvtColor(depth_resized, cv2.COLOR_BGR2RGB)
            depth_pil = Image.fromarray(depth_image)

            # 添加圆角效果
            depth_pil = self.add_rounded_corners(depth_pil, 10)
            depth_photo = ImageTk.PhotoImage(depth_pil)

            # 更新显示
            self.root.after(0, lambda: self.rgb_label.config(image=rgb_photo, text=""))
            self.root.after(0, lambda: self.depth_label.config(image=depth_photo, text=""))

            # 保持引用防止垃圾回收
            self.rgb_label.image = rgb_photo
            self.depth_label.image = depth_photo

        except Exception as e:
            self.log_debug(f"显示更新错误: {e}")

    def add_rounded_corners(self, image, radius):
        """为图像添加圆角效果"""
        try:
            # 创建圆角遮罩
            mask = Image.new('L', image.size, 0)
            from PIL import ImageDraw
            draw = ImageDraw.Draw(mask)
            draw.rounded_rectangle([(0, 0), image.size], radius, fill=255)

            # 应用遮罩
            result = Image.new('RGBA', image.size, (0, 0, 0, 0))
            result.paste(image, (0, 0))
            result.putalpha(mask)

            return result
        except:
            # 如果圆角处理失败，返回原图
            return image

    def capture_and_save(self):
        """拍摄并保存图像和深度数据"""
        if not self.camera_running or self.current_rgb_frame is None:
            self.log_debug("错误: 相机未运行或无图像数据")
            messagebox.showwarning("警告", "请先启动相机")
            return

        if not self.current_session_path:
            self.log_debug("错误: 未创建会话文件夹")
            messagebox.showerror("错误", "会话文件夹未创建，请重新启动相机")
            return

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # 包含毫秒
            capture_id = f"{self.save_counter + 1:04d}_{timestamp}"

            # 保存RGB图像到rgb文件夹
            rgb_filename = f"rgb_{capture_id}.png"
            rgb_path = os.path.join(self.current_session_path, "rgb", rgb_filename)

            self.pictureSaveNumber -= 1
            if self.pictureSaveMode == 0:
                if self.pictureSaveNumber == 10:
                    pygame.mixer.music.load("D:\\python project\\ReadCamera\\Change.wav")
                    pygame.mixer.music.play()
                elif self.pictureSaveNumber == 1:
                    pygame.mixer.music.load("D:\\python project\\ReadCamera\\LastOne.wav")
                    pygame.mixer.music.play()
                elif self.pictureSaveNumber == 0:
                    pygame.mixer.music.load("D:\\python project\\ReadCamera\\Next.wav")
                    pygame.mixer.music.play()
                    self.pictureSaveNumber = 20
                else:
                    pygame.mixer.music.load("D:\\python project\\ReadCamera\\OK.wav")
                    pygame.mixer.music.play()
            if self.pictureSaveMode == 1:
                if self.pictureSaveNumber == 5:
                    pygame.mixer.music.load("D:\\python project\\ReadCamera\\Change.wav")
                    pygame.mixer.music.play()
                elif self.pictureSaveNumber == 1:
                    pygame.mixer.music.load("D:\\python project\\ReadCamera\\LastOne.wav")
                    pygame.mixer.music.play()
                elif self.pictureSaveNumber == 0:
                    pygame.mixer.music.load("D:\\python project\\ReadCamera\\Next.wav")
                    pygame.mixer.music.play()
                    self.pictureSaveNumber = 20
                else:
                    pygame.mixer.music.load("D:\\python project\\ReadCamera\\OK.wav")
                    pygame.mixer.music.play()

            if len(self.current_rgb_frame.shape) == 3:
                rgb_save = cv2.cvtColor(self.current_rgb_frame, cv2.COLOR_BGR2RGB)
            else:
                rgb_save = self.current_rgb_frame

            Image.fromarray(rgb_save).save(rgb_path)

            # 保存深度数据到depth文件夹
            depth_filename = f"depth_{capture_id}.npy"
            depth_path = os.path.join(self.current_session_path, "depth", depth_filename)
            np.save(depth_path, self.current_depth_frame)

            # 保存深度可视化图像到depth_vis文件夹
            depth_vis_filename = None
            if self.current_depth_frame is not None:
                if self.pipeline:
                    depth_colormap = cv2.applyColorMap(
                        cv2.convertScaleAbs(self.current_depth_frame, alpha=0.03),
                        cv2.COLORMAP_JET
                    )
                else:
                    depth_colormap = cv2.applyColorMap(self.current_depth_frame, cv2.COLORMAP_JET)

                depth_vis_filename = f"depth_vis_{capture_id}.png"
                depth_vis_path = os.path.join(self.current_session_path, "depth_vis", depth_vis_filename)
                cv2.imwrite(depth_vis_path, depth_colormap)

            # 保存元数据到metadata文件夹
            metadata = {
                "capture_id": capture_id,
                "capture_index": self.save_counter + 1,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
                "session_name": os.path.basename(self.current_session_path),
                "camera_type": self.camera_type,
                "camera_index": self.camera_index if hasattr(self, 'camera_index') else 0,
                "resolution": self.resolution_var.get(),
                "fps": self.fps_var.get(),
                "rgb_file": rgb_filename,
                "depth_file": depth_filename,
                "depth_visualization": depth_vis_filename,
                "image_size": self.current_rgb_frame.shape[:2],
                "relative_paths": {
                    "rgb": os.path.join("rgb", rgb_filename),
                    "depth": os.path.join("depth", depth_filename),
                    "depth_vis": os.path.join("depth_vis", depth_vis_filename) if depth_vis_filename else None
                }
            }

            metadata_filename = f"metadata_{capture_id}.json"
            metadata_path = os.path.join(self.current_session_path, "metadata", metadata_filename)
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            self.save_counter += 1
            self.counter_var.set(str(self.save_counter))

            self.log_debug(f"数据保存成功: {capture_id}")
            self.log_debug(f"保存位置: {os.path.basename(self.current_session_path)}")

        except Exception as e:
            self.log_debug(f"保存失败: {str(e)}")
            messagebox.showerror("错误", f"保存失败: {str(e)}")

    def open_deepdata_folder(self):
        """打开数据文件夹"""
        try:
            # 如果有当前会话，优先打开会话文件夹
            if self.current_session_path and os.path.exists(self.current_session_path):
                folder_to_open = self.current_session_path
                self.log_debug(f"打开当前会话文件夹: {os.path.basename(self.current_session_path)}")
            else:
                folder_to_open = self.deepdata_path
                self.log_debug("打开主数据文件夹")

            if os.name == 'nt':
                os.startfile(folder_to_open)
            elif os.name == 'posix':
                os.system(f'open "{folder_to_open}"' if sys.platform == 'darwin'
                          else f'xdg-open "{folder_to_open}"')
        except Exception as e:
            self.log_debug(f"无法打开文件夹: {str(e)}")
            messagebox.showerror("错误", f"无法打开文件夹: {str(e)}")

    def open_sessions_folder(self):
        """打开会话列表文件夹"""
        try:
            sessions_path = os.path.join(self.deepdata_path, "sessions")
            if os.name == 'nt':
                os.startfile(sessions_path)
            elif os.name == 'posix':
                os.system(f'open "{sessions_path}"' if sys.platform == 'darwin'
                          else f'xdg-open "{sessions_path}"')
            self.log_debug("打开会话列表文件夹")
        except Exception as e:
            self.log_debug(f"无法打开会话文件夹: {str(e)}")
            messagebox.showerror("错误", f"无法打开会话文件夹: {str(e)}")

    def on_closing(self):
        """程序关闭时的清理工作"""
        self.stop_camera()
        self.root.destroy()


def main():
    """主函数"""
    root = tk.Tk()
    app = DepthCameraGUI(root)

    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
