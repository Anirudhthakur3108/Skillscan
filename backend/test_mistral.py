import os
from dotenv import load_dotenv
from mistralai.client import Mistral

load_dotenv()

api_key = os.getenv("MISTRAL_API_KEY", "")

if not api_key or api_key == "your_mistral_api_key_here":
    print("STATUS: API Key is MISSING or set to placeholder.")
else:
    print(f"STATUS: API Key found (starts with: {api_key[:4]}...)")
    client = Mistral(api_key=api_key)
    try:
        response = client.chat.complete(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": "Say 'API Working'"}],
            max_tokens=10
        )
        print(f"RESPONSE: {response.choices[0].message.content}")
        print("RESULT: SUCCESS")
    except Exception as e:
        print(f"RESULT: FAILED - {e}")
