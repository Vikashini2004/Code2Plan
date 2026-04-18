import streamlit as st
from supabase import create_client
from openai import OpenAI

# Initialize Supabase
url = "https://yuhhpwvnjlcsqdvbvefv.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inl1aGhwd3Zuamxjc3FkdmJ2ZWZ2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYzMzk2MDYsImV4cCI6MjA5MTkxNTYwNn0.47Nx0lU3BW0miDriqE-ozk8KDIvPFocAuUPtW6R3bbQ"
supabase = create_client(url, key)

# 2. Ollama AI Setup
# We use the OpenAI SDK because Ollama supports its format.
# Ensure you have run: ollama pull llama3 (or qwen2.5-coder)
ai_client = OpenAI(
    base_url="http://localhost:11434/v1", 
    api_key="ollama" # Not used by Ollama but required by the library
)

# 3. Model Name (Change to 'qwen2.5-coder' if you want better code tasks)
MODEL_NAME = "llama3-groq-tool-use"
