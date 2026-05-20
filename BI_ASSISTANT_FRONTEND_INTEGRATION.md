# 🎯 BI Assistant Frontend Integration Guide

## Overview
This guide shows frontend developers how to integrate the BI Assistant into web/mobile applications.

---

## JavaScript/React Integration

### 1. Basic Chat with Auto-Detection

```javascript
async function askQuestion(question) {
  const response = await fetch('http://localhost:8000/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question })
  });
  
  const data = await response.json();
  
  // Check if it's a BI response
  if (data.data?.type === 'bi_result') {
    return {
      type: 'BI',
      kpi: data.data.kpi_result,
      link: data.data.dashboard_link,
      insight: data.insight
    };
  }
  
  // Otherwise, it's a SQL response
  return {
    type: 'SQL',
    sql: data.sql_query,
    data: data.data,
    insight: data.insight
  };
}

// Usage
const result = await askQuestion("ca janvier 2025 SAPEC");

if (result.type === 'BI') {
  console.log(`KPI: ${result.kpi}`);
  console.log(`Dashboard: ${result.link}`);
  // Open dashboard
  window.open(result.link, '_blank');
} else {
  // Display table and chart
  displayResults(result.data);
}
```

### 2. React Component

```jsx
import React, { useState } from 'react';

function BIAssistantChat() {
  const [question, setQuestion] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question })
      });
      
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="e.g., ca janvier 2025 SAPEC"
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Loading...' : 'Ask'}
        </button>
      </form>

      {result && (
        <div className="result">
          {result.data?.type === 'bi_result' ? (
            // BI Result
            <div className="bi-result">
              <h3>{result.data.kpi_result}</h3>
              <a 
                href={result.data.dashboard_link} 
                target="_blank" 
                rel="noopener noreferrer"
                className="dashboard-link"
              >
                📊 Open Power BI Dashboard
              </a>
              <p className="insight">{result.insight}</p>
            </div>
          ) : (
            // SQL Result
            <div className="sql-result">
              <pre>{result.sql_query}</pre>
              <table>
                {/* Display result.data as table */}
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default BIAssistantChat;
```

### 3. Detecting BI Questions (Client-Side)

```javascript
async function isQuestion(question) {
  const response = await fetch(
    `/api/bi/is-bi-question?question=${encodeURIComponent(question)}`
  );
  
  const data = await response.json();
  
  if (data.is_bi_question) {
    console.log('BI Question detected!');
    console.log(`KPI: ${data.parsed_details.kpi_type}`);
    console.log(`Year: ${data.parsed_details.year}`);
    console.log(`Month: ${data.parsed_details.month}`);
    console.log(`Company: ${data.parsed_details.company}`);
    
    return data.parsed_details;
  }
  
  return null;
}

// Usage
const biDetails = await isQuestion("ca 2024");
if (biDetails) {
  // Show BI-specific UI
}
```

### 4. Direct BI Query Endpoint

```javascript
async function getBIInsights(question) {
  const response = await fetch('/api/bi/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question })
  });
  
  const data = await response.json();
  
  return {
    kpi: data.kpi_result,
    dashboard: data.dashboard_link,
    filters: data.parsed_filters,
    filterExpression: data.parsed_filters.filter_expression
  };
}

// Usage
const insights = await getBIInsights("encaissement février 2023 PEM");

// Display the KPI value
document.getElementById('kpi-value').textContent = insights.kpi;

// Create a clickable dashboard link
const link = document.createElement('a');
link.href = insights.dashboard;
link.target = '_blank';
link.textContent = '📊 View Dashboard';
link.className = 'dashboard-button';

// Show applied filters
console.log(`Filters: ${insights.filterExpression}`);
```

---

## Streamlit Integration

### 1. Basic Streamlit App

```python
import streamlit as st
import requests
import json

st.set_page_config(page_title="BI Assistant", layout="wide")

st.title("📊 BI Assistant")
st.markdown("Ask KPI questions and get Power BI dashboard links instantly")

# Input
question = st.text_input(
    "Ask a question",
    placeholder="e.g., ca janvier 2025 SAPEC"
)

if st.button("Get Insights"):
    if question:
        with st.spinner("Processing..."):
            try:
                # Call API
                response = requests.post(
                    "http://localhost:8000/chat",
                    json={"question": question}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Check if it's a BI result
                    if result.get("data", {}).get("type") == "bi_result":
                        # Display BI result
                        st.success("✅ BI Query Detected!")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.metric(
                                "KPI Result",
                                result["data"]["kpi_result"]
                            )
                        
                        with col2:
                            st.markdown(
                                f"""
                                [📊 Open Power BI Dashboard]({result['data']['dashboard_link']})
                                {{target=_blank}}
                                """
                            )
                        
                        # Show applied filters
                        st.subheader("Applied Filters")
                        st.json(result.get("data", {}))
                    else:
                        # Display SQL result
                        st.success("✅ SQL Query Generated")
                        st.code(result.get("sql_query"), language="sql")
                        st.dataframe(result.get("data"))
                else:
                    st.error(f"Error: {response.status_code}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Examples
st.markdown("---")
st.markdown("### 📝 Query Examples")

examples = [
    ("ca 2024", "Revenue for 2024"),
    ("ca janvier 2025 SAPEC", "SAPEC revenue for January 2025"),
    ("encaissement février 2023 PEM", "PEM cash in for February 2023"),
    ("achat mars", "Purchase data for March"),
    ("décaissement SAPEC", "SAPEC cash outflow"),
]

for example_q, description in examples:
    if st.button(f"📌 {description}", key=example_q):
        st.session_state.question = example_q
        st.rerun()
```

### 2. Advanced Streamlit with Session Management

```python
import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="BI Assistant Pro",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Session state
if 'session_id' not in st.session_state:
    # Create new session
    response = requests.post("http://localhost:8000/session")
    st.session_state.session_id = response.json()["session_id"]

if 'history' not in st.session_state:
    st.session_state.history = []

# Sidebar
with st.sidebar:
    st.title("⚙️ Settings")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("🔄 New Session"):
            response = requests.post("http://localhost:8000/session")
            st.session_state.session_id = response.json()["session_id"]
            st.session_state.history = []
            st.rerun()
    
    with col2:
        st.text(f"Session: {st.session_state.session_id[-8:]}")
    
    st.markdown("---")
    st.subheader("📋 Query History")
    
    for i, h in enumerate(st.session_state.history):
        if st.button(f"🔗 {h['question'][:30]}...", key=f"hist_{i}"):
            pass

# Main content
st.title("📊 Business Intelligence Assistant")

# Question input
question = st.text_input(
    "Your question:",
    placeholder="e.g., ca janvier 2025 SAPEC"
)

col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    submit = st.button("🔍 Get Insights", use_container_width=True)

with col2:
    st.button("💾 Save", use_container_width=True)

with col3:
    st.button("📤 Export", use_container_width=True)

if submit and question:
    with st.spinner("Processing..."):
        response = requests.post(
            "http://localhost:8000/chat",
            json={
                "question": question,
                "session_id": st.session_state.session_id
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Add to history
            st.session_state.history.append({
                "question": question,
                "timestamp": datetime.now()
            })
            
            # BI Result
            if result.get("data", {}).get("type") == "bi_result":
                st.success("✅ BI Query Processed")
                
                # KPI Card
                kpi_text = result["data"]["kpi_result"]
                value = kpi_text.split(": ")[1] if ": " in kpi_text else ""
                
                with st.container(border=True):
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        st.metric("KPI Value", value)
                    
                    with col2:
                        dashboard_url = result["data"]["dashboard_link"]
                        st.markdown(
                            f"""
                            <a href="{dashboard_url}" target="_blank">
                                <button style="width: 100%; padding: 10px;">
                                    📊 Open Power BI
                                </button>
                            </a>
                            """,
                            unsafe_allow_html=True
                        )
                
                # Filters applied
                with st.expander("🔍 Filters Applied"):
                    filters = result.get("data", {})
                    st.json(filters)
            
            # SQL Result
            else:
                st.success("✅ SQL Query Generated")
                
                with st.expander("📝 SQL Query"):
                    st.code(result.get("sql_query"), language="sql")
                
                with st.expander("📊 Results"):
                    st.dataframe(result.get("data"))
        else:
            st.error(f"Error: {response.text}")
```

---

## cURL Examples

### Check if Question is BI Query
```bash
curl "http://localhost:8000/bi/is-bi-question?question=ca%202024"

# Response
{
  "is_bi_question": true,
  "question": "ca 2024",
  "parsed_details": {
    "kpi_type": "Chiffre d'affaires",
    "year": 2024,
    "month": null,
    "company": null
  }
}
```

### Get BI Query Results
```bash
curl -X POST http://localhost:8000/bi/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "encaissement février 2023 PEM"
  }'

# Response
{
  "kpi_result": "Encaissement: 598,500 TND",
  "dashboard_link": "https://app.powerbi.com/...?filter=D_Date/Year eq 2023 and D_Date/MonthNumber eq 2 and D_CompanyName/companyName eq 'PEM'",
  "parsed_filters": {
    "kpi_type": "Encaissement",
    "year": 2023,
    "month": 2,
    "company": "PEM",
    "filter_expression": "D_Date/Year eq 2023 and D_Date/MonthNumber eq 2 and D_CompanyName/companyName eq 'PEM'"
  }
}
```

---

## HTML/CSS Examples

### Simple Dashboard Widget

```html
<!DOCTYPE html>
<html>
<head>
  <style>
    .bi-card {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 20px;
      border-radius: 8px;
      margin: 10px 0;
      box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .bi-kpi {
      font-size: 32px;
      font-weight: bold;
      margin: 10px 0;
    }
    
    .bi-dashboard-btn {
      background: white;
      color: #667eea;
      padding: 10px 20px;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-weight: bold;
      margin-top: 10px;
    }
    
    .bi-dashboard-btn:hover {
      background: #f0f0f0;
    }
    
    .bi-filters {
      font-size: 12px;
      margin-top: 10px;
      opacity: 0.9;
    }
  </style>
</head>
<body>
  <div id="bi-result"></div>
  
  <script>
    async function displayBIResult(question) {
      const response = await fetch('/api/bi/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question })
      });
      
      const data = await response.json();
      
      const html = `
        <div class="bi-card">
          <div class="bi-kpi">${data.kpi_result}</div>
          <button class="bi-dashboard-btn" 
                  onclick="window.open('${data.dashboard_link}', '_blank')">
            📊 Open Power BI Dashboard
          </button>
          <div class="bi-filters">
            Filters: ${data.parsed_filters.filter_expression}
          </div>
        </div>
      `;
      
      document.getElementById('bi-result').innerHTML = html;
    }
    
    // Display result for "ca janvier 2025 SAPEC"
    displayBIResult("ca janvier 2025 SAPEC");
  </script>
</body>
</html>
```

---

## Error Handling

```javascript
async function askQuestionWithErrorHandling(question) {
  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    
    // Validate response structure
    if (!data.data) {
      throw new Error("Invalid response format");
    }
    
    return data;
    
  } catch (error) {
    console.error("Error:", error);
    return {
      error: true,
      message: error.message,
      type: error.name
    };
  }
}
```

---

## Performance Tips

1. **Cache BI Queries**: Same question asked twice within 7 minutes returns cached result (<10ms)
2. **Pre-check Questions**: Use `/bi/is-bi-question` to route logic client-side
3. **Batch Requests**: Group multiple questions into one request
4. **Session Reuse**: Keep session_id between requests for context
5. **Lazy Load**: Only fetch dashboard link when user clicks

---

## Testing Your Integration

```javascript
// Test all endpoints
async function testBIAssistant() {
  console.log("Testing BI Assistant...");
  
  // Test 1: Chat endpoint with BI auto-detection
  console.log("\n1. Testing /chat with BI auto-detection");
  const chat = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question: "ca 2024" })
  });
  console.log(await chat.json());
  
  // Test 2: Dedicated BI endpoint
  console.log("\n2. Testing /bi/query");
  const bi = await fetch('/api/bi/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question: "encaissement février 2023 PEM" })
  });
  console.log(await bi.json());
  
  // Test 3: BI question checker
  console.log("\n3. Testing /bi/is-bi-question");
  const check = await fetch('/api/bi/is-bi-question?question=ca%202024');
  console.log(await check.json());
  
  console.log("\n✅ All tests completed!");
}

// Run tests
testBIAssistant();
```

---

## Deployment Considerations

1. **CORS**: Configure CORS for frontend domain
2. **Authentication**: Add API key validation for /bi endpoints
3. **Rate Limiting**: Implement rate limiting for /bi/query
4. **Monitoring**: Track BI query metrics separately
5. **Caching Headers**: Set cache headers for dashboard links
6. **CDN**: Consider CDN for Power BI link distribution

---

**Ready to integrate!** Choose your framework and get started.
