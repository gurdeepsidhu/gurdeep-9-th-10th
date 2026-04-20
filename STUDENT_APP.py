import streamlit as st
import json
from openai import OpenAI
from fpdf import FPDF
try:
    from streamlit_mic_recorder import speech_to_text
    ENABLE_VOICE = False # Disabled due to Streamlit Cloud compatibility issues
except ImportError:
    ENABLE_VOICE = False
import io

def init_session_state():
    if 'attempted' not in st.session_state:
        st.session_state.attempted = 0
    if 'correct' not in st.session_state:
        st.session_state.correct = 0
    if 'topic_mistakes' not in st.session_state:
        st.session_state.topic_mistakes = {} 
    if 'topic_streak' not in st.session_state:
        st.session_state.topic_streak = {}
    if 'answered_qs' not in st.session_state:
        st.session_state.answered_qs = set()

def generate_pdf(questions, topic_name):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("helvetica", "B", 16)
        pdf.cell(190, 10, f"Mock Test: {topic_name}", ln=True, align="C")
        pdf.ln(10)
        
        def clean_text(text):
            return str(text).encode('latin-1', 'replace').decode('latin-1')

        for idx, q in enumerate(questions[:10]):
            pdf.set_font("helvetica", "B", 12)
            pdf.write(8, clean_text(f"Q{idx + 1}. {q['question_text']}\n"))
            pdf.set_font("helvetica", size=12)
            for key, val in q['options'].items():
                pdf.write(6, clean_text(f"  {key}) {val}\n"))
            pdf.ln(5)
        
        return pdf.output()
    except Exception as e:
        return None

def get_gap_analysis_warning(client, topic):
    prompt = f"""
System Persona: You are an experienced, caring examiner and teacher for 9th-10th grade. 
The student has just gotten multiple questions wrong in the topic: '{topic}'.
Provide a short, encouraging "Pro-tip" or warning in friendly Hinglish (e.g. starting with "Beta...").
Identify what fundamental concept they might be missing based on the topic '{topic}', and give them a quick tip to revise it. Keep it under 3-4 sentences.
"""
    models_to_try = ["llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "mixtral-8x7b-32768"]
    last_error = ""
    for model_name in models_to_try:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            last_error = str(e)
            if "Model not found" in last_error:
                continue
            break
    return f"Error connecting to AI: {last_error}"

# Phase 6: The Analogy Library
ANALOGY_LIBRARY = {
    "voltage": "Water Pressure in a pipe",
    "current": "Flow of water in a pipe",
    "resistance": "A narrow section or stones in the pipe slowing water down",
    "photosynthesis": "Cooking food in a kitchen (Leaves = Kitchen, Sunlight = Stove heat, Chlorophyll = Chef)",
    "refraction": "A shopping cart moving from pavement to mud (one wheel slows down, causing the cart to turn)",
    "balancing equations": "A see-saw that must have equal weight on both sides",
    "exothermic": "A hand warmer releasing heat to its surroundings",
}

def get_ai_explanation(client, question, options, user_answer, correct_answer, is_correct, topic=""):
    if is_correct:
        insight_type = "Advanced Insight"
    else:
        insight_type = "Basic Explanation"
        
    specific_analogy_instruction = ""
    topic_lower = topic.lower()
    for key, analogy in ANALOGY_LIBRARY.items():
        if key in topic_lower or key in question.lower():
            specific_analogy_instruction = f"\nCRITICAL RULE: Since this question is about '{key}', you MUST use the '{analogy}' analogy to explain it."
            break

    prompt = f"""
System Persona: You are not just a teacher; you are a Board Paper Evaluator for 9th-10th grade. Your tone is highly empathetic but authoritative. 

Context:
Question: {question}
Options: {json.dumps(options)}
Student's Answer: {user_answer}
Correct Answer: {correct_answer}
Status: {'Correct' if is_correct else 'Incorrect'}
Topic: {topic}{specific_analogy_instruction}

Task for {insight_type}:
1. Explain the correct answer using short bullet points and **bold** key terms to make it highly scannable for kids. Do NOT write long paragraphs.
2. If the status is 'Incorrect', NEVER scold the student. Instead, act as a "Reasoning Bridge". Look at their incorrect answer, try to find the logic in why they chose it, and gently correct them. Start with something similar to: "Aapka logic sahi tha, lekin aapne shayad chhoti si galti kar di... Chaliye ise ek simple kahani se samajhte hain."
3. After explaining, ALWAYS add a 'Board Secret' section with the following three points:
   - Step Marking: (Give a specific tip like: "Is question mein agar aap diagram nahi banayenge, toh 1 mark kat jayega.")
   - Keywords: (Give a specific tip like: "Answer mein 'Refraction' ke saath 'Optical Density' word ka hona must hai.")
   - Analogy: (Use a daily life example to explain the core concept. { 'Follow the CRITICAL RULE above for the specific analogy.' if specific_analogy_instruction else 'Invent a highly relatable analogy like traffic or kitchen recipes.' })
   - Diagram Suggestion: (Suggest a simple, relevant diagram or visual for this specific question. Format it strictly as: **[Diagram Suggestion: Description of the visual]**)

4. Add a 'Quick Concept Recap' section:
   - Provide 2-3 short bullet points explaining the core Science/Physics principle behind the question. 
   - Focus strictly on the "Why" (e.g., if the question is about refraction, explain the change in speed of light or Snell's Law).
"""
    models_to_try = ["llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "mixtral-8x7b-32768"]
    last_error = ""
    for model_name in models_to_try:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            last_error = str(e)
            if "Model not found" in last_error:
                continue
            break
    return f"Error connecting to AI: {last_error}"

st.set_page_config(page_title="Student Dashboard", page_icon="📚", layout="wide")

# Custom CSS for card styling
st.markdown("""
<style>
    .question-card {
        background-color: #ffffff;
        padding: 25px;
        border-radius: 12px;
        margin-bottom: 25px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        color: #212529;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
    }
    .question-header {
        display: flex;
        justify-content: space-between;
        margin-bottom: 15px;
        font-size: 0.9em;
        color: #6c757d;
    }
    .badge {
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 0.75em;
        font-weight: bold;
        text-transform: uppercase;
    }
    .badge-easy { background-color: #d1e7dd; color: #0f5132; }
    .badge-medium { background-color: #fff3cd; color: #664d03; }
    .badge-hard { background-color: #f8d7da; color: #842029; }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_and_flatten_data():
    import os
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, 'database.json')
    
    try:
        with open(db_path, 'r') as f:
            db = json.load(f)
    except FileNotFoundError:
        st.error(f"Database not found at {db_path}!")
        return []

    questions = []

    def recursive_flatten(data, path_dict):
        """Recursively traverses the JSON until it finds a list of questions."""
        if isinstance(data, list):
            # We found the actual questions!
            for q in data:
                flat_q = q.copy()
                # Carry over the hierarchy info
                flat_q.update(path_dict)
                # Ensure compatibility with old 'Chapter' key
                if 'Chapter' not in flat_q:
                    flat_q['Chapter'] = path_dict.get('Topic', 'Unknown')
                questions.append(flat_q)
            return

        if isinstance(data, dict):
            for key, value in data.items():
                new_path = path_dict.copy()
                # Assign key to the correct hierarchy level based on depth
                depth = len(path_dict)
                if depth == 0: new_path['Class'] = key
                elif depth == 1: new_path['Subject'] = key
                elif depth == 2: new_path['Topic'] = key
                else: 
                    # For levels deeper than 3, we append to Topic for display
                    new_path['Topic'] = f"{path_dict['Topic']} > {key}"
                
                recursive_flatten(value, new_path)

    recursive_flatten(db, {})
    return questions

def main():
    init_session_state()
    st.sidebar.title("📚 PYQ Learning Hub")
    
    # Check if API Key is stored in Streamlit Cloud Secrets
    api_key = st.secrets.get("GROQ_API_KEY")
    
    if api_key:
        st.sidebar.success(f"✅ Key loaded! (...{api_key[-4:]})")
    else:
        st.sidebar.warning("⚠️ No Key found in Secrets!")
        api_key = st.sidebar.text_input("Enter Groq API Key", type="password")
    
    client = None
    if api_key:
        try:
            client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
            st.sidebar.success("✅ AI Teacher Active")
            # Debug: Show available models to find the correct one
            try:
                models_data = client.models.list().data
                available_ids = [m.id for m in models_data]
                st.sidebar.write(f"📋 Available Models: {', '.join(available_ids)}")
            except Exception as model_err:
                st.sidebar.error(f"⚠️ Could not list models: {model_err}")
        except Exception as e:
            st.sidebar.error(f"❌ AI Error: {e}")
    else:
        st.sidebar.info("🔑 AI is currently offline. Please add your API key.")

    all_questions = load_and_flatten_data()
    st.sidebar.write(f"📚 Questions in DB: {len(all_questions)}")

    # Phase 8: Surprise Me! (Daily Challenge)
    if st.sidebar.button("🎲 Surprise Me!"):
        import random
        st.session_state.surprise_q = random.choice(all_questions)
        st.session_state.show_surprise = True

    st.title("🎯 Board Exam PYQ Assistant")
    st.write("Solve previous year questions and get AI-powered insights!")

    # Display Surprise Question
    if 'show_surprise' in st.session_state and st.session_state.show_surprise:
        st.divider()
        st.subheader("🌟 Daily Challenge: Surprise Question!")
        q = st.session_state.surprise_q
        
        # Determine badge class for difficulty
        diff = q['Difficulty'].lower()
        badge_class = f"badge-{diff}" if diff in ['easy', 'medium', 'hard'] else "badge-medium"
        
        with st.container():
            html_card = f"""
            <div class="question-card" style="border: 2px solid #FFD700;">
                <div class="question-header">
                    <div><strong>{q['Year']}</strong> | {q['Chapter']} > {q['Topic']}</div>
                    <div class="badge {badge_class}">{q['Difficulty']}</div>
                </div>
                <h5 style="color: #212529;">Q. {q['question_text']}</h5>
                <ul style="list-style-type: none; padding-left: 0;">
            """
            for key, val in q['options'].items():
                html_card += f"<li style='margin-bottom: 5px;'><strong>{key})</strong> {val}</li>"
            html_card += "</ul></div>"
            st.markdown(html_card, unsafe_allow_html=True)
            
            if st.button("Close Surprise Challenge"):
                st.session_state.show_surprise = False
                st.rerun()
        st.divider()

    if not all_questions:
        st.warning("⚠️ No questions found in the database. Please check database.json.")
        return

    # Phase 5: Progress Dashboard
    st.subheader("📊 Your Progress")
    
    # Block 1: Smart Data & Syllabus Tracker
    total_questions = len(all_questions)
    completed_questions = st.session_state.correct
    progress_val = min(completed_questions / total_questions, 1.0) if total_questions > 0 else 0.0
    st.progress(progress_val)
    st.write(f"Aapne **{completed_questions} out of {total_questions}** questions sahi solve kar liye hain. Keep it up!")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("Total Attempted", st.session_state.attempted)
    with col_b:
        st.metric("Correct Answers", st.session_state.correct)
    with col_c:
        acc = 0 if st.session_state.attempted == 0 else int((st.session_state.correct / st.session_state.attempted) * 100)
        st.metric("Accuracy", f"{acc}%")
    st.divider()

    # Extract unique values for filters
    classes = sorted(list(set(q['Class'] for q in all_questions)))
    subjects = sorted(list(set(q['Subject'] for q in all_questions)))

    # --- Sidebar Filters ---
    st.sidebar.divider()
    st.sidebar.subheader("🎯 Navigation")
    
    classes = sorted(list(set(q['Class'] for q in all_questions)))
    selected_class = st.sidebar.selectbox("1. Select Class", ["All"] + classes)
    
    if selected_class != "All":
        subjects = sorted(list(set(q['Subject'] for q in all_questions if q['Class'] == selected_class)))
    else:
        subjects = sorted(list(set(q['Subject'] for q in all_questions)))
    selected_subject = st.sidebar.selectbox("2. Select Subject", ["All"] + subjects)
    
    if selected_subject != "All":
        topics = sorted(list(set(q['Topic'] for q in all_questions if q['Subject'] == selected_subject and (selected_class == "All" or q['Class'] == selected_class))))
    else:
        topics = []
    
    if topics:
        selected_topic_filter = st.sidebar.selectbox("3. Select Topic", ["All"] + topics)
    else:
        selected_topic_filter = "All"
        if selected_subject != "All":
            st.sidebar.info("No specific topics found.")

    st.sidebar.divider()

    # --- Apply Filters ---
    filtered_questions = all_questions
    
    if selected_class != "All":
        filtered_questions = [q for q in filtered_questions if q['Class'] == selected_class]
        
    if selected_subject != "All":
        filtered_questions = [q for q in filtered_questions if q['Subject'] == selected_subject]

    if selected_topic_filter != "All":
        filtered_questions = [q for q in filtered_questions if q['Topic'] == selected_topic_filter]
        
    # Search Topic or Chapter
    search_topic = st.text_input("🔍 Search Topics or Chapters (Across all filters)")
    if search_topic:
        search_lower = search_topic.lower()
        filtered_questions = [
            q for q in filtered_questions 
            if search_lower in q['Topic'].lower() or search_lower in q['Chapter'].lower()
        ]

    # --- Display Questions ---
    st.subheader(f"Questions Found: {len(filtered_questions)}")
    
    # Phase 5: PDF Mock Test Generator
    if filtered_questions:
        topic_name = search_topic if search_topic else "Mixed Topics"
        pdf_bytes = generate_pdf(filtered_questions, topic_name)
        if pdf_bytes:
            st.download_button(
                label="📄 Download Mock Test (PDF)",
                data=bytes(pdf_bytes),
                file_name=f"MockTest_{topic_name}.pdf",
                mime="application/pdf"
            )
        else:
            st.warning("⚠️ PDF generation currently unavailable for these questions.")

    for idx, q in enumerate(filtered_questions):
        # Determine badge class for difficulty
        diff = q['Difficulty'].lower()
        badge_class = f"badge-{diff}" if diff in ['easy', 'medium', 'hard'] else "badge-medium"
        
        # We use a mix of st.container and raw HTML to achieve the card look
        with st.container():
            html_card = f"""
            <div class="question-card">
                <div class="question-header">
                    <div><strong>{q['Year']}</strong> | {q['Chapter']} > {q['Topic']}</div>
                    <div class="badge {badge_class}">{q['Difficulty']}</div>
                </div>
                <h5 style="color: #212529;">Q{idx + 1}. {q['question_text']}</h5>
                <ul style="list-style-type: none; padding-left: 0;">
            """
            for key, val in q['options'].items():
                html_card += f"<li style='margin-bottom: 5px;'><strong>{key})</strong> {val}</li>"
            html_card += "</ul></div>"
            
            st.markdown(html_card, unsafe_allow_html=True)
            # Phase 7: Cheat Sheet Feature
            if st.button(f"📝 {q['Topic']} Cheat Sheet", key=f"cheat_{q['question_id']}"):
                if client:
                    with st.spinner(f"Generating Cheat Sheet for {q['Topic']}..."):
                        cheat_prompt = f"Create a 3-point cheat sheet for the Class 10 Science topic '{q['Topic']}'. Focus STRICTLY on the 3 most important concepts that are guaranteed to appear in board exams. Use short bullet points and bold key terms."
                        models_to_try = ["llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "mixtral-8x7b-32768"]
                        success = False
                        for model_name in models_to_try:
                            try:
                                response = client.chat.completions.create(
                                    model=model_name,
                                    messages=[{"role": "user", "content": cheat_prompt}]
                                )
                                st.info(response.choices[0].message.content)
                                success = True
                                break
                            except Exception as e:
                                if "Model not found" in str(e):
                                    continue
                                st.error(f"Error: {e}")
                                break
                        if not success:
                            st.error("Could not find a compatible Groq model. Please check your API access.")
                else:
                    st.info("💡 (AI offline. Add API key in sidebar to get dynamic cheat sheets!)")

            # Phase 4: AI Teacher Interaction
            with st.expander("💡 Click to Solve & Get AI Insight"):
                submit_key = f"submitted_{q['question_id']}"
                has_submitted = submit_key in st.session_state
                
                user_choice = st.radio(
                    "Your Answer:", 
                    options=list(q['options'].keys()), 
                    key=f"radio_{q['question_id']}", 
                    index=None,
                    disabled=has_submitted
                )
                
                if not has_submitted:
                    if st.button("Submit", key=f"btn_{q['question_id']}"):
                        if not user_choice:
                            st.warning("Please select an answer first.")
                        else:
                            st.session_state[submit_key] = user_choice
                            st.rerun()
                else:
                    saved_choice = st.session_state[submit_key]
                    is_correct = (saved_choice == q['correct_answer'])
                    
                    # Tracking progress (only counted once because of answered_qs set)
                    if q['question_id'] not in st.session_state.answered_qs:
                        st.session_state.attempted += 1
                        st.session_state.answered_qs.add(q['question_id'])
                        if is_correct:
                            st.session_state.correct += 1
                            st.session_state.topic_streak[q['Topic']] = 0
                        else:
                            st.session_state.topic_mistakes[q['Topic']] = st.session_state.topic_mistakes.get(q['Topic'], 0) + 1
                            st.session_state.topic_streak[q['Topic']] = st.session_state.topic_streak.get(q['Topic'], 0) + 1
                    
                    if is_correct:
                        st.success(f"Correct! 🎉 The answer is {q['correct_answer']}.")
                        st.balloons()
                    else:
                        st.error(f"Incorrect. 😔 The correct answer is {q['correct_answer']}.")
                        
                        # Gap Analysis Trigger
                        streak = st.session_state.topic_streak.get(q['Topic'], 0)
                        if streak >= 3:
                            st.warning("Don't worry! Let's simplify this topic before we move forward.")
                            if client:
                                with st.spinner("AI Teacher is generating a 1-minute summary..."):
                                    warning = get_gap_analysis_warning(client, q['Topic'])
                                    st.info(f"💡 **1-Minute Summary:**\n\n{warning}")
                    
                    # Teacher's Insight Button appears ONLY after submission
                    if st.button("Teacher's Insight", key=f"insight_{q['question_id']}"):
                        if client:
                            with st.spinner("AI Teacher is analyzing your answer..."):
                                explanation = get_ai_explanation(
                                    client,
                                    q['question_text'], 
                                    q['options'], 
                                    saved_choice, 
                                    q['correct_answer'], 
                                    is_correct,
                                    q['Topic']
                                )
                                st.markdown("### 🤖 Teacher's Insight")
                                st.write(explanation)
                        else:
                            st.info("💡 (AI Teacher is offline. Add API key in sidebar to activate.)")
                            if "explanations" in q:
                                st.markdown("### 📝 Pre-generated Insight")
                                if is_correct:
                                    st.write(f"**Advanced Insight:** {q['explanations']['advanced']}")
                                else:
                                    st.write(f"**Basic Explanation:** {q['explanations']['basic']}")

    # Phase 5: Session Summary Chart
    st.divider()
    st.subheader("📈 Session Summary")
    if st.session_state.attempted > 0:
        incorrect_count = st.session_state.attempted - st.session_state.correct
        import pandas as pd
        
        # Simple bar chart data
        chart_data = pd.DataFrame(
            {"Count": [st.session_state.correct, incorrect_count]}, 
            index=["Correct", "Incorrect"]
        )
        
        st.bar_chart(chart_data, color="#4CAF50") # Use a clean green, though streamlit usually handles color
    else:
        st.info("Answer some questions to see your session summary chart!")

if __name__ == "__main__":
    main()
