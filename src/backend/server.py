import os
import json
import requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from uml import generate_uml_from_code
import markdown2
import pdfkit
from suggestions import generate_suggestions

load_dotenv()
WKHTMLTOPDF_PATH = r"C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe"
config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GITHUB_API_TOKEN = os.getenv("GITHUB_API_TOKEN")

print(f"🔍 GITHUB_API_TOKEN Loaded: {os.getenv('GITHUB_API_TOKEN')}")

@app.route("/generate-suggestions", methods=["POST"])
def generate_suggestions_api():
    try:
        data = request.json
        repo_url = data.get("repo_url")
        if not repo_url:
            return jsonify({"error": "No GitHub repo URL provided"}), 400

        repo_name = repo_url.replace("https://github.com/", "").strip("/")
        headers = {"Authorization": f"token {GITHUB_API_TOKEN}"}
        contents_url = f"https://api.github.com/repos/{repo_name}/contents"
        response = requests.get(contents_url, headers=headers)

        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch repo contents"}), 500

        items = response.json()
        if not isinstance(items, list):
            return jsonify({"error": "Unexpected GitHub API structure"}), 500

        code_files = []
        for item in items:
            if isinstance(item, dict) and item.get("type") == "file" and any(item["name"].endswith(ext) for ext in [".py", ".js", ".java"]):
                raw_url = f"https://raw.githubusercontent.com/{repo_name}/main/{item['name']}"
                file_content = requests.get(raw_url).text
                code_files.append({
                    "filename": item["name"],
                    "content": file_content[:2000]
                })

        combined_code = "\n\n".join(f"### {file['filename']}\n```\n{file['content']}\n```" for file in code_files)
        suggestions = generate_suggestions(combined_code, project_name=repo_name.split("/")[-1])
        return jsonify({"message": "Suggestions generated from code", "suggestions": suggestions})

    except Exception as e:
        print(f"❌ ERROR in /generate-suggestions: {str(e)}")
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
        pdfkit.from_string(html_content, pdf_path, configuration=config)

        print(f"📄 PDF Generated: {pdf_path}")
        return jsonify({"message": "PDF generated successfully", "pdf_url": f"http://127.0.0.1:5000/download-pdf/{pdf_filename}"})

    except Exception as e:
        print(f"❌ ERROR in generate-pdf: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/download-pdf/<filename>", methods=["GET"])
def download_pdf(filename):
    pdf_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True)
    else:
        return jsonify({"error": "PDF not found"}), 404

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:5174"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

def fetch_github_repo_data(repo_url):
    repo_name = repo_url.replace("https://github.com/", "").strip("/")
    headers = {"Authorization": f"token {GITHUB_API_TOKEN}"}
    contents_url = f"https://api.github.com/repos/{repo_name}/contents"
    response = requests.get(contents_url, headers=headers)
    print("git contents", response)

    if response.status_code != 200:
        return None, f"Error fetching repository: {response.status_code} - {response.text}"

    items = response.json()
    if not isinstance(items, list):
        return None, "GitHub API did not return expected list"

    file_structure = [{"name": item.get("name", ""), "type": item.get("type", "")} for item in items]
    all_files = [item["name"] for item in file_structure if item["type"] == "file"]

    languages_url = f"https://api.github.com/repos/{repo_name}/languages"
    response = requests.get(languages_url, headers=headers)
    languages = list(response.json().keys()) if response.status_code == 200 else ["Unknown"]

    dependencies = []
    if "package.json" in all_files:
        package_url = f"https://raw.githubusercontent.com/{repo_name}/main/package.json"
        response = requests.get(package_url, headers=headers)
        if response.status_code == 200:
            package_data = json.loads(response.text)
            dependencies = list(package_data.get("dependencies", {}).keys())

    elif "requirements.txt" in all_files:
        req_url = f"https://raw.githubusercontent.com/{repo_name}/main/requirements.txt"
        response = requests.get(req_url, headers=headers)
        if response.status_code == 200:
            dependencies = response.text.splitlines()

    return {
        "project_name": repo_name.split("/")[-1],
        "language": languages,
        "structure": file_structure,
        "dependencies": dependencies
    }, None

def extract_metadata(project_folder):
    project_info = {
        "project_name": os.path.basename(project_folder),
        "language": "Unknown",
        "structure": [],
        "dependencies": []
    }

    all_files = []
    for root, _, files in os.walk(project_folder):
        relative_path = os.path.relpath(root, project_folder)
        project_info["structure"].append({"folder": relative_path, "files": files})
        all_files.extend(files)

    extensions = {".py": "Python", ".js": "JavaScript", ".java": "Java", ".jsx": "JavaScript"}
    detected_languages = set(ext for file in all_files for ext, lang in extensions.items() if file.endswith(ext))
    project_info["language"] = list(detected_languages) if detected_languages else ["Unknown"]

    if "package.json" in all_files:
        with open(os.path.join(project_folder, "package.json"), "r") as f:
            try:
                package_data = json.load(f)
                project_info["dependencies"] = list(package_data.get("dependencies", {}).keys())
            except json.JSONDecodeError:
                project_info["dependencies"] = ["Error reading package.json"]
    elif "requirements.txt" in all_files:
        with open(os.path.join(project_folder, "requirements.txt"), "r") as f:
            project_info["dependencies"] = f.read().splitlines()

    return project_info

def generate_documentation(code_files, project_name="Project"):
    API_URL = "https://openrouter.ai/api/v1/chat/completions"
    if not OPENROUTER_API_KEY:
        return "Error: Missing OpenRouter API Key. Please check your .env file."

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""
You are a professional technical writer and software engineer.

Your task is to read the following source code files and generate a comprehensive **GitHub-style README** in **Markdown**.

Follow this format:

# {project_name}

## 🔍 Overview
- Describe what the project does in simple language.
- Mention key technologies used.
- Identify the purpose or user problem it solves.

## ⚙️ Installation
- Write precise steps to clone, install dependencies, and run the app.

## 📁 Project Structure
- List key folders/files and what they do.
- Explain components, hooks, services, or utilities found.

## 🚀 Features
- Mention any UI behavior, form handling, API calls, or validations.
- Focus on actual app logic, not tools.

## 🧪 Testing
- If there's a test framework or sample test, explain how to run tests.

## 📦 Technologies Used
- Only list tools used **once** (like React, ESLint, Vite, Tailwind).

## 🧠 Developer Notes
- Add any assumptions or developer-facing notes found in the code.

---

### Code Files (trimmed to 2000 characters each):
"""
    for file in code_files:
        prompt += f"\n#### {file['filename']}\n```js\n{file['content'][:2000]}\n```\n"

    prompt += "\nOnly output a Markdown README. Avoid repetition. Focus on real functionality if found."

    data = {
        "model": "qwen/qwen2.5-vl-32b-instruct:free",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4096,
        "temperature": 0.2
    }

    try:
        response = requests.post(API_URL, headers=headers, json=data)
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()

    except Exception as e:
        return f"Error generating documentation: {str(e)}"

@app.route("/generate-docs", methods=["OPTIONS", "POST"])
def generate_docs():
    try:
        if request.method == "OPTIONS":
            response = jsonify({"message": "CORS preflight successful"})
            response.headers["Access-Control-Allow-Origin"] = "http://localhost:5174"
            response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            response.headers["Access-Control-Allow-Credentials"] = "true"
            return response, 200

        if "files" in request.files:
            uploaded_files = request.files.getlist("files")
            project_folder = os.path.join(UPLOAD_FOLDER, "project")
            os.makedirs(project_folder, exist_ok=True)

            for file in uploaded_files:
                file_path = os.path.join(project_folder, file.filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                file.save(file_path)

            metadata = extract_metadata(project_folder)
            code_files = []
            for root, _, files in os.walk(project_folder):
                for name in files:
                    if name.endswith((".py", ".js", ".java")):
                        full_path = os.path.join(root, name)
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                            code_files.append({"filename": name, "content": f.read()})
        else:
            data = request.json
            repo_url = data.get("repo_url")
            if not repo_url:
                return jsonify({"error": "No input provided"}), 400

            metadata, error = fetch_github_repo_data(repo_url)
            if error:
                return jsonify({"error": error}), 500

            repo_name = repo_url.replace("https://github.com/", "").strip("/")
            headers = {"Authorization": f"token {GITHUB_API_TOKEN}"}
            contents_url = f"https://api.github.com/repos/{repo_name}/contents"
            response = requests.get(contents_url, headers=headers)
            items = response.json()
            code_files = []
            for item in items:
                if isinstance(item, dict) and item.get("type") == "file" and any(item["name"].endswith(ext) for ext in [".py", ".js", ".java"]):
                    raw_url = f"https://raw.githubusercontent.com/{repo_name}/main/{item['name']}"
                    file_content = requests.get(raw_url).text
                    code_files.append({"filename": item["name"], "content": file_content})

        documentation = generate_documentation(code_files, project_name=metadata["project_name"])
        return jsonify({"message": "Documentation generated", "documentation": documentation})

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/generate-uml-images", methods=["POST"])
def generate_uml_images():
    print("🎯 /generate-uml-images called")
    try:
        data = request.json
        repo_url = data.get("repo_url")
        if not repo_url:
            return jsonify({"error": "No GitHub repo URL provided"}), 400

        metadata, error = fetch_github_repo_data(repo_url)
        if error:
            return jsonify({"error": error}), 500

        repo_name = repo_url.replace("https://github.com/", "").strip("/")
        headers = {"Authorization": f"token {GITHUB_API_TOKEN}"}
        contents_url = f"https://api.github.com/repos/{repo_name}/contents"
        response = requests.get(contents_url, headers=headers)

        code_files = []
        for item in response.json():
            if item["type"] == "file" and any(item["name"].endswith(ext) for ext in [".py", ".js", ".java"]):
                raw_url = f"https://raw.githubusercontent.com/{repo_name}/main/{item['name']}"
                file_content = requests.get(raw_url).text
                code_files.append({"filename": item["name"], "content": file_content[:2000]})

        diagrams = generate_uml_from_code(code_files, project_name=metadata["project_name"])
        return jsonify({"message": "UML diagrams generated from GitHub code", "uml_diagrams": diagrams})

    except Exception as e:
        print(f"❌ ERROR in /generate-uml-images: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, threaded=True)
