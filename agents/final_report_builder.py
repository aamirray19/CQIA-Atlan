import json
import os
from groq import Groq
from dotenv import load_dotenv


load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

class FinalQualityReportAgent:
    """
    Builds a consolidated final report from a JSON quality analysis report.
    """

    def __init__(self, model="openai/gpt-oss-20b"):
        self.model = model

    def build_report(self, report_json: list):
        """
        report_json: list of dicts representing issues
        """
        system_prompt = """
        You are a final report builder AI.
        You will receive JSON reports with issues.
        Each issue has:
        - agent
        - location
        - error_description
        - fix_suggestion
        - severity

        Task:
        1. Include only major issues (High or Critical).
        2. Output in a human-readable format.
        3. Each issue shows:
           - Issue Type
           - Location
           - Error Description
           - Suggested Fix
           - Severity

        Return the top 10 issues sorted by severity (Critical first).
        Be concise.
        """

        user_prompt = json.dumps(report_json, indent=2)

        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0
        )

        try:
            content = response.choices[0].message.content
        except (KeyError, IndexError):
            content = "Error: Unable to generate final report."

        return content


