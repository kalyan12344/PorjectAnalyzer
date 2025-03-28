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

# Load environment variables


load_dotenv()
WKHTMLTOPDF_PATH = r"C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe"
config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# Set directories
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load API keys
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GITHUB_API_TOKEN = os.getenv("GITHUB_API_TOKEN")

print(f"🔍 GITHUB_API_TOKEN Loaded: {os.getenv('GITHUB_API_TOKEN')}")



@app.route("/generate-suggestions", methods=["POST"])
def generate_suggestions_api():
    """Generate suggestions by analyzing the code directly."""
    try:
        data = request.json
        repo_url = data.get("repo_url")
        if not repo_url:
            return jsonify({"error": "No GitHub repo URL provided"}), 400

        # Fetch the code files
        repo_name = repo_url.replace("https://github.com/", "").strip("/")
        headers = {"Authorization": f"token {GITHUB_API_TOKEN}"}
        contents_url = f"https://api.github.com/repos/{repo_name}/contents"
        response = requests.get(contents_url, headers=headers)

        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch repo contents"}), 500

        code_files = []
        for item in response.json():
            if item["type"] == "file" and any(item["name"].endswith(ext) for ext in [".py", ".js", ".java"]):
                raw_url = f"https://raw.githubusercontent.com/{repo_name}/main/{item['name']}"
                file_content = requests.get(raw_url).text
                code_files.append({
                    "filename": item["name"],
                    "content": file_content[:2000]
                })

        # Join all code content into a single string
        combined_code = "\n\n".join(
            f"### {file['filename']}\n```{file['content']}```"
            for file in code_files
        )

        # Generate AI suggestions
        suggestions = generate_suggestions(combined_code, project_name=repo_name.split("/")[-1])
        return jsonify({"message": "Suggestions generated from code", "suggestions": suggestions})

    except Exception as e:
        print(f"❌ ERROR in /generate-suggestions: {str(e)}")
        return jsonify({"error": str(e)}), 500
@app.route("/generate-pdf", methods=["POST"])
def generate_pdf():
    """Convert generated documentation to a downloadable PDF."""
    try:
        data = request.json
        documentation = data.get("documentation", "")
        project_name = data.get("project_name", "Project")

        if not documentation:
            return jsonify({"error": "No documentation provided"}), 400

        # Convert Markdown to HTML
        html_content = markdown2.markdown(documentation)

        # Define paths
        pdf_filename = f"{project_name}.pdf"
        pdf_path = os.path.join(UPLOAD_FOLDER, pdf_filename)

        # ✅ Ensure pdfkit uses the correct configuration
        pdfkit.from_string(html_content, pdf_path, configuration=config)

        print(f"📄 PDF Generated: {pdf_path}")
        return jsonify({"message": "PDF generated successfully", "pdf_url": f"http://127.0.0.1:5000/download-pdf/{pdf_filename}"})

    except Exception as e:
        print(f"❌ ERROR in generate-pdf: {str(e)}")
        return jsonify({"error": str(e)}), 500



@app.route("/download-pdf/<filename>", methods=["GET"])
def download_pdf(filename):
    """Serve the generated PDF file for download."""
    pdf_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True)
    else:
        return jsonify({"error": "PDF not found"}), 404


@app.after_request
def add_cors_headers(response):
    """Ensure CORS headers are applied to all responses."""
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:5174"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

def fetch_github_repo_data(repo_url):
    """Fetch repository metadata from GitHub API without cloning."""
    repo_name = repo_url.replace("https://github.com/", "").strip("/")
    headers = {"Authorization": f"token {GITHUB_API_TOKEN}"}

    # Fetch repo structure
    contents_url = f"https://api.github.com/repos/{repo_name}/contents"
    response = requests.get(contents_url, headers=headers)
    print("git contents",response)
    if response.status_code != 200:
        return None, f"Error fetching repository: {response.status_code} - {response.text}"

    file_structure = [{"name": item["name"], "type": item["type"]} for item in response.json()]
    all_files = [item["name"] for item in file_structure if item["type"] == "file"]

    # Fetch languages
    languages_url = f"https://api.github.com/repos/{repo_name}/languages"
    response = requests.get(languages_url, headers=headers)
    languages = list(response.json().keys()) if response.status_code == 200 else ["Unknown"]

    # Fetch dependencies
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

    # Construct metadata
    project_metadata = {
        "project_name": repo_name.split("/")[-1],
        "language": languages,
        "structure": file_structure,
        "dependencies": dependencies
    }
    return project_metadata, None


def extract_metadata(project_folder):
    """Extract project metadata from uploaded folder."""
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

    # Detect programming languages
    extensions = {".py": "Python", ".js": "JavaScript", ".java": "Java", ".jsx": "JavaScript"}
    detected_languages = set(ext for file in all_files for ext, lang in extensions.items() if file.endswith(ext))
    project_info["language"] = list(detected_languages) if detected_languages else ["Unknown"]

    # Extract dependencies
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


def generate_documentation(project_metadata):
    """Generate structured Markdown documentation using OpenRouter."""
    API_URL = "https://openrouter.ai/api/v1/chat/completions"

    if not OPENROUTER_API_KEY:
        return "Error: Missing OpenRouter API Key. Please check your .env file."

    HEADERS = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""
    You are a software documentation expert. Generate a **detailed and structured** Markdown documentation for the following project.

    **Project Name:** {project_metadata["project_name"]}
    **Programming Language:** {", ".join(project_metadata["language"])}
    **Dependencies:** {", ".join(project_metadata["dependencies"]) if project_metadata["dependencies"] else "None"}

    **Project Structure:**  
    ```
    {json.dumps(project_metadata["structure"], indent=2)}
    ```

    **📌 Generate the following sections using detailed Markdown formatting:**
    
    # {project_metadata["project_name"]}

    ## Overview
    - Provide a **detailed introduction** about the project.
    - Explain the **purpose and features** of the project.
    - Mention the **intended users and use cases**.

    ## Installation
    - List all **required software** (e.g., Node.js, Python, databases).
    - Provide **detailed step-by-step** installation instructions.

    ## Code Structure
    - Show the **full directory structure**.
    - Provide **a table explaining key files** and their roles.

    ## Features & Functionality
    - Describe the **main features of the project**.
    - Provide code snippets where necessary.

    ## API Documentation (If Applicable)
    - List available **backend API endpoints**.
    - Provide request/response examples.

    ## Configuration
    - Explain how to **configure the project settings**.
    - Provide instructions for setting up **environment variables**.

    ## Dependencies
    - List dependencies **along with their versions**.

    ## Usage
    - Provide a **step-by-step guide** on running and using the project.

    ## Testing
    - Provide details on **how to run unit and integration tests**.

    ## Deployment
    - Give a **detailed guide on deploying** the project.

    **Ensure the output is well-structured and clean Markdown.**
    """

    data = {
        "model": "deepseek/deepseek-r1-distill-qwen-32b:free",
        # "model": "qwen/qwen-2.5-coder-32b-instruct:free",

        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4096,
        "temperature": 0.2
    }

    try:
        response = requests.post(API_URL, headers=HEADERS, json=data)

        # ✅ Log Full Response for Debugging
        # print(f"📡 OpenRouter API Response: {response.status_code} - {response.text}")

        if response.status_code != 200:
            return f"Error: OpenRouter API failed with status {response.status_code} - {response.text}"

        response_data = response.json()

        # ✅ Check if 'choices' Key Exists
        if "choices" not in response_data or not response_data["choices"]:
            return f"Error: OpenRouter API response missing 'choices': {response_data}"

        return response_data["choices"][0]["message"]["content"].strip()

    except requests.exceptions.JSONDecodeError as e:
        return f"Error: Failed to parse OpenRouter response - {str(e)}"

@app.route("/generate-docs", methods=["OPTIONS", "POST"])
def generate_docs():
    """Decide whether to process a folder or GitHub repo and generate documentation."""
    
    try:
        # ✅ Handle CORS Preflight Request
        if request.method == "OPTIONS":
            response = jsonify({"message": "CORS preflight successful"})
            response.headers["Access-Control-Allow-Origin"] = "http://localhost:5174"
            response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            response.headers["Access-Control-Allow-Credentials"] = "true"
            return response, 200
        
        if "files" in request.files:
            # Folder Upload Case
            uploaded_files = request.files.getlist("files")
            project_folder = os.path.join(UPLOAD_FOLDER, "project")
            os.makedirs(project_folder, exist_ok=True)

            for file in uploaded_files:
                file_path = os.path.join(project_folder, file.filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                file.save(file_path)

            metadata = extract_metadata(project_folder)
        else:
            # GitHub Analysis Case
            data = request.json
            repo_url = data.get("repo_url")
            if not repo_url:
                return jsonify({"error": "No input provided"}), 400

            metadata, error = fetch_github_repo_data(repo_url)
            if error:
                return jsonify({"error": error}), 500

        documentation = generate_documentation(metadata)
        return jsonify({"message": "Documentation generated", "documentation": documentation})

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")  # ✅ Log the error in Flask console
        return jsonify({"error": str(e)}), 500  # ✅ Send error details to frontend



@app.route("/generate-uml-images", methods=["POST"])
def generate_uml_images():
    print("🎯 /generate-uml-images called")
    try:
        data = request.json
        repo_url = data.get("repo_url")
        if not repo_url:
            return jsonify({"error": "No GitHub repo URL provided"}), 400

        # ✅ Step 1: Fetch repo metadata (structure, langs, deps)
        metadata, error = fetch_github_repo_data(repo_url)
        if error:
            return jsonify({"error": error}), 500

        # ✅ Step 2: Fetch raw source code files for UML generation
        repo_name = repo_url.replace("https://github.com/", "").strip("/")
        headers = {"Authorization": f"token {GITHUB_API_TOKEN}"}
        contents_url = f"https://api.github.com/repos/{repo_name}/contents"
        response = requests.get(contents_url, headers=headers)

        code_files = []
        for item in response.json():
            if item["type"] == "file" and any(item["name"].endswith(ext) for ext in [".py", ".js", ".java"]):
                raw_url = f"https://raw.githubusercontent.com/{repo_name}/main/{item['name']}"
                file_content = requests.get(raw_url).text
                code_files.append({
                    "filename": item["name"],
                    "content": file_content[:2000]  # Limit content size
                })

        # ✅ Step 3: Generate UML Diagrams
        diagrams = generate_uml_from_code(code_files, project_name=metadata["project_name"])

        return jsonify({
            "message": "UML diagrams generated from GitHub code",
            "uml_diagrams": diagrams
        })

    except Exception as e:
        print(f"❌ ERROR in /generate-uml-images: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, threaded=True)
