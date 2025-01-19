import streamlit as st

def init_page_config():
    """Initialize page configuration and load global styles"""
    st.set_page_config(
        layout="wide",
        menu_items={
            'Get Help': None,
            'Report a bug': None,
            'About': None
        }
    )
    
    # Increase the upload limit to 1GB
    st._config.set_option('server.maxUploadSize', 1000)
    
    # Load global CSS
    with open('static/styles.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True) 