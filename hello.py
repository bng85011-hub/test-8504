import streamlit as st

st.title("Hello App")

name = st.text_input("이름을 입력하세요")

if name:
    st.write(f"Hello, {name}!")
