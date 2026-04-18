import os
import json
import fitz  # PyMuPDF
import google.generativeai as genai

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def process_text_with_gemini(text):
    # Try to load API key from env, otherwise prompt for it
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        api_key = input("Enter your Gemini API Key (or set GEMINI_API_KEY env var): ").strip()
    
    if not api_key:
        print("Error: API Key is required to use the Gemini Extractor.")
        return []
        
    genai.configure(api_key=api_key)
    
    prompt = f"""
You are an expert educational content extractor building a database of Class 10 Board Questions.
Extract all multiple-choice questions from the following text.

CRITICAL INSTRUCTIONS:
1. If the text lacks an answer key, automatically deduce the correct answer based on standard 10th-grade Science knowledge.
2. Generate a 1-sentence 'teacher_hint' that provides a logic-based tip or "board secret" for each question.
3. Output strictly in the following JSON format as a list of objects. Do NOT wrap the JSON in Markdown backticks (e.g., no ```json ... ```). Just output the raw JSON list.

Format Example:
[
  {{
    "question_id": "UNIQUE_ID (e.g., PHY-10-TOPIC-001)",
    "topic": "Extracted or inferred topic (e.g., 'Refraction')",
    "year": "Extracted year or 'Unknown Year'",
    "difficulty": "Easy, Medium, or Hard (infer if not stated)",
    "question_text": "The question itself",
    "options": {{
      "A": "Option 1",
      "B": "Option 2",
      "C": "Option 3",
      "D": "Option 4"
    }},
    "correct_answer": "A, B, C, or D",
    "teacher_hint": "Your generated logic-based tip"
  }}
]

Text to process:
{text}
"""
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        
        # Clean up response if it has markdown formatting
        output = response.text.strip()
        if output.startswith("```json"):
            output = output[7:-3].strip()
        elif output.startswith("```"):
            output = output[3:-3].strip()
            
        return json.loads(output)
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        return []

def main():
    papers_dir = "papers"
    output_file = "ingested_database.json"
    
    if not os.path.exists(papers_dir):
        print(f"Directory '{papers_dir}' not found. Creating it...")
        os.makedirs(papers_dir)
        print("Please place your PDF files in the 'papers' directory and run again.")
        return
        
    all_extracted_questions = []
    
    pdf_files = [f for f in os.listdir(papers_dir) if f.endswith(".pdf")]
    
    if not pdf_files:
        print(f"No PDF files found in '{papers_dir}' directory.")
        return
        
    for filename in pdf_files:
        print(f"\nProcessing {filename}...")
        pdf_path = os.path.join(papers_dir, filename)
        
        # 1. Extract raw text
        text = extract_text_from_pdf(pdf_path)
        print(f"Extracted {len(text)} characters of text. Sending to AI for smart extraction...")
        
        # 2. Extract structured JSON via Gemini
        extracted_qs = process_text_with_gemini(text)
        
        if extracted_qs:
            all_extracted_questions.extend(extracted_qs)
            print(f"✅ Successfully extracted and solved {len(extracted_qs)} questions from {filename}.")
        else:
            print(f"❌ Failed to extract questions from {filename}.")
                
    if all_extracted_questions:
        # Load existing if any
        if os.path.exists(output_file):
            try:
                with open(output_file, 'r') as f:
                    existing_data = json.load(f)
                    all_extracted_questions = existing_data + all_extracted_questions
            except Exception:
                pass
                
        # 3. Save to database
        with open(output_file, 'w') as f:
            json.dump(all_extracted_questions, f, indent=4)
        print(f"\n🎉 Success! Total {len(all_extracted_questions)} questions saved to {output_file}.")
        print("You can now review this file before merging it into your main app database.")
    else:
        print("\nNo questions were extracted from any files.")

if __name__ == "__main__":
    main()
