import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def generate_suggestions(documentation, project_name="Project"):
    """Generate AI-powered improvement suggestions only for existing code/files."""

    API_URL = "https://openrouter.ai/api/v1/chat/completions"

    if not OPENROUTER_API_KEY:
        return "Error: Missing OpenRouter API Key. Please check your .env file."

    HEADERS = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""
    You are a senior software architect and code reviewer.

    Analyze ONLY the **existing files and code** from the following project. 
    Do **not** suggest creating new files, modules, or folders.

     Provide structured improvement suggestions for:
    - Code Efficiency
    - Security
    - Maintainability
    - Scalability
    - Best Practices

    For each improvement:
    -  **Mention the file name** (must already exist)
    -  **Mention the function or section (if applicable)**
    -  **Describe what is wrong**
    -  **Provide improved code (if possible)**

     If you have future ideas or feature suggestions for the entire project (not the best practices), list them separately under:
    **"💡 Additional Notes "**

    ---
    **Project Name:** {project_name}

    **Existing Project Documentation:**
    ```
    {documentation}
    ```

    ---
    Format your response in **Markdown** with proper headings and code blocks.
    """

    data = {
        "model": "qwen/qwen-2.5-coder-32b-instruct:free",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4096,
        "temperature": 0.2
    }

    try:
        response = requests.post(API_URL, headers=HEADERS, json=data)
        response_data = response.json()

        print(f"📡 OpenRouter API Response: {response.status_code} - {response.text}")

        if response.status_code != 200 or "choices" not in response_data:
            return f"Error: OpenRouter API failed with status {response.status_code} - {response.text}"

        return response_data["choices"][0]["message"]["content"].strip()

    except Exception as e:
        print(f"❌ ERROR in generate_suggestions: {str(e)}")
        return f"Error: {str(e)}"
