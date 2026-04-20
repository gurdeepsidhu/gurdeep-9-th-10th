import streamlit as st
import json
from openai import OpenAI
from fpdf import FPDF
import io
import os
import random

# --- Initialization ---
def init_session_state():
    if 'attempted' not in st.session_state: st.session_state.attempted = 0
    if 'correct' not in st.session_state: st.session_state.correct = 0
    if 'topic_mistakes' not in st.session_state: st.session_state.topic_mistakes = {} 
    if 'topic_streak' not in st.session_state: st.session_state.topic_streak = {}
    if 'answered_qs' not in st.session_state: st.session_state.answered_qs = set()
    if 'bookmarks' not in st.session_state: st.session_state.bookmarks = set()
    if 'mistake_qs' not in st.session_state: st.session_state.mistake_qs = set()

# --- Load and Process Data ---
@st.cache_data
def load_and_flatten_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, 'database.json')
    try:
        with open(db_path, 'r', encoding='utf-8') as f:
            db = json.load(f)
    except FileNotFoundError:
        st.error(f"Database not found at {db_path}!")
        return []

    questions = []
    def recursive_flatten(data, path_dict):
        if isinstance(data, list):
            for q in data:
                flat_q = q.copy()
                flat_q.update(path_dict)
                if 'Chapter' not in flat_q:
                    flat_q['Chapter'] = path_dict.get('Topic', 'Unknown')
                questions.append(flat_q)
            return
        if isinstance(data, dict):
            for key, value in data.items():
                new_path = path_dict.copy()
                depth = len(path_dict)
                if depth == 0: new_path['Class'] = key
                elif depth == 1: new_path['Subject'] = key
                elif depth == 2: new_path['Topic'] = key
                else: new_path['Topic'] = f"{path_dict['Topic']} > {key}"
                recursive_flatten(value, new_path)
    recursive_flatten(db, {})
    return questions

# --- AI Integration ---
def get_ai_teacher_client():
    api_key = st.secrets.get("GROQ_API_KEY")
    if not api_key:
        api_key = st.sidebar.text_input("Enter Groq API Key", type="password")
    if api_key:
        return OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
    return None

def get_ai_explanation(client, q, user_answer, is_correct):
    prompt = f"""
    Context: Question: {q['question_text']}, Correct: {q['correct_answer']}, User: {user_answer}, Status: {'Correct' if is_correct else 'Incorrect'}
    Topic: {q['Topic']}
    Task: Explain the answer in short bullet points for 10th grade. Use a friendly tone.
    """
    try:
        response = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}])
        return response.choices[0].message.content
    except:
        return "AI Teacher busy. Please try again!"

# --- UI Components ---
def display_question_card(q, idx, client, mode):
    # Safe access to fields with defaults
    diff = q.get('Difficulty', q.get('difficulty', 'Medium')).lower()
    year = q.get('Year', q.get('year', 'Unknown'))
    chapter = q.get('Chapter', q.get('chapter', 'Unknown'))
    topic = q.get('Topic', 'General')
    
    badge_class = f"badge-{diff}" if diff in ['easy', 'medium', 'hard'] else "badge-medium"
    
    with st.container():
        st.markdown(f"""
        <div class="question-card">
            <div class="question-header">
                <div><strong>{year}</strong> | {chapter} > {topic}</div>
                <div class="badge {badge_class}">{diff.capitalize()}</div>
            </div>
            <h5 style="color: #212529;">Q. {q.get('question_text', 'No question text available.')}</h5>
        </div>
        """, unsafe_allow_html=True)
        
        # Options
        submit_key = f"sub_{q['question_id']}_{mode}"
        has_submitted = submit_key in st.session_state
        
        user_choice = st.radio(f"Select Answer for Q{idx+1}:", list(q['options'].keys()), 
                               format_func=lambda x: f"{x}) {q['options'][x]}",
                               key=f"rad_{q['question_id']}_{mode}", index=None, disabled=has_submitted)
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if not has_submitted:
                if st.button(f"Submit Answer", key=f"btn_{q['question_id']}_{mode}"):
                    if user_choice:
                        st.session_state[submit_key] = user_choice
                        # Tracking
                        if q['question_id'] not in st.session_state.answered_qs:
                            st.session_state.attempted += 1
                            st.session_state.answered_qs.add(q['question_id'])
                            if user_choice == q['correct_answer']:
                                st.session_state.correct += 1
                                st.balloons()
                            else:
                                st.session_state.mistake_qs.add(q['question_id'])
                        st.rerun()
            else:
                saved = st.session_state[submit_key]
                if saved == q['correct_answer']:
                    st.success(f"Correct! The answer is {q['correct_answer']}")
                else:
                    st.error(f"Incorrect. The correct answer is {q['correct_answer']}")
                
                if st.button("Get AI Insight", key=f"ai_{q['question_id']}_{mode}"):
                    if client:
                        with st.spinner("Analyzing..."):
                            insight = get_ai_explanation(client, q, saved, saved == q['correct_answer'])
                            st.info(insight)
                    else:
                        st.warning("Connect AI in sidebar for insights!")

        with col2:
            is_bookmarked = q['question_id'] in st.session_state.bookmarks
            label = "🔖 Saved" if is_bookmarked else "📑 Bookmark"
            if st.button(label, key=f"book_{q['question_id']}_{mode}"):
                if is_bookmarked: st.session_state.bookmarks.remove(q['question_id'])
                else: st.session_state.bookmarks.add(q['question_id'])
                st.rerun()

# --- Main App ---
def main():
    st.set_page_config(page_title="PYQ Hub", layout="wide")
    init_session_state()
    
    # CSS
    st.markdown("""
    <style>
        .question-card { background: white; padding: 20px; border-radius: 10px; border: 1px solid #ddd; margin-bottom: 10px; }
        .question-header { display: flex; justify-content: space-between; color: #666; font-size: 0.8em; margin-bottom: 10px; }
        .badge { padding: 4px 8px; border-radius: 10px; font-weight: bold; }
        .badge-easy { background: #d1e7dd; color: #0f5132; }
        .badge-medium { background: #fff3cd; color: #664d03; }
        .badge-hard { background: #f8d7da; color: #842029; }
    </style>
    """, unsafe_allow_html=True)

    st.sidebar.title("📚 PYQ Hub")
    client = get_ai_teacher_client()
    all_qs = load_and_flatten_data()
    
    tab1, tab2 = st.tabs(["Practice Mode", "Review Mode"])
    
    with tab1:
        st.title("🎯 Practice Zone")
        # Sidebar Filters Logic
        classes = sorted(list(set(q['Class'] for q in all_qs)))
        sel_class = st.sidebar.selectbox("Class", ["All"] + classes)
        
        filtered = [q for q in all_qs if (sel_class == "All" or q['Class'] == sel_class)]
        
        subjects = sorted(list(set(q['Subject'] for q in filtered)))
        sel_subj = st.sidebar.selectbox("Subject", ["All"] + subjects)
        if sel_subj != "All": filtered = [q for q in filtered if q['Subject'] == sel_subj]
        
        # Real-time Score
        st.info(f"Score: {st.session_state.correct} / {st.session_state.attempted} (Accuracy: {0 if st.session_state.attempted == 0 else int(st.session_state.correct/st.session_state.attempted*100)}%)")
        
        for idx, q in enumerate(filtered):
            display_question_card(q, idx, client, "practice")

    with tab2:
        st.title("🧠 Review My Mistakes")
        review_ids = st.session_state.bookmarks.union(st.session_state.mistake_qs)
        review_qs = [q for q in all_qs if q['question_id'] in review_ids]
        
        if not review_qs:
            st.success("No mistakes yet! Keep practicing.")
        else:
            if st.button("Clear All Mistakes"):
                st.session_state.mistake_qs = set()
                st.rerun()
            for idx, q in enumerate(review_qs):
                display_question_card(q, idx, client, "review")

if __name__ == "__main__":
    main()
