import os
import re
import sys
import webbrowser
from tkinter import messagebox
from urllib.parse import urlparse

import keyboard
import pyperclip
import time


from PIL import Image, ImageTk
import customtkinter as ctk
import tkinter as tk



class HistoryState:
    """历史记录状态类，存储输入框状态"""

    def __init__(self, text, cursor_pos=0):
        self.text = text
        self.cursor_pos = cursor_pos


class EnhancedEntry(ctk.CTkEntry):
    """增强型输入框，支持撤销/重做功能"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 初始化历史记录
        self.undo_stack = []  # 撤销栈
        self.redo_stack = []  # 重做栈
        self.current_state = None  # 当前状态

        # 绑定事件
        self.bind("<KeyRelease>", self.track_changes)
        self.bind("<Control-z>", self.undo)
        self.bind("<Control-Z>", self.undo)
        self.bind("<Control-y>", self.redo)
        self.bind("<Control-Y>", self.redo)

        # 初始状态
        self.save_state()

    def save_state(self):
        """保存当前状态到历史记录"""
        current_text = self.get()
        cursor_pos = self.index(tk.INSERT)  # 获取光标位置

        # 只有当状态变化时才保存
        if not self.current_state or current_text != self.current_state.text:
            # 保存当前状态到撤销栈
            if self.current_state:
                self.undo_stack.append(self.current_state)
                # 限制栈大小
                if len(self.undo_stack) > 50:
                    self.undo_stack.pop(0)

            # 创建新状态
            self.current_state = HistoryState(current_text, cursor_pos)

            # 清除重做栈（新操作使重做历史无效）
            self.redo_stack = []

    def track_changes(self, event):
        """跟踪文本变化并保存状态"""
        # 忽略导航键（方向键、功能键等）
        if event.keysym in ("Left", "Right", "Up", "Down", "Shift_L", "Shift_R",
                            "Control_L", "Control_R", "Alt_L", "Alt_R", "Caps_Lock"):
            return

        self.save_state()

    def apply_state(self, state):
        """应用历史状态到输入框"""
        # 解除事件绑定避免循环
        self.unbind("<KeyRelease>")

        # 更新文本
        self.delete(0, "end")
        self.insert(0, state.text)

        # 恢复光标位置
        self.icursor(state.cursor_pos)

        # 重新绑定事件
        self.bind("<KeyRelease>", self.track_changes)

        # 更新当前状态
        self.current_state = state

    def undo(self, event=None):
        """执行撤销操作"""
        if self.undo_stack:
            # 将当前状态保存到重做栈
            if self.current_state:
                self.redo_stack.append(self.current_state)
                if len(self.redo_stack) > 50:
                    self.redo_stack.pop(0)

            # 应用上一个状态
            previous_state = self.undo_stack.pop()
            self.apply_state(previous_state)

        return "break"  # 阻止默认行为

    def redo(self, event=None):
        """执行重做操作"""
        if self.redo_stack:
            # 将当前状态保存到撤销栈
            if self.current_state:
                self.undo_stack.append(self.current_state)
                if len(self.undo_stack) > 50:
                    self.undo_stack.pop(0)

            # 应用重做状态
            next_state = self.redo_stack.pop()
            self.apply_state(next_state)

        return "break"  # 阻止默认行为

def resource_path(resource_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path,resource_path)



class VideoParser:
    def __init__(self):


        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("dark-blue")

        self.root = ctk.CTk()
        self.root.title("视频解释器")
        self.root.geometry("800x494")
        self.root.iconbitmap(resource_path("icon.ico"))

        self.platform_urls = {
            "腾讯视频": "https://v.qq.com/",
            "优酷视频": "https://www.youku.com/",
            "爱奇艺": "https://www.iqiyi.com/",
            "哔哩哔哩": "https://www.bilibili.com/",
            "芒果TV": "https://www.mgtv.com/",
            "乐视视频": "https://www.le.com/",
            "暴风影音": "http://www.baofeng.com/",
            "搜狐视频": "https://tv.sohu.com/",
            "1905电影": "https://www.1905.com/",
            "PPTV": "https://www.pptv.com/",
            "风行视频": "http://www.fun.tv/",
            "AcFun": "https://www.acfun.cn/"
        }

        self.parse_apis = {
            "①夜幕解析": "https://www.yemu.xyz/?url=",
            "②8090g": "https://www.8090g.cn/?url=",
            "③M1907": "https://im1907.top/?jx=",
            "④PlayerJY": "https://jx.playerjy.com/?url=",
            "⑤虾米": "https://jx.xmflv.com/?url=",
            "⑥ckplayer": "https://www.ckplayer.vip/jiexi/?url=",
            "⑦yparse": "https://jx.yparse.com/index.php?url=",
            "⑧剖云": "https://www.pouyun.com/?url=",
            "⑨咸鱼": "https://jx.aidouer.net/?url=",
            "⑩m3u8 ": "https://jx.m3u8.tv/jiexi/?url=",
            #"冰豆": "https://api.qianqi.net/vip/?url=",
            #"play": "https://www.playm3u8.cn/jiexi.php?url=",
        }

        self.current_frame = None
        self.create_ui()

    def create_ui(self):

        left_panel = ctk.CTkFrame(
            self.root,
            fg_color = "#ffffff",
            width = 200
        )
        left_panel.pack(side="left",fill="y",padx=2,pady=2)
        left_panel.pack_propagate(False)

        author_btn = ctk.CTkButton(
            left_panel,
            text="关于作者",
            height=35,
            command=self.show_about,
            fg_color = "#e0e0e0",
            hover_color = "#c0c0c0",
            text_color = "#000000",
            corner_radius=8,
        )

        author_btn.pack(pady=20,padx=20,fill="x",side="bottom")

        image = Image.open(resource_path("hezhao.jpg"))
        image = image.resize((180, 180))
        photo = ImageTk.PhotoImage(image)
        author_label = tk.Label(left_panel, image=photo, bg="#f0f0f0")
        author_label.image = photo
        author_label.pack(expand=True)

        image = Image.open(resource_path("dp.jpg"))
        image = image.resize((180, 180))
        photo = ImageTk.PhotoImage(image)
        author_label = tk.Label(left_panel, image=photo, bg="#f0f0f0")
        author_label.image = photo
        author_label.pack(expand=True)


        gif = Image.open(resource_path("qinqin.gif"))
        frames = []
        try:
            while True:
                frame = ImageTk.PhotoImage(gif.copy().resize((180, 180)))
                frames.append(frame)
                gif.seek(gif.tell() + 1)
        except EOFError:
            pass

        if frames:
            gif_label = tk.Label(left_panel, bg="#f0f0f0")
            gif_label.pack(expand=True)
            self.frames = frames

            def update_frame(frame_index=0):
                frame = self.frames[frame_index]
                gif_label.configure(image=frame)
                next_frame = (frame_index + 1) % len(self.frames)
                self.root.after(50,update_frame,next_frame)
            update_frame()

        self.main_panel = ctk.CTkFrame(
            self.root,
            fg_color = "#ffffff",
        )
        self.main_panel.pack(side="right", fill="both", expand=True, padx=2, pady=2)
        self.create_main_frame()
        self.create_about_frame()
        self.show_main_frame()

    def create_main_frame(self):

        self.main_frame = ctk.CTkFrame(
            self.main_panel,
            fg_color="#ffffff"
        )

        platform_frame = ctk.CTkFrame(self.main_frame,fg_color="transparent")
        platform_frame.pack(fill="x",padx=30,pady=(30,0))
        platform_label = ctk.CTkLabel(
            platform_frame,
            text="选择视频平台：",
            font=("微软雅黑", 14),
            text_color="#000000",
        )
        platform_label.pack(side="left",padx=(0,10))
        platform_names = list(self.platform_urls.keys())
        self.platform_var = ctk.StringVar(value=platform_names[0])
        custom_icon = ctk.CTkImage(
            light_image=Image.open(resource_path("icon.png")),  # 浅色模式图标
            dark_image=Image.open(resource_path("icon.png")),  # 深色模式图标（可以用同一个）
            size=(15, 15)
        )
        platform_dropdown = ctk.CTkOptionMenu(
            platform_frame,
            values=platform_names,
            variable=self.platform_var,
            width=200,
            height=35,
            fg_color="#e0e0e0",
            button_color="#e0e0e0",
            button_hover_color="#b0b0b0",
            dropdown_fg_color="#e0e0e0",
            dropdown_hover_color="#b0b0b0",
            dropdown_text_color="#000000",
            text_color="#000000",
            font=("微软雅黑", 13),
        )
        platform_dropdown.pack(side="left",padx=5)
        visit_btn = ctk.CTkButton(
            platform_frame,
            text="访问平台",
            width=100,
            height=35,
            command=self.visit_selected_platform,
            fg_color="#e0e0e0",
            hover_color="#c0c0c0",
            text_color="#000000",
            corner_radius=8,
        )
        visit_btn.pack(side="left",padx=10)

        api_frame = ctk.CTkFrame(self.main_frame,fg_color="transparent")
        api_frame.pack(fill="x",padx=30,pady=(20,0))
        api_label = ctk.CTkLabel(
            api_frame,
            text="选择解析接口：",
            font=("微软雅黑", 14),
            text_color="#000000"
        )
        api_label.pack(side="left",padx=(0,10))
        api_names = list(self.parse_apis.keys())
        self.api_var = ctk.StringVar(value=api_names[0])
        api_dropdown = ctk.CTkOptionMenu(
            api_frame,
            values=api_names,
            variable=self.api_var,
            width=200,
            height=35,fg_color="#e0e0e0",
            button_color="#e0e0e0",
            button_hover_color="#b0b0b0",
            dropdown_fg_color="#e0e0e0",
            dropdown_hover_color="#b0b0b0",
            dropdown_text_color="#000000",
            text_color="#000000",
            font=("微软雅黑", 13),
        )
        api_dropdown.pack(side="left",padx=5)

        # URL输入框框架
        url_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        url_frame.pack(fill="x", padx=30, pady=(20, 0))

        # 使用增强型输入框
        self.url_entry = EnhancedEntry(
            url_frame,
            placeholder_text="请输入视频链接...",
            height=35,
            font=("微软雅黑", 13),
            fg_color="#ffffff",
            text_color="#000000",
            border_color="#000000",
            border_width=0.5,
            corner_radius=8,
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 15))



        get_url_bun = ctk.CTkButton(
            url_frame,
            text="获取链接",
            width=100,
            height=35,
            command=self.get_current_url,
            fg_color="#e0e0e0",
            hover_color="#c0c0c0",
            text_color="#000000",
            corner_radius=8,
        )
        get_url_bun.pack(side="right",padx=5)
        clear_btn = ctk.CTkButton(
            url_frame,
            text="清空",
            width=100,
            height=35,
            command=lambda: self.url_entry.delete(0, 'end'),
            fg_color="#e0e0e0",
            hover_color="#c0c0c0",
            text_color="#000000",
            corner_radius=8,

        )
        clear_btn.pack(side="right",padx=5)

        parse_btn = ctk.CTkButton(
            url_frame,
            text="解析",
            width=100,
            height=35,
            command=self.parse_video,
            fg_color="#e0e0e0",
            hover_color="#c0c0c0",
            text_color="#000000",
            corner_radius=8,
        )
        parse_btn.pack(side="right")

        # 分割线  # 添加分割线
        separator = ctk.CTkFrame(
            self.main_frame,
            height=2,
            fg_color="#c0c0c0"  # 分割线颜色
        )
        separator.pack(fill="x", padx=30, pady=20)  # 布局
        # 使用说明  # 添加使用说明区域
        tip_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")  # 创建说明Frame
        tip_frame.pack(fill="x", padx=30)  # 布局
        tips = [  # 使用说明内容
            "使用说明：",
            "1. 点击按钮访问视频网站",
            "2. 找到想看的视频页面",
            "3. 点击'获取链接'按钮获取视频地址，或者手动复制输入视频地址",
            "4. 点击'开始解析'按钮观看视频"
        ]
        for i, tip in enumerate(tips):  # 遍历说明内容
            color = "#000000" if i == 0 else "#333333"  # 标题用黑色，内容用深灰色
            tip_label = ctk.CTkLabel(
                tip_frame,
                text=tip,  # 说明文本
                font=ctk.CTkFont(size=13),  # 字体大小
                text_color=color  # 文本颜色
            )
            tip_label.pack(anchor="w", pady=2)  # 布局


    def create_about_frame(self):
        self.about_frame = ctk.CTkFrame(  # 创建关于界面Frame
            self.main_panel,
            fg_color="#ffffff"  # 背景色
        )
        # 创建作者信息容器Frame
        info_frame = ctk.CTkFrame(
            self.about_frame,
            fg_color="#f0f0f0",  # 背景色
            corner_radius=15  # 圆角
        )
        info_frame.pack(padx=30, pady=30, fill="both", expand=True)  # 布局
        # 标题  # 添加标题标签
        title = ctk.CTkLabel(
            info_frame,
            text="祝愿董盼越来越幸福",  # 标题文本
            font=ctk.CTkFont(size=24),  # 字体微软雅黑，大小24
            text_color="#000000"  # 文本颜色
        )
        title.pack(pady=20)  # 布局
        # 作者信息

        disclaimer_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        disclaimer_frame.pack(pady=40, padx=30)  # 布局
        disclaimer_text = (
            "希望美丽勇敢的董盼越来越厉害\n\n"
            "做的事情都可以如愿以偿\n\n"
            "开心多多，烦恼少少\n\n"
            "                                    ---- 2025.7.28"
        )
        disclaimer_label = ctk.CTkLabel(
            disclaimer_frame,
            text=disclaimer_text,  # 文本
            font=ctk.CTkFont(size=20),  # 字体大小
            text_color="#666666",  # 文本颜色
            justify="left"  # 左对齐
        )
        disclaimer_label.pack(anchor="w")  # 布局


        # 返回按钮
        back_btn = ctk.CTkButton(
            info_frame,
            text="返回主页",  # 按钮文本
            command=self.show_main_frame,  # 点击后返回主界面
            height=40,  # 按钮高度
            fg_color="#e0e0e0",  # 按钮背景色
            hover_color="#c0c0c0",  # 悬停颜色
            text_color="#000000",  # 按钮文本颜色
            corner_radius=8  # 圆角
        )
        back_btn.pack(pady=(0, 20))  # 布局




    def show_main_frame(self):
        if self.current_frame:
            self.current_frame.pack_forget()
        self.main_frame.pack(fill="both",expand=True)
        self.current_frame = self.main_frame

    def show_about(self):
        if self.current_frame:
            self.current_frame.pack_forget()
        self.about_frame.pack(fill="both", expand=True)
        self.current_frame = self.about_frame

    def parse_video(self):
        url = self.url_entry.get()
        if url:
            selected_api = self.api_var.get()
            parse_api = f"{self.parse_apis[selected_api]}{url}"
            webbrowser.open(parse_api)
        else:
            self.show_warning("请先获取视频链接！")



    def get_current_url(self):
        try:
            pyperclip.copy('')
            time.sleep(0.2)
            keyboard.press_and_release('alt+tab')
            time.sleep(0.2)
            keyboard.press_and_release('alt+d')
            time.sleep(0.2)
            keyboard.press_and_release("ctrl+c")
            time.sleep(0.2)
            keyboard.press_and_release('alt+tab')
            time.sleep(0.2)
            url = pyperclip.paste().strip()
            self.url_entry.delete(0, 'end')
            self.url_entry.insert(0, url)

            if not url or not self.is_valid_video_url(url):
                pyperclip.copy('')
                time.sleep(0.2)
                keyboard.press_and_release('alt+tab+tab')
                time.sleep(0.2)
                keyboard.press_and_release('f6')
                time.sleep(0.2)
                keyboard.press_and_release('ctrl+c')
                time.sleep(0.2)
                keyboard.press_and_release('f6')
                time.sleep(0.2)
                keyboard.press_and_release('ctrl+c')
                time.sleep(0.2)
                keyboard.press_and_release('f6')
                time.sleep(0.2)
                keyboard.press_and_release('ctrl+c')
                time.sleep(0.2)
                url = pyperclip.paste().strip()
                self.url_entry.delete(0, 'end')
                self.url_entry.insert(0, url)
                time.sleep(0.2)

            if not url or not self.is_valid_video_url(url):
                self.show_warning(
                    "获取链接失败！\n\n"
                    "请确保：\n"
                    "1. 浏览器窗口已打开视频页面\n"
                    "2. 点击获取前先切换到浏览器窗口\n"
                    "3. 如果还是无法获取，请手动复制视频链接"
                )
        except Exception as e:
            self.show_warning(
                "获取链接失败！\n\n"
                "请手动复制视频链接，或按F6选中地址栏后按Ctrl+C复制"
            )






    def is_valid_video_url(self, url):
        if not url:
            return False
        try:
            parsed = urlparse(url)
            supported_patterns = [
                ('youku.com', r'v\.youku\.com/v_show/id_[^?]+'),
                ('iqiyi.com', r'www\.iqiyi\.com/[vw]_[^?]+'),
                ('v.qq.com', r'v\.qq\.com/x/cover/|v\.qq\.com/x/page/[^?]+'),
                ('bilibili.com', r'www\.bilibili\.com/video/[^?]+'),
                ('mgtv.com', r'www\.mgtv\.com/b/[^?]+'),
                ('le.com', r'www\.le\.com/ptv/vplay/[^?]+'),
                ('sohu.com', r'tv\.sohu\.com/v/[^?]+'),
                ('1905.com', r'www\.1905\.com/vod/play/[^?]+'),
                ('pptv.com', r'v\.pptv\.com/show/[^?]+'),
                ('fun.tv', r'www\.fun\.tv/vplay/[^?]+'),
                ('acfun.cn', r'www\.acfun\.cn/v/[^?]+')
            ]
            return any(
                domain in parsed.netloc and re.search(pattern, url)
                for domain, pattern in supported_patterns
            )
        except Exception as e:
            return False



    def show_warning(self, message):
        warning_window = ctk.CTkToplevel()
        warning_window.title("提示")
        warning_window.geometry("400*250")
        warning_window.attributes('-topmost',True)
        warning_window.transient(self.root)
        warning_window.configure(fg_color="#ffffff")
        warning_window.iconbitmap(resource_path("icon.png"))
        text_frame = ctk.CTkFrame(
            warning_window,
            fg_color="#ffffff"
        )
        text_frame.pack(expand=True,fill="both",padx=20,pady=(20,10))
        label = ctk.CTkLabel(
            text_frame,
            text=message,
            font=("微软雅黑", 14),
            text_color="#000000",
            wraplength=360,
            justify="center",
        )
        label.pack(expand=True)
        button_frame = ctk.CTkFrame(
            warning_window,
            fg_color="#ffffff"
        )
        button_frame.pack(fill="x",padx=20,pady=(0,20))
        btn = ctk.CTkButton(
            button_frame,
            text="确定",
            command=warning_window.destroy,
            width=100,
            height=40,
            fg_color="#e0e0e0",
            hover_color="#c0c0c0",
            text_color="#000000",
            corner_radius=8,
        )
        btn.pack(pady=10)
        warning_window.update()
        warning_window.minsize(warning_window.winfo_width(), warning_window.winfo_height())
        window_width = warning_window.winfo_width()
        window_height = warning_window.winfo_height()
        screen_width = warning_window.winfo_screenwidth()
        screen_height = warning_window.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        warning_window.geometry(f"+{x}+{y}")


    def run(self):  # 启动主循环的方法
        self.root.mainloop()  # 启动Tkinter主循环

    def visit_selected_platform(self):
        selected_platform = self.platform_var.get()
        url = self.platform_urls[selected_platform]
        webbrowser.open(url)


if __name__ == "__main__":  # 程序入口
    app = VideoParser()  # 创建VideoParser应用实例
    app.run()  # 启动应用主循环

