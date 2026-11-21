
"""Automated tests for user authentication and admin approval."""

import pytest

from dashboard import authentication as auth


@pytest.fixture
def isolated_auth_db(tmp_path, monkeypatch):
    """Use a separate temporary database for every test."""
    test_db = tmp_path / "test_users.db"
    monkeypatch.setattr(auth, "DB_PATH", test_db)
    auth.init_auth_db()
    return test_db


def get_user_pk():
    """Get the database ID of the registered user."""
    with auth._connect() as conn:
        row = conn.execute(
            "SELECT id FROM users WHERE role='user' LIMIT 1"
        ).fetchone()
    return row["id"]


def test_signup_creates_pending_user(isolated_auth_db):
    """New registrations must remain pending until approval."""
    success, message = auth.register_user(
        "Test User",
        "testuser01",
        "test01@example.com",
        "StrongPass123",
    )

    assert success is True
    assert "approval" in message.lower()

    result = auth.authenticate("testuser01", "StrongPass123")
    assert result is not None
    assert result["status"] == "pending"


def test_approved_user_can_login(isolated_auth_db):
    """An approved user must be able to authenticate."""
    auth.register_user(
        "Approved User",
        "approved01",
        "approved01@example.com",
        "StrongPass123",
    )

    user_pk = get_user_pk()
    auth.review_user(user_pk, "approved", "admin01")

    result = auth.authenticate("approved01", "StrongPass123")

    assert result is not None
    assert result["status"] == "approved"
    assert result["role"] == "user"


def test_rejected_user_cannot_access_dashboard(isolated_auth_db):
    """A rejected user must not receive approved access."""
    auth.register_user(
        "Rejected User",
        "rejected01",
        "rejected01@example.com",
        "StrongPass123",
    )

    user_pk = get_user_pk()
    auth.review_user(user_pk, "rejected", "admin01")

    result = auth.authenticate("rejected01", "StrongPass123")

    assert result is not None
    assert result["status"] == "rejected"


def test_wrong_password_is_rejected(isolated_auth_db):
    """Incorrect passwords must not authenticate."""
    auth.register_user(
        "Password User",
        "password01",
        "password01@example.com",
        "StrongPass123",
    )

    result = auth.authenticate("password01", "WrongPassword123")

    assert result is None


def test_duplicate_user_id_is_rejected(isolated_auth_db):
    """Duplicate user IDs must not be registered."""
    auth.register_user(
        "First User",
        "duplicate01",
        "first@example.com",
        "StrongPass123",
    )

    success, message = auth.register_user(
        "Second User",
        "duplicate01",
        "second@example.com",
        "StrongPass123",
    )

    assert success is False
    assert "already registered" in message.lower()
