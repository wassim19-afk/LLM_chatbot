# config/settings.py
# This module centralizes all configuration settings for the application.
# It loads environment variables and provides default values where appropriate.

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """
    Global settings class for the application.
    Contains database, API, and other configuration parameters.
    """

    # Database settings
    DB_SERVER: str = os.getenv('DB_SERVER', 'localhost')
    DB_DATABASE: str = os.getenv('DB_DATABASE', 'your_database')
    DB_USERNAME: str = os.getenv('DB_USERNAME', 'your_username')
    DB_PASSWORD: str = os.getenv('DB_PASSWORD', 'your_password')

    # Ollama API settings
    OLLAMA_URL: str = os.getenv('OLLAMA_URL', 'http://localhost:11434/api/generate')
    OLLAMA_MODEL: str = os.getenv('OLLAMA_MODEL', 'mistral')

    # FastAPI settings
    API_HOST: str = os.getenv('API_HOST', 'localhost')
    API_PORT: int = int(os.getenv('API_PORT', '8000'))

    # Streamlit settings
    STREAMLIT_HOST: str = os.getenv('STREAMLIT_HOST', '0.0.0.0')
    STREAMLIT_PORT: int = int(os.getenv('STREAMLIT_PORT', '8501'))

    # Cache settings
    CACHE_TTL_SECONDS: int = int(os.getenv('CACHE_TTL_SECONDS', '420'))  # 7 minutes
    CACHE_MAX_SIZE: int = int(os.getenv('CACHE_MAX_SIZE', '100'))

    # BI defaults (must match Power BI dashboard default scope)
    DEFAULT_BI_COMPANIES: str = os.getenv('DEFAULT_BI_COMPANIES', 'PEM,SAPEC')

    # Connection pool settings
    DB_POOL_SIZE: int = int(os.getenv('DB_POOL_SIZE', '5'))

# Instantiate settings
settings = Settings()