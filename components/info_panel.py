import streamlit as st
import base64

def render_info_panel():
    st.markdown("""
        <style>
        .info-container {
            margin-top: 1rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Wrap all content in settings container
    st.markdown('<div class="info-container">', unsafe_allow_html=True)
    
    st.markdown("### Information Panel")
    
    # Initialize pdf_ref in session state if not exists
    if 'pdf_ref' not in st.session_state:
        st.session_state.pdf_ref = None
    
    # Get the uploaded file from session state
    if 'uploaded_file' in st.session_state and st.session_state.uploaded_file is not None:
        # Store PDF reference
        st.session_state.pdf_ref = st.session_state.uploaded_file
        
        try:
            # Display filename before the PDF viewer
            st.markdown(f"**File name:** {st.session_state.pdf_ref.name}")
            
            # Convert PDF to base64
            base64_pdf = base64.b64encode(st.session_state.pdf_ref.getvalue()).decode('utf-8')
            
            # Embed PDF viewer
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Error displaying PDF: {str(e)}")
    else:
        st.markdown("Upload a PDF file to view its content here.")
    
    # Display search mode and selected files
    search_mode = st.session_state.get('search_mode')
    if search_mode == 'specific_files':
        selected_files = st.session_state.get('selected_files', [])
        if selected_files:
            st.markdown("**Selected Files:**")
            for file in selected_files:
                st.markdown(f"- {file}")
        else:
            st.markdown("No files selected")
    elif search_mode == 'all_files':
        st.markdown("**Searching in all files**")
        all_files = st.session_state.get('available_files', [])
        if all_files:
            for file in all_files:
                st.markdown(f"- {file}")
        else:
            st.markdown("No files available")
    