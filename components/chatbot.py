import streamlit as st
import os
from mistralai import Mistral
from dotenv import load_dotenv
from prompts.system_prompts import DEFAULT_ASSISTANT_PROMPT
from utils.code_interpreter import CodeInterpreter
from typing import Optional

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
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    # Load environment variables
    load_dotenv()
    
    # Get API key from environment
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        st.error("Please set your Mistral API key in the .env file")
        return
    
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
                chatbot = Chatbot()
                
                # Check if it's a visualization request
                if any(keyword in prompt.lower() for keyword in ['plot', 'graph', 'visualize', 'chart']):
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
        system_prompt = """You are a Python data visualization expert. Generate only executable Python code using 
        matplotlib for the requested visualization. For simple visualizations, create sample data within the code. 
        Return only the Python code without any explanation or markdown."""
        
        try:
            response = self.mistral_client.chat.complete(
                model="mistral-large-latest",
                messages=[
                    {"role": "system", "content": system_prompt},
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