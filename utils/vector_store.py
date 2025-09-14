# utils/vector_store.py
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.docstore.document import Document
from typing import List, Dict, Any
import os
import json

# Initialize embeddings (free, open-source)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")


class VectorDB:
    def __init__(self, persist_dir="vector_db"):
        self.persist_dir = persist_dir

        # Chroma instances for each namespace
        self.rag_store = Chroma(
            persist_directory=persist_dir,
            embedding_function=embeddings,
            collection_name="rag_payloads"
        )
        self.report_store = Chroma(
            persist_directory=persist_dir,
            embedding_function=embeddings,
            collection_name="ai_agent_reports"
        )

    def add_rag_payloads(self, payloads: List[Dict[str, Any]]):
        """
        payloads: list of dicts from RAGPayloadBuilder
        """
        docs = [
            Document(
                page_content=p.get("raw_code", ""),  # use raw_code instead of 'content'
                metadata={"name": p.get("name"), "file_path": p.get("file_path")}
            )
            for p in payloads if "raw_code" in p
        ]
        if docs:
            self.rag_store.add_documents(docs)
            self.rag_store.persist()

    def add_ai_reports(self, reports: Dict[str, List[Dict[str, Any]]]):
        """
        reports: dict of agent_name -> report_list
        """
        docs = []
        for agent_name, report_list in reports.items():
            for i, r in enumerate(report_list):
                docs.append(
                    Document(
                        page_content=json.dumps(r),
                        metadata={"agent": agent_name, "index": i}
                    )
                )
        if docs:
            self.report_store.add_documents(docs)
            self.report_store.persist()

    def query_rag(self, query: str, k: int = 5):
        return self.rag_store.similarity_search(query, k=k)

    def query_reports(self, query: str, k: int = 5):
        return self.report_store.similarity_search(query, k=k)

    def clear_all(self):
        """Clears all documents in both namespaces."""
        self.rag_store.delete_collection()
        self.report_store.delete_collection()
        self.rag_store.persist()
        self.report_store.persist()