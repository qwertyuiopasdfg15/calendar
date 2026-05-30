import sounddevice as sd
from scipy.io.wavfile import write
import speech_recognition as sr
import numpy as np

# 检查音频设备
def check_audio_devices():
    """检查可用的音频设备"""
    try:
        devices = sd.query_devices()
        input_devices = [d for d in devices if d['max_input_channels'] > 0]
        if len(input_devices) == 0:
            print("警告：未找到麦克风输入设备")
            return False
        else:
            print(f"找到 {len(input_devices)} 个麦克风设备")
            for dev in input_devices:
                print(f"  - {dev['name']}")
            return True
    except Exception as e:
        print(f"检查音频设备失败: {e}")
        return False


def record_and_recognize():
    """
    录音并转为文字。
    """
    # 先检查音频设备
    if not check_audio_devices():
        print("没有找到可用的麦克风，请检查设备连接")
        return None
    
    sample_rate = 16000
    
    print("开始录音，按回车键停止...")
    
    try:
        audio_chunks = []
        
        def callback(indata, frames, time, status):
            audio_chunks.append(indata.copy())
        
        stream = sd.InputStream(
            samplerate=sample_rate,
            channels=1,
            dtype='int16',
            callback=callback
        )
        stream.start()
        
        input()  # 等待按回车
        
        stream.stop()
        stream.close()
        
        if len(audio_chunks) == 0:
            print("没有录到声音！")
            return None
        
        audio = np.concatenate(audio_chunks, axis=0)
        audio = audio.flatten()
        
        print(f"录音时长：{len(audio)/sample_rate:.1f} 秒")
        
    except Exception as e:
        print(f"录音失败：{e}")
        print("提示：请确保麦克风已连接并有录音权限")
        return None
    
    filename = "temp.wav"
    write(filename, sample_rate, audio)
    print(f"已保存：{filename}")
    
    print("正在识别...")
    r = sr.Recognizer()
    
    try:
        with sr.AudioFile(filename) as source:
            audio_data = r.record(source)
        text = r.recognize_google(audio_data, language='zh-CN')
        print(f"\n✅ 识别结果：{text}")
        return text
    except sr.UnknownValueError:
        print("未能识别出内容，可能录音太模糊或无声音。")
    except sr.RequestError as e:
        print(f"网络请求失败：{e}")
    except Exception as e:
        print(f"识别错误：{e}")
    
    return None


if __name__ == "__main__":
    record_and_recognize()