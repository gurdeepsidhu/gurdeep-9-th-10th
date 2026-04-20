import streamlit as st
import json
from openai import OpenAI
from fpdf import FPDF
import io
import os
import random
import time
import pandas as pd
import plotly.express as px

# --- Initialization ---
def init_session_state():
    if 'attempted' not in st.session_state: st.session_state.attempted = 0
    if 'correct' not in st.session_state: st.session_state.correct = 0
    if 'topic_mistakes' not in st.session_state: st.session_state.topic_mistakes = {} 
    if 'topic_streak' not in st.session_state: st.session_state.topic_streak = {}
    if 'answered_qs' not in st.session_state: st.session_state.answered_qs = set()
    if 'bookmarks' not in st.session_state: st.session_state.bookmarks = set()
    if 'mistake_qs' not in st.session_state: st.session_state.mistake_qs = set()
    if 'subject_stats' not in st.session_state: st.session_state.subject_stats = {}
    if 'accuracy_history' not in st.session_state: st.session_state.accuracy_history = []
    if 'exam_mode' not in st.session_state: st.session_state.exam_mode = False
    if 'start_time' not in st.session_state: st.session_state.start_time = None

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
                            
                            is_correct = (user_choice == q['correct_answer'])
                            if is_correct:
                                st.session_state.correct += 1
                                st.balloons()
                            else:
                                st.session_state.mistake_qs.add(q['question_id'])
                                
                            # Subject Tracking
                            subj = q.get('Subject', 'General')
                            if subj not in st.session_state.subject_stats:
                                st.session_state.subject_stats[subj] = {'correct': 0, 'attempted': 0}
                            st.session_state.subject_stats[subj]['attempted'] += 1
                            if is_correct: st.session_state.subject_stats[subj]['correct'] += 1
                            
                            # Accuracy History
                            current_acc = int(st.session_state.correct / st.session_state.attempted * 100)
                            st.session_state.accuracy_history.append(current_acc)
                            if len(st.session_state.accuracy_history) > 20: st.session_state.accuracy_history.pop(0)

                        st.rerun()
            else:
                if has_submitted:
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
                elif is_locked:
                    st.warning("Time is up! Answers are locked.")

        with col2:
            is_bookmarked = q['question_id'] in st.session_state.bookmarks
            label = "🔖 Saved" if is_bookmarked else "📑 Bookmark"
            if st.button(label, key=f"book_{q['question_id']}_{mode}"):
                if is_bookmarked: st.session_state.bookmarks.remove(q['question_id'])
                else: st.session_state.bookmarks.add(q['question_id'])
                st.rerun()

# --- Main App ---
def main():
    st.set_page_config(page_title="PYQ Student Hub", layout="wide")
    init_session_state()
    
    # Premium UI CSS
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #f8fafc; }
        .main { background-color: #f8fafc; }
        .question-card { background: #ffffff; padding: 30px; border-radius: 16px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); margin-bottom: 25px; transition: all 0.3s ease; }
        .question-card:hover { box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); transform: translateY(-2px); }
        .question-header { display: flex; justify-content: space-between; align-items: center; color: #475569; font-size: 0.85em; margin-bottom: 15px; border-bottom: 1px solid #f1f5f9; padding-bottom: 10px; }
        .badge { padding: 6px 14px; border-radius: 9999px; font-weight: 700; font-size: 0.7em; text-transform: uppercase; letter-spacing: 0.05em; }
        .badge-easy { background: #dcfce7; color: #166534; }
        .badge-medium { background: #fef3c7; color: #92400e; }
        .badge-hard { background: #fee2e2; color: #991b1b; }
        div.stButton > button { background-color: #1e293b; color: white; border-radius: 10px; padding: 10px 20px; border: none; font-weight: 600; width: 100%; transition: all 0.2s; }
        div.stButton > button:hover { background-color: #0d9488; color: white; border: none; }
        .stAlert { border-radius: 12px; border: none; }
    </style>
    """, unsafe_allow_html=True)

    st.sidebar.title("📚 Student Dashboard")
    client = get_ai_teacher_client()
    all_qs = load_and_flatten_data()
    
    # --- Sidebar Navigation (Dynamic Drill-Down) ---
    st.sidebar.divider()
    st.sidebar.subheader("🎯 Smart Navigation")
    
    classes = sorted(list(set(q['Class'] for q in all_qs)))
    sel_class = st.sidebar.selectbox("1. Choose Class", ["All"] + classes)
    
    filtered = all_qs
    if sel_class != "All":
        filtered = [q for q in filtered if q['Class'] == sel_class]
        subjects = sorted(list(set(q['Subject'] for q in filtered)))
        sel_subj = st.sidebar.selectbox("2. Choose Subject", ["All"] + subjects)
        
        if sel_subj != "All":
            filtered = [q for q in filtered if q['Subject'] == sel_subj]
            all_topics = sorted(list(set(q['Topic'] for q in filtered)))
            has_subfolders = any(" > " in t for t in all_topics)
            
            if has_subfolders:
                categories = sorted(list(set(t.split(" > ")[0] for t in all_topics)))
                sel_cat = st.sidebar.selectbox("3. Choose Category", ["All"] + categories)
                if sel_cat != "All":
                    filtered = [q for q in filtered if q['Topic'].startswith(sel_cat)]
                    sub_topics = sorted(list(set(q['Topic'] for q in filtered)))
                    display_topics = [t.split(" > ")[-1] if " > " in t else t for t in sub_topics]
                    sel_topic = st.sidebar.selectbox("4. Choose Chapter", ["All"] + display_topics)
                    if sel_topic != "All":
                        filtered = [q for q in filtered if q['Topic'].endswith(sel_topic)]
            else:
                sel_topic = st.sidebar.selectbox("3. Choose Chapter", ["All"] + all_topics)
                if sel_topic != "All":
                    filtered = [q for q in filtered if q['Topic'] == sel_topic]

    acc = 0 if st.session_state.attempted == 0 else int(st.session_state.correct/st.session_state.attempted*100)
    st.info(f"📊 Live Stats | Score: {st.session_state.correct} / {st.session_state.attempted} | Accuracy: {acc}%")

    tab1, tab2, tab3 = st.tabs(["🚀 Practice Mode", "🧠 Review Mode", "📊 Analytics"])
    
    with tab1:
        st.title("🎯 Practice & Exam Zone")
        
        col_ex1, col_ex2 = st.columns([2, 1])
        with col_ex1:
            if not st.session_state.exam_mode:
                if st.button("🏁 Start 30-Min Exam Simulator"):
                    st.session_state.exam_mode = True
                    st.session_state.start_time = time.time()
                    st.rerun()
            else:
                if st.button("⏹️ Stop Exam"):
                    st.session_state.exam_mode = False
                    st.session_state.start_time = None
                    st.rerun()
        
        with col_ex2:
            is_locked = False
            if st.session_state.exam_mode and st.session_state.start_time:
                elapsed = time.time() - st.session_state.start_time
                remaining = max(0, 1800 - int(elapsed))
                mins, secs = divmod(remaining, 60)
                st.error(f"⏱️ Time: {mins:02d}:{secs:02d}")
                if remaining == 0: 
                    is_locked = True
                    st.warning("⚠️ TIME UP!")
            
        for idx, q in enumerate(filtered):
            display_question_card(q, idx, client, "practice", is_locked=is_locked)

    with tab2:
        st.title("🧠 Your Personal Review Room")
        review_ids = st.session_state.bookmarks.union(st.session_state.mistake_qs)
        review_qs = [q for q in filtered if q['question_id'] in review_ids]
        
        if not review_qs:
            st.success("No mistakes yet for this selection!")
        else:
            if st.button("Clear Mistake History", key="clear_mistakes_v5"):
                st.session_state.mistake_qs = set()
                st.rerun()
            for idx, q in enumerate(review_qs):
                display_question_card(q, idx, client, "review")

    with tab3:
        st.title("📈 Performance Analytics")
        st.write("Visualize your learning journey!")
        
        col_an1, col_an2 = st.columns(2)
        
        with col_an1:
            st.subheader("🎯 Subject Mastery")
            if st.session_state.subject_stats:
                data = []
                for s, stats in st.session_state.subject_stats.items():
                    acc_s = int((stats['correct'] / stats['attempted']) * 100)
                    data.append({"Subject": s, "Accuracy (%)": acc_s})
                df = pd.DataFrame(data)
                fig = px.bar(df, x='Subject', y='Accuracy (%)', color_discrete_sequence=['#0d9488'], template="plotly_white")
                fig.update_layout(yaxis_range=[0,100])
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Start practicing to see subject-wise analytics!")
                
        with col_an2:
            st.subheader("📈 Accuracy Over Time")
            if len(st.session_state.accuracy_history) > 1:
                df_hist = pd.DataFrame({
                    "Attempt": list(range(1, len(st.session_state.accuracy_history) + 1)),
                    "Accuracy (%)": st.session_state.accuracy_history
                })
                fig_line = px.line(df_hist, x='Attempt', y='Accuracy (%)', markers=True, color_discrete_sequence=['#1e293b'], template="plotly_white")
                fig_line.update_layout(yaxis_range=[0,100])
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.info("Solve more questions to see your progress curve!")

        st.divider()
        st.subheader("🏆 Mastery Summary")
        cols = st.columns(3)
        cols[0].metric("Questions Attempted", st.session_state.attempted)
        cols[1].metric("Correct Answers", st.session_state.correct)
        acc_total = 0 if st.session_state.attempted == 0 else int(st.session_state.correct/st.session_state.attempted*100)
        cols[2].metric("Overall Accuracy", f"{acc_total}%")

if __name__ == "__main__":
    main()
