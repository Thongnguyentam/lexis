import os
import io
import sys
import contextlib
import warnings
from typing import Optional, List, Any
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO

class CodeInterpreter:
    def __init__(self):
        self.globals = {
            'pd': pd,
            'plt': plt,
            'st': st,
            'print': self._capture_print
        }
        self.output = []
        
    def _capture_print(self, *args, **kwargs):
        """Capture print statements"""
        output = StringIO()
        print(*args, file=output, **kwargs)
        self.output.append(output.getvalue())
        output.close()

    def execute_code(self, code: str) -> Optional[List[Any]]:
        """Execute code safely and return results"""
        with st.spinner('Executing code...'):
            try:
                # Reset output collection
                self.output = []
                
                # Capture stdout and stderr
                stdout = StringIO()
                stderr = StringIO()
                
                # Add data to globals if it exists in session state
                if 'visualization_data' in st.session_state:
                    self.globals['data'] = st.session_state.visualization_data
                
                with contextlib.redirect_stdout(stdout), \
                     contextlib.redirect_stderr(stderr), \
                     warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    
                    # Create a new figure for plotting
                    plt.figure(figsize=(10, 6))
                    
                    # Execute the code
                    exec(code, self.globals)
                    
                    # Get any printed output
                    stdout_content = stdout.getvalue()
                    stderr_content = stderr.getvalue()
                    
                    results = []
                    
                    # Add any printed output
                    if stdout_content:
                        results.append(stdout_content)
                    if stderr_content:
                        results.append(f"Warnings/Errors:\n{stderr_content}")
                    
                    # Add any matplotlib figures
                    if plt.get_fignums():
                        results.append(plt.gcf())
                    
                    plt.close('all')
                    return results
                    
            except Exception as e:
                st.error(f"Error executing code: {str(e)}")
                return None

    def display_results(self, results):
        """Display execution results"""
        if not results:
            return
            
        for result in results:
            if isinstance(result, str):
                st.text(result)
            elif isinstance(result, plt.Figure):
                st.pyplot(result)
            else:
                st.write(result) 