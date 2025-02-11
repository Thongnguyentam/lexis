import streamlit as st
import base64
from components.mindmap import MindMap

def render_info_panel():
    """Render the information panel component of the application.
    
    This panel serves multiple purposes:
    1. Displays interactive mind maps when generated
    2. Shows PDF document previews when files are selected
    3. Indicates current search mode and selected files
    
    The panel includes:
    - Custom styling for buttons and titles
    - Interactive controls for mind map nodes (expand/delete)
    - PDF viewer with error handling
    - Search mode status display
    """
    
    # Add custom styles for info panel title and buttons
    st.markdown("""
        <style>
        /* Custom styles for consistent panel appearance */
        .info-panel-title {
            margin-top: 15px !important;
        }
        
        /* Button container styles for full-width layout */
        .stButton {
            width: 100%;
            margin-bottom: 10px;
        }
        
        /* Common button styling for consistent look */
        .stButton > button {
            width: 100%;
            border-radius: 20px;
            padding: 10px 20px;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        
        /* Expand button styling - uses teal color scheme */
        [data-testid="baseButton-secondary"] {
            background-color: #00CED1 !important;
            color: white !important;
            border: none !important;
        }
        
        /* Delete button styling - uses warning color scheme */
        .stButton > button[kind="primary"] {
            background-color: #FF4500 !important;
            border: none !important;
        }
        
        /* Hover animation for better interactivity */
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        
        /* YouTube video container styling */
        .video-container {
            position: relative;
            padding-bottom: 56.25%; /* 16:9 aspect ratio */
            height: 0;
            overflow: hidden;
            max-width: 100%;
        }
        
        .video-container iframe {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<h1 class="info-panel-title">Info Panel</h1>', unsafe_allow_html=True)
    
    # YouTube Video Display Section
    if 'current_video' in st.session_state:
        video = st.session_state.current_video
        st.markdown(f"**Video Title:** {video['title']}")
        st.markdown(f"**Channel:** {video['author']}")
        
        # Create embedded video player
        video_embed = f"""
        <div class="video-container">
            <iframe
                src="https://www.youtube.com/embed/{video['id']}"
                frameborder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowfullscreen
            ></iframe>
        </div>
        """
        st.markdown(video_embed, unsafe_allow_html=True)
        st.markdown("---")  # Visual separator
    
    # Mind Map Display Section
    if st.session_state.get('show_mindmap', False) and st.session_state.get('current_mindmap'):
        mindmap = st.session_state.current_mindmap
        
        # Display mind map visualization and controls
        if mindmap.nodes:  # Only show if there are nodes
            clicked_node = mindmap.visualize()
            
            # Show interactive controls when a node is selected
            if clicked_node:
                st.markdown(f"#### Selected: {clicked_node}")
                col1, col2 = st.columns(2, gap="medium")
                with col1:
                    # Expand button to grow the mind map from selected node
                    if st.button("🔄 Expand", key=f"expand_{clicked_node}", use_container_width=True):
                        mindmap.ask_for_extended_graph(selected_node=clicked_node)
                        st.rerun()
                with col2:
                    # Delete button to remove the selected node and its children
                    if st.button("🗑️ Delete", key=f"delete_{clicked_node}", type="primary", use_container_width=True):
                        mindmap._delete_node(clicked_node)
                        st.rerun()
                st.markdown("---")  # Visual separator
    
    # PDF Display Section
    elif 'current_file' in st.session_state and st.session_state.get('current_file'):
        try:
            # Retrieve selected PDF file from session state
            current_file = st.session_state.uploaded_files.get(st.session_state['current_file'])
            if current_file:
                st.markdown(f"**File name:** {st.session_state['current_file']}")
                # Display file size for debugging purposes
                st.markdown(f"File size: {len(current_file.getvalue()) / 1024:.2f} KB")
                
                try:
                    # Convert PDF to base64 for embedded display
                    pdf_bytes = current_file.getvalue()
                    base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
                    
                    # Create embedded PDF viewer with error handling
                    pdf_display = f"""
                        <iframe 
                            src="data:application/pdf;base64,{base64_pdf}" 
                            width="100%" 
                            height="700" 
                            type="application/pdf"
                            style="border: none;"
                        >
                        </iframe>
                    """
                    st.markdown(pdf_display, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error encoding PDF: {str(e)}")
            else:
                st.warning("File object not found in session state")
            
        except Exception as e:
            # Detailed error reporting with debug information
            st.error(f"Error displaying PDF: {str(e)}")
            st.write("Session state keys:", st.session_state.keys())
            st.write("Current file:", st.session_state.get('current_file'))
            st.write("Available files:", st.session_state.get('available_files'))
    
    # Search Mode Display Section
    search_mode = st.session_state.get('search_mode')
    if search_mode == 'specific_files':
        # Display list of files selected for targeted search
        selected_files = st.session_state.get('selected_files', [])
        if selected_files:
            st.markdown("**Selected for Search:**")
            for file in selected_files:
                st.markdown(f"- {file}")
    elif search_mode == 'all_files':
        st.markdown("**Searching in all files**")
    