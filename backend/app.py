from flask import Flask, request, jsonify, render_template
import os
import PyPDF2
from groq import Groq



app = Flask(__name__, static_folder="static", template_folder="templates")   
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("API key not found. Please set GROQ_API_KEY in .env")

client = Groq(api_key=api_key)

def extract_text_from_file(filepath):
    if filepath.endswith('.pdf'):
        try:
            text = ""
            with open(filepath, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text()
            return text
        except Exception as e:
            print(f"Error: {e}")
            return None
    else:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    syllabus = request.files.get('syllabus')
    model = request.files.get('model')

    if not syllabus or not model:
        return jsonify({'error': 'Both files are required'}), 400

    syllabus_path = os.path.join(app.config['UPLOAD_FOLDER'], syllabus.filename)
    model_path = os.path.join(app.config['UPLOAD_FOLDER'], model.filename)

    syllabus.save(syllabus_path)
    model.save(model_path)

    syllabus_text = extract_text_from_file(syllabus_path)
    model_text = extract_text_from_file(model_path)

    if not syllabus_text or not model_text:
        return jsonify({'error': 'Failed to read one or both files'}), 500

    prompt = f"""You are an expert in designing question papers. Your task is to generate a completely new question paper that follows the exact format, line order, and layout of the provided Model Question Paper Format. This means that every header line (such as "Time : Three Hours", "Maximum : 100 Marks", etc.), spacing, and line numbering must appear exactly in the same order and on the same lines as in the model. Do not replicate the model’s actual questions; only replicate its format.

At the same time, you must generate all the questions based on the provided Syllabus Content. The questions should be:
- Derived from the syllabus (for example, if the syllabus is mathematics, the questions must be math-based).
- Created to exactly match the number of questions in the model.
- Marked with the appropriate Course Outcomes (CO) and Bloom’s Taxonomy Levels (BL), exactly as they appear in the model question paper. Use the following levels as a guide:
  - L1: Remembering (e.g., define, list)
  - L2: Understanding (e.g., explain, describe)
  - L3: Applying (e.g., solve, demonstrate)
  - L4: Analysing (e.g., analyze, compare)
  - L5: Evaluating (e.g., evaluate, justify)
  - L6: Creating (e.g., design, propose)

Important requirements:
1. **Exact Format Replication:**
- Replicate every static line of the model (headers, footers, section lines, etc.) in the correct order and on the correct line numbers.
- Do not insert the model’s sample questions anywhere; only its format.

2. **Syllabus-Based Questions:**
- Generate new questions solely based on the Syllabus Content.
- Ensure the generated questions are appropriate for the subject (e.g., if the syllabus is math-based, all questions must be mathematical).
- The number of questions generated must exactly match the number in the model.
- Each question must include the correct CO and BL indicators exactly as in the model.

3. **Multiple Syllabus Handling:**
- If more than one syllabus is provided, integrate the relevant topics from all syllabi while still adhering to the model’s question count and format.

Model Question Paper Format: {model_text}
Syllabus Content: {syllabus_text}

Based solely on the information above, generate a complete question paper that:
- **Strictly replicates the model’s format and line order.**
- **Generates new, syllabus-based questions that exactly match the number, placement, CO, and BL from the model.**
- **Uses varied vocabulary (e.g., “explain”, “discuss”, “analyze”, “solve”, “design”, “propose”) to reflect the intended difficulty levels.**

Output only the final generated question paper with no additional commentary.
"""
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=2048
        )
        result = response.choices[0].message.content
        return jsonify({'output': result})
    except Exception as e:
        print(f"Generation Error: {e}")
        return jsonify({'error': 'Generation failed'}), 500
