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
from services.auth_service import authenticate_user, register_user
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
            --bg: #f8fafc;
            --surface: rgba(255, 255, 255, 0.78);
            --surface-solid: #ffffff;
            --text: #1f2937;
            --text-muted: #6b7280;
            --line: rgba(148, 163, 184, 0.16);
            --accent: #4f46e5;
            --accent-strong: #4338ca;
            --shadow: 0 16px 34px rgba(15, 23, 42, 0.06);
            --shadow-soft: 0 8px 18px rgba(15, 23, 42, 0.05);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        html, body, [data-testid="stAppViewContainer"] {
            background: radial-gradient(circle at top left, rgba(79, 70, 229, 0.08), transparent 30%), linear-gradient(180deg, var(--bg), var(--bg));
            color: var(--text);
            font-family: 'Inter', 'Plus Jakarta Sans', sans-serif;
        }

        [data-testid="stHeader"] {
            background: rgba(248, 250, 252, 0.72);
            backdrop-filter: blur(16px);
            border-bottom: 1px solid rgba(148, 163, 184, 0.12);
        }

        [data-testid="stMainBlockContainer"] {
            padding: 1.25rem 2rem 10rem 2rem !important;
        }

        .main-content {
            padding: 0;
            max-width: 1280px;
            margin: 0 auto;
        }

        .top-nav {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            margin-top: 0.7rem;
            margin-bottom: 1rem;
            padding: 0.8rem 1rem;
            border-radius: 18px;
            background: rgba(255, 255, 255, 0.68);
            border: 1px solid rgba(148, 163, 184, 0.14);
            box-shadow: var(--shadow-soft);
            backdrop-filter: blur(16px);
        }

        .top-nav-label {
            font-size: 0.82rem;
            font-weight: 700;
            color: var(--accent);
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }

        .top-nav-copy {
            font-size: 0.88rem;
            color: var(--text-muted);
            font-weight: 500;
        }

        .header-section {
            background: transparent;
            padding: 0.2rem 0 1.1rem 0;
            margin-bottom: 0.9rem;
        }

        .header-title {
            font-size: 2.4rem;
            font-weight: 800;
            letter-spacing: -0.05em;
            color: var(--text);
            margin-bottom: 0.35rem;
        }

        .header-subtitle {
            font-size: 1rem;
            color: var(--text-muted);
            font-weight: 500;
        }

        .chat-shell {
            background: rgba(255, 255, 255, 0.58);
            border: 1px solid rgba(148, 163, 184, 0.14);
            border-radius: 28px;
            padding: 1.25rem;
            box-shadow: var(--shadow);
            backdrop-filter: blur(20px);
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
            padding: 0.95rem 1.25rem;
            border-radius: 18px 18px 6px 18px;
            max-width: 65%;
            word-wrap: break-word;
            font-size: 0.95rem;
            line-height: 1.5;
            box-shadow: 0 10px 24px rgba(79, 70, 229, 0.18);
        }

        .assistant-bubble-content {
            background: rgba(255, 255, 255, 0.92);
            color: var(--text);
            padding: 1rem 1.25rem;
            border-radius: 18px 18px 18px 6px;
            max-width: 65%;
            word-wrap: break-word;
            font-size: 0.95rem;
            line-height: 1.5;
            border: 1px solid rgba(148, 163, 184, 0.18);
            box-shadow: var(--shadow-soft);
        }

        @keyframes slideInRight {
            from { opacity: 0; transform: translateX(20px); }
            to { opacity: 1; transform: translateX(0); }
        }

        @keyframes slideInLeft {
            from { opacity: 0; transform: translateX(-20px); }
            to { opacity: 1; transform: translateX(0); }
        }

        .response-card {
            background: rgba(255, 255, 255, 0.9);
            border-radius: 20px;
            padding: 1rem 1.25rem;
            margin: 0;
            border: 1px solid rgba(148, 163, 184, 0.18);
            color: var(--text);
            box-shadow: var(--shadow-soft);
        }

        .timestamp {
            font-size: 0.7rem;
            color: #94a3b8;
            margin-top: 0.5rem;
        }

        .hero-card {
            background: rgba(255, 255, 255, 0.82);
            border: 1px solid rgba(148, 163, 184, 0.16);
            border-radius: 28px;
            box-shadow: var(--shadow);
            backdrop-filter: blur(18px);
            padding: 2rem 1.8rem;
            margin-bottom: 1.5rem;
        }

        .hero-illustration {
            width: 64px;
            height: 64px;
            border-radius: 22px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 1rem auto;
            color: var(--accent);
            background: linear-gradient(180deg, rgba(79, 70, 229, 0.14), rgba(79, 70, 229, 0.04));
            border: 1px solid rgba(79, 70, 229, 0.16);
            font-size: 1.75rem;
        }

        .hero-title {
            font-size: 1.15rem;
            font-weight: 700;
            color: var(--text);
            text-align: center;
            margin-bottom: 0.35rem;
        }

        .hero-copy {
            text-align: center;
            color: var(--text-muted);
            font-size: 0.95rem;
        }

        .suggestions-section {
            padding: 0;
            background: transparent;
            border-top: none;
            margin-top: 1.1rem;
        }

        .suggestions-title {
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 0.75rem;
        }

        .suggestion-card-wrap .stButton > button {
            width: 100%;
            background: rgba(255, 255, 255, 0.92) !important;
            color: var(--text) !important;
            border: 1px solid rgba(148, 163, 184, 0.18) !important;
            border-radius: 20px !important;
            min-height: 92px;
            padding: 1rem 1rem !important;
            text-align: left;
            box-shadow: var(--shadow-soft);
            transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
        }

        .suggestion-card-wrap .stButton > button:hover {
            transform: translateY(-2px);
            border-color: rgba(79, 70, 229, 0.26) !important;
            box-shadow: 0 14px 24px rgba(15, 23, 42, 0.08);
        }

        .suggestion-card-title {
            display: block;
            font-size: 0.95rem;
            font-weight: 700;
            color: var(--text);
            margin-top: 0.55rem;
        }

        .suggestion-card-subtitle {
            display: block;
            font-size: 0.8rem;
            color: var(--text-muted);
            margin-top: 0.15rem;
            font-weight: 500;
        }

        .custom-input-row {
            margin-top: 1rem;
        }

        div[data-testid="stHorizontalBlock"]:has(div[data-testid="stTextInput"]) {
            position: sticky;
            left: auto;
            width: 100%;
            bottom: 0.8rem;
            z-index: 90;
            align-items: center;
            background: #ffffff;
            border: 1px solid rgba(226, 232, 240, 1);
            border-radius: 999px;
            padding: 0.2rem 0.35rem;
            box-shadow: 0 14px 30px rgba(15, 23, 42, 0.12);
        }

        div[data-testid="stHorizontalBlock"]:has(div[data-testid="stTextInput"]) > div {
            align-self: center;
        }

        .stTextInput > div > div > input {
            background: #ffffff !important;
            border: 1px solid rgba(226, 232, 240, 1) !important;
            border-radius: 999px !important;
            color: var(--text) !important;
            font-size: 0.93rem !important;
            padding: 0.42rem 1.15rem !important;
            min-height: 32px !important;
            box-shadow: none !important;
        }

        .stTextInput > div > div > input:focus {
            border-color: rgba(79, 70, 229, 0.35) !important;
            box-shadow: 0 0 0 4px rgba(79, 70, 229, 0.12) !important;
        }

        .stTextInput > div > div > input::placeholder {
            color: #94a3b8 !important;
        }

        [data-testid="stForm"] [data-testid="stTextInput"] > div {
            margin-bottom: 0;
        }

        [data-testid="stForm"] [data-testid="stFormSubmitButton"] > button {
            height: 44px !important;
            min-height: 44px !important;
            width: auto !important;
            max-width: none !important;
            border-radius: 12px !important;
            background: #ffffff !important;
            color: var(--text) !important;
            border: 1px solid rgba(148, 163, 184, 0.16) !important;
            padding: 0 0.9rem !important;
            line-height: 1 !important;
            box-shadow: var(--shadow-soft) !important;
        }

        [data-testid="stSidebar"] {
            background: rgba(248, 250, 252, 0.84);
            backdrop-filter: blur(18px);
            border-right: 1px solid rgba(148, 163, 184, 0.14);
        }

        [data-testid="stSidebarCollapseButton"] [data-testid="stBaseButton-headerNoPadding"],
        [data-testid="stSidebarCollapseButton"] [data-testid="stIconMaterial"] {
            color: #000000 !important;
        }

        [data-testid="stHeader"] [data-testid="stBaseButton-headerNoPadding"],
        [data-testid="stHeader"] [data-testid="stBaseButton-headerNoPadding"] [data-testid="stIconMaterial"] {
            color: #000000 !important;
        }

        [data-testid="stSidebar"] > [data-testid="stVerticalBlock"] {
            gap: 0.8rem;
            padding: 1rem 0.9rem 1.25rem 0.9rem;
        }

        .sidebar-header {
            font-size: 1.1rem;
            font-weight: 800;
            letter-spacing: -0.03em;
            color: var(--text);
            margin-bottom: 0.25rem;
            padding: 0 0.15rem;
        }

        .sidebar-logo-row {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.15rem 0.15rem 0.8rem 0.15rem;
            margin-bottom: 0.25rem;
        }

        .sidebar-logo-icon {
            width: 2.5rem;
            height: 2.5rem;
            border-radius: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, rgba(79, 70, 229, 0.15), rgba(79, 70, 229, 0.05));
            color: var(--accent);
            border: 1px solid rgba(79, 70, 229, 0.18);
            box-shadow: var(--shadow-soft);
            flex: 0 0 auto;
        }

        .sidebar-logo-text {
            display: flex;
            flex-direction: column;
            gap: 0.1rem;
        }

        .sidebar-logo-title {
            font-size: 1rem;
            font-weight: 800;
            color: var(--text);
            letter-spacing: -0.03em;
        }

        .sidebar-logo-subtitle {
            font-size: 0.8rem;
            color: var(--text-muted);
            font-weight: 500;
        }

        .sidebar-section-title {
            font-size: 0.82rem;
            font-weight: 700;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-bottom: 0.6rem;
            display: block;
        }

        .sidebar-mini-stat {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.7rem 0.85rem;
            border-radius: 14px;
            background: rgba(255, 255, 255, 0.72);
            border: 1px solid rgba(148, 163, 184, 0.14);
            margin-bottom: 0.5rem;
            color: var(--text);
            box-shadow: var(--shadow-soft);
        }

        .sidebar-mini-stat-label {
            font-size: 0.82rem;
            color: var(--text-muted);
            font-weight: 600;
        }

        .sidebar-mini-stat-value {
            font-size: 0.88rem;
            color: var(--text);
            font-weight: 700;
        }

        .status-badge {
            display: inline-block;
            background: rgba(34, 197, 94, 0.12);
            color: #166534;
            padding: 0.3rem 0.8rem;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 700;
        }

        .st-key-new_chat [data-testid="stBaseButton-secondary"] {
            background: #111827 !important;
            border: none !important;
            border-radius: 999px !important;
            padding: 0.95rem 1rem !important;
            box-shadow: 0 10px 22px rgba(15, 23, 42, 0.22);
            font-weight: 700;
            color: #ffffff !important;
        }

        .st-key-new_chat [data-testid="stBaseButton-secondary"]:hover {
            transform: translateY(-1px);
            background: #000000 !important;
            box-shadow: 0 14px 28px rgba(15, 23, 42, 0.26);
        }

        .sidebar-pill-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.55rem;
        }

        .sidebar-pill-grid .stButton > button {
            background: #ffffff !important;
            color: var(--text) !important;
            border: 1px solid rgba(148, 163, 184, 0.16) !important;
            border-radius: 999px !important;
            padding: 0.7rem 0.8rem !important;
            font-weight: 600;
            box-shadow: var(--shadow-soft);
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
            min-height: 42px !important;
            padding: 0.35rem 0.5rem !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            line-height: 1 !important;
            text-align: center !important;
            font-size: 1rem !important;
        }

        .sidebar-list-item {
            display: flex;
            align-items: center;
            gap: 0.7rem;
            padding: 0.75rem 0.85rem;
            background: rgba(255, 255, 255, 0.72);
            border: 1px solid rgba(148, 163, 184, 0.14);
            border-radius: 16px;
            box-shadow: var(--shadow-soft);
            color: var(--text);
            font-size: 0.9rem;
            line-height: 1.35;
        }

        .sidebar-dot {
            width: 0.5rem;
            height: 0.5rem;
            border-radius: 999px;
            background: #22c55e;
            box-shadow: 0 0 0 4px rgba(34, 197, 94, 0.12);
            flex: 0 0 auto;
        }

        .sidebar-icon-line {
            width: 1.6rem;
            height: 1.6rem;
            border-radius: 999px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            color: var(--accent);
            background: rgba(79, 70, 229, 0.06);
            border: 1px solid rgba(79, 70, 229, 0.12);
            flex: 0 0 auto;
            font-size: 0.82rem;
        }

        .sidebar-help {
            color: var(--text-muted);
            font-size: 0.86rem;
            line-height: 1.5;
            padding: 0.2rem 0.1rem 0 0.1rem;
        }

        div[data-testid="stButton"] > button,
        .stButton > button,
        button[kind="secondary"] {
            background: #ffffff !important;
            color: var(--text) !important;
            border: 1px solid rgba(148, 163, 184, 0.18) !important;
            border-radius: 14px !important;
            padding: 0.7rem 1rem !important;
            font-weight: 600 !important;
            transition: all 0.2s ease !important;
            font-size: 0.9rem !important;
            box-shadow: var(--shadow-soft) !important;
        }

        div[data-testid="stButton"] > button:hover,
        .stButton > button:hover,
        button[kind="secondary"]:hover {
            background: #f8fafc !important;
            box-shadow: 0 10px 20px rgba(15, 23, 42, 0.08) !important;
            border-color: rgba(79, 70, 229, 0.22) !important;
        }

        div[data-testid="stButton"] > button:active,
        .stButton > button:active,
        button[kind="secondary"]:active {
            background: #eef2ff !important;
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

        .auth-shell {
            max-width: 1120px;
            margin: 1.25rem auto 0 auto;
            padding: 1.25rem;
        }

        .auth-grid {
            display: grid;
            grid-template-columns: 1.1fr 0.95fr;
            gap: 1rem;
            align-items: stretch;
        }

        .auth-hero,
        .auth-card {
            background: rgba(255, 255, 255, 0.82);
            border: 1px solid rgba(148, 163, 184, 0.16);
            border-radius: 28px;
            box-shadow: var(--shadow);
            backdrop-filter: blur(18px);
        }

        .auth-hero {
            padding: 2.25rem;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            min-height: 520px;
            background: radial-gradient(circle at top right, rgba(79, 70, 229, 0.12), transparent 34%), rgba(255, 255, 255, 0.84);
        }

        .auth-kicker {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            font-size: 0.8rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--accent);
            margin-bottom: 0.9rem;
        }

        .auth-title {
            font-size: 2.35rem;
            line-height: 1.05;
            letter-spacing: -0.05em;
            color: var(--text);
            margin-bottom: 0.8rem;
            font-weight: 800;
        }

        .auth-copy {
            font-size: 1rem;
            line-height: 1.6;
            color: var(--text-muted);
            max-width: 42rem;
        }

        .auth-points {
            display: grid;
            gap: 0.75rem;
            margin-top: 1.4rem;
        }

        .auth-point {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.85rem 0.95rem;
            border-radius: 16px;
            background: rgba(248, 250, 252, 0.8);
            border: 1px solid rgba(148, 163, 184, 0.14);
            color: var(--text);
            font-weight: 600;
        }

        .auth-point-badge {
            width: 2rem;
            height: 2rem;
            border-radius: 999px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: rgba(79, 70, 229, 0.1);
            color: var(--accent);
            font-size: 0.85rem;
            flex: 0 0 auto;
        }

        .auth-card {
            padding: 1.6rem;
        }

        .auth-card-title {
            font-size: 1.35rem;
            font-weight: 800;
            color: var(--text);
            margin-bottom: 0.35rem;
        }

        .auth-card-copy {
            color: var(--text-muted);
            margin-bottom: 1rem;
            line-height: 1.5;
        }

        /* Auth buttons: match logout style (rounded rectangle, bordered) */
        .auth-card div[data-testid="stButton"] > button,
        .auth-card div[data-testid="stFormSubmitButton"] > button,
        .auth-card .stFormSubmitButton > button,
        .auth-card .stFormSubmitButton button,
        .auth-card .stButton > button,
        .auth-card button,
        .auth-card button > div,
        .auth-card button > span {
            border-radius: 12px !important;
            border: 1px solid rgba(148, 163, 184, 0.16) !important;
            background: #ffffff !important;
            color: var(--text) !important;
            height: 44px !important;
            padding: 0 0.9rem !important;
            font-weight: 600 !important;
            box-shadow: var(--shadow-soft) !important;
            transition: transform 0.12s ease, box-shadow 0.12s ease, filter 0.12s ease !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            width: 100% !important;
            max-width: none !important;
        }

        /* Also force any inner element to not remain circular */
        .auth-card button, .auth-card button * {
            border-radius: 12px !important;
        }

        /* Override Streamlit's compact circular form submit button when inside auth-card */
        .auth-card [data-testid="stForm"] [data-testid="stFormSubmitButton"] > button,
        .auth-card [data-testid="stFormSubmitButton"] > button {
            width: 100% !important;
            max-width: none !important;
            height: 44px !important;
            min-height: 44px !important;
            border-radius: 12px !important;
            padding: 0 0.9rem !important;
            background: #ffffff !important;
            color: var(--text) !important;
            box-shadow: var(--shadow-soft) !important;
            border: 1px solid rgba(148, 163, 184, 0.16) !important;
        }

        .auth-card .stButton > button[role="button"],
        .auth-card div[data-testid="stFormSubmitButton"] > button {
            border-radius: 12px !important;
        }

        .auth-card div[data-testid="stButton"] > button:hover,
        .auth-card div[data-testid="stFormSubmitButton"] > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 12px 20px rgba(15, 23, 42, 0.08) !important;
        }

        .auth-card div[data-testid="stButton"] > button:active,
        .auth-card div[data-testid="stFormSubmitButton"] > button:active {
            transform: translateY(0);
        }

        /* Ensure the small icon/button circles elsewhere are unaffected by forcing width only inside auth-card */

        .auth-note {
            margin-top: 1rem;
            color: var(--text-muted);
            font-size: 0.9rem;
            line-height: 1.5;
        }

        @media (max-width: 900px) {
            .auth-grid {
                grid-template-columns: 1fr;
            }

            .auth-hero {
                min-height: auto;
            }
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


def _logout_user():
    st.session_state.authenticated = False
    st.session_state.auth_user = None
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


def render_auth_screen():
    st.markdown('<div class="auth-shell">', unsafe_allow_html=True)
    left_col, right_col = st.columns([1.1, 0.95])

    with left_col:
        st.markdown(
            """
            <div class="auth-hero">
                <div>
                    <div class="auth-kicker">Accès sécurisé</div>
                    <div class="auth-title">Connectez-vous pour accéder au chat BI.</div>
                    <div class="auth-copy">
                        Le chat reste inchangé après authentification. Si vous n’avez pas encore de compte,
                        créez-en un depuis la page d’inscription pour débloquer l’accès.
                    </div>
                    <div class="auth-points">
                        <div class="auth-point"><span class="auth-point-badge">1</span><span>Connexion obligatoire avant d’utiliser le chat</span></div>
                        <div class="auth-point"><span class="auth-point-badge">2</span><span>Création de compte locale, rapide et sans dépendance externe</span></div>
                        <div class="auth-point"><span class="auth-point-badge">3</span><span>Une fois authentifié, vous retrouvez l’interface BI telle quelle</span></div>
                    </div>
                </div>
                <div class="auth-note">Astuce: utilisez votre email ou votre nom d’utilisateur pour vous connecter.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right_col:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        st.markdown('<div class="auth-card-title">Bienvenue</div>', unsafe_allow_html=True)
        st.markdown('<div class="auth-card-copy">Choisissez une action ci-dessous.</div>', unsafe_allow_html=True)

        switch_left, switch_right = st.columns(2)
        with switch_left:
            if st.button("Se connecter", use_container_width=True, key="auth_switch_login"):
                st.session_state.auth_mode = "login"
                st.rerun()
        with switch_right:
            if st.button("Créer un compte", use_container_width=True, key="auth_switch_register"):
                st.session_state.auth_mode = "register"
                st.rerun()

        if st.session_state.auth_mode == "register":
            st.subheader("Créer un compte")
            with st.form("register_form", clear_on_submit=False):
                full_name = st.text_input("Nom complet", placeholder="Votre nom complet")
                email = st.text_input("Email", placeholder="vous@exemple.com")
                username = st.text_input("Username", placeholder="username")
                password = st.text_input("Mot de passe", type="password", placeholder="Mot de passe")
                confirm_password = st.text_input("Confirmer le mot de passe", type="password", placeholder="Confirmer le mot de passe")
                register_submitted = st.form_submit_button("Créer le compte", use_container_width=True)

            if register_submitted:
                if password != confirm_password:
                    st.error("Les deux mots de passe ne correspondent pas.")
                else:
                    success, message, user = register_user(full_name, email, username, password)
                    if success:
                        st.success(message)
                        _set_authenticated_user(user)
                        st.rerun()
                    else:
                        st.error(message)
        else:
            st.subheader("Se connecter")
            with st.form("login_form", clear_on_submit=False):
                identifier = st.text_input("Email ou nom d'utilisateur", placeholder="vous@exemple.com ou identifiant")
                password = st.text_input("Mot de passe", type="password", placeholder="Votre mot de passe")
                login_submitted = st.form_submit_button("Se connecter", use_container_width=True)

            if login_submitted:
                success, message, user = authenticate_user(identifier, password)
                if success:
                    st.success(message)
                    _set_authenticated_user(user)
                    st.rerun()
                else:
                    st.error(message)

        st.markdown(
            """
            <div class="auth-note">
                Si vous avez déjà un compte, connectez-vous. Sinon, créez d’abord un compte pour accéder au chat.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


if not st.session_state.authenticated:
    render_auth_screen()
    st.stop()

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
        <div class="top-nav-copy">● Connexion active</div>
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
                <div class="hero-illustration">◌</div>
                <div class="hero-title">Bienvenue ! Posez une question...</div>
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
            <div class="suggestions-title">Essayez un exemple</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    suggestions = [
        ("▣", "Quel est mon CA de 2024 ?", "sug_1"),
        ("◌", "Quels sont mes Top 5 Clients ?", "sug_2"),
        ("▤", "Quel est mon CA par mois ?", "sug_3"),
        ("⇄", "Derniers 10 mois", "sug_4")
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
    input_col, send_col = st.columns([12, 1])
    with input_col:
        prompt = st.text_input(
            "Question",
            value="",
            placeholder="Posez votre question sur les données...",
            key="chat_input_text",
            label_visibility="collapsed",
        )
    with send_col:
        send_clicked = st.form_submit_button("➤", on_click=queue_chat_prompt)

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
