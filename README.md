# AI-Powered BI Chatbot

This is a complete AI-powered Business Intelligence chatbot with both backend and frontend components. It uses FastAPI for the API, Streamlit for the UI, Ollama with the Mistral model for natural language processing, and SQL Server for data storage.

## Features

- **Natural Language to SQL**: Converts user questions into SQL Server queries using LLM.
- **Safe Query Execution**: Executes queries with basic safeguards.
- **Insight Generation**: Provides business insights based on query results.
- **Web Interface**: User-friendly Streamlit frontend.
- **Modular Architecture**: Clean separation of concerns across modules.

## Project Structure

- `app/`: Streamlit frontend
  - `app.py`: Main Streamlit application
- `api/`: FastAPI backend
  - `main.py`: Application entry point
  - `routes/chat.py`: Chat endpoint
  - `schemas/chat_schema.py`: Pydantic models
- `services/`: Business logic services
  - `llm_service.py`: Interface with Ollama API
  - `sql_generator.py`: SQL generation from questions
  - `insights_service.py`: Insight generation from data
- `data/`: Database interactions
  - `db_connection.py`: SQL Server connection and query execution
- `utils/`: Utilities
  - `prompts.py`: LLM prompt templates
- `config/`: Configuration
  - `settings.py`: Centralized application settings

## Setup

1. **Install Dependencies**:
   ```
   pip install -r requirements.txt
   ```

2. **Set Up Environment Variables**:
   Create a `.env` file in the root directory with your configurations:
   ```
   DB_SERVER=your_server
   DB_DATABASE=your_database
   DB_USERNAME=your_username
   DB_PASSWORD=your_password
   OLLAMA_URL=http://localhost:11434/api/generate
   OLLAMA_MODEL=mistral
   API_HOST=0.0.0.0
   API_PORT=8000
   STREAMLIT_HOST=0.0.0.0
   STREAMLIT_PORT=8501
   ```

3. **Install and Run Ollama**:
   - Download and install Ollama from https://ollama.ai/
   - Pull the Mistral model: `ollama pull mistral`
   - Ensure Ollama is running on `http://localhost:11434`

4. **Run the Backend**:
   ```
   uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Run the Frontend** (in a separate terminal):
   ```
   streamlit run app/app.py --server.address 0.0.0.0 --server.port 8501
   ```

## API Usage

- **POST /api/chat**: Send a JSON with `{"question": "Your natural language question"}`
- Response includes `sql_query`, `data`, and `insight`.

## Notes

- Ensure your database schema is known to the LLM for accurate SQL generation.
- The Streamlit app communicates with the FastAPI backend.
- This is a basic implementation; enhance prompts and add more validation for production use.