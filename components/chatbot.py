import streamlit as st
import os
from mistralai import Mistral
from dotenv import load_dotenv
from prompts.system_prompts import DEFAULT_ASSISTANT_PROMPT, VISUALIZATION_EXPERT_PROMPT
from utils.code_interpreter import CodeInterpreter
from typing import Optional
from datetime import datetime

def init_chat_history():
    """Initialize chat history in session state"""
    if "chats" not in st.session_state:
        st.session_state.chats = {}
    
    if "current_chat_id" not in st.session_state:
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

def get_current_chat():
    """Get the current chat's messages"""
    if st.session_state.current_chat_id in st.session_state.chats:
        return st.session_state.chats[st.session_state.current_chat_id]["messages"]
    return []

def add_message(role, content):
    """Add a message to the current chat"""
    if st.session_state.current_chat_id in st.session_state.chats:
        st.session_state.chats[st.session_state.current_chat_id]["messages"].append({
            "role": role,
            "content": content
        })
        # Update chat title based on first user message if it's still "New Chat"
        if (role == "user" and 
            len(st.session_state.chats[st.session_state.current_chat_id]["messages"]) == 2 and
            st.session_state.chats[st.session_state.current_chat_id]["title"] == "New Chat"):
            st.session_state.chats[st.session_state.current_chat_id]["title"] = content[:30] + "..."

def start_new_chat():
    """Start a new chat session"""
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
    st.experimental_rerun()

def render_chatbot():
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    # Load environment variables
    load_dotenv()
    
    # Get API key from environment
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        st.error("Please set your Mistral API key in the .env file")
        return
    
    init_chat_history()
    
    margin_top = "1rem"

    # Add title with custom class
    st.markdown('<h1 class="chat-title">💬 Chat with Mistral</h1>', unsafe_allow_html=True)

    # Display current chat messages
    messages = get_current_chat()
    for message in messages:
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
                chatbot = Chatbot()
                
                # Check if it's a visualization request
                if any(keyword in prompt.lower() for keyword in ['histogram', 'plot', 'graph', 'visualize', 'chart']):
                    response = chatbot.process_visualization_request(prompt)
                else:
                    # Handle regular chat responses
                    response = chatbot.process_query(prompt)
                
                message_placeholder.markdown(response)
                add_message("assistant", response)
                
            except Exception as e:
                message_placeholder.error(f"Error: {str(e)}")

class Chatbot:
    def __init__(self):
        self.code_interpreter = CodeInterpreter()
        # Initialize Mistral client
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            raise ValueError("Please set your Mistral API key in the .env file")
        self.mistral_client = Mistral(api_key=api_key)
        
    def process_visualization_request(self, query: str) -> str:
        """Handle visualization requests"""
        try:
            response = self.mistral_client.chat.complete(
                model="mistral-large-latest",
                messages=[
                    {"role": "system", "content": VISUALIZATION_EXPERT_PROMPT},
                    {"role": "user", "content": query}
                ]
            )
            
            # Extract just the Python code from the response
            code = response.choices[0].message.content
            
            # If the response contains markdown code blocks, extract just the code
            if "```python" in code:
                code = code.split("```python")[1].split("```")[0].strip()
            elif "```" in code:
                code = code.split("```")[1].split("```")[0].strip()
            
            # Execute the code
            results = self.code_interpreter.execute_code(code)
            if results:
                self.code_interpreter.display_results(results)
                return "I've created the visualization based on your request. Let me know if you'd like any adjustments!"
            return "I couldn't create the visualization. Please try again with a different request."
            
        except Exception as e:
            st.error(f"Error creating visualization: {str(e)}")
            return "Sorry, I encountered an error while creating the visualization."

    def process_query(self, query: str) -> str:
        """Process user query"""
        try:
            response = self.mistral_client.chat.complete(
                model="mistral-large-latest",
                messages=[
                    {"role": "system", "content": DEFAULT_ASSISTANT_PROMPT},
                    {"role": "user", "content": query}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            st.error(f"Error processing query: {str(e)}")
            return "Sorry, I encountered an error while processing your request."

    def __del__(self):
        """Cleanup resources"""
        if hasattr(self, 'code_interpreter'):
            self.code_interpreter.close()