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
# Reliability & Fault Tolerance Agent
# ------------------------
class ReliabilityAgent:
    """
    Analyze code reliability and fault tolerance issues across multiple payloads and store results in memory.
    """

    def __init__(self, model="openai/gpt-oss-20b"):
        self.client = client
        self.model = model
        self.report = []  # store results in-memory

    def analyze_batch(self, payloads: list):
        """
        Analyze multiple payloads to detect reliability and fault tolerance issues.
        """
        system_prompt = """
        You are a reliability and fault tolerance analysis agent.
        You will receive a JSON payload containing metadata, raw code, and optional AST.
        Detect potential reliability or fault tolerance issues, such as:
        - Missing exception handling
        - Unsafe resource usage (e.g., file/db/network without proper cleanup)
        - Missing input validation
        - Operations that may crash under edge cases
        - Single points of failure
        
        Output a STRICTLY valid JSON array of issues. Each issue must have:
        - agent: reliability and fault tolerance
        - location (file path + function/class name)
        - error_description (describe the reliability/fault tolerance problem)
        - fix_suggestion (how to improve fault tolerance/reliability)
        - severity (Low, Medium, High, Critical)
        - explanation (why this is a reliability concern)
        
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
        Return the cumulative reliability/fault tolerance report stored in memory.
        """
        return self.report

# ------------------------
# Example Usage
# ------------------------
if __name__ == "__main__":
    agent = ReliabilityAgent()

    test_payloads = [
        {
            "file_path": "C:\\Users\\aamir\\main.py",
            "type": "function",
            "name": "process_data",
            "lines_of_code": 10,
            "raw_code": """def process_data(data):
    total = 0
    for i in data:
        total += i
    return total""",
            "ast_dump": "FunctionDef(name='process_data', ...)",
            "language": ".py"
        },
        {
            "file_path": "C:\\Users\\aamir\\utils.py",
            "type": "function",
            "name": "save_file",
            "lines_of_code": 5,
            "raw_code": """def save_file(filename, data):
    f = open(filename, "w")
    f.write(data)
    f.close()""",
            "ast_dump": "FunctionDef(name='save_file', ...)",
            "language": ".py"
        }
    ]

    # Analyze batch of payloads
    agent.analyze_batch(test_payloads)

    # Get final report in memory
    final_report = agent.get_final_report()

    # Print nicely formatted JSON
    print("Final Reliability & Fault Tolerance Report:", json.dumps(final_report, indent=2))
