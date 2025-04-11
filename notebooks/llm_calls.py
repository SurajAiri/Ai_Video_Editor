import os
from litellm import completion
from dotenv import load_dotenv

load_dotenv()
# # Replace with your Google API Key
# os.environ["GOOGLE_API_KEY"] = "your-api-key-here"

response = completion(
    api_key=os.getenv("GOOGLE_API_KEY"),
    model="gemini/gemini-1.5-flash",  # Gemini Pro via LiteLLM
    messages=[
        {"role": "user", "content": "What's a quick summary of the Python programming language?"}
    ]
)

print(response["choices"][0]["message"]["content"])
