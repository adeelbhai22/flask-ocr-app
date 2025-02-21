from flask import Flask, render_template, request, jsonify
import os
import pytesseract
import cv2
import numpy as np
from pdf2image import convert_from_path
from werkzeug.utils import secure_filename
import re


if 'DYNO' in os.environ:  # This checks if the app is running on Heroku
    pytesseract.pytesseract.tesseract_cmd = "/app/.apt/usr/bin/tesseract"
else:
    # Local path (Windows or Linux)
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def convert_pdf_to_images(pdf_path):
    """Convert PDF pages to images before OCR processing."""
    images = convert_from_path(pdf_path)
    image_paths = []
    for i, img in enumerate(images):
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], f'page_{i+1}.jpg')
        img.save(image_path, "JPEG")
        image_paths.append(image_path)
    return image_paths

def extract_text(image_path):
    """Extract structured information from a receipt image using Tesseract OCR."""
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    text = pytesseract.image_to_string(image, config="--psm 6")

    # Debug: Print extracted text
    print("\n===== Extracted OCR Text =====")
    print(text)
    print("==============================\n")

    # Convert text to lowercase and remove unwanted characters
    text = text.lower()
    text = re.sub(r"[^\w\s#\-$.,:]", "", text)  # Remove special characters

    # Define regex patterns to find specific fields
    receipt_pattern = r"receipt\s*#\s*:\s*([\w\-]+)"   # Extracts receipt number
    bill_to_pattern = r"bill to\s*:\s*(.*?)\s*address"  # Extracts "Bill To" before "Address"
    total_pattern = r"total\s*:\s*\$?([\d\.,]+)"  # Extracts total

    # Extract values using regex search
    receipt_match = re.search(receipt_pattern, text)
    bill_to_match = re.search(bill_to_pattern, text, re.DOTALL)
    total_match = re.search(total_pattern, text)

    # Get extracted values or return "Not found"
    extracted_data = {
        "Receipt #": receipt_match.group(1).strip() if receipt_match else "Not found",
        "Bill To": bill_to_match.group(1).strip() if bill_to_match else "Not found",
        "Total": total_match.group(1).strip() if total_match else "Not found",
    }

    return extracted_data

@app.route('/')
def index():
    """Render the main HTML page."""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and extract structured data from receipt."""
    if 'file' not in request.files:
        return jsonify({"error": "No file part"})

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No selected file"})

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        extracted_text = extract_text(file_path)  # Extract OCR text

        return jsonify(extracted_text)  # Return only extracted fields

    return jsonify({"error": "Invalid file format. Only PNG, JPG, JPEG, and PDF are allowed."})

if __name__ == '__main__':
    app.run(debug=True)
