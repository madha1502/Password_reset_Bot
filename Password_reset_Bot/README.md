# AI-Powered Password Reset Walkthrough Bot

A complete, production-quality Proof of Concept (POC) demonstrating an automated, secure IT Helpdesk password reset system. This application guides users through an identity verification flow using a **stateful AI chat agent**, validates their details against an SQLite user database, handles **6-digit One-Time Passwords (OTP)** via a simulated/SMTP email server, updates credentials securely, and records detailed **Audit Logs** for complete auditability.

## Architecture & Technology Stack

- **Backend**: FastAPI (Python 3.9+), SQLAlchemy ORM
- **Database**: SQLite (contains tables for `users`, `otp_codes`, `audit_logs`, `mock_emails`, and `chat_sessions`)
- **Conversational Agent**: Local Llama 3.2 via Ollama (with a robust Python rule-engine fallback if Ollama is offline)
- **Frontend**: Next.js 15 (React, Tailwind CSS, Lucide Icons)

---

## Directory Structure

```
├── backend/
│   ├── .env                 # Environment variables configuration
│   ├── main.py              # FastAPI server entrypoint and CORS settings
│   ├── models.py            # SQLAlchemy database schemas
│   ├── database.py          # SQLite connection and session initialization
│   ├── schemas.py           # Pydantic validation schemas
│   ├── email_service.py     # SMTP service & mock email collector
│   ├── agent.py             # Stateful AI agent logic & rule fallback
│   ├── seed.py              # CLI database initialization and seeding script
│   └── requirements.txt     # Python backend dependencies
└── frontend/
    ├── src/
    │   └── app/
    │       ├── page.tsx     # Split-screen React Dashboard & Chat client
    │       ├── layout.tsx   # Global Next.js page layout
    │       └── globals.css  # CSS and Tailwind imports
    ├── package.json         # Frontend package specifications
    └── tsconfig.json        # TypeScript configuration
```

---

## Setup & Running Guide

### 1. Backend Setup (FastAPI)

1. Open your terminal and navigate to the backend folder:
   ```bash
   cd backend
   ```

2. Create and activate a Python virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install the required Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Seed the database with default mock users:
   ```bash
   python seed.py
   ```

5. Run the FastAPI development server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

The backend API documentation will be available at: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### 2. Frontend Setup (Next.js)

1. Open a new terminal tab/window and navigate to the frontend folder:
   ```bash
   cd frontend
   ```

2. Install the frontend dependencies:
   ```bash
   npm install
   ```

3. Launch the Next.js development server:
   ```bash
   npm run dev
   ```

The application will be accessible at: [http://localhost:3000](http://localhost:3000)

---

## Testing the Password Reset Workflow

To test the application end-to-end, follow this script:

1. **Verify Default Users**:
   Open [http://localhost:3000](http://localhost:3000) and click on the **SQLite User Store** tab on the right side. You will see the default seeded users and their SHA-256 hashed passwords:
   - `user@example.com` (Seed password: `userpass456`)
   - `admin@example.com` (Seed password: `adminpass123`)
   - `test@example.com` (Seed password: `testpass789`)
   - `john.doe@company.com` (Seed password: `companysecure123`)

2. **Trigger Reset Intent**:
   In the Chat Interface (left panel), type:
   > "I forgot my password" or "I can't log in"
   The AI agent will respond, asking you to provide your registered email.

3. **Provide Email**:
   Type:
   > "My email is user@example.com"
   The backend will check the user database. If found, it will generate a 6-digit OTP code, write a transaction to the `mock_emails` table, write an audit log, and prompt you to input the code.

4. **Retrieve OTP Code**:
   Click the **Mock Inbox** tab in the right-hand panel. You will see a new email sent to `user@example.com` with the Subject: *"Your Password Reset OTP Verification Code"*.
   - Click the email in the list.
   - Click **Copy Code** to copy the 6-digit number to your clipboard.

5. **Submit OTP Code**:
   Paste or type the 6-digit code in the chat.
   The backend will verify the code against active codes. Once verified, it will delete the OTP code to prevent reuse, update the session verification state, write an audit log, and prompt you to enter a new password.

6. **Provide New Password**:
   Type in a new password of your choice (minimum 6 characters, e.g. `secretpassword123`).
   The agent will complete the change. Look at the **SQLite User Store** tab — the password hash for `user@example.com` will have instantly changed!
   Look at the **Workflow & Logs** tab — the audit logs timeline will show the complete lifecycle of this request.

---

## AI Agent Dual-Mode Behavior

The agent uses a hybrid approach to ensure robust conversational capabilities:
- **Ollama Mode (Llama 3.2)**: If an Ollama instance is detected on port `11434` with `llama3.2`, the agent uses it to dynamically analyze user intent and parse inputs (email, OTP, password).
- **Rule-Engine Fallback**: If Ollama is offline or the model is not found, the agent transparently falls back to an internal regex state processor. This ensures that the chat functions perfectly even without local model downloads.
