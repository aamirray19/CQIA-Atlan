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
# Security Analysis Agent
# ------------------------
class SecurityAnalysisAgent:
    """
    Analyze code security vulnerabilities across multiple payloads and store results in memory.
    """

    def __init__(self, model="openai/gpt-oss-20b"):
        self.client = client
        self.model = model
        self.report = []  # store results in-memory

    def analyze_batch(self, payloads: list):
        """
        Analyze multiple payloads at once to detect security issues.
        """
        system_prompt = """
        You are a security analysis agent.
        You will receive a JSON payload containing metadata, raw code, and optional AST.
        Detect potential security vulnerabilities in the code, such as:
        - Hardcoded secrets or credentials
        - SQL injection or unsafe database queries
        - Command injection or unsafe eval/exec usage
        - Insecure use of external libraries
        - Missing input validation or improper sanitization
        
        Output a STRICTLY valid JSON array of issues. Each issue must have:
        - agent: security
        - location (file path + function/class name)
        - error_description (describe the security issue)
        - fix_suggestion (how to remediate or secure the code)
        - severity (Low, Medium, High, Critical)
        - explanation (why this is a security concern)

        Only add high and critical issues, avoid noise.
        Make the output concise and to the point to save tokens.
        If no issues are detected, output [].
        Don't add more than 5 issues.
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
        Return the cumulative security report stored in memory.
        """
        return self.report

# ------------------------
# Example Usage
# ------------------------
if __name__ == "__main__":
    agent = SecurityAnalysisAgent()

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
            "name": "save_password",
            "lines_of_code": 5,
            "raw_code": """def save_password(password):
    with open("passwords.txt", "a") as f:
        f.write(password)""",
            "ast_dump": "FunctionDef(name='save_password', ...)",
            "language": ".py"
        }
    ]

    # Analyze batch of payloads
    agent.analyze_batch(test_payloads)

    # Get final report in memory
    final_report = agent.get_final_report()

    # Print nicely formatted JSON
    print("Final Security Report:", json.dumps(final_report, indent=2))
