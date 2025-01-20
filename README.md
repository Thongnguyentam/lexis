# Project X - Research Assistant

## Overview

**Project X** is an advanced research assistant designed to streamline and enhance the research process by leveraging state-of-the-art AI technologies. With hybrid retrieval, multi-modal support, and advanced citation capabilities, Project X empowers researchers to efficiently analyze, retrieve, and cite information from diverse data sources.

---

## Features

### 1. **Robust Retrieval Augmented Generation (RAG)**

- **Hybrid Retrieval:** Combines full-text and vector-based retrieval with re-ranking to ensure the highest quality of results.
- **Multi-File Search:** Search data across multiple documents, not limited to a single file.
- **AI Agent Assistance:** If local data is insufficient, an AI agent can perform searches on the web.

---

### 2. **Multi-Modal Question Answering (QA)**

- **Document Parsing:** Perform QA on documents containing text, figures, and tables.
- **Multi-Document Support:** Seamlessly analyze and extract insights from multiple documents simultaneously.

---

### 3. **Advanced Citations**

- **Detailed Citations with Previews:**
  - Ensure correctness with detailed citations directly in the in-browser PDF viewer.
  - View relevant scores and highlights for context.
  - Receive warnings if retrieval pipelines return low-relevance articles.
- **Video Citations (Future Feature):**
  - Cite specific quotes from videos with accurate timestamps and proper format.
  - Save time on manual video referencing, ensuring precision in both time and content.

---

### 4. **Interactive Mind Maps**

- **AI-Powered Generation:** Create mind maps automatically from any topic or text using Mistral AI.
- **Interactive Editing:**
  - Expand nodes to explore related concepts
  - Delete nodes and their connections
  - Visual node selection and highlighting
- **Dynamic Visualization:** Interactive graph layout with physics simulation for optimal readability.

---

### 5. **Data Visualization**

- Automatically generate visualizations from data files using Python and matplotlib.
- Interactive plots and charts to support research findings and presentations.

---

## Technologies

### Frontend

- **Streamlit:** Modern Python web framework for interactive UI components
- **Streamlit-Agraph:** Interactive graph visualization for mind maps
- **Custom CSS:** Responsive design with modern animations and styling

### Backend

- **Mistral AI:** Large language model for intelligent responses and mind map generation
- **Snowflake Cortex:** Enterprise data platform for efficient RAG implementation
- **Python 3.8+:** Core programming language
  - matplotlib: Data visualization
  - base64: PDF encoding and display
  - typing: Type hints for better code reliability

### Architecture

- **Component-Based Design:**
  - Modular components for chat, info panel, and mind maps
  - Session state management for persistent data
  - Error handling and graceful fallbacks
- **RAG Pipeline:**
  - Hybrid retrieval combining traditional and AI methods
  - Source attribution and relevance scoring
  - Multi-document context integration

---

## Installation and Usage

### Prerequisites

- Python 3.8 or higher
- Required Python libraries (see `requirements.txt`)
- Mistral AI API key
- Snowflake account configuration

### Installation

1. Clone the repository:

```
bash
git clone https://github.com/stephanienguyen2020/project-x.git
cd project-x
```

2. Create and activate a virtual environment:

```
bash
python -m venv .venv
source .venv/bin/activate # On Windows use: venv\Scripts\activate
```

3. Install dependencies:

```
bash
pip install -r requirements.txt
```

4. Set up your environment variables:
   Create a `.env` file in the project root using the `.env.example` file as a reference.

5. Run the application:

```
bash
streamlit run app.py
```

The application will be available at `http://localhost:8501`

### Project Structure

project-x/
├── app.py # Main Streamlit application
├── components/ # UI components
│ ├── chatbot.py # Chat interface
│ ├── info_panel.py # Information panel
│ ├── mindmap.py # Mind map visualization
│ └── settings.py # Settings interface
├── services/ # Backend services
│ └── snowflake_utils.py # Snowflake integration
├── static/ # Static assets
│ └── styles.css # Custom styling
├── utils/ # Utility functions
├── prompts/ # System prompts
└── requirements.txt # Dependencies

### Troubleshooting

1. **Connection Issues**

   - Verify your Mistral AI API key is correct
   - Check Snowflake credentials and network access
   - Ensure all required environment variables are set

2. **Visualization Problems**

   - Make sure matplotlib and streamlit-agraph are properly installed
   - Check browser console for any JavaScript errors
   - Try clearing browser cache and Streamlit cache

3. **Performance Issues**
   - Adjust Snowflake warehouse size if needed
   - Consider reducing chunk size for large documents
   - Monitor memory usage for large mind maps

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## Support

For support, please:

1. Check the [Issues](https://github.com/stephanienguyen2020/project-x/issues) page
2. Review existing documentation
3. Create a new issue if needed

---

## Acknowledgments

- Mistral AI for their powerful language model
- Snowflake for enterprise data platform capabilities
- Streamlit team for the excellent web framework
- All contributors who have helped shape this project
