from pathlib import Path
from typing import List, Dict, Any

class RAGPayloadBuilder:
    """
    Builds a simple RAG payload for any given file.
    Each payload contains the file's metadata and its full raw code content,
    making it suitable for ingestion into a vector database.
    This builder treats every file as a single document, regardless of language.
    """

    def __init__(self):
        """Initializes the RAGPayloadBuilder."""
        pass


    def build_payloads(self, files: List[Path]) -> List[Dict[str, Any]]:
        """
        Processes a list of files and generates a flat list of RAG payloads.
        Each file is treated as a single document.
        """
        payloads = []
        for file_path in files:
            if not file_path.is_file():
                continue

            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception as e:
                payloads.append({
                    "file_path": str(file_path),
                    "error": f"File read error: {e}"
                })
                continue

            payloads.append({
                "file_path": str(file_path),
                "type": "file",
                "name": file_path.name,
                "lines_of_code": len(content.splitlines()),
                "raw_code": content,
                "language": file_path.suffix.lower(),
            })
        
        return payloads
