
# Code Quality Intelligence Agent

**Overview:**

The **Code Quality Intelligence Agent (CQIA)** is a multi-agent system designed to automatically evaluate the quality of source code.  
It combines **static analysis, AST parsing, concurrent multi-agent evaluation, and a RAG-powered chatbot** to provide deep insights into your project’s maintainability, security, and reliability.

---

## 🔍 Overview

CQIA leverages **five specialized agents**, each targeting a critical aspect of code quality:

1. **Code Duplication Agent**  
   Detects redundant or repeated logic across files and modules, improving maintainability.

2. **Security Agent**  
   Flags unsafe functions, insecure dependencies, and potential vulnerabilities.

3. **Performance Agent**  
   Highlights inefficient loops, heavy memory usage, and resource bottlenecks.

4. **Reliability & Fault Tolerance Agent**  
   Reviews exception handling and recovery strategies to ensure system resilience.

5. **Complexity Agent**  
   Uses AST-driven structural analysis (cyclomatic complexity, nesting depth) to measure readability and maintainability.

---

## ⚙️ How It Works

### 1. **Ingestion & Payload Creation**
- Source files are ingested automatically.  
- Each file is transformed into a **payload** containing:
  - **Raw Code** – original source for direct inspection.
  - **AST (Abstract Syntax Tree)** – structural representation of the code.
  - **Metadata** – file paths, function boundaries, and contextual info.

### 2. **Concurrent Multi-Agent Analysis**
- The payload is sent to all five agents **concurrently**, ensuring faster evaluations.  
- Each agent produces issue reports specific to its domain.  

### 3. **RAG Chatbot**
- A **Retrieval-Augmented Generation (RAG) chatbot** is integrated for interactive exploration.  
- It leverages embeddings of raw code, AST fragments, and metadata to:
  - Describe project folder structures.  
  - Summarize detected issues.  
  - Provide natural language insights.  

### 4. **Report Generation**
- All results are aggregated into a **comprehensive quality report**, combining duplication, security, performance, reliability, and complexity metrics.

---

## 📊 Output

- **Structured JSON Reports** for each agent.  
- **Consolidated Multi-Agent Report** summarizing overall code quality.  
- **Interactive Chatbot** to query project structure and issues in natural language.  



## Environment Variables

To run this project, you will need to add the following environment variables to your .env file

`GROQ_API_KEY`



## Deployment

To deploy this project, clone the Repository and run the below commands

```bash
  pip install -r requirements.txt
```

```bash
  streamlit run app.py
```