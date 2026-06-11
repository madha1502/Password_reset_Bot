# 🔐 Ollama Powered Password Recovery Assistant

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0.3-000000?style=for-the-badge&logo=flask&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-LLaMA3-FF6B35?style=for-the-badge&logo=ollama&logoColor=white)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![SendGrid](https://img.shields.io/badge/SendGrid-Email-1A82E2?style=for-the-badge&logo=sendgrid&logoColor=white)

---

## Overview

The **Ollama Powered Password Recovery Assistant** is a locally-hosted, privacy-first chatbot that guides users through a secure, multi-step password reset flow using a locally-running LLM (LLaMA 3 via Ollama). The system combines intelligent conversational AI with industry-standard security practices — including OTP verification, risk-based throttling, and SHA-256 password hashing — all without sending sensitive data to external AI APIs. An admin dashboard provides real-time oversight of all recovery sessions, user accounts, and system events.

---

## Features

- 🤖 **AI-Guided Recovery Chat** — Conversational password reset flow powered by a local LLaMA 3 model via Ollama
- 🔑 **OTP Email Verification** — Time-limited one-time passwords delivered via SendGrid
- 🛡️ **Risk Analysis Engine** — Dynamic risk scoring to detect and throttle suspicious reset attempts
- 👤 **User Authentication** — Secure login/registration with bcrypt-hashed passwords
- 🔒 **Password Strength Enforcement** — Real-time validation of new password complexity rules
- 📊 **Admin Dashboard** — Full visibility into users, sessions, OTP events, and risk flags
- 🗄️ **SQLite Database** — Zero-config persistent storage via SQLAlchemy ORM
- 🐳 **Docker Support** — One-command deployment with Docker Compose
- 🌐 **REST API Backend** — Clean Flask Blueprint-based API with CORS support
- 📱 **Responsive UI** — Bootstrap 5 frontend that works on desktop and mobile

---

## Tech Stack

| Category       | Technology         | Purpose                                      |
|----------------|--------------------|----------------------------------------------|
| Backend        | Python 3.11 / Flask| Web framework and REST API                   |
| AI / LLM       | Ollama + LLaMA 3   | Local language model for guided recovery chat|
| Database       | SQLite + SQLAlchemy| Persistent storage and ORM                   |
| Authentication | bcrypt             | Secure password hashing                      |
| Email          | SendGrid API       | OTP delivery to users                        |
| Frontend       | Bootstrap 5 / JS   | Responsive chat and admin UI                 |
| DevOps         | Docker + Compose   | Containerised deployment                     |
| Config         | python-dotenv      | Environment variable management              |
| WSGI Server    | Gunicorn           | Production-grade WSGI server                 |

---

## Project Structure

```
Ollama_Bot/
├── backend/
│   ├── __init__.py
│   ├── app.py                  # Flask application factory
│   ├── models.py               # SQLAlchemy ORM models
│   ├── config.py               # Configuration classes
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py             # Login / register / logout routes
│   │   ├── chat.py             # Ollama chat session routes
│   │   ├── password_reset.py   # OTP request & verification routes
│   │   └── admin.py            # Admin dashboard routes
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ollama_service.py   # Ollama API integration
│   │   ├── email_service.py    # SendGrid email service
│   │   └── risk_service.py     # Risk analysis engine
│   └── utils/
│       ├── __init__.py
│       └── helpers.py          # Shared utility functions
├── frontend/
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── chat.html
│   │   ├── reset_password.html
│   │   └── admin/
│   │       ├── dashboard.html
│   │       └── users.html
│   └── static/
│       ├── css/
│       │   └── style.css
│       └── js/
│           ├── chat.js
│           └── admin.js
├── .env                        # Environment variables (do NOT commit)
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── run.py                      # Application entry point
└── README.md
```

---

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.11+** — [https://www.python.org/downloads/](https://www.python.org/downloads/)
- **Ollama** — [https://ollama.com](https://ollama.com) (to run the local LLM)
- **Git** — for cloning the repository
- **A SendGrid account** — [https://sendgrid.com](https://sendgrid.com) (free tier is sufficient)
- **Docker & Docker Compose** *(optional, for containerised deployment)*

> **Note:** Node.js is **not** required — all frontend assets use CDN-hosted Bootstrap 5 and vanilla JavaScript.

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/madha1502/Password_reset_Bot.git
cd Password_reset_Bot/Ollama_Bot
```

### 2. Create and Activate a Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
# Copy the template
copy .env .env.local    # Windows
cp .env .env.local      # macOS / Linux
```

Open `.env` (or `.env.local`) and fill in your credentials:

```env
SECRET_KEY=your-very-random-secret-key-here
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxx
MAIL_FROM=noreply@yourdomain.com
```

### 5. Install Ollama

Download and install Ollama from [https://ollama.com](https://ollama.com), then start the service:

```bash
ollama serve   # starts the local Ollama daemon (if not already running)
```

### 6. Pull the LLaMA 3 Model

```bash
ollama pull llama3
```

> This downloads the model (~4.7 GB). Ensure you have sufficient disk space and a stable internet connection for the initial pull.

### 7. Run the Application

```bash
python run.py
```

The application will be available at **[http://localhost:5000](http://localhost:5000)**.

---

## Running with Docker

Ensure Docker Desktop is running, then:

```bash
docker-compose up --build
```

- The Flask app is served on **port 5000**.
- Ollama must be running on the **host machine** (not inside Docker). The compose file is pre-configured to reach it via `host.docker.internal:11434`.
- The SQLite database and session files are persisted via volume mounts.

To stop the services:

```bash
docker-compose down
```

---

## Environment Variables

| Variable           | Description                                          | Example                            |
|--------------------|------------------------------------------------------|------------------------------------|
| `SECRET_KEY`       | Flask session signing secret (change in production!) | `s3cr3t-r@nd0m-k3y`               |
| `FLASK_DEBUG`      | Enable Flask debug mode (`true` / `false`)           | `true`                             |
| `ALLOWED_ORIGINS`  | CORS allowed origins (comma-separated)               | `http://localhost:5000`            |
| `DATABASE_URL`     | SQLAlchemy database URI                              | `sqlite:///./ollama_bot.db`        |
| `SENDGRID_API_KEY` | SendGrid API key for email delivery                  | `SG.xxxxxxxxxxxxxxxxxxxxxxxx`      |
| `MAIL_FROM`        | Verified sender email address                        | `noreply@yourdomain.com`           |
| `OLLAMA_URL`       | Base URL of the running Ollama instance              | `http://localhost:11434`           |
| `OLLAMA_MODEL`     | Ollama model name to use for chat                    | `llama3`                           |

---

## API Endpoints

| Method | Endpoint                        | Auth Required | Description                                    |
|--------|---------------------------------|---------------|------------------------------------------------|
| GET    | `/`                             | No            | Landing page                                   |
| GET    | `/login`                        | No            | Login page                                     |
| POST   | `/auth/login`                   | No            | Authenticate user and create session           |
| GET    | `/register`                     | No            | Registration page                              |
| POST   | `/auth/register`                | No            | Create new user account                        |
| POST   | `/auth/logout`                  | Yes           | Destroy session and log out                    |
| GET    | `/chat`                         | Yes           | AI chat interface                              |
| POST   | `/chat/message`                 | Yes           | Send a message and receive AI response         |
| GET    | `/reset-password`               | No            | Password reset landing page                    |
| POST   | `/reset/request-otp`            | No            | Request OTP for a given email address          |
| POST   | `/reset/verify-otp`             | No            | Verify submitted OTP token                     |
| POST   | `/reset/set-password`           | No            | Set new password after OTP verification        |
| GET    | `/admin/dashboard`              | Admin Only    | Admin overview dashboard                       |
| GET    | `/admin/users`                  | Admin Only    | List all registered users                      |
| GET    | `/admin/sessions`               | Admin Only    | View active and historical chat sessions       |
| GET    | `/admin/risk-log`               | Admin Only    | View risk engine event log                     |
| DELETE | `/admin/users/<id>`             | Admin Only    | Delete a user account                          |

---

## Default Test Users

The following demo accounts are seeded on first run for development and testing:

| Name          | Email                    | Password      | Role  |
|---------------|--------------------------|---------------|-------|
| Alice Admin   | alice@example.com        | Admin@1234    | Admin |
| Bob User      | bob@example.com          | User@5678     | User  |
| Carol User    | carol@example.com        | User@9012     | User  |

> ⚠️ **Important:** Change or remove these default credentials before deploying to any public or production environment.

---

## Security Features

- 🔐 **SHA-256 / bcrypt Password Hashing** — Passwords are never stored in plain text; bcrypt is used with a per-user salt
- ⏱️ **OTP Expiry** — One-time passwords expire after a configurable time window (default: 10 minutes)
- 🚦 **Rate Limiting via Risk Engine** — The risk analysis service assigns a score to each reset attempt based on velocity, IP, and behaviour patterns; high-risk requests are throttled or blocked
- 🍪 **Secure Session Management** — Flask sessions are signed with `SECRET_KEY` and can be configured for `HttpOnly` and `Secure` cookie flags in production
- 🔎 **Input Validation** — All user-submitted data is validated and sanitised server-side before processing or persistence
- 🌐 **CORS Protection** — Cross-Origin Resource Sharing is restricted to `ALLOWED_ORIGINS` defined in the environment
- 🤖 **Local LLM Privacy** — All AI inference runs on-device via Ollama; no user data is sent to external AI APIs

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-new-feature`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature/my-new-feature`
5. Open a Pull Request

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2026 madha1502

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
