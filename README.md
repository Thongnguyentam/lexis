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

### 4. **Complex Reasoning Support**

- **Question Decomposition:** Automatically break down complex or multi-hop questions for accurate answers.
- **Agent-Based Reasoning:** Utilize advanced reasoning methods like ReAct and ReWOO to tackle intricate queries.

---

### 5. **Data Visualization**

- Automatically generate visualizations from data files to support research findings and presentations.

---

## Planned Features

- **RAG for Video Content:** Extend RAG capabilities to video content for research, including citation generation for specific timestamps and quotes.

---

## Technologies

- **LLM:** Powered by Mistral LLM for state-of-the-art language understanding.
- **Snowflake Cortex:** Ensures efficient data management and retrieval.
- **Hybrid Retrieval Pipeline:** Combines traditional and AI-driven retrieval methods.
- **Agent-Based Reasoning Frameworks:** ReAct, ReWOO, and others.

---

## Installation and Usage

### Prerequisites

- Python 3.8 or higher
- Required Python libraries (see `requirements.txt`)

### Installation

1. Clone the repository:
