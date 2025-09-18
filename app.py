# # ==========================
# # app.py (Updated with Chat UI + Expanders)
# # ==========================
# import streamlit as st
# import os, shutil, tempfile, zipfile, stat, json, asyncio, random, time
# from pathlib import Path

# from ingestion.ingestor import Ingestor
# from builder.rag_payload_builder import RAGPayloadBuilder
# from builder.agent_payload_builder import AgentPayloadBuilder
# from utils.vector_store import VectorDB
# from agents.performance_analysis_agent import PerformanceAnalysisAgent
# from agents.code_duplication_agent import CodeDuplicationAgent
# from agents.complexity_analysis_agent import ComplexityAnalysisAgent
# from agents.reliability_fault_tolerence_agent import ReliabilityAgent
# from agents.security_analysis_agent import SecurityAnalysisAgent
# from agents.final_report_builder import FinalQualityReportAgent
# from utils.rag_chatbot import RAGChatbot  # multi-turn RAG chatbot using Groq

# # --- Error handler for shutil.rmtree on Windows ---
# def _on_rm_error(func, path, exc_info):
#     if not os.access(path, os.W_OK):
#         os.chmod(path, stat.S_IWUSR)
#         func(path)
#     else:
#         raise

# # --- Streamlit Session State Initialization ---
# for key in [
#     "ingested_data", "temp_dir", "rag_payloads", "agent_payloads",
#     "ai_reports", "final_major_report", "vector_stored",
#     "chat_history", "messages"
# ]:
#     if key not in st.session_state:
#         st.session_state[key] = None

# # ==========================
# # Step 1: Ingest Codebase
# # ==========================
# st.set_page_config(layout="wide")
# st.title("📂 Code Quality Intelligence Agent")
# st.markdown("Ingest a codebase, run quality analysis, store results, generate final report, and interact via RAG Chatbot.")
# st.markdown("---")

# source_option = st.radio(
#     "**Select codebase source**",
#     ("Local File(s)", "Local Folder (Zip)", "GitHub URL"),
#     horizontal=True
# )

# # Clear previous state if source changes
# if st.session_state.get("source_option") != source_option:
#     st.session_state.source_option = source_option
#     st.session_state.ingested_data = None
#     st.session_state.rag_payloads = None
#     st.session_state.agent_payloads = None
#     st.session_state.ai_reports = None
#     st.session_state.final_major_report = None
#     st.session_state.vector_stored = None
#     if st.session_state.temp_dir and os.path.exists(st.session_state.temp_dir):
#         shutil.rmtree(st.session_state.temp_dir, onerror=_on_rm_error)
#         st.session_state.temp_dir = None

# # --- Input Handling ---
# def handle_input(source_option: str):
#     data_to_process = {}
#     if not st.session_state.temp_dir:
#         st.session_state.temp_dir = tempfile.mkdtemp()

#     if source_option == "Local File(s)":
#         uploaded_files = st.file_uploader("Upload one or more files", accept_multiple_files=True)
#         if uploaded_files:
#             ingestor = Ingestor()
#             for uploaded_file in uploaded_files:
#                 temp_filepath = Path(st.session_state.temp_dir) / uploaded_file.name
#                 with open(temp_filepath, "wb") as f:
#                     f.write(uploaded_file.getbuffer())
#                 data_to_process.update(ingestor.ingest_file(str(temp_filepath)))
#             st.session_state.ingested_data = data_to_process

#     elif source_option == "Local Folder (Zip)":
#         uploaded_zip = st.file_uploader("Upload a `.zip` file", type=["zip"])
#         if uploaded_zip:
#             with zipfile.ZipFile(uploaded_zip, 'r') as zip_ref:
#                 zip_ref.extractall(st.session_state.temp_dir)
#             ingestor = Ingestor()
#             data_to_process = ingestor.ingest_folder(str(st.session_state.temp_dir))
#             st.session_state.ingested_data = data_to_process

#     elif source_option == "GitHub URL":
#         github_url = st.text_input("Enter public GitHub repository URL")
#         if github_url and github_url.strip():
#             ingestor = Ingestor()
#             data_to_process = ingestor.ingest_github_repo(github_url.strip())
#             for rel_path, content in data_to_process.items():
#                 file_path = Path(st.session_state.temp_dir) / rel_path
#                 file_path.parent.mkdir(parents=True, exist_ok=True)
#                 with open(file_path, "w", encoding="utf-8") as f:
#                     f.write(content)
#             st.session_state.ingested_data = data_to_process

# handle_input(source_option)

# if st.session_state.ingested_data:
#     st.success(f"✔️ Files Ingested: {len(st.session_state.ingested_data)}")

# # ==========================
# # Async Agent Runner
# # ==========================
# MAX_CONCURRENT = 2  # control concurrency vs rate limits
# semaphore = asyncio.Semaphore(MAX_CONCURRENT)

# async def safe_run(agent, payloads, name, retries=5):
#     async with semaphore:
#         for i in range(retries):
#             try:
#                 start = time.time()
#                 result = agent.analyze_batch(payloads)
#                 duration = round(time.time() - start, 2)
#                 st.write(f"✅ {name} finished in {duration}s")
#                 return {name: result}
#             except Exception as e:
#                 if "rate limit" in str(e).lower():
#                     wait = (2 ** i) + random.random()
#                     st.warning(f"⚠️ {name} rate-limited, retrying in {wait:.2f}s...")
#                     await asyncio.sleep(wait)
#                 else:
#                     st.error(f"❌ {name} failed: {e}")
#                     return {name: []}
#         return {name: []}

# async def run_all_agents(payloads):
#     agents = [
#         ("Performance", PerformanceAnalysisAgent()),
#         ("Duplication", CodeDuplicationAgent()),
#         ("Complexity", ComplexityAnalysisAgent()),
#         ("Reliability", ReliabilityAgent()),
#         ("Security", SecurityAnalysisAgent()),
#     ]
#     tasks = [asyncio.create_task(safe_run(agent, payloads, name)) for name, agent in agents]
#     return await asyncio.gather(*tasks)

# # ==========================
# # Step 2-6: Run All Agents
# # ==========================
# if st.button("Run Full Quality Analysis Workflow"):
#     file_paths = [Path(st.session_state.temp_dir) / rel_path for rel_path in st.session_state.ingested_data.keys()]
#     rag_builder = RAGPayloadBuilder()
#     st.session_state.rag_payloads = rag_builder.build_payloads(file_paths)
#     st.session_state.agent_payloads = AgentPayloadBuilder.build_payloads(file_paths)
#     st.success(f"RAG Payloads Count: {len(st.session_state.rag_payloads)}")
#     st.success(f"Agent Payloads Count: {len(st.session_state.agent_payloads)}")

#     st.info("🚀 Running quality agents concurrently with retry logic...")
#     all_results_list = []
#     agent_payloads = st.session_state.agent_payloads
#     progress_bar = st.progress(0, text="Initializing agent runs...")

#     for i, payload in enumerate(agent_payloads):
#         progress_text = f"Processing payload {i+1} of {len(agent_payloads)}..."
#         progress_bar.progress((i + 1) / len(agent_payloads), text=progress_text)
#         results_for_one_payload = asyncio.run(run_all_agents([payload]))
#         all_results_list.append(results_for_one_payload)

#     # Merge into final agent reports
#     merged_report = { "Performance": [], "Duplication": [], "Complexity": [], "Reliability": [], "Security": [] }
#     for results_for_one_payload in all_results_list:
#         for agent_result_dict in results_for_one_payload:
#             for agent_name, analysis_data in agent_result_dict.items():
#                 if agent_name in merged_report:
#                     if isinstance(analysis_data, list):
#                         merged_report[agent_name].extend(analysis_data)
#                     elif analysis_data:
#                         merged_report[agent_name].append(analysis_data)

#     st.session_state.ai_reports = merged_report
#     st.success("✅ JSON Reports Generated")

#     # Display agent reports in expanders
#     st.subheader("Generated JSON Reports per Agent")
#     for agent, issues in merged_report.items():
#         with st.expander(f"{agent} Report", expanded=False):
#             st.json(issues)

#     # Store in vector DB
#     db = VectorDB(persist_dir="vector_db")
#     if st.session_state.rag_payloads:
#         db.add_rag_payloads(st.session_state.rag_payloads)
#     if st.session_state.ai_reports:
#         db.add_ai_reports(st.session_state.ai_reports)
#     st.session_state.vector_stored = True
#     st.success("Payloads and JSON reports stored in vector DB")

#     # Final major report
#     final_agent = FinalQualityReportAgent()
#     st.session_state.final_major_report = final_agent.build_report(st.session_state.ai_reports)

#     st.subheader("📑 Final Major Report (Human Readable)")
#     st.text_area("Final Report", st.session_state.final_major_report, height=300)

# # ==========================
# # Step 7: Multi-turn RAG Chatbot
# # ==========================
# if st.session_state.vector_stored:
#     st.markdown("---")
#     st.subheader("💬 RAG Chatbot")

#     if "messages" not in st.session_state or st.session_state.messages is None:
#         st.session_state.messages = []

#     rag_agent = RAGChatbot()

#     # Display chat history
#     for msg in st.session_state.messages:
#         with st.chat_message(msg["role"]):
#             st.markdown(msg["content"])

#     if user_input := st.chat_input("Ask about the reports..."):
#         st.session_state.messages.append({"role": "user", "content": user_input})
#         with st.chat_message("user"):
#             st.markdown(user_input)

#         with st.chat_message("assistant"):
#             response = rag_agent.query(user_input, st.session_state.messages)
#             st.markdown(response)

#         st.session_state.messages.append({"role": "assistant", "content": response})


# ==========================
# app.py (Updated with Chat UI + Expanders)
# ==========================
import streamlit as st
import os, shutil, tempfile, zipfile, stat, json, asyncio, random, time
from pathlib import Path

from ingestion.ingestor import Ingestor
from builder.rag_payload_builder import RAGPayloadBuilder
from builder.agent_payload_builder import AgentPayloadBuilder
from utils.vector_store import VectorDB
from agents.performance_analysis_agent import PerformanceAnalysisAgent
from agents.code_duplication_agent import CodeDuplicationAgent
from agents.complexity_analysis_agent import ComplexityAnalysisAgent
from agents.reliability_fault_tolerence_agent import ReliabilityAgent
from agents.security_analysis_agent import SecurityAnalysisAgent
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
for key in [
    "ingested_data", "temp_dir", "rag_payloads", "agent_payloads",
    "ai_reports", "final_major_report", "vector_stored",
    "chat_history", "messages"
]:
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
# Async Agent Runner
# ==========================
MAX_CONCURRENT = 2  # control concurrency vs rate limits
semaphore = asyncio.Semaphore(MAX_CONCURRENT)

async def safe_run(agent, payloads, name, retries=5):
    async with semaphore:
        for i in range(retries):
            try:
                start = time.time()
                result = agent.analyze_batch(payloads)
                duration = round(time.time() - start, 2)
                st.write(f"✅ {name} finished in {duration}s")
                return {name: result}
            except Exception as e:
                if "rate limit" in str(e).lower():
                    wait = (2 ** i) + random.random()
                    st.warning(f"⚠️ {name} rate-limited, retrying in {wait:.2f}s...")
                    await asyncio.sleep(wait)
                else:
                    st.error(f"❌ {name} failed: {e}")
                    return {name: []}
        return {name: []}

async def run_all_agents(payloads):
    agents = [
        ("Performance", PerformanceAnalysisAgent()),
        ("Duplication", CodeDuplicationAgent()),
        ("Complexity", ComplexityAnalysisAgent()),
        ("Reliability", ReliabilityAgent()),
        ("Security", SecurityAnalysisAgent()),
    ]
    tasks = [asyncio.create_task(safe_run(agent, payloads, name)) for name, agent in agents]
    return await asyncio.gather(*tasks)

# ==========================
# Step 2-6: Run All Agents
# ==========================
if st.button("Run Full Quality Analysis Workflow"):
    file_paths = [Path(st.session_state.temp_dir) / rel_path for rel_path in st.session_state.ingested_data.keys()]
    rag_builder = RAGPayloadBuilder()
    st.session_state.rag_payloads = rag_builder.build_payloads(file_paths)
    st.session_state.agent_payloads = AgentPayloadBuilder.build_payloads(file_paths)
    st.success(f"RAG Payloads Count: {len(st.session_state.rag_payloads)}")
    st.success(f"Agent Payloads Count: {len(st.session_state.agent_payloads)}")

    st.info("🚀 Running quality agents concurrently with retry logic...")
    all_results_list = []
    agent_payloads = st.session_state.agent_payloads
    progress_bar = st.progress(0, text="Initializing agent runs...")

    for i, payload in enumerate(agent_payloads):
        progress_text = f"Processing payload {i+1} of {len(agent_payloads)}..."
        progress_bar.progress((i + 1) / len(agent_payloads), text=progress_text)
        results_for_one_payload = asyncio.run(run_all_agents([payload]))
        all_results_list.append(results_for_one_payload)

    # Merge into final agent reports
    merged_report = { "Performance": [], "Duplication": [], "Complexity": [], "Reliability": [], "Security": [] }
    for results_for_one_payload in all_results_list:
        for agent_result_dict in results_for_one_payload:
            for agent_name, analysis_data in agent_result_dict.items():
                if agent_name in merged_report:
                    if isinstance(analysis_data, list):
                        merged_report[agent_name].extend(analysis_data)
                    elif analysis_data:
                        merged_report[agent_name].append(analysis_data)

    st.session_state.ai_reports = merged_report
    st.success("✅ JSON Reports Generated")

    # Display agent reports in expanders
    st.subheader("Generated JSON Reports per Agent")
    for agent, issues in merged_report.items():
        with st.expander(f"{agent} Report", expanded=False):
            st.json(issues)

    # Store in vector DB
    db = VectorDB(persist_dir="vector_db")
    if st.session_state.rag_payloads:
        db.add_rag_payloads(st.session_state.rag_payloads)
    if st.session_state.ai_reports:
        db.add_ai_reports(st.session_state.ai_reports)
    st.session_state.vector_stored = True
    st.success("Payloads and JSON reports stored in vector DB")

    # Final major report
    final_agent = FinalQualityReportAgent()
    st.session_state.final_major_report = final_agent.build_report(st.session_state.ai_reports)

    st.subheader("📑 Final Major Report (Human Readable)")
    st.text_area("Final Report", st.session_state.final_major_report, height=300)

# ==========================
# Step 7: Multi-turn RAG Chatbot
# ==========================
if st.session_state.vector_stored:
    st.markdown("---")
    st.subheader("💬 RAG Chatbot")

    if "messages" not in st.session_state or st.session_state.messages is None:
        st.session_state.messages = []

    rag_agent = RAGChatbot()

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if user_input := st.chat_input("Ask about the reports..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            response = rag_agent.query(user_input, st.session_state.messages)
            st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})
