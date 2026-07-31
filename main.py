import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = "llama-3.3-70b-versatile"
MAX_HISTORY_MESSAGES = 20  # keeps last 10 user+assistant turns


def trim_history(history):
    if len(history) > MAX_HISTORY_MESSAGES:
        overflow = len(history) - MAX_HISTORY_MESSAGES
        del history[:overflow]


def main():
    history = []
    print("Chatbot ready. Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ")

        if user_input.strip().lower() == "exit":
            print("Session ended.")
            break

        if not user_input.strip():
            print("Bot: (empty input ignored, please type something)\n")
            continue

        history.append({"role": "user", "content": user_input})

        response = client.chat.completions.create(
            model=MODEL,
            messages=history
        )

        assistant_reply = response.choices[0].message.content
        history.append({"role": "assistant", "content": assistant_reply})
        trim_history(history)

        print(f"Bot: {assistant_reply}\n")


if __name__ == "__main__":
    main()