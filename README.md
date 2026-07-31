# AI Chatbot with Memory

A stateful CLI chatbot built on the Groq API (Llama 3.3 70B) that maintains conversation context across a live session.

## Why this project
Frontier LLM APIs are stateless by default — every request is treated as an isolated transaction with no memory of prior turns. This project engineers a **stateful conversational loop** on top of that stateless API by maintaining an in-memory history array, appending each turn, and re-sending the full context with every call.

## Features
- Live multi-turn conversation with context retention
- Input validation guard (blocks empty/whitespace submissions before they hit the API)
- Sliding window (FIFO) history trimming to prevent token/context overflow
- Graceful error handling for network and API failures, with logging

## Tech Stack
- Python 3.11
- Groq API (`groq` SDK) — free tier, OpenAI-compatible schema
- `python-dotenv` for secrets management

## Setup
1. Clone the repo
2. Create a virtual environment: `python -m venv venv` then activate it
3. Install dependencies: `pip install -r requirements.txt`
4. Create a `.env` file in the root:
5. Run: `python main.py`

## Usage
Type normally to chat. Type `exit` to end the session.

## Architecture Notes
- History is stored as a list of `{"role": ..., "content": ...}` objects — the standard chat-completion schema used across OpenAI-compatible APIs.
- History is capped at 20 messages (10 turns); oldest messages are dropped first when the cap is exceeded.
- On API failure, the unanswered user message is removed from history to keep the payload structurally consistent for the next request.

## Known Limitations
- Memory is session-only — no persistence across restarts (planned as a future milestone: SQLite/JSON-based storage).
- Trimming is message-count based, not token-count based.