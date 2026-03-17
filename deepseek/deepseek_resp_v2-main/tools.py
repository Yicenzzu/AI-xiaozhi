import json, ast
import pygame  
import requests, json
from io import BytesIO 
import tempfile 
import time
import datetime  
import io 
import dateutil.parser  
import locale 
import os
from dotenv import load_dotenv  
import subprocess  
import asyncio
from get_music import baidu
import threading
import time

def async_while_loop(song_namelist,current_music_index):
    """后台运行的while循环"""
    while True:
     for event in pygame.event.get():
        if event.type == pygame.USEREVENT:
            pygame.mixer.music.stop()
            # 音乐播放结束，播放下一首
            current_music_index += 1
            if current_music_index>=len(song_namelist):
       
                R=play(song_namelist[current_music_index])
        if event.type == pygame.QUIT:
            running = False
    return R
#load_dotenv("xiaoxin.env")  
quitReg=False
pause=False
playing=False
api=baidu.baidu() 
def getTools():
    return [fun_playmusic_desc,fun_stopplay_desc,fun_pauseplay_desc,fun_unpauseplay_desc]

def getPlayerStatus():
    global playing,pause
    if playing:
        return "playing"
    if pause:
        return "pause"
    
    
def isPlaying():
    """
    check if playing
    
    return：
        Yes if playing, No if not playing
    """
    return playing
    
def playmusic(song_namelist):
    """
    play music
    
    params：
        song_name：the name of music
        
    return：
        status
    """
    global playing, pause 
    # 设置当前音乐索引
    current_music_index = 0

    # 设置音乐播放结束事件
    pygame.mixer.music.set_endevent(pygame.USEREVENT)
    print("playmusic")
    R=play(song_namelist[current_music_index])
   
    return R
def play(song_name):
    global playing, pause 
    #return f"为您找到歌曲：{song_name} 已开始播放。如果有其他任务请告知我，我先退下了。"
    #初始化所有api
    
    
    songname,singername,songurl=api.search(song_name['song_name'])
    
    count=len(songurl)
    
    if(count>0):
        musicName = downloadAndPlay([songurl,songname],0)
        if musicName:
            print("找到歌曲：'"+musicName+"' 开始播放。请欣赏。")
            return f"为您找到歌曲：{musicName} 已开始播放。请欣赏。" #"找到歌曲：'"+musicName+"' 开始播放。请欣赏。"
        else:
            playing=False
            pause = False
            print("没有找到音乐")
            return "没有找到音乐"
    
    return "没有找到音乐"
def downloadAndPlay(music_json,index):
    global playing, pause 
    songName=music_json[1][index]
    count=len(music_json[0])
    if index>=count:
        return False
    try:
   # print(music_json["result"]["songs"][index],index)
        song_url=api.get_music_url(music_json[0][index])
       # print(song_url)
    
    
        response = requests.get(song_url)  
        audio_data = BytesIO(response.content)  

        temp_file_name = "temp_audio.mp3"  # 临时文件名 
        
        try:
        
            with open(temp_file_name, 'wb') as temp_file:  
                temp_file.write(audio_data.getbuffer())  
        except PermissionError:
            temp_file_name = "temp_audio1.mp3"  # 临时文件名 
            with open(temp_file_name, 'wb') as temp_file:  
                temp_file.write(audio_data.getbuffer())  
        temp_file.close()
        print(temp_file_name)
        
        # 初始化pygame  
        pygame.init()  
   
        # 播放音乐  
        pygame.mixer.music.load(temp_file_name)  
        pygame.mixer.music.play()
        playing=True
        pause = False
        print(songName)
        return songName
    except Exception as e:  
        print("failed play try next one")
        playing=False
        pause = False
        index+=1
        return downloadAndPlay(music_json,index)
        
    
fun_playmusic_desc = {
    "type": "function",
    'function':{
        'name': 'playmusic',
        'description': '播放歌曲',
        'parameters': {
            'type': 'object',
            'properties': {
                'song_name': {
                    'type': 'string',
                    'description': '歌名'
                },
            },
            'required': ['song_name']
        }
    }
}
def stopplay():
    """
    停止播放音乐
    
    返回：
        播放状态
    """
    global playing, pause 
    pygame.mixer.music.stop()  
    playing=False
    pause = False
    return "音乐已停止。"
    
fun_stopplay_desc = {
    "type": "function",
    'function':{
        'name': 'stopplay',
        'description': '停止播放',
        'parameters': {
            'type': 'object',
            'properties': {

            },
            'required': []
        }
    }
}
def pauseplay():
    """
    暂停音乐播放
    
    返回：
        播放状态 : 已暂停
    """
    global playing, pause
    pygame.mixer.music.pause()

    playing=False
    pause = True
    return "播放已暂停。"

fun_pauseplay_desc = {
    "type": "function",
    'function':{
        'name': 'pauseplay',
        'description': '暂停播放',
        'parameters': {
            'type': 'object',
            'properties': {

            },
            'required': []
        }
    }
}

def unpauseplay():
    """
    恢复音乐播放
    
    返回：
        播放状态 : 已经继续播放
    """
    global playing, pause
    pygame.mixer.music.unpause()
    playing=True
    pause = False
    return "恢复播放"

fun_unpauseplay_desc = {
    "type": "function",
    'function':{
        'name': 'unpauseplay',
        'description': '恢复播放',
        'parameters': {
            'type': 'object',
            'properties': {

            },
            'required': []
        }
    }
}
def isPause():
    return pause

def isPlaying():
    return playing
