from groq import Groq
import os
import json
from dotenv import load_dotenv


load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


class CodeDuplicationAgent:
    """
    Analyze code duplication across multiple payloads and store results in memory.
    """

    def __init__(self, model="openai/gpt-oss-20b"):
        self.client = client
        self.model = model
        self.report = []  

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
        - Or any other code duplication issues

        Output a STRICTLY valid JSON array of issues. Each issue must include:
        - agent: code duplication
        - location: file path + function/class name where the duplication occurs
        - duplicate_of: if possible, indicate the file/function/class this is similar to
        - error_description: describe why this code is considered duplicated or redundant
        - fix_suggestion: suggest how to refactor or remove duplication
        - severity: Low, Medium, High
        - explanation: a short reasoning why this duplication is a problem

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
        Return the cumulative report stored in memory.
        """
        return self.report
