import streamlit as st
from components.settings import render_settings
from components.chatbot import render_chatbot
from components.info_panel import render_info_panel

st.set_page_config(layout="wide")

def main():
    # Custom CSS for layout
    st.markdown("""
        <style>
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 1rem !important;
        }
        
        [data-testid="stSidebarContent"] {
            padding-top: 1rem !important;
        }
        
        .stMarkdown {
            margin-top: 0 !important;
        }
        
        h1, h2, h3 {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
        
        /* Remove default Streamlit padding */
        .main > div {
            padding-top: 1rem !important;
        }
        
        [data-testid="column"] {
            padding-top: 0 !important;
            padding-bottom: 0 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # Create three columns with equal top padding
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