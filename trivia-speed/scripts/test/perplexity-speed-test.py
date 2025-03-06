import requests
import time
from dotenv import load_dotenv
import os
from pydantic import BaseModel

# Load environment variables from .env file
load_dotenv()

# Define the Pydantic model for structured output
class TriviaAnalysis(BaseModel):
    rationale: str
    answer: str

# Get API key from environment variables
api_key = os.getenv("PERPLEXITY_API_KEY")
if not api_key:
    raise ValueError("PERPLEXITY_API_KEY not found in environment variables")

url = "https://api.perplexity.ai/chat/completions"
headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

# Sample question for testing
question = "What company created the iPhone?"
options = ["1. Samsung", "2. Apple", "3. Google", "4. Microsoft"]

# Format the question and options like in perplexity.py
user_prompt = f"Question: {question}\n\nOptions:\n" + "\n".join(options)

system_prompt = """
# Role
You are an expert trivia player.

# Task
I will give you a trivia question that has been extracted using OCR. The question will include multiple choice options. 
These questions are coming from Robinhood's trivia game so they are mostly financial questions. 
If you clearly do not know the answer, then say that you do not know.

# Output Format
You MUST provide your response in valid JSON format with these fields:
- "rationale": A very brief explanation (1-2 sentences)
- "answer": The final answer (just the letter or specific answer word/phrase)

Example:
{
  "rationale": "Company X was founded in 1975 by Bill Gates and Paul Allen.",
  "answer": "Microsoft"
}
"""

payload = {
    "model": "sonar-reasoning",
    "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ],
    "temperature": 0.1,  # Lower temperature for more deterministic responses
    "response_format": {
        "type": "json_schema",
        "json_schema": {
            "schema": TriviaAnalysis.model_json_schema()
        }
    }
}

start_time = time.time()
response = requests.post(url, json=payload, headers=headers)
latency = time.time() - start_time
print(f"Latency: {latency:.3f} seconds")

# Parse the response using the Pydantic model
try:
    result = response.json()
    content = result["choices"][0]["message"]["content"]
    analysis = TriviaAnalysis.model_validate_json(content)
    print("\nStructured Response:")
    print(f"Rationale: {analysis.rationale}")
    print(f"Answer: {analysis.answer}")
except Exception as e:
    print("\nError parsing response:", e)
    print("Raw response:", response.json())