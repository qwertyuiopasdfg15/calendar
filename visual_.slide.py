import tkinter as tk
from tkinter import ttk, messagebox
from data_stracture import Month, Thing, Day
import sys
from io import StringIO

class CalendarGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("日历待办事项管理系统")
        self.root.geometry("1300x900")
        
        # 创建Month对象（1月）
        self.month = Month(month=1)
        
        # 添加一些示例数据
        self.add_sample_data()
        
        # 创建主框架
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 标题
        title_label = ttk.Label(self.main_frame, text="2026年1月日历", font=("Arial", 20, "bold"))
        title_label.grid(row=0, column=0, columnspan=7, pady=10)
        
        # 星期标签
        weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        for i, day in enumerate(weekdays):
            label = ttk.Label(self.main_frame, text=day, font=("Arial", 12, "bold"), width=14)
            label.grid(row=1, column=i, padx=2, pady=5)
        
        # 创建画布和滚动条（用于支持滚动）
        self.canvas_frame = ttk.Frame(self.main_frame)
        self.canvas_frame.grid(row=2, column=0, columnspan=7, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.canvas = tk.Canvas(self.canvas_frame, height=600)
        self.scrollbar = ttk.Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # 创建30天的格子
        self.day_frames = {}
        self.create_calendar_grid()
        
        # 控制按钮框架
        control_frame = ttk.Frame(self.main_frame)
        control_frame.grid(row=3, column=0, columnspan=7, pady=20)
        
        ttk.Button(control_frame, text="刷新所有", command=self.refresh_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="添加待办事项", command=self.open_add_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="查看所有事项", command=self.view_all_things).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="清空所有事项", command=self.clear_all_things).pack(side=tk.LEFT, padx=5)
        
        # 状态栏
        self.status_bar = ttk.Label(self.main_frame, text="就绪", relief=tk.SUNKEN)
        self.status_bar.grid(row=4, column=0, columnspan=7, sticky=(tk.W, tk.E), pady=5)
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(2, weight=1)
        self.canvas_frame.columnconfigure(0, weight=1)
        self.canvas_frame.rowconfigure(0, weight=1)
    
    def add_sample_data(self):
        """添加示例数据"""
        # 第1天
        thing1 = Thing(content="完成项目报告", time=[], deadline=True)
        thing2 = Thing(content="买水果", time=[], deadline=False)
        self.month.add_things(1, [thing1, thing2])
        
        # 第5天
        thing3 = Thing(content="参加部门会议", time=[10, 0], deadline=False)
        self.month.add_thing(5, thing3)
        
        # 第15天
        thing4 = Thing(content="提交年度总结", time=[], deadline=True)
        thing5 = Thing(content="健身", time=[18, 0], deadline=False)
        self.month.add_things(15, [thing4, thing5])
        
        # 第25天
        thing6 = Thing(content="朋友聚会", time=[19, 0], deadline=False)
        self.month.add_thing(25, thing6)
        
        # 第30天
        thing7 = Thing(content="月末总结", time=[], deadline=True)
        self.month.add_thing(30, thing7)
    
    def create_calendar_grid(self):
        """创建日历格子（6行，前5行每行7天，第6行只有2天）"""
        # 2026年1月1日是周四，所以第1天应该在第4列（索引3）
        start_offset = 3  # 周四的偏移量
        
        row = 0
        col = start_offset
        
        for day_num in range(1, 31):
            # 创建日期框
            frame = tk.Frame(self.scrollable_frame, relief=tk.RAISED, borderwidth=2, width=160, height=200)
            frame.grid(row=row, column=col, padx=2, pady=2, sticky=(tk.W, tk.E, tk.N, tk.S))
            frame.pack_propagate(False)
            
            # 日期标签
            date_label = tk.Label(frame, text=f"{day_num}", font=("Arial", 12, "bold"), fg="blue")
            date_label.pack(anchor=tk.NW, padx=5, pady=2)
            
            # 待办事项显示区域
            text_area = tk.Text(frame, wrap=tk.WORD, height=10, width=18, font=("Arial", 9))
            text_area.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
            
            # 存储frame和text_area
            self.day_frames[day_num] = {
                'frame': frame,
                'text': text_area,
                'date_label': date_label
            }
            
            # 绑定双击事件
            frame.bind("<Double-Button-1>", lambda e, d=day_num: self.open_day_detail(d))
            text_area.bind("<Double-Button-1>", lambda e, d=day_num: self.open_day_detail(d))
            
            # 更新格子内容
            self.update_day_display(day_num)
            
            # 更新列和行
            col += 1
            if col > 6:  # 一周7天（0-6）
                col = 0
                row += 1
        
        # 为最后一行添加一些空白格子（如果需要）
        remaining_cols = 7 - (30 - start_offset) % 7
        if remaining_cols < 7 and row == 4:  # 如果最后一行不满
            for _ in range(remaining_cols):
                empty_frame = tk.Frame(self.scrollable_frame, relief=tk.RAISED, borderwidth=2, width=160, height=200)
                empty_frame.grid(row=row, column=col, padx=2, pady=2, sticky=(tk.W, tk.E, tk.N, tk.S))
                empty_frame.pack_propagate(False)
                col += 1
    
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
                text_area.insert(tk.END, f"📋 共{thing_count}项\n", 'count')
            
            # 显示到文本区域
            if reminders:
                text_area.insert(tk.END, "📌 提醒:\n", 'reminder_title')
                for r in reminders[:3]:  # 最多显示3条
                    text_area.insert(tk.END, f"  {r[:20]}\n", 'reminder')
                if len(reminders) > 3:
                    text_area.insert(tk.END, f"  ...还有{len(reminders)-3}条\n", 'reminder')
            
            if deadline_reminders:
                text_area.insert(tk.END, "\n⚠️ 截止:\n", 'deadline_title')
                for dr in deadline_reminders[:3]:  # 最多显示3条
                    text_area.insert(tk.END, f"  {dr[:20]}\n", 'deadline')
                if len(deadline_reminders) > 3:
                    text_area.insert(tk.END, f"  ...还有{len(deadline_reminders)-3}条\n", 'deadline')
            
            if not reminders and not deadline_reminders:
                if thing_count > 0:
                    text_area.insert(tk.END, "暂无提醒", 'empty')
                else:
                    text_area.insert(tk.END, "今日无事", 'empty')
            
            # 设置文本样式
            text_area.tag_config('count', foreground='purple', font=('Arial', 9, 'bold'))
            text_area.tag_config('reminder_title', foreground='green', font=('Arial', 9, 'bold'))
            text_area.tag_config('reminder', foreground='black', font=('Arial', 8))
            text_area.tag_config('deadline_title', foreground='red', font=('Arial', 9, 'bold'))
            text_area.tag_config('deadline', foreground='red', font=('Arial', 8))
            text_area.tag_config('empty', foreground='gray', font=('Arial', 9, 'italic'))
            
            text_area.config(state=tk.DISABLED)  # 设置为只读
    
    def refresh_all(self):
        """刷新所有格子的显示"""
        for day_num in range(1, 31):
            self.update_day_display(day_num)
        self.update_status("已刷新所有日历格子")
    
    def open_add_dialog(self):
        """打开添加待办事项对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("添加待办事项")
        dialog.geometry("400x450")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="日期 (1-30):", font=("Arial", 10)).pack(pady=5)
        day_entry = ttk.Entry(dialog, width=10)
        day_entry.pack(pady=5)
        
        ttk.Label(dialog, text="事项内容:", font=("Arial", 10)).pack(pady=5)
        content_entry = ttk.Entry(dialog, width=40)
        content_entry.pack(pady=5)
        
        ttk.Label(dialog, text="时间 (格式: 时 分，留空表示无时间提醒):", font=("Arial", 10)).pack(pady=5)
        time_frame = ttk.Frame(dialog)
        time_frame.pack(pady=5)
        hour_entry = ttk.Entry(time_frame, width=5)
        hour_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(time_frame, text=":").pack(side=tk.LEFT)
        minute_entry = ttk.Entry(time_frame, width=5)
        minute_entry.pack(side=tk.LEFT, padx=5)
        
        deadline_var = tk.BooleanVar()
        ttk.Checkbutton(dialog, text="标记为截止日期", variable=deadline_var).pack(pady=10)
        
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
        
        ttk.Button(dialog, text="添加", command=add_thing).pack(pady=20)
    
    def open_day_detail(self, day_num):
        """打开某一天的详细视图"""
        detail_dialog = tk.Toplevel(self.root)
        detail_dialog.title(f"第{day_num}天 - 详细待办事项")
        detail_dialog.geometry("550x650")
        detail_dialog.transient(self.root)
        
        day = self.month.get_day(day_num)
        
        # 显示日期
        ttk.Label(detail_dialog, text=f"第{day_num}天", font=("Arial", 16, "bold")).pack(pady=10)
        
        # 显示所有事项
        if day and day.everything:
            ttk.Label(detail_dialog, text=f"共 {len(day.everything)} 个事项", font=("Arial", 12)).pack(pady=5)
            
            # 创建列表框显示事项
            list_frame = ttk.Frame(detail_dialog)
            list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            scrollbar = ttk.Scrollbar(list_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=12, font=("Arial", 10))
            listbox.pack(fill=tk.BOTH, expand=True)
            scrollbar.config(command=listbox.yview)
            
            for i, thing in enumerate(day.everything):
                time_str = f"{thing.time[0]}:{thing.time[1]:02d}" if thing.time else "无时间"
                deadline_str = "🔴截止日期" if thing.deadline else "🟢普通事项"
                listbox.insert(tk.END, f"{i+1}. {thing.content}")
                listbox.insert(tk.END, f"   时间: {time_str} | 类型: {deadline_str}")
                listbox.insert(tk.END, "-" * 40)
            
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
            
            def delete_selected():
                selection = listbox.curselection()
                if selection:
                    index = selection[0] // 3  # 每个事项占3行
                    if 0 <= index < len(day.everything):
                        del day.everything[index]
                        self.update_day_display(day_num)
                        detail_dialog.destroy()
                        self.open_day_detail(day_num)
                        self.update_status(f"已删除第{day_num}天的事项")
            
            ttk.Button(button_frame, text="删除选中事项", command=delete_selected).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="关闭", command=detail_dialog.destroy).pack(side=tk.LEFT, padx=5)
        else:
            ttk.Label(detail_dialog, text="📭 暂无待办事项", font=("Arial", 12)).pack(pady=50)
            ttk.Button(detail_dialog, text="关闭", command=detail_dialog.destroy).pack(pady=10)
    
    def view_all_things(self):
        """查看所有事项"""
        all_dialog = tk.Toplevel(self.root)
        all_dialog.title("所有待办事项")
        all_dialog.geometry("700x600")
        all_dialog.transient(self.root)
        
        text_area = tk.Text(all_dialog, wrap=tk.WORD, font=("Arial", 10))
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        total_info = f"{'='*50}\n"
        total_info += f"             {self.month.month}月 所有事项\n"
        total_info += f"{'='*50}\n\n"
        total_info += f"📊 总事项数: {self.month.get_total_things_count()}\n\n"
        
        for day_num in range(1, 31):
            day = self.month.get_day(day_num)
            if day and day.everything:
                total_info += f"\n{'─'*40}\n"
                total_info += f"📅 第{day_num}天 (共{len(day.everything)}项)\n"
                total_info += f"{'─'*40}\n"
                for i, thing in enumerate(day.everything):
                    time_str = f"{thing.time[0]}:{thing.time[1]:02d}" if thing.time else "无时间"
                    deadline_str = "🔴 截止日期" if thing.deadline else "🟢 普通事项"
                    total_info += f"  {i+1}. {thing.content}\n"
                    total_info += f"      ⏰ 时间: {time_str} | {deadline_str}\n"
                
                total_info += f"\n📢 提醒:\n"
                output = self.get_working_output(day_num)
                for line in output.split('\n'):
                    if line.strip():
                        total_info += f"     {line}\n"
        
        text_area.insert(1.0, total_info)
        text_area.config(state=tk.DISABLED)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(all_dialog, orient="vertical", command=text_area.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_area.configure(yscrollcommand=scrollbar.set)
        
        ttk.Button(all_dialog, text="关闭", command=all_dialog.destroy).pack(pady=10)
    
    def clear_all_things(self):
        """清空所有事项"""
        if messagebox.askyesno("确认", "确定要清空所有待办事项吗？此操作不可恢复！"):
            for day_num in range(1, 31):
                day = self.month.get_day(day_num)
                if day:
                    day.everything.clear()
            self.refresh_all()
            self.update_status("已清空所有待办事项")
    
    def update_status(self, message):
        """更新状态栏消息"""
        self.status_bar.config(text=message)
        self.root.after(3000, lambda: self.status_bar.config(text="就绪"))


def main():
    root = tk.Tk()
    app = CalendarGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()