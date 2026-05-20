# 🤖 AI BI Chatbot - Conversational Chat System

## Quick Start (60 seconds)

### 1. Start Backend
```bash
cd c:\Users\ASUS\Desktop\llm
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```
✅ Backend running on `http://127.0.0.1:8000`

### 2. Start Frontend (New Terminal)
```bash
cd c:\Users\ASUS\Desktop\llm
streamlit run app/app.py --server.port 8501
```
✅ Frontend running on `http://127.0.0.1:8501`

### 3. Open Browser
Navigate to: **`http://localhost:8501`**

### 4. Start Chatting
1. Click "➕ New Chat"
2. Type: "What is the revenue for 2024?"
3. Get: Simple KPI answer + Power BI link
4. Ask follow-up questions - system remembers context!

---

## What's New? 🎯

### Before (Single Question)
```
User: "revenue for 2024?"
Bot: One-time answer
User: "What about 2023?"
Bot: No context (forgot previous answer)
```

### After (Conversational)
```
User: "revenue for 2024?"
Bot: Remembers in session memory ✓
User: "Compare to last year"
Bot: Uses context → More accurate answers ✓
User: "Details for Q3?"
Bot: Understands conversation flow ✓
```

---

## Key Features ✨

| Feature | Status | Details |
|---------|--------|---------|
| **Session Management** | ✅ | Click "New Chat" to create session |
| **Chat History** | ✅ | All messages visible in chronological order |
| **Context Awareness** | ✅ | Bot remembers previous answers |
| **Timestamps** | ✅ | Each message shows when it was sent |
| **SQL Visibility** | ✅ | Click "SQL Query" to see generated queries |
| **Data Display** | ✅ | Click "Query Results" to see raw data |
| **Simple Responses** | ✅ | Concise KPI + Power BI redirect |
| **Multi-language** | 🟡 | French only (planned: English, Spanish) |
| **Search History** | 🔜 | Coming soon |
| **Export** | 🔜 | Save conversations as PDF |

---

## How Sessions Work

### Session Lifecycle
```
1. Click "New Chat"
   ↓
2. Backend creates UUID: 53e6cd2a-...
   ↓
3. Frontend stores in st.session_state.session_id
   ↓
4. Each question sent with this ID
   ↓
5. Backend maintains conversation memory
   ↓
6. Context injected into LLM prompts
   ↓
7. Click "Clear Chat" → Resets history (keeps session)
   ↓
8. Click "New Chat" → Creates NEW session
```

### What Gets Remembered?
- ✅ User questions
- ✅ Bot answers
- ✅ SQL queries generated
- ✅ Data results returned
- ✅ Timestamps of each interaction
- ✅ Last 5 interactions injected into LLM context

---

## Response Format

### Single-Row Result (KPI Format)
```
Q: "revenue for 2024?"
A: "Le chiffre d'affaires est 232,993,525.42, pour plus de détails veuillez consulter le dashboard Power BI."
```

### Multi-Row Result (Expandable Data)
```
Q: "How does 2024 compare to other years?"
A: [KPI from 2024 + expandable table showing 2023-2026]
```

### SQL Query Visibility
```
Click "📊 SQL Query" expander:
SELECT
    YEAR([Posting Date]) AS [Year],
    SUM([Amount]) AS [Revenue CA]
FROM [dbo].[Fact_CustomerPayementDetail]
WHERE YEAR([Posting Date]) >= 2022
GROUP BY YEAR([Posting Date])
ORDER BY [Year] DESC
```

---

## File Structure

```
llm/
├── app/
│   ├── app.py                    ← 🆕 CHAT INTERFACE (new)
│   ├── app_legacy.py             ← Backup of old UI
│   └── app_chat.py               ← Draft version
├── api/
│   ├── main.py
│   └── routes/
│       └── chat.py               ← Updated: context injection
├── services/
│   ├── memory_service.py         ← Enhanced: response storage
│   ├── llm_service.py            ← Enhanced: context injection
│   ├── sql_generator.py
│   └── ...other services...
├── config/
│   ├── settings.py
│   └── logger.py
├── data/
│   └── db_connection.py
├── CONVERSATIONAL_CHAT_IMPLEMENTATION.md  ← Full technical docs
├── CHAT_INTERFACE_DEPLOYMENT_SUMMARY.md   ← This summary
└── README.md                              ← This file
```

---

## API Reference

### POST /api/session
Create a new conversation session.

**Request:**
```bash
curl -X POST http://127.0.0.1:8000/api/session
```

**Response:**
```json
{
  "session_id": "53e6cd2a-4b3e-11ee-8e0b-0242ac120002"
}
```

### POST /api/chat
Send a question within a session.

**Request:**
```json
{
  "question": "What is the revenue for 2024?",
  "session_id": "53e6cd2a-4b3e-11ee-8e0b-0242ac120002",
  "model": "mistral"
}
```

**Response:**
```json
{
  "sql_query": "SELECT YEAR(...) FROM ...",
  "data": [{"Year": 2024, "Revenue CA": 232993525.42}],
  "insight": "Le chiffre d'affaires est 232,993,525.42, pour plus de détails veuillez consulter le dashboard Power BI.",
  "session_id": "53e6cd2a-4b3e-11ee-8e0b-0242ac120002"
}
```

### GET /api/schema
Get database schema for context.

### GET /api/analytics
Get business metrics definitions.

---

## Troubleshooting 🔧

### Problem: "ModuleNotFoundError"
**Solution:** Activate virtual environment
```bash
.venv\Scripts\activate
```

### Problem: "Connection refused" (port 8000)
**Solution:** Check if backend is running
```bash
# Backend not starting? Try:
pip install -r requirements.txt --force-reinstall
uvicorn api.main:app --port 8000
```

### Problem: "Connection refused" (port 8501)
**Solution:** Check if frontend is running
```bash
# Frontend not starting? Try:
streamlit run app/app.py --server.port 8501 --logger.level=debug
```

### Problem: "No active session" in chat
**Solution:** Click "➕ New Chat" button in sidebar

### Problem: Old UI still showing
**Solution:** 
```bash
# Hard refresh browser (Ctrl+Shift+Delete) or run:
# 1. Stop Streamlit (Ctrl+C)
# 2. Clear cache and restart:
streamlit cache clear
streamlit run app/app.py --server.port 8501
```

### Problem: Backend restarting constantly
**Solution:** File changes detected (auto-reload enabled). This is normal during development. If it's stuck, run:
```bash
ps aux | grep python  # Find process
kill -9 <PID>         # Kill it
# Then restart uvicorn
```

---

## Testing the System

### Manual Test Sequence
1. **Create Session**
   ```bash
   # Navigate to http://localhost:8501
   # Click "New Chat"
   # Check sidebar shows "Session: XXXX..."
   ```

2. **Single Question**
   ```
   Input: "What is the revenue for 2024?"
   Expected: French KPI sentence + Power BI mention
   ```

3. **Multi-Row Response**
   ```
   Input: "Show all years"
   Expected: Table with 2023-2026 data
   ```

4. **Follow-up Question**
   ```
   Input: "Which year was best?"
   Expected: Bot uses previous context
   ```

5. **Session Persistence**
   ```
   Input: "Tell me about 2024 again"
   Expected: Bot remembers from earlier
   ```

### API Test Sequence
```bash
# 1. Create session
curl -X POST http://127.0.0.1:8000/api/session

# 2. Save session_id returned
# 3. Send chat request
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"ca 2024?","session_id":"YOUR_SESSION_ID","model":"mistral"}'

# 4. Verify response contains "insight" field
```

---

## Performance

| Operation | Time | Status |
|-----------|------|--------|
| Session Creation | ~10ms | ✅ Fast |
| Chat Response | 400-500ms | ✅ Good (cached) |
| Chat Response (uncached) | 9-10s | ⚠️ LLM processing |
| Frontend Render | <100ms | ✅ Very fast |

**Typical Full Flow:** 1-2 seconds (UI + backend + DB)

---

## Configuration

### Backend Settings (`config/settings.py`)
```python
API_PORT = 8000              # FastAPI port
DB_SERVER = "..."            # SQL Server
DB_DATABASE = "BI_LLM"       # Database name
CACHE_NAMESPACE = "simple-v1::" # Cache prefix
MAX_INTERACTIONS = 10        # Per session max
```

### Frontend Settings (`app/app.py`)
```python
st.set_page_config(
    page_title="AI BI Chatbot",
    layout="wide",
    initial_sidebar_state="expanded"
)
```

---

## FAQ ❓

**Q: Can multiple users chat simultaneously?**
A: Yes! Each user gets their own session ID.

**Q: What happens if I refresh the browser?**
A: Session persists if session_id is in URL. Otherwise, click "New Chat" to start fresh.

**Q: Can I export conversations?**
A: Not yet (planned feature). Current workaround: Screenshot or copy-paste.

**Q: How long do sessions persist?**
A: In-memory only. Sessions lost on backend restart. (Database persistence planned).

**Q: Does it support other languages?**
A: Only French currently. Multi-language support planned.

**Q: Can I use a different LLM?**
A: Currently Mistral only. Multi-LLM support planned.

**Q: Is context always injected?**
A: Only when follow-up to previous question detected. Can be manual via prompt keywords.

---

## Production Checklist 📋

Before deploying to production:

- [ ] Run full test suite
- [ ] Load test with 50+ concurrent users
- [ ] Add authentication (JWT tokens)
- [ ] Move sessions to persistent database
- [ ] Implement rate limiting (10 req/min per user)
- [ ] Add monitoring and alerting
- [ ] Set up log rotation
- [ ] Configure SSL/TLS
- [ ] Document API for integrations
- [ ] Create user documentation
- [ ] Set up CI/CD pipeline
- [ ] Create Database backup strategy
- [ ] Performance test with real data volume

---

## Support & Documentation

- **Technical Docs:** `CONVERSATIONAL_CHAT_IMPLEMENTATION.md`
- **Deployment Guide:** `CHAT_INTERFACE_DEPLOYMENT_SUMMARY.md`
- **API Schema:** `http://127.0.0.1:8000/docs` (Swagger UI)
- **Database Schema:** `api/routes/chat.py` (SQL examples)

---

## Updates & Changelog

### Version 1.0.0 (Current)
- ✅ Full conversational chat interface
- ✅ Session-based memory
- ✅ Context-aware LLM responses
- ✅ Streamlit chat UI with message bubbles
- ✅ Expandable SQL and data views
- ✅ Simple French KPI format

### Planned (v1.1)
- 🔜 Persistent database sessions
- 🔜 User authentication
- 🔜 Multi-language support
- 🔜 Export to PDF
- 🔜 Conversation search

### Planned (v2.0)
- 🔜 Multi-LLM support
- 🔜 Analytics dashboard
- 🔜 Advanced filters
- 🔜 Real-time data updates

---

## Contributing

To add features:

1. Create a branch: `git checkout -b feature/my-feature`
2. Make changes
3. Test locally
4. Submit PR with documentation

---

## License

Proprietary - AI BI Chatbot Internal Use Only

---

**🎉 Ready to chat? Go to `http://localhost:8501` now!**

Questions? Check `CONVERSATIONAL_CHAT_IMPLEMENTATION.md` for detailed technical docs.
