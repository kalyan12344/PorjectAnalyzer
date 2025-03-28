import os
import requests
import zlib
import json
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GITHUB_API_TOKEN = os.getenv("GITHUB_API_TOKEN")


def encode_plantuml(plantuml_text):
    def deflate_and_encode(text):
        zlibbed_str = zlib.compress(text.encode("utf-8"))
        compressed = zlibbed_str[2:-4]
        return encode_base64(compressed)

    def encode_base64(data):
        chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"
        res = ""
        b = 0
        bits = 0
        for byte in data:
            b = (b << 8) | byte
            bits += 8
            while bits >= 6:
                bits -= 6
                res += chars[(b >> bits) & 0x3F]
        if bits > 0:
            res += chars[(b << (6 - bits)) & 0x3F]
        return res

    return deflate_and_encode(plantuml_text)


def get_uml_image_url(plantuml_code):
    encoded = encode_plantuml(plantuml_code)
    return f"https://www.plantuml.com/plantuml/png/{encoded}"


def clean_plantuml_code(text):
    start = text.find("@startuml")
    end = text.find("@enduml") + len("@enduml")
    if start == -1 or end == -1:
        return text.strip()
    return text[start:end].strip()


def fetch_github_repo_data(repo_url):
    """Fetch repository metadata from GitHub API without cloning."""
    repo_name = repo_url.replace("https://github.com/", "").strip("/")
    headers = {"Authorization": f"token {GITHUB_API_TOKEN}"}

    # Fetch repo structure
    contents_url = f"https://api.github.com/repos/{repo_name}/contents"
    response = requests.get(contents_url, headers=headers)
    print("git contents", response)
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


def generate_uml_from_code(code_files, project_name="Project"):
    diagram_prompts = {
        "class": "Generate a PlantUML **class diagram** showing classes, methods, and relationships.",
        "use_case": "Generate a PlantUML **use case diagram** showing actors and use cases.",
        "sequence": "Generate a PlantUML **sequence diagram** showing interactions between components."
    }

    diagrams = {}

    for diagram_type, instruction in diagram_prompts.items():
        prompt = f"""
You are a UML expert. {instruction}

Use the following source code files to generate a diagram.

**Project Name:** {project_name}

**Files:**
"""
        for file in code_files:
            prompt += f"\n### {file['filename']}\n\n```\n{file['content']}\n```\n"

        prompt += "\nStart your answer with @startuml and end with @enduml."

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "qwen/qwen-2.5-coder-32b-instruct:free",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 2048,
            "temperature": 0.2
        }

        try:
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
            result = response.json()["choices"][0]["message"]["content"].strip()
            print(f"\n📤 Raw UML Output ({diagram_type}):\n{result}\n")

            plantuml_cleaned = clean_plantuml_code(result)
            image_url = get_uml_image_url(plantuml_cleaned)

            diagrams[diagram_type] = {
                "plantuml_code": plantuml_cleaned,
                "image_url": image_url
            }

        except Exception as e:
            diagrams[diagram_type] = {
                "error": f"Failed to generate {diagram_type} diagram: {str(e)}"
            }

    return diagrams