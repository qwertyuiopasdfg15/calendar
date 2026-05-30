import tkinter as tk
from tkinter import ttk, messagebox
from data_stracture import Month, Thing, Day
import sys
from io import StringIO
import threading
import re

# 尝试导入音频相关模块
try:
    import sounddevice as sd
    from scipy.io.wavfile import write
    import speech_recognition as sr
    import numpy as np
    AUDIO_AVAILABLE = True
    print("✅ 音频模块加载成功")
except ImportError as e:
    print(f"⚠️ 音频模块导入失败: {e}")
    AUDIO_AVAILABLE = False

# 导入大模型处理函数
try:
    from chat_for_charavter import parse_calendar_command
    AI_AVAILABLE = True
    print("✅ 大模型模块加载成功")
except ImportError:
    print("⚠️ 大模型模块导入失败，使用增强解析器")
    AI_AVAILABLE = False
    
    def parse_calendar_command(user_input):
        """增强的命令解析器，支持删除特定事项"""
        cmd = {"action": "add", "date": 1, "content": user_input, "time": [], "deadline": False, "delete_content": ""}
        
        # 提取日期
        date_match = re.search(r'(\d+)(?:号|日)', user_input)
        if date_match:
            cmd["date"] = int(date_match.group(1))
        
        # 提取时间
        time_match = re.search(r'(\d{1,2})[:：](\d{2})', user_input)
        if not time_match:
            time_match = re.search(r'(\d{1,2})\s*点(?:\s*(\d{1,2})\s*分)?', user_input)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2)) if time_match.group(2) else 0
                if "下午" in user_input and hour < 12:
                    hour += 12
                cmd["time"] = [hour, minute]
        
        # 判断操作类型
        if "删除" in user_input or "移除" in user_input or "去掉" in user_input:
            cmd["action"] = "delete"
            # 提取要删除的事项内容
            delete_patterns = [
                r'删除(?:第?\d+号?的)?[：:]*\s*(.+?)(?:的事?项?|$)',  # 删除1号的买水果
                r'把\s*(.+?)\s*删除',  # 把买水果删除
                r'移除\s*(.+?)(?:这个事项)?',  # 移除买水果
            ]
            for pattern in delete_patterns:
                match = re.search(pattern, user_input)
                if match:
                    cmd["delete_content"] = match.group(1).strip()
                    cmd["content"] = cmd["delete_content"]
                    break
            if not cmd["delete_content"]:
                # 如果没匹配到，尝试提取关键词
                words = user_input.replace("删除", "").replace("移除", "").replace("去掉", "")
                words = re.sub(r'\d+号', '', words)
                cmd["delete_content"] = words.strip()
                cmd["content"] = cmd["delete_content"]
        
        elif "查看" in user_input or "显示" in user_input or "有什么" in user_input:
            cmd["action"] = "view"
        
        elif "清空" in user_input or "清除" in user_input:
            cmd["action"] = "clear"
            if "所有" in user_input or "全部" in user_input:
                cmd["clear_all"] = True
        
        elif "截止" in user_input or "ddl" in user_input or "deadline" in user_input:
            cmd["action"] = "add"
            cmd["deadline"] = True
            # 提取内容
            content = user_input
            for word in ["截止", "ddl", "deadline", "添加", "提醒我"]:
                content = content.replace(word, "")
            content = re.sub(r'\d+号', '', content)
            cmd["content"] = content.strip()
        
        else:
            cmd["action"] = "add"
            # 提取内容
            content = user_input
            for word in ["添加", "提醒我", "记得", "帮我记"]:
                content = content.replace(word, "")
            content = re.sub(r'\d+号', '', content)
            cmd["content"] = content.strip()
        
        return cmd


class VoiceRecognizer:
    def __init__(self):
        self.available = AUDIO_AVAILABLE
        if not self.available:
            return
        self.is_recording = False
        self.audio_chunks = []
        self.sample_rate = 16000
        self.stream = None
        
    def start_recording(self):
        if not self.available:
            return False
        self.audio_chunks = []
        self.is_recording = True
        
        def callback(indata, frames, time, status):
            if self.is_recording:
                self.audio_chunks.append(indata.copy())
        
        try:
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype='int16',
                callback=callback
            )
            self.stream.start()
            return True
        except Exception as e:
            print(f"录音启动失败: {e}")
            self.available = False
            return False
    
    def stop_recording_and_recognize(self):
        if not self.available:
            return None
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        self.is_recording = False
        if len(self.audio_chunks) == 0:
            return None
        audio = np.concatenate(self.audio_chunks, axis=0)
        audio = audio.flatten()
        filename = "temp_voice.wav"
        try:
            write(filename, self.sample_rate, audio)
        except:
            return None
        try:
            r = sr.Recognizer()
            with sr.AudioFile(filename) as source:
                audio_data = r.record(source)
            text = r.recognize_google(audio_data, language='zh-CN')
            return text
        except:
            return None


class VoiceCalendarGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🎙️ 智能语音日历系统")
        self.root.geometry("1200x800")
        
        # 创建Month对象
        self.month = Month(month=1)
        
        # 语音识别器
        self.voice_recognizer = VoiceRecognizer()
        self.is_recording = False
        
        # 添加示例数据
        self.add_sample_data()
        
        # 创建主框架
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ========== 麦克风按钮区域 ==========
        voice_frame = tk.Frame(self.main_frame, bg="#FF5722", relief=tk.RAISED, bd=5, height=150)
        voice_frame.pack(fill=tk.X, pady=10, padx=10)
        voice_frame.pack_propagate(False)
        
        self.voice_btn = tk.Button(voice_frame, 
                                   text="🎤🎙️ 点击开始语音输入 🎙️🎤\n(说完后再次点击停止)", 
                                   font=("Arial", 20, "bold"),
                                   bg="#4CAF50", fg="white",
                                   command=self.toggle_voice_recording,
                                   cursor="hand2",
                                   relief=tk.RAISED,
                                   bd=5,
                                   height=3)
        self.voice_btn.pack(expand=True, fill=tk.BOTH, padx=20, pady=10)
        
        self.voice_status = tk.Label(voice_frame, text="💡 点击上方绿色按钮开始语音输入", 
                                     font=("Arial", 12),
                                     bg="#FF5722", fg="white")
        self.voice_status.pack(pady=5)
        
        if not AUDIO_AVAILABLE:
            self.voice_btn.config(text="⚠️ 语音功能不可用 ⚠️\n请安装依赖", bg="#9E9E9E", state=tk.DISABLED)
            self.voice_status.config(text="请运行: pip install sounddevice scipy SpeechRecognition numpy", fg="yellow")
        
        # ========== 标题和月份 ==========
        title_frame = ttk.Frame(self.main_frame)
        title_frame.pack(pady=10)
        
        title_label = tk.Label(title_frame, text="📅 智能语音日历", font=("Arial", 20, "bold"), fg="#2196F3")
        title_label.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(title_frame, text="◀ 上月", command=self.prev_month, width=10).pack(side=tk.LEFT, padx=5)
        self.month_label = ttk.Label(title_frame, text="2026年1月", font=("Arial", 16, "bold"))
        self.month_label.pack(side=tk.LEFT, padx=10)
        ttk.Button(title_frame, text="下月 ▶", command=self.next_month, width=10).pack(side=tk.LEFT, padx=5)
        
        # ========== 日历区域 ==========
        self.calendar_frame = ttk.Frame(self.main_frame)
        self.calendar_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 星期标签
        weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        for i, day in enumerate(weekdays):
            label = tk.Label(self.calendar_frame, text=day, font=("Arial", 11, "bold"),
                            bg="#2196F3", fg="white", width=10)
            label.grid(row=0, column=i, padx=2, pady=2, sticky="ew")
        
        # 创建日历格子
        self.day_frames = {}
        self.create_calendar_grid()
        
        # ========== 语音命令提示 ==========
        tip_frame = ttk.LabelFrame(self.main_frame, text="🎤 语音命令示例", padding="5")
        tip_frame.pack(pady=5, fill=tk.X, padx=10)
        
        tips = [
            "📅 添加: '1号下午3点开会' / '15号截止交报告'",
            "🗑️ 删除: '删除1号的买水果' / '把买水果删除' / '移除3号的健身'",
            "👀 查看: '查看5号' / '5号有什么事情'",
            "🧹 清空: '清空28号' / '清空所有事项'"
        ]
        
        for tip in tips:
            tk.Label(tip_frame, text=tip, font=("Arial", 9), fg="#666").pack(anchor=tk.W, padx=5, pady=2)
        
        # ========== 手动输入区域 ==========
        input_frame = ttk.LabelFrame(self.main_frame, text="📝 手动输入命令", padding="10")
        input_frame.pack(pady=10, fill=tk.X, padx=10)
        
        input_row = ttk.Frame(input_frame)
        input_row.pack(fill=tk.X)
        
        ttk.Label(input_row, text="命令:", font=("Arial", 11)).pack(side=tk.LEFT, padx=5)
        
        self.text_entry = ttk.Entry(input_row, font=("Arial", 11), width=50)
        self.text_entry.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        self.text_entry.bind("<Return>", self.process_text_input)
        
        ttk.Button(input_row, text="🚀 执行", command=self.process_text_input, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(input_row, text="🗑️ 清空", command=lambda: self.text_entry.delete(0, tk.END), width=8).pack(side=tk.LEFT, padx=5)
        
        # 示例命令
        example_frame = ttk.Frame(input_frame)
        example_frame.pack(pady=10)
        
        ttk.Label(example_frame, text="快速示例:", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        
        examples = [
            ("📅 1号开会", "1号开会"),
            ("⚠️ 15号截止交报告", "15号截止交报告"),
            ("👀 查看5号", "查看5号"),
            ("🗑️ 删除1号的买水果", "删除1号的买水果"),
            ("🗑️ 移除25号的朋友聚会", "移除25号的朋友聚会")
        ]
        
        for text, cmd in examples:
            btn = ttk.Button(example_frame, text=text, width=14,
                           command=lambda c=cmd: self.set_example_command(c))
            btn.pack(side=tk.LEFT, padx=3)
        
        # ========== 控制按钮 ==========
        control_frame = ttk.Frame(self.main_frame)
        control_frame.pack(pady=10)
        
        ttk.Button(control_frame, text="➕ 添加待办", command=self.open_add_dialog, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="📋 查看全部", command=self.view_all_things, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="🔄 刷新", command=self.refresh_all, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="🗑️ 清空全部", command=self.clear_all_things, width=10).pack(side=tk.LEFT, padx=5)
        
        if AUDIO_AVAILABLE:
            ttk.Button(control_frame, text="🎙️ 测试麦克风", command=self.test_microphone, width=12).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="❌ 退出", command=self.root.quit, width=8).pack(side=tk.LEFT, padx=5)
        
        # 状态栏
        self.status_bar = ttk.Label(self.main_frame, text="✅ 系统就绪 | 支持语音删除特定事项", relief=tk.SUNKEN)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=2)
        
        # 配置网格
        for i in range(7):
            self.calendar_frame.columnconfigure(i, weight=1)
    
    def set_example_command(self, command):
        self.text_entry.delete(0, tk.END)
        self.text_entry.insert(0, command)
        self.process_text_input()
    
    def test_microphone(self):
        def test():
            try:
                import sounddevice as sd
                import numpy as np
                
                self.update_status("🎤 正在测试麦克风...")
                self.voice_status.config(text="🔊 正在测试麦克风（3秒录音）...")
                
                duration = 3
                sample_rate = 16000
                
                self.root.bell()
                recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, 
                                  channels=1, dtype='int16')
                sd.wait()
                
                audio_level = np.abs(recording).max()
                
                if audio_level > 100:
                    self.voice_status.config(text=f"✅ 麦克风正常！音量: {audio_level}")
                    self.update_status(f"麦克风测试成功")
                    messagebox.showinfo("成功", f"麦克风工作正常！\n音量: {audio_level}")
                else:
                    self.voice_status.config(text="⚠️ 音量过低，请检查麦克风")
                    messagebox.showwarning("提示", "麦克风音量过低")
                    
            except Exception as e:
                self.voice_status.config(text=f"❌ 测试失败: {str(e)[:30]}")
                messagebox.showerror("错误", f"测试失败:\n{str(e)}")
        
        threading.Thread(target=test, daemon=True).start()
    
    def prev_month(self):
        if self.month.month > 1:
            self.month.month -= 1
            self.month_label.config(text=f"2026年{self.month.month}月")
            self.clear_all_things(silent=True)
            self.refresh_all()
    
    def next_month(self):
        if self.month.month < 12:
            self.month.month += 1
            self.month_label.config(text=f"2026年{self.month.month}月")
            self.clear_all_things(silent=True)
            self.refresh_all()
    
    def add_sample_data(self):
        thing1 = Thing(content="完成项目报告", time=[], deadline=True)
        thing2 = Thing(content="买水果", time=[], deadline=False)
        self.month.add_things(1, [thing1, thing2])
        
        thing3 = Thing(content="参加部门会议", time=[10, 0], deadline=False)
        self.month.add_thing(5, thing3)
        
        thing4 = Thing(content="提交年度总结", time=[], deadline=True)
        thing5 = Thing(content="健身", time=[18, 0], deadline=False)
        self.month.add_things(15, [thing4, thing5])
        
        thing6 = Thing(content="朋友聚会", time=[19, 0], deadline=False)
        self.month.add_thing(25, thing6)
        
        thing7 = Thing(content="写周报", time=[16, 0], deadline=False)
        self.month.add_thing(20, thing7)
    
    def create_calendar_grid(self):
        start_offset = 3
        row = 1
        col = start_offset
        
        for day_num in range(1, 31):
            frame = tk.Frame(self.calendar_frame, relief=tk.RAISED, borderwidth=2, 
                           bg='white', cursor="hand2")
            frame.grid(row=row, column=col, padx=2, pady=2, sticky="nsew")
            frame.config(width=100, height=100)
            frame.grid_propagate(False)
            
            top_frame = tk.Frame(frame, bg='white')
            top_frame.pack(fill=tk.X, padx=3, pady=2)
            
            date_label = tk.Label(top_frame, text=f"{day_num}", font=("Arial", 10, "bold"), 
                                 fg="blue", bg='white')
            date_label.pack(side=tk.LEFT)
            
            add_btn = tk.Button(top_frame, text="+", font=("Arial", 8, "bold"), 
                               bg='#4CAF50', fg='white', width=2,
                               command=lambda d=day_num: self.quick_add_thing(d))
            add_btn.pack(side=tk.RIGHT, padx=2)
            
            text_area = tk.Text(frame, wrap=tk.WORD, font=("Arial", 7), 
                               bg='white', relief=tk.FLAT, height=5)
            text_area.pack(fill=tk.BOTH, expand=True, padx=3, pady=2)
            
            self.day_frames[day_num] = {
                'frame': frame,
                'text': text_area,
                'date_label': date_label
            }
            
            frame.bind("<Double-Button-1>", lambda e, d=day_num: self.open_day_detail(d))
            text_area.bind("<Double-Button-1>", lambda e, d=day_num: self.open_day_detail(d))
            
            self.update_day_display(day_num)
            
            col += 1
            if col > 6:
                col = 0
                row += 1
    
    def get_working_output(self, day_num):
        day = self.month.get_day(day_num)
        if day and day.everything:
            old_stdout = sys.stdout
            sys.stdout = StringIO()
            day.working()
            output = sys.stdout.getvalue()
            sys.stdout = old_stdout
            return output if output else "今日无事"
        return "今日无事"
    
    def update_day_display(self, day_num):
        if day_num in self.day_frames:
            text_area = self.day_frames[day_num]['text']
            text_area.config(state=tk.NORMAL)
            text_area.delete(1.0, tk.END)
            
            output = self.get_working_output(day_num)
            
            reminders = []
            deadline_reminders = []
            lines = output.split('\n')
            current_section = None
            
            for line in lines:
                if '=== 截止日期提醒 ===' in line:
                    current_section = 'deadline'
                elif line.strip():
                    if current_section == 'deadline':
                        deadline_reminders.append(line.strip())
                    elif line.strip() != '今日无事':
                        reminders.append(line.strip())
            
            day = self.month.get_day(day_num)
            thing_count = len(day.everything) if day else 0
            if thing_count > 0:
                text_area.insert(tk.END, f"📋{thing_count}\n", 'count')
            
            # 显示事项列表（用于删除时参考）
            if day and day.everything:
                text_area.insert(tk.END, "📝\n", 'list_title')
                for thing in day.everything[:3]:  # 最多显示3个
                    text_area.insert(tk.END, f"•{thing.content[:10]}\n", 'list_item')
                if len(day.everything) > 3:
                    text_area.insert(tk.END, f"•+{len(day.everything)-3}\n", 'list_item')
            
            if reminders:
                for r in reminders[:2]:
                    text_area.insert(tk.END, f"📌{r[:12]}\n", 'reminder')
            
            if deadline_reminders:
                for dr in deadline_reminders[:2]:
                    text_area.insert(tk.END, f"⚠️{dr[:12]}\n", 'deadline')
            
            text_area.tag_config('count', foreground='purple', font=('Arial', 7, 'bold'))
            text_area.tag_config('list_title', foreground='blue', font=('Arial', 6, 'bold'))
            text_area.tag_config('list_item', foreground='#333', font=('Arial', 6))
            text_area.tag_config('reminder', foreground='green', font=('Arial', 6))
            text_area.tag_config('deadline', foreground='red', font=('Arial', 6))
            
            text_area.config(state=tk.DISABLED)
    
    def toggle_voice_recording(self):
        if not AUDIO_AVAILABLE:
            messagebox.showinfo("功能不可用", "语音功能需要安装依赖:\npip install sounddevice scipy SpeechRecognition numpy")
            return
        
        if not self.is_recording:
            self.start_voice_recording()
        else:
            self.stop_voice_recording()
    
    def start_voice_recording(self):
        self.is_recording = True
        self.voice_btn.config(text="🔴🔴 录音中... 点击停止 🔴🔴", bg="#f44336")
        self.voice_status.config(text="🔴 正在录音... 请说话 (说完后再次点击按钮)", fg="white")
        self.update_status("正在录音...")
        
        threading.Thread(target=self._record_audio, daemon=True).start()
    
    def _record_audio(self):
        self.voice_recognizer.start_recording()
    
    def stop_voice_recording(self):
        self.is_recording = False
        self.voice_btn.config(text="⏳ 处理中...", bg="#FF9800", state=tk.DISABLED)
        self.voice_status.config(text="⏳ 正在识别语音...", fg="white")
        
        threading.Thread(target=self._process_voice, daemon=True).start()
    
    def _process_voice(self):
        text = self.voice_recognizer.stop_recording_and_recognize()
        self.root.after(0, lambda: self._handle_voice_result(text))
    
    def _handle_voice_result(self, text):
        self.voice_btn.config(state=tk.NORMAL)
        
        if text:
            self.voice_status.config(text=f"✅ 识别成功: '{text}'", fg="white")
            self.process_command(text)
        else:
            self.voice_status.config(text="❌ 识别失败，请重试或使用文字输入", fg="white")
            messagebox.showwarning("识别失败", "未能识别语音，请重试或使用文字输入")
        
        self.voice_btn.config(text="🎤🎙️ 点击开始语音输入 🎙️🎤\n(说完后再次点击停止)", bg="#4CAF50")
        self.root.after(3000, lambda: self.voice_status.config(text="💡 点击上方绿色按钮开始语音输入"))
    
    def process_text_input(self, event=None):
        text = self.text_entry.get().strip()
        if text:
            self.text_entry.delete(0, tk.END)
            self.process_command(text)
    
    def process_command(self, user_input):
        self.update_status(f"处理: {user_input}")
        threading.Thread(target=self._parse_and_execute, args=(user_input,), daemon=True).start()
    
    def _parse_and_execute(self, user_input):
        command = parse_calendar_command(user_input)
        self.root.after(0, lambda: self.execute_command(command, user_input))
    
    def execute_command(self, command, original_input):
        action = command.get("action")
        date = command.get("date", 1)
        content = command.get("content", "")
        delete_content = command.get("delete_content", "")
        time_list = command.get("time", [])
        deadline = command.get("deadline", False)
        
        try:
            if action == "add":
                thing = Thing(content=content, time=time_list, deadline=deadline)
                self.month.add_thing(date, thing)
                self.update_day_display(date)
                msg = f"✅ 已在{date}号添加: {content}"
                if deadline:
                    msg += " [截止]"
                messagebox.showinfo("成功", msg)
                self.update_status(msg)
            
            elif action == "delete":
                day = self.month.get_day(date)
                if day and day.everything:
                    # 使用 delete_content 或 content 作为要删除的内容
                    search_content = delete_content if delete_content else content
                    
                    # 查找匹配的事项
                    found_items = []
                    for i, thing in enumerate(day.everything):
                        # 精确匹配或包含匹配
                        if search_content and (search_content in thing.content or thing.content in search_content):
                            found_items.append((i, thing))
                        # 如果没有指定具体内容，显示列表让用户选择
                    
                    if len(found_items) == 1:
                        # 只有一个匹配，直接删除
                        idx, thing = found_items[0]
                        del day.everything[idx]
                        self.update_day_display(date)
                        msg = f"🗑️ 已删除{date}号的事项: {thing.content}"
                        messagebox.showinfo("成功", msg)
                        self.update_status(msg)
                    
                    elif len(found_items) > 1:
                        # 多个匹配，让用户选择
                        self.show_delete_selection_dialog(date, found_items, search_content)
                    
                    else:
                        # 没有找到，显示当天所有事项让用户选择
                        if day.everything:
                            self.show_delete_selection_dialog(date, [(i, thing) for i, thing in enumerate(day.everything)], None)
                        else:
                            msg = f"❌ {date}号没有待办事项"
                            messagebox.showwarning("未找到", msg)
                            self.update_status(msg)
                else:
                    msg = f"❌ {date}号没有待办事项"
                    messagebox.showwarning("未找到", msg)
                    self.update_status(msg)
            
            elif action in ["view", "query"]:
                self.open_day_detail(date)
            
            elif action == "clear":
                if command.get("clear_all"):
                    self.clear_all_things()
                else:
                    day = self.month.get_day(date)
                    if day:
                        count = len(day.everything)
                        day.everything.clear()
                        self.update_day_display(date)
                        msg = f"🗑️ 已清空{date}号的{count}个事项"
                        messagebox.showinfo("成功", msg)
                        self.update_status(msg)
            
            self.update_status(f"完成: {original_input}")
            
        except Exception as e:
            messagebox.showerror("错误", str(e))
            self.update_status(f"错误: {str(e)}")
    
    def show_delete_selection_dialog(self, date, items, search_keyword):
        """显示删除选择对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"选择要删除的事项 - 第{date}天")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        
        tk.Label(dialog, text=f"第{date}天找到多个匹配事项:", font=("Arial", 12, "bold")).pack(pady=10)
        
        if search_keyword:
            tk.Label(dialog, text=f"搜索关键词: '{search_keyword}'", font=("Arial", 10), fg="blue").pack()
        
        listbox = tk.Listbox(dialog, font=("Arial", 11), height=8)
        listbox.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        for idx, thing in items:
            time_str = f" {thing.time[0]}:{thing.time[1]:02d}" if thing.time else ""
            deadline_str = " [截止]" if thing.deadline else ""
            listbox.insert(tk.END, f"{thing.content}{time_str}{deadline_str}")
        
        def delete_selected():
            selection = listbox.curselection()
            if selection:
                idx, thing = items[selection[0]]
                day = self.month.get_day(date)
                if day:
                    del day.everything[idx]
                    self.update_day_display(date)
                    msg = f"🗑️ 已删除{date}号的事项: {thing.content}"
                    messagebox.showinfo("成功", msg)
                    self.update_status(msg)
                    dialog.destroy()
            else:
                messagebox.showwarning("提示", "请选择要删除的事项")
        
        def delete_all():
            if messagebox.askyesno("确认", f"确定要删除第{date}天的所有{len(items)}个事项吗？"):
                day = self.month.get_day(date)
                if day:
                    # 删除所有匹配的（按索引从大到小删除）
                    for idx, _ in sorted(items, key=lambda x: x[0], reverse=True):
                        del day.everything[idx]
                    self.update_day_display(date)
                    msg = f"🗑️ 已删除{date}号的{len(items)}个事项"
                    messagebox.showinfo("成功", msg)
                    self.update_status(msg)
                    dialog.destroy()
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="删除选中", command=delete_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="删除全部", command=delete_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def refresh_all(self):
        for day_num in range(1, 31):
            self.update_day_display(day_num)
        self.update_status("已刷新")
    
    def open_add_dialog(self, default_day=None):
        dialog = tk.Toplevel(self.root)
        dialog.title("添加待办事项")
        dialog.geometry("400x400")
        
        ttk.Label(dialog, text="添加待办事项", font=("Arial", 14, "bold")).pack(pady=10)
        
        ttk.Label(dialog, text="日期 (1-30):").pack(pady=5)
        day_entry = ttk.Entry(dialog, width=10)
        day_entry.pack(pady=5)
        if default_day:
            day_entry.insert(0, str(default_day))
        
        ttk.Label(dialog, text="事项内容:").pack(pady=5)
        content_entry = ttk.Entry(dialog, width=40)
        content_entry.pack(pady=5)
        
        ttk.Label(dialog, text="时间 (时:分，可选):").pack(pady=5)
        time_frame = ttk.Frame(dialog)
        time_frame.pack()
        hour_entry = ttk.Entry(time_frame, width=5)
        hour_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(time_frame, text=":").pack(side=tk.LEFT)
        minute_entry = ttk.Entry(time_frame, width=5)
        minute_entry.pack(side=tk.LEFT, padx=5)
        
        deadline_var = tk.BooleanVar()
        ttk.Checkbutton(dialog, text="截止日期", variable=deadline_var).pack(pady=10)
        
        def add_thing():
            try:
                day_num = int(day_entry.get())
                if not 1 <= day_num <= 30:
                    messagebox.showerror("错误", "日期必须在1-30之间")
                    return
                content = content_entry.get()
                if not content:
                    messagebox.showerror("错误", "请输入事项内容")
                    return
                time_list = []
                if hour_entry.get() and minute_entry.get():
                    hour = int(hour_entry.get())
                    minute = int(minute_entry.get())
                    if 0 <= hour <= 23 and 0 <= minute <= 59:
                        time_list = [hour, minute]
                thing = Thing(content=content, time=time_list, deadline=deadline_var.get())
                self.month.add_thing(day_num, thing)
                self.update_day_display(day_num)
                dialog.destroy()
            except:
                messagebox.showerror("错误", "输入无效")
        
        ttk.Button(dialog, text="添加", command=add_thing).pack(pady=20)
    
    def quick_add_thing(self, day_num):
        dialog = tk.Toplevel(self.root)
        dialog.title(f"添加 - 第{day_num}天")
        dialog.geometry("350x300")
        
        ttk.Label(dialog, text=f"第{day_num}天", font=("Arial", 12, "bold")).pack(pady=10)
        
        ttk.Label(dialog, text="事项:").pack(pady=5)
        content_entry = ttk.Entry(dialog, width=40)
        content_entry.pack(pady=5)
        
        deadline_var = tk.BooleanVar()
        ttk.Checkbutton(dialog, text="截止日期", variable=deadline_var).pack(pady=10)
        
        def add():
            content = content_entry.get()
            if content:
                thing = Thing(content=content, time=[], deadline=deadline_var.get())
                self.month.add_thing(day_num, thing)
                self.update_day_display(day_num)
                dialog.destroy()
        
        ttk.Button(dialog, text="添加", command=add).pack(pady=20)
    
    def open_day_detail(self, day_num):
        dialog = tk.Toplevel(self.root)
        dialog.title(f"第{day_num}天详情")
        dialog.geometry("500x450")
        
        day = self.month.get_day(day_num)
        
        tk.Label(dialog, text=f"第{day_num}天", font=("Arial", 16, "bold")).pack(pady=10)
        
        if day and day.everything:
            listbox = tk.Listbox(dialog, font=("Arial", 11), height=8)
            listbox.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            
            for i, thing in enumerate(day.everything):
                time_str = f"{thing.time[0]}:{thing.time[1]:02d}" if thing.time else "无时间"
                deadline_str = "🔴 截止" if thing.deadline else "🟢 普通"
                listbox.insert(tk.END, f"{i+1}. {thing.content} [{time_str}] {deadline_str}")
            
            def delete_selected():
                selection = listbox.curselection()
                if selection:
                    if messagebox.askyesno("确认", f"确定要删除这个事项吗？"):
                        del day.everything[selection[0]]
                        self.update_day_display(day_num)
                        dialog.destroy()
                        self.open_day_detail(day_num)
            
            button_frame = ttk.Frame(dialog)
            button_frame.pack(pady=10)
            ttk.Button(button_frame, text="删除选中", command=delete_selected).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="关闭", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        else:
            tk.Label(dialog, text="暂无事项", font=("Arial", 12)).pack(pady=50)
            ttk.Button(dialog, text="关闭", command=dialog.destroy).pack(pady=10)
    
    def view_all_things(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("所有事项")
        dialog.geometry("600x500")
        
        text_area = tk.Text(dialog, wrap=tk.WORD)
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        info = f"=== {self.month.month}月 所有事项 ===\n\n"
        info += f"总数: {self.month.get_total_things_count()}\n\n"
        
        for day_num in range(1, 31):
            day = self.month.get_day(day_num)
            if day and day.everything:
                info += f"\n第{day_num}天:\n"
                for i, thing in enumerate(day.everything):
                    time_str = f"{thing.time[0]}:{thing.time[1]:02d}" if thing.time else "无时间"
                    deadline_str = "截止" if thing.deadline else "普通"
                    info += f"  {i+1}. {thing.content} [{time_str}] [{deadline_str}]\n"
        
        text_area.insert(1.0, info)
        text_area.config(state=tk.DISABLED)
        ttk.Button(dialog, text="关闭", command=dialog.destroy).pack(pady=10)
    
    def clear_all_things(self, silent=False):
        if silent or messagebox.askyesno("确认", "确定要清空所有待办事项吗？此操作不可恢复！"):
            for day_num in range(1, 31):
                day = self.month.get_day(day_num)
                if day:
                    day.everything.clear()
            self.refresh_all()
            if not silent:
                self.update_status("已清空所有事项")
    
    def update_status(self, message):
        self.status_bar.config(text=f"📌 {message}")
        self.root.after(3000, lambda: self.status_bar.config(text="✅ 系统就绪 | 支持语音删除特定事项"))


def main():
    root = tk.Tk()
    app = VoiceCalendarGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()