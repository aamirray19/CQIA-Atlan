from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.docstore.document import Document
from groq import Groq
import os
from dotenv import load_dotenv


load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

class RAGChatbot:
    def __init__(self, vector_db_dir="vector_db", model="openai/gpt-oss-20b"):
        # Two separate vector stores
        self.rag_store = Chroma(
            persist_directory=vector_db_dir,
            embedding_function=embeddings,
            collection_name="rag_payloads"
        )
        self.report_store = Chroma(
            persist_directory=vector_db_dir,
            embedding_function=embeddings,
            collection_name="ai_agent_reports"
        )
        self.model = model

    def query(self, user_query, chat_history=None, k=5):
        """
        Multi-turn query:
        - chat_history: list of {"role": "user"/"assistant", "content": str}
        """
        if chat_history is None:
            chat_history = []

        # Retrieve top-k docs from both vector stores
        rag_docs = self.rag_store.similarity_search(user_query, k=k)
        report_docs = self.report_store.similarity_search(user_query, k=k)
        all_docs = rag_docs + report_docs

        context_text = "\n".join([doc.page_content for doc in all_docs])

        # Construct messages with chat history
        messages = [{"role": "system", "content":
                     f"You are a helpful code assistant. Use the context from the codebase and AI reports to answer questions.\nContext:\n{context_text}"}]

        # Append previous conversation
        messages.extend(chat_history)

        # Add the current user query
        messages.append({"role": "user", "content": user_query})

        # Groq API call
        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0
        )

        try:
            answer = response.choices[0].message.content
        except Exception:
            answer = "Failed to generate answer."

        return answer

