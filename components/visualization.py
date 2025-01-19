import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
from mistralai import Mistral
import json

def generate_visualization_code(client, data_description, visualization_request):
    """Generate Python code for visualization using Mistral AI"""
    system_prompt = """You are a Python data visualization expert. Generate only executable Python code using 
    matplotlib or pandas plotting for the requested visualization. The code should:
    1. Read the data that was previously parsed
    2. Create the requested visualization
    3. Use st.pyplot() to display the plot
    Return only the Python code without any explanation or markdown."""
    
    user_prompt = f"""Data description: {data_description}
    Visualization request: {visualization_request}
    Generate Python code to create this visualization using the 'data' DataFrame that's already loaded."""
    
    response = client.chat.complete(
        model="mistral-large-latest",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    
    return response.choices[0].message.content

def execute_visualization(code, data):
    """Execute the generated visualization code safely"""
    try:
        # Create a new figure
        plt.figure(figsize=(10, 6))
        
        # Add data to local namespace
        local_vars = {'data': data, 'plt': plt, 'pd': pd, 'st': st}
        
        # Execute the code
        exec(code, globals(), local_vars)
        
        # Capture the plot
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        
        return buf
    except Exception as e:
        st.error(f"Error generating visualization: {str(e)}")
        return None
    finally:
        plt.close() 