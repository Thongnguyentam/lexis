import streamlit as st
import os
from dotenv import load_dotenv

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
        </style>
    """, unsafe_allow_html=True)
    
    # Wrap all content in settings container
    st.markdown('<div class="settings-container">', unsafe_allow_html=True)
    
    # Conversations dropdown section
    st.markdown("### Conversations")
    
    # Create a container for the conversations list
    conversations_container = st.container()
    
    with conversations_container:
        # Add New Chat button
        if st.button("+ New Chat", use_container_width=True):
            # Handle new chat creation
            st.session_state.setdefault('conversations', [])
            st.session_state.conversations.insert(0, f"New Chat {len(st.session_state.conversations) + 1}")
        
        # Initialize conversations in session state if not exists
        st.session_state.setdefault('conversations', [
            "Previous Chat 1",
            "Previous Chat 2",
            "Previous Chat 3"
        ])
        
        # Initialize edit mode state if not exists
        st.session_state.setdefault('edit_mode', False)
        
        # Create a dropdown for conversations
        if st.session_state.edit_mode:
            # Show text input when editing
            edited_name = st.text_input(
                "Edit Conversation Name",
                value=st.session_state.get('selected_conv', ''),
                key="edit_conv_name",
                label_visibility="collapsed"
            )
        else:
            # Show dropdown when not editing
            selected_conv = st.selectbox(
                "Select Conversation",
                options=st.session_state.conversations,
                key="conversation_select",
                label_visibility="collapsed"
            )
            st.session_state.selected_conv = selected_conv
        
        # Store selected conversation in session state
        if not st.session_state.edit_mode and st.session_state.get('selected_conv'):
            st.session_state['current_conversation'] = st.session_state.conversations.index(st.session_state.selected_conv)
        
        # Action buttons row
        col1, col2, col3 = st.columns([4, 1, 1])
        with col2:
            if st.session_state.edit_mode:
                if st.button("💾", key="save_edit", use_container_width=True):
                    idx = st.session_state.conversations.index(st.session_state.selected_conv)
                    st.session_state.conversations[idx] = edited_name
                    st.session_state.edit_mode = False
                    st.experimental_rerun()
            else:
                if st.button("✏️", key="edit_conv", use_container_width=True):
                    st.session_state.edit_mode = True
                    st.experimental_rerun()
        
        with col3:
            if st.button("🗑️", key="delete_conv", use_container_width=True):
                idx = st.session_state.conversations.index(st.session_state.selected_conv)
                st.session_state.conversations.pop(idx)
                st.experimental_rerun()
    
    # Divider
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
    
    # Initialize file search state
    st.session_state.setdefault('show_file_search', False)
    st.session_state.setdefault('available_files', [
        "document1.pdf",
        "report2023.pdf",
        "analysis.pdf",
        "data.pdf"
    ])
    
    with col1:
        if st.button("Search All", key="search_all", use_container_width=True):
            # Handle Search All action
            st.session_state['search_all_clicked'] = True
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
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Upload PDF",
        type=["pdf"],
        help="Drop your PDF file here"
    )
    
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
    
    