import requests
import random
import json
import os
import streamlit as st

API_KEY = os.environ["API_KEY"]

def generate_quiz(text_input, num_questions=3, difficulty="Medium"):
    """
    Sends a prompt to the local Ollama instance to generate a JSON quiz.
    """
    
    api_key = st.secrets["LLM_API_KEY"]
    # 1. Define the Endpoint
    url = f"https://api-gateway.netdb.csie.ncku.edu.tw/api/chat"
    
    # 2. Define the Prompt
    # We explicitly ask for a JSON array structure.
    prompt = f"""
    You are a Teacher AI. Your goal is to generate a quiz based on the user's text.
    
    Instructions:
    1. Create {num_questions} multiple-choice questions based on the text below.
    2. Difficulty Level: {difficulty}.
    2-1. Based on the given difficulty level, generate questions as followed:
    Easy: Blank a keyword in a statement of user text, and use the keyword as the answer. Alternatively, generate "fill in the blank" problems. Example: "The _____ is the powerhouse of the cell".
    Medium: Phrase a problem based on a statement in user text. Do not include the answer. OR: Ask what a keyword in user text means, and use descriptions of keywords as answer choices.
    Hard: Any, you may use answers that require calculations.
    
    3. You must output ONLY a raw JSON array as indicated by the following structure. Do not add markdown formatting like ```json.
    
    Required JSON Structure:
    {{'quiz':[
        {{
            "question": "The question text",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "answer": "The exact text of the correct option",
            "explanation": "A short explanation of why it is correct. If the answer is factual information, use verified facts outside given text as reference if possible. If you really must refer to user text, give detailed explanations that aren't mentioned in the text."
        }}, //followed by the next question
    ]}}

    User Text:
    "{text_input}"
    
    4. Additional instructions for generating answers:
    If the answer is a numeric value, make sure it follows number format like 987,654,321.12345.\
    If the answer has a unit, make sure other choices have the same unit
    
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + api_key,
    }

    # 3. Construct the Payload
    payload = {
        "model": "gemma3:4b",  # <--- CHANGE THIS to your installed model (e.g. 'mistral')
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that outputs strict JSON."},
            {"role": "user", "content": prompt}
        ],
        "format": "json",   # <--- CRITICAL: Forces Ollama to output valid JSON
        "stream": False     # Keep it false to get the whole response at once
    }

    try:
        # 4. Make the Request
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status() # Check for HTTP errors
        
        # 5. Parse the Response
        result = response.json()
        
        print("result:")
        print(result)
        print()
        
        content = result['message']['content']
        content = content.replace("```json", "").replace("```", "").strip()
        
        quiz_data = json.loads(content)['quiz']
        
        print("quiz_data:")
        print(quiz_data)
        print()

        # 2. VALIDATE AND FIX <--- Add this step
        quiz_data = validate_and_fix_quiz(quiz_data)
        
        return quiz_data


    except requests.exceptions.ConnectionError:
        return {"error": "Could not connect to Ollama. Is it running?"}
    except json.JSONDecodeError:
        return {"error": "The model failed to return valid JSON. Try again."}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}
    
def validate_and_fix_quiz(quiz_data):
    """
    Ensures every question has the correct answer listed in its options.
    If the answer is missing, it overwrites a random option with the answer.
    """
    for q in quiz_data:
        # Get the correct answer string and the list of options
        correct_ans = q.get("answer", "").strip()
        options = q.get("options", [])

        # Basic cleanup: ensure we actually have options
        if not options:
            q["options"] = ["Error", "Error", "Error", correct_ans]
            continue

        # CHECK: Is the answer in the list?
        # We use a case-insensitive check to be safe (e.g., "CPU" vs "cpu")
        # specific implementation depends on exact string matching needs
        
        if correct_ans not in options:
            # --- THE FIX ---
            # The LLM forgot to include the answer in the choices.
            # We will overwrite the first option (or a random one) with the correct answer.
            
            # optional: shuffle so the answer isn't always the first one
            random_index = random.randint(0, len(options) - 1)
            options[random_index] = correct_ans
            
            # Update the list in the dictionary
            q["options"] = options
            
    return quiz_data