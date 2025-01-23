from datetime import datetime

def start_new_chat():
    """Create a fresh chat session with a new timestamp-based ID.
    Initializes with default welcome message and triggers page rerun."""
    import streamlit as st
    
    new_chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    st.session_state.current_chat_id = new_chat_id
    st.session_state.chats[new_chat_id] = {
        "title": "New Chat",
        "messages": [
            {
                "role": "assistant",
                "content": "Hi! I'm a chatbot powered by Mistral AI. I can help you analyze documents, answer questions, and assist with various tasks. How can I help you today? 🤖"
            }
        ]
    }
    st.rerun() 