import streamlit as st
from openai import OpenAI
from audiorecorder import audiorecorder
import numpy as np
import os
from datetime import datetime
from gtts import gTTS
import base64

def ask_gpt(prompt, model, client):
    response = client.chat.completions.create(
        model = model, messages=prompt
    )
    system_message = response['choices'][0]['message']
    return system_message['content']

def TTS(response):
    filename = "output.mp3"
    tts=gTTS(text=response, lang='ko')
    tts.save(filename)
    
    with open(filename, 'rb') as f:
        data=f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
        <audio autoplay='True'>
        <source src='data:audio/mp3;base64,{b64}' type='audio/mp3'>
        </audio>
        """
        st.markdown(md, unsafe_allow_html=True,)
    os.remove(filename)

def main():
    # 기본 설정
    st.set_page_config(
        page_title = '음성 비서 프로그램',
        layout='wide'
    )
    
    flag_start = False
    
    st.header('음성 비서 프로그램')
    
    st.markdown('---')
    
    with st.expander('음성 비서 프로그램에 관하여', expanded=True):
        st.write(
            """
            - 음성 비서 프로그램의 UI는 스트림릿을 활용하였습니다.
            - STT(Speech to Text)는 OpenAI의 Whisper AI를 활용하였습니다.
            - 답변은 OpenAI의 GPT 모델을 활용했습니다.
            - TTS(Text-To-Speech)는 구글의 Google Translate TTS를 활용하였습니다.
            """
        )
        st.markdown("")
        
    with st.sidebar:
        client = OpenAI(api_key=st.text_input(
            label='OPENAI API KEY', 
            placeholder='Enter your API Key',
            value="",
            type="password"))
        st.markdown('---')
        
        model = st.radio(label='GPT 모델', options=['gpt-4-turbo', 'gpt-3.5-turbo'])
        st.markdown('---')
        
        if st.button(label='초기화'):
            pass
        
    # 기능 구현
    col1, col2 = st.columns(2)
    with col1:
        st.subheader('질문하기')
        audio = audiorecorder('클릭하여 녹음하기', '녹음 중...')
        
        # 오디오 길이와 이미 저장된 오디오인지 확인
        if len(audio) > 0 and not np.array_equal(audio, st.session_state['check_audio']):
            # 음성 재생
            st.audio(audio.tobytes())
            # 음원에서 텍스트 추출
            question = STT(audio, client)
            
            # 채팅 시각화를 위한 질문 내용 저장
            now = datetime.now().strftime("%H:%M")
            st.session_state['chat'] = st.session_state['chat'] + [('user', now, question)]
            st.session_state['messages'] = st.session_state['message'] + [{'role':'user', 'content':question}]
            st.session_state['check_audio'] = audio
            flag_start = True
        
    with col2:
        st.subheader('질문/답변')
        if flag_start:
            # 답변 받기
            response = ask_gpt(st.session_state['messages'], model)
            # GPT 모델에 넣을 프롬프트를 위해 답변 저장
            st.session_state['messages'] = st.session_state['messages'] + [{'role':'system', 'content':response}]
            # 채팅 시각화를 위해 답변 저장
            now = datetime.now().strftime('%H:%M')
            st.session_state['chat'] = st.session_state['chat'] + [{'bot', now, response}]
            
            # 채팅 형식으로 시각화
            for sender, time, message in st.session_state['chat']:
                if sender == 'user':
                    st.write(f"<div style='display:flex;align-items:center;'><div style='background-color:#007AFF;color:white;border-radius:12px;padding:8px 12px;margin-right:8px;'>{message}</div><div style='font-size:0.8rem;color:gray;'>{time}</div></div>",
                             unsafe_allow_html=True)
                    st.write("")
                else:
                    st.write(f"<div style='display:flex;align-items:center;justify-content:flex-end'><div style='background-color:lightgray;border-radius:12px;padding:8px 12px;margin-left:8px;'>{message}</div><div style='font-size:0.8rem;color:gray;'>{time}</div></div>",
                             unsafe_allow_html=True)
                    st.write("")
            TTS(response)
                    
        
    if "chat" not in st.session_state:
        st.session_state['chat'] = []
    if 'messages' not in st.session_state:
        st.session_state['messages'] = [
            {'role': 'system', 
             'content': 'You are a thoughful assistant. Respond to all input in 25 words and answer in Korea'
             }
            ]
    if 'check_audio' not in st.session_state:
        st.session_state['check_audio'] = []

def STT(audio, client):
    # 파일 저장
    filename = 'input.mp3'
    wav_file = open(filename, 'wb')
    wav_file.write(audio.tobytes())
    wav_file.close()
    
    #음원 파일 열고 텍스트 얻기
    audio_file = open(filename, 'rb')
    transcript = client.audio.transcriptions.create(
        file=audio_file, model='whisper-1',response_format='text')
    audio_file.close()
    os.remove(filename)
    
    return transcript
        
if __name__=="__main__":
    main()