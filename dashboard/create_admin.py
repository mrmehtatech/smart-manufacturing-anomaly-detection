"""Create the first administrator account for the dashboard."""
import getpass
from authentication import create_admin_account


def main() -> None:
    print("Create Smart Manufacturing administrator account")
    full_name = input("Admin full name: ").strip()
    user_id = input("Admin User ID: ").strip()
    email = input("Admin email: ").strip()
    password = getpass.getpass("Admin password (minimum 10 characters): ")
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        raise SystemExit("Passwords do not match.")
    if len(password) < 10:
        raise SystemExit("Password must contain at least 10 characters.")
    try:
        create_admin_account(user_id, full_name, email, password)
    except Exception as exc:
        raise SystemExit(str(exc)) from exc
    print("Admin account created. Keep these credentials private.")


if __name__ == "__main__":
    main()
