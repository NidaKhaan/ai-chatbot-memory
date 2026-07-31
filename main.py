import logging
from db import init_db, get_existing_sessions, load_session_history, save_message, new_session_id, delete_session
from chat import get_reply, trim_history, SYSTEM_PROMPT
from groq import APIError, APIConnectionError

logger = logging.getLogger(__name__)


def choose_session(conn):
    sessions = get_existing_sessions(conn)

    if not sessions:
        return new_session_id()

    print("\nExisting sessions found:")
    for i, (session_id, started, count, title) in enumerate(sessions, start=1):
        preview = (title[:40] + "…") if title and len(title) > 40 else (title or "New chat")
        print(f"  {i}. {preview}  ({count} messages)")

    print(f"  N. Start a new session")
    print(f"  D. Delete a session")

    choice = input("\nChoose a session number to resume, 'N' for new, or 'D' to delete: ").strip().lower()

    if choice == "n":
        return new_session_id()

    if choice == "d":
        del_choice = input("Enter the number of the session to delete: ").strip()
        try:
            index = int(del_choice) - 1
            if 0 <= index < len(sessions):
                delete_session(conn, sessions[index][0])
                print("Session deleted.\n")
        except ValueError:
            print("Invalid input, nothing deleted.\n")
        return choose_session(conn)

    try:
        index = int(choice) - 1
        if 0 <= index < len(sessions):
            return sessions[index][0]
    except ValueError:
        pass

    print("Invalid choice, starting a new session instead.\n")
    return new_session_id()


def main():
    conn = init_db()
    session_id = choose_session(conn)
    history = load_session_history(conn, session_id)
    if not history:
        history = [SYSTEM_PROMPT]

    print(f"\nSession: {session_id}")
    print(f"Loaded {len(history)} prior messages." if len(history) > 1 else "Starting fresh.")
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
            assistant_reply = get_reply(history)

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