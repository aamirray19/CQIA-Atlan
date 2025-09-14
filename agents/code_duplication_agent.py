from groq import Groq
import os
import json
from dotenv import load_dotenv

# ------------------------
# Load API Key
# ------------------------
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ------------------------
# Code Duplication Agent
# ------------------------
class CodeDuplicationAgent:
    """
    Analyze code duplication across multiple payloads and store results in memory.
    """

    def __init__(self, model="openai/gpt-oss-20b"):
        self.client = client
        self.model = model
        self.report = []  # store results in-memory

    def analyze_batch(self, payloads: list):
        """
        Analyze multiple payloads at once to detect code duplication across them.
        """
        system_prompt = """
        You are a code duplication detection agent. 
        You will receive a JSON payload containing metadata, raw code, and optional AST. 
        Your task is to identify code that is duplicated or highly similar within the project, which could affect maintainability and readability.

        Detect issues such as:
        - Functions, methods, or classes that are almost identical
        - Repeated blocks of code with minor variations
        - Redundant logic that could be refactored into reusable components

        Output a STRICTLY valid JSON array of issues. Each issue must include:
        - agent: code duplication
        - location: file path + function/class name where the duplication occurs
        - duplicate_of: if possible, indicate the file/function/class this is similar to
        - error_description: describe why this code is considered duplicated or redundant
        - fix_suggestion: suggest how to refactor or remove duplication
        - severity: Low, Medium, High
        - explanation: a short reasoning why this duplication is a problem

        Only add high and critical issues, avoid noise.
        Make the output concise and to the point to save tokens.
        If no issues are detected, output [].
        Don't add more than 10 issues.
        Strictly avoid any extra text outside the JSON array.
        """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(payloads, indent=2)}
            ],
            temperature=0
        )

        # Parse LLM response
        try:
            result = json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            result = []

        # Append to in-memory report
        self.report.extend(result)
        return result

    def get_final_report(self):
        """
        Return the cumulative report stored in memory.
        """
        return self.report

# ------------------------
# Example Usage
# ------------------------
if __name__ == "__main__":
    agent = CodeDuplicationAgent()

    # Two payloads with similar code to test duplication detection
    test_payloads = [
        {
            "file_path": "C:\\Users\\aamir\\main.py",
            "type": "function",
            "name": "get_db_connection",
            "lines_of_code": 8,
            "raw_code": """def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "db"),
        database=os.getenv("DB_NAME", "speeddb"),
        user=os.getenv("DB_USER", "speeduser"),
        password=os.getenv("DB_PASS", "speedpass")
    )""",
            "ast_dump": "FunctionDef(name='get_db_connection', ...)",
            "language": ".py"
        },
        {
            "file_path": "C:\\Users\\aamir\\utils.py",
            "type": "function",
            "name": "connect_db",
            "lines_of_code": 8,
            "raw_code": """def connect_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "db"),
        database=os.getenv("DB_NAME", "speeddb"),
        user=os.getenv("DB_USER", "speeduser"),
        password=os.getenv("DB_PASS", "speedpass")
    )""",
            "ast_dump": "FunctionDef(name='connect_db', ...)",
            "language": ".py"
        }
    ]

    # Analyze the batch of payloads
    agent.analyze_batch(test_payloads)

    # Get the final in-memory report
    final_report = agent.get_final_report()

    # Print nicely formatted JSON
    print("Final Code Duplication Report:", json.dumps(final_report, indent=2))
