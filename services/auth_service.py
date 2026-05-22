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
SESSIONS_TOKENS_FILE = PROJECT_ROOT / "data" / "auth_tokens.json"


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


VALID_ROLES = {"admin", "user"}


def _public_user(user_record: dict) -> dict:
    return {
        "id": user_record.get("id"),
        "full_name": user_record.get("full_name", ""),
        "username": user_record.get("username", ""),
        "email": user_record.get("email", ""),
        "role": user_record.get("role", "user"),
        "created_at": user_record.get("created_at", ""),
        "privileges": user_record.get("privileges", []),
    }


def _seed_default_admin() -> None:
    users = _load_users()
    if not users:
        salt = secrets.token_hex(16)
        now = datetime.utcnow().isoformat()
        admin = {
            "id": str(uuid.uuid4()),
            "full_name": "Administrateur",
            "email": "admin@biapp.local",
            "username": "admin",
            "role": "admin",
            "password_salt": salt,
            "password_hash": _hash_password("admin123", salt),
            "privileges": ["all"],
            "created_at": now,
            "updated_at": now,
        }
        _save_users([admin])


def list_users() -> list[dict]:
    _seed_default_admin()
    return [_public_user(u) for u in _load_users()]


def admin_create_user(
    full_name: str,
    email: str,
    username: str,
    password: str,
    role: str = "user",
    privileges: list[str] | None = None,
) -> tuple[bool, str, dict | None]:
    full_name = (full_name or "").strip()
    email = (email or "").strip()
    username = (username or "").strip()
    password = password or ""
    role = role if role in VALID_ROLES else "user"

    if not full_name or not email or not username or not password:
        return False, "Tous les champs sont obligatoires.", None

    users = _load_users()
    for u in users:
        if _normalize(u.get("email", "")) == _normalize(email):
            return False, "Email déjà utilisé.", None
        if _normalize(u.get("username", "")) == _normalize(username):
            return False, "Nom d'utilisateur déjà pris.", None

    salt = secrets.token_hex(16)
    now = datetime.utcnow().isoformat()
    record = {
        "id": str(uuid.uuid4()),
        "full_name": full_name,
        "email": email,
        "username": username,
        "role": role,
        "password_salt": salt,
        "password_hash": _hash_password(password, salt),
        "privileges": privileges or [],
        "created_at": now,
        "updated_at": now,
    }
    users.append(record)
    _save_users(users)
    return True, "Utilisateur créé.", _public_user(record)


def update_user(
    user_id: str,
    role: str | None = None,
    privileges: list[str] | None = None,
    full_name: str | None = None,
    email: str | None = None,
    username: str | None = None,
) -> tuple[bool, str]:
    users = _load_users()
    for u in users:
        if u.get("id") == user_id:
            if role is not None and role in VALID_ROLES:
                u["role"] = role
            if privileges is not None:
                u["privileges"] = privileges
            if full_name is not None:
                u["full_name"] = full_name.strip()
            if email is not None and email.strip():
                u["email"] = email.strip()
            if username is not None and username.strip():
                u["username"] = username.strip()
            u["updated_at"] = datetime.utcnow().isoformat()
            _save_users(users)
            return True, "Utilisateur mis à jour."
    return False, "Utilisateur introuvable."


def update_password(user_id: str, new_password: str) -> tuple[bool, str]:
    if not new_password or len(new_password) < 4:
        return False, "Mot de passe trop court (min. 4 caractères)."
    users = _load_users()
    for u in users:
        if u.get("id") == user_id:
            salt = secrets.token_hex(16)
            u["password_salt"] = salt
            u["password_hash"] = _hash_password(new_password, salt)
            u["updated_at"] = datetime.utcnow().isoformat()
            _save_users(users)
            return True, "Mot de passe mis à jour."
    return False, "Utilisateur introuvable."


def delete_user(user_id: str) -> tuple[bool, str]:
    users = _load_users()
    filtered = [u for u in users if u.get("id") != user_id]
    if len(filtered) == len(users):
        return False, "Utilisateur introuvable."
    _save_users(filtered)
    return True, "Utilisateur supprimé."


def get_stats() -> dict:
    users = _load_users()
    tokens = _load_tokens()
    active_sessions = len(tokens)
    try:
        from services.session_store import list_sessions
        bi_queries = sum(
            len(s.get("messages", [])) // 2
            for s in [__import__('json').loads(open(f, encoding='utf-8').read())
                      for f in (Path(__file__).resolve().parents[1] / "data" / "sessions").glob("*.json")
                      if f.exists()]
        )
    except Exception:
        bi_queries = 0
    return {
        "total_users": len(users),
        "active_sessions": active_sessions,
        "bi_queries": bi_queries,
        "admins": sum(1 for u in users if u.get("role") == "admin"),
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


def _load_tokens() -> dict:
    if not SESSIONS_TOKENS_FILE.exists():
        return {}
    try:
        with open(SESSIONS_TOKENS_FILE, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_tokens(tokens: dict) -> None:
    SESSIONS_TOKENS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SESSIONS_TOKENS_FILE, "w", encoding="utf-8") as fh:
        json.dump(tokens, fh, indent=2, ensure_ascii=False)


def create_session_token(user: dict) -> str:
    token = secrets.token_urlsafe(32)
    tokens = _load_tokens()
    tokens[token] = {
        "user_id": user.get("id"),
        "username": user.get("username"),
        "full_name": user.get("full_name"),
        "email": user.get("email"),
        "role": user.get("role", "user"),
        "privileges": user.get("privileges", []),
        "created_at": datetime.utcnow().isoformat(),
    }
    _save_tokens(tokens)
    return token


def validate_session_token(token: str) -> dict | None:
    if not token:
        return None
    tokens = _load_tokens()
    entry = tokens.get(token)
    if not entry:
        return None
    return {
        "id": entry.get("user_id"),
        "username": entry.get("username"),
        "full_name": entry.get("full_name"),
        "email": entry.get("email"),
        "role": entry.get("role", "user"),
        "privileges": entry.get("privileges", []),
    }


def revoke_session_token(token: str) -> None:
    tokens = _load_tokens()
    tokens.pop(token, None)
    _save_tokens(tokens)


def authenticate_user(identifier: str, password: str) -> tuple[bool, str, dict | None]:
    identifier = (identifier or "").strip()
    password = password or ""

    if not identifier or not password:
        return False, "Veuillez renseigner votre identifiant et votre mot de passe.", None

    _seed_default_admin()
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