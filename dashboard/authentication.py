"""SQLite-backed signup, admin approval, and login for the Streamlit dashboard.

For classroom/local demonstration. Use HTTPS, a managed identity provider,
rate limiting, backups, and hardened hosting before any public deployment.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
import sqlite3
from pathlib import Path
from typing import Optional

import streamlit as st

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "users.db"
ITERATIONS = 600_000


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_auth_db() -> None:
    with _connect() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            user_id TEXT NOT NULL UNIQUE COLLATE NOCASE,
            email TEXT NOT NULL UNIQUE COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user' CHECK(role IN ('admin','user')),
            status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','approved','rejected')),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            reviewed_at TEXT,
            reviewed_by TEXT
        )""")


def _hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    return f"{salt.hex()}:{digest.hex()}"


def _verify_password(password: str, encoded: str) -> bool:
    try:
        salt_hex, digest_hex = encoded.split(":", 1)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
    except (ValueError, TypeError):
        return False
    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    return hmac.compare_digest(actual, expected)


def create_admin_account(user_id: str, full_name: str, email: str, password: str) -> None:
    init_auth_db()
    with _connect() as conn:
        existing = conn.execute("SELECT id FROM users WHERE role='admin' LIMIT 1").fetchone()
        if existing:
            raise ValueError("An admin account already exists. Use the existing admin login.")
        conn.execute(
            "INSERT INTO users(full_name,user_id,email,password_hash,role,status,reviewed_at,reviewed_by) VALUES(?,?,?,?, 'admin','approved',CURRENT_TIMESTAMP,'system')",
            (full_name.strip(), user_id.strip(), email.strip(), _hash_password(password)),
        )


def bootstrap_admin_from_secrets() -> None:
    """Create or update the admin account using Streamlit Cloud secrets."""

    if "admin" not in st.secrets:
        return

    admin = st.secrets["admin"]

    required_fields = ["full_name", "user_id", "email", "password"]
    if any(not admin.get(field) for field in required_fields):
        raise ValueError("Admin secrets are incomplete.")

    with _connect() as conn:
        existing = conn.execute(
            "SELECT id FROM users WHERE role='admin' LIMIT 1"
        ).fetchone()

        if existing:
            conn.execute(
                """
                UPDATE users
                SET full_name=?, user_id=?, email=?, password_hash=?,
                    status='approved'
                WHERE id=?
                """,
                (
                    admin["full_name"].strip(),
                    admin["user_id"].strip(),
                    admin["email"].strip(),
                    _hash_password(admin["password"]),
                    existing["id"],
                ),
            )
            return

        conn.execute(
            """
            INSERT INTO users(
                full_name, user_id, email, password_hash,
                role, status, reviewed_at, reviewed_by
            )
            VALUES(?,?,?,?,'admin','approved',CURRENT_TIMESTAMP,'system')
            """,
            (
                admin["full_name"].strip(),
                admin["user_id"].strip(),
                admin["email"].strip(),
                _hash_password(admin["password"]),
            ),
        )



def register_user(full_name: str, user_id: str, email: str, password: str) -> tuple[bool, str]:
    init_auth_db()
    if not full_name.strip() or not user_id.strip() or not email.strip():
        return False, "Please complete all fields."
    if any(ch.isspace() for ch in user_id.strip()):
        return False, "User ID must not contain spaces."
    if len(password) < 10:
        return False, "Password must contain at least 10 characters."
    try:
        with _connect() as conn:
            conn.execute(
                "INSERT INTO users(full_name,user_id,email,password_hash) VALUES(?,?,?,?)",
                (full_name.strip(), user_id.strip(), email.strip(), _hash_password(password)),
            )
        return True, "Signup request submitted. Wait for admin approval before logging in."
    except sqlite3.IntegrityError:
        return False, "That User ID or email is already registered."


def authenticate(user_id: str, password: str) -> Optional[dict]:
    init_auth_db()
    with _connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE user_id=? COLLATE NOCASE", (user_id.strip(),)).fetchone()
    if not row or not _verify_password(password, row["password_hash"]):
        return None
    if row["status"] != "approved":
        return {"status": row["status"], "role": row["role"], "user_id": row["user_id"]}
    return {"status": "approved", "role": row["role"], "user_id": row["user_id"], "full_name": row["full_name"]}


def pending_users() -> list[dict]:
    init_auth_db()
    with _connect() as conn:
        rows = conn.execute("SELECT id,full_name,user_id,email,created_at FROM users WHERE role='user' AND status='pending' ORDER BY created_at").fetchall()
    return [dict(row) for row in rows]


def review_user(user_pk: int, decision: str, admin_user_id: str) -> None:
    if decision not in {"approved", "rejected"}:
        raise ValueError("Invalid review decision")
    with _connect() as conn:
        conn.execute(
            "UPDATE users SET status=?, reviewed_at=CURRENT_TIMESTAMP, reviewed_by=? WHERE id=? AND role='user' AND status='pending'",
            (decision, admin_user_id, user_pk),
        )


def require_login() -> dict:
    """Show login/signup UI and stop until a user with approved status signs in."""
    init_auth_db()
      bootstrap_admin_from_secrets()
    current = st.session_state.get("auth_user")
    if current and current.get("status") == "approved":
        return current

    st.title("Smart Manufacturing | Secure Access")
    st.caption("Create an account and wait for administrator approval, or sign in if approved.")
    login_tab, signup_tab = st.tabs(["Login", "Sign Up"])

    with login_tab:
        with st.form("login_form"):
            login_id = st.text_input("User ID", key="login_user_id")
            login_password = st.text_input("Password", type="password", key="login_password")
            login_submit = st.form_submit_button("Login", use_container_width=True)
        if login_submit:
            result = authenticate(login_id, login_password)
            if result is None:
                st.error("Invalid User ID or Password.")
            elif result["status"] == "pending":
                st.warning("Your signup request is pending admin approval. Please try again after approval.")
            elif result["status"] == "rejected":
                st.error("Your signup request was not approved. Contact the administrator.")
            else:
                st.session_state["auth_user"] = result
                st.rerun()

    with signup_tab:
        with st.form("signup_form"):
            full_name = st.text_input("Full Name", max_chars=100)
            new_user_id = st.text_input("Choose User ID", max_chars=64)
            email = st.text_input("Email Address", max_chars=254)
            new_password = st.text_input("Create Password (minimum 10 characters)", type="password", max_chars=256)
            confirm_password = st.text_input("Confirm Password", type="password", max_chars=256)
            signup_submit = st.form_submit_button("Submit for Admin Approval", use_container_width=True)
        if signup_submit:
            if new_password != confirm_password:
                st.error("Passwords do not match.")
            else:
                ok, message = register_user(full_name, new_user_id, email, new_password)
                (st.success if ok else st.error)(message)
    st.stop()


def render_admin_approval_panel(admin_user_id: str) -> None:
    st.subheader("Admin approval requests")
    requests = pending_users()
    if not requests:
        st.info("There are no pending signup requests.")
        return
    for request in requests:
        with st.container(border=True):
            st.write(f"**{request['full_name']}** — `{request['user_id']}`")
            st.caption(f"{request['email']} • Requested: {request['created_at']}")
            approve_col, reject_col = st.columns(2)
            with approve_col:
                if st.button("Approve", key=f"approve_{request['id']}", type="primary", use_container_width=True):
                    review_user(request["id"], "approved", admin_user_id)
                    st.success(f"{request['user_id']} approved.")
                    st.rerun()
            with reject_col:
                if st.button("Reject", key=f"reject_{request['id']}", use_container_width=True):
                    review_user(request["id"], "rejected", admin_user_id)
                    st.warning(f"{request['user_id']} rejected.")
                    st.rerun()
