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
# General Quality Analysis Agent
# ------------------------
class QualityAnalysisAgent:
    """
    Analyze code for multiple quality aspects:
    - Security
    - Performance
    - Reliability & Fault Tolerance
    - Code Duplication
    - Complexity

    Outputs a single JSON array of issues, each issue has:
    - agent
    - location
    - error_description / issue_description
    - fix_suggestion / improvement_suggestion
    - severity
    - explanation
    """

    def __init__(self, model="openai/gpt-oss-20b"):
        self.client = client
        self.model = model
        self.report = []  # all issues appended here

    def analyze_batch(self, payloads: list):
        """
        Analyze multiple payloads and append issues to the report.
        """
        system_prompt = """
        You are a general code quality analysis agent. Analyze the incoming JSON payloads for:

        1. Security:
            - High/Critical vulnerabilities (hardcoded secrets, SQL injection, unsafe eval/exec)
            - agent: security
            - location, error_description, fix_suggestion, severity, explanation

        2. Performance:
            - Inefficient patterns that degrade performance
            - agent: performance
            - location, issue_description, improvement_suggestion, severity, explanation

        3. Reliability & Fault Tolerance:
            - Patterns leading to crashes or poor fault tolerance
            - agent: reliability
            - location, issue_description, fix_suggestion, severity, explanation

        4. Code Duplication:
            - Repeated code fragments/functions
            - agent: code_duplication
            - location, duplicated_code, suggestion, severity, explanation

        5. Complexity:
            - Overly complex functions/classes (high cyclomatic complexity)
            - agent: complexity
            - location, issue_description, suggestion, severity, explanation

        IMPORTANT:
        - Return a SINGLE JSON ARRAY with all issues combined.
        - Each issue object MUST have the fields: agent, location, error_description/issue_description, fix_suggestion/improvement_suggestion, severity, explanation.
        - Limit each category to 2 issues max.
        - If no issues, return an empty array.
        - Do not add any extra text outside the JSON.
        """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(payloads, indent=2)}
            ],
            temperature=0
        )

        try:
            result = json.loads(response.choices[0].message.content)
            if isinstance(result, list):
                self.report.extend(result)
        except (json.JSONDecodeError, AttributeError):
            # If parsing fails, keep empty report
            pass

        return self.report

    def get_final_report(self):
        """
        Return the cumulative JSON array of all issues.
        """
        return self.report


# ------------------------
# Example Usage
# ------------------------
if __name__ == "__main__":
    agent = QualityAnalysisAgent()

    test_payloads = [
        {
            "file_path": "main.py",
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
        },
        {
            "file_path": "utils.py",
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

    agent.analyze_batch(test_payloads)
    print(json.dumps(agent.get_final_report(), indent=2))
