"""Admin dashboard page — user management, stats, RBAC."""
from __future__ import annotations
import sys
import os
import html as html_mod
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import importlib
import importlib.util
import services.auth_service as _auth_mod
importlib.reload(_auth_mod)

import streamlit as st
from services.auth_service import (
    list_users, admin_create_user, update_user, update_password, delete_user, get_stats
)

ALL_PRIVILEGES = [
    "Tableaux de bord", "Requêtes SQL", "Export données",
    "Rapports BI", "Gestion sessions", "Accès complet",
]

ADMIN_CSS = """
<style>
/* ── Admin shell ─────────────────────────────────────── */
[data-testid="stSidebar"] { background: #0f172a !important; }

/* ── Override global pill/999px radius → sharp inputs ── */
.stTextInput > div,
.stTextInput > div > div,
.stTextInput > div > div > input,
.stSelectbox > div > div,
.stMultiSelect > div > div,
.stMultiSelect > div > div > div,
.stTextArea > div,
.stTextArea > div > textarea,
[data-baseweb="input"],
[data-baseweb="select"] > div,
[data-baseweb="textarea"] {
    border-radius: 6px !important;
}
/* Tags inside multiselect */
[data-baseweb="tag"] { border-radius: 4px !important; }
/* Buttons in admin keep moderate rounding */
.stButton > button { border-radius: 6px !important; }
.stFormSubmitButton > button { border-radius: 6px !important; }

.adm-stat-grid { display:flex; gap:1rem; margin-bottom:1.5rem; flex-wrap:wrap; }
.adm-stat-card {
    flex:1; min-width:160px;
    background:#ffffff; border-radius:12px;
    padding:1.25rem 1.5rem;
    box-shadow:0 2px 12px rgba(15,23,42,.08);
    border-top:4px solid #2563eb;
}
.adm-stat-val { font-size:2rem; font-weight:800; color:#1e293b; line-height:1; }
.adm-stat-lbl { font-size:0.78rem; color:#64748b; margin-top:.3rem; font-weight:500; text-transform:uppercase; letter-spacing:.06em; }

/* table */
.adm-table { width:100%; border-collapse:collapse; background:#fff;
    border-radius:12px; overflow:hidden;
    box-shadow:0 2px 12px rgba(15,23,42,.08); }
.adm-table th { background:#f8fafc; color:#475569; font-size:.75rem;
    font-weight:700; text-transform:uppercase; letter-spacing:.07em;
    padding:.75rem 1rem; text-align:left; border-bottom:1px solid #e2e8f0; }
.adm-table td { padding:.75rem 1rem; border-bottom:1px solid #f1f5f9;
    color:#1e293b; font-size:.88rem; vertical-align:middle; }
.adm-table tr:last-child td { border-bottom:none; }
.adm-table tr:hover td { background:#f8fafc; }

/* badges */
.badge { display:inline-block; padding:.2rem .6rem; border-radius:999px;
    font-size:.7rem; font-weight:700; text-transform:uppercase; letter-spacing:.06em; }
.badge-admin { background:#dbeafe; color:#1d4ed8; }
.badge-user  { background:#dcfce7; color:#15803d; }

/* section header */
.adm-section-hdr {
    display:flex; justify-content:space-between; align-items:center;
    margin:1.5rem 0 .75rem;
}
.adm-section-title { font-size:1.15rem; font-weight:700; color:#1e293b; }

/* modal */
.adm-modal-bg {
    position:fixed; inset:0; background:rgba(15,23,42,.45);
    display:flex; align-items:center; justify-content:center;
    z-index:9999;
}
.adm-modal {
    background:#fff; border-radius:16px; padding:2rem 2.25rem;
    max-width:520px; width:100%;
    box-shadow:0 24px 64px rgba(15,23,42,.2);
}
.adm-modal-title { font-size:1.25rem; font-weight:800; color:#1e293b; margin-bottom:1.25rem; }
</style>
"""


def _sidebar(active: str) -> str:
    menu_items = [
        ("dashboard", "📊", "Dashboard"),
        ("users", "👥", "Utilisateurs"),
        ("privileges", "🔑", "Privilèges"),
        ("settings", "⚙️", "Paramètres"),
    ]
    st.sidebar.markdown(
        """
        <div style="padding:1.5rem 1rem .5rem;">
            <div style="color:#fff;font-size:1.1rem;font-weight:800;letter-spacing:-.02em;">
                🤖 AI BI Chatbot
            </div>
            <div style="color:#475569;font-size:.75rem;margin-top:.2rem;">Panneau d'administration</div>
        </div>
        <hr style="border-color:#1e293b;margin:.5rem 0 1rem;">
        """,
        unsafe_allow_html=True,
    )
    for key, icon, label in menu_items:
        is_active = key == active
        bg = "#1e40af" if is_active else "transparent"
        col = "#ffffff" if is_active else "#94a3b8"
        st.sidebar.markdown(
            f"""<div style="background:{bg};padding:.6rem 1rem;border-radius:8px;
                margin:.15rem .5rem;cursor:pointer;display:flex;align-items:center;gap:.6rem;">
                <span style="font-size:1rem;">{icon}</span>
                <span style="color:{col};font-size:.88rem;font-weight:{'700' if is_active else '500'};">{label}</span>
            </div>""",
            unsafe_allow_html=True,
        )
        if st.sidebar.button(label, key=f"nav_{key}", use_container_width=True):
            st.session_state.admin_page = key
            st.rerun()
    st.sidebar.markdown("<hr style='border-color:#1e293b;margin:1rem .5rem;'>", unsafe_allow_html=True)
    if st.sidebar.button("🚪 Déconnexion", key="admin_logout", use_container_width=True):
        from services.auth_service import revoke_session_token as _revoke
        _revoke(st.session_state.get("auth_token", ""))
        for _k in ["authenticated","auth_user","auth_token","session_id","messages"]:
            st.session_state[_k] = False if _k == "authenticated" else None if _k != "messages" else []
        st.query_params.clear()
        st.rerun()


def _stat_cards(stats: dict) -> None:
    cards = [
        (stats["total_users"], "Total utilisateurs", "👤"),
        (stats["active_sessions"], "Sessions actives", "🟢"),
        (stats["bi_queries"], "Requêtes BI traitées", "🔍"),
        (stats["admins"], "Administrateurs", "🛡️"),
    ]
    cols = st.columns(4)
    for col, (val, lbl, icon) in zip(cols, cards):
        col.markdown(
            f"""<div class="adm-stat-card">
                <div class="adm-stat-val">{icon} {val}</div>
                <div class="adm-stat-lbl">{lbl}</div>
            </div>""",
            unsafe_allow_html=True,
        )


def _users_table(users: list[dict]) -> None:
    st.markdown(
        """<div class="adm-section-hdr">
            <span class="adm-section-title">👥 Gestion des utilisateurs</span>
        </div>""",
        unsafe_allow_html=True,
    )

    if st.button("＋ Nouvel utilisateur", key="btn_new_user", type="primary"):
        st.session_state.show_new_user_modal = True
        st.session_state.edit_user_id = None

    # Header row
    h0, h1, h2, h3, h4 = st.columns([3, 1.2, 2, 1.5, 2])
    h0.markdown("<div style='font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:#64748b;padding:.5rem 0 .25rem;'>Utilisateur</div>", unsafe_allow_html=True)
    h1.markdown("<div style='font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:#64748b;padding:.5rem 0 .25rem;'>Rôle</div>", unsafe_allow_html=True)
    h2.markdown("<div style='font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:#64748b;padding:.5rem 0 .25rem;'>Privilèges</div>", unsafe_allow_html=True)
    h3.markdown("<div style='font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:#64748b;padding:.5rem 0 .25rem;'>Créé le</div>", unsafe_allow_html=True)
    h4.markdown("<div style='font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:#64748b;padding:.5rem 0 .25rem;'>Actions</div>", unsafe_allow_html=True)
    st.markdown("<hr style='margin:.1rem 0 .5rem;border-color:#e2e8f0;'>", unsafe_allow_html=True)

    for u in users:
        uid = u.get("id", "")
        role = u.get("role", "user")
        badge_cls = "badge-admin" if role == "admin" else "badge-user"
        badge_lbl = "Admin" if role == "admin" else "User"
        created = u.get("created_at", "")[:10]
        name = html_mod.escape(u.get("full_name", ""))
        email = html_mod.escape(u.get("email", ""))
        privs_raw = u.get("privileges", [])
        privs = ", ".join(p for p in privs_raw if p != "all") or "—"

        c0, c1, c2, c3, c4 = st.columns([3, 1.2, 2, 1.5, 2])
        c0.markdown(
            f"<div style='padding:.4rem 0'><strong style='color:#1e293b'>{name}</strong>"
            f"<br><span style='color:#64748b;font-size:.78rem;'>{email}</span></div>",
            unsafe_allow_html=True,
        )
        c1.markdown(
            f"<div style='padding:.6rem 0'><span class='badge {badge_cls}'>{badge_lbl}</span></div>",
            unsafe_allow_html=True,
        )
        c2.markdown(
            f"<div style='padding:.6rem 0;font-size:.82rem;color:#64748b;'>{privs}</div>",
            unsafe_allow_html=True,
        )
        c3.markdown(
            f"<div style='padding:.6rem 0;font-size:.82rem;color:#64748b;'>{created}</div>",
            unsafe_allow_html=True,
        )
        with c4:
            btn_c1, btn_c2 = st.columns(2)
            with btn_c1:
                if st.button("✏️", key=f"edit_{uid}", help="Éditer", use_container_width=True):
                    st.session_state.edit_user_id = uid
                    st.session_state.show_new_user_modal = True
                    st.rerun()
            with btn_c2:
                if st.button("🗑️", key=f"del_{uid}", help="Supprimer", use_container_width=True):
                    ok, msg = delete_user(uid)
                    st.toast(msg, icon="✅" if ok else "❌")
                    st.rerun()
        st.markdown("<hr style='margin:.1rem 0;border-color:#f1f5f9;'>", unsafe_allow_html=True)


def _new_user_modal(edit_id: str | None = None) -> None:
    users = list_users()
    edit_user = next((u for u in users if u.get("id") == edit_id), None) if edit_id else None
    title = "✏️ Modifier l'utilisateur" if edit_user else "➕ Nouvel utilisateur"

    st.markdown(f"### {title}")

    # ── Info + role + privileges form ──────────────────────────
    with st.form("user_form"):
        col_l, col_r = st.columns(2)
        with col_l:
            full_name = st.text_input("Nom complet", value=edit_user.get("full_name", "") if edit_user else "")
            email = st.text_input("Email", value=edit_user.get("email", "") if edit_user else "",
                                  disabled=bool(edit_user))
        with col_r:
            username = st.text_input("Nom d'utilisateur",
                                     value=edit_user.get("username", "") if edit_user else "",
                                     disabled=bool(edit_user))
            role = st.selectbox(
                "Rôle",
                ["user", "admin"],
                index=0 if not edit_user else (0 if edit_user.get("role") == "user" else 1),
            )
        if not edit_user:
            password = st.text_input("Mot de passe", type="password", placeholder="Mot de passe initial")
        _default_privs = [p for p in (edit_user.get("privileges", []) if edit_user else []) if p in ALL_PRIVILEGES]
        selected_privs = st.multiselect(
            "Privilèges d'accès",
            ALL_PRIVILEGES,
            default=_default_privs,
            help="Les utilisateurs avec rôle 'user' accèdent uniquement au chatbot.",
        )
        c1, c2 = st.columns(2)
        submitted = c1.form_submit_button("💾 Enregistrer", use_container_width=True, type="primary")
        cancelled = c2.form_submit_button("❌ Annuler", use_container_width=True)

    if submitted:
        if edit_user:
            ok, msg = update_user(edit_id, role=role, privileges=selected_privs, full_name=full_name)
        else:
            ok, msg, _ = admin_create_user(full_name, email, username, password, role, selected_privs)
        st.toast(msg, icon="✅" if ok else "❌")
        if ok:
            st.session_state.show_new_user_modal = False
            st.session_state.edit_user_id = None
            st.rerun()

    if cancelled:
        st.session_state.show_new_user_modal = False
        st.session_state.edit_user_id = None
        st.rerun()

    # ── Password change section (edit only) ────────────────────
    if edit_user:
        st.markdown("---")
        st.markdown("#### 🔒 Changer le mot de passe")
        with st.form("pwd_form"):
            new_pwd = st.text_input("Nouveau mot de passe", type="password", placeholder="Nouveau mot de passe")
            confirm_pwd = st.text_input("Confirmer", type="password", placeholder="Confirmer le mot de passe")
            pwd_submitted = st.form_submit_button("🔒 Mettre à jour le mot de passe", type="primary", use_container_width=True)
        if pwd_submitted:
            if new_pwd != confirm_pwd:
                st.error("Les mots de passe ne correspondent pas.")
            else:
                ok, msg = update_password(edit_id, new_pwd)
                st.toast(msg, icon="✅" if ok else "❌")


def _privileges_page(users: list[dict]) -> None:
    st.markdown("### 🔑 Gestion des privilèges")
    for u in users:
        with st.expander(f"{u['full_name']} — {u['email']}"):
            current = u.get("privileges", [])
            valid_current = [p for p in current if p in ALL_PRIVILEGES]
            new_privs = st.multiselect(
                "Privilèges", ALL_PRIVILEGES, default=valid_current, key=f"priv_{u['id']}"
            )
            if st.button("Mettre à jour", key=f"upd_{u['id']}", type="primary"):
                ok, msg = update_user(u["id"], privileges=new_privs)
                st.toast(msg, icon="✅" if ok else "❌")
                st.rerun()


def _settings_page(auth_user: dict) -> None:
    st.markdown("### ⚙️ Paramètres")
    st.info(f"Connecté en tant que **{auth_user.get('full_name')}** (`{auth_user.get('role')}`)")
    st.markdown("---")
    st.markdown("**Identifiants par défaut (première installation) :**")
    st.code("login: admin\nmot de passe: admin123")
    st.warning("⚠️ Changez ce mot de passe en production via la gestion des utilisateurs.")


def render_admin(auth_user: dict) -> None:
    st.markdown(ADMIN_CSS, unsafe_allow_html=True)

    if "admin_page" not in st.session_state:
        st.session_state.admin_page = "dashboard"
    if "show_new_user_modal" not in st.session_state:
        st.session_state.show_new_user_modal = False
    if "edit_user_id" not in st.session_state:
        st.session_state.edit_user_id = None

    page = st.session_state.admin_page

    # Rebuild sidebar nav (labels only for clickability)
    st.sidebar.markdown(
        """<div style="padding:1.5rem 1rem .5rem;">
            <div style="color:#fff;font-size:1.1rem;font-weight:800;">🤖 AI BI Chatbot</div>
            <div style="color:#475569;font-size:.75rem;margin-top:.2rem;">Panneau d'administration</div>
        </div><hr style="border-color:#1e293b;margin:.5rem 0 .75rem;">""",
        unsafe_allow_html=True,
    )

    nav_items = [
        ("dashboard", "📊 Dashboard"),
        ("users", "👥 Utilisateurs"),
        ("privileges", "🔑 Privilèges"),
        ("settings", "⚙️ Paramètres"),
    ]
    for key, label in nav_items:
        is_active = key == page
        btn_style = "primary" if is_active else "secondary"
        if st.sidebar.button(label, key=f"nav_{key}", use_container_width=True, type=btn_style):
            st.session_state.admin_page = key
            st.rerun()

    st.sidebar.markdown("<hr style='border-color:#1e293b;margin:.75rem 0;'>", unsafe_allow_html=True)
    if st.sidebar.button("🚪 Déconnexion", key="admin_logout_btn", use_container_width=True):
        from services.auth_service import revoke_session_token as _revoke
        _revoke(st.session_state.get("auth_token", ""))
        for _k in ["authenticated","auth_user","auth_token","session_id","messages"]:
            st.session_state[_k] = False if _k == "authenticated" else None if _k != "messages" else []
        st.query_params.clear()
        st.rerun()

    # ── Main content ──
    display_name = html_mod.escape(auth_user.get("full_name") or auth_user.get("username") or "Admin")
    st.markdown(
        f"""<div style="display:flex;justify-content:space-between;align-items:center;
            margin-bottom:1.5rem;padding-bottom:1rem;border-bottom:1px solid #e2e8f0;">
            <div>
                <div style="font-size:1.5rem;font-weight:800;color:#1e293b;">
                    {"📊 Dashboard" if page=="dashboard"
                     else "👥 Utilisateurs" if page=="users"
                     else "🔑 Privilèges" if page=="privileges"
                     else "⚙️ Paramètres"}
                </div>
                <div style="color:#64748b;font-size:.85rem;">Administration · AI BI Chatbot</div>
            </div>
            <div style="background:#f1f5f9;padding:.5rem 1rem;border-radius:8px;
                color:#1e293b;font-size:.85rem;font-weight:600;">
                👤 {display_name}
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

    stats = get_stats()
    users = list_users()

    if page == "dashboard":
        _stat_cards(stats)
        st.markdown("---")
        st.markdown("#### Aperçu des utilisateurs récents")
        import pandas as pd
        df = pd.DataFrame([{
            "Nom": u["full_name"],
            "Email": u["email"],
            "Rôle": u["role"],
            "Créé le": u["created_at"][:10],
        } for u in users[:5]])
        st.dataframe(df, use_container_width=True, hide_index=True)

    elif page == "users":
        if st.session_state.show_new_user_modal:
            _new_user_modal(st.session_state.edit_user_id)
        else:
            _users_table(users)

    elif page == "privileges":
        _privileges_page(users)

    elif page == "settings":
        _settings_page(auth_user)
