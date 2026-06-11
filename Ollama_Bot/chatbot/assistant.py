from datetime import datetime
from chatbot.ollama_client import OllamaClient
from chatbot.prompt_templates import build_messages, get_fallback_response
from backend.models import ChatHistory

# Single shared client — re-checks availability on each request
_client = OllamaClient()


def process_message(session_id: str, user_message: str, db) -> str:
    """
    Process a user message:
    1. Persist user turn
    2. Build prompt from history
    3. Query Ollama (or fall back to rule engine)
    4. Persist assistant turn
    5. Return assistant reply
    """
    # 1. Save the user message
    db.add(ChatHistory(
        session_id=session_id,
        role="user",
        message=user_message,
        timestamp=datetime.utcnow(),
    ))
    db.commit()

    # 2. Load recent history (excluding the message just saved, already included via build_messages)
    rows = (
        db.query(ChatHistory)
        .filter(ChatHistory.session_id == session_id)
        .order_by(ChatHistory.timestamp.asc())
        .limit(20)
        .all()
    )
    history = [{"role": r.role, "message": r.message} for r in rows[:-1]]  # exclude last (current user msg)

    # 3. Generate response
    if _client.is_available():
        try:
            messages = build_messages(history, user_message)
            response = _client.chat(messages)
        except Exception as e:
            print(f"[Ollama] Error: {e} — falling back to rule engine.")
            response = get_fallback_response(user_message)
    else:
        print("[Ollama] Offline — using rule engine.")
        response = get_fallback_response(user_message)

    # 4. Save assistant response
    db.add(ChatHistory(
        session_id=session_id,
        role="assistant",
        message=response,
        timestamp=datetime.utcnow(),
    ))
    db.commit()

    return response
