import sys
import os
import json
import html
from pathlib import Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import streamlit as st
import requests
from datetime import datetime
from config.settings import settings
from services.auth_service import authenticate_user, register_user, create_session_token, validate_session_token, revoke_session_token
import importlib.util as _ilu, pathlib as _pl
_admin_spec = _ilu.spec_from_file_location("admin", _pl.Path(__file__).parent / "pages" / "admin.py")
_admin_mod = _ilu.module_from_spec(_admin_spec)
_admin_spec.loader.exec_module(_admin_mod)
render_admin = _admin_mod.render_admin
from services.session_store import delete_session as delete_session_record
import re

st.set_page_config(
    page_title="AI BI Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - Professional Design
def inject_custom_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

        :root {
            --bg: #f0f4f8;
            --surface: #ffffff;
            --surface-solid: #ffffff;
            --text: #1e293b;
            --text-muted: #64748b;
            --line: rgba(148, 163, 184, 0.2);
            --accent: #2563eb;
            --accent-strong: #1d4ed8;
            --accent-hover: #1e40af;
            --sidebar-bg: #0f172a;
            --sidebar-surface: #1e293b;
            --sidebar-text: #f1f5f9;
            --sidebar-muted: #94a3b8;
            --sidebar-accent: #3b82f6;
            --sidebar-hover: rgba(255,255,255,0.06);
            --shadow: 0 4px 24px rgba(15, 23, 42, 0.08);
            --shadow-soft: 0 2px 8px rgba(15, 23, 42, 0.05);
            --shadow-md: 0 8px 32px rgba(15, 23, 42, 0.10);
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        html, body, [data-testid="stAppViewContainer"] {
            background: var(--bg);
            color: var(--text);
            font-family: 'Inter', 'Plus Jakarta Sans', sans-serif;
        }

        [data-testid="stHeader"] {
            background: var(--bg);
            border-bottom: 1px solid rgba(148, 163, 184, 0.15);
        }

        [data-testid="stMainBlockContainer"] {
            padding: 4rem 2.5rem 10rem 2.5rem !important;
        }

        .main-content {
            padding: 0;
            max-width: 1200px;
            margin: 0 auto;
        }

        /* ── TOP BANNER ── */
        .top-nav {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            margin-bottom: 1.5rem;
            padding: 0.7rem 1.2rem;
            border-radius: 10px;
            background: #ffffff;
            border: 1px solid rgba(148, 163, 184, 0.18);
            box-shadow: var(--shadow-soft);
        }

        .top-nav-label {
            font-size: 0.72rem;
            font-weight: 700;
            color: var(--accent);
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }

        .top-nav-copy {
            font-size: 0.82rem;
            color: var(--text-muted);
            font-weight: 400;
            margin-top: 0.1rem;
        }

        .top-nav-status {
            display: flex;
            align-items: center;
            gap: 0.45rem;
            font-size: 0.82rem;
            font-weight: 600;
            color: #16a34a;
        }

        .top-nav-dot {
            width: 8px; height: 8px;
            border-radius: 50%;
            background: #22c55e;
            box-shadow: 0 0 0 3px rgba(34,197,94,0.18);
            display: inline-block;
        }

        /* ── MAIN HEADER ── */
        .header-section {
            background: transparent;
            padding: 0 0 1.25rem 0;
            margin-bottom: 0.5rem;
        }

        .header-title {
            font-size: 2.2rem;
            font-weight: 800;
            letter-spacing: -0.04em;
            color: var(--text);
            margin-bottom: 0.3rem;
            line-height: 1.1;
        }

        .header-subtitle {
            font-size: 0.97rem;
            color: var(--text-muted);
            font-weight: 400;
        }

        /* ── HERO CARD ── */
        .hero-card {
            background: #ffffff;
            border: 1px solid rgba(148, 163, 184, 0.18);
            border-radius: 16px;
            box-shadow: var(--shadow-md);
            padding: 3rem 2rem 2.5rem 2rem;
            margin-bottom: 1.75rem;
            text-align: center;
        }

        .hero-illustration {
            font-size: 2.5rem;
            margin-bottom: 1rem;
            display: block;
        }

        .hero-title {
            font-size: 1.35rem;
            font-weight: 700;
            color: var(--text);
            margin-bottom: 1rem;
        }

        .hero-example {
            display: inline-flex;
            align-items: center;
            gap: 0.6rem;
            background: #f8fafc;
            border: 1px solid rgba(37, 99, 235, 0.18);
            border-radius: 10px;
            padding: 0.7rem 1.2rem;
            font-size: 1rem;
            font-weight: 600;
            color: var(--accent);
            margin-top: 0.25rem;
        }

        .hero-copy {
            text-align: center;
            color: var(--text-muted);
            font-size: 0.93rem;
            margin-top: 0.75rem;
        }

        /* ── CHAT SHELL ── */
        .chat-shell {
            background: #ffffff;
            border: 1px solid rgba(148, 163, 184, 0.18);
            border-radius: 16px;
            padding: 1.5rem;
            box-shadow: var(--shadow-md);
        }

        .chat-messages-container {
            min-height: 400px;
            max-height: 63vh;
            overflow-y: auto;
            padding-bottom: 1rem;
        }

        .user-bubble, .assistant-bubble {
            margin-bottom: 1.1rem;
            padding: 0;
        }

        .user-bubble {
            display: flex;
            justify-content: flex-end;
            animation: slideInRight 0.3s ease-out;
        }

        .assistant-bubble {
            display: flex;
            justify-content: flex-start;
            animation: slideInLeft 0.3s ease-out;
        }

        .user-bubble-content {
            background: linear-gradient(135deg, var(--accent) 0%, var(--accent-strong) 100%);
            color: white;
            padding: 0.85rem 1.2rem;
            border-radius: 16px 16px 4px 16px;
            max-width: 65%;
            word-wrap: break-word;
            font-size: 0.93rem;
            line-height: 1.5;
            box-shadow: 0 4px 16px rgba(37, 99, 235, 0.22);
        }

        .assistant-bubble-content {
            background: #f8fafc;
            color: var(--text);
            padding: 0.9rem 1.2rem;
            border-radius: 16px 16px 16px 4px;
            max-width: 65%;
            word-wrap: break-word;
            font-size: 0.93rem;
            line-height: 1.5;
            border: 1px solid rgba(148, 163, 184, 0.2);
            box-shadow: var(--shadow-soft);
        }

        @keyframes slideInRight {
            from { opacity: 0; transform: translateX(16px); }
            to { opacity: 1; transform: translateX(0); }
        }

        @keyframes slideInLeft {
            from { opacity: 0; transform: translateX(-16px); }
            to { opacity: 1; transform: translateX(0); }
        }

        .response-card {
            background: #f8fafc;
            border-radius: 12px;
            padding: 0.9rem 1.2rem;
            margin: 0;
            border: 1px solid rgba(148, 163, 184, 0.2);
            color: var(--text);
            box-shadow: var(--shadow-soft);
        }

        .timestamp {
            font-size: 0.68rem;
            color: #94a3b8;
            margin-top: 0.45rem;
        }

        /* ── SUGGESTIONS SECTION ── */
        .suggestions-section {
            padding: 0;
            background: transparent;
            border-top: none;
            margin-top: 0.5rem;
            margin-bottom: 0.25rem;
        }

        .suggestions-title {
            font-size: 1rem;
            font-weight: 700;
            color: var(--text);
            margin-bottom: 0.85rem;
        }

        .suggestion-card-wrap .stButton > button {
            width: 100%;
            background: #ffffff !important;
            color: var(--text) !important;
            border: 1px solid rgba(148, 163, 184, 0.22) !important;
            border-radius: 10px !important;
            min-height: 52px;
            padding: 0.75rem 1.1rem !important;
            text-align: left;
            box-shadow: var(--shadow-soft);
            font-size: 0.9rem !important;
            font-weight: 500 !important;
            transition: all 0.18s ease;
        }

        .suggestion-card-wrap .stButton > button:hover {
            transform: translateY(-1px);
            border-color: rgba(37, 99, 235, 0.3) !important;
            box-shadow: 0 6px 18px rgba(37, 99, 235, 0.08) !important;
            color: var(--accent) !important;
        }

        .custom-input-row { margin-top: 1rem; }

        /* ── STICKY INPUT BAR ── */
        div[data-testid="stHorizontalBlock"]:has(div[data-testid="stTextInput"]) {
            position: sticky;
            left: auto;
            width: 100%;
            bottom: 0.8rem;
            z-index: 90;
            align-items: center;
            background: #ffffff;
            border: 1px solid rgba(148, 163, 184, 0.22);
            border-radius: 999px;
            padding: 0.25rem 0.4rem;
            box-shadow: 0 8px 32px rgba(15, 23, 42, 0.12);
        }

        div[data-testid="stHorizontalBlock"]:has(div[data-testid="stTextInput"]) > div {
            align-self: center;
        }

        /* Pill input only inside the sticky chat bar */
        div[data-testid="stHorizontalBlock"]:has(div[data-testid="stTextInput"]) .stTextInput > div > div > input {
            background: #ffffff !important;
            border: none !important;
            border-radius: 999px !important;
            color: var(--text) !important;
            font-size: 0.93rem !important;
            padding: 0.5rem 1.2rem !important;
            min-height: 34px !important;
            box-shadow: none !important;
        }

        div[data-testid="stHorizontalBlock"]:has(div[data-testid="stTextInput"]) .stTextInput > div > div > input:focus {
            border-color: transparent !important;
            box-shadow: none !important;
        }

        .stTextInput > div > div > input::placeholder {
            color: #94a3b8 !important;
        }

        [data-testid="stForm"] [data-testid="stTextInput"] > div {
            margin-bottom: 0;
        }

        /* ── Strip all border-radius from stForm ── */
        :root { --border-radius: 8px; }
        [data-testid="stForm"],
        [data-testid="stForm"] > *,
        [data-testid="stForm"] > * > *,
        [data-testid="stForm"] > * > * > *,
        [data-testid="stForm"] > * > * > * > * ,
        [data-testid="stForm"] > * > * > * > * > * {
            border-radius: 0 !important;
            -webkit-border-radius: 0 !important;
        }

        [data-testid="stForm"] [data-testid="stFormSubmitButton"] > button {
            height: 42px !important;
            min-height: 42px !important;
            width: auto !important;
            max-width: none !important;
            border-radius: 8px !important;
            background: var(--accent) !important;
            color: #ffffff !important;
            border: none !important;
            padding: 0 1.4rem !important;
            font-weight: 600 !important;
            font-size: 0.88rem !important;
            line-height: 1 !important;
            box-shadow: 0 4px 14px rgba(37,99,235,0.35) !important;
            transition: background 0.18s ease, box-shadow 0.18s ease !important;
        }

        [data-testid="stForm"] [data-testid="stFormSubmitButton"] > button:hover {
            background: var(--accent-hover) !important;
            box-shadow: 0 6px 20px rgba(37,99,235,0.45) !important;
        }

        /* ══════════════════════════════════════════
           SIDEBAR — Navy dark theme
        ══════════════════════════════════════════ */
        [data-testid="stSidebar"] {
            background: var(--sidebar-bg) !important;
            border-right: 1px solid rgba(255,255,255,0.06);
        }

        [data-testid="stSidebarCollapseButton"] [data-testid="stBaseButton-headerNoPadding"],
        [data-testid="stSidebarCollapseButton"] [data-testid="stIconMaterial"] {
            color: #94a3b8 !important;
        }

        [data-testid="stHeader"] [data-testid="stBaseButton-headerNoPadding"],
        [data-testid="stHeader"] [data-testid="stBaseButton-headerNoPadding"] [data-testid="stIconMaterial"] {
            color: var(--text) !important;
        }

        [data-testid="stSidebar"] > [data-testid="stVerticalBlock"] {
            gap: 0.6rem;
            padding: 1.25rem 1rem 1.5rem 1rem;
        }

        /* Sidebar text overrides */
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] div {
            color: var(--sidebar-text) !important;
        }

        [data-testid="stSidebar"] input {
            background: rgba(255,255,255,0.07) !important;
            border: 1px solid rgba(255,255,255,0.12) !important;
            color: var(--sidebar-text) !important;
            border-radius: 8px !important;
        }

        [data-testid="stSidebar"] input::placeholder {
            color: #64748b !important;
        }

        .sidebar-logo-row {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0 0 1rem 0;
            border-bottom: 1px solid rgba(255,255,255,0.07);
            margin-bottom: 0.5rem;
        }

        .sidebar-logo-icon {
            width: 2.4rem;
            height: 2.4rem;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: rgba(59,130,246,0.18);
            color: var(--sidebar-accent);
            border: 1px solid rgba(59,130,246,0.25);
            font-size: 1.1rem;
            flex: 0 0 auto;
        }

        .sidebar-logo-text { display: flex; flex-direction: column; gap: 0.08rem; }

        .sidebar-logo-title {
            font-size: 0.97rem;
            font-weight: 700;
            color: #f1f5f9 !important;
            letter-spacing: -0.02em;
        }

        .sidebar-logo-subtitle {
            font-size: 0.75rem;
            color: #64748b !important;
            font-weight: 400;
        }

        .sidebar-section-title {
            font-size: 0.7rem;
            font-weight: 700;
            color: #475569 !important;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-bottom: 0.45rem;
            margin-top: 0.3rem;
            display: block;
        }

        .sidebar-mini-stat {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.6rem 0.8rem;
            border-radius: 10px;
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.07);
            margin-bottom: 0.4rem;
        }

        .sidebar-mini-stat-label {
            font-size: 0.8rem;
            color: #94a3b8 !important;
            font-weight: 500;
        }

        .sidebar-mini-stat-value {
            font-size: 0.85rem;
            color: #f1f5f9 !important;
            font-weight: 600;
        }

        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            background: rgba(34, 197, 94, 0.15);
            color: #4ade80 !important;
            padding: 0.25rem 0.65rem;
            border-radius: 999px;
            font-size: 0.72rem;
            font-weight: 700;
            border: 1px solid rgba(34,197,94,0.2);
        }

        /* Sidebar buttons — global override inside sidebar */
        [data-testid="stSidebar"] div[data-testid="stButton"] > button,
        [data-testid="stSidebar"] .stButton > button {
            background: rgba(255,255,255,0.92) !important;
            color: #1e293b !important;
            border: 1px solid rgba(255,255,255,0.3) !important;
            border-radius: 8px !important;
            padding: 0.45rem 0.5rem !important;
            font-weight: 600 !important;
            font-size: 0.78rem !important;
            box-shadow: none !important;
            transition: background 0.15s ease !important;
            white-space: normal !important;
            word-break: break-word !important;
            line-height: 1.3 !important;
            min-height: 36px !important;
            height: auto !important;
        }

        [data-testid="stSidebar"] div[data-testid="stButton"] > button:hover,
        [data-testid="stSidebar"] .stButton > button:hover {
            background: #ffffff !important;
            border-color: rgba(255,255,255,0.5) !important;
            color: #1e293b !important;
        }

        [data-testid="stSidebar"] div[data-testid="stButton"] > button p,
        [data-testid="stSidebar"] .stButton > button p,
        [data-testid="stSidebar"] div[data-testid="stButton"] > button span,
        [data-testid="stSidebar"] .stButton > button span {
            color: #1e293b !important;
        }

        /* New Analysis CTA — accent blue */
        .st-key-new_chat [data-testid="stBaseButton-secondary"] {
            background: var(--accent) !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 0.7rem 1rem !important;
            box-shadow: 0 4px 14px rgba(37,99,235,0.35) !important;
            font-weight: 600 !important;
            font-size: 0.88rem !important;
            color: #ffffff !important;
        }

        .st-key-new_chat [data-testid="stBaseButton-secondary"]:hover {
            background: var(--accent-hover) !important;
            box-shadow: 0 6px 20px rgba(37,99,235,0.45) !important;
        }

        /* Logout — subtle ghost */
        .st-key-logout_user [data-testid="stBaseButton-secondary"] {
            background: rgba(239,68,68,0.1) !important;
            border: 1px solid rgba(239,68,68,0.2) !important;
            color: #fca5a5 !important;
            border-radius: 8px !important;
            font-size: 0.82rem !important;
        }

        .st-key-logout_user [data-testid="stBaseButton-secondary"]:hover {
            background: rgba(239,68,68,0.18) !important;
        }

        .sidebar-pill-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.45rem;
        }

        div[class*="st-key-session_delete_"] {
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
        }

        div[class*="st-key-session_delete_"] > div[data-testid="stButton"] {
            width: 100% !important;
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
        }

        div[class*="st-key-session_delete_"] .stButton > button,
        div[class*="st-key-session_delete_"] button[kind="secondary"],
        div[class*="st-key-session_delete_"] [data-testid="stBaseButton-secondary"] {
            width: 100% !important;
            min-width: 0 !important;
            min-height: 38px !important;
            padding: 0.3rem 0.4rem !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            line-height: 1 !important;
            text-align: center !important;
            font-size: 0.9rem !important;
        }

        .sidebar-list-item {
            display: flex;
            align-items: center;
            gap: 0.6rem;
            padding: 0.6rem 0.8rem;
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.07);
            border-radius: 10px;
            color: #cbd5e1 !important;
            font-size: 0.85rem;
            line-height: 1.35;
            margin-bottom: 0.35rem;
        }

        .sidebar-icon-line {
            width: 1.5rem;
            height: 1.5rem;
            border-radius: 6px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            color: var(--sidebar-accent) !important;
            background: rgba(59,130,246,0.12);
            flex: 0 0 auto;
            font-size: 0.78rem;
        }

        .sidebar-help {
            color: #475569 !important;
            font-size: 0.8rem;
            line-height: 1.5;
            padding: 0.1rem 0;
        }

        /* ══════════════════════════════════════════
           MAIN AREA — global button defaults
        ══════════════════════════════════════════ */
        div[data-testid="stButton"] > button,
        .stButton > button,
        button[kind="secondary"] {
            background: #ffffff !important;
            color: var(--text) !important;
            border: 1px solid rgba(148, 163, 184, 0.22) !important;
            border-radius: 8px !important;
            padding: 0.6rem 0.95rem !important;
            font-weight: 500 !important;
            transition: all 0.18s ease !important;
            font-size: 0.88rem !important;
            box-shadow: var(--shadow-soft) !important;
        }

        div[data-testid="stButton"] > button:hover,
        .stButton > button:hover,
        button[kind="secondary"]:hover {
            background: #f8fafc !important;
            box-shadow: 0 4px 14px rgba(15, 23, 42, 0.07) !important;
            border-color: rgba(37, 99, 235, 0.25) !important;
        }

        div[data-testid="stButton"] > button:active,
        .stButton > button:active,
        button[kind="secondary"]:active {
            background: #eff6ff !important;
        }

        .sql-code-container {
            background: #1e293b;
            border-radius: 14px;
            padding: 1rem;
            margin: 1rem 0;
            overflow-x: auto;
            border: 1px solid #334155;
        }

        .sql-code {
            color: #e2e8f0;
            font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
            font-size: 0.85rem;
            line-height: 1.6;
            white-space: pre-wrap;
            word-wrap: break-word;
        }

        .streamlit-expanderContent {
            background: rgba(248, 250, 252, 0.8);
            border: 1px solid rgba(148, 163, 184, 0.16);
            border-radius: 14px;
            padding: 1rem;
        }

        .loading-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 1rem;
            padding: 2rem;
            color: #666;
        }

        .loading-text {
            font-size: 0.95rem;
            font-weight: 500;
        }

        @media (max-width: 768px) {
            [data-testid="stMainBlockContainer"] {
                padding: 1rem 1rem 8rem 1rem !important;
            }

            div[data-testid="stHorizontalBlock"]:has(div[data-testid="stTextInput"]) {
                width: 100%;
                left: auto;
                bottom: 0.65rem;
            }

            .user-bubble-content,
            .assistant-bubble-content {
                max-width: 85%;
            }

            .header-title {
                font-size: 1.9rem;
            }

            .input-footer {
                width: calc(100% - 1rem);
                bottom: 0.5rem;
            }

            .sidebar-pill-grid {
                grid-template-columns: 1fr;
            }
        }

        @media (max-width: 1200px) and (min-width: 769px) {
            div[data-testid="stHorizontalBlock"]:has(div[data-testid="stTextInput"]) {
                width: 100%;
                left: auto;
                bottom: 0.75rem;
            }
        }

        ::-webkit-scrollbar {
            width: 8px;
        }

        ::-webkit-scrollbar-track {
            background: transparent;
        }

        ::-webkit-scrollbar-thumb {
            background: #d1d5db;
            border-radius: 999px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: #9ca3af;
        }

        /* ══════════════════════════════════════════
           AUTH PAGE
        ══════════════════════════════════════════ */

        /* Page-level: light grey background, center content */
        [data-testid="stAppViewContainer"]:has(.auth-left-panel) {
            background: #e8edf2 !important;
        }

        /* Remove all Streamlit padding on auth page */
        .auth-left-panel ~ * [data-testid="stMainBlockContainer"],
        .auth-right-panel ~ * [data-testid="stMainBlockContainer"] {
            padding: 0 !important;
        }

        /* Card wrapper: the two columns side-by-side */
        .auth-left-panel {
            background: #0f172a;
            border-radius: 12px 0 0 12px;
            padding: 2.5rem 2rem;
            min-height: 440px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            margin: 0;
        }

        .auth-right-panel {
            background: #ffffff;
        }

        .auth-kicker {
            display: inline-block;
            background: #2563eb;
            color: #ffffff !important;
            font-size: 0.68rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            padding: 0.3rem 0.75rem;
            border-radius: 6px;
            margin-bottom: 1.5rem;
        }

        .auth-title {
            font-size: 1.75rem;
            line-height: 1.2;
            font-weight: 800;
            color: #ffffff !important;
            margin-bottom: 2rem;
            letter-spacing: -0.03em;
        }

        .auth-points {
            display: flex;
            flex-direction: column;
            gap: 1rem;
            margin-bottom: 2rem;
        }

        .auth-point {
            display: flex;
            align-items: flex-start;
            gap: 0.75rem;
            font-size: 0.88rem;
            font-weight: 400;
            line-height: 1.45;
            color: #cbd5e1 !important;
        }

        .auth-point span { color: #cbd5e1 !important; }

        .auth-point-icon {
            font-size: 1rem;
            flex: 0 0 auto;
            margin-top: 0.05rem;
        }

        .auth-note {
            color: #475569 !important;
            font-size: 0.78rem;
            line-height: 1.5;
        }

        .auth-card-title {
            font-size: 2rem;
            font-weight: 800;
            color: #1e293b !important;
            margin-bottom: 1.5rem;
            letter-spacing: -0.04em;
        }

        /* Column layout: glue the two columns together as one card */
        .auth-left-panel ~ [data-testid="stVerticalBlock"],
        div:has(> .auth-left-panel) {
            padding: 0 !important;
            margin: 0 !important;
        }

        /* Force columns container to look like a unified card */
        [data-testid="stHorizontalBlock"]:has(.auth-left-panel) {
            gap: 0 !important;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 12px 48px rgba(15,23,42,0.14);
            max-width: 860px;
            margin: 8vh auto 0 auto !important;
            align-items: stretch !important;
        }

        [data-testid="stHorizontalBlock"]:has(.auth-left-panel) > [data-testid="stColumn"] {
            padding: 0 !important;
        }

        [data-testid="stHorizontalBlock"]:has(.auth-left-panel) > [data-testid="stColumn"]:first-child {
            background: #0f172a !important;
            border-radius: 16px 0 0 16px !important;
        }

        [data-testid="stHorizontalBlock"]:has(.auth-left-panel) > [data-testid="stColumn"]:last-child {
            background: #ffffff !important;
            border-radius: 0 16px 16px 0 !important;
            padding: 2.5rem 2.5rem 2rem 2.5rem !important;
        }

        /* Right column inputs */
        [data-testid="stHorizontalBlock"]:has(.auth-left-panel) [data-testid="stColumn"]:last-child label {
            font-size: 0.88rem !important;
            font-weight: 600 !important;
            color: #1e293b !important;
        }

        [data-testid="stHorizontalBlock"]:has(.auth-left-panel) [data-testid="stColumn"]:last-child .stTextInput > div > div > input {
            border: 1px solid #d1d5db !important;
            border-radius: 8px !important;
            background: #ffffff !important;
            color: #1e293b !important;
            font-size: 0.93rem !important;
            padding: 0.65rem 0.9rem !important;
            box-shadow: none !important;
        }

        [data-testid="stHorizontalBlock"]:has(.auth-left-panel) [data-testid="stColumn"]:last-child .stTextInput > div > div > input:focus {
            border-color: #2563eb !important;
            box-shadow: 0 0 0 3px rgba(37,99,235,0.12) !important;
        }

        [data-testid="stHorizontalBlock"]:has(.auth-left-panel) [data-testid="stColumn"]:last-child .stTextInput > div > div > input::placeholder {
            color: #9ca3af !important;
        }

        /* Submit button */
        [data-testid="stHorizontalBlock"]:has(.auth-left-panel) [data-testid="stColumn"]:last-child [data-testid="stFormSubmitButton"] > button {
            width: 100% !important;
            max-width: none !important;
            height: 48px !important;
            min-height: 48px !important;
            border-radius: 8px !important;
            background: #2563eb !important;
            color: #ffffff !important;
            border: none !important;
            font-weight: 600 !important;
            font-size: 1rem !important;
            box-shadow: 0 4px 14px rgba(37,99,235,0.3) !important;
            margin-top: 0.5rem !important;
        }

        [data-testid="stHorizontalBlock"]:has(.auth-left-panel) [data-testid="stColumn"]:last-child [data-testid="stFormSubmitButton"] > button:hover {
            background: #1d4ed8 !important;
        }

        [data-testid="stHorizontalBlock"]:has(.auth-left-panel) [data-testid="stColumn"]:last-child [data-testid="stFormSubmitButton"] > button * {
            color: #ffffff !important;
        }

        /* ── Auth card shape fix: override global 999px radius ── */
        [data-testid="stHorizontalBlock"]:has(.auth-left-panel) {
            border-radius: 16px !important;
            overflow: hidden !important;
        }

        [data-testid="stHorizontalBlock"]:has(.auth-left-panel) > [data-testid="stColumn"]:first-child,
        [data-testid="stHorizontalBlock"]:has(.auth-left-panel) > [data-testid="stColumn"]:first-child > div,
        [data-testid="stHorizontalBlock"]:has(.auth-left-panel) > [data-testid="stColumn"]:first-child > div > div {
            border-radius: 0 !important;
        }

        [data-testid="stHorizontalBlock"]:has(.auth-left-panel) > [data-testid="stColumn"]:last-child,
        [data-testid="stHorizontalBlock"]:has(.auth-left-panel) > [data-testid="stColumn"]:last-child > div,
        [data-testid="stHorizontalBlock"]:has(.auth-left-panel) > [data-testid="stColumn"]:last-child > div > div {
            border-radius: 0 !important;
        }

        /* Override global input 999px radius inside auth */
        [data-testid="stHorizontalBlock"]:has(.auth-left-panel) .stTextInput > div > div > input {
            border-radius: 8px !important;
            border: 1px solid #d1d5db !important;
        }

        @media (max-width: 780px) {
            [data-testid="stHorizontalBlock"]:has(.auth-left-panel) { flex-direction: column; margin: 2rem auto !important; }
        }
            .auth-page-wrap [data-testid="stColumn"]:first-child { border-radius: 16px 16px 0 0 !important; }
            .auth-page-wrap [data-testid="stColumn"]:last-child { border-radius: 0 0 16px 16px !important; }
        }
            .auth-left { flex: none; min-height: auto; }
            .auth-right { flex: none; }
        }
    </style>
    """, unsafe_allow_html=True)

inject_custom_css()

API_URL = f"http://127.0.0.1:{settings.API_PORT}/api/chat"
SESSION_URL = f"http://127.0.0.1:{settings.API_PORT}/api/session"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SESSIONS_DIR = PROJECT_ROOT / "data" / "sessions"

# Initialize session state
if "session_id" not in st.session_state:
    st.session_state.session_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_name" not in st.session_state:
    st.session_state.session_name = None

if "selected_session_id" not in st.session_state:
    st.session_state.selected_session_id = None

if "rename_target_session_id" not in st.session_state:
    st.session_state.rename_target_session_id = None

if "session_rename_text" not in st.session_state:
    st.session_state.session_rename_text = ""

if "sql_expanded" not in st.session_state:
    st.session_state.sql_expanded = {}

if "user_suggestion" not in st.session_state:
    st.session_state.user_suggestion = None

if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "auth_user" not in st.session_state:
    st.session_state.auth_user = None

if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "login"

if "auth_token" not in st.session_state:
    st.session_state.auth_token = None

# Restore session from query param on page refresh
if not st.session_state.authenticated:
    _token_param = st.query_params.get("token", "")
    if _token_param:
        _restored_user = validate_session_token(_token_param)
        if _restored_user:
            st.session_state.authenticated = True
            st.session_state.auth_user = _restored_user
            st.session_state.auth_token = _token_param

# Helper Functions
def extract_kpi_value(text):
    """Extract numeric values from text for KPI display"""
    numbers = re.findall(r'€?\s*[\d\s,\.]+(?:\s*(?:M|K|%|€)?)?', text)
    return numbers

def create_user_bubble(content, timestamp):
    """Create styled user message bubble"""
    st.markdown(f"""
    <div class="user-bubble">
        <div class="user-bubble-content">
            {content}
            <div class="timestamp">🕐 {timestamp}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_assistant_bubble(content, timestamp):
    """Create styled assistant message bubble"""
    st.markdown(f"""
    <div class="assistant-bubble">
        <div class="assistant-bubble-content">
            {content}
            <div class="timestamp">🕐 {timestamp}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_response_card(content, data=None):
    """Create response card wrapper"""
    
    # Check if this is a BI response
    if data and isinstance(data, dict) and data.get("type") == "bi_result":
        kpi_result = data.get("kpi_result", "")
        dashboard_link = data.get("dashboard_link", "")
        
        # Display KPI result
        st.markdown(f"""
        <div class="response-card" style="margin: 1rem 0;">
            {kpi_result}
        </div>
        """, unsafe_allow_html=True)
        
        # Display dashboard link as button
        if dashboard_link:
            st.link_button("📊 Ouvrir Power BI Dashboard", dashboard_link, use_container_width=False)
    else:
        # Normal response
        st.markdown(f"""
        <div class="response-card" style="margin: 1rem 0;">
            {content}
        </div>
        """, unsafe_allow_html=True)

def create_kpi_card(label, value):
    """Create KPI display card"""
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
    </div>
    """, unsafe_allow_html=True)

def create_sql_code_block(sql):
    """Create styled SQL code block"""
    st.markdown(f"""
    <div class="sql-code-container">
        <div class="sql-code">{sql}</div>
    </div>
    """, unsafe_allow_html=True)


def _session_display_name(session_id, session_name=None):
    name = (session_name or st.session_state.session_name or "").strip()
    return name if name else f"Session {session_id[:8]}"


def _message_pairs_from_history(history_items):
    messages = []
    for item in history_items:
        timestamp = item.get("timestamp", "")
        question = item.get("question", "")
        response = item.get("response", "")
        sql_query = item.get("sql") or item.get("sql_generated", "")

        messages.append({
            "role": "user",
            "content": question,
            "timestamp": timestamp,
        })
        messages.append({
            "role": "assistant",
            "content": response,
            "timestamp": timestamp,
            "sql": sql_query,
        })
    return messages


def _session_file_path(session_id):
    return SESSIONS_DIR / f"{session_id}.json"


def _read_session_record(session_id):
    session_file = _session_file_path(session_id)
    if not session_file.exists():
        return {}

    try:
        with open(session_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        interactions = data.get("interactions", []) if isinstance(data, dict) else []
        if not isinstance(interactions, list):
            interactions = []

        session_name = data.get("session_name") if isinstance(data, dict) else None
        if not session_name or not str(session_name).strip():
            session_name = f"Session {session_id[:8]}"

        first_question = interactions[0].get("question", "").strip() if interactions else ""
        if first_question and str(session_name).strip().lower() == first_question.lower():
            session_name = f"Session {session_id[:8]}"

        return {
            "session_id": session_id,
            "session_name": session_name,
            "created_at": data.get("created_at") if isinstance(data, dict) else None,
            "updated_at": data.get("updated_at") if isinstance(data, dict) else None,
            "interaction_count": data.get("interaction_count", len(interactions)) if isinstance(data, dict) else len(interactions),
            "interactions": interactions,
        }
    except Exception:
        return {}


def fetch_sessions_catalog():
    try:
        sessions = []
        if SESSIONS_DIR.exists():
            for session_file in SESSIONS_DIR.glob("*.json"):
                record = _read_session_record(session_file.stem)
                if record:
                    sessions.append(record)
        sessions.sort(key=lambda item: item.get("updated_at") or item.get("created_at") or "", reverse=True)
        return sessions
    except Exception:
        return []


def load_session_history(session_id):
    try:
        data = _read_session_record(session_id)
        if not data:
            return False

        st.session_state.session_id = session_id
        st.session_state.selected_session_id = session_id
        st.session_state.session_name = data.get("session_name") or _session_display_name(session_id)
        st.session_state.session_rename_text = st.session_state.session_name
        st.session_state.rename_target_session_id = session_id
        st.session_state.messages = _message_pairs_from_history(data.get("interactions", []))
        return True
    except Exception:
        return False


def rename_current_session(session_id, new_name):
    try:
        session_record = _read_session_record(session_id)
        if not session_record:
            return False

        session_record["session_name"] = new_name.strip()
        session_record["updated_at"] = datetime.now().isoformat()

        session_file = _session_file_path(session_id)
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session_record, f, indent=2, default=str, ensure_ascii=False)

        st.session_state.session_name = new_name.strip()
        st.session_state.session_rename_text = st.session_state.session_name
        return True
    except Exception:
        pass
    return False


def _create_new_session_state():
    resp = requests.post(SESSION_URL, timeout=5)
    if not resp.ok:
        return False

    new_session_id = resp.json()["session_id"]
    st.session_state.session_id = new_session_id
    st.session_state.selected_session_id = new_session_id
    st.session_state.session_name = f"Session {new_session_id[:8]}"
    st.session_state.session_rename_text = st.session_state.session_name
    st.session_state.rename_target_session_id = new_session_id
    st.session_state.messages = []
    return True


def delete_current_session(session_id):
    try:
        if not delete_session_record(session_id):
            return False

        if st.session_state.session_id == session_id or st.session_state.selected_session_id == session_id:
            if not _create_new_session_state():
                st.session_state.session_id = None
                st.session_state.selected_session_id = None
                st.session_state.session_name = None
                st.session_state.session_rename_text = ""
                st.session_state.rename_target_session_id = None
                st.session_state.messages = []
        elif st.session_state.rename_target_session_id == session_id:
            st.session_state.rename_target_session_id = st.session_state.session_id

        return True
    except Exception:
        return False


def queue_chat_prompt():
    """Capture the current input value and clear the field safely."""
    prompt_value = st.session_state.get("chat_input_text", "").strip()
    if prompt_value and prompt_value != st.session_state.get("pending_prompt"):
        st.session_state.pending_prompt = prompt_value
    st.session_state.chat_input_text = ""


def _set_authenticated_user(user: dict | None):
    st.session_state.authenticated = True
    st.session_state.auth_user = user or {}
    st.session_state.auth_mode = "login"
    token = create_session_token(user or {})
    st.session_state.auth_token = token
    st.query_params["token"] = token


def _logout_user():
    token = st.session_state.get("auth_token")
    if token:
        revoke_session_token(token)
    st.session_state.authenticated = False
    st.session_state.auth_user = None
    st.session_state.auth_token = None
    st.session_state.session_id = None
    st.session_state.selected_session_id = None
    st.session_state.session_name = None
    st.session_state.session_rename_text = ""
    st.session_state.rename_target_session_id = None
    st.session_state.messages = []
    st.session_state.sql_expanded = {}
    st.session_state.user_suggestion = None
    st.session_state.pending_prompt = None
    st.session_state.auth_mode = "login"
    st.query_params.clear()


def render_auth_screen():
    left_col, right_col = st.columns([4, 6], gap="small")

    with left_col:
        st.markdown(
            """
            <div class="auth-left-panel">
                <div>
                    <div class="auth-kicker">ACCÈS SÉCURISÉ</div>
                    <div class="auth-title">Connectez-vous pour accéder au chat BI.</div>
                    <div class="auth-points">
                        <div class="auth-point">
                            <span class="auth-point-icon">🛡️</span>
                            <span>Connexion obligatoire avant d&#39;utiliser le chat</span>
                        </div>
                        <div class="auth-point">
                            <span class="auth-point-icon">👤</span>
                            <span>Création de compte locale, rapide et sans dépendance externe</span>
                        </div>
                        <div class="auth-point">
                            <span class="auth-point-icon">🖥️</span>
                            <span>Une fois authentifié, retrouvez votre interface BI intacte</span>
                        </div>
                    </div>
                </div>
                <div class="auth-note">Astuce : utilisez votre email ou votre nom d&#39;utilisateur pour vous connecter.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right_col:
        st.markdown(
            """
            <div class="auth-right-panel">
                <div class="auth-card-title">Bienvenue</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.form("login_form", clear_on_submit=False):
            identifier = st.text_input(
                "Email ou nom d'utilisateur",
                placeholder="vous@exemple.com ou identifiant",
            )
            password = st.text_input(
                "Mot de passe",
                type="password",
                placeholder="Votre mot de passe",
            )
            login_submitted = st.form_submit_button("Se connecter", use_container_width=True)

        if login_submitted:
            success, message, user = authenticate_user(identifier, password)
            if success:
                st.success(message)
                _set_authenticated_user(user)
                st.rerun()
            else:
                st.error(message)


if not st.session_state.authenticated:
    render_auth_screen()
    st.stop()

# ── RBAC Router ──────────────────────────────────────────────
_role = (st.session_state.auth_user or {}).get("role", "user")
if _role == "admin":
    render_admin(st.session_state.auth_user)
    st.stop()

# ── User: Chatbot ─────────────────────────────────────────────
# Sidebar - Modern Design
with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-logo-row">
            <div class="sidebar-logo-icon">💬</div>
            <div class="sidebar-logo-text">
                <div class="sidebar-logo-title">AI BI Chatbot</div>
                <div class="sidebar-logo-subtitle">Mistral LLM - BI conversationnelle</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    user_profile = st.session_state.auth_user or {}
    if user_profile:
        display_name = html.escape(user_profile.get("full_name") or user_profile.get("username") or user_profile.get("email") or "Utilisateur")
        st.markdown(
            f"""
            <div class="sidebar-mini-stat">
                <span class="sidebar-mini-stat-label">Utilisateur</span>
                <span class="sidebar-mini-stat-value" style="max-width: 170px; text-align: right; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{display_name}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("Déconnexion", use_container_width=True, key="logout_user"):
            _logout_user()
            st.rerun()

    st.markdown('<div class="sidebar-cta">', unsafe_allow_html=True)
    if st.button("➕ Nouvelle Analyse", use_container_width=True, key="new_chat", help="Créer une nouvelle conversation"):
        try:
            if _create_new_session_state():
                st.rerun()
        except Exception as e:
            st.error(f"Erreur: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<span class="sidebar-section-title">Statut Système</span>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="sidebar-mini-stat">
            <span class="sidebar-mini-stat-label">Connecté</span>
            <span class="status-badge">● Actif</span>
        </div>
        <div class="sidebar-mini-stat">
            <span class="sidebar-mini-stat-label">Messages</span>
            <span class="sidebar-mini-stat-value">{len(st.session_state.messages)}</span>
        </div>
        {f'<div class="sidebar-mini-stat"><span class="sidebar-mini-stat-label">Session</span><span class="sidebar-mini-stat-value" style="font-size: 0.78rem;">{(st.session_state.session_name or ("Session " + st.session_state.session_id[:8])) if st.session_state.session_id else ""}</span></div>' if st.session_state.session_id else ''}
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.session_id:
        st.markdown('<span class="sidebar-section-title">Session Active</span>', unsafe_allow_html=True)
        current_name = st.session_state.session_name or _session_display_name(st.session_state.session_id)

        if st.session_state.rename_target_session_id != st.session_state.session_id:
            st.session_state.rename_target_session_id = st.session_state.session_id
            st.session_state.session_rename_text = current_name

        rename_value = st.text_input(
            "Renommer la session",
            key="session_rename_text",
            placeholder="Nom de la session",
            label_visibility="collapsed",
        )
        rename_col, delete_col = st.columns(2)
        with rename_col:
            if st.button("Renommer", key="rename_session_btn", use_container_width=True):
                if rename_value.strip():
                    if rename_current_session(st.session_state.session_id, rename_value.strip()):
                        st.rerun()
                else:
                    st.warning("Le nom de la session ne peut pas être vide.")
        with delete_col:
            if st.button("🗑️ Supprimer", key="delete_active_session_btn", use_container_width=True, help="Supprimer cette session"):
                if delete_current_session(st.session_state.session_id):
                    st.rerun()

    st.markdown('<span class="sidebar-section-title">Historique des sessions</span>', unsafe_allow_html=True)
    session_catalog = fetch_sessions_catalog()
    if session_catalog:
        for session_item in session_catalog[:12]:
            session_id = session_item.get("session_id")
            if session_id == st.session_state.session_id:
                continue
            session_name = _session_display_name(session_id, session_item.get("session_name"))
            row_left, row_right = st.columns([9, 1])
            with row_left:
                label = f"{session_name} ({session_item.get('interaction_count', 0)})"
                if st.button(label, key=f"session_load_{session_id}", use_container_width=True):
                    if load_session_history(session_id):
                        st.rerun()
            with row_right:
                if st.button("🗑", key=f"session_delete_{session_id}", help="Supprimer cette session", use_container_width=True):
                    if delete_current_session(session_id):
                        st.rerun()
    else:
        st.markdown(
            """
            <div class="sidebar-help">
                Aucune session sauvegardée pour le moment.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<span class="sidebar-section-title">Actions Clés</span>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-pill-grid">', unsafe_allow_html=True)
    col_clear, col_refresh = st.columns(2)
    with col_clear:
        if st.button("🗑️ Effacer", use_container_width=True, key="clear_chat", help="Effacer l'historique"):
            st.session_state.messages = []
            st.rerun()
    with col_refresh:
        if st.button("🔄 Rafraîchir", use_container_width=True, key="refresh_sessions", help="Mettre à jour les sessions"):
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<span class="sidebar-section-title">Connexions</span>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="sidebar-list-item">
            <span class="sidebar-icon-line">▣</span>
            <span>Connecté à : <strong>Power BI</strong></span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<span class="sidebar-section-title">Modèles et Fonctionnalités</span>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="sidebar-list-item"><span class="sidebar-icon-line">◌</span><span>Modèle : <strong>Mistral LLM</strong></span></div>
        <div class="sidebar-list-item"><span class="sidebar-icon-line">⇄</span><span>Génération SQL</span></div>
        <div class="sidebar-list-item"><span class="sidebar-icon-line">◉</span><span>Mémoire Contexte</span></div>
        <div class="sidebar-list-item"><span class="sidebar-icon-line">▤</span><span>Analyse Temps-Réel</span></div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<span class="sidebar-section-title">Aide</span>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="sidebar-help">
            Paramètres et assistance disponibles depuis cette zone. La vue reste volontairement discrète pour garder l’attention sur l’analyse.
        </div>
        """,
        unsafe_allow_html=True,
    )

# Main Header
st.markdown(
    """
    <div class="top-nav">
        <div>
            <div class="top-nav-label">Premium BI Workspace</div>
            <div class="top-nav-copy">Interface SaaS moderne pour explorer vos données métier</div>
        </div>
        <div class="top-nav-status"><span class="top-nav-dot"></span>Connexion active</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="header-section">
        <div class="header-title">AI BI Chatbot</div>
        <div class="header-subtitle">Analyse intelligente de vos données métier.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Main content wrapper
st.markdown('<div class="main-content">', unsafe_allow_html=True)
st.markdown('<div class="chat-shell">', unsafe_allow_html=True)

# Chat Messages Display
chat_container = st.container()

with chat_container:
    if len(st.session_state.messages) == 0:
        st.markdown(
            """
            <div class="hero-card">
                <div class="hero-title">Bienvenue | Lancez une analyse</div>
                <div class="hero-example">📊 Quel est mon CA de 2024 ?</div>
                <div class="hero-copy">Lancez une analyse, comparez vos indicateurs et explorez vos résultats en langage naturel.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    for idx, message in enumerate(st.session_state.messages):
        if message["role"] == "user":
            create_user_bubble(message["content"], message.get("timestamp", ""))
        else:
            create_response_card(message["content"], message.get("data"))

            st.markdown(f"<div class='timestamp'>🕐 {message.get('timestamp', '')}</div>", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Suggestions Section (before input)
if len(st.session_state.messages) < 1:
    st.markdown(
        """
        <div class="suggestions-section">
            <div class="suggestions-title">Explorez vos données</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    suggestions = [
        ("📊", "Quel est mon CA de 2024 ?", "sug_1"),
        ("🏆", "Quels sont mes Top 5 Clients ?", "sug_2"),
        ("📈", "Quel est mon CA par mois ?", "sug_3"),
        ("📅", "Derniers 10 mois", "sug_4")
    ]

    for row_start in range(0, len(suggestions), 2):
        cols = st.columns(2)
        for offset, col in enumerate(cols):
            index = row_start + offset
            if index < len(suggestions):
                icon, text, key = suggestions[index]
                with col:
                    st.markdown('<div class="suggestion-card-wrap">', unsafe_allow_html=True)
                    if st.button(f"{icon}  {text}", use_container_width=True, key=key):
                        st.session_state.user_suggestion = text
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

with st.form("chat_input_form", clear_on_submit=False):
    input_col, send_col = st.columns([8, 2])
    with input_col:
        prompt = st.text_input(
            "Question",
            value="",
            placeholder="Posez votre question sur les données...",
            key="chat_input_text",
            label_visibility="collapsed",
        )
    with send_col:
        send_clicked = st.form_submit_button("Lancer une analyse", on_click=queue_chat_prompt)

if st.session_state.pending_prompt:
    actual_prompt = st.session_state.pending_prompt
    st.session_state.pending_prompt = None
elif st.session_state.user_suggestion:
    actual_prompt = st.session_state.user_suggestion
    st.session_state.user_suggestion = None
else:
    actual_prompt = None

if actual_prompt:
    if not st.session_state.session_id:
        try:
            resp = requests.post(SESSION_URL, timeout=5)
            if resp.ok:
                st.session_state.session_id = resp.json()["session_id"]
        except Exception as e:
            st.error(f"Failed to create session: {e}")
            st.stop()
    
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": actual_prompt,
        "timestamp": timestamp
    })
    
    # Get response with loading state
    st.markdown('<div class="loading-spinner">⏳<div class="loading-text">Analyse des données...</div></div>', unsafe_allow_html=True)
    
    try:
        payload = {
            "question": actual_prompt,
            "session_id": st.session_state.session_id,
            "model": "mistral"
        }
        
        response = requests.post(API_URL, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        if data.get("session_id"):
            st.session_state.session_id = data["session_id"]
        
        answer = data.get("insight", "No response")
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Add to chat history
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "sql": data.get("sql_query"),
            "timestamp": timestamp,
            "data": data.get("data", [])
        })
        
        st.rerun()
        
    except Exception as e:
        error_msg = str(e)
        st.error(f"❌ Erreur: {error_msg}")
