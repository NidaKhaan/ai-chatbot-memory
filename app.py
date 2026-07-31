import streamlit as st
from db import init_db, get_existing_sessions, load_session_history, save_message, new_session_id
from chat import get_reply, trim_history, SYSTEM_PROMPT
from groq import APIError, APIConnectionError

st.set_page_config(page_title="Synapse — AI with Memory", page_icon="assets/synapse-avatar.svg", layout="centered")

conn = init_db()

if "session_id" not in st.session_state:
    st.session_state.session_id = None
    st.session_state.history = []

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

.pulse-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: #6C5CE7;
    box-shadow: 0 0 0 0 rgba(108, 92, 231, 0.7);
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0% { box-shadow: 0 0 0 0 rgba(108, 92, 231, 0.6); }
    70% { box-shadow: 0 0 0 10px rgba(108, 92, 231, 0); }
    100% { box-shadow: 0 0 0 0 rgba(108, 92, 231, 0); }
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

.stButton button {
    background-color: #1A1D24;
    color: #E8E9ED;
    border: 1px solid #23262F;
    border-radius: 8px;
    font-family: 'Inter', sans-serif;
}

.stButton button:hover {
    border-color: #6C5CE7;
    color: #6C5CE7;
}
</style>
""", unsafe_allow_html=True)

# ---------- Sidebar ----------
st.sidebar.markdown("### Sessions")

sessions = get_existing_sessions(conn)

if st.sidebar.button("＋ New Session", use_container_width=True):
    st.session_state.session_id = new_session_id()
    st.session_state.history = [SYSTEM_PROMPT]
    st.rerun()

if sessions:
    st.sidebar.markdown("**Resume:**")
    for i, (session_id, started, count) in enumerate(sessions, start=1):
        date_only = started.split("T")[0]
        label = f"Session {i} · {date_only} · {count} msgs"
        if st.sidebar.button(label, key=f"resume_{session_id}", use_container_width=True):
            st.session_state.session_id = session_id
            st.session_state.history = load_session_history(conn, session_id)
            st.rerun()

# ---------- Main ----------
st.markdown("""
<div class="synapse-header">
    <div class="pulse-dot"></div> Synapse
</div>
<div class="synapse-sub">An AI that remembers the conversation, not just the message.</div>
""", unsafe_allow_html=True)

if st.session_state.session_id is None:
    st.info("Start a new session or resume one from the sidebar to begin.")
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