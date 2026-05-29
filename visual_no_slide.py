import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from data_stracture import Month, Thing, Day
import sys
from io import StringIO

class CalendarGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("日历待办事项管理系统")
        
        # 获取屏幕尺寸
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 设置窗口大小为屏幕的90%
        window_width = int(screen_width * 0.9)
        window_height = int(screen_height * 0.9)
        
        self.root.geometry(f"{window_width}x{window_height}")
        self.root.state('zoomed')  # Windows下最大化
        
        # 创建Month对象（1月）
        self.month = Month(month=1)
        
        # 添加一些示例数据
        self.add_sample_data()
        
        # 创建主框架
        self.main_frame = ttk.Frame(root, padding="5")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题和月份选择
        title_frame = ttk.Frame(self.main_frame)
        title_frame.pack(pady=5)
        
        title_label = ttk.Label(title_frame, text="2026年1月日历", font=("Arial", 18, "bold"))
        title_label.pack(side=tk.LEFT, padx=10)
        
        # 月份切换按钮
        ttk.Button(title_frame, text="◀ 上月", command=self.prev_month, width=8).pack(side=tk.LEFT, padx=5)
        self.month_label = ttk.Label(title_frame, text="1月", font=("Arial", 14))
        self.month_label.pack(side=tk.LEFT, padx=10)
        ttk.Button(title_frame, text="下月 ▶", command=self.next_month, width=8).pack(side=tk.LEFT, padx=5)
        
        # 计算格子大小（根据屏幕尺寸动态调整）
        self.calc_grid_size(window_width, window_height)
        
        # 创建日历框架
        self.calendar_frame = ttk.Frame(self.main_frame)
        self.calendar_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 星期标签
        weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        for i, day in enumerate(weekdays):
            label = ttk.Label(self.calendar_frame, text=day, font=("Arial", 11, "bold"), 
                            width=self.cell_width//10, anchor="center")
            label.grid(row=0, column=i, padx=1, pady=2, sticky="ew")
        
        # 创建30天的格子（6行x7列）
        self.day_frames = {}
        self.create_calendar_grid()
        
        # 控制按钮框架
        control_frame = ttk.Frame(self.main_frame)
        control_frame.pack(pady=10)
        
        ttk.Button(control_frame, text="➕ 添加待办", command=self.open_add_dialog, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="📋 查看全部", command=self.view_all_things, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="🔄 刷新", command=self.refresh_all, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="🗑️ 清空全部", command=self.clear_all_things, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="❌ 退出", command=self.root.quit, width=8).pack(side=tk.LEFT, padx=5)
        
        # 状态栏
        self.status_bar = ttk.Label(self.main_frame, text="就绪 | 双击任意日期查看详细事项", relief=tk.SUNKEN)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=2)
        
        # 配置网格权重
        for i in range(7):
            self.calendar_frame.columnconfigure(i, weight=1)
        for i in range(1, 7):  # 6行日历格子
            self.calendar_frame.rowconfigure(i, weight=1)
    
    def calc_grid_size(self, window_width, window_height):
        """计算格子大小"""
        # 每个格子宽度 = 窗口宽度 / 7 - 边距
        self.cell_width = max(140, window_width // 7 - 10)
        # 每个格子高度 = (窗口高度 - 其他元素高度) / 6
        self.cell_height = max(120, (window_height - 200) // 6)
    
    def prev_month(self):
        """上一个月"""
        if self.month.month > 1:
            self.month.month -= 1
            self.month_label.config(text=f"{self.month.month}月")
            self.clear_all_things(silent=True)
            self.refresh_all()
            self.update_status(f"已切换到{self.month.month}月")
    
    def next_month(self):
        """下一个月"""
        if self.month.month < 12:
            self.month.month += 1
            self.month_label.config(text=f"{self.month.month}月")
            self.clear_all_things(silent=True)
            self.refresh_all()
            self.update_status(f"已切换到{self.month.month}月")
    
    def add_sample_data(self):
        """添加示例数据"""
        # 第1天
        thing1 = Thing(content="完成项目报告", time=[], deadline=True)
        thing2 = Thing(content="买水果", time=[], deadline=False)
        self.month.add_things(1, [thing1, thing2])
        
        # 第5天
        thing3 = Thing(content="参加部门会议", time=[10, 0], deadline=False)
        self.month.add_thing(5, thing3)
        
        # 第10天
        thing8 = Thing(content="文档整理", time=[14, 30], deadline=False)
        self.month.add_thing(10, thing8)
        
        # 第15天
        thing4 = Thing(content="提交年度总结", time=[], deadline=True)
        thing5 = Thing(content="健身", time=[18, 0], deadline=False)
        self.month.add_things(15, [thing4, thing5])
        
        # 第20天
        thing9 = Thing(content="团队聚餐", time=[19, 0], deadline=False)
        self.month.add_thing(20, thing9)
        
        # 第25天
        thing6 = Thing(content="朋友聚会", time=[19, 0], deadline=False)
        self.month.add_thing(25, thing6)
        
        # 第28天
        thing10 = Thing(content="项目截止", time=[], deadline=True)
        self.month.add_thing(28, thing10)
        
        # 第30天
        thing7 = Thing(content="月末总结", time=[], deadline=True)
        self.month.add_thing(30, thing7)
    
    def create_calendar_grid(self):
        """创建日历格子（6行x7列，显示1-30日）"""
        # 2026年1月1日是周四，所以第1天应该在第4列（索引3）
        start_offset = 3  # 周四的偏移量（周一=0, 周二=1, 周三=2, 周四=3）
        
        row = 1  # 从第1行开始（第0行是星期标签）
        col = start_offset
        
        for day_num in range(1, 31):
            # 创建日期框
            frame = tk.Frame(self.calendar_frame, relief=tk.RAISED, borderwidth=2, 
                           bg='white', cursor="hand2")
            frame.grid(row=row, column=col, padx=2, pady=2, sticky="nsew")
            
            # 设置固定大小
            frame.grid_propagate(False)
            frame.configure(width=self.cell_width, height=self.cell_height)
            
            # 顶部框架（日期和操作按钮）
            top_frame = tk.Frame(frame, bg='white')
            top_frame.pack(fill=tk.X, padx=3, pady=2)
            
            # 日期标签
            date_label = tk.Label(top_frame, text=f"{day_num}", font=("Arial", 12, "bold"), 
                                 fg="blue", bg='white')
            date_label.pack(side=tk.LEFT)
            
            # 添加快速添加按钮
            add_btn = tk.Button(top_frame, text="+", font=("Arial", 10, "bold"), 
                               bg='#4CAF50', fg='white', width=2, height=1,
                               command=lambda d=day_num: self.quick_add_thing(d))
            add_btn.pack(side=tk.RIGHT, padx=2)
            
            # 待办事项显示区域
            text_area = tk.Text(frame, wrap=tk.WORD, font=("Arial", 9), 
                               bg='white', relief=tk.FLAT, cursor="hand2")
            text_area.pack(fill=tk.BOTH, expand=True, padx=3, pady=2)
            
            # 存储frame和text_area
            self.day_frames[day_num] = {
                'frame': frame,
                'text': text_area,
                'date_label': date_label,
                'top_frame': top_frame
            }
            
            # 绑定双击事件
            frame.bind("<Double-Button-1>", lambda e, d=day_num: self.open_day_detail(d))
            text_area.bind("<Double-Button-1>", lambda e, d=day_num: self.open_day_detail(d))
            date_label.bind("<Double-Button-1>", lambda e, d=day_num: self.open_day_detail(d))
            
            # 绑定右键菜单
            frame.bind("<Button-3>", lambda e, d=day_num: self.show_context_menu(e, d))
            text_area.bind("<Button-3>", lambda e, d=day_num: self.show_context_menu(e, d))
            
            # 更新格子内容
            self.update_day_display(day_num)
            
            # 更新列和行
            col += 1
            if col > 6:  # 一周7天（0-6）
                col = 0
                row += 1
    
    def show_context_menu(self, event, day_num):
        """显示右键菜单"""
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="添加待办事项", command=lambda: self.open_add_dialog(day_num))
        menu.add_command(label="查看详情", command=lambda: self.open_day_detail(day_num))
        menu.add_separator()
        menu.add_command(label="清空当天事项", command=lambda: self.clear_day(day_num))
        menu.post(event.x_root, event.y_root)
    
    def quick_add_thing(self, day_num):
        """快速添加待办事项"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"快速添加 - 第{day_num}天")
        dialog.geometry("400x350")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text=f"为第{day_num}天添加待办事项", font=("Arial", 12, "bold")).pack(pady=10)
        
        ttk.Label(dialog, text="事项内容:", font=("Arial", 10)).pack(pady=5)
        content_entry = ttk.Entry(dialog, width=40)
        content_entry.pack(pady=5)
        
        ttk.Label(dialog, text="时间 (时:分，可选):", font=("Arial", 10)).pack(pady=5)
        time_frame = ttk.Frame(dialog)
        time_frame.pack(pady=5)
        hour_entry = ttk.Entry(time_frame, width=5)
        hour_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(time_frame, text=":").pack(side=tk.LEFT)
        minute_entry = ttk.Entry(time_frame, width=5)
        minute_entry.pack(side=tk.LEFT, padx=5)
        
        deadline_var = tk.BooleanVar()
        ttk.Checkbutton(dialog, text="标记为截止日期", variable=deadline_var).pack(pady=10)
        
        def add():
            content = content_entry.get()
            if not content:
                messagebox.showerror("错误", "请输入事项内容")
                return
            
            time_list = []
            if hour_entry.get() and minute_entry.get():
                try:
                    hour = int(hour_entry.get())
                    minute = int(minute_entry.get())
                    if 0 <= hour <= 23 and 0 <= minute <= 59:
                        time_list = [hour, minute]
                except ValueError:
                    pass
            
            thing = Thing(content=content, time=time_list, deadline=deadline_var.get())
            self.month.add_thing(day_num, thing)
            self.update_day_display(day_num)
            self.update_status(f"已添加事项到第{day_num}天")
            dialog.destroy()
        
        ttk.Button(dialog, text="添加", command=add).pack(pady=20)
        ttk.Button(dialog, text="取消", command=dialog.destroy).pack()
    
    def get_working_output(self, day_num):
        """获取某一天working函数的输出内容"""
        day = self.month.get_day(day_num)
        if day and day.everything:
            # 重定向标准输出到StringIO
            old_stdout = sys.stdout
            sys.stdout = StringIO()
            
            # 执行working函数
            day.working()
            
            # 获取输出内容
            output = sys.stdout.getvalue()
            
            # 恢复标准输出
            sys.stdout = old_stdout
            
            return output if output else "今日无事"
        else:
            return "今日无事"
    
    def update_day_display(self, day_num):
        """更新单个格子的显示内容"""
        if day_num in self.day_frames:
            text_area = self.day_frames[day_num]['text']
            text_area.config(state=tk.NORMAL)
            text_area.delete(1.0, tk.END)
            
            # 获取working输出
            output = self.get_working_output(day_num)
            
            # 解析输出并格式化显示
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
            
            # 显示事项数量
            day = self.month.get_day(day_num)
            thing_count = len(day.everything) if day else 0
            if thing_count > 0:
                text_area.insert(tk.END, f"📋 {thing_count}项\n", 'count')
            
            # 显示到文本区域
            if reminders:
                text_area.insert(tk.END, "📌 提醒:\n", 'reminder_title')
                for r in reminders[:3]:  # 最多显示3条
                    # 截取较短的内容
                    display_text = r[:20] + "..." if len(r) > 20 else r
                    text_area.insert(tk.END, f"  • {display_text}\n", 'reminder')
                if len(reminders) > 3:
                    text_area.insert(tk.END, f"  • ...还有{len(reminders)-3}条\n", 'reminder')
            
            if deadline_reminders:
                text_area.insert(tk.END, "⚠️ 截止提醒:\n", 'deadline_title')
                for dr in deadline_reminders[:3]:  # 最多显示3条
                    display_text = dr[:20] + "..." if len(dr) > 20 else dr
                    text_area.insert(tk.END, f"  • {display_text}\n", 'deadline')
                if len(deadline_reminders) > 3:
                    text_area.insert(tk.END, f"  • ...还有{len(deadline_reminders)-3}条\n", 'deadline')
            
            if not reminders and not deadline_reminders:
                if thing_count > 0:
                    text_area.insert(tk.END, "✓ 暂无提醒", 'empty')
                else:
                    text_area.insert(tk.END, "📭 今日无事\n", 'empty')
                    text_area.insert(tk.END, "双击或右键添加", 'hint')
            
            # 设置文本样式
            text_area.tag_config('count', foreground='purple', font=('Arial', 9, 'bold'))
            text_area.tag_config('reminder_title', foreground='green', font=('Arial', 9, 'bold'))
            text_area.tag_config('reminder', foreground='#2E7D32', font=('Arial', 8))
            text_area.tag_config('deadline_title', foreground='red', font=('Arial', 9, 'bold'))
            text_area.tag_config('deadline', foreground='#C62828', font=('Arial', 8))
            text_area.tag_config('empty', foreground='#999999', font=('Arial', 9, 'italic'))
            text_area.tag_config('hint', foreground='#CCCCCC', font=('Arial', 8, 'italic'))
            
            text_area.config(state=tk.DISABLED)  # 设置为只读
    
    def refresh_all(self):
        """刷新所有格子的显示"""
        for day_num in range(1, 31):
            self.update_day_display(day_num)
        self.update_status("已刷新所有日历格子")
    
    def open_add_dialog(self, default_day=None):
        """打开添加待办事项对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("添加待办事项")
        dialog.geometry("450x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="添加新待办事项", font=("Arial", 14, "bold")).pack(pady=10)
        
        ttk.Label(dialog, text="日期 (1-30):", font=("Arial", 10)).pack(pady=5)
        day_entry = ttk.Entry(dialog, width=10)
        day_entry.pack(pady=5)
        if default_day:
            day_entry.insert(0, str(default_day))
        
        ttk.Label(dialog, text="事项内容:", font=("Arial", 10)).pack(pady=5)
        content_entry = ttk.Entry(dialog, width=45)
        content_entry.pack(pady=5)
        
        ttk.Label(dialog, text="时间 (可选，格式: 时 分):", font=("Arial", 10)).pack(pady=5)
        time_frame = ttk.Frame(dialog)
        time_frame.pack(pady=5)
        hour_entry = ttk.Entry(time_frame, width=5)
        hour_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(time_frame, text=":").pack(side=tk.LEFT)
        minute_entry = ttk.Entry(time_frame, width=5)
        minute_entry.pack(side=tk.LEFT, padx=5)
        
        deadline_var = tk.BooleanVar()
        ttk.Checkbutton(dialog, text="标记为截止日期（会提前3天提醒）", variable=deadline_var).pack(pady=10)
        
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
                    else:
                        messagebox.showerror("错误", "时间格式不正确")
                        return
                
                thing = Thing(content=content, time=time_list, deadline=deadline_var.get())
                self.month.add_thing(day_num, thing)
                self.update_day_display(day_num)
                messagebox.showinfo("成功", f"已添加事项到第{day_num}天")
                self.update_status(f"已添加事项到第{day_num}天")
                dialog.destroy()
            except ValueError:
                messagebox.showerror("错误", "请输入有效的数字")
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)
        ttk.Button(button_frame, text="添加", command=add_thing).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def open_day_detail(self, day_num):
        """打开某一天的详细视图"""
        detail_dialog = tk.Toplevel(self.root)
        detail_dialog.title(f"第{day_num}天 - 详细待办事项")
        detail_dialog.geometry("650x750")
        detail_dialog.transient(self.root)
        
        day = self.month.get_day(day_num)
        
        # 显示日期
        ttk.Label(detail_dialog, text=f"第{day_num}天", font=("Arial", 18, "bold")).pack(pady=10)
        
        # 显示所有事项
        if day and day.everything:
            ttk.Label(detail_dialog, text=f"共 {len(day.everything)} 个事项", font=("Arial", 12)).pack(pady=5)
            
            # 创建列表框显示事项
            list_frame = ttk.Frame(detail_dialog)
            list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            scrollbar = ttk.Scrollbar(list_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=12, 
                                font=("Arial", 10), selectmode=tk.SINGLE)
            listbox.pack(fill=tk.BOTH, expand=True)
            scrollbar.config(command=listbox.yview)
            
            thing_list = []
            for i, thing in enumerate(day.everything):
                time_str = f"{thing.time[0]}:{thing.time[1]:02d}" if thing.time else "无时间"
                deadline_str = "🔴 截止日期" if thing.deadline else "🟢 普通事项"
                display_text = f"{i+1}. {thing.content} [{time_str}] {deadline_str}"
                listbox.insert(tk.END, display_text)
                thing_list.append(thing)
            
            # 显示working输出
            ttk.Label(detail_dialog, text="📢 提醒信息:", font=("Arial", 12, "bold")).pack(pady=5)
            output_text = tk.Text(detail_dialog, wrap=tk.WORD, height=12, font=("Arial", 10))
            output_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            output = self.get_working_output(day_num)
            output_text.insert(1.0, output)
            output_text.config(state=tk.DISABLED)
            
            # 按钮框架
            button_frame = ttk.Frame(detail_dialog)
            button_frame.pack(pady=10)
            
            def add_new():
                self.open_add_dialog(day_num)
                detail_dialog.destroy()
            
            def delete_selected():
                selection = listbox.curselection()
                if selection:
                    index = selection[0]
                    if 0 <= index < len(day.everything):
                        del day.everything[index]
                        self.update_day_display(day_num)
                        detail_dialog.destroy()
                        self.open_day_detail(day_num)
                        self.update_status(f"已删除第{day_num}天的事项")
            
            def edit_selected():
                selection = listbox.curselection()
                if selection:
                    index = selection[0]
                    thing = day.everything[index]
                    self.edit_thing(day_num, index, thing)
                    detail_dialog.destroy()
            
            ttk.Button(button_frame, text="➕ 添加", command=add_new).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="✏️ 编辑", command=edit_selected).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="🗑️ 删除", command=delete_selected).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="关闭", command=detail_dialog.destroy).pack(side=tk.LEFT, padx=5)
        else:
            ttk.Label(detail_dialog, text="📭 暂无待办事项", font=("Arial", 14)).pack(pady=50)
            ttk.Button(detail_dialog, text="➕ 添加事项", 
                      command=lambda: [self.open_add_dialog(day_num), detail_dialog.destroy()]).pack(pady=10)
            ttk.Button(detail_dialog, text="关闭", command=detail_dialog.destroy).pack(pady=5)
    
    def edit_thing(self, day_num, index, thing):
        """编辑待办事项"""
        dialog = tk.Toplevel(self.root)
        dialog.title("编辑待办事项")
        dialog.geometry("450x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="编辑待办事项", font=("Arial", 14, "bold")).pack(pady=10)
        
        ttk.Label(dialog, text="事项内容:", font=("Arial", 10)).pack(pady=5)
        content_entry = ttk.Entry(dialog, width=45)
        content_entry.insert(0, thing.content)
        content_entry.pack(pady=5)
        
        ttk.Label(dialog, text="时间 (可选，格式: 时 分):", font=("Arial", 10)).pack(pady=5)
        time_frame = ttk.Frame(dialog)
        time_frame.pack(pady=5)
        hour_entry = ttk.Entry(time_frame, width=5)
        hour_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(time_frame, text=":").pack(side=tk.LEFT)
        minute_entry = ttk.Entry(time_frame, width=5)
        minute_entry.pack(side=tk.LEFT, padx=5)
        
        if thing.time:
            hour_entry.insert(0, str(thing.time[0]))
            minute_entry.insert(0, str(thing.time[1]))
        
        deadline_var = tk.BooleanVar(value=thing.deadline)
        ttk.Checkbutton(dialog, text="标记为截止日期（会提前3天提醒）", variable=deadline_var).pack(pady=10)
        
        def save():
            content = content_entry.get()
            if not content:
                messagebox.showerror("错误", "请输入事项内容")
                return
            
            time_list = []
            if hour_entry.get() and minute_entry.get():
                try:
                    hour = int(hour_entry.get())
                    minute = int(minute_entry.get())
                    if 0 <= hour <= 23 and 0 <= minute <= 59:
                        time_list = [hour, minute]
                except ValueError:
                    pass
            
            thing.content = content
            thing.time = time_list
            thing.deadline = deadline_var.get()
            
            self.update_day_display(day_num)
            self.update_status(f"已编辑第{day_num}天的事项")
            dialog.destroy()
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)
        ttk.Button(button_frame, text="保存", command=save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def clear_day(self, day_num):
        """清空某一天的所有事项"""
        if messagebox.askyesno("确认", f"确定要清空第{day_num}天的所有事项吗？"):
            day = self.month.get_day(day_num)
            if day:
                day.everything.clear()
                self.update_day_display(day_num)
                self.update_status(f"已清空第{day_num}天的所有事项")
    
    def view_all_things(self):
        """查看所有事项"""
        all_dialog = tk.Toplevel(self.root)
        all_dialog.title(f"{self.month.month}月 所有待办事项")
        all_dialog.geometry("900x750")
        all_dialog.transient(self.root)
        
        # 创建带滚动条的文本框
        text_frame = ttk.Frame(all_dialog)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_area = tk.Text(text_frame, wrap=tk.WORD, font=("Arial", 10), 
                           yscrollcommand=scrollbar.set)
        text_area.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=text_area.yview)
        
        total_info = f"{'='*70}\n"
        total_info += f"{' ':*^70}\n"
        total_info += f"{self.month.month}月 所有待办事项\n"
        total_info += f"{' ':*^70}\n\n"
        total_info += f"📊 总事项数: {self.month.get_total_things_count()}\n\n"
        
        for day_num in range(1, 31):
            day = self.month.get_day(day_num)
            if day and day.everything:
                total_info += f"\n{'─'*70}\n"
                total_info += f"📅 第{day_num}天 (共{len(day.everything)}项)\n"
                total_info += f"{'─'*70}\n"
                for i, thing in enumerate(day.everything):
                    time_str = f"{thing.time[0]}:{thing.time[1]:02d}" if thing.time else "无时间"
                    deadline_str = "🔴 截止日期" if thing.deadline else "🟢 普通事项"
                    total_info += f"  {i+1}. {thing.content}\n"
                    total_info += f"      ⏰ 时间: {time_str} | {deadline_str}\n"
                
                total_info += f"\n📢 提醒:\n"
                output = self.get_working_output(day_num)
                for line in output.split('\n'):
                    if line.strip() and '===' not in line:
                        total_info += f"     {line}\n"
        
        text_area.insert(1.0, total_info)
        text_area.config(state=tk.DISABLED)
        
        ttk.Button(all_dialog, text="关闭", command=all_dialog.destroy).pack(pady=10)
    
    def clear_all_things(self, silent=False):
        """清空所有事项"""
        if silent or messagebox.askyesno("确认", "确定要清空所有待办事项吗？此操作不可恢复！"):
            for day_num in range(1, 31):
                day = self.month.get_day(day_num)
                if day:
                    day.everything.clear()
            self.refresh_all()
            if not silent:
                self.update_status("已清空所有待办事项")
    
    def update_status(self, message):
        """更新状态栏消息"""
        self.status_bar.config(text=message)
        self.root.after(3000, lambda: self.status_bar.config(text="就绪 | 双击任意日期查看详细事项 | 右键打开快捷菜单"))


def main():
    root = tk.Tk()
    app = CalendarGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()