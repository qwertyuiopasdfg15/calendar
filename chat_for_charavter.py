"""
文本处理工具 - 根据指令要求处理文本
"""

import requests
import json

# ==================== 配置区 ====================
DASHSCOPE_API_KEY = ""  # 替换成你的百炼 API Key


def process_text_by_instruction(text_b: str, instruction_a: str, model: str = "qwen-turbo") -> str:
    """
    根据指令要求处理文本
    
    Args:
        text_b: 待处理的原始文字
        instruction_a: 处理要求文字（告诉 AI 如何处理）
        model: 使用的模型，默认 qwen-turbo（免费）
    
    Returns:
        处理后的文本
    
    Examples:
        >>> # 翻译
        >>> process_text_by_instruction("Hello world", "翻译成中文")
        "你好世界"
        
        >>> # 总结
        >>> process_text_by_instruction("很长的一段文章...", "用3句话总结主要内容")
        "..."
        
        >>> # 改写
        >>> process_text_by_instruction("这段话写得太啰嗦了", "改写成简洁专业的风格")
        "..."
    """
    
    url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 构建提示词：将指令和待处理文本组合
    # 使用 system 角色设定 AI 的身份，user 角色给出具体任务
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
        "temperature": 0.5,  # 降低随机性，使输出更稳定
        "max_tokens": 4000,
        "top_p": 0.9
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        
        if response.status_code != 200:
            error_msg = response.json()
            return f"错误: {error_msg.get('message', '未知错误')}"
        
        result = response.json()
        processed_text = result['choices'][0]['message']['content']
        
        return processed_text.strip()
        
    except requests.exceptions.Timeout:
        return "错误: 请求超时"
    except Exception as e:
        return f"错误: {str(e)}"


# ==================== 增强版（支持历史对话） ====================

class TextProcessor:
    """文本处理器 - 支持连续的文本处理任务"""
    
    def __init__(self, api_key: str, model: str = "qwen-turbo"):
        self.api_key = api_key
        self.model = model
        self.url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
        self.history = []  # 保存历史处理记录
        
    def process(self, text: str, instruction: str, add_to_history: bool = True) -> str:
        """
        处理文本
        
        Args:
            text: 待处理文字
            instruction: 处理要求
            add_to_history: 是否保存到历史记录
        
        Returns:
            处理后的文本
        """
        messages = [
            {
                "role": "system",
                "content": "你是一个专业的文本处理助手，严格按照用户的要求处理文本，只输出处理后的结果。"
            }
        ]
        
        # 添加历史记录（如果有）
        if self.history:
            for item in self.history[-6:]:  # 最近3轮
                messages.append({"role": "user", "content": item["input"]})
                messages.append({"role": "assistant", "content": item["output"]})
        
        # 添加当前任务
        messages.append({
            "role": "user",
            "content": f"【处理要求】：{instruction}\n\n【待处理文本】：{text}\n\n【处理结果】："
        })
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.5,
            "max_tokens": 4000
        }
        
        try:
            response = requests.post(self.url, headers=headers, json=data, timeout=60)
            
            if response.status_code != 200:
                return f"错误: {response.json().get('message', '未知错误')}"
            
            result = response.json()
            processed_text = result['choices'][0]['message']['content'].strip()
            
            # 保存历史
            if add_to_history:
                self.history.append({
                    "input": f"【要求】：{instruction}\n【文本】：{text}",
                    "output": processed_text
                })
            
            return processed_text
            
        except Exception as e:
            return f"错误: {str(e)}"
    
    def clear_history(self):
        """清空历史记录"""
        self.history = []
        
    def get_history(self):
        """获取历史记录"""
        return self.history


# ==================== 便捷函数集合 ====================

def translate(text: str, target_lang: str = "中文") -> str:
    """翻译文本"""
    return process_text_by_instruction(text, f"翻译成{target_lang}")

def summarize(text: str, max_length: int = None) -> str:
    """总结文本"""
    instruction = "用简洁的语言总结这段文字的核心内容"
    if max_length:
        instruction = f"用不超过{max_length}字总结这段文字"
    return process_text_by_instruction(text, instruction)

def rewrite(text: str, style: str = "更流畅") -> str:
    """改写文本"""
    return process_text_by_instruction(text, f"改写成{style}的风格")

def extract_keywords(text: str, count: int = 5) -> str:
    """提取关键词"""
    return process_text_by_instruction(text, f"提取{count}个最重要的关键词，用逗号分隔")

def proofread(text: str) -> str:
    """校对文本（修正语法和错别字）"""
    return process_text_by_instruction(text, "校对文本，修正语法错误和错别字，保持原意不变")

def simplify(text: str, level: str = "简单") -> str:
    """简化文本"""
    return process_text_by_instruction(text, f"用{level}易懂的语言重新表达")


# ==================== 使用示例 ====================

if __name__ == "__main__":
    # 示例1：直接使用函数
    print("=" * 60)
    print("示例1：翻译")
    result = process_text_by_instruction(
        "Artificial intelligence is transforming the world.",
        "翻译成中文"
    )
    print(f"结果: {result}")
    
    print("\n" + "=" * 60)
    print("示例2：总结")
    long_text = """
    机器学习是人工智能的一个分支，它使计算机能够从数据中学习而不需要明确编程。
    通过算法和统计模型，计算机可以识别数据中的模式并做出预测或决策。
    深度学习是机器学习的一个子集，使用多层神经网络来处理复杂的任务，
    如图像识别、自然语言处理和语音识别。
    """
    result = process_text_by_instruction(long_text, "用两句话总结这段文字")
    print(f"结果: {result}")
    
    print("\n" + "=" * 60)
    print("示例3：使用处理器的连续任务")
    processor = TextProcessor(DASHSCOPE_API_KEY)
    
    # 连续处理
    result1 = processor.process("This is a test sentence.", "翻译成中文")
    print(f"翻译: {result1}")
    
    result2 = processor.process(result1, "改写成更正式的表达")
    print(f"改写: {result2}")
    
    print("\n" + "=" * 60)
    print("示例4：使用便捷函数")
    text = "我今天去了超市，买了苹果和香蕉，苹果很好吃。"
    print(f"原文: {text}")
    print(f"校对: {proofread(text)}")
    print(f"简化: {simplify(text)}")