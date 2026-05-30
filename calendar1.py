"""
日历增强版 - 添加提醒功能（不修改原代码）
通过继承和扩展实现提醒功能
"""

import tkinter as tk
from tkinter import ttk, messagebox
from calendar2 import VoiceCalendarGUI, Month, Thing, VoiceRecognizer, parse_calendar_command, AUDIO_AVAILABLE
import sys
from io import StringIO
import threading
import re
from datetime import datetime


class ReminderType:
    """提醒类型常量"""
    NONE = "无提醒"
    TIME = "定时提醒"
    DEADLINE = "截止提醒"
    BOTH = "定时+截止提醒"


class EnhancedThing(Thing):
    """扩展的Thing类，支持更多提醒方式（不修改原Thing类）"""
    
    def __init__(self, content=None, time=None, deadline=False, reminder_days=None, reminder_method="弹窗"):
        """
        初始化扩展的Thing类
        
        Args:
            content: 事件内容
            time: 时间列表 [时, 分]
            deadline: 是否为截止日期
            reminder_days: 提前提醒天数列表，如[-3, -2, -1]表示提前3、2、1天
            reminder_method: 提醒方式 ("弹窗", "语音", "两者")
        """
        super().__init__(content, time, deadline)
        self._reminder_days = reminder_days if reminder_days else ([-3, -2, -1] if deadline else [])
        self._reminder_method = reminder_method
        self._created_time = datetime.now()
    
    @property
    def reminder_days(self):
        return self._reminder_days
    
    @reminder_days.setter
    def reminder_days(self, value):
        self._reminder_days = value
    
    @property
    def reminder_method(self):
        return self._reminder_method
    
    @reminder_method.setter
    def reminder_method(self, value):
        if value in ["弹窗", "语音", "两者"]:
            self._reminder_method = value
    
    def get_reminder_info(self, current_date):
        """获取提醒信息"""
        info = {
            "reminder_type": self.get_reminder_type(),
            "reminder_method": self._reminder_method,
            "reminder_days": self._reminder_days,
            "reminder_time": f"{self.time[0]}:{self.time[1]:02d}" if self.time else "无",
            "active_reminders": []
        }
        
        # 检查当前日期的提醒
        if self.deadline and self._reminder_days:
            for day_offset in self._reminder_days:
                if current_date == day_offset:
                    info["active_reminders"].append(f"⚠️ 截止提醒：还剩{abs(day_offset)}天")
        
        if self.time and not self.deadline:
            info["active_reminders"].append(f"⏰ 定时提醒：{info['reminder_time']}")
        
        return info
    
    def get_reminder_type(self):
        """获取提醒类型"""
        has_time = bool(self.time)
        if self.deadline and has_time:
            return ReminderType.BOTH
        elif self.deadline:
            return ReminderType.DEADLINE
        elif has_time:
            return ReminderType.TIME
        else:
            return ReminderType.NONE
    
    def update_reminder_method(self, method):
        """更新提醒方式"""
        if method in ["弹窗", "语音", "两者"]:
            self._reminder_method = method
            return True
        return False
    
    def update_reminder_days(self, days):
        """更新提前提醒天数"""
        self._reminder_days = days


class VoiceCalendarWithReminder(VoiceCalendarGUI):
    """带提醒功能的语音日历（继承原类，不修改原代码）"""
    
    def __init__(self, root):
        # 保存原始方法
        self.original_add_thing = None
        self.original_add_sample_data = None
        
        # 先初始化父类
        super().__init__(root)
        
        # 替换Month中的add_thing方法
        self.original_add_thing = self.month.add_thing
        self.month.add_thing = self._enhanced_add_thing
        
        # 重新加载示例数据（使用增强版）
        self._reload_sample_data()
        
        # 添加提醒命令解析器
        self.reminder_commands = self._get_reminder_commands()
        
        # 在状态栏添加提示
        self.status_bar.config(text="✅ 系统就绪 | 支持语音修改提醒方式 | 双击查看详细提醒")
        
        # 在语音命令提示区域添加提醒相关命令
        self._add_reminder_tips()
    
    def _get_reminder_commands(self):
        """获取提醒相关的命令模式"""
        return {
            "update_method": r'(?:把|将)?\s*(\d+号)?的?[\s]*(.+?)(?:改成|修改为|设置成|改为)\s*(弹窗|语音|两者)\s*(?:提醒)?',
            "update_days": r'(?:设置|调整)?\s*(\d+号)?的?[\s]*(.+?)(?:提前|提前\s*(\d+)\s*天)\s*(?:提醒)?',
            "cancel_reminder": r'(?:取消|删除|移除)\s*(\d+号)?的?[\s]*(.+?)(?:的)?\s*(?:提醒|提前提醒)'
        }
    
    def _add_reminder_tips(self):
        """添加提醒相关的提示"""
        # 找到语音命令提示框并添加新提示
        for child in self.main_frame.winfo_children():
            if isinstance(child, ttk.LabelFrame) and child.cget("text") == "🎤 语音命令示例":
                # 添加新的提示
                new_tips = [
                    "⚙️ 修改提醒: '把1号的开会改成语音提醒' / '修改15号的提醒方式为弹窗'",
                    "📅 设置提前提醒: '设置1号开会提前3天提醒' / '取消15号的提前提醒'"
                ]
                for tip in new_tips:
                    tk.Label(child, text=tip, font=("Arial", 9), fg="#2196F3").pack(anchor=tk.W, padx=5, pady=2)
                break
    
    def _reload_sample_data(self):
        """重新加载示例数据（使用增强版Thing）"""
        # 清空现有数据
        for day in self.month.days:
            day.everything.clear()
        
        # 添加增强版示例数据
        thing1 = EnhancedThing(content="完成项目报告", time=[], deadline=True, 
                               reminder_days=[-3, -2, -1], reminder_method="弹窗")
        thing2 = EnhancedThing(content="买水果", time=[], deadline=False, reminder_method="语音")
        self._add_enhanced_thing(1, thing1)
        self._add_enhanced_thing(1, thing2)
        
        thing3 = EnhancedThing(content="参加部门会议", time=[10, 0], deadline=False, reminder_method="两者")
        self._add_enhanced_thing(5, thing3)
        
        thing4 = EnhancedThing(content="提交年度总结", time=[], deadline=True,
                               reminder_days=[-5, -3, -1], reminder_method="弹窗")
        thing5 = EnhancedThing(content="健身", time=[18, 0], deadline=False, reminder_method="语音")
        self._add_enhanced_thing(15, thing4)
        self._add_enhanced_thing(15, thing5)
        
        thing6 = EnhancedThing(content="朋友聚会", time=[19, 0], deadline=False, reminder_method="弹窗")
        self._add_enhanced_thing(25, thing6)
        
        thing7 = EnhancedThing(content="写周报", time=[16, 0], deadline=False, reminder_method="两者")
        self._add_enhanced_thing(20, thing7)
        
        # 刷新显示
        self.refresh_all()
    
    def _add_enhanced_thing(self, day_number, thing):
        """添加增强版事项"""
        self.month.days[day_number - 1].everything.append(thing)
        print(f"已在第{day_number}天添加事项: {thing.content} (提醒方式: {thing.reminder_method})")
    
    def _enhanced_add_thing(self, day_number, thing):
        """增强的添加事项方法"""
        if not isinstance(thing, EnhancedThing):
            # 转换普通Thing为EnhancedThing
            enhanced_thing = EnhancedThing(
                content=thing.content,
                time=thing.time,
                deadline=thing.deadline,
                reminder_days=[-3, -2, -1] if thing.deadline else []
            )
            self.month.days[day_number - 1].everything.append(enhanced_thing)
        else:
            self.month.days[day_number - 1].everything.append(thing)
        print(f"已在第{day_number}天添加事项: {thing.content}")
    
    def parse_reminder_command(self, user_input):
        """解析提醒修改命令"""
        result = {
            "action": None,
            "date": None,
            "content": None,
            "reminder_method": None,
            "reminder_days": None
        }
        
        # 提取日期
        date_match = re.search(r'(\d+)(?:号|日)', user_input)
        if date_match:
            result["date"] = int(date_match.group(1))
        
        # 1. 修改提醒方式
        method_match = re.search(r'(\d+号)?的?[\s]*(.+?)(?:改成|修改为|设置成|改为)\s*(弹窗|语音|两者)', user_input)
        if method_match:
            content = method_match.group(2).strip()
            # 清理内容
            for word in ["把", "将", "提醒", "方式"]:
                content = content.replace(word, "")
            result["content"] = content.strip()
            result["reminder_method"] = method_match.group(3)
            result["action"] = "update_method"
            return result
        
        # 2. 设置提前提醒天数
        days_match = re.search(r'(\d+号)?的?[\s]*(.+?)(?:提前|提前\s*(\d+)\s*天)', user_input)
        if days_match:
            days = int(days_match.group(3)) if days_match.group(3) else 1
            content = days_match.group(2).strip()
            for word in ["设置", "调整", "提醒"]:
                content = content.replace(word, "")
            result["content"] = content.strip()
            result["reminder_days"] = [-days, -(days-1), -1] if days > 1 else [-days]
            result["action"] = "update_days"
            return result
        
        # 3. 取消提醒
        if "取消" in user_input and ("提醒" in user_input or "提前" in user_input):
            cancel_match = re.search(r'(\d+号)?的?[\s]*(.+?)(?:的)?(?:提醒|提前提醒)', user_input)
            if cancel_match:
                content = cancel_match.group(2).strip()
                for word in ["取消", "删除", "移除"]:
                    content = content.replace(word, "")
                result["content"] = content.strip()
                result["reminder_days"] = []
                result["action"] = "update_days"
                return result
        
        return result
    
    def update_thing_reminder(self, date, content_keyword, method=None, days=None):
        """更新事项的提醒设置"""
        day = self.month.get_day(date)
        if not day:
            return False, f"第{date}天不存在"
        
        found_things = []
        for thing in day.everything:
            if content_keyword and (content_keyword in thing.content or thing.content in content_keyword):
                found_things.append(thing)
        
        if not found_things:
            return False, f"未找到包含'{content_keyword}'的事项"
        
        if len(found_things) > 1:
            return False, f"找到多个匹配事项，请指定更具体的内容"
        
        thing = found_things[0]
        
        if method:
            if hasattr(thing, 'update_reminder_method'):
                thing.update_reminder_method(method)
                self.update_day_display(date)
                return True, f"已将'{thing.content}'的提醒方式改为'{method}'"
            else:
                return False, f"该事项不支持修改提醒方式"
        
        if days is not None:
            if hasattr(thing, 'update_reminder_days'):
                thing.update_reminder_days(days)
                self.update_day_display(date)
                if days:
                    return True, f"已将'{thing.content}'设置为提前{abs(days[0])}天提醒"
                else:
                    return True, f"已取消'{thing.content}'的提前提醒"
            else:
                return False, f"该事项不支持修改提前提醒"
        
        return False, "未指定修改内容"
    
    def _parse_and_execute(self, user_input):
        """重写命令解析方法，添加提醒命令处理"""
        # 先检查是否是提醒修改命令
        reminder_cmd = self.parse_reminder_command(user_input)
        
        if reminder_cmd["action"] in ["update_method", "update_days"] and reminder_cmd["date"] and reminder_cmd["content"]:
            success, msg = self.update_thing_reminder(
                reminder_cmd["date"],
                reminder_cmd["content"],
                reminder_cmd["reminder_method"],
                reminder_cmd["reminder_days"]
            )
            self.root.after(0, lambda: self._show_reminder_result(success, msg))
            return
        
        # 否则使用父类的命令解析
        command = parse_calendar_command(user_input)
        self.root.after(0, lambda: self.execute_command(command, user_input))
    
    def _show_reminder_result(self, success, message):
        """显示提醒操作结果"""
        if success:
            messagebox.showinfo("成功", message)
        else:
            messagebox.showwarning("提示", message)
        self.update_status(message)
    
    def update_day_display(self, day_num):
        """重写更新显示方法，添加提醒图标"""
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
            
            # 显示事项列表和提醒图标
            if day and day.everything:
                text_area.insert(tk.END, "📝\n", 'list_title')
                for thing in day.everything[:3]:
                    # 获取提醒图标
                    reminder_icon = ""
                    if hasattr(thing, 'reminder_method'):
                        if thing.reminder_method == "语音":
                            reminder_icon = "🎤"
                        elif thing.reminder_method == "弹窗":
                            reminder_icon = "💬"
                        elif thing.reminder_method == "两者":
                            reminder_icon = "🎤💬"
                    
                    icon = "🔴" if thing.deadline else "🟢"
                    text_area.insert(tk.END, f"{icon}{reminder_icon}{thing.content[:10]}\n", 'list_item')
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
    
    def open_add_dialog(self, default_day=None):
        """重写添加对话框，添加提醒方式选择"""
        dialog = tk.Toplevel(self.root)
        dialog.title("添加待办事项")
        dialog.geometry("450x500")
        
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
        ttk.Checkbutton(dialog, text="截止日期", variable=deadline_var).pack(pady=5)
        
        # 提醒方式选择
        ttk.Label(dialog, text="提醒方式:", font=("Arial", 10)).pack(pady=5)
        method_var = tk.StringVar(value="弹窗")
        method_frame = ttk.Frame(dialog)
        method_frame.pack()
        ttk.Radiobutton(method_frame, text="弹窗", variable=method_var, value="弹窗").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(method_frame, text="语音", variable=method_var, value="语音").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(method_frame, text="两者", variable=method_var, value="两者").pack(side=tk.LEFT, padx=10)
        
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
                
                # 使用增强版Thing
                reminder_days = [-3, -2, -1] if deadline_var.get() else []
                thing = EnhancedThing(content=content, time=time_list, deadline=deadline_var.get(),
                                     reminder_days=reminder_days, reminder_method=method_var.get())
                self.month.add_thing(day_num, thing)
                self.update_day_display(day_num)
                dialog.destroy()
                messagebox.showinfo("成功", f"已添加事项到第{day_num}天\n提醒方式: {method_var.get()}")
            except Exception as e:
                messagebox.showerror("错误", f"输入无效: {str(e)}")
        
        ttk.Button(dialog, text="添加", command=add_thing).pack(pady=20)
        ttk.Button(dialog, text="取消", command=dialog.destroy).pack()
    
    def quick_add_thing(self, day_num):
        """重写快速添加，添加提醒方式选择"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"快速添加 - 第{day_num}天")
        dialog.geometry("400x380")
        
        ttk.Label(dialog, text=f"第{day_num}天", font=("Arial", 12, "bold")).pack(pady=10)
        
        ttk.Label(dialog, text="事项:").pack(pady=5)
        content_entry = ttk.Entry(dialog, width=40)
        content_entry.pack(pady=5)
        
        deadline_var = tk.BooleanVar()
        ttk.Checkbutton(dialog, text="截止日期", variable=deadline_var).pack(pady=5)
        
        ttk.Label(dialog, text="提醒方式:").pack(pady=5)
        method_var = tk.StringVar(value="弹窗")
        method_frame = ttk.Frame(dialog)
        method_frame.pack()
        ttk.Radiobutton(method_frame, text="弹窗", variable=method_var, value="弹窗").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(method_frame, text="语音", variable=method_var, value="语音").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(method_frame, text="两者", variable=method_var, value="两者").pack(side=tk.LEFT, padx=10)
        
        def add():
            content = content_entry.get()
            if content:
                reminder_days = [-3, -2, -1] if deadline_var.get() else []
                thing = EnhancedThing(content=content, time=[], deadline=deadline_var.get(),
                                     reminder_days=reminder_days, reminder_method=method_var.get())
                self.month.add_thing(day_num, thing)
                self.update_day_display(day_num)
                dialog.destroy()
                self.update_status(f"已添加事项: {content} (提醒: {method_var.get()})")
        
        ttk.Button(dialog, text="添加", command=add).pack(pady=20)
        ttk.Button(dialog, text="取消", command=dialog.destroy).pack()
    
    def open_day_detail(self, day_num):
        """重写详细视图，显示提醒信息"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"第{day_num}天 - 详细待办事项（含提醒信息）")
        dialog.geometry("650x600")
        
        day = self.month.get_day(day_num)
        
        tk.Label(dialog, text=f"第{day_num}天", font=("Arial", 16, "bold")).pack(pady=10)
        
        if day and day.everything:
            # 创建带滚动条的文本框
            frame = tk.Frame(dialog)
            frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            scrollbar = tk.Scrollbar(frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            text_widget = tk.Text(frame, yscrollcommand=scrollbar.set, font=("Arial", 10), height=12)
            text_widget.pack(fill=tk.BOTH, expand=True)
            scrollbar.config(command=text_widget.yview)
            
            for i, thing in enumerate(day.everything):
                time_str = f"{thing.time[0]}:{thing.time[1]:02d}" if thing.time else "无时间"
                deadline_str = "🔴 截止日期" if thing.deadline else "🟢 普通事项"
                
                # 获取提醒信息
                if hasattr(thing, 'get_reminder_type'):
                    reminder_type = thing.get_reminder_type()
                    reminder_method = thing.reminder_method
                    reminder_days_str = f"提前{abs(thing.reminder_days[0])}天" if thing.reminder_days else "无"
                else:
                    reminder_type = "普通"
                    reminder_method = "默认"
                    reminder_days_str = "无"
                
                text_widget.insert(tk.END, f"{i+1}. {thing.content}\n", "bold")
                text_widget.insert(tk.END, f"   时间: {time_str} | 类型: {deadline_str}\n")
                text_widget.insert(tk.END, f"   提醒类型: {reminder_type} | 方式: {reminder_method} | 提前: {reminder_days_str}\n")
                text_widget.insert(tk.END, "-" * 50 + "\n")
            
            text_widget.tag_config("bold", font=("Arial", 11, "bold"))
            text_widget.config(state=tk.DISABLED)
            
            # 显示working输出
            tk.Label(dialog, text="📢 今日提醒信息:", font=("Arial", 12, "bold")).pack(pady=5)
            output_text = tk.Text(dialog, wrap=tk.WORD, height=8, font=("Arial", 10))
            output_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            output = self.get_working_output(day_num)
            output_text.insert(1.0, output)
            output_text.config(state=tk.DISABLED)
            
            # 按钮
            button_frame = ttk.Frame(dialog)
            button_frame.pack(pady=10)
            
            def edit_reminder():
                # 创建编辑对话框
                edit_dialog = tk.Toplevel(dialog)
                edit_dialog.title("选择要修改的事项")
                edit_dialog.geometry("400x300")
                
                tk.Label(edit_dialog, text="选择要修改提醒的事项:", font=("Arial", 12)).pack(pady=10)
                
                listbox = tk.Listbox(edit_dialog, font=("Arial", 11), height=8)
                listbox.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
                
                thing_list = []
                for i, thing in enumerate(day.everything):
                    listbox.insert(tk.END, f"{i+1}. {thing.content}")
                    thing_list.append(thing)
                
                def select_thing():
                    selection = listbox.curselection()
                    if selection:
                        thing = thing_list[selection[0]]
                        edit_dialog.destroy()
                        self._edit_reminder_settings(day_num, thing, dialog)
                
                ttk.Button(edit_dialog, text="选择", command=select_thing).pack(pady=10)
            
            ttk.Button(button_frame, text="⚙️ 修改提醒设置", command=edit_reminder).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="关闭", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        else:
            tk.Label(dialog, text="暂无事项", font=("Arial", 12)).pack(pady=50)
            ttk.Button(dialog, text="关闭", command=dialog.destroy).pack(pady=10)
    
    def _edit_reminder_settings(self, day_num, thing, parent_dialog):
        """编辑单个事项的提醒设置"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"修改提醒设置 - {thing.content}")
        dialog.geometry("400x400")
        dialog.transient(parent_dialog)
        
        tk.Label(dialog, text=f"事项: {thing.content}", font=("Arial", 12, "bold")).pack(pady=10)
        
        # 提醒方式
        tk.Label(dialog, text="提醒方式:", font=("Arial", 10)).pack(pady=5)
        method_var = tk.StringVar(value=thing.reminder_method if hasattr(thing, 'reminder_method') else "弹窗")
        method_frame = ttk.Frame(dialog)
        method_frame.pack()
        ttk.Radiobutton(method_frame, text="弹窗", variable=method_var, value="弹窗").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(method_frame, text="语音", variable=method_var, value="语音").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(method_frame, text="两者", variable=method_var, value="两者").pack(side=tk.LEFT, padx=10)
        
        # 提前提醒天数（仅截止事项）
        if thing.deadline:
            tk.Label(dialog, text="提前提醒天数:", font=("Arial", 10)).pack(pady=5)
            days_var = tk.StringVar(value=str(abs(thing.reminder_days[0])) if hasattr(thing, 'reminder_days') and thing.reminder_days else "0")
            days_entry = ttk.Entry(dialog, width=10, textvariable=days_var)
            days_entry.pack(pady=5)
            tk.Label(dialog, text="(输入0表示不提前提醒)", font=("Arial", 8), fg="gray").pack()
        
        def save():
            # 更新提醒方式
            if hasattr(thing, 'update_reminder_method'):
                thing.update_reminder_method(method_var.get())
            
            # 更新提前提醒天数
            if thing.deadline and hasattr(thing, 'update_reminder_days'):
                try:
                    days = int(days_var.get())
                    if days > 0:
                        thing.update_reminder_days([-days, -(days-1), -1] if days > 1 else [-days])
                    else:
                        thing.update_reminder_days([])
                except:
                    pass
            
            self.update_day_display(day_num)
            messagebox.showinfo("成功", "提醒设置已更新")
            dialog.destroy()
            parent_dialog.destroy()
            self.open_day_detail(day_num)
        
        ttk.Button(dialog, text="保存", command=save).pack(pady=20)
        ttk.Button(dialog, text="取消", command=dialog.destroy).pack()
    
    def view_all_things(self):
        """重写查看所有事项，显示提醒信息"""
        dialog = tk.Toplevel(self.root)
        dialog.title("所有事项（含提醒信息）")
        dialog.geometry("750x650")
        
        text_area = tk.Text(dialog, wrap=tk.WORD)
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        info = f"{'='*70}\n"
        info += f"{self.month.month}月 所有事项及提醒设置\n"
        info += f"{'='*70}\n\n"
        info += f"总数: {self.month.get_total_things_count()}\n\n"
        
        for day_num in range(1, 31):
            day = self.month.get_day(day_num)
            if day and day.everything:
                info += f"\n{'─'*70}\n"
                info += f"📅 第{day_num}天 (共{len(day.everything)}项)\n"
                info += f"{'─'*70}\n"
                for i, thing in enumerate(day.everything):
                    time_str = f"{thing.time[0]}:{thing.time[1]:02d}" if thing.time else "无时间"
                    deadline_str = "截止日期" if thing.deadline else "普通"
                    
                    if hasattr(thing, 'get_reminder_type'):
                        reminder_type = thing.get_reminder_type()
                        reminder_method = thing.reminder_method
                        reminder_days = f"提前{abs(thing.reminder_days[0])}天" if thing.reminder_days else "无"
                    else:
                        reminder_type = "普通"
                        reminder_method = "默认"
                        reminder_days = "无"
                    
                    info += f"  {i+1}. {thing.content}\n"
                    info += f"      ⏰ 时间: {time_str} | 类型: {deadline_str}\n"
                    info += f"      🔔 提醒: {reminder_type} | 方式: {reminder_method} | 提前: {reminder_days}\n"
        
        text_area.insert(1.0, info)
        text_area.config(state=tk.DISABLED)
        
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=text_area.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_area.configure(yscrollcommand=scrollbar.set)
        
        ttk.Button(dialog, text="关闭", command=dialog.destroy).pack(pady=10)


def main():
    root = tk.Tk()
    app = VoiceCalendarWithReminder(root)
    root.mainloop()


if __name__ == "__main__":
    main()