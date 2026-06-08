import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()

api_url = os.getenv("LLM_API_URL")
username = os.getenv("LLM_USERNAME")
password = os.getenv("LLM_PASSWORD")
model = os.getenv("LLM_MODEL")

print("API URL:", api_url)
print("Model:", model)
print("Auth provided:", bool(username and password))

# Test payload for Ollama /api/generate endpoint
payload = {
    "model": model,
    "prompt": "Say hello in exactly 3 words.",
    "stream": False
}

try:
    auth = HTTPBasicAuth(username, password) if username and password else None
    response = requests.post(api_url, json=payload, auth=auth, timeout=30)
    print("Status Code:", response.status_code)
    try:
        data = response.json()
        print("Response JSON:")
        print(data)
        if "response" in data:
            print(f"\nModel output: {data['response']}")
    except Exception:
        print("Response Text:", response.text)
except Exception as e:
    print("Error:", e)
