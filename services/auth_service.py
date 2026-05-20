"""Local authentication helpers for the Streamlit frontend.

This keeps the chat flow unchanged while providing a lightweight
register/login store backed by a JSON file in data/users.json.
"""

from __future__ import annotations

import hashlib
import json
import secrets
import uuid
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
USERS_FILE = PROJECT_ROOT / "data" / "users.json"


def _ensure_store() -> None:
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not USERS_FILE.exists():
        with open(USERS_FILE, "w", encoding="utf-8") as file_handle:
            json.dump({"users": []}, file_handle, indent=2, ensure_ascii=False)


def _load_users() -> list[dict]:
    _ensure_store()
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as file_handle:
            data = json.load(file_handle)
        users = data.get("users", []) if isinstance(data, dict) else []
        return users if isinstance(users, list) else []
    except Exception:
        return []


def _save_users(users: list[dict]) -> None:
    _ensure_store()
    with open(USERS_FILE, "w", encoding="utf-8") as file_handle:
        json.dump({"users": users}, file_handle, indent=2, ensure_ascii=False)


def _normalize(value: str) -> str:
    return (value or "").strip().lower()


def _hash_password(password: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}{password}".encode("utf-8")).hexdigest()


def _public_user(user_record: dict) -> dict:
    return {
        "id": user_record.get("id"),
        "full_name": user_record.get("full_name", ""),
        "username": user_record.get("username", ""),
        "email": user_record.get("email", ""),
    }


def register_user(full_name: str, email: str, username: str, password: str) -> tuple[bool, str, dict | None]:
    full_name = (full_name or "").strip()
    email = (email or "").strip()
    username = (username or "").strip()
    password = password or ""

    if not full_name or not email or not username or not password:
        return False, "Tous les champs sont obligatoires.", None

    users = _load_users()
    normalized_email = _normalize(email)
    normalized_username = _normalize(username)

    for existing_user in users:
        if _normalize(existing_user.get("email", "")) == normalized_email:
            return False, "Un compte existe déjà avec cet email.", None
        if _normalize(existing_user.get("username", "")) == normalized_username:
            return False, "Ce nom d'utilisateur est déjà utilisé.", None

    salt = secrets.token_hex(16)
    now = datetime.utcnow().isoformat()
    user_record = {
        "id": str(uuid.uuid4()),
        "full_name": full_name,
        "email": email,
        "username": username,
        "password_salt": salt,
        "password_hash": _hash_password(password, salt),
        "created_at": now,
        "updated_at": now,
    }

    users.append(user_record)
    _save_users(users)
    return True, "Compte créé avec succès.", _public_user(user_record)


def authenticate_user(identifier: str, password: str) -> tuple[bool, str, dict | None]:
    identifier = (identifier or "").strip()
    password = password or ""

    if not identifier or not password:
        return False, "Veuillez renseigner votre identifiant et votre mot de passe.", None

    users = _load_users()
    normalized_identifier = _normalize(identifier)

    for user_record in users:
        if normalized_identifier not in {
            _normalize(user_record.get("username", "")),
            _normalize(user_record.get("email", "")),
        }:
            continue

        expected_hash = user_record.get("password_hash", "")
        salt = user_record.get("password_salt", "")
        if expected_hash and salt and secrets.compare_digest(_hash_password(password, salt), expected_hash):
            return True, "Connexion réussie.", _public_user(user_record)

        return False, "Mot de passe incorrect.", None

    return False, "Aucun compte trouvé avec cet identifiant.", None