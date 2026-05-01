import os
from dotenv import load_dotenv
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage

# 👇 This loads your .env file
load_dotenv()

api_key = os.getenv("MISTRAL_API_KEY")

if not api_key:
    raise ValueError("❌ API key missing")

client = MistralClient(api_key=api_key)

response = client.chat(
    model="mistral-small-latest",
    messages=[
        ChatMessage(role="user", content="Say hello in one sentence.")
    ]
)

print(response.choices[0].message.content)