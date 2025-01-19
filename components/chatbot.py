import streamlit as st
import os
from mistralai import Mistral
from dotenv import load_dotenv
from prompts.system_prompts import DEFAULT_ASSISTANT_PROMPT
from utils.snowflake_rag import SnowflakeRAG
import pandas as pd

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
                            "role": "system",
                            "content": DEFAULT_ASSISTANT_PROMPT
                        }
                    ] + [
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

class Chatbot:
    def __init__(self):
        self.rag = SnowflakeRAG()
        # ... existing initialization code ...

    def setup_rag_components(self):
        """Setup RAG-related UI components"""
        with st.sidebar:
            st.header("Document Processing")
            uploaded_file = st.file_uploader("Upload PDF", type=['pdf'])
            if uploaded_file:
                if st.button("Process Document"):
                    try:
                        # Save to Snowflake stage (implementation needed)
                        stage_path = "@DOCUMENTS_STAGE"
                        self.rag.extract_pdf_text(stage_path, "RAW_DOCUMENTS")
                        self.rag.chunk_text("RAW_DOCUMENTS", "CHUNKED_DOCUMENTS")
                        self.rag.create_search_service(
                            "DOCUMENT_SEARCH",
                            "CHUNKED_DOCUMENTS",
                            "YOUR_DATABASE",
                            "YOUR_SCHEMA"
                        )
                        st.success("Document processed successfully!")
                    except Exception as e:
                        st.error(f"Error processing document: {str(e)}")

    def process_query(self, query: str):
        """Process user query using RAG"""
        try:
            # Get relevant context
            context = self.rag.search_context(
                "DOCUMENT_SEARCH",
                query,
                "YOUR_DATABASE",
                "YOUR_SCHEMA"
            )

            # Display retrieved context
            st.subheader("Retrieved Context")
            search_df = pd.json_normalize(context['results'])
            for _, row in search_df.iterrows():
                st.write(f"**Source:** {row['DOCUMENT_NAME']}")
                st.caption(row['CHUNK'])
                st.write('---')

            # Get LLM response
            model = st.selectbox(
                'Select Model:',
                ['mistral-large2', 'mistral-7b', 'llama3.1-8b', 'llama3.1-70b']
            )
            response = self.rag.get_llm_response(query, context, model)
            
            return response
        except Exception as e:
            st.error(f"Error processing query: {str(e)}")
            return None

    def display(self):
        """Display chatbot interface"""
        self.setup_rag_components()
        # ... existing display code ...