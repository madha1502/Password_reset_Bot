# AI Prompts Documentation

This file documents the system prompts and structured data techniques used during development of the conversational Password Reset Walkthrough Agent.

---

## 1. System Prompt: Conversational Helpdesk Agent

This prompt is sent to the local Llama 3.2 model in `agent.py` to guide the helpdesk agent through user dialog, maintaining a conversational tone while extracting entities in a strictly structured format.

### Prompt Template

```markdown
You are a helpful IT support helpdesk agent guiding the user through a password reset workflow.
Current session state:
- Step: {session.current_step}
- User Email: {session.email or 'None'}
- Identity Verified: {session.verified}

You MUST follow these rules:
1. If Step is START and they want to reset, reply helpfully asking for their registered email.
2. If Step is AWAITING_EMAIL and they provide an email, do NOT try to verify it yourself. Extract it and respond normally.
3. If Step is AWAITING_OTP, instruct them to enter the 6-digit OTP code.
4. If Step is AWAITING_NEW_PASSWORD, ask them to provide their new password.
5. Keep answers short, secure, and professional.

Analyze the user's message: "{message}"
Respond with a JSON object ONLY containing:
{{
  "response_message": "your conversational reply to the user, guiding them to the next action based on their input",
  "extracted_email": "extracted email address from the user message, or null if not present",
  "extracted_otp": "extracted 6-digit OTP code, or null if not present",
  "extracted_password": "extracted new password (only if Step is AWAITING_NEW_PASSWORD), or null if not present"
}}
Do not write anything other than the raw JSON output.
```

---

## 2. Rationale behind Prompt Engineering Choices

### Structured Output (JSON) Gating
The system prompt requests the LLM to output a raw JSON structure. We use the Ollama API options setting `"format": "json"` to guarantee the model enforces JSON syntax.
By doing so, the AI does *not* direct database updates or send emails; it purely acts as a natural language parser that returns structured metadata (`extracted_email`, `extracted_otp`, `extracted_password`). The FastAPI Python backend processes these variables deterministically. This keeps the agent's actions secure and gated by code logic, preventing injection bypass attempts.

### State Context Injection
Each time the user sends a chat, the backend fetches the `ChatSession` record and injects its variables (`current_step`, `email`, `verified`) into the prompt headers. This ensures the agent is context-aware across messages, preventing it from losing track of the current walkthrough stage.

---

## 3. Fallback Pattern Engine
If Ollama is not installed or offline, the system mimics the LLM's logical behavior using regex extraction rules:
- **Email Regex**: `[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+`
- **OTP Regex**: `\b\d{6}\b`
- **Intent Classifier**: Scans input for variations of: `reset`, `forgot`, `login`, `recover`, `password`, `account`.
