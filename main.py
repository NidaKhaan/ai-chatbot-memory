import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = "llama-3.3-70b-versatile"

def main():
    history = []
    print("Chatbot ready. Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ")

        if user_input.strip().lower() == "exit":
            print("Session ended.")
            break

        history.append({"role": "user", "content": user_input})

        response = client.chat.completions.create(
            model=MODEL,
            messages=history
        )

        assistant_reply = response.choices[0].message.content
        history.append({"role": "assistant", "content": assistant_reply})

        print(f"Bot: {assistant_reply}\n")

if __name__ == "__main__":
    main()