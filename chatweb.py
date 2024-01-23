import json
import os.path
import time
import requests
import streamlit as st
from PIL import Image


st.set_page_config(
    page_title='乌冬面',
    layout='centered'
)

prompt = ['请你扮演一位微信用户“乌冬面”，并根据聊天记录以及不同用户的输入作出响应。']
url = 'http://47.106.23.17:8081//wechat/usaodon/chatglm_6b'

if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = {}

if 'friend' not in st.session_state:
    st.session_state['friend'] = {}

if 'role' not in st.session_state:
    st.session_state['role'] = ''


def post_request(model_input):
    data = {'input': model_input}
    data = json.dumps(data, ensure_ascii=False).encode('utf-8')
    try:
        request = requests.post(url, data=data)
        res = json.loads(request.text)['output']
    except:
        res = '乌冬面:遭了，请求超时了'
    return res


def send_click():
    if st.session_state['user'] != None:
        chat_input = st.session_state['user']
        print('用户输入:', chat_input)

        role = st.session_state['role']

        if role not in st.session_state['friend']:
            st.session_state['friend'][role] = []
        st.session_state['friend'][role].append(':'.join([role, chat_input]))

        if len(st.session_state['friend'][role]) > 10:
            temp_list = prompt + st.session_state['friend'][role][-10:]
        else:
            temp_list = prompt + st.session_state['friend'][role]

        print('Model input: {}'.format(temp_list))
        output = post_request(temp_list)

        print('Output: {}'.format(output))

        output = output.split(' ')[0].strip()
        st.session_state['friend'][role].append(output)


with st.sidebar:
    st.title('选择你的角色，给乌冬面发消息')

    charactor = st.selectbox(' ', ('乌冬面女朋友', '乌冬面堂兄弟', '乌冬面研究生同学', '乌冬面本科同学', '乌冬面领导'))
    charactor_lookup = {
        '乌冬面女朋友': '老婆',
        '乌冬面堂兄弟': '堂哥',
        '乌冬面研究生同学': '祥',
        '乌冬面本科同学': '丁丁',
        '乌冬面师兄': '向元新'
    }

    role = charactor_lookup[charactor]
    st.session_state['role'] = role
    img = Image.open('{}/service/{}.png'.format(os.getcwd(), role))
    st.image(img)

st.title('乌冬面')
st.divider()

user_input = st.chat_input()

if user_input != '':
    st.session_state['user'] = user_input
    send_click()

if role in st.session_state['friend']:
    print(st.session_state['friend'][role])
    for i in range(len(st.session_state['friend'][role])):
        line = st.session_state['friend'][role][i]
        if line.find('乌冬面') != -1:
            chat_list = line.split('乌冬面:')[1].split('<s>')
            for c in chat_list:
                img = Image.open('{}/service/usaodon.png'.format(os.getcwd()))
                with st.chat_message('user', avatar=img):
                    st.write(c)
        else:
            img = Image.open('{}/service/{}.png'.format(os.getcwd(), role))
            with st.chat_message('assistant', avatar=img):
                st.write(line.replace(role + ':', ''))
