"""
增强版日历 - 添加提醒功能（不修改原文件）
通过继承扩展 Thing 类
"""

import tkinter as tk
from tkinter import ttk, messagebox
from data_stracture import Month, Thing, Day
from voice_calendar import VoiceCalendarGUI, VoiceRecognizer
import sys
from io import StringIO
import threading
import re


class EnhancedThing(Thing):
    """扩展的Thing类，添加提醒功能"""
    
    def __init__(self, content=None, time=None, deadline=False, reminder_method="弹窗", reminder_days=None):
        super().__init__(content, time, deadline)
        self._reminder_method = reminder_method
        self._reminder_days = reminder_days if reminder_days is not None else ([-3, -2, -1] if deadline else [])
    
    @property
    def reminder_method(self):
        return self._reminder_method
    
    @property
    def reminder_days(self):
        return self._reminder_days
    
    def get_reminder_method(self):
        return self._reminder_method
    
    def get_reminder_days(self):
        return self._reminder_days
    
    def get_reminder_type(self):
        """获取提醒类型"""
        has_time = bool(self.time)
        if self.deadline and has_time:
            return "定时+截止"
        elif self.deadline:
            return "截止提醒"
        elif has_time:
            return "定时提醒"
        else:
            return "无提醒"
    
    def update_reminder(self, method=None, days=None):
        """更新提醒设置"""
        if method and method in ["弹窗", "语音", "两者", "无"]:
            self._reminder_method = method
        if days is not None:
            self._reminder_days = days
        return True


class EnhancedVoiceCalendar(VoiceCalendarGUI):
    """增强版语音日历，支持提醒设置"""
    
    def __init__(self, root):
        # 先保存原始方法
        self.original_add_thing = None
        
        # 初始化父类
        super().__init__(root)
        
        # 替换添加方法
        self.original_add_thing = self.month.add_thing
        self.month.add_thing = self._enhanced_add_thing
        
        # 重新加载示例数据（使用增强版）
        self._reload_enhanced_sample_data()
        
        # 添加提醒设置对话框
        self._add_reminder_ui()
    
    def _enhanced_add_thing(self, day_number, thing):
        """增强的添加方法，自动转换普通Thing为EnhancedThing"""
        if not isinstance(thing, EnhancedThing):
            enhanced_thing = EnhancedThing(
                content=thing.content,
                time=thing.time,
                deadline=thing.deadline
            )
            self.month.days[day_number - 1].everything.append(enhanced_thing)
        else:
            self.month.days[day_number - 1].everything.append(thing)
        print(f"已在第{day_number}天添加事项: {thing.content}")
    
    def _reload_enhanced_sample_data(self):
        """重新加载示例数据"""
        # 清空现有数据
        for day in self.month.days:
            day.everything.clear()
        
        # 添加增强版示例数据
        thing1 = EnhancedThing(content="完成项目报告", time=[], deadline=True, 
                               reminder_method="弹窗", reminder_days=[-3, -2, -1])
        thing2 = EnhancedThing(content="买水果", time=[], deadline=False, reminder_method="语音")
        self.month.add_things(1, [thing1, thing2])
        
        thing3 = EnhancedThing(content="参加部门会议", time=[10, 0], deadline=False, reminder_method="两者")
        self.month.add_thing(5, thing3)
        
        thing4 = EnhancedThing(content="提交年度总结", time=[], deadline=True,
                               reminder_method="弹窗", reminder_days=[-5, -3, -1])
        thing5 = EnhancedThing(content="健身", time=[18, 0], deadline=False, reminder_method="语音")
        self.month.add_things(15, [thing4, thing5])
        
        thing6 = EnhancedThing(content="朋友聚会", time=[19, 0], deadline=False, reminder_method="弹窗")
        self.month.add_thing(25, thing6)
        
        thing7 = EnhancedThing(content="写周报", time=[16, 0], deadline=False, reminder_method="两者")
        self.month.add_thing(20, thing7)
        
        self.refresh_all()
    
    def _add_reminder_ui(self):
        """在控制按钮区域添加提醒设置按钮"""
        # 找到控制按钮框架
        for child in self.main_frame.winfo_children():
            if isinstance(child, ttk.Frame):
                for sub in child.winfo_children():
                    if isinstance(sub, ttk.Frame):
                        # 在清空全部按钮旁边添加提醒设置按钮
                        ttk.Button(sub, text="🔔 提醒设置", command=self.open_reminder_settings, 
                                  width=10).pack(side=tk.LEFT, padx=5)
                        break
                break
    
    def open_reminder_settings(self):
        """打开全局提醒设置对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("提醒设置")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        
        tk.Label(dialog, text="提醒设置", font=("Arial", 16, "bold")).pack(pady=10)
        
        # 选择日期
        tk.Label(dialog, text="选择日期 (1-30):").pack(pady=5)
        day_frame = ttk.Frame(dialog)
        day_frame.pack()
        day_spinbox = ttk.Spinbox(day_frame, from_=1, to=30, width=5)
        day_spinbox.pack(side=tk.LEFT, padx=5)
        
        # 刷新显示当前事项
        def refresh_thing_list():
            try:
                day_num = int(day_spinbox.get())
                day = self.month.get_day(day_num)
                thing_listbox.delete(0, tk.END)
                if day and day.everything:
                    for i, thing in enumerate(day.everything):
                        reminder_info = ""
                        if hasattr(thing, 'get_reminder_method'):
                            reminder_info = f" [{thing.get_reminder_method()}]"
                        thing_listbox.insert(tk.END, f"{i+1}. {thing.content}{reminder_info}")
                else:
                    thing_listbox.insert(tk.END, "暂无事项")
            except:
                pass
        
        tk.Label(dialog, text="选择事项:").pack(pady=5)
        thing_listbox = tk.Listbox(dialog, height=6, font=("Arial", 10))
        thing_listbox.pack(fill=tk.X, padx=20, pady=5)
        
        ttk.Button(dialog, text="刷新列表", command=refresh_thing_list).pack(pady=5)
        
        # 提醒方式选择
        tk.Label(dialog, text="提醒方式:", font=("Arial", 10, "bold")).pack(pady=5)
        method_frame = ttk.Frame(dialog)
        method_frame.pack()
        method_var = tk.StringVar(value="弹窗")
        ttk.Radiobutton(method_frame, text="弹窗 💬", variable=method_var, value="弹窗").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(method_frame, text="语音 🎤", variable=method_var, value="语音").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(method_frame, text="两者 🎤💬", variable=method_var, value="两者").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(method_frame, text="无 ❌", variable=method_var, value="无").pack(side=tk.LEFT, padx=10)
        
        # 提前提醒天数（仅截止事项）
        tk.Label(dialog, text="提前提醒天数 (截止事项):", font=("Arial", 10, "bold")).pack(pady=5)
        days_frame = ttk.Frame(dialog)
        days_frame.pack()
        days_var = tk.StringVar(value="3")
        ttk.Radiobutton(days_frame, text="不提前", variable=days_var, value="0").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(days_frame, text="提前1天", variable=days_var, value="1").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(days_frame, text="提前3天", variable=days_var, value="3").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(days_frame, text="提前5天", variable=days_var, value="5").pack(side=tk.LEFT, padx=5)
        
        def apply_settings():
            try:
                day_num = int(day_spinbox.get())
                selection = thing_listbox.curselection()
                if not selection:
                    messagebox.showwarning("提示", "请先选择要设置的事项")
                    return
                
                day = self.month.get_day(day_num)
                if not day or selection[0] >= len(day.everything):
                    messagebox.showwarning("提示", "请刷新列表后重新选择")
                    return
                
                thing = day.everything[selection[0]]
                if hasattr(thing, 'update_reminder'):
                    # 计算提醒天数列表
                    days = int(days_var.get())
                    if days > 0:
                        reminder_days = [-days, -(days-1), -1] if days > 1 else [-days]
                    else:
                        reminder_days = []
                    
                    thing.update_reminder(method=method_var.get(), days=reminder_days)
                    self.update_day_display(day_num)
                    messagebox.showinfo("成功", f"已更新「{thing.content}」的提醒设置\n提醒方式: {method_var.get()}\n提前提醒: {days}天")
                    refresh_thing_list()
            except Exception as e:
                messagebox.showerror("错误", str(e))
        
        ttk.Button(dialog, text="应用设置", command=apply_settings).pack(pady=10)
        ttk.Button(dialog, text="关闭", command=dialog.destroy).pack(pady=5)
        
        # 初始刷新
        refresh_thing_list()
    
    def open_day_detail(self, day_num):
        """重写详细视图，显示提醒信息"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"第{day_num}天 - 详情及提醒设置")
        dialog.geometry("600x550")
        
        day = self.month.get_day(day_num)
        
        tk.Label(dialog, text=f"第{day_num}天", font=("Arial", 16, "bold")).pack(pady=10)
        
        if day and day.everything:
            # 事项列表
            listbox = tk.Listbox(dialog, font=("Arial", 11), height=6)
            listbox.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            
            thing_list = []
            for i, thing in enumerate(day.everything):
                time_str = f"{thing.time[0]}:{thing.time[1]:02d}" if thing.time else "无时间"
                deadline_str = "🔴截止" if thing.deadline else "🟢普通"
                # 获取提醒信息
                if hasattr(thing, 'get_reminder_method'):
                    reminder_str = f"提醒:{thing.get_reminder_method()}"
                else:
                    reminder_str = ""
                listbox.insert(tk.END, f"{i+1}. {thing.content} [{time_str}] {deadline_str} {reminder_str}")
                thing_list.append(thing)
            
            # 提醒信息显示
            tk.Label(dialog, text="📢 提醒信息:", font=("Arial", 12, "bold")).pack(pady=5)
            output_text = tk.Text(dialog, wrap=tk.WORD, height=8, font=("Arial", 10))
            output_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
            
            output = self.get_working_output(day_num)
            output_text.insert(1.0, output)
            output_text.config(state=tk.DISABLED)
            
            # 按钮框架
            button_frame = ttk.Frame(dialog)
            button_frame.pack(pady=10)
            
            def edit_reminder():
                selection = listbox.curselection()
                if selection and selection[0] < len(thing_list):
                    self._edit_single_reminder(day_num, selection[0], thing_list[selection[0]], dialog)
                else:
                    messagebox.showwarning("提示", "请先选择要设置的事项")
            
            def delete_selected():
                selection = listbox.curselection()
                if selection:
                    if messagebox.askyesno("确认", "确定要删除这个事项吗？"):
                        del day.everything[selection[0]]
                        self.update_day_display(day_num)
                        dialog.destroy()
                        self.open_day_detail(day_num)
            
            ttk.Button(button_frame, text="⚙️ 设置提醒", command=edit_reminder).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="🗑️ 删除", command=delete_selected).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="关闭", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        else:
            tk.Label(dialog, text="暂无事项", font=("Arial", 12)).pack(pady=50)
            ttk.Button(dialog, text="关闭", command=dialog.destroy).pack(pady=10)
    
    def _edit_single_reminder(self, day_num, index, thing, parent_dialog):
        """编辑单个事项的提醒设置"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"提醒设置 - {thing.content}")
        dialog.geometry("400x350")
        dialog.transient(parent_dialog)
        
        tk.Label(dialog, text=f"事项: {thing.content}", font=("Arial", 12, "bold")).pack(pady=10)
        
        # 当前提醒信息
        if hasattr(thing, 'get_reminder_method'):
            current_method = thing.get_reminder_method()
            current_days = abs(thing.reminder_days[0]) if thing.reminder_days else 0
        else:
            current_method = "无"
            current_days = 0
        
        tk.Label(dialog, text=f"当前提醒方式: {current_method}", font=("Arial", 10)).pack()
        tk.Label(dialog, text=f"当前提前提醒: {current_days}天", font=("Arial", 10)).pack(pady=5)
        
        tk.Label(dialog, text="-" * 30).pack(pady=5)
        
        # 提醒方式选择
        tk.Label(dialog, text="新提醒方式:", font=("Arial", 10, "bold")).pack(pady=5)
        method_var = tk.StringVar(value=current_method if current_method != "无" else "弹窗")
        method_frame = ttk.Frame(dialog)
        method_frame.pack()
        ttk.Radiobutton(method_frame, text="弹窗 💬", variable=method_var, value="弹窗").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(method_frame, text="语音 🎤", variable=method_var, value="语音").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(method_frame, text="两者 🎤💬", variable=method_var, value="两者").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(method_frame, text="无 ❌", variable=method_var, value="无").pack(side=tk.LEFT, padx=5)
        
        # 提前提醒天数（仅截止事项）
        if thing.deadline:
            tk.Label(dialog, text="提前提醒天数:", font=("Arial", 10, "bold")).pack(pady=5)
            days_var = tk.StringVar(value=str(current_days))
            days_frame = ttk.Frame(dialog)
            days_frame.pack()
            ttk.Radiobutton(days_frame, text="不提前", variable=days_var, value="0").pack(side=tk.LEFT, padx=5)
            ttk.Radiobutton(days_frame, text="提前1天", variable=days_var, value="1").pack(side=tk.LEFT, padx=5)
            ttk.Radiobutton(days_frame, text="提前3天", variable=days_var, value="3").pack(side=tk.LEFT, padx=5)
            ttk.Radiobutton(days_frame, text="提前5天", variable=days_var, value="5").pack(side=tk.LEFT, padx=5)
        
        def save():
            if hasattr(thing, 'update_reminder'):
                # 计算提醒天数列表
                if thing.deadline:
                    days = int(days_var.get())
                    if days > 0:
                        reminder_days = [-days, -(days-1), -1] if days > 1 else [-days]
                    else:
                        reminder_days = []
                else:
                    reminder_days = thing.reminder_days if hasattr(thing, 'reminder_days') else []
                
                thing.update_reminder(method=method_var.get(), days=reminder_days)
                self.update_day_display(day_num)
                messagebox.showinfo("成功", f"已更新「{thing.content}」的提醒设置")
                dialog.destroy()
                parent_dialog.destroy()
                self.open_day_detail(day_num)
        
        ttk.Button(dialog, text="保存", command=save).pack(pady=20)
        ttk.Button(dialog, text="取消", command=dialog.destroy).pack()
    
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
        ttk.Label(dialog, text="提醒方式:", font=("Arial", 10, "bold")).pack(pady=5)
        method_var = tk.StringVar(value="弹窗")
        method_frame = ttk.Frame(dialog)
        method_frame.pack()
        ttk.Radiobutton(method_frame, text="弹窗 💬", variable=method_var, value="弹窗").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(method_frame, text="语音 🎤", variable=method_var, value="语音").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(method_frame, text="两者 🎤💬", variable=method_var, value="两者").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(method_frame, text="无 ❌", variable=method_var, value="无").pack(side=tk.LEFT, padx=5)
        
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
                thing = EnhancedThing(
                    content=content, 
                    time=time_list, 
                    deadline=deadline_var.get(),
                    reminder_method=method_var.get(),
                    reminder_days=reminder_days
                )
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
        ttk.Radiobutton(method_frame, text="弹窗 💬", variable=method_var, value="弹窗").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(method_frame, text="语音 🎤", variable=method_var, value="语音").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(method_frame, text="两者 🎤💬", variable=method_var, value="两者").pack(side=tk.LEFT, padx=5)
        
        def add():
            content = content_entry.get()
            if content:
                reminder_days = [-3, -2, -1] if deadline_var.get() else []
                thing = EnhancedThing(
                    content=content, 
                    time=[], 
                    deadline=deadline_var.get(),
                    reminder_method=method_var.get(),
                    reminder_days=reminder_days
                )
                self.month.add_thing(day_num, thing)
                self.update_day_display(day_num)
                dialog.destroy()
                self.update_status(f"已添加事项: {content} (提醒: {method_var.get()})")
        
        ttk.Button(dialog, text="添加", command=add).pack(pady=20)
        ttk.Button(dialog, text="取消", command=dialog.destroy).pack()


def main():
    root = tk.Tk()
    app = EnhancedVoiceCalendar(root)
    root.mainloop()


if __name__ == "__main__":
    main()