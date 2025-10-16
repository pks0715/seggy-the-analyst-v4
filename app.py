from flask import Flask, request, jsonify, render_template
import os
import requests
import json
from datetime import datetime
import PyPDF2
import io
import time

app = Flask(__name__)

# Groq Configuration
GROQ_API_KEY = "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"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"  # Fast and capable model on Groq

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

def split_text_into_batches(text, max_batch_size=4000):
    """Split text into manageable batches for analysis"""
    words = text.split()
    batches = []
    current_batch = []
    current_size = 0
    
    for word in words:
        if current_size + len(word) + 1 > max_batch_size and current_batch:
            batches.append(" ".join(current_batch))
            current_batch = [word]
            current_size = len(word)
        else:
            current_batch.append(word)
            current_size += len(word) + 1
    
    if current_batch:
        batches.append(" ".join(current_batch))
    
    print(f"Split text into {len(batches)} batches")
    return batches

def analyze_batch_with_groq(batch_text, batch_number, total_batches, analysis_type):
    """Analyze a single batch of text with Groq"""
    print(f"Analyzing batch {batch_number}/{total_batches} for {analysis_type}...")
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    if analysis_type == "financial_ratios":
        prompt = f"""
        Analyze this batch of financial data (Batch {batch_number}/{total_batches}) and extract key financial ratios and metrics:
        
        {batch_text}
        
        Focus on:
        - Profitability ratios (Gross Margin, Net Margin, ROE, ROA)
        - Liquidity ratios (Current Ratio, Quick Ratio) 
        - Leverage ratios (Debt-to-Equity, Debt-to-Assets)
        - Efficiency ratios (Asset Turnover, Inventory Turnover)
        
        Provide only the ratios and their values in a clear format.
        """
    elif analysis_type == "trends":
        prompt = f"""
        Analyze this batch of financial data (Batch {batch_number}/{total_batches}) and identify trends and patterns:
        
        {batch_text}
        
        Focus on:
        - Revenue growth trends
        - Expense patterns
        - Profitability changes
        - Key financial statement movements
        
        Provide clear trend observations.
        """
    else:  # overview
        prompt = f"""
        Analyze this batch of financial data (Batch {batch_number}/{total_batches}) and provide a general overview:
        
        {batch_text}
        
        Focus on:
        - Overall financial health
        - Key strengths
        - Potential concerns
        - Major financial statement items
        
        Provide a concise overview.
        """
    
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 1500,
        "temperature": 0.1,
        "top_p": 0.9
    }
    
    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=120)  # 2 minute timeout
        print(f"Batch {batch_number} response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            analysis = result['choices'][0]['message']['content']
            print(f"✅ Batch {batch_number} analysis successful ({len(analysis)} chars)")
            return analysis
        else:
            print(f"❌ Batch {batch_number} failed: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print(f"❌ Batch {batch_number} timeout after 120 seconds")
        return None
    except Exception as e:
        print(f"❌ Batch {batch_number} error: {e}")
        return None

def analyze_financial_data_with_groq(extracted_text):
    """
    Analyze financial data using Groq with batch processing
    """
    print("=== STARTING GROQ ANALYSIS WITH BATCH PROCESSING ===")
    
    # Test Groq connection first
    if not test_groq_connection():
        print("Groq connection test failed - skipping analysis")
        return None
    
    # Split text into batches
    batches = split_text_into_batches(extracted_text)
    
    if not batches:
        print("No batches created from text")
        return None
    
    all_analyses = {
        "financial_ratios": [],
        "trends": [],
        "overview": []
    }
    
    # Analyze each batch for different aspects
    analysis_types = ["financial_ratios", "trends", "overview"]
    
    for analysis_type in analysis_types:
        print(f"\n--- Starting {analysis_type.upper()} analysis ---")
        type_analyses = []
        
        for i, batch in enumerate(batches, 1):
            batch_analysis = analyze_batch_with_groq(batch, i, len(batches), analysis_type)
            if batch_analysis:
                type_analyses.append(batch_analysis)
            
            # Add delay between requests to avoid rate limits
            if i < len(batches):
                time.sleep(1)  # 1 second delay between batches
        
        all_analyses[analysis_type] = type_analyses
        print(f"Completed {analysis_type}: {len(type_analyses)}/{len(batches)} batches successful")
    
    # Combine all analyses into final report
    return combine_analyses_into_report(all_analyses)

def combine_analyses_into_report(all_analyses):
    """Combine batch analyses into a comprehensive report"""
    print("Combining batch analyses into final report...")
    
    final_report = """
COMPREHENSIVE FINANCIAL DUE DILIGENCE REPORT
Generated using Groq with Batch Processing
============================================

"""
    
    # Add financial ratios section
    if all_analyses["financial_ratios"]:
        final_report += "1. KEY FINANCIAL RATIOS AND METRICS\n"
        final_report += "-----------------------------------\n"
        for analysis in all_analyses["financial_ratios"]:
            final_report += analysis + "\n\n"
    
    # Add trends section
    if all_analyses["trends"]:
        final_report += "2. FINANCIAL TRENDS AND PATTERNS\n"
        final_report += "---------------------------------\n"
        for analysis in all_analyses["trends"]:
            final_report += analysis + "\n\n"
    
    # Add overview section
    if all_analyses["overview"]:
        final_report += "3. OVERALL FINANCIAL ASSESSMENT\n"
        final_report += "--------------------------------\n"
        for analysis in all_analyses["overview"]:
            final_report += analysis + "\n\n"
    
    # Add summary
    final_report += "4. EXECUTIVE SUMMARY\n"
    final_report += "--------------------\n"
    final_report += f"Analysis completed using {len(all_analyses['financial_ratios'])} batches for ratios, "
    final_report += f"{len(all_analyses['trends'])} batches for trends, "
    final_report += f"{len(all_analyses['overview'])} batches for overview.\n\n"
    
    final_report += "Report generated using Groq API with Llama 3.3 70B model."
    
    return final_report

def test_groq_connection():
    """Test if Groq API key is working"""
    print("=== TESTING GROQ CONNECTION ===")
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    test_payload = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "user",
                "content": "Hello, please respond with 'GROQ API is working' if you can read this."
            }
        ],
        "max_tokens": 50
    }
    
    try:
        print("Sending test request to Groq...")
        response = requests.post(GROQ_API_URL, headers=headers, json=test_payload, timeout=30)
        print(f"Groq test response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Groq connection SUCCESSFUL!")
            print(f"Response: {result['choices'][0]['message']['content']}")
            return True
        else:
            print(f"❌ Groq connection FAILED: {response.status_code}")
            print(f"Error details: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Groq test error: {e}")
        return False

def generate_fallback_report(extracted_texts, file_names):
    """Generate fallback report when AI service is unavailable"""
    total_chars = sum(len(text) for text in extracted_texts.values())
    
    report = {
        "status": "fallback",
        "report_content": f"""
FINANCIAL DUE DILIGENCE REPORT (FALLBACK ANALYSIS)

Total Files Analyzed: {len(file_names)}

⚠️ AI SERVICE UNAVAILABLE

The AI analysis service (Groq) is currently unavailable.

DOCUMENTS PROCESSED:
{chr(10).join(f'- {name}' for name in file_names)}

TEXT EXTRACTION SUMMARY:
- Successfully extracted text from {len(file_names)} documents
- Total characters processed: {total_chars}

NEXT STEPS:
1. Check Groq API key and quota
2. Verify internet connection
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
✅ Report generated successfully using Groq with batch processing
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
    """Test endpoint to check Groq connection"""
    result = test_groq_connection()
    return jsonify({
        'api_working': result,
        'message': 'Groq connection test completed - check server logs for details'
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
        print("Attempting AI analysis with Groq (batch processing)...")
        ai_analysis = analyze_financial_data_with_groq(combined_text)
        
        if ai_analysis:
            print("✅ AI analysis successful! Generating full report...")
            report = generate_full_report(ai_analysis, extracted_texts, file_names)
        else:
            print("❌ AI analysis failed, generating fallback report")
            report = generate_fallback_report(extracted_texts, file_names)
        
        return jsonify(report)
        
    except Exception as e:
        print(f"❌ Error in analyze_documents: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
