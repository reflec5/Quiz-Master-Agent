import streamlit as st
import agent_logic

# Page Configuration
st.set_page_config(page_title="Quiz Master", page_icon="🎓")

st.title("🎓 Quiz Master - AI Quiz Generator")
st.caption("Powered by Ollama")

# --- SIDEBAR: SETTINGS ---
with st.sidebar:
    st.header("Settings")
    difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])
    num_questions = st.slider("Number of Questions", 1, 5, 3)

# --- MAIN: INPUT ---
st.subheader("1. Provide Study Material")
user_text = st.text_area("Paste your notes, article, or code snippet here:", height=200)

# Initialize Session State
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None
if "answers" not in st.session_state:
    st.session_state.answers = {}

# --- ACTION: GENERATE ---
if st.button("Generate Quiz", type="primary"):
    if not user_text:
        st.warning("Please enter some text first.")
    else:
        with st.spinner("Agent is analyzing text and generating questions..."):
            # Call the backend
            data = agent_logic.generate_quiz(user_text, num_questions, difficulty)
            print(data)
            
            # Error Handling
            if isinstance(data, dict) and "error" in data:
                st.error(data["error"])
            else:
                st.session_state.quiz_data = data
                st.session_state.answers = {} # Reset answers
                
                st.rerun() # Refresh to show the quiz

# --- MAIN: QUIZ DISPLAY ---
if st.session_state.quiz_data:
    st.divider()
    st.subheader("2. Take the Quiz")
    
    score = 0
    total = len(st.session_state.quiz_data)
    
    # Loop through questions
    for i, q in enumerate(st.session_state.quiz_data):
        st.markdown(f"#### Q{i+1}: {q['question']}")
        
        # Create a unique key for each radio button using the index 'i'
        user_choice = st.radio(
            "Select an answer:", 
            q['options'], 
            key=f"q_{i}", 
            index=None
        )
        
        # Check Answer Button
        if st.button(f"Check Answer {i+1}"):
            if user_choice == q['answer']:
                st.success("✅ Correct!")
            elif user_choice:
                st.error(f"❌ Wrong. The correct answer is **{q['answer']}**")
                st.info(f"💡 Explanation: {q['explanation']}")
            else:
                st.warning("Please select an option.")
        
        st.markdown("---")
    
    # Reset Button
    if st.button("Start Over"):
        st.session_state.quiz_data = None
        st.rerun()