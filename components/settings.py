import streamlit as st
import os
from dotenv import load_dotenv
import pandas as pd
from utils.chat_utils import start_new_chat
from utils.snowflake_upload import upload_to_stage

def render_settings():
    # Load environment variables
    load_dotenv()
    
    # Get API key from environment or session state
    default_api_key = os.getenv('MISTRAL_API_KEY', '')
    
    # Conversations section
    st.sidebar.markdown('<h1>Conversations</h1>', unsafe_allow_html=True)
    
    # New Chat button
    if st.sidebar.button("+ New Chat", use_container_width=True, type="primary"):
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
            edited_name = st.sidebar.text_input(
                "Edit Chat Name",
                value=current_chat["title"],
                key="edit_chat_name",
                label_visibility="collapsed"
            )
        else:
            # Show dropdown when not editing
            selected_title = st.sidebar.selectbox(
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
                st.rerun()
        
        # Action buttons row
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            if st.session_state.edit_mode:
                if st.button("💾", key="save_edit", use_container_width=True):
                    st.session_state.chats[st.session_state.current_chat_id]["title"] = edited_name
                    st.session_state.edit_mode = False
                    st.rerun()
            else:
                if st.button("✏️", key="edit_conv", use_container_width=True):
                    st.session_state.edit_mode = True
                    st.rerun()
        
        with col2:
            if st.button("🗑️", key="delete_conv", use_container_width=True):
                if st.session_state.current_chat_id in st.session_state.chats:
                    del st.session_state.chats[st.session_state.current_chat_id]
                    if not st.session_state.chats:
                        start_new_chat()
                    else:
                        st.session_state.current_chat_id = next(iter(st.session_state.chats))
                    st.rerun()

    st.sidebar.markdown("---")
    
    # File Collection section
    st.sidebar.markdown('<h1>File Collection</h1>', unsafe_allow_html=True)
    col1, col2 = st.sidebar.columns(2)
    
    # Initialize file search state and available files if not exists
    # st.session_state.setdefault('show_file_search', False)
    st.session_state.setdefault('available_files', [])
    
    # with col1:
    #     if st.button("🔍 All", key="search_all", use_container_width=True):
    #         st.session_state['search_mode'] = 'all_files'
    #         st.session_state['show_file_search'] = False
    
    # with col2:
    #     if st.button("🔍 in File(s)", key="search_files", use_container_width=True):
    #         st.session_state['show_file_search'] = not st.session_state['show_file_search']
    
    # Show file selection dropdown if search in files is clicked
    if st.session_state['show_file_search']:
        selected_files = st.sidebar.multiselect(
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
    uploaded_file = st.sidebar.file_uploader(
        "Upload Files",
        type=["pdf", "docx", "txt", "csv", "xlsx", "xls", "ppt", "pptx"],
        help="Drop your files here"
    )
    
    # Handle uploaded file
    if uploaded_file is not None:
        try:
            if uploaded_file.name not in st.session_state.available_files:
                if 'uploaded_files' not in st.session_state:
                    st.session_state.uploaded_files = {}
                
                file_bytes = uploaded_file.read()
                uploaded_file.seek(0)
                
                st.session_state.available_files.append(uploaded_file.name)
                st.session_state.uploaded_files[uploaded_file.name] = uploaded_file
                st.session_state.uploaded_file = uploaded_file
                st.session_state['current_file'] = uploaded_file.name
                
                upload_to_stage(uploaded_file)
                st.sidebar.success(f"File '{uploaded_file.name}' uploaded successfully! Size: {len(file_bytes) / 1024:.2f} KB")
        except Exception as e:
            st.sidebar.error(f"Error processing uploaded file: {str(e)}")
    
    # Available Files dropdown
    if st.session_state.available_files:
        st.sidebar.markdown("#### Available Files")
        file_options = ["Select a file..."] + st.session_state.available_files
        selected_option = st.sidebar.selectbox(
            "Select a file to view",
            options=file_options,
            key="file_viewer_selector",
            label_visibility="collapsed",
            index=file_options.index(st.session_state.get('current_file', "Select a file..."))
        )
        
        if selected_option != "Select a file...":
            st.session_state['current_file'] = selected_option

    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    


    st.sidebar.markdown("---")
    
    # API and Snowflake Configuration Section
    st.sidebar.markdown('<h1>Configuration</h1>', unsafe_allow_html=True)
    
    # Initialize Snowflake configs in session state
    snowflake_configs = {
        'mistral_api_key': os.getenv('MISTRAL_API_KEY', ''),
        'account': os.getenv('SNOWFLAKE_ACCOUNT', ''),
        'user': os.getenv('SNOWFLAKE_USER', ''),
        'password': os.getenv('SNOWFLAKE_PASSWORD', ''),
        'database': os.getenv('SNOWFLAKE_DATABASE', ''),
        'schema': os.getenv('SNOWFLAKE_SCHEMA', ''),
        'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE', ''),
        'search_service': os.getenv('SNOWFLAKE_SEARCH_SERVICE', ''),
        'stage_name': os.getenv('SNOWFLAKE_STAGE_NAME', '')
    }
    
    for key in snowflake_configs:
        st.session_state.setdefault(f'config_{key}', snowflake_configs[key])
    
    # Show warning if required configurations are missing
    missing_configs = [
        key for key in snowflake_configs 
        if not st.session_state[f'config_{key}']
    ]
    if missing_configs:
        warning_msg = "⚠️ Required configurations missing:\n"
        for key in missing_configs:
            config_name = 'MISTRAL_API_KEY' if key == 'mistral_api_key' else f'SNOWFLAKE_{key.upper()}'
            warning_msg += f"- {config_name}\n"
        st.sidebar.warning(warning_msg)
    
    # Configuration inputs
    for key in snowflake_configs:
        # Add h3 title for each input
        title = "Mistral API Key" if key == 'mistral_api_key' else f"Snowflake {key.replace('_', ' ').title()}"
        st.sidebar.markdown(f"<h3>{title}</h3>", unsafe_allow_html=True)
        
        input_col, button_col = st.sidebar.columns([4, 1])
        
        # Input field for each configuration
        with input_col:
            new_value = st.text_input(
                "",
                value=st.session_state[f'config_{key}'],
                type="password",
                key=f"config_{key}_input",
                placeholder=f"{'MISTRAL_API_KEY' if key == 'mistral_api_key' else f'SNOWFLAKE_{key.upper()}'}",
                label_visibility="collapsed"
            )
        
        # Save button for each configuration
        with button_col:
            if st.button("💾", key=f"save_config_{key}", use_container_width=True):
                if new_value:
                    st.session_state[f'config_{key}'] = new_value
                    if key == 'mistral_api_key':
                        st.session_state.mistral_api_key = new_value
                    st.sidebar.success("✓ Saved!")
                else:
                    st.sidebar.warning("⚠️ Required")
    
    st.sidebar.markdown("---")
    