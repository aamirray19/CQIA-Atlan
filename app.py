# ==========================
# app.py
# ==========================
import streamlit as st
import os, shutil, tempfile, zipfile, stat
from pathlib import Path

from ingestion.ingestor import Ingestor
from builder.rag_payload_builder import RAGPayloadBuilder
from builder.agent_payload_builder import AgentPayloadBuilder
from utils.vector_store import VectorDB
from agents.general_agent import QualityAnalysisAgent
from agents.final_report_builder import FinalQualityReportAgent
from utils.rag_chatbot import RAGChatbot  # multi-turn RAG chatbot using Groq

# --- Error handler for shutil.rmtree on Windows ---
def _on_rm_error(func, path, exc_info):
    if not os.access(path, os.W_OK):
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise

# --- Streamlit Session State Initialization ---
for key in ["ingested_data", "temp_dir", "rag_payloads", "agent_payloads",
            "ai_reports", "final_major_report", "vector_stored", "chat_history"]:
    if key not in st.session_state:
        st.session_state[key] = None

# ==========================
# Step 1: Ingest Codebase
# ==========================
st.set_page_config(layout="wide")
st.title("📂 Code Quality Intelligence Agent")
st.markdown("Ingest a codebase, run quality analysis, store results, generate final report, and interact via RAG Chatbot.")
st.markdown("---")

source_option = st.radio(
    "**Select codebase source**",
    ("Local File(s)", "Local Folder (Zip)", "GitHub URL"),
    horizontal=True
)

# Clear previous state if source changes
if st.session_state.get("source_option") != source_option:
    st.session_state.source_option = source_option
    st.session_state.ingested_data = None
    st.session_state.rag_payloads = None
    st.session_state.agent_payloads = None
    st.session_state.ai_reports = None
    st.session_state.final_major_report = None
    st.session_state.vector_stored = None
    if st.session_state.temp_dir and os.path.exists(st.session_state.temp_dir):
        shutil.rmtree(st.session_state.temp_dir, onerror=_on_rm_error)
        st.session_state.temp_dir = None

# --- Input Handling ---
def handle_input(source_option: str):
    data_to_process = {}
    if not st.session_state.temp_dir:
        st.session_state.temp_dir = tempfile.mkdtemp()

    if source_option == "Local File(s)":
        uploaded_files = st.file_uploader("Upload one or more files", accept_multiple_files=True)
        if uploaded_files:
            ingestor = Ingestor()
            for uploaded_file in uploaded_files:
                temp_filepath = Path(st.session_state.temp_dir) / uploaded_file.name
                with open(temp_filepath, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                data_to_process.update(ingestor.ingest_file(str(temp_filepath)))
            st.session_state.ingested_data = data_to_process

    elif source_option == "Local Folder (Zip)":
        uploaded_zip = st.file_uploader("Upload a `.zip` file", type=["zip"])
        if uploaded_zip:
            with zipfile.ZipFile(uploaded_zip, 'r') as zip_ref:
                zip_ref.extractall(st.session_state.temp_dir)
            ingestor = Ingestor()
            data_to_process = ingestor.ingest_folder(str(st.session_state.temp_dir))
            st.session_state.ingested_data = data_to_process

    elif source_option == "GitHub URL":
        github_url = st.text_input("Enter public GitHub repository URL")
        if github_url and github_url.strip():
            ingestor = Ingestor()
            data_to_process = ingestor.ingest_github_repo(github_url.strip())
            for rel_path, content in data_to_process.items():
                file_path = Path(st.session_state.temp_dir) / rel_path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
            st.session_state.ingested_data = data_to_process

handle_input(source_option)

if st.session_state.ingested_data:
    st.success(f"✔️ Files Ingested: {len(st.session_state.ingested_data)}")

# ==========================
# Step 2-6: Single "Run All" Button
# ==========================
if st.button("Run Full Quality Analysis Workflow"):
    # --- Build Payloads ---
    file_paths = [Path(st.session_state.temp_dir) / rel_path for rel_path in st.session_state.ingested_data.keys()]
    rag_builder = RAGPayloadBuilder()
    st.session_state.rag_payloads = rag_builder.build_payloads(file_paths)
    st.session_state.agent_payloads = AgentPayloadBuilder.build_payloads(file_paths)
    st.success(f"RAG Payloads Count: {len(st.session_state.rag_payloads)}")
    st.success(f"Agent Payloads Count: {len(st.session_state.agent_payloads)}")

    # --- Run General Quality Analysis Agent ---
    agent = QualityAnalysisAgent()
    for payload in st.session_state.agent_payloads:
        agent.analyze_batch([payload])  # sequential processing
    st.session_state.ai_reports = agent.get_final_report()
    st.success(f"JSON Report Generated: {len(st.session_state.ai_reports)} issues")
    st.subheader("Generated JSON Report")
    st.json(st.session_state.ai_reports)

    # --- Store in Vector DB ---
    db = VectorDB(persist_dir="vector_db")
    if st.session_state.rag_payloads:
        db.add_rag_payloads(st.session_state.rag_payloads)
    if st.session_state.ai_reports:
        db.add_ai_reports({"GeneralQuality": st.session_state.ai_reports})
    st.session_state.vector_stored = True
    st.success("Payloads and JSON report stored in vector DB")

    # --- Generate Final Major Report using Groq ---
    final_agent = FinalQualityReportAgent()
    st.session_state.final_major_report = final_agent.build_report(st.session_state.ai_reports)
    st.subheader("Final Major Report (Human Readable)")
    st.text_area("Final Report", st.session_state.final_major_report, height=300)

# ==========================
# Step 7: Multi-turn RAG Chatbot
# ==========================
if st.session_state.vector_stored:
    st.markdown("---")
    st.subheader("RAG Chatbot (Multi-turn)")
    query = st.text_input("Ask a question to the RAG Chatbot")
    if "chat_history" not in st.session_state or st.session_state.chat_history is None:
        st.session_state.chat_history = []

    if st.button("Send Query"):
        rag_agent = RAGChatbot()
        response = rag_agent.ask(query, st.session_state.chat_history)
        st.session_state.chat_history.append((query, response))
        st.text_area(
            "Chat History",
            "\n\n".join([f"Q: {q}\nA: {a}" for q, a in st.session_state.chat_history]),
            height=300
        )
        # --- Clear vector DB after chatbot interaction ---
        db.clear_all()
        st.success("✅ Vector DB cleared after RAG Chatbot session")
