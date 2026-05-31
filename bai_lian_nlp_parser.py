"""
文本处理工具 - 根据指令要求处理文本
支持单命令和多命令解析
"""

import requests
import json
import re

DASHSCOPE_API_KEY = ""#add your key here


def process_text_by_instruction(text_b: str, instruction_a: str, model: str = "qwen-turbo") -> str:
    url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    messages = [
        {
            "role": "system",
            "content": "你是一个专业的文本处理助手，严格按照用户的要求处理文本，只输出处理后的结果，不要添加额外的解释。"
        },
        {
            "role": "user",
            "content": f"请根据以下要求处理文本：\n\n【要求】：{instruction_a}\n\n【待处理文本】：{text_b}\n\n【处理结果】："
        }
    ]
    
    data = {
        "model": model,
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": 4000,
        "top_p": 0.9
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        if response.status_code != 200:
            return f"错误: {response.json().get('message', '未知错误')}"
        result = response.json()
        return result['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"错误: {str(e)}"


# ==================== 多命令解析提示词（强化版） ====================
MULTI_COMMAND_INSTRUCTION = """
你是一个日历事件解析器。用户可能一次性输入多个操作。

【最重要】你必须输出一个JSON数组，格式如下：
[{"action":"add","date":2,"content":"和客户开会","time":[15,0],"deadline":false}, {"action":"add","date":3,"content":"交方案","time":[],"deadline":true}]

【严格要求】
1. 必须用方括号 [] 开头和结尾
2. 多个对象之间必须用逗号 , 分隔
3. 绝对禁止输出多个单独的JSON对象，例如：{"a":1}{"b":2} 这种是错误的！

操作类型: "add"(添加), "delete"(删除), "view"(查看), "clear"(清空)

日期规则: "明天"=2, "后天"=3, "昨天"=1, "今天"=1, "X号"=X
时间规则: "下午3点"=[15,0], "晚上7点"=[19,0], "上午10点"=[10,0]

正确示例1:
输入: "明天下午3点开会，后天截止交报告"
输出: [{"action":"add","date":2,"content":"开会","time":[15,0],"deadline":false}, {"action":"add","date":3,"content":"交报告","time":[],"deadline":true}]

正确示例2:
输入: "1号开会，删除3号的健身，查看5号"
输出: [{"action":"add","date":1,"content":"开会","time":[],"deadline":false}, {"action":"delete","date":3,"content":"健身","time":[],"deadline":false}, {"action":"view","date":5,"content":"","time":[],"deadline":false}]

正确示例3:
输入: "明天下午3点和客户开会，后天截止交方案，把昨天的健身补到今晚7点，看看这周五有什么安排"
输出: [{"action":"add","date":2,"content":"和客户开会","time":[15,0],"deadline":false}, {"action":"add","date":3,"content":"交方案","time":[],"deadline":true}, {"action":"add","date":1,"content":"健身","time":[19,0],"deadline":false}, {"action":"view","date":5,"content":"","time":[],"deadline":false}]

【再次强调】只输出一个JSON数组，不要输出任何其他内容。不要输出多个单独的JSON对象！

【修改时间的处理规则 - 重要！】
当用户说"把A改成B"、"把某时间改成某时间"、"挪到"、"调整到"时，你需要：
1. 先输出一个 delete 操作，删除原事项
2. 再输出一个 add 操作，在新时间添加事项
例如：用户说"把1号下午3点的会改成下午4点"
输出：[{"action":"delete","date":1,"content":"会","time":[],"deadline":false}, {"action":"add","date":1,"content":"会","time":[16,0],"deadline":false}]

例如：用户说"把3号的健身挪到5号下午5点"
输出：[{"action":"delete","date":3,"content":"健身","time":[],"deadline":false}, {"action":"add","date":5,"content":"健身","time":[17,0],"deadline":false}]

日期规则: "明天"=2, "后天"=3, "昨天"=1, "今天"=1, "X号"=X
时间规则: "下午3点"=[15,0], "晚上7点"=[19,0], "上午10点"=[10,0]

现在处理以下输入：
"""


def parse_multi_commands(user_input: str) -> list:
    """解析多个命令 - 带多种修复方法"""
    result = process_text_by_instruction(user_input, MULTI_COMMAND_INSTRUCTION)
    print(f"AI返回原始内容: {result[:300]}...")
    
    # 方法1：直接解析JSON数组
    try:
        start = result.find('[')
        end = result.rfind(']') + 1
        if start != -1 and end != 0:
            json_str = result[start:end]
            commands = json.loads(json_str)
            if isinstance(commands, list) and len(commands) > 0:
                print(f"✅ 方法1成功: {len(commands)}个命令")
                return commands
    except Exception as e:
        print(f"方法1失败: {e}")
    
    # 方法2：处理连续JSON对象 {"a":1}{"b":2} -> [{"a":1},{"b":2}]
    try:
        # 在 } { 之间插入逗号
        fixed = re.sub(r'\}\s*\{', '},{', result)
        # 用数组包裹
        fixed = '[' + fixed + ']'
        commands = json.loads(fixed)
        if isinstance(commands, list) and len(commands) > 0:
            print(f"✅ 方法2成功: 修复连续对象，{len(commands)}个命令")
            return commands
    except Exception as e:
        print(f"方法2失败: {e}")
    
    # 方法3：正则提取每个JSON对象
    try:
        objects = re.findall(r'\{[^{}]*"action"[^{}]*\}', result)
        commands = []
        for obj_str in objects:
            try:
                commands.append(json.loads(obj_str))
            except:
                pass
        if len(commands) > 0:
            print(f"✅ 方法3成功: 提取{len(commands)}个对象")
            return commands
    except Exception as e:
        print(f"方法3失败: {e}")
    
    return None


def parse_single_command(user_input: str) -> dict:
    """解析单个命令"""
    SINGLE_INSTRUCTION = f"""
将用户输入转化为一个JSON对象，格式：{{"action":"add/delete/view/clear","date":数字,"content":"内容","time":[时,分],"deadline":true/false}}
日期规则: "明天"=2, "后天"=3, "昨天"=1
时间规则: "下午3点"=[15,0]
只输出JSON，不要有其他内容。

输入：{user_input}
输出："""
    
    result = process_text_by_instruction(user_input, SINGLE_INSTRUCTION)
    try:
        start = result.find('{')
        end = result.rfind('}') + 1
        if start != -1:
            return json.loads(result[start:end])
    except:
        pass
    return {"action": "error", "date": 1, "content": "解析失败", "time": [], "deadline": False}


def parse_calendar_command(user_input: str):
    """智能解析 - 自动判断单/多命令"""
    # 判断是否多命令
    separators = ['，', ',', '、', '以及', '然后', '。']
    verbs = ['添加', '删除', '查看', '截止', '看看']
    dates = re.findall(r'\d+号|明天|后天|昨天|今天', user_input)
    
    # 多命令条件
    has_sep = any(sep in user_input for sep in separators)
    has_multi_dates = len(dates) > 1
    has_multi_verbs = sum(1 for v in verbs if v in user_input) > 1
    
    if has_sep or has_multi_dates or has_multi_verbs or len(user_input) > 30:
        multi_result = parse_multi_commands(user_input)
        if multi_result:
            return multi_result if len(multi_result) > 1 else multi_result[0]
    
    return parse_single_command(user_input)


if __name__ == "__main__":
    test = "明天下午3点和客户开会，后天截止交方案，把昨天的健身补到今晚7点，看看这周五有什么安排"
    result = parse_calendar_command(test)
    print(f"结果类型: {type(result)}")
    print(f"结果: {json.dumps(result, ensure_ascii=False, indent=2)}")