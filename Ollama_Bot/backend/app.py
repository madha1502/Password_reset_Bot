import os
import secrets
import hashlib
from flask import Flask, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv

# Load .env relative to the app.py file location
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path)
print(f"\n[DEBUG] Dotenv path: {dotenv_path}")
print(f"[DEBUG] Dotenv file exists? {os.path.exists(dotenv_path)}")
print(f"[DEBUG] SMTP Server loaded: {os.getenv('SMTP_SERVER')}")
print(f"[DEBUG] SMTP Username loaded: {os.getenv('SMTP_USERNAME')}\n")


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def create_app():
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates"),
        static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), "static"),
    )

    app.secret_key = os.getenv("SECRET_KEY", secrets.token_hex(32))
    app.config["SESSION_TYPE"] = "filesystem"
    app.config["SESSION_PERMANENT"] = False

    CORS(
        app,
        supports_credentials=True,
        origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:5000").split(","),
    )

    # Initialize DB
    from backend.database import init_db
    init_db()

    # Seed test users
    _seed_users()

    # Register blueprints
    from backend.routes import auth_bp, reset_bp, chat_bp, admin_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(reset_bp, url_prefix="/reset")
    app.register_blueprint(chat_bp, url_prefix="/chat")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # Page routes
    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/login")
    def login_page():
        return render_template("login.html")

    @app.route("/register")
    def register_page():
        return render_template("register.html")

    @app.route("/forgot-password")
    def forgot_password_page():
        return render_template("forgot_password.html")

    @app.route("/verify-otp")
    def verify_otp_page():
        return render_template("verify_otp.html")

    @app.route("/reset-password")
    def reset_password_page():
        return render_template("reset_password.html")

    @app.route("/admin/panel")
    def admin_page():
        return render_template("admin/dashboard.html")

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error"}), 500

    return app


def _seed_users():
    """Seed test users on first run."""
    from backend.database import SessionLocal
    from backend.models import User
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            test_users = [
                ("Admin User", "admin@ollama.com", "admin123", True),
                ("Alice Johnson", "alice@example.com", "alice123", False),
                ("Bob Smith", "bob@example.com", "bob123", False),
            ]
            for name, email, password, is_admin in test_users:
                db.add(User(
                    name=name, email=email,
                    password_hash=hash_password(password),
                    is_admin=is_admin
                ))
            db.commit()
            print("[DB] Test users seeded.")
    except Exception as e:
        print(f"[DB] Seed error: {e}")
        db.rollback()
    finally:
        db.close()
