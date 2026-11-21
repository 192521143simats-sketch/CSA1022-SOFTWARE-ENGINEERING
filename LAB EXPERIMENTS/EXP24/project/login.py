USERS = {"admin": "admin123", "sarvesh": "pass@123"}


def login(username, password):
    """Return True when the username/password pair is valid."""
    return USERS.get(username) == password


if __name__ == "__main__":
    print("admin/admin123  ->", login("admin", "admin123"))
    print("admin/wrong     ->", login("admin", "wrong"))
