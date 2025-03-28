import os
import requests
import cv2
import pytesseract
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Setup Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Load API key
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def classify_ui_component(img, x, y, w, h, text):
    """Classify a UI component based on size, aspect ratio, and text."""
    aspect_ratio = w / h
    area = w * h

    if "button" in text.lower() or (aspect_ratio > 1.5 and h < 80):
        return "button"
    elif "input" in text.lower() or (w > 100 and h < 40):
        return "input"
    elif w > 200 and h > 100:
        return "card"
    elif text:
        return "text"
    else:
        return "container"

def process_image(image_path):
    """Extract and classify UI elements from image."""
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    ui_elements = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)

        if w > 50 and h > 20:  # Filter out noise
            cropped = img[y:y + h, x:x + w]
            text = pytesseract.image_to_string(cropped).strip()
            el_type = classify_ui_component(img, x, y, w, h, text)
            ui_elements.append({
                "type": el_type,
                "content": text,
                "position": (x, y, w, h)
            })

    # Sort by position: top to bottom, then left to right
    ui_elements.sort(key=lambda el: (el["position"][1], el["position"][0]))
    return ui_elements

def generate_prompt(ui_elements):
    """Generate a layout prompt using the Mistral model via OpenRouter."""
    API_URL = "https://openrouter.ai/api/v1/chat/completions"

    if not OPENROUTER_API_KEY:
        return "Error: Missing OpenRouter API Key. Please check your .env file."

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    ui_description = "\n".join([
        f"- {el['type']} with text '{el['content']}' at position {el['position']}"
        for el in ui_elements
    ])

    prompt = f"""
You are a UI expert. Based on the following extracted UI elements, generate a **clear layout prompt** to recreate the same UI using **React and Tailwind CSS**.

Only include visible layout components. Describe the layout structure (rows, columns, spacing) and content hierarchy clearly.

**UI Elements:**
{ui_description}

**Instructions for Output:**
- Use terminology suited for React and Tailwind CSS.
- Group elements logically (e.g., cards in a row).
- Reflect accurate layout flow (top-down, left-right).
- The output should be a single prompt for a code-generating AI to build the same UI.

**Output Example:**
