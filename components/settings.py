import streamlit as st
import os
from dotenv import load_dotenv
import pandas as pd
from components.chatbot import start_new_chat

def render_settings():
    # Load environment variables
    load_dotenv()
    
    # Get API key from environment or session state
    default_api_key = os.getenv('MISTRAL_API_KEY', '')
    
    st.markdown("""
        <style>
        .settings-container {
            margin-top: 1rem;
        }
        .chat-list {
            margin-bottom: 1rem;
        }
        .chat-item {
            padding: 0.5rem;
            margin: 0.25rem 0;
            border-radius: 4px;
            cursor: pointer;
        }
        .chat-item:hover {
            background-color: #f0f2f6;
        }
        .selected-chat {
            background-color: #e6f3ff;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Wrap all content in settings container
    st.markdown('<div class="settings-container">', unsafe_allow_html=True)
    
    # Conversations dropdown section
    st.markdown("### Conversations")
    
    # New Chat button
    if st.button("+ New Chat", use_container_width=True):
        start_new_chat()
    
    # Initialize edit mode state if not exists
    st.session_state.setdefault('edit_mode', False)
    
    if "chats" in st.session_state:
        # Get list of chat titles for dropdown
        chat_options = [
            (chat_id, chat_data["title"]) 
            for chat_id, chat_data in st.session_state.chats.items()
        ]
        
        if st.session_state.edit_mode:
            # Show text input when editing
            current_chat = st.session_state.chats[st.session_state.current_chat_id]
            edited_name = st.text_input(
                "Edit Chat Name",
                value=current_chat["title"],
                key="edit_chat_name",
                label_visibility="collapsed"
            )
        else:
            # Show dropdown when not editing
            selected_title = st.selectbox(
                "Select Conversation",
                options=[title for _, title in chat_options],
                index=next(
                    (i for i, (chat_id, _) in enumerate(chat_options) 
                    if chat_id == st.session_state.current_chat_id), 
                    0
                ),
                key="conversation_select",
                label_visibility="collapsed"
            )
            # Find chat_id for selected title
            selected_chat_id = next(
                chat_id for chat_id, title in chat_options 
                if title == selected_title
            )
            if selected_chat_id != st.session_state.current_chat_id:
                st.session_state.current_chat_id = selected_chat_id
                st.experimental_rerun()
        
        # Action buttons row
        col1, col2 = st.columns(2)
        
        with col1:
            if st.session_state.edit_mode:
                if st.button("💾 Save", key="save_edit", use_container_width=True):
                    st.session_state.chats[st.session_state.current_chat_id]["title"] = edited_name
                    st.session_state.edit_mode = False
                    st.experimental_rerun()
            else:
                if st.button("✏️ Edit", key="edit_conv", use_container_width=True):
                    st.session_state.edit_mode = True
                    st.experimental_rerun()
        
        with col2:
            if st.button("🗑️ Delete", key="delete_conv", use_container_width=True):
                if st.session_state.current_chat_id in st.session_state.chats:
                    del st.session_state.chats[st.session_state.current_chat_id]
                    # Create new chat if we deleted the last one
                    if not st.session_state.chats:
                        start_new_chat()
                    else:
                        # Switch to another existing chat
                        st.session_state.current_chat_id = next(iter(st.session_state.chats))
                    st.experimental_rerun()

    st.markdown("---")
    
    # Initialize API key in session state if not exists
    st.session_state.setdefault('mistral_api_key', default_api_key)
    
    # API key input with password mask
    api_key = st.text_input(
        "Mistral API Key",
        value=st.session_state.mistral_api_key,
        type="password",
        help="Enter your Mistral API key here. You can also set it in the .env file.",
        placeholder="sk-..."
    )
    
    # Save API key to session state when changed
    if api_key != st.session_state.mistral_api_key:
        st.session_state.mistral_api_key = api_key
        if api_key:
            st.success("API key updated successfully!")
    
    # Show API key status
    if st.session_state.mistral_api_key:
        st.info("✓ API key is set")
    else:
        st.warning("⚠️ API key is not set")
  
    # Divider
    st.markdown("---")
    
    # File Collection section
    st.markdown("#### File Collection")
    col1, col2 = st.columns(2)
    
    # Initialize file search state and available files if not exists
    st.session_state.setdefault('show_file_search', False)
    st.session_state.setdefault('available_files', [])
    
    with col1:
        if st.button("Search All", key="search_all", use_container_width=True):
            st.session_state['search_mode'] = 'all_files'
            st.session_state['show_file_search'] = False
    
    with col2:
        if st.button("Search in File(s)", key="search_files", use_container_width=True):
            # Toggle file search dropdown
            st.session_state['show_file_search'] = not st.session_state['show_file_search']
    
    # Show file selection dropdown if search in files is clicked
    if st.session_state['show_file_search']:
        selected_files = st.multiselect(
            "Select files to search",
            options=st.session_state.available_files,
            default=None,
            key="file_selector"
        )
        if selected_files:
            st.session_state['selected_files'] = selected_files
            st.session_state['search_mode'] = 'specific_files'
        else:
            st.session_state['selected_files'] = []
            st.session_state['search_mode'] = None
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Upload PDF",
        type=["pdf"],
        help="Drop your PDF file here"
    )
    
    # Handle uploaded file
    if uploaded_file is not None:
        try:
            # Add the uploaded file to available_files if not already present
            if uploaded_file.name not in st.session_state.available_files:
                # Initialize uploaded_files dict if not exists
                if 'uploaded_files' not in st.session_state:
                    st.session_state.uploaded_files = {}
                
                # Store the file data
                file_bytes = uploaded_file.read()
                uploaded_file.seek(0)  # Reset file pointer after reading
                
                # Store everything in session state
                st.session_state.available_files.append(uploaded_file.name)
                st.session_state.uploaded_files[uploaded_file.name] = uploaded_file
                st.session_state.uploaded_file = uploaded_file
                st.session_state['current_file'] = uploaded_file.name
                
                st.success(f"File '{uploaded_file.name}' uploaded successfully! Size: {len(file_bytes) / 1024:.2f} KB")
        except Exception as e:
            st.error(f"Error processing uploaded file: {str(e)}")
    
    # Available Files dropdown
    if st.session_state.available_files:
        st.markdown("#### Available Files")
        file_options = ["Select a file..."] + st.session_state.available_files
        selected_option = st.selectbox(
            "Select a file to view",
            options=file_options,
            key="file_viewer_selector",
            label_visibility="collapsed",
            index=file_options.index(st.session_state.get('current_file', "Select a file..."))  # Set default value to current file
        )
        
        if selected_option != "Select a file...":
            st.session_state['current_file'] = selected_option
    
    # Feedback section with toggle
    feedback_header = st.container()
    with feedback_header:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("#### Feedback")
        with col2:
            # Initialize show_feedback state if not exists
            if 'show_feedback' not in st.session_state:
                st.session_state.show_feedback = False
                
            # Create a clickable header that toggles visibility
            if st.button(
                '▼' if not st.session_state.show_feedback else '▲',
                key='toggle_feedback',
                use_container_width=True
            ):
                st.session_state.show_feedback = not st.session_state.show_feedback
                st.experimental_rerun()
    
    # Show feedback content only if show_feedback is True
    if st.session_state.show_feedback:
        # Correctness section
        st.markdown("##### Correctness:")
        correctness = st.radio(
            "Correctness",
            options=["The answer is correct", "The answer is incorrect"],
            label_visibility="collapsed"
        )
        
        # Other issue section
        st.markdown("##### Other issue:")
        other_issue = st.radio(
            "Other issue",
            options=["The answer is offensive", "The evidence is incorrect"],
            label_visibility="collapsed"
        )
        
        # More detail text area
        feedback_detail = st.text_area(
            "More detail (e.g. how wrong is it, what is the correct answer, etc...)",
            height=100
        )
        
        # Help text
        st.markdown("This will send the current chat and the user settings to help with investigation")
        
        # Report button
        if st.button("Report", use_container_width=True):
            # Handle report submission
            feedback_data = {
                'correctness': correctness,
                'other_issue': other_issue,
                'detail': feedback_detail
            }
            st.session_state['feedback_submitted'] = feedback_data

    
    st.markdown('</div>', unsafe_allow_html=True)
    
    