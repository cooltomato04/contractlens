import os
import base64
from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser

# Load environment variables
load_dotenv()

# Check for production API key
anthropic_key = os.getenv("ANTHROPIC_API_KEY")

if anthropic_key:
    # Production deployment using Claude
    from langchain_anthropic import ChatAnthropic
    
    chat_model = ChatAnthropic(
        model_name="claude-3-5-sonnet-latest",
        anthropic_api_key=anthropic_key,
        temperature=0.0
    )
    llm = chat_model | StrOutputParser()
else:
    # Development mode using local Ollama model
    from langchain_community.llms import Ollama
    
    api_url = os.getenv("LLM_API_URL")
    username = os.getenv("LLM_USERNAME")
    password = os.getenv("LLM_PASSWORD")
    model_name = os.getenv("LLM_MODEL", "qwen3:30b-a3b-q4_K_M")
    
    if api_url:
        base_url = api_url.replace("/api/generate", "").replace("/api/chat", "")
    else:
        base_url = "http://localhost:11434"
        
    headers = {}
    if username and password:
        auth_str = f"{username}:{password}"
        b64_auth = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")
        headers["Authorization"] = f"Basic {b64_auth}"
        
    ollama_model = Ollama(
        base_url=base_url,
        model=model_name,
        headers=headers,
        temperature=0.0
    )
    llm = ollama_model | StrOutputParser()
