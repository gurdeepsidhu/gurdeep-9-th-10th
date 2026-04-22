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
    if 'mistake_reasons' not in st.session_state: st.session_state.mistake_reasons = {"Silly Mistake": 0, "Concept Gap": 0, "Confusing Question": 0}
    if 'subject_stats' not in st.session_state: st.session_state.subject_stats = {}
    if 'topic_stats' not in st.session_state: st.session_state.topic_stats = {}
    if 'accuracy_history' not in st.session_state: st.session_state.accuracy_history = []
    if 'exam_mode' not in st.session_state: st.session_state.exam_mode = False
    if 'start_time' not in st.session_state: st.session_state.start_time = None

# --- Load and Process Data ---
# @st.cache_data
def load_and_flatten_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # Switching back to database.json to restore summaries
    db_path = os.path.join(base_dir, 'database.json')
    try:
        with open(db_path, 'r', encoding='utf-8') as f:
            questions = json.load(f)
        
        # Standardize the data so the bouncer understands both formats
        for item in questions:
            if 'Subject' not in item and 'subject' in item: item['Subject'] = item['subject']
            if 'Topic' not in item and 'chapter' in item: item['Topic'] = item['chapter']
            if 'Class' not in item: item['Class'] = "Class 10" # Default
            if 'question_text' not in item and 'question' in item: item['question_text'] = item['question']
            
            # Final cleanup: Move generic 'Science' to specific subjects if possible
            if item['Subject'] == "Science":
                t = item.get('Topic', '')
                if t in ["Refraction", "Electricity", "Magnetic Effects of Electric Current", "Sources of Energy"]:
                    item['Subject'] = "Physics"
                elif t in ["Acids, Bases and Salts", "Chemical Reactions and Equations"]:
                    item['Subject'] = "Chemistry"
                elif t in ["Life Processes", "Control and Coordination", "Biology"]:
                    item['Subject'] = "Biology"
            
        return questions
    except FileNotFoundError:
        st.error(f"Database not found at {db_path}!")
        return []
    except Exception as e:
        st.error(f"Error loading database: {e}")
        return []

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
        submit_key = f"sub_{q.get('id', q.get('question_id'))}_{mode}"
        has_submitted = submit_key in st.session_state
        actual_lock = has_submitted or is_locked
        
        # Handle options as a list or a dictionary
        opts = q.get('options', {})
        if isinstance(opts, list):
            # If it's a list ["A) Option 1", ...], turn it into a dict {"A": "Option 1", ...}
            display_opts = {}
            for opt in opts:
                key = opt.split(')')[0].strip()
                val = opt.split(')')[-1].strip()
                display_opts[key] = val
        else:
            display_opts = opts

        user_choice = st.radio(f"Select Answer for Q{idx+1}:", list(display_opts.keys()), 
                               format_func=lambda x: f"{x}) {display_opts[x]}",
                               key=f"rad_{q.get('id', q.get('question_id'))}_{mode}", index=None, disabled=actual_lock)
        
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
                            
                            # Logic to check if the answer is correct
                            # Handle both "A" and "A) 30°" formats
                            corr = q.get('correct_answer', '')
                            is_correct = (user_choice == corr or corr.startswith(f"{user_choice})"))
                            
                            if is_correct:
                                st.session_state.correct += 1
                                st.balloons()
                            else:
                                st.session_state.mistake_qs.add(q.get('id', q.get('question_id')))
                                
                            # Subject Tracking
                            subj = q.get('Subject', 'General')
                            if subj not in st.session_state.subject_stats:
                                st.session_state.subject_stats[subj] = {'correct': 0, 'attempted': 0}
                            st.session_state.subject_stats[subj]['attempted'] += 1
                            if is_correct: st.session_state.subject_stats[subj]['correct'] += 1
                            
                            # Topic Mastery Tracking
                            top = q.get('Topic', 'General')
                            if top not in st.session_state.topic_stats:
                                st.session_state.topic_stats[top] = {'correct': 0, 'attempted': 0}
                            st.session_state.topic_stats[top]['attempted'] += 1
                            if is_correct: st.session_state.topic_stats[top]['correct'] += 1
                            
                            # Accuracy History
                            current_acc = int(st.session_state.correct / st.session_state.attempted * 100)
                            st.session_state.accuracy_history.append(current_acc)
                            if len(st.session_state.accuracy_history) > 20: st.session_state.accuracy_history.pop(0)

                        st.rerun()
            else:
                if has_submitted:
                    saved = st.session_state[submit_key]
                    # Check if correct (again, for the UI display)
                    corr = q.get('correct_answer', '')
                    is_right = (saved == corr or corr.startswith(f"{saved})"))
                    
                    if is_right:
                        st.success(f"✅ Correct! The answer is {corr}")
                        
                        # --- Advanced Insight for Correct Answers ---
                        exp = q.get('explanations', {})
                        # Use 'explanation' as a fallback for advanced insight
                        adv_exp = q.get('explanation', exp.get('advanced', "Great job! You mastered this concept."))
                        st.info(f"🚀 **Advanced Insight:** {adv_exp}")
                    else:
                        st.error(f"❌ Incorrect. The correct answer is {corr}")
                        
                        # --- Smart Feedback ---
                        exp = q.get('explanations', {})
                        basic_exp = q.get('explanation', exp.get('basic', "No explanation available yet."))
                        st.info(f"💡 **Quick Explanation:** {basic_exp}")
                        
                        # --- Mistake Tracker ---
                        st.write("💭 **Why did you miss this?**")
                        r_cols = st.columns(3)
                        q_id = q.get('id', q.get('question_id'))
                        if r_cols[0].button("Silly Mistake 🤡", key=f"silly_{q_id}"):
                            st.session_state.mistake_reasons["Silly Mistake"] += 1
                            st.toast("Mistake logged! Let's stay focused next time.")
                        if r_cols[1].button("Concept Gap 🧠", key=f"concept_{q_id}"):
                            st.session_state.mistake_reasons["Concept Gap"] += 1
                            st.toast("Logged! Maybe review this topic in the textbook.")
                        if r_cols[2].button("Confusing ❓", key=f"confused_{q_id}"):
                            st.session_state.mistake_reasons["Confusing Question"] += 1
                            st.toast("Logged! We'll look into simplifying this.")
                    
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

def display_summary_card(s):
    """Displays a very prominent revision summary card."""
    # Simple estimate: 1 min per 100 words
    word_count = len(str(s.get('content', '')).split())
    read_time = max(1, round(word_count / 100))
    
    with st.container():
        st.markdown(f"""
        <div style="background-color: #e0f2fe; padding: 35px; border-radius: 20px; border: 2px solid #38bdf8; margin-bottom: 30px; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <div style="display: flex; align-items: center;">
                    <span style="font-size: 2rem; margin-right: 15px;">🌟</span>
                    <strong style="color: #0369a1; text-transform: uppercase; font-size: 1rem; letter-spacing: 0.1em;">Chapter Quick Revision</strong>
                </div>
                <div style="background: #0ea5e9; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 700;">⏱️ {read_time} min read</div>
            </div>
            <h2 style="color: #0c4a6e; margin-top: 0; font-weight: 800;">{s.get('title', s.get('Topic', 'Chapter Overview'))}</h2>
            <hr style="border: 0; border-top: 1px solid #bae6fd; margin: 15px 0;">
            <div style="color: #1e293b; line-height: 1.8; font-size: 1.1rem;">
                {s.get('content', 'No content provided.')}
            </div>
        </div>
        """, unsafe_allow_html=True)

# --- Main App ---
def main():
    st.set_page_config(page_title="PYQ Student Hub v4.0", layout="wide")
    init_session_state()
    st.sidebar.success("✅ App Version 4.0: Categories & Summaries Fixed")
    
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
    
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.toast("Database refreshed!")
        st.rerun()

    all_qs = load_and_flatten_data()
    
    client = get_ai_teacher_client()
    
    # --- Sidebar Navigation (Hierarchical) ---
    st.sidebar.divider()
    st.sidebar.subheader("🎯 Smart Navigation")
    
    # 1. Class Selection
    classes = sorted(list(set(q['Class'] for q in all_qs)))
    sel_class = st.sidebar.selectbox("1. Select Class", ["All"] + classes)
    
    filtered = all_qs
    if sel_class != "All":
        filtered = [q for q in filtered if q['Class'] == sel_class]
    
    # 2. Subject Selection
    subjects = sorted(list(set(q['Subject'] for q in filtered)))
    sel_subj = st.sidebar.selectbox("2. Select Subject (Physics, Maths, etc.)", ["All"] + subjects)
    
    if sel_subj != "All":
        filtered = [q for q in filtered if q['Subject'] == sel_subj]
        
    # 3. Topic/Chapter Selection
    all_topics = sorted(list(set(q['Topic'] for q in filtered)))
    
    # Check if we should use subfolders (e.g., "Physics > Refraction")
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

    # --- System Check (Debug) - Moved after filtered is defined ---
    with st.sidebar.expander("🛠️ System Check"):
        all_summaries = [i for i in all_qs if str(i.get('type', '')).lower() == 'summary']
        st.write(f"Total Summaries: {len(all_summaries)}")
        st.write(f"Total Questions: {len(all_qs) - len(all_summaries)}")
        if all_summaries:
            st.write("Topics with summaries:")
            for s in all_summaries:
                st.write(f"- {s.get('Topic')}")
        
        f_summaries = [i for i in filtered if str(i.get('type', '')).lower() == 'summary']
        st.write(f"Summaries in current view: {len(f_summaries)}")

    acc = 0 if st.session_state.attempted == 0 else int(st.session_state.correct/st.session_state.attempted*100)
    
    # --- Sidebar Mastery Visuals ---
    st.sidebar.divider()
    st.sidebar.subheader("🏆 Your Mastery")
    for subj, stats in st.session_state.subject_stats.items():
        s_acc = int((stats['correct'] / stats['attempted']) * 100)
        st.sidebar.write(f"{subj}: {s_acc}%")
        st.sidebar.progress(s_acc / 100)
        
    st.sidebar.divider()
    st.sidebar.info(f"📊 Live Stats | Score: {st.session_state.correct} / {st.session_state.attempted} | Accuracy: {acc}%")

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
            
        # --- Prioritize Summaries over Questions ---
        st.subheader("📖 Chapter Revision Notes")
        
        # AGGRESSIVE SEARCH: Find current topic
        current_topic_names = list(set(q.get('Topic') for q in filtered))
        
        # If no topic is selected (All), we look at all topics in filtered view
        display_summaries = [item for item in all_qs if str(item.get('type', '')).lower() == 'summary' and item.get('Topic') in current_topic_names]
        
        if display_summaries:
            for item in display_summaries:
                display_summary_card(item)
            st.divider()
        else:
            st.warning("⚠️ No Revision Notes found for this selection yet.")
            st.info(f"Debug: Currently looking for summaries in topics: {current_topic_names}")
            
        st.subheader("📝 Practice Questions")
        questions = [item for item in filtered if str(item.get('type', '')).lower() != 'summary']
        for idx, item in enumerate(questions):
            display_question_card(item, idx, client, "practice", is_locked=is_locked)

    with tab2:
        st.title("🧠 Your Personal Review Room")
        review_ids = st.session_state.bookmarks.union(st.session_state.mistake_qs)
        
        # Get topics that have mistakes/bookmarks
        review_topics = set(q.get('Topic') for q in filtered if q.get('question_id') in review_ids)
        
        # Show summaries for those topics + the questions themselves
        review_qs = [q for q in filtered if q.get('question_id') in review_ids or (str(q.get('type', '')).lower() == 'summary' and q.get('Topic') in review_topics)]
        
        if not review_ids:
            st.success("No mistakes yet for this selection!")
        else:
            if st.button("Clear Mistake History", key="clear_mistakes_v5"):
                st.session_state.mistake_qs = set()
                st.rerun()
            # --- Prioritize Summaries over Questions in Review ---
            s_review = [item for item in review_qs if str(item.get('type', '')).lower() == 'summary']
            q_review = [item for item in review_qs if str(item.get('type', '')).lower() != 'summary']
            
            for item in s_review:
                display_summary_card(item)
            for idx, item in enumerate(q_review):
                display_question_card(item, idx, client, "review")

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
        st.subheader("💭 Mistake Analysis")
        if sum(st.session_state.mistake_reasons.values()) > 0:
            reason_data = [{"Reason": k, "Count": v} for k, v in st.session_state.mistake_reasons.items()]
            df_reasons = pd.DataFrame(reason_data)
            fig_reasons = px.pie(df_reasons, values='Count', names='Reason', 
                                 hole=0.4,
                                 color_discrete_sequence=['#f87171', '#60a5fa', '#fbbf24'],
                                 template="plotly_white")
            fig_reasons.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_reasons, use_container_width=True)
            st.caption("This chart helps you identify if your mistakes are conceptual or just lack of focus.")
        else:
            st.info("No mistakes recorded yet. Keep up the great work!")

        st.divider()
        st.subheader("🏆 Mastery Summary")
        cols = st.columns(3)
        cols[0].metric("Questions Attempted", st.session_state.attempted)
        cols[1].metric("Correct Answers", st.session_state.correct)
        acc_total = 0 if st.session_state.attempted == 0 else int(st.session_state.correct/st.session_state.attempted*100)
        cols[2].metric("Overall Accuracy", f"{acc_total}%")

if __name__ == "__main__":
    main()
