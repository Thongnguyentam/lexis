import streamlit as st
from snowflake.snowpark import Session, FileOperation

stage_nm='docs'

conn_param={
    "user": st.secrets["snowflake"]["user"],
    'account': st.secrets["snowflake"]["account"],
    'password': st.secrets["snowflake"]["password"],
    'database': st.secrets["snowflake"]["database"],
    'warehouse': st.secrets["snowflake"]["warehouse"],
    'schema': st.secrets["snowflake"]["schema"]
}

try:
    # Create session
    session = Session.builder.configs(conn_param).create()
    st.success("Successfully connected to Snowflake!")

    # First, make sure the stage exists
    try:
        session.sql(f"CREATE STAGE IF NOT EXISTS {stage_nm}").collect()
        st.write(f"Stage '{stage_nm}' is ready")
    except Exception as e:
        st.error(f"Error creating stage: {str(e)}")

    uploaded_file = st.file_uploader("Choose a file")
    if uploaded_file is not None:
        try:
            # Show file details
            st.write(f"Uploading file: {uploaded_file.name}")
            
            # Attempt to upload
            stage_location = f'@{stage_nm}/{uploaded_file.name}'
            FileOperation(session).put_stream(
                input_stream=uploaded_file, 
                stage_location=stage_location
            )
            
            # Verify upload
            result = session.sql(f"LIST @{stage_nm}").collect()
            st.success(f"File uploaded successfully! Files in stage:")
            st.write(result)
            
        except Exception as e:
            st.error(f"Error uploading file: {str(e)}")

except Exception as e:
    st.error(f"Failed to connect to Snowflake: {str(e)}")
