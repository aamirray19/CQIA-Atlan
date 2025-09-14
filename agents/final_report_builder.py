import json
import os
from groq import Groq
from dotenv import load_dotenv

# ------------------------
# Load API Key
# ------------------------
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

class FinalQualityReportAgent:
    """
    Builds a consolidated final report from the general quality analysis agent.
    Only includes major issues (Critical or High severity).
    Uses Groq API instead of LangChain/OpenAI.
    """

    def __init__(self, model="openai/gpt-oss-20b"):
        self.model = model

    def build_report(self, agent_report: list):
        """
        agent_report: list of dicts from the general quality analysis agent
        """
        # Filter only major issues (High or Critical)
        major_issues = [issue for issue in agent_report if issue.get("severity") in ("High", "Critical")]
        if not major_issues:
            return "No major issues found."

        system_prompt = """
        You are a final report builder AI.
        You will receive JSON reports from a general quality analysis agent.
        Each report contains issues with the following fields:
        - agent (Security, Performance, Reliability, CodeDuplication, Complexity)
        - location
        - error_description
        - fix_suggestion
        - severity (Low, Medium, High, Critical)

        Your task:
        1. Include only major issues (High or Critical severity).
        2. Output in a human-readable format (not JSON).
        3. Each issue should show:
           - Issue Type
           - Location
           - Error Description
           - Suggested Fix
           - Severity

        Only include issues that could disrupt the working of the system.
        Be concise and clear.
        """

        user_prompt = json.dumps(major_issues, indent=2)

        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0
        )

        # Extract the content
        try:
            content = response.choices[0].message.content
        except (KeyError, IndexError):
            content = "Error: Unable to generate final report."

        return content


# =========================
# Example Usage
# =========================
if __name__ == "__main__":
    # Example cumulative report from general quality agent
    general_report = [
        {"agent": "Security", "location": "auth.py:12", "error_description": "Hardcoded password", "fix_suggestion": "Use environment variables", "severity": "High"},
        {"agent": "Performance", "location": "performance_utils.py:2", "error_description": "Nested loops causing O(n^2)", "fix_suggestion": "Optimize loops", "severity": "High"},
        {"agent": "Complexity", "location": "complex_utils.py:2-8", "error_description": "Deeply nested conditionals", "fix_suggestion": "Refactor to smaller functions", "severity": "High"},
        {"agent": "Reliability", "location": "network_utils.py:2-4", "error_description": "Missing error handling", "fix_suggestion": "Add try/except with retries", "severity": "Critical"},
        {"agent": "CodeDuplication", "location": "duplication_utils.py:1-8", "error_description": "Duplicate code blocks", "fix_suggestion": "Refactor into single function", "severity": "Medium"},
        {"agent": "Security", "location": "network_utils.py:3", "error_description": "SQL Injection risk", "fix_suggestion": "Use parameterized queries", "severity": "Critical"},
        {"agent": "Performance", "location": "analytics.py:15", "error_description": "Inefficient query", "fix_suggestion": "Add proper indexing", "severity": "Medium"}
    ]

    agent = FinalQualityReportAgent()
    final_report = agent.build_report(general_report)

    print("===== FINAL MAJOR ISSUES REPORT =====")
    print(final_report)
