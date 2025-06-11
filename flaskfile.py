from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import openai
import pdfplumber
import pytesseract
from PIL import Image
import os

app = Flask(__name__)

# Set your OpenAI GPT API key
openai.api_key = "OPEN_API_KEY"

# Directory where PDF files are stored
pdf_files_dir = "C:\\Users\\DINESH\\Dropbox\\PC\\Downloads"

def extract_text_from_pdf(pdf_path):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text()
        if not text:
            # If text extraction fails, try using OCR on the PDF pages
            text = extract_text_with_ocr(pdf_path)
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None

def extract_text_with_ocr(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            # Convert each PDF page to an image and use OCR
            image = page.to_image()
            text += pytesseract.image_to_string(image.original)
    return text

def generate_labels_with_gpt(text):
    prompt = f"Given the following text:\n{text}\nAsk ChatGPT:\n"
    questions = ["What is the name?", "Which school did they attend?", "Any specific prompts you want to ask?"]
    answers = {}

    for question in questions:
        prompt_with_question = f"{prompt}\nUser: {question}\nChatGPT:"
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt_with_question,
            temperature=0.7,
            max_tokens=20,
            n=1,
            stop=None
        )
        answer = response.choices[0].text.strip()
        answers[question] = answer

    return answers

@app.route('/generate_labels', methods=['POST'])
def generate_labels():
    try:
        if 'text' in request.form:
            # If 'text' is in form data, use it
            text = request.form['text']
        else:
            # If 'file' is in files data, extract text from the PDF
            pdf_file = request.files.get('file')
            
            if pdf_file and pdf_file.filename.lower() == 'profile.pdf':
                # Use the predefined filename for "profile.pdf"
                pdf_path = os.path.join(pdf_files_dir, 'profile.pdf')
                pdf_file.save(pdf_path)
                text = extract_text_from_pdf(pdf_path)
            else:
                return jsonify({'error': 'Invalid or missing file'}), 400

            if not text:
                return jsonify({'error': 'Error extracting text from PDF'}), 400

        result = generate_labels_with_gpt(text)
        return jsonify(result), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
