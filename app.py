import streamlit as st
from components.settings import render_settings
from components.chatbot import render_chatbot
from components.info_panel import render_info_panel

# Set maximum upload size to 1GB (1000MB)
st.set_page_config(
    layout="wide",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# Increase the upload limit
st._config.set_option('server.maxUploadSize', 1000)

def initialize_session_state():
    """Initialize session state variables"""
    if 'conversations' not in st.session_state:
        st.session_state.conversations = [
            "Previous Chat 1",
            "Previous Chat 2",
            "Previous Chat 3"
        ]
    
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False
    
    if 'show_file_search' not in st.session_state:
        st.session_state.show_file_search = False
    
    if 'available_files' not in st.session_state:
        st.session_state.available_files = []
    
    if 'pdf_ref' not in st.session_state:
        st.session_state.pdf_ref = None

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

    # Initialize session state
    initialize_session_state()
    
    # Create the main layout with columns
    col1, col2, col3 = st.columns([1, 2, 2])
    
    # Render components in their respective columns
    with col1:
        render_settings()
    
    with col2:
        render_chatbot()
    
    with col3:
        render_info_panel()

if __name__ == "__main__":
    main() 