from groq import Groq
import os
import json
from dotenv import load_dotenv


load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


class PerformanceAnalysisAgent:
    """
    Analyze code performance issues across multiple payloads and store results in memory.
    """

    def __init__(self, model="openai/gpt-oss-20b"):
        self.client = client
        self.model = model
        self.report = []  

    def analyze_batch(self, payloads: list):
        """
        Analyze multiple payloads at once to detect performance issues.
        """
        system_prompt = """
        You are a performance analysis agent.
        You will receive a JSON payload containing metadata, raw code, and optional AST.
        Detect potential performance issues in the code, such as:
        - Inefficient loops or nested loops
        - Repeated database or network calls
        - Memory-heavy operations or large temporary objects
        - Poor algorithm choices (e.g., O(n^2) where O(n) possible)
        - Unnecessary computations or redundant code
        - Or any other Performance issues
        
        Output a STRICTLY valid JSON array of issues. Each issue must have:
        - agent: performance
        - location (file path + function/class name)
        - error_description (describe the performance problem)
        - fix_suggestion (how to optimize/refactor)
        - severity (Low, Medium, High, Critical)
        - explanation (why this is a performance concern)
        
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
        Return the cumulative performance report stored in memory.
        """
        return self.report
