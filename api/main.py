# api/main.py
# This is the main entry point for the FastAPI application.
# It sets up the app, includes routes, and handles startup configurations.

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes.chat import router as chat_router
from config.settings import settings
from services.rag_service import get_rag_service

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="AI-Powered BI Chatbot Backend",
    description="A FastAPI backend for an AI chatbot that converts natural language to SQL, executes queries, and generates insights.",
    version="2.0.0"
)

# Add CORS middleware for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG service on startup
@app.on_event("startup")
async def startup_event():
    """Initialize services on app startup."""
    get_rag_service()

# Include the chat router
app.include_router(chat_router, prefix="/api", tags=["chat"])

@app.get("/")
async def root():
    """
    Root endpoint to check if the API is running.
    """
    return {"message": "AI BI Chatbot API is running", "version": "2.0.0"}

# To run the app: uvicorn api.main:app --reload --host 0.0.0.0 --port 8000