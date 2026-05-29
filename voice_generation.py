import sounddevice as sd
from scipy.io.wavfile import write
import speech_recognition as sr
import numpy as np

def record_and_recognize():
    """
    录音并转为文字。
    """
    sample_rate = 16000  # 语音识别推荐采样率
    
    print("开始录音，按回车键停止...")
    
    try:
        # 用列表收集音频块，避免 InputStream 读取时序问题
        audio_chunks = []
        
        def callback(indata, frames, time, status):
            """每收到一块音频就存起来"""
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
        
        # 把所有块拼起来
        if len(audio_chunks) == 0:
            print("没有录到声音！")
            return None
        
        audio = np.concatenate(audio_chunks, axis=0)
        # 转为一维数组
        audio = audio.flatten()
        
        print(f"录音时长：{len(audio)/sample_rate:.1f} 秒")
        
    except Exception as e:
        print(f"录音失败：{e}")
        return None
    
    # 保存为 WAV
    filename = "temp.wav"
    write(filename, sample_rate, audio)
    print(f"已保存：{filename}")
    
    # 语音识别
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
    
    return None


if __name__ == "__main__":
    record_and_recognize()