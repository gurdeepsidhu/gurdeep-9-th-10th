import json
import os
import time
import toml
from openai import OpenAI
import re

def get_api_key():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(base_dir)
    secrets_path = os.path.join(project_dir, '.streamlit', 'secrets.toml')
    try:
        secrets = toml.load(secrets_path)
        return secrets.get('GROQ_API_KEY')
    except Exception as e:
        print(f"Failed to load secrets: {e}")
        return None

def main():
    api_key = get_api_key()
    if not api_key:
        print("No Groq API Key found!")
        return

    client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(base_dir)
    db_file = os.path.join(project_dir, 'database.json')

    with open(db_file, 'r', encoding='utf-8') as f:
        db_data = json.load(f)

    # Find all Class 9 topics and their question counts
    class_9_topics = set()
    question_counts = {} # (Subject, Topic) -> count
    
    for item in db_data:
        if item.get('Class') == 'Class 9':
            subj = item.get('Subject')
            topic = item.get('Topic')
            class_9_topics.add((subj, topic))
            if 'question_text' in item:
                question_counts[(subj, topic)] = question_counts.get((subj, topic), 0) + 1

    print(f"Found {len(class_9_topics)} topics for Class 9.")
    
    # We will save incrementally
    generated_count = 0
    target_per_chapter = 10

    for subj, topic in sorted(list(class_9_topics)):
        # Skip if subject or topic is missing
        if not subj or not topic:
            continue
            
        current = question_counts.get((subj, topic), 0)
        needed = target_per_chapter - current
        
        if needed > 0:
            print(f"[{subj}] {topic} needs {needed} more questions (Current: {current}). Generating...")
            
            prompt = f"""
You are an expert Class 9 {subj} teacher in India (CBSE/NCERT board).
Generate EXACTLY {needed} multiple choice practice questions for the chapter "{topic}".
The questions should be a mix of easy, medium, and hard difficulty.

Respond ONLY with a raw JSON array of objects. NO markdown formatting, NO backticks, NO extra text.
Format each object EXACTLY like this:
{{
    "question_text": "The actual question?",
    "options": {{
        "A": "First option",
        "B": "Second option",
        "C": "Third option",
        "D": "Fourth option"
    }},
    "correct_answer": "A",
    "explanations": {{
        "basic": "Step 1: ... Step 2: ...",
        "advanced": "Excellent job! You have a solid grasp of this concept."
    }},
    "year": "Standard",
    "difficulty": "Medium",
    "chapter": "{topic}",
    "Class": "Class 9",
    "Subject": "{subj}",
    "Topic": "{topic}"
}}
"""
            try:
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3
                )
                
                content = response.choices[0].message.content.strip()
                # Remove markdown backticks if the model ignores the instruction
                if content.startswith('```'):
                    content = re.sub(r'^```[a-z]*\n|\n```$', '', content)
                if content.startswith('```'):
                    content = content[3:]
                if content.endswith('```'):
                    content = content[:-3]
                    
                new_qs = json.loads(content)
                
                # Add IDs and append
                for idx, q in enumerate(new_qs):
                    q['question_id'] = f"GEN-{topic[:3].upper()}-{int(time.time())}-{idx}"
                    db_data.append(q)
                    
                generated_count += len(new_qs)
                
                # Save immediately to prevent data loss on crash
                with open(db_file, 'w', encoding='utf-8') as f:
                    json.dump(db_data, f, indent=4)
                    
                print(f"  -> Successfully added {len(new_qs)} questions. Saved DB.")
                time.sleep(2) # Prevent rate limiting
                
            except Exception as e:
                print(f"  -> Failed to generate for {topic}: {e}")
                print(f"  -> Raw response: {content[:200] if 'content' in locals() else 'None'}")
                time.sleep(5)
                
    print(f"\nDone! Generated {generated_count} new questions total.")

if __name__ == '__main__':
    main()
