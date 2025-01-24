from services.rag_agents import AgentRAG
from services.search_service import search
import streamlit as st
import os
from mistralai import Mistral
from dotenv import load_dotenv
from prompts.system_prompts import DEFAULT_ASSISTANT_PROMPT, VISUALIZATION_EXPERT_PROMPT
from utils.code_interpreter import CodeInterpreter
from typing import Optional
from datetime import datetime
from config import SnowflakeConfig
from components.mindmap import MindMap
from components.videorag import VideoRAG
import codecs
from utils.chat_utils import start_new_chat

def init_chat_history():
    """Initialize or retrieve chat history from session state.
    Creates a new chat session if none exists, with a timestamp-based ID
    and default welcome message."""
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
                    "content": "Hi! I’m Lexis, your AI research assistant. Unlike generic AI, I specialize in analyzing documents, answering complex questions, and even creating knowledge graphs to visualize insights. Ready to dive in? 🤖"
                }
            ]
        }

def get_current_chat():
    """Retrieve messages from the current active chat session.
    
    Returns:
        list: List of message dictionaries containing role and content.
        Returns empty list if no current chat exists.
    """
    if st.session_state.current_chat_id in st.session_state.chats:
        return st.session_state.chats[st.session_state.current_chat_id]["messages"]
    return []

def add_message(role, content):
    """Add a new message to the current chat session.
    Also updates chat title based on first user message.
    
    Args:
        role (str): Message sender role ('user' or 'assistant')
        content (str): Message content text
    """
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

def render_chatbot():
    """Render the main chatbot interface including:
    - Chat history display
    - Message input
    - Response handling for different types of requests (visualization, mindmap, etc)
    
    Handles API authentication and error states."""
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    # Load environment variables
    load_dotenv()
    
    # Get API key from environment
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        return
    
    init_chat_history()
    # Add title with custom class
    st.markdown('<h1 class="chat-title">💬 Chat with Lexis</h1>', unsafe_allow_html=True)

    # Display current chat messages
    messages = get_current_chat()
    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Add RAG status indicator
    # if hasattr(st.session_state, 'chatbot') and st.session_state.chatbot.snowflake:
    #     st.sidebar.success("📚 Knowledge Base: Connected")
    # else:
    #     st.sidebar.warning("📚 Knowledge Base: Disconnected")
    
    # Chat input
    if prompt := st.chat_input("Message Mistral..."):
        # Add user message to chat
        with st.chat_message("user"):
            st.markdown(prompt)
        add_message("user", prompt)
        
        # Get bot response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            
            # Add custom CSS for progress bar
            st.markdown("""
                <style>
                .stProgress > div > div > div > div {
                    background-color: #00CED1;
                }
                </style>""", 
                unsafe_allow_html=True
            )
            progress_bar = st.progress(0)
            
            try:
                chatbot = Chatbot()
                progress_bar.progress(30)  # Start processing
                
                # Check if it's a visualization request
                if any(keyword in prompt.lower() for keyword in ['histogram', 'plot', 'graph', 'visualize', 'chart']):
                    progress_bar.progress(60)  # Visualization processing
                    response = chatbot.process_visualization_request(prompt)
                else:
                    # Handle regular chat responses
                    progress_bar.progress(60)  # Query processing
                    response = chatbot.process_query(prompt)
                
                progress_bar.progress(100)  # Complete
                progress_bar.empty()  # Remove progress bar
                message_placeholder.markdown(response)
                add_message("assistant", response)
                
            except Exception as e:
                progress_bar.empty()  # Remove progress bar
                message_placeholder.error(f"Error: {str(e)}")

def is_youtube_url(query: str) -> bool:
    """Check if the query contains a YouTube URL."""
    return any(x in query.lower() for x in ['youtube.com/watch?v=', 'youtu.be/', 'youtube.com/shorts/'])

class Chatbot:
    """Main chatbot class handling message processing and responses.
    
    Integrates with:
    - Mistral AI for language processing
    - Snowflake for RAG (Retrieval Augmented Generation)
    - Code interpreter for visualizations
    - Mind map generation
    """

    def __init__(self):
        """Initialize chatbot components including:
        - Code interpreter for running visualization code
        - Mistral AI client for language processing
        - Snowflake connector for knowledge base access"""
        self.code_interpreter = CodeInterpreter()
        
        # Initialize Mistral client
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            # Instead of raising an error, just set client to None
            self.mistral_client = None
            return
        self.mistral_client = Mistral(api_key=api_key)
        
        # Initialize Snowflake RAG
        try:
            snowflake_config = SnowflakeConfig()
            self.snowflake = AgentRAG(snowflake_config)
        except Exception as e:
            st.error(f"Error initializing Snowflake: {str(e)}")
            self.snowflake = None

        # Initialize VideoRAG
        self.video_rag = VideoRAG(self.mistral_client)
        self.current_video_id = None

    def is_mindmap_request(self, query: str) -> bool:
        """Detect if user query is requesting mind map visualization
        by checking for relevant keywords.
        
        Args:
            query (str): User input text
            
        Returns:
            bool: True if query appears to be requesting a mind map
        """
        mindmap_keywords = [
            'mind map', 'mindmap', 'knowledge graph', 'knowledgegraph',
            'mindmaps', 'knowledge graphs', 'knowledgegraphs'
        ]
        return any(keyword in query.lower() for keyword in mindmap_keywords)

    def process_mindmap_request(self, query: str) -> str:
        """Generate and display an interactive mind map based on user query.
        Stores mind map in session state for info panel display.
        
        Args:
            query (str): User's mind map request
            
        Returns:
            str: Success/error message about mind map creation
        """
        try:
            # Initialize or get existing mindmap
            mindmap = MindMap.load()
            
            # Generate new mindmap
            mindmap.ask_for_initial_graph(query=query)
            
            # Store mindmap in session state for info panel
            st.session_state.show_mindmap = True
            st.session_state.current_mindmap = mindmap
            
            return "I've created a mind map based on your request. You can view and interact with it in the information panel. Click on nodes to expand or delete them!"
            
        except Exception as e:
            st.error(f"Error creating mind map: {str(e)}")
            return "Sorry, I encountered an error while creating the mind map."

    def process_visualization_request(self, query: str) -> str:
        """Generate data visualizations using Mistral AI and code interpreter.
        
        Args:
            query (str): User's visualization request
            
        Returns:
            str: Success/error message about visualization creation
            
        Process:
        1. Get visualization code from Mistral AI
        2. Extract pure Python code from response
        3. Execute code through interpreter
        4. Display results
        """
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
        """Process user input and generate appropriate response.
        
        Args:
            query (str): User input text
            
        Returns:
            str: Response text, potentially including source attribution
            
        Handles multiple request types:
        - Mind map generation
        - Data visualization
        - RAG-enhanced responses
        - Regular chat responses
        """
        try:
            # # Check if query contains YouTube URL
            # if is_youtube_url(query):
            #     return self.video_rag.process_video_query(query)
            
            # # If we have a current video and the query seems to be about it
            # elif self.current_video_id and not self.is_mindmap_request(query):
            #     return self.video_rag.query_video(query, self.current_video_id)
            
            # Check if it's a mindmap request
            if self.is_mindmap_request(query):
                return self.process_mindmap_request(query)
            # Check if it's a visualization request
            elif any(keyword in query.lower() for keyword in ['histogram', 'plot', 'graph', 'visualize', 'chart']):
                return self.process_visualization_request(query)
            # Handle regular queries
            elif self.snowflake:
                # # Get RAG context and prompt
                # prompt, source_paths = self.snowflake.create_prompt_no_agent(query)
                # # Use Mistral with RAG context
                # response = self.mistral_client.chat.complete(
                #     model="mistral-large-latest",
                #     messages=[
                #         {"role": "system", "content": DEFAULT_ASSISTANT_PROMPT},
                #         {"role": "user", "content": prompt}
                #     ]
                # )
                
                # # Add source attribution if sources were found
                # answer = response.choices[0].message.content
                # if source_paths:
                #     sources_list = "\n".join([f"- {path}" for path in source_paths])
                #     answer += f"\n\nSources:\n{sources_list}"
                answer = search(query)
                return answer
            else:
                # Fallback to regular chat if Snowflake is not available
                return self._process_regular_query(query)
                
        except Exception as e:
            st.error(f"Error processing query: {e}")
            return "Sorry, I encountered an error while processing your request."

    def _process_regular_query(self, query: str) -> str:
        """Handle standard chat queries without RAG enhancement.
        Used as fallback when Snowflake connection unavailable.
        
        Args:
            query (str): User input text
            
        Returns:
            str: Direct response from Mistral AI
        """
        response = self.mistral_client.chat.complete(
            model="mistral-large-latest",
            messages=[
                {"role": "system", "content": DEFAULT_ASSISTANT_PROMPT},
                {"role": "user", "content": query}
            ]
        )
        return response.choices[0].message.content

    def cleanup(self):
        """Clean up resources and connections:
        - Code interpreter cleanup
        - Snowflake session closure
        - VideoRAG cleanup"""
        if hasattr(self, 'code_interpreter'):
            self.code_interpreter.cleanup()
        if hasattr(self, 'snowflake'):
            try:
                self.snowflake.session.close()
            except:
                pass
        # if hasattr(self, 'video_rag'):
        #     self.video_rag.cleanup()

    def __del__(self):
        """Destructor to ensure proper resource cleanup when object is deleted."""
        self.cleanup()