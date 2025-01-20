import streamlit as st
import base64
from components.mindmap import MindMap

def render_info_panel():
    # Add custom styles for info panel title and buttons
    st.markdown("""
        <style>
        .info-panel-title {
            margin-top: 15px !important;
        }
        
        /* Button container styles */
        .stButton {
            width: 100%;
            margin-bottom: 10px;
        }
        
        /* Button styles */
        .stButton > button {
            width: 100%;
            border-radius: 20px;
            padding: 10px 20px;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        
        /* Expand button specific styles */
        [data-testid="baseButton-secondary"] {
            background-color: #00CED1 !important;
            color: white !important;
            border: none !important;
        }
        
        /* Delete button specific styles */
        .stButton > button[kind="primary"] {
            background-color: #FF4500 !important;
            border: none !important;
        }
        
        /* Hover effects */
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<h1 class="info-panel-title">Info Panel</h1>', unsafe_allow_html=True)
    
    # Check if we should display a mindmap
    if st.session_state.get('show_mindmap', False) and st.session_state.get('current_mindmap'):
        mindmap = st.session_state.current_mindmap
        
        # Create columns for the mindmap controls
        if mindmap.nodes:  # Only show if there are nodes
            clicked_node = mindmap.visualize()
            
            # Show node controls if a node is clicked
            if clicked_node:
                st.markdown(f"#### Selected: {clicked_node}")
                col1, col2 = st.columns(2, gap="medium")
                with col1:
                    if st.button("🔄 Expand", key=f"expand_{clicked_node}", use_container_width=True):
                        mindmap.ask_for_extended_graph(selected_node=clicked_node)
                        st.experimental_rerun()
                with col2:
                    if st.button("🗑️ Delete", key=f"delete_{clicked_node}", type="primary", use_container_width=True):
                        mindmap._delete_node(clicked_node)
                        st.experimental_rerun()
                st.markdown("---")  # Add a separator
    
    # Display PDF content if available
    elif 'current_file' in st.session_state and st.session_state.get('current_file'):
        try:
            # Get the selected file from uploaded_files
            current_file = st.session_state.uploaded_files.get(st.session_state['current_file'])
            if current_file:
                st.markdown(f"**File name:** {st.session_state['current_file']}")
                # Add debug info
                st.markdown(f"File size: {len(current_file.getvalue()) / 1024:.2f} KB")
                
                try:
                    # Convert PDF to base64
                    pdf_bytes = current_file.getvalue()
                    base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
                    
                    # Embed PDF viewer with error handling
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
            st.error(f"Error displaying PDF: {str(e)}")
            # Add debug info
            st.write("Session state keys:", st.session_state.keys())
            st.write("Current file:", st.session_state.get('current_file'))
            st.write("Available files:", st.session_state.get('available_files'))
    
    # Display search mode and selected files for search
    search_mode = st.session_state.get('search_mode')
    if search_mode == 'specific_files':
        selected_files = st.session_state.get('selected_files', [])
        if selected_files:
            st.markdown("**Selected for Search:**")
            for file in selected_files:
                st.markdown(f"- {file}")
    elif search_mode == 'all_files':
        st.markdown("**Searching in all files**")
    