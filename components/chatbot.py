import streamlit as st
import os
from mistralai import Mistral
from dotenv import load_dotenv

def init_chat_history():
    if "messages" not in st.session_state:
        # Add initial welcome message
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hi! I'm a chatbot powered by Mistral AI. I can help you analyze documents, answer questions, and assist with various tasks. How can I help you today? 🤖"
            }
        ]

def add_message(role, content):
    st.session_state.messages.append({"role": role, "content": content})

def render_chatbot():
    st.markdown("""
        <style>
        .chat-container {
            margin-top: 1rem;
        }
        </style>
    """, unsafe_allow_html=True)
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    # Load environment variables
    load_dotenv()
    
    # Get API key from environment
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        st.error("Please set your Mistral API key in the .env file")
        return
        
    model = "mistral-large-latest"
    
    # Initialize Mistral client
    client = Mistral(api_key=api_key)
    
    init_chat_history()
    
    st.title("💬 Chat with Mistral")

    # Display messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Message Mistral..."):
        # Add user message to chat
        with st.chat_message("user"):
            st.markdown(prompt)
        add_message("user", prompt)
        
        # Get bot response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            try:
                chat_response = client.chat.complete(
                    model=model,
                    messages=[
                        {
                            "role": msg["role"],
                            "content": msg["content"]
                        }
                        for msg in st.session_state.messages
                    ]
                )
                
                # Get and display response
                assistant_response = chat_response.choices[0].message.content
                message_placeholder.markdown(assistant_response)
                add_message("assistant", assistant_response)
                
            except Exception as e:
                message_placeholder.error(f"Error: {str(e)}")