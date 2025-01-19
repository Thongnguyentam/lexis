import streamlit as st

def render_chatbot():
    st.markdown("### Conversations")
    
    # Chat messages container
    chat_container = st.container()
    
    with chat_container:
        # Display messages here
        st.markdown("Chat messages will appear here")
    
    # Input area
    user_input = st.text_input("Chat input", key="chat_input")
    
    # Buttons
    col1, col2 = st.columns([4, 1])
    with col1:
        if st.button("Send", use_container_width=True):
            if user_input:
                # Handle sending message
                st.write(f"Sent: {user_input}")
    
    with col2:
        if st.button("Regen", use_container_width=True):
            # Handle regenerating response
            st.write("Regenerating response...") 