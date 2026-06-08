import os
import base64
from dotenv import load_dotenv
from langchain_community.llms import Ollama

# Load environment variables
load_dotenv()

# Retrieve API credentials and configuration
api_url = os.getenv("LLM_API_URL")
username = os.getenv("LLM_USERNAME")
password = os.getenv("LLM_PASSWORD")
model_name = os.getenv("LLM_MODEL", "qwen3:30b-a3b-q4_K_M")

# Parse base URL from endpoint URL (remove path suffix if present)
if api_url:
    base_url = api_url.replace("/api/generate", "").replace("/api/chat", "")
else:
    base_url = "http://localhost:11434"

# Set up authorization header if Basic Auth credentials are provided
headers = {}
if username and password:
    auth_str = f"{username}:{password}"
    b64_auth = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")
    headers["Authorization"] = f"Basic {b64_auth}"

# Initialize the Ollama model instance
llm = Ollama(
    base_url=base_url,
    model=model_name,
    headers=headers,
    temperature=0.0
)
