class Thing:
    def __init__(self, content=None, time=None, deadline=False):
        """
        初始化Thing类
        :param content: str类型，默认为None，事件内容
        :param time: list类型，默认为None，如需闹铃这一项为具体时间，如[14,0]表示14点0分
        :param deadline: bool类型，默认为False，是否为deadline
        """
        self.content = content
        self.time = time if time is not None else []
        self.deadline = deadline
    
    def get_content(self):
        """查看content的值"""
        return self.content
    
    def get_time(self):
        """查看time的值"""
        return None if self.time==[] else self.time[0],self.time[1]
    
    def get_deadline(self):
        """查看deadline的值"""
        return self.deadline
    
class Day:
    def __init__(self, date=None, everything=None):
        """
        初始化Day类
        :param date: int类型，默认为None
        :param everything: list类型，包含Thing对象，默认为None
        """
        self.date = date if date is not None else []
        self.everything = everything if everything is not None else []
    
    def get_date(self):
        """查看date的值"""
        return self.date
    
    def get_everything(self):
        """查看everything的值"""
        return len(self.everything), self.everything
    
    def add_thing(self, thing):
        """添加一个Thing对象到everything中"""
        if isinstance(thing, Thing):
            self.everything.append(thing)
        else:
            print("只能添加Thing对象")

    def get_all_info(self):
        """查看所有变量的详细信息"""
        info = f"日期: {self.date}\n"
        info += f"待办事项数量: {len(self.everything)}\n"
        for i, thing in enumerate(self.everything):
            info += f"  事项{i+1}: 内容={thing.content}, 时间={thing.time}, 截止日期={thing.deadline}\n"
        return info
    
    def remind(self):#可视化时要重写这个函数，对无dealine的提醒,分为有无定时提醒
        """提醒功能：对everything中的每个thing进行处理"""
        for thing in self.everything:
            if thing.deadline:
                # deadline为True时，什么都不干
                continue
            else:
                # deadline为False时
                if not thing.time:  # time为空
                    print(f"提醒: {thing.content}")
                else:  # time不为空
                    print(f"在{thing.time[0]}时{thing.time[1]}分提醒{thing.content}")
    
    def deadline_remind(self):#对dealine的提醒，可视化时与remind函数合并
        """截止日期提醒功能：对deadline为True的thing进行提醒"""
        print("=== 截止日期提醒 ===")
        for thing in self.everything:
            if not thing.deadline:
                # deadline为False时，什么都不干
                continue
            else:
                # deadline为True时，输出日期-3、-2、-1的提醒
                print(f"在{self.date-3}日{self.date-2}日{self.date-1}日提醒{thing.content}")

    def working(self):
        """工作功能：对everything中的每个thing进行处理，处理完后从everything中删除"""
        self.remind()
        self.deadline_remind()

class Month:
    def __init__(self,  month=None):
        """
        初始化Month类:
        param month: 月份，如1
        创建一个包含30个Day对象的列表，date分别为1-30
        """
        self.month = month
        self.days = []
        
        # 初始化30个Day对象，date为1-30
        for day_num in range(1, 31):
            day = Day(date=day_num, everything=[])
            self.days.append(day)
    
    def get_day(self, day_number):
        """
        获取指定日期的Day对象
        :param day_number: 日期(1-30)
        :return: Day对象或None
        """
        if 1 <= day_number <= 30:
            return self.days[day_number - 1]
        else:
            print(f"错误：日期必须在1-30之间，输入的是{day_number}")
            return None
    
    def add_thing(self, day_number, thing):
        """
        在某一天添加一个Thing对象
        :param day_number: 日期(1-30)
        :param thing: Thing对象
        """
        self.days[day_number-1].everything.append(thing)
        print(f"已在第{day_number}天添加事项: {thing.content}")
    
    def add_things(self, day_number, things):
        """
        在某一天添加多个Thing对象
        :param day_number: 日期(1-30)
        :param things: Thing对象列表
        """
        for thing in things:
            self.add_thing(day_number, thing)
    def view_day(self, day_number):
        """
        查看某一天的所有事项
        :param day_number: 日期(1-30)
        """
        day = self.get_day(day_number)
        if day:
            print(day.get_all_info())
    
    def view_all_days(self):
        """查看所有30天的事项概览"""
        print(f"=== {self.month}月 事项概览 ===")
        for i, day in enumerate(self.days):
            day_num = i + 1
            thing_count = len(day.everything)
            if thing_count > 0:
                print(f"第{day_num}天: {thing_count}个事项")
                for j, thing in enumerate(day.everything):
                    print(f"  - {thing.content}")
    
    def view_days_with_things(self):
        """只查看有事项的天数"""
        print(f"=== 有事项的日期 ===")
        has_things = False
        for i, day in enumerate(self.days):
            if day.everything:
                has_things = True
                day_num = i + 1
                print(f"\n第{day_num}天:")
                print(day.get_all_info())
        
        if not has_things:
            print("本月暂无任何事项")
    
    def get_total_things_count(self):
        """获取本月总事项数"""
        total = sum(len(day.everything) for day in self.days)
        return total
    
    def working_day(self, day_number):
        """对某一天进行提醒"""
        day = self.get_day(day_number)
        if day:
            day.working()
    
    def working_all_days(self):
        """对所有天进行提醒"""
        for i, day in enumerate(self.days):
            if day.everything:
                day.working()
    
    

# 使用示例
if __name__ == "__main__":
    # 创建一个月对象
    month = Month( month=1)
    
    # 在第1天添加事项
    thing1 = Thing(content="完成项目报告", time=[], deadline=True)
    thing2 = Thing(content="买水果", time=[], deadline=False)
    month.add_things(1, [thing1, thing2])
    
    # 在第5天添加事项
    thing3 = Thing(content="参加部门会议", time=[10,0], deadline=False)
    month.add_thing(5, thing3)
    
    # 在第15天添加事项
    thing4 = Thing(content="提交年度总结", time=[], deadline=True)
    thing5 = Thing(content="健身", time=[18,0], deadline=False)
    month.add_things(15, [thing4, thing5])
    
    # 在第25天添加事项
    thing6 = Thing(content="朋友聚会", time=[19,0], deadline=False)
    month.add_thing(25, thing6)
    
    print("\n" + "="*50)
    # 查看某一天的事项
    print("\n查看第1天的事项:")
    month.view_day(1)
    
    print("\n查看第5天的事项:")
    month.view_day(5)
    
    print("\n" + "="*50)
    # 查看所有有事项的天数
    month.view_days_with_things()
    
    print("\n" + "="*50)
    # 查看本月总事项数
    print(f"本月总事项数: {month.get_total_things_count()}")
    
    print("\n" + "="*50)
    # 提醒功能
    month.working_day(1)
    month.working_day(15)
    
    
