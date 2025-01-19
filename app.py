import streamlit as st
from components.settings import render_settings
from components.chatbot import render_chatbot
from components.info_panel import render_info_panel

st.set_page_config(layout="wide")

def main():
    # Apply custom CSS
    with open("static/styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    # Create three columns
    settings_col, chat_col, info_col = st.columns([1, 2, 1])
    # Render components in their respective columns
    with settings_col:
        render_settings()
    
    with chat_col:
        render_chatbot()
    
    with info_col:
        render_info_panel()

if __name__ == "__main__":
    main() 