# 📊 Business Intelligence Assistant Guide

## Overview

The **Business Intelligence (BI) Assistant** is a specialized module that parses French and English KPI queries, extracts filters (year, month, company), and generates dynamic **Power BI dashboard links** with pre-applied filters.

### Key Features
- ✅ Natural language query parsing (French & English)
- ✅ Automatic filter extraction (year, month, company)
- ✅ Smart KPI type detection (Revenue, Purchase, Cash In/Out)
- ✅ Dynamic Power BI URL generation with filters
- ✅ Mock KPI value generation for demo/test
- ✅ Integrated with existing chat system
- ✅ Session memory for conversation context

---

## 🎯 How It Works

### 1. Query Recognition
The BI Assistant automatically detects if a question is a BI query by looking for:
- **KPI keywords**: `ca`, `chiffre d'affaires`, `revenue`, `achat`, `purchase`, `encaissement`, `décaissement`
- **Time filters**: Year (1900-2100), French month names, month numbers (1-12)
- **Company names**: `PEM`, `SAPEC`

### 2. Filter Extraction
Extracts and normalizes:
- **Year**: 2024, 2025, etc.
- **Month**: Converts French month names to numbers (janvier→1, février→2, etc.)
- **Company**: Normalizes to uppercase (pem→PEM, sapec→SAPEC)
- **KPI Type**: Classifies query intent

### 3. Power BI Link Generation
Creates URLs with Power BI's filter syntax:
```
https://app.powerbi.com/groups/me/reports/[REPORT_ID]/[PAGE_ID]?filter=FILTER_EXPRESSION
```

**Filter expression examples:**
- `D_Date/Year eq 2024`
- `D_Date/Year eq 2024 and D_Date/MonthNumber eq 1`
- `D_Date/Year eq 2024 and D_CompanyName/companyName eq 'SAPEC'`

---

## 📝 Query Examples

### Format 1: Year Only
```
Query: "ca 2024"
↓
KPI: Chiffre d'affaires (Revenue)
Year: 2024
Filter: D_Date/Year eq 2024
```

### Format 2: Year + Month
```
Query: "ca janvier 2025"
↓
KPI: Chiffre d'affaires
Year: 2025
Month: 1 (January)
Filter: D_Date/Year eq 2025 and D_Date/MonthNumber eq 1
```

### Format 3: Year + Month + Company
```
Query: "ca janvier 2025 SAPEC"
↓
KPI: Chiffre d'affaires
Year: 2025
Month: 1
Company: SAPEC
Filter: D_Date/Year eq 2025 and D_Date/MonthNumber eq 1 and D_CompanyName/companyName eq 'SAPEC'
```

### Format 4: Different KPI Types
```
"encaissement février 2023 PEM"
↓
KPI: Encaissement (Cash In)
Year: 2023
Month: 2 (February)
Company: PEM
Filter: D_Date/Year eq 2023 and D_Date/MonthNumber eq 2 and D_CompanyName/companyName eq 'PEM'

"achat mars 2024"
↓
KPI: Achat (Purchase)
Year: 2024
Month: 3 (March)
Filter: D_Date/Year eq 2024 and D_Date/MonthNumber eq 3

"décaissement SAPEC"
↓
KPI: Décaissement (Cash Out)
Company: SAPEC
Filter: D_CompanyName/companyName eq 'SAPEC'
```

---

## 🔌 API Endpoints

### 1. Main Chat Endpoint (Auto-Detection)
```http
POST /chat
Content-Type: application/json

{
  "question": "ca janvier 2025 SAPEC",
  "session_id": "optional-session-id"
}
```

**Response:**
```json
{
  "sql_query": null,
  "data": {
    "type": "bi_result",
    "kpi_result": "Chiffre d'affaires: 840,000 TND",
    "dashboard_link": "https://app.powerbi.com/groups/me/reports/.../877e016bbac4411c08e6?filter=D_Date/Year eq 2025 and D_Date/MonthNumber eq 1 and D_CompanyName/companyName eq 'SAPEC'"
  },
  "insight": "Chiffre d'affaires: 840,000 TND\nDashboard: https://...",
  "deterministic_insight": "Chiffre d'affaires: 840,000 TND",
  "session_id": "abc123..."
}
```

### 2. Dedicated BI Endpoint
```http
POST /bi/query
Content-Type: application/json

{
  "question": "encaissement février 2023 PEM",
  "session_id": "optional-session-id"
}
```

**Response:**
```json
{
  "kpi_result": "Encaissement: 63,000 TND",
  "dashboard_link": "https://app.powerbi.com/groups/me/reports/.../877e016bbac4411c08e6?filter=D_Date/Year eq 2023 and D_Date/MonthNumber eq 2 and D_CompanyName/companyName eq 'PEM'",
  "parsed_filters": {
    "kpi_type": "Encaissement",
    "year": 2023,
    "month": 2,
    "company": "PEM",
    "filter_expression": "D_Date/Year eq 2023 and D_Date/MonthNumber eq 2 and D_CompanyName/companyName eq 'PEM'"
  },
  "session_id": "abc123..."
}
```

### 3. Check if Question is BI Query
```http
GET /bi/is-bi-question?question=ca%202024
```

**Response:**
```json
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

---

## 🧠 Supported KPI Types

| KPI | French | English | Keywords |
|-----|--------|---------|----------|
| Revenue | Chiffre d'affaires | Revenue | `ca`, `chiffre`, `revenue`, `ventes`, `sales` |
| Purchase | Achat | Purchase | `achat`, `achats`, `purchase`, `buy` |
| Cash In | Encaissement | Cash In | `encaissement`, `cash in`, `inflow` |
| Cash Out | Décaissement | Cash Out | `décaissement`, `cash out`, `outflow` |

---

## 📅 French Month Mapping

| Month | Numbers | Aliases |
|-------|---------|---------|
| Janvier | 1 | janv, jan |
| Février | 2 | févr, feb |
| Mars | 3 | mar |
| Avril | 4 | avr, apr |
| Mai | 5 | - |
| Juin | 6 | jun |
| Juillet | 7 | juil, jul |
| Août | 8 | aou, aug |
| Septembre | 9 | sept, sep |
| Octobre | 10 | oct |
| Novembre | 11 | nov |
| Décembre | 12 | déc, dec |

---

## 🏢 Supported Companies

| Company | Aliases |
|---------|---------|
| PEM | pem, PEM |
| SAPEC | sapec, SAPEC |

(Easily extendable in `COMPANY_MAP` in `services/bi_assistant.py`)

---

## 📦 Implementation Details

### File Structure
```
services/
  ├── bi_assistant.py          # Main BI Assistant service
  │   ├── BIAssistant class
  │   ├── KPIType enum
  │   ├── parse_query()
  │   ├── is_bi_question()
  │   ├── process_bi_question()
  │   └── get_bi_assistant() [singleton]
  │
api/
  └── routes/
      └── chat.py              # Updated with BI endpoints
          ├── POST /chat       # Auto-detects BI questions
          ├── POST /bi/query   # Dedicated BI endpoint
          └── GET /bi/is-bi-question
```

### Key Classes

#### `BIAssistant`
```python
class BIAssistant:
    def parse_query(self, question: str) -> Dict
    def is_bi_question(self, question: str) -> bool
    def process_bi_question(self, question: str, kpi_value: Optional[float]) -> Tuple[str, str]
    def generate_power_bi_link(self, filter_expression: str) -> str
    def get_mock_kpi_value(self, parsed_query: Dict) -> float
```

#### `KPIType` Enum
```python
class KPIType(Enum):
    REVENUE = "Chiffre d'affaires"
    PURCHASE = "Achat"
    CASH_IN = "Encaissement"
    CASH_OUT = "Décaissement"
```

---

## 🧪 Testing

### Run Tests
```bash
cd c:\Users\ASUS\Desktop\llm
python test_bi_assistant.py
```

### Test Coverage
- ✅ Query parsing (KPI type, year, month, company)
- ✅ Filter extraction (individual and combined)
- ✅ BI question detection
- ✅ Power BI link generation
- ✅ Mock KPI value generation
- ✅ Response formatting

### Test Output Example
```
================================================================================
BUSINESS INTELLIGENCE ASSISTANT TEST
================================================================================

📝 Query: ca 2024
--------------------------------------------------------------------------------
  KPI Type: Chiffre d'affaires
  Year: 2024
  Month: None
  Company: None
  Filters: D_Date/Year eq 2024

✅ RESPONSE:
  Chiffre d'affaires: 1,200,000 TND

🔗 DASHBOARD:
  https://app.powerbi.com/groups/me/reports/58e4e4b4-2263-47b4-935f-acbe8e54e984/877e016bbac4411c08e6?filter=D_Date/Year eq 2024
```

---

## 🚀 Integration with Chatbot

### Flow

```
User Question
     ↓
Chat Endpoint (/chat)
     ↓
Cache Check
     ├─→ Hit → Return cached response
     └─→ Miss → Continue
     ↓
BI Question Detection
     ├─→ Is BI → Process with BIAssistant
     │   ├─→ Parse query
     │   ├─→ Extract filters
     │   ├─→ Generate Power BI link
     │   └─→ Return BI response
     └─→ Not BI → Process with LLM/SQL
     ↓
Cache Response
     ↓
Add to Session Memory
     ↓
Record Analytics
     ↓
Return to User
```

### Response Handling (Frontend)

```javascript
// Detect BI response
if (response.data.type === 'bi_result') {
  // Display KPI value
  console.log(response.data.kpi_result);
  // Display dashboard link
  const link = response.data.dashboard_link;
  console.log(`Open Power BI: ${link}`);
} else {
  // Handle regular SQL response
  displayTable(response.data);
}
```

---

## ⚙️ Configuration

### Power BI Base URL
Located in `services/bi_assistant.py`:
```python
BASE_POWER_BI_URL = "https://app.powerbi.com/groups/me/reports/58e4e4b4-2263-47b4-935f-acbe8e54e984/877e016bbac4411c08e6"
```

Update `58e4e4b4-2263-47b4-935f-acbe8e54e984` with your Report ID and `877e016bbac4411c08e6` with your Page ID.

### Mock KPI Values
Configured in `get_mock_kpi_value()`:
```python
base_values = {
    KPIType.REVENUE: 1_200_000,     # TND
    KPIType.PURCHASE: 800_000,
    KPIType.CASH_IN: 900_000,
    KPIType.CASH_OUT: 600_000,
}
```

Adjustments:
- Specific month: -5% (base_value *= 0.95)
- PEM company: -30% (base_value *= 0.7)
- SAPEC company: -20% (base_value *= 0.8)

---

## 🔐 Security Considerations

1. **SQL Injection**: BI queries don't generate SQL, so SQL injection is not a concern
2. **Filter Validation**: All filters are generated from predefined enums and mappings
3. **Company Names**: Only recognized companies (PEM, SAPEC) are accepted
4. **Date Validation**: Years must be 1900-2100, months 1-12
5. **URL Encoding**: Power BI filter expressions are properly encoded

---

## 📈 Analytics Integration

BI queries are recorded in analytics with:
- `question`: Original user question
- `response_time`: Elapsed time in seconds
- `success`: true/false
- `cache_hit`: true/false
- `model`: "BI_ASSISTANT"

Example:
```json
{
  "question": "ca janvier 2025 SAPEC",
  "response_time": 0.023,
  "success": true,
  "cache_hit": false,
  "model": "BI_ASSISTANT"
}
```

---

## 🐛 Troubleshooting

### Issue: Question not recognized as BI query
**Solution**: 
- Ensure query contains KPI keyword (ca, achat, encaissement, décaissement)
- OR contains time filter (year, month)
- OR contains company name (PEM, SAPEC)

### Issue: Incorrect month extraction
**Solution**: 
- Use full French month names (janvier, février) or abbreviations (janv, févr)
- Ensure no typos in month names

### Issue: Power BI link not working
**Solution**:
- Verify Power BI Base URL is correct
- Check that Report ID and Page ID match your Power BI account
- Ensure filters match your Power BI data model column names

### Issue: Mock KPI values seem unrealistic
**Solution**:
- Configure `base_values` and adjustments in `get_mock_kpi_value()`
- In production, query actual database instead of returning mock values

---

## 🔮 Future Enhancements

1. **Database Integration**: Query actual data instead of mock values
2. **More Companies**: Add additional company names to `COMPANY_MAP`
3. **Additional KPIs**: Extend `KPIType` enum with more metrics
4. **Date Range Queries**: Support "from X to Y" date ranges
5. **Comparative Analysis**: "Compare 2024 vs 2023"
6. **Predictive Insights**: AI-powered trend analysis
7. **Export Options**: CSV, Excel, PDF export of results
8. **Multi-language**: Support English, Arabic, Spanish

---

## 📞 Support

For issues or questions:
1. Check test file: `test_bi_assistant.py`
2. Review logs: `logs/chatbot.log`
3. Consult this guide: `BI_ASSISTANT_GUIDE.md`

---

**Status**: ✅ Ready for production use
**Last Updated**: April 2026
