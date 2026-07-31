import sqlite3
import uuid
from datetime import datetime

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


def new_session_id():
    return str(uuid.uuid4())[:8]