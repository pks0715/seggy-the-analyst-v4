from flask import Flask, request, jsonify, render_template
import os
import requests
import json
from datetime import datetime
import PyPDF2
import io

app = Flask(__name__)

# OpenRouter Configuration
OPENROUTER_API_KEY = "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"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEEPSEEK_R1_MODEL = "deepseek/deepseek-r1"

def extract_text_from_pdf(file):
    """Extract text from PDF file"""
    try:
        # Reset file pointer to beginning
        file.seek(0)
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None

def test_openrouter_connection():
    """Test if OpenRouter API key is working"""
    print("=== TESTING OPENROUTER CONNECTION ===")
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://seggy-the-analyst-v4.onrender.com",
        "X-Title": "Financial Due Diligence Tool"
    }
    
    test_payload = {
        "model": DEEPSEEK_R1_MODEL,
        "messages": [
            {
                "role": "user",
                "content": "Hello, please respond with 'API is working' if you can read this."
            }
        ],
        "max_tokens": 50
    }
    
    try:
        print("Sending test request to OpenRouter...")
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=test_payload, timeout=30)
        print(f"Test response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ OpenRouter connection SUCCESSFUL!")
            print(f"Response: {result}")
            return True
        else:
            print(f"❌ OpenRouter connection FAILED: {response.status_code}")
            print(f"Error details: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ OpenRouter test error: {e}")
        return False

def analyze_financial_data_with_deepseek(extracted_text):
    """
    Analyze financial data using Deepseek R1 via OpenRouter
    """
    print("=== STARTING DEEPSEEK ANALYSIS ===")
    
    # First test the connection
    if not test_openrouter_connection():
        print("OpenRouter connection test failed - skipping analysis")
        return None
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://seggy-the-analyst-v4.onrender.com",
        "X-Title": "Financial Due Diligence Tool"
    }
    
    # Limit text length to avoid token limits
    if len(extracted_text) > 10000:
        extracted_text = extracted_text[:10000] + "\n\n[Document truncated for analysis...]"
    
    prompt = f"""
    Analyze these financial documents and provide a comprehensive due diligence report:

    {extracted_text}

    Provide analysis covering:
    1. Financial health assessment
    2. Key financial ratios  
    3. Trends and patterns
    4. Strengths and concerns
    5. Recommendations

    Format as a professional due diligence report.
    """
    
    payload = {
        "model": DEEPSEEK_R1_MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 2000,
        "temperature": 0.1
    }
    
    try:
        print("Sending analysis request to OpenRouter...")
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=60)
        print(f"Analysis response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Analysis request SUCCESSFUL!")
            
            if 'choices' in result and len(result['choices']) > 0:
                analysis = result['choices'][0]['message']['content']
                print(f"Analysis length: {len(analysis)} characters")
                return analysis
            else:
                print("Unexpected response format:", result)
                return None
        else:
            print(f"❌ Analysis request FAILED: {response.status_code}")
            print(f"Error details: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print("❌ OpenRouter API timeout after 60 seconds")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ OpenRouter API connection error: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error during AI analysis: {e}")
        return None

def generate_fallback_report(extracted_texts, file_names):
    """Generate fallback report when AI service is unavailable"""
    total_chars = sum(len(text) for text in extracted_texts.values())
    
    report = {
        "status": "fallback",
        "report_content": f"""
FINANCIAL DUE DILIGENCE REPORT (FALLBACK ANALYSIS)

Total Files Analyzed: {len(file_names)}

⚠️ AI SERVICE UNAVAILABLE

The AI analysis service (Deepseek R1 via OpenRouter) is currently unavailable.

Possible reasons:
- API key authentication failed
- OpenRouter service temporary unavailable
- Billing setup required for OpenRouter account

DOCUMENTS PROCESSED:
{chr(10).join(f'- {name}' for name in file_names)}

TEXT EXTRACTION SUMMARY:
- Successfully extracted text from {len(file_names)} documents
- Total characters processed: {total_chars}

NEXT STEPS:
1. Check OpenRouter account billing setup
2. Verify API key is valid and active
3. Try again in a few minutes

Document processing completed at: {datetime.now().strftime('%m/%d/%Y, %I:%M:%S %p')}
""",
        "files_processed": file_names,
        "characters_processed": total_chars,
        "timestamp": datetime.now().isoformat()
    }
    
    return report

def generate_full_report(ai_analysis, extracted_texts, file_names):
    """Generate full report with AI analysis"""
    total_chars = sum(len(text) for text in extracted_texts.values())
    
    report = {
        "status": "success",
        "report_content": f"""
FINANCIAL DUE DILIGENCE REPORT

Total Files Analyzed: {len(file_names)}
Analysis Generated: {datetime.now().strftime('%m/%d/%Y, %I:%M:%S %p')}

DOCUMENTS PROCESSED:
{chr(10).join(f'- {name}' for name in file_names)}

TEXT EXTRACTION SUMMARY:
- Successfully extracted text from {len(file_names)} documents  
- Total characters processed: {total_chars}

AI ANALYSIS RESULTS:
{ai_analysis}

---
✅ Report generated successfully using Deepseek R1 via OpenRouter
""",
        "files_processed": file_names,
        "characters_processed": total_chars,
        "timestamp": datetime.now().isoformat()
    }
    
    return report

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/test-api')
def test_api():
    """Test endpoint to check OpenRouter connection"""
    result = test_openrouter_connection()
    return jsonify({
        'api_working': result,
        'message': 'OpenRouter connection test completed - check server logs for details'
    })

@app.route('/analyze', methods=['POST'])
def analyze_documents():
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files uploaded'}), 400
        
        files = request.files.getlist('files')
        if not files or all(file.filename == '' for file in files):
            return jsonify({'error': 'No files selected'}), 400
        
        extracted_texts = {}
        file_names = []
        
        # Extract text from all uploaded files
        for file in files:
            if file and file.filename.endswith('.pdf'):
                print(f"Processing file: {file.filename}")
                text = extract_text_from_pdf(file)
                if text:
                    extracted_texts[file.filename] = text
                    file_names.append(file.filename)
                    print(f"Successfully extracted {len(text)} characters from {file.filename}")
                else:
                    return jsonify({'error': f'Failed to extract text from {file.filename}'}), 400
        
        if not extracted_texts:
            return jsonify({'error': 'No valid text extracted from uploaded files'}), 400
        
        # Combine all extracted text for analysis
        combined_text = "\n\n".join([f"--- {name} ---\n{text}" for name, text in extracted_texts.items()])
        print(f"Combined text length: {len(combined_text)} characters")
        
        # Try AI analysis first
        print("Attempting AI analysis with Deepseek R1...")
        ai_analysis = analyze_financial_data_with_deepseek(combined_text)
        
        if ai_analysis:
            print("✅ AI analysis successful! Generating full report...")
            report = generate_full_report(ai_analysis, extracted_texts, file_names)
        else:
            print("❌ AI analysis failed, generating fallback report")
            report = generate_fallback_report(extracted_texts, file_names)
        
        return jsonify(report)
        
    except Exception as e:
        print(f"❌ Error in analyze_documents: {e}")
        return jsonify({'error': 'Internal server error'
