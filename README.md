# :snowflake: Project X - Research Assistant :blue_book: :bookmark_tabs:

**Project X** is an advanced research assistant designed to streamline and enhance the research process by leveraging state-of-the-art AI technologies. With hybrid retrieval, multi-modal support, and advanced citation capabilities, Project X empowers researchers to efficiently analyze, retrieve, and cite information from diverse data sources.

---

## :snowflake: Core Features

### 1. **Robust Retrieval Augmented Generation (RAG)** :robot:

- **Hybrid Retrieval:** Combines full-text and vector-based retrieval with re-ranking to ensure the highest quality of results.
- **Multi-File Search:** Search data across multiple documents, not limited to a single file.
- **AI Agent Assistance:** If local data is insufficient, a mode with AI agents can perform searches on the web.
- **Multi-Agent Architecture**: Powered by Autogen and Mistral AI, enabling dynamic and context-aware retrieval-augmented generation (RAG). The agents are designed to collaborate seamlessly by performing advanced tasks such as: 
  - **Web Search**: Agents can autonomously search the web to gather real-time, relevant information for user queries.  
  - **Research Paper Retrieval**: By querying Arxiv databases and repositories, agents can locate and summarize research papers or articles pertinent to the topic of interest.  
  - **Knowledge Aggregation**: Through intelligent filtering and integration of diverse data sources, the agents ensure high-quality and accurate responses tailored to the user's needs.  

---

### 2. **Multi-Modal Question Answering (QA)** :left_speech_bubble:

- **Document Parsing:** Perform QA on documents containing text, figures, and tables.
- **Multi-Document Support:** Seamlessly analyze and extract insights from multiple documents simultaneously.

---

### 3. **Advanced Citations** :open_book:

- **Detailed Citations with Previews:**
  - Ensure correctness with detailed citations directly in the in-browser PDF viewer.
  - View relevant scores and highlights for context.
  - Receive warnings if retrieval pipelines return low-relevance articles.
- **Video Citations (Future Feature):**
  - Cite specific quotes from videos with accurate timestamps and proper format.
  - Save time on manual video referencing, ensuring precision in both time and content.

---

### 4. **Interactive Mind Maps** :pencil2:

- **AI-Powered Generation:** Create mind maps automatically from any topic or text using Mistral AI.
- **Interactive Editing:**
  - Expand nodes to explore related concepts
  - Delete nodes and their connections
  - Visual node selection and highlighting
- **Dynamic Visualization:** Interactive graph layout with physics simulation for optimal readability.

---

### 5. **Data Visualization** :chart:

- Automatically generate visualizations from data files using Python and matplotlib.
- Interactive plots and charts to support research findings and presentations.

---

## :snowflake: Technical Architecture
![Description of Image](https://drive.google.com/uc?export=view&id=1quNYad3x2--dm3Fqpe9qYES2PKlckPYZ)

### :asterisk: Frontend Stack

- **Streamlit:** Modern Python web framework for interactive UI components
- **Streamlit-Agraph:** Interactive graph visualization for mind maps
- **Custom CSS:** Responsive design with modern animations and styling

### :asterisk: Backend Stack

- **Mistral AI:** Large language model for intelligent responses and mind map generation
- **Snowflake Cortex Search Service:** Enterprise data platform for efficient RAG implementation including pre-processing, labelling, storing documents, and searching relevant text chunks.
- **Trulens:** Evaluation and monitoring framework for AI applications
- **Python 3.8+:** Core programming language

### :asterisk: Agentic RAG with Multi-Agents Pipeline

1. **User Proxy**: Initial query handling
3. **Intent Classifier**: A semantic router to identify user's intent, whether reading uploaded documents, searching for a paper, searching for real-time data, or general query.
4. **Specialized Agents**:
   - Document Reading Agent
   - Web Search Agent
   - Articles Research Agent
   - Conversation Agent
5. **Critic Agent**: Response refinement based on user's query, retrieved context information, writer agent's response to reduce hallucinations from LLMs.

### :asterisk: Evaluation and Tracking for LLM Experiments
![Description of Image](https://drive.google.com/uc?export=view&id=1PftJkJLoYlitlQ78nm-G2Bb1SURkZBQK)

Utilizing Trulens for tracking and evaluating performance across three core metrics:

- **Answer Relevance:** Ensures responses are coherent, accurate, and reasoned.
- **Context Relevance:** Validates the quality of retrieved information, ensuring it aligns with the query.
- **Groundedness:** Functions as hallucination detection, verifying all responses against source documents.

Our development process included creating multiple RAG versions:

- **Agent-Based Version:** Combines multiple AI agents (Document Reading, Article Research, Web Search) with Trulens' context filter guardrails. This approach enhanced context quality, reduced hallucinations, and balanced latency.
- **Agent-Free Version:** Offers simplicity with low latency by retrieving relevant context solely from uploaded documents. Although limited in accessing real-time data, it maintains high context relevance.

![Description of Image](https://drive.google.com/uc?export=view&id=11Mgwqn1LnKgPFEmy4XtFydIUbFLZA36a)

Our agent_v3's iterative refinements, including Trulens context filtering at threshold 0.5 and enhanced processing through multiple AI agents, make it a more robust and efficient RAG system compared to Agent_v1. It achieves better groundedness and higher answer quality.

---

## :snowflake: Installation and Usage

### Prerequisites

- Python 3.8 or higher
- Required Python libraries (see `requirements.txt`)
- Mistral AI API key, OPENAI API key
- Snowflake account configuration

### Installation

1. Clone the repository:

```bash
git clone https://github.com/stephanienguyen2020/project-x.git
cd project-x
```

2. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate # On Windows use: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set up your secrets:
   Create .streamlit/secrets.toml following the structure in secrets.toml.sample

5. Run the application:

```bash
streamlit run app.py
```

The application will be available at `http://localhost:8501`

### :snowflake: Project Structure
```
project-x/
├── assistance                # Multi-agents
│   ├── ...
│   ├── writer_agent.py       # Main researcher agent
│
├── components/               # UI components
│   ├── chatbot.py            # Chat interface
│   ├── info_panel.py         # Information panel
│   ├── ...
│   ├── mindmap.py            # Mind map visualization
│   └── settings.py           # Settings interface
│
├── services/                 # Backend services
│   └── rag_agents.py         # RAG version with agents
│   └── rag_no_agents.py      # RAG Version without agents 
├── ...
├── utils/                    # Utility functions
│   └── ...
│   └── trulens_feedbacks.py  # Trulensfeedback metrics
│   └── trulens_utils.py      # Trulens utilities
│
├── prompts/                  # System prompts
├── app.py                    # Main Streamlit application
└── requirements.txt          # Dependencies
```
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

## :reminder_ribbon: Support 

For support, please:

1. Check the [Issues](https://github.com/stephanienguyen2020/project-x/issues) page
2. Review existing documentation
3. Create a new issue if needed

---

## :snowflake: Acknowledgments

- Mistral AI for their powerful language model
- Snowflake for enterprise data platform capabilities
- Streamlit team for the excellent web framework
- All contributors who have helped shape this project
