from openai import OpenAI
import os

import streamlit as st

# Load API key from Streamlit secrets
api_key = st.secrets.get("GROQ_API_KEY")

if not api_key:
    import os
    api_key = os.environ.get("GROQ_API_KEY")

if not api_key:
    print("Error: GROQ_API_KEY not found in secrets or environment variables.")
    exit()

client = OpenAI(
    api_key=api_key,
    base_url="https://api.groq.com/openai/v1"
)

try:
    models = client.models.list()
    print("Available Models:")
    for model in models.data:
        print(f"- {model.id}")
except Exception as e:
    print(f"Error: {e}")
