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
    if 'mistake_qs' not in st.session_state:
        st.session_state.mistake_qs = set()
    if 'exam_mode' not in st.session_state:
        st.session_state.exam_mode = False
    if 'start_time' not in st.session_state:
        st.session_state.start_time = None

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
def display_question_card(q, idx, client, mode, is_locked=False):
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
        
        # Lock check for Exam Mode
        actual_lock = has_submitted or is_locked

        user_choice = st.radio(f"Select Answer for Q{idx+1}:", list(q['options'].keys()), 
                               format_func=lambda x: f"{x}) {q['options'][x]}",
                               key=f"rad_{q['question_id']}_{mode}", index=None, disabled=actual_lock)
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if not actual_lock:
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
                if has_submitted:
                    saved = st.session_state[submit_key]
                    if saved == q['correct_answer']:
                        st.success(f"Correct! The answer is {q['correct_answer']}")
                    else:
                        st.error(f"Incorrect. The correct answer is {q['correct_answer']}")
                    
                    # AI Insight hidden in Exam Mode until finish? 
                    # For now, let's allow it but label it 'Exam Review'
                    if st.button("Get AI Insight", key=f"ai_{q['question_id']}_{mode}"):
                        if client:
                            with st.spinner("Analyzing..."):
                                insight = get_ai_explanation(client, q, saved, saved == q['correct_answer'])
                                st.info(insight)
                        else:
                            st.warning("Connect AI in sidebar for insights!")
                elif is_locked:
                    st.warning("Time is up! You can no longer submit answers for this exam.")

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
    
    # Premium UI CSS
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        
        /* General Styles */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            background-color: #f8fafc;
        }
        
        .main {
            background-color: #f8fafc;
        }
        
        /* Card Styling */
        .question-card {
            background: #ffffff;
            padding: 30px;
            border-radius: 16px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            margin-bottom: 25px;
            transition: all 0.3s ease;
        }
        
        .question-card:hover {
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            transform: translateY(-2px);
        }
        
        /* Header & Badge Styling */
        .question-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: #475569;
            font-size: 0.85em;
            margin-bottom: 15px;
            border-bottom: 1px solid #f1f5f9;
            padding-bottom: 10px;
        }
        
        .badge {
            padding: 6px 14px;
            border-radius: 9999px;
            font-weight: 700;
            font-size: 0.7em;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .badge-easy { background: #dcfce7; color: #166534; }
        .badge-medium { background: #fef3c7; color: #92400e; }
        .badge-hard { background: #fee2e2; color: #991b1b; }
        
        /* Sidebar Polish */
        .sidebar .sidebar-content {
            background-color: #1e293b;
            color: white;
        }
        
        /* Button Styling Overrides */
        div.stButton > button {
            background-color: #1e293b;
            color: white;
            border-radius: 10px;
            padding: 10px 20px;
            border: none;
            font-weight: 600;
            width: 100%;
            transition: all 0.2s;
        }
        
        div.stButton > button:hover {
            background-color: #0d9488; /* Teal */
            color: white;
            border: none;
        }
        
        /* Info Boxes */
        .stAlert {
            border-radius: 12px;
            border: none;
        }
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
        
        acc = 0 if st.session_state.attempted == 0 else int(st.session_state.correct/st.session_state.attempted*100)
        st.info(f"Practice Score: {st.session_state.correct} / {st.session_state.attempted} (Accuracy: {acc}%)")
        
        # --- Exam Mode Toggle ---
        st.markdown("---")
        col_ex1, col_ex2 = st.columns([2, 1])
        with col_ex1:
            if not st.session_state.exam_mode:
                if st.button("🏁 Start 30-Min Exam Simulator"):
                    st.session_state.exam_mode = True
                    st.session_state.start_time = __import__('time').time()
                    st.rerun()
            else:
                if st.button("⏹️ Stop Exam"):
                    st.session_state.exam_mode = False
                    st.session_state.start_time = None
                    st.rerun()
        
        with col_ex2:
            if st.session_state.exam_mode and st.session_state.start_time:
                elapsed = __import__('time').time() - st.session_state.start_time
                remaining = max(0, 1800 - int(elapsed)) # 30 mins = 1800s
                mins, secs = divmod(remaining, 60)
                st.error(f"⏱️ Time Left: {mins:02d}:{secs:02d}")
                if remaining == 0:
                    st.warning("⚠️ TIME UP! Exam has been submitted.")
        
        for idx, q in enumerate(filtered):
            # In Exam Mode, we disable 'Get AI Insight' and 'Bookmark' until finished?
            # Actually let's just make sure they can't change answers if remaining == 0
            is_locked = False
            if st.session_state.exam_mode and st.session_state.start_time:
                if (__import__('time').time() - st.session_state.start_time) >= 1800:
                    is_locked = True
            
            display_question_card(q, idx, client, "practice", is_locked=is_locked)

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
