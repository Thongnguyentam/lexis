import streamlit as st

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
    
    # PDF viewer
    st.markdown("#### PDF Preview")
    st.markdown("PDF content will be displayed here")
    
    # Additional information
    st.markdown("#### Document Information")
    st.markdown("Document metadata and information will appear here")
    