import streamlit as st
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import time
from typing import List, Tuple
import os

# Initialize model and tokenizer at startup
print("Loading Phi-1.5 model and tokenizer...")
MODEL = None
TOKENIZER = None

try:
    TOKENIZER = AutoTokenizer.from_pretrained(
        "microsoft/phi-1_5",
        trust_remote_code=True,
        padding_side='left'
    )
    if TOKENIZER.pad_token is None:
        TOKENIZER.pad_token = TOKENIZER.eos_token
        
    MODEL = AutoModelForCausalLM.from_pretrained(
        "microsoft/phi-1_5",
        torch_dtype=torch.float32,
        trust_remote_code=True
    )
    
    if torch.cuda.is_available():
        MODEL = MODEL.to("cuda")
    print("Model and tokenizer loaded successfully!")
except Exception as e:
    print(f"Error loading model: {str(e)}")

# Set page config
st.set_page_config(
    page_title="Phi-1.5 Assistant",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for chat layout with vivid colors
st.markdown("""
    <style>
    .user-message {
        background-color: #4A90E2;  /* Bright blue */
        color: white;
        padding: 15px;
        border-radius: 15px;
        margin: 5px 0;
        float: right;
        clear: both;
        max-width: 80%;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    .bot-message {
        background-color: #50C878;  /* Emerald green */
        color: white;
        padding: 15px;
        border-radius: 15px;
        margin: 5px 0;
        float: left;
        clear: both;
        max-width: 80%;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    .footer {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        padding: 10px;
        text-align: center;
        font-size: 14px;
        color: #808080;
    }
    .chat-container {
        margin-bottom: 60px;
    }
    .stButton>button {
        background-color: #4A90E2;
        color: white;
    }
    /* Custom styling for the chat input area */
    .chat-input-container {
        display: flex;
        gap: 10px;
        align-items: flex-start;
    }
    .chat-textarea {
        flex-grow: 1;
    }
    .send-button {
        min-width: 100px;
    }
    </style>
    <div class="footer">Made with ♥ by Pouryare</div>
""", unsafe_allow_html=True)

# Initialize chat history
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

def generate_response(prompt: str, max_length: int = 100) -> str:
    """
    Generate response using Phi-1.5.
    """
    try:
        formatted_prompt = f"Instruct: {prompt}\nOutput:"
        
        inputs = TOKENIZER(
            formatted_prompt,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        )
        
        if torch.cuda.is_available():
            inputs = {k: v.to("cuda") for k, v in inputs.items()}

        with torch.no_grad():
            outputs = MODEL.generate(
                inputs.input_ids,
                attention_mask=inputs.attention_mask,
                max_new_tokens=max_length,
                num_return_sequences=1,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                pad_token_id=TOKENIZER.pad_token_id,
                eos_token_id=TOKENIZER.eos_token_id,
                repetition_penalty=1.2
            )

        response = TOKENIZER.decode(
            outputs[0][inputs.input_ids.shape[1]:],
            skip_special_tokens=True,
            clean_up_tokenization_spaces=True
        )
        
        return response.strip()

    except Exception as e:
        return f"Error generating response: {str(e)}"

def display_chat_history():
    """Display the chat history with vivid colors."""
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for role, message in st.session_state.chat_history:
        if role == "user":
            st.markdown(f'<div class="user-message">{message}</div>', 
                       unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="bot-message">{message}</div>', 
                       unsafe_allow_html=True)
        st.markdown("<div style='clear: both'></div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def main():
    """Main function to run the Streamlit application."""
    if MODEL is None or TOKENIZER is None:
        st.error("Failed to load the model. Please check the console for error messages.")
        return

    st.title("Phi-1.5 Assistant")
    st.write("Ask me anything!")
    
    st.sidebar.title("Generation Parameters")
    max_length = st.sidebar.slider("Max Response Length", 20, 500, 100)
    
    # Create the chat input area
    with st.form(key="chat_form"):
        col1, col2 = st.columns([8, 1])  # Adjust ratio for better spacing
        
        with col1:
            user_input = st.text_area("Type your message:", height=100, label_visibility="collapsed")
            
        with col2:
            submit_button = st.form_submit_button("Send")
        
        if submit_button and user_input:
            st.session_state.chat_history.append(("user", user_input))
            
            with st.spinner("Generating response..."):
                response = generate_response(user_input, max_length)
                st.session_state.chat_history.append(("bot", response))
    
    display_chat_history()
    
    if st.sidebar.button("Clear Chat", key="clear_chat"):
        st.session_state.chat_history = []
        st.experimental_rerun()

if __name__ == "__main__":
    main()