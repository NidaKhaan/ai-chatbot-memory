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
MAX_HISTORY_MESSAGES = 20

SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are Synapse, a sharp and concise AI assistant with persistent memory. "
        "You remember details the user shares and reference them naturally when relevant. "
        "Keep responses focused and conversational — no unnecessary filler."
    )
}


def trim_history(history):
    if len(history) > MAX_HISTORY_MESSAGES:
        overflow = len(history) - MAX_HISTORY_MESSAGES
        del history[:overflow]


def get_reply(history):
    """
    Sends the full history to Groq and returns the assistant's reply text.
    Raises APIConnectionError or APIError on failure — caller decides how to handle it.
    """
    response = client.chat.completions.create(
        model=MODEL,
        messages=history
    )
    return response.choices[0].message.content