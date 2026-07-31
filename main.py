import os
import logging
from dotenv import load_dotenv
from groq import Groq, APIError, APIConnectionError

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

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

        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=history
            )
            assistant_reply = response.choices[0].message.content

        except APIConnectionError as e:
            logger.error(f"Connection failed: {e}")
            print("Bot: Network issue, couldn't reach the AI. Try again.\n")
            history.pop()  # remove the unanswered user message
            continue

        except APIError as e:
            logger.error(f"API error: {e}")
            print("Bot: Something went wrong on the API side. Try again.\n")
            history.pop()
            continue

        history.append({"role": "assistant", "content": assistant_reply})
        trim_history(history)

        print(f"Bot: {assistant_reply}\n")


if __name__ == "__main__":
    main()