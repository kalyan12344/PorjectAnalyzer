import os
import json
import requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import markdown2
import pdfkit
from suggestions import generate_suggestions

load_dotenv()

# Configuration
WKHTMLTOPDF_PATH = r"C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe"
config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True, methods=["GET", "POST", "OPTIONS"])

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GITHUB_API_TOKEN = os.getenv("GITHUB_API_TOKEN")

# Helper Functions

def generate_documentation(code_files, project_name, is_frontend, is_backend, dependencies):
    """Generate Markdown documentation using AI"""
    API_URL = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    # Build prompt
    overview = ""
    if is_frontend:
        overview += "- 🖥️ **Frontend**: Detected (React/Vue/Next.js)\n"
    if is_backend:
        overview += "- ⚙️ **Backend**: Detected (Python/Node/Java)\n"
    if dependencies:
        overview += f"- 📦 Dependencies: {', '.join(dependencies)}\n"

    structure = "\n".join(
        f"- `{file['filename']}`: "
        f"{'React Component' if file['filename'].endswith(('.jsx', '.tsx')) else 'Vue Component' if file['filename'].endswith('.vue') else 'Next.js Page' if 'pages' in file['filename'] else 'Express.js Route Handler' if file['filename'].endswith('.js') and is_backend else 'Python Service' if file['filename'].endswith('.py') and is_backend else 'Java Service' if file['filename'].endswith('.java') and is_backend else 'Database Configuration' if file['filename'].endswith(('.sql', '.yaml')) else 'Configuration File' if file['filename'].endswith(('.json', '.ini', '.toml')) else 'Utility Module' if file['filename'].endswith('.js') or file['filename'].endswith('.py') else 'File'}"
        f" - {file['summary'] if 'summary' in file else 'No description provided'}"
        f"{' (Key File)' if 'key_file' in file and file['key_file'] else ''}"
        for file in code_files
    )
    

    samples = "\n".join(
        f"### {file['filename']}\n```\n{file['content']}\n```"
        for file in code_files[:5]
    )

    prompt = f"""
    You are a professional technical writer tasked with creating comprehensive and detailed technical documentation for the project '{project_name}'.

    **Project Overview:**
    Provide a detailed overview of the project's purpose, goals, and functionality.

    **Target Audience:** Developers and technical team members.

    **Desired Output Structure (Markdown):**

    # Project: {project_name}

    ## 1. Introduction
    Provide a brief introduction.

    ## 2. Project Overview
    {overview}
    Describe the project's purpose, features, and functionality in detail.

    ## 3. Architecture
    Explain the project's architecture, including the relationship between frontend and backend components.

    ## 4. Key Components
    Describe the key components of the project, including:
    {structure}
    Provide code examples for the most important components:
    {samples}

    ## 5. API Endpoints (If Applicable)
    If the project has an API, describe the endpoints, request/response formats, and authentication methods.

    ## 6. Database Schema (If Applicable)
    If the project uses a database, describe the schema and relationships.

    ## 7. Setup Instructions
    Provide detailed instructions on how to set up the project, including environment setup and dependency installation.

    ## 8. Dependencies
    List all dependencies and their versions.

    ## 9. Conclusion
    Summarize the project and its key aspects.

    **Instructions:**

    - Use Markdown formatting for the entire document.
    - Include code examples in Markdown code blocks.
    - Provide detailed explanations and technical details.
    - Focus on the key aspects of the project that developers need to know.
    - Use a clear and concise writing style.
    - Be detailed and informative.
    - If a section is not applicable, mention that it is not applicable.
    """

    data = {
        "model": "qwen/qwen2.5-vl-3b-instruct:free",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4000,
        "temperature": 0.3
    }

    try:
        response = requests.post(API_URL, headers=headers, json=data)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error generating documentation: {str(e)}"

def get_default_branch(repo_name):
    headers = {"Authorization": f"token {GITHUB_API_TOKEN}"}
    response = requests.get(f"https://api.github.com/repos/{repo_name}", headers=headers)
    if response.status_code == 200:
        return response.json().get("default_branch", "main")
    return "main"

def fetch_github_repo_contents(repo_name, path=""):
    headers = {"Authorization": f"token {GITHUB_API_TOKEN}"}
    contents_url = f"https://api.github.com/repos/{repo_name}/contents/{path}"
    response = requests.get(contents_url, headers=headers)

    if response.status_code == 403:
        raise Exception("GitHub API rate limit exceeded or token is invalid.")
    elif response.status_code != 200:
        raise Exception(f"Failed to fetch GitHub contents: {response.status_code} - {response.text}")

    items = response.json()
    all_files = []

    for item in items:
        if isinstance(item, dict):
            if item.get("type") == "file":
                all_files.append({
                    "path": f"{path}/{item['name']}" if path else item["name"],
                    "name": item["name"],
                    "type": "file"
                })
            elif item.get("type") == "dir":
                all_files.extend(fetch_github_repo_contents(
                    repo_name,
                    f"{path}/{item['name']}" if path else item["name"]
                ))

    return all_files

def detect_project_type(files):
    frontend_exts = ('.jsx', '.tsx', '.vue', '.svelte')
    backend_exts = ('.py', '.java', '.go', '.rb')

    is_frontend = any(
        f["name"].endswith(frontend_exts) or
        f["name"] in ('vite.config.js', 'next.config.js')
        for f in files
    )

    is_backend = any(
        f["name"].endswith(backend_exts) or
        f["name"] in ('requirements.txt', 'pom.xml')
        for f in files
    )

    return is_frontend, is_backend

def extract_code_files(repo_name, all_files, default_branch="main", max_chars=2000):
    code_exts = ('.py', '.js', '.java', '.jsx', '.ts', '.tsx', '.vue')
    code_files = []
    for file in all_files:
        if file["type"] == "file" and file["name"].endswith(code_exts):
            raw_url = f"https://raw.githubusercontent.com/{repo_name}/{default_branch}/{file['path']}"
            file_content = requests.get(raw_url).text
            code_files.append({
                "filename": file["path"],
                "content": file_content[:max_chars],
                "language": file["name"].split('.')[-1]
            })
    return code_files

@app.route("/generate-docs", methods=["POST"])
def generate_docs():
    try:
        data = request.json
        repo_url = data.get("repo_url")
        if not repo_url:
            return jsonify({"error": "No GitHub repo URL provided"}), 400

        repo_name = repo_url.replace("https://github.com/", "").strip("/")
        default_branch = get_default_branch(repo_name)
        all_files = fetch_github_repo_contents(repo_name)
        code_files = extract_code_files(repo_name, all_files, default_branch)

        is_frontend, is_backend = detect_project_type(all_files)

        dependencies = []
        if any(f["name"] == "package.json" for f in all_files):
            raw_url = f"https://raw.githubusercontent.com/{repo_name}/{default_branch}/package.json"
            response = requests.get(raw_url)
            if response.status_code == 200:
                try:
                    dependencies = list(json.loads(response.text).get("dependencies", {}).keys())
                except json.JSONDecodeError:
                    pass

        documentation = generate_documentation(
            code_files,
            repo_name.split("/")[-1],
            is_frontend,
            is_backend,
            dependencies
        )

        return jsonify({
            "message": "Documentation generated",
            "documentation": documentation,
            "structure": all_files
        })

    except Exception as e:
        print(f"\u274c ERROR: {str(e)}")
        return jsonify({"error": str(e)}), 500

# generate_documentation() stays unchanged

@app.route("/generate-suggestions", methods=["POST", "OPTIONS"])
def generate_suggestions_route():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200
    return handle_suggestions()

def handle_suggestions():
    try:
        data = request.json
        repo_url = data.get("repo_url")
        if not repo_url:
            return jsonify({"error": "No GitHub repo URL provided"}), 400

        repo_name = repo_url.replace("https://github.com/", "").strip("/")
        default_branch = get_default_branch(repo_name)
        all_files = fetch_github_repo_contents(repo_name)
        code_files = extract_code_files(repo_name, all_files, default_branch)

        suggestions = generate_suggestions(code_files, repo_name.split("/")[-1])
        return jsonify({
            "message": "Suggestions generated",
            "suggestions": suggestions
        })

    except Exception as e:
        print(f"\u274c Suggestion Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/generate-pdf", methods=["POST"])
def generate_pdf():
    try:
        data = request.json
        documentation = data.get("documentation", "")
        project_name = data.get("project_name", "Project")

        if not documentation:
            return jsonify({"error": "No documentation provided"}), 400

        html_content = markdown2.markdown(documentation)
        pdf_filename = f"{project_name}.pdf"
        pdf_path = os.path.join(UPLOAD_FOLDER, pdf_filename)

        pdfkit.from_string(
            html_content,
            pdf_path,
            configuration=config,
            options={"enable-local-file-access": ""}
        )

        return jsonify({
            "message": "PDF generated successfully",
            "pdf_url": f"/download-pdf/{pdf_filename}"
        })

    except Exception as e:
        print(f"\u274c PDF Generation Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/download-pdf/<filename>", methods=["GET"])
def download_pdf(filename):
    pdf_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True)
    return jsonify({"error": "PDF not found"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
