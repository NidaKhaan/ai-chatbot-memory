import os
import logging
import sqlite3
import uuid
from datetime import datetime
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
DB_PATH = "chat_history.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


def get_existing_sessions(conn):
    cursor = conn.execute("""
        SELECT session_id, MIN(timestamp) as started, COUNT(*) as msg_count
        FROM messages
        GROUP BY session_id
        ORDER BY started DESC
    """)
    return cursor.fetchall()


def load_session_history(conn, session_id):
    cursor = conn.execute(
        "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id ASC",
        (session_id,)
    )
    return [{"role": row[0], "content": row[1]} for row in cursor.fetchall()]


def save_message(conn, session_id, role, content):
    conn.execute(
        "INSERT INTO messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
        (session_id, role, content, datetime.now().isoformat())
    )
    conn.commit()


def choose_session(conn):
    sessions = get_existing_sessions(conn)

    if not sessions:
        return str(uuid.uuid4())[:8]

    print("\nExisting sessions found:")
    for i, (session_id, started, count) in enumerate(sessions, start=1):
        print(f"  {i}. {session_id}  (started {started}, {count} messages)")

    print(f"  N. Start a new session")

    choice = input("\nChoose a session number to resume, or 'N' for new: ").strip().lower()

    if choice == "n":
        return str(uuid.uuid4())[:8]

    try:
        index = int(choice) - 1
        if 0 <= index < len(sessions):
            return sessions[index][0]
    except ValueError:
        pass

    print("Invalid choice, starting a new session instead.\n")
    return str(uuid.uuid4())[:8]


def trim_history(history):
    if len(history) > MAX_HISTORY_MESSAGES:
        overflow = len(history) - MAX_HISTORY_MESSAGES
        del history[:overflow]


def main():
    conn = init_db()
    session_id = choose_session(conn)
    history = load_session_history(conn, session_id)

    print(f"\nSession: {session_id}")
    print(f"Loaded {len(history)} prior messages." if history else "Starting fresh.")
    print("Type 'exit' to quit.\n")

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
            history.pop()
            continue

        except APIError as e:
            logger.error(f"API error: {e}")
            print("Bot: Something went wrong on the API side. Try again.\n")
            history.pop()
            continue

        history.append({"role": "assistant", "content": assistant_reply})
        trim_history(history)

        save_message(conn, session_id, "user", user_input)
        save_message(conn, session_id, "assistant", assistant_reply)

        print(f"Bot: {assistant_reply}\n")

    conn.close()


if __name__ == "__main__":
    main()