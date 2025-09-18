from groq import Groq
import os
import json
from dotenv import load_dotenv


load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


class ReliabilityAgent:
    """
    Analyze code reliability and fault tolerance issues across multiple payloads and store results in memory.
    """

    def __init__(self, model="openai/gpt-oss-20b"):
        self.client = client
        self.model = model
        self.report = []  

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

        # Append to report
        self.report.extend(result)
        return result

    def get_final_report(self):
        """
        Return the cumulative reliability/fault tolerance report stored in memory.
        """
        return self.report
