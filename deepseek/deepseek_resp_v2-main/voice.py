#from bot import Bot
#gpt = Bot(model='gpt-4o-mini',tools=[],prompt="你是我的工作助手。",debug=True)
import os  
from dotenv import load_dotenv  
import io  
import azure.cognitiveservices.speech as speechsdk  
from openai import OpenAI
import time  
import datetime  
import threading  
import json, ast  

import requests  
from io import BytesIO  
import tempfile  
#import pyaudio  
from tools import *
import msvcrt
load_dotenv("1.env")  
client = OpenAI(api_key=os.environ["api_key"], base_url=os.environ["base_url"])
#client = OpenAI(api_key="1", base_url="http://localhost:11434/v1") 
Azure_speech_key = os.environ["Azure_speech_key"]  
Azure_speech_region = os.environ["Azure_speech_region"]  
Azure_speech_speaker = os.environ["Azure_speech_speaker"]  
WakeupWord = os.environ["WakeupWord"]  
WakeupModelFile = os.environ["WakeupModelFile"]  

messages = []  

# Set up Azure Speech-to-Text and Text-to-Speech credentials  
speech_key = Azure_speech_key  
service_region = Azure_speech_region  
speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)  
# Set up Azure Text-to-Speech language  
speech_config.speech_synthesis_language = "zh-CN"  
# Set up Azure Speech-to-Text language recognition  
speech_config.speech_recognition_language = "zh-CN"  
lang = "zh-CN"  
# Set up the voice configuration  
speech_config.speech_synthesis_voice_name = Azure_speech_speaker  
speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)  
connection = speechsdk.Connection.from_speech_synthesizer(speech_synthesizer)  
connection.open(True)  
# Creates an instance of a keyword recognition model. Update this to  
# point to the location of your keyword recognition model.  
model = speechsdk.KeywordRecognitionModel(WakeupModelFile)  
# The phrase your keyword recognition model triggers on.  
keyword = WakeupWord  
# Set up the audio configuration  
audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)  
# Create a speech recognizer and start the recognition  
#speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)  
auto_detect_source_language_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(languages=["ja-JP", "zh-CN"])  
speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config,  
                                               auto_detect_source_language_config=auto_detect_source_language_config)  
unknownCount = 0  
sysmesg = {"role": "system", "content": os.environ["sysprompt_zh-CN"]}  
tts_sentence_end = [ ".", "!", "?", ";", "。", "！", "？", "；", "\n" ]
from pynput import keyboard as pynput_keyboard    
is_playing=False
isListenning=False

key_state= "release"
def on_press(key):
        if key == pynput_keyboard.Key.f2:
            on_space_key_press(None)
def on_release(key):
        if key == pynput_keyboard.Key.f2:
            on_space_key_release(None)
    # Stop listener
       # if key == pynput_keyboard.Key.esc:
       #     return False
def on_space_key_press(event):
        global key_state
        if key_state == "press":
            return
        key_state = "press"
        if getPlayerStatus()=='playing':
                    pauseplay() #被唤醒后，如果有音乐播放则暂停播放
        stop_playback()
def on_space_key_release(event):
        global key_state
        key_state = "release"
        print("打断，等待输入")
      
# 停止播放的函数
def stop_playback():
    global is_playing
    speech_synthesizer.stop_speaking_async()
def speech_to_text():  
    global unknownCount  
    global lang,isListenning  
    print("Please say...")  
    result = speech_recognizer.recognize_once_async().get()  
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:  
        unknownCount = 0  
        isListenning=False
        return result.text  
    elif result.reason == speechsdk.ResultReason.NoMatch:  
        isListenning=False
        unknownCount += 1  
        error = os.environ["sorry_" + lang]  
        text_to_speech(error)  
        return '...'  
    elif result.reason == speechsdk.ResultReason.Canceled:  
        isListenning=False
        return "speech recognizer canceled." 
    
# 监听键盘按键，当按下空格键时，发送listen消息
listener = pynput_keyboard.Listener(on_press=on_press, on_release=on_release)
listener.start()
def getVoiceSpeed():  
    return 17  
  
def text_to_speech(text, _lang=None):  
    global lang  
    try:  
        result = buildSpeech(text).get()  
        #result = speech_synthesizer.speak_ssml_async(ssml_text).get()  
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:  
            print("Text-to-speech conversion successful.")  
            return "Done."  
        else:  
            print(f"Error synthesizing audio: {result}")  
            return "Failed."  
    except Exception as ex:  
        print(f"Error synthesizing audio: {ex}")  
        return "Error occured!"  
        
def buildSpeech(text, _lang=None):
    voice_lang = lang  
    voice_name = "zh-CN-XiaoxiaoMultilingualNeural"  
    ssml_text = f'''  
        <speak xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xmlns:emo="http://www.w3.org/2009/10/emotionml" version="1.0" xml:lang="{lang}"><voice name="{voice_name}"><lang xml:lang="{voice_lang}"><prosody rate="{getVoiceSpeed()}%">{text.replace('*', ' ')}</prosody></lang></voice></speak>  
    '''  
    print(f"{voice_name} {voice_lang}!")  
    return speech_synthesizer.speak_ssml_async(ssml_text)
  
def generate_text(prompt):  
    global messages  ,isListenning
    isListenning=True
    inp=speech_recognizer.recognize_once_async().get()  
    messages.append({"role": "user", "content": prompt})  
    tools = getTools()  
    collected_messages = []
    last_tts_request = None

    split=True
    result=''
    function_list=[]
    index=0
    
    # response_gen = client.chat.completions.create(
    #     model="deepseek-ai/DeepSeek-V3",
    #     messages=[sysmesg]+messages[-20:],
    #     tools=tools,
    #     stream=False
    # )
    stream = client.chat.completions.create(
        model="Qwen/Qwen2.5-72B-Instruct-128K",
        messages=[sysmesg]+messages[-20:],
        tools=tools,
        stream=True
    )
    func_call_list = []
    for part in stream:
        delta= part.choices[0].delta
        if delta.content:

            chunk_message =  delta.content  # 抽取流式message里的内容

            if chunk_message is not None and chunk_message!='':
                collected_messages.append(chunk_message)  # 收集保存message
                result=result+chunk_message
                
                if chunk_message in tts_sentence_end and split: # 发现分段标记：句子结束
                    text = ''.join(collected_messages).strip() # 构建句子
                    if len(text)>500 or "</think>" in text: #如果这句足够长，后面不再分段朗读了
                        split=False
                    elif len(text)<15: #如果这句太短了，不单独朗读，并入后面
                        continue
                    
                    
                    if text != '': # 如果句子里只有 \n or space则跳过朗读
                        print(f"Speech synthesized to speaker for: {text}")
                        text=text.replace("</think>","嗯，我想好了，下面是我的回答。")
                        last_tts_request = buildSpeech(text)
                       # last_tts_request = speech_synthesizer.speak_text_async(text)
                        collected_messages.clear()
        if delta.tool_calls:
          #  print(delta.tool_calls)
            for tcchunk in delta.tool_calls:
                if len(func_call_list) <= tcchunk.index:
                    func_call_list.append({
                        "id": "",
                        "name": "",
                        "type": "function", 
                        "function": { "name": "", "arguments": "" } 
                    })
                tc = func_call_list[tcchunk.index]
                if tcchunk.id:
                    tc["id"] += tcchunk.id
                if tcchunk.function.name:
                    tc["function"]["name"] += tcchunk.function.name
                if tcchunk.function.arguments:
                    tc["function"]["arguments"] += tcchunk.function.arguments
    namelist=[]
    if func_call_list:
        print(f'⏳Call internal function...')
        for  index, func in enumerate(func_call_list):
        
            function_name = func["function"]["name"]
            print(f'⏳Call {function_name}...')
            function_to_call = globals()[function_name]
            print(f'⏳Call {function_to_call}...')    
            a=func["function"]["arguments"]#+'"}' 
            print(a)
            function_args = json.loads(a)
            print(f'⏳Call params: {function_args}')
            print(f'⏳Call internal function done! ')
            if func["function"]["name"]=='playmusic':
                
                namelist.append(function_args)
                if index == len(func_call_list) - 1:  
                    #print(namelist)
                    function_response = function_to_call(namelist)
                    print("执行结果：")
                    print(function_response)
                    
                    messages.pop()
                    last_tts_request = buildSpeech(function_response)
                    result = function_response  
                    
            else:
            
                function_response = function_to_call(**function_args)
                print("执行结果：")
                print(function_response)
                messages.pop()
                last_tts_request = buildSpeech(function_response)
                result = function_response  
            print("===================================")     
        
       
 
    if last_tts_request:
        last_tts_request.get()  
        
        
    return result
  
def Get_Chat_Deployment():  
    deploymentModel = os.environ["Azure_OPENAI_Chat_API_Deployment"]  
    return deploymentModel  
  

def recognized_cb(evt):  
    result = evt.result  
    if result.reason == speechsdk.ResultReason.RecognizedKeyword:  
        print("RECOGNIZED KEYWORD: {}".format(result.text))  
    global done  
    done = True  

def canceled_cb(evt):  
    result = evt.result  
    if result.reason == speechsdk.ResultReason.Canceled:  
        print('CANCELED: {}'.format(result.cancellation_details.reason))  
    global done  
    done = True  
def display_text(tex) :
    print(tex)  
import time
def start_recognition():  
    global unknownCount ,isListenning ,playing
    while True:  
        keyword_recognizer = speechsdk.KeywordRecognizer()  
        keyword_recognizer.recognized.connect(recognized_cb)  
        keyword_recognizer.canceled.connect(canceled_cb) 
        first=os.environ["welcome_" + lang]
        display_text(first) 
        if getPlayerStatus()!='playing':
            text_to_speech(first)  
        isListenning=True
        result_future = keyword_recognizer.recognize_once_async(model)  
        while True:  
            result = result_future.get()
            # Read result audio (incl. the keyword).
            if result.reason == speechsdk.ResultReason.RecognizedKeyword:
                print("Keyword recognized")
                isListenning=False
                if getPlayerStatus()=='playing':
                    pauseplay() #被唤醒后，如果有音乐播放则暂停播放
                break
            time.sleep(0.1)  
            
        display_text("很高兴为您服务，我在听请讲。")  
        text_to_speech("很高兴为您服务，我在听请讲。")  
        
          
        while unknownCount < 2:
            isListenning=True
            t0=time.time()
            user_input = speech_to_text()
            if user_input=='...':
                continue
            print(f"You: {user_input}")  
            
            display_text(f"You: {user_input}")  
            t1=time.time()
            print(t1-t0,getPlayerStatus())
            response = generate_text(user_input)
            t2=time.time()
            print(t2-t1,getPlayerStatus())
            if getPlayerStatus()=='playing':
                break
            
            #text_to_speech(f"你说的是：{user_input}")  
            
          
        bye_text = os.environ["bye_" + lang]  
        display_text(bye_text) 
        if getPlayerStatus()!='playing':
            text_to_speech(bye_text)  
        
        unknownCount = 0  
        time.sleep(0.1)  

if __name__ == "__main__":
    start_recognition()