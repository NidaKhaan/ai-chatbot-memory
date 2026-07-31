import base64
import streamlit as st
from db import init_db, get_existing_sessions, load_session_history, save_message, new_session_id, delete_session
from chat import get_reply, trim_history, SYSTEM_PROMPT
from groq import APIError, APIConnectionError

st.set_page_config(page_title="Synapse — AI with Memory", page_icon="assets/synapse-avatar.svg", layout="centered")

conn = init_db()

if "session_id" not in st.session_state:
    st.session_state.session_id = None
    st.session_state.history = []


def load_svg_as_data_uri(path):
    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/svg+xml;base64,{encoded}"


synapse_logo = load_svg_as_data_uri("assets/synapse-avatar.svg")

# ---------- Custom styling ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background-color: #0F1115;
    color: #E8E9ED;
}

section[data-testid="stSidebar"] {
    background-color: #14161C;
    border-right: 1px solid #23262F;
}

.synapse-header {
    display: flex;
    align-items: center;
    gap: 10px;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 28px;
    margin-bottom: 0px;
}

.synapse-logo {
    width: 32px;
    height: 32px;
}

.synapse-sub {
    color: #8B8FA3;
    font-size: 14px;
    margin-top: 2px;
    margin-bottom: 24px;
}

div[data-testid="stChatMessage"] {
    background-color: #1A1D24;
    border-radius: 12px;
    border: 1px solid #23262F;
}

.stButton button[kind="primary"] {
    background-color: #6C5CE7;
    color: #FFFFFF;
    border: none;
}

.stButton button[kind="primary"]:hover {
    background-color: #5b4dd1;
    color: #FFFFFF;
}

.stButton button[kind="secondary"] {
    background-color: #1A1D24;
    color: #E8E9ED;
    border: 1px solid #23262F;
    text-align: left;
    justify-content: flex-start;
}

.stButton button[kind="secondary"]:hover {
    border-color: #6C5CE7;
    color: #6C5CE7;
}

.delete-btn button {
    background-color: transparent;
    border: none;
    color: #8B8FA3;
    padding: 0px;
}

.delete-btn button:hover {
    color: #E05252;
}
</style>
""", unsafe_allow_html=True)

# ---------- Sidebar ----------
st.sidebar.markdown("### Synapse")

if st.sidebar.button("＋ New chat", use_container_width=True, type="primary"):
    st.session_state.session_id = new_session_id()
    st.session_state.history = [SYSTEM_PROMPT]
    st.rerun()

sessions = get_existing_sessions(conn)

if sessions:
    st.sidebar.markdown(
        "<div style='color:#8B8FA3; font-size:12px; margin:16px 0 4px; text-transform:uppercase; letter-spacing:0.5px;'>Recent</div>",
        unsafe_allow_html=True
    )

    for session_id, started, count, title in sessions:
        display_title = (title[:28] + "…") if title and len(title) > 28 else (title or "New chat")
        is_active = session_id == st.session_state.session_id
        button_type = "primary" if is_active else "secondary"

        col1, col2 = st.sidebar.columns([5, 1])

        with col1:
            if st.button(display_title, key=f"resume_{session_id}", use_container_width=True, type=button_type):
                st.session_state.session_id = session_id
                st.session_state.history = load_session_history(conn, session_id)
                st.rerun()

        with col2:
            st.markdown('<div class="delete-btn">', unsafe_allow_html=True)
            if st.button("✕", key=f"delete_{session_id}"):
                delete_session(conn, session_id)
                if st.session_state.session_id == session_id:
                    st.session_state.session_id = None
                    st.session_state.history = []
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# ---------- Main ----------
st.markdown(f"""
<div class="synapse-header">
    <img src="{synapse_logo}" class="synapse-logo" /> Synapse
</div>
<div class="synapse-sub">An AI that remembers the conversation, not just the message.</div>
""", unsafe_allow_html=True)

if st.session_state.session_id is None:
    st.info("Start a new chat or resume one from the sidebar to begin.")
else:
    for msg in st.session_state.history:
        if msg["role"] == "system":
            continue
        avatar = "assets/synapse-avatar.svg" if msg["role"] == "assistant" else "assets/user-avatar.svg"
        with st.chat_message(msg["role"], avatar=avatar):
            st.write(msg["content"])

    user_input = st.chat_input("Message Synapse...")

    if user_input:
        if not user_input.strip():
            st.warning("Empty input ignored.")
        else:
            st.session_state.history.append({"role": "user", "content": user_input})
            with st.chat_message("user", avatar="assets/user-avatar.svg"):
                st.write(user_input)

            try:
                with st.spinner("Synapse is thinking..."):
                    assistant_reply = get_reply(st.session_state.history)

                st.session_state.history.append({"role": "assistant", "content": assistant_reply})
                trim_history(st.session_state.history)

                save_message(conn, st.session_state.session_id, "user", user_input)
                save_message(conn, st.session_state.session_id, "assistant", assistant_reply)

                with st.chat_message("assistant", avatar="assets/synapse-avatar.svg"):
                    st.write(assistant_reply)

            except (APIConnectionError, APIError) as e:
                st.session_state.history.pop()
                st.error("Something went wrong reaching Synapse. Try again.")