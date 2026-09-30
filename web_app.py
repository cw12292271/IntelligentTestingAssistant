import os

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

MY_API_KEY = os.getenv("MY_API_KEY")

import streamlit as st
import requests
import json

st.title("智能测试助手 v2")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = "web_user_001"

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("输入测试需求..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            try:
                payload = json.dumps({
                    "session_id": st.session_state.session_id,
                    "message": prompt,
                })
                resp = requests.post(
                    "http://127.0.0.1:8000/chat",
                    data=payload.encode("utf-8"),
                    headers={
                        "Content-Type": "application/json",
                        "X-API-Key": MY_API_KEY,
                    },
                    timeout=60,
                )

                if resp.status_code == 200:
                    reply = resp.json().get("reply", "无回复")
                else:
                    reply = f"请求失败 [{resp.status_code}]：{resp.text}"
            except Exception as e:
                reply = f"调用失败：{e}"
        st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})