from groq import Groq
import os
import json
from dotenv import load_dotenv


load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


class ComplexityAnalysisAgent:
    """
    Analyze code complexity across multiple payloads and store results in memory.
    """

    def __init__(self, model="openai/gpt-oss-20b"):
        self.client = client
        self.model = model
        self.report = []  

    def analyze_batch(self, payloads: list):
        """
        Analyze multiple payloads at once to detect complexity issues.
        """
        system_prompt = """
        You are a code complexity analysis agent. 
        You will receive a JSON payload containing metadata, raw code, and optional AST. 
        Your goal is to identify potential code complexity issues that could affect readability, maintainability, and scalability.

        Detect issues such as:
        - High cyclomatic complexity (too many if/else/switch branches)
        - Deeply nested loops or conditionals
        - Very long functions or methods
        - Excessive parameters or arguments
        - Hard-to-read logic due to poor structure
        - Repetitive or redundant code blocks

        Output a STRICTLY valid JSON array of issues. Each issue must include:
        - agent: complexity
        - location: file path + function/class name
        - error_description: explain the complexity issue in simple terms
        - fix_suggestion: suggest ways to simplify or refactor the code
        - severity: Low, Medium, High, Critical
        - explanation: a short reasoning why this is a problem
        - Or any other complexity issues

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
        Return the cumulative complexity report stored in memory.
        """
        return self.report

