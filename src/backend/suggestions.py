import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def generate_suggestions(code_files, project_name="Project"):
    """Generate AI-powered improvement suggestions with deep code analysis."""

    API_URL = "https://openrouter.ai/api/v1/chat/completions"

    if not OPENROUTER_API_KEY:
        return "Error: Missing OpenRouter API Key. Please check your .env file."

    if not code_files:
        return "Error: No code files found to analyze."

    # Combine code into readable chunks
    code_context = "\n\n".join(
        f"### File: {file['filename']} ({file.get('language', 'unknown')})\nPurpose: {file.get('summary', 'No summary provided')}\n```{file.get('language', '')}\n{file['content'][:2000]}\n```"
        for file in code_files
    )

    prompt = (
        f"You are a senior software engineer conducting a thorough code review for the '{project_name}' project. "
        f"Analyze the following files and provide detailed, actionable improvement suggestions.\n\n"
        f"**Project Context:** This project [briefly describe the project's purpose and architecture].\n\n"
        f"**File Relationships:** If files depend on each other, mention these relationships.\n\n"
        f"**Desired Output Format (Markdown):**\n"
        f"```markdown\n"
        f"## File: [filename] ([language])\n\n"
        f"### ⚠️ Security Issues\n"
        f"- [description of the issue]\n"
        f"- Affected function/section: [function/section]\n"
        f"- Suggested fix: [code snippet or explanation]\n\n"
        f"### ⚡️ Performance Issues\n"
        f"- [description of the issue]\n"
        f"- Affected function/section: [function/section]\n"
        f"- Suggested fix: [code snippet or explanation]\n\n"
        f"### 🛠️ Maintainability Issues\n"
        f"- [description of the issue]\n"
        f"- Affected function/section: [function/section]\n"
        f"- Suggested fix: [code snippet or explanation]\n\n"
        f"### ✅ Best Practices\n"
        f"- [description of the issue]\n"
        f"- Affected function/section: [function/section]\n"
        f"- Suggested fix: [code snippet or explanation]\n"
        f"```\n\n"
        f"**Instructions:**\n"
        f"- Provide detailed and actionable suggestions.\n"
        f"- Prioritize critical issues (security, performance) over minor style improvements.\n"
        f"- Use markdown formatting for clarity.\n"
        f"- Include code snippets whenever possible.\n"
        f"- Clearly label each issue with the appropriate category (Security, Performance, Maintainability, Best Practices).\n"
        f"- If a file is generally well-written, mention that and highlight any minor improvements.\n\n"
        f"**Codebase:**\n{code_context}\n\n"
    )

    data = {
        "model": "qwen/qwen2.5-vl-3b-instruct:free",
        "messages": [
            {"role": "system", "content": "You are a senior code reviewer skilled in all modern programming languages."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 4096,
        "temperature": 0.2,
        "top_p": 0.95
    }

    try:
        response = requests.post(API_URL, headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }, json=data, timeout=30)

        response.raise_for_status()
        result = response.json()

        if not result.get("choices"):
            return "Error: No analysis results returned from API"

        return result["choices"][0]["message"]["content"].strip()

    except requests.exceptions.RequestException as e:
        print(f"❌ API Request Error: {e}")
        return f"API Error: {str(e)}"
    except Exception as e:
        print(f"❌ General Error: {e}")
        return f"Analysis Error: {str(e)}"