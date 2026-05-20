# services/insights_service.py
# This module generates business insights from SQL query results.
# It sends the query and results to the LLM to analyze and provide meaningful insights.

from decimal import Decimal
import re
from typing import List, Dict, Any, Optional, Tuple

from services.llm_service import call_ollama
from utils.prompts import INSIGHTS_GENERATION_PROMPT


def generate_simple_response(data: List[Dict[str, Any]], question: Optional[str] = None, conversation_history: Optional[List[Dict[str, Any]]] = None) -> str:
    """
    Return a concise one-sentence French response.
    
    If conversation_history provided, may add context comparisons.

    Rules:
    - TOP N query: format and display all N rows with names/values
    - Monthly/Yearly queries: display all time periods with values
    - Single-row KPI: return direct KPI sentence with value.
    - Multi-row/table: redirect to Power BI dashboard.
    - With history: try to add comparison if relevant
    """
    if not data:
        return "Aucune donnée n'a été trouvée."

    # Check if this is a TOP N CUSTOMERS query
    if question and _is_top_customers_query(question):
        return _format_top_customers_response(data, question)
    
    # Check if this is a MONTHLY/YEARLY query
    if question and _is_monthly_yearly_query(question):
        return _format_monthly_yearly_response(data, question)

    row = _pick_relevant_row(data, question=question)
    if not row:
        return "Aucune donnée n'a été trouvée."

    label, value = _pick_kpi_pair(row)
    if label is None:
        return "Aucune donnée n'a été trouvée."

    base_response = f"Le {label} est {value}"
    
    # Try to add context from conversation history if provided
    if conversation_history and len(conversation_history) > 1:
        try:
            previous_response = conversation_history[-1].get("response", "")
            if previous_response:
                base_response += f" (comparé au précédent: {previous_response})"
        except:
            pass
    
    return base_response


def _is_top_customers_query(question: str) -> bool:
    """Detect if question is asking for top N customers."""
    return bool(re.search(r'top\s*(\d+)?\s*(client|customer|vente|sale)', question.lower()))


def _is_monthly_yearly_query(question: str) -> bool:
    """Detect if question is asking for monthly/yearly breakdown."""
    normalized = question.lower()
    # Check for patterns indicating monthly/yearly breakdown
    return bool(re.search(r'(mois|month|par mois|par\s*an|par\s*annee|annual|yearly|by\s*year|dernier|derniers|12\s*mois)', normalized))


def _format_top_customers_response(data: List[Dict[str, Any]], question: str) -> str:
    """Format response for TOP N customers queries."""
    if not data or len(data) == 0:
        return "Aucun client trouvé."
    
    # Extract number from question
    match = re.search(r'top\s*(\d+)', question.lower())
    top_n = int(match.group(1)) if match else len(data)
    
    # Build response with customer names and amounts
    lines = [f"Voici les {min(top_n, len(data))} meilleurs clients:"]
    
    for idx, row in enumerate(data[:top_n], 1):
        # Try to get Name and Total Sales Amount
        name = row.get('Name') or row.get('name') or row.get('Nom') or 'Unknown'
        amount = row.get('Total Sales Amount') or row.get('Total_Sales_Amount') or row.get('Montant') or 'N/A'
        
        # Format the amount if it's numeric
        try:
            if isinstance(amount, (int, float, Decimal)):
                amount_formatted = f"{float(amount):,.2f}€"
            else:
                amount_formatted = str(amount)
        except:
            amount_formatted = str(amount)
        
        lines.append(f"{idx}. {name}: {amount_formatted}")
    
    return "\n".join(lines)


def _format_monthly_yearly_response(data: List[Dict[str, Any]], question: str) -> str:
    """Format response for monthly/yearly breakdown queries."""
    if not data or len(data) == 0:
        return "Aucune donnée trouvée."
    
    # Detect if it's monthly or yearly
    is_monthly = bool(re.search(r'(mois|month|par mois)', question.lower()))
    period_label = "Mois" if is_monthly else "Année"
    
    # Build response with periods and amounts
    lines = [f"Voici le détail par {period_label.lower()}:"]
    lines.append("")  # Empty line for readability
    
    from datetime import datetime
    
    for idx, row in enumerate(data, 1):
        # Try to get Month/Year and Total Amount - check all possible column names
        period = None
        amount = None
        
        # Check for period columns
        for col in ['Month', 'month', 'Year', 'year', 'Date', 'date', 'Posting Date']:
            if col in row and row[col]:
                period = row[col]
                break
        
        # Check for amount columns
        for col in ['Total Amount', 'Total_Amount', 'Total', 'Chiffre d\'affaires CA', 'Montant', 'Revenue', 'Sales']:
            if col in row and row[col]:
                amount = row[col]
                break
        
        if not period:
            period = f"Période {idx}"
        
        if not amount:
            amount = 'N/A'
        
        # Format the period properly
        period_formatted = ""
        try:
            # If it's a date object
            if hasattr(period, 'year'):
                if is_monthly:
                    period_formatted = period.strftime("%B %Y")
                else:
                    period_formatted = period.strftime("%Y")
            # If it's a string
            elif isinstance(period, str):
                # Check if it looks like a year only (YYYY)
                if re.match(r'^\d{4}$', period.strip()):
                    period_formatted = period.strip()
                # Parse ISO date format 
                elif 'T' in period or '-' in period:
                    period_obj = datetime.fromisoformat(period.split('T')[0])
                    if is_monthly:
                        period_formatted = period_obj.strftime("%B %Y")
                    else:
                        period_formatted = period_obj.strftime("%Y")
                else:
                    period_formatted = str(period)
            else:
                period_formatted = str(period)
        except Exception as e:
            period_formatted = str(period)
        
        # Format the amount if it's numeric
        try:
            if isinstance(amount, (int, float, Decimal)):
                amount_formatted = f"{float(amount):,.2f}€"
            else:
                # Try to parse as float
                try:
                    amount_float = float(str(amount).replace(',', '.').replace('€', '').strip())
                    amount_formatted = f"{amount_float:,.2f}€"
                except:
                    amount_formatted = str(amount)
        except:
            amount_formatted = str(amount)
        
        lines.append(f"{idx}. {period_formatted}: {amount_formatted}")
    
    return "\n".join(lines)


def _pick_relevant_row(data: List[Dict[str, Any]], question: Optional[str] = None) -> Dict[str, Any]:
    """Select the most relevant row for a concise KPI answer."""
    if len(data) == 1:
        return data[0]

    question_year = _extract_year_from_question(question)
    if question_year is not None:
        for row in data:
            for key, value in row.items():
                if str(value).strip() == str(question_year):
                    return row

    for row in data:
        if any(isinstance(value, (int, float, Decimal)) for value in row.values()):
            return row

    return data[0]


def _extract_year_from_question(question: Optional[str]) -> Optional[int]:
    """Extract a 4-digit year from the question if present."""
    if not question:
        return None

    match = re.search(r"\b(20\d{2})\b", question)
    if match:
        return int(match.group(1))
    return None


def _pick_kpi_pair(row: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    """Return a label/value pair suitable for a sentence response."""
    numeric_items = []
    for key, value in row.items():
        if isinstance(value, Decimal):
            numeric_items.append((key, float(value)))
        elif isinstance(value, (int, float)):
            numeric_items.append((key, value))

    if not numeric_items:
        return None, None

    label_key, label_value = numeric_items[-1]
    if len(numeric_items) >= 2:
        for key, _ in numeric_items[:-1]:
            if "year" in key.lower() or "date" in key.lower():
                year_str = str(row[key])
                return label_key, f"{label_value:,.2f}€ in {year_str}"
                break

    if isinstance(label_value, (int, float)) and label_value < 0:
        return label_key, f"de {abs(label_value):,.2f}€"

    if isinstance(label_value, (int, float)):
        return label_key, f"{label_value:,.2f}€"

    return label_key, str(label_value)


def generate_insight(data: List[Dict[str, Any]], question: str, sql_query: str) -> str:
    """
    Generate an insightful response using the LLM.
    
    This sends the query/data to the LLM for analysis.
    Falls back to a simple response if LLM fails.
    """
    try:
        prompt = INSIGHTS_GENERATION_PROMPT.format(
            question=question,
            sql_query=sql_query,
            data=str(data)
        )
        response = call_ollama(prompt)
        return response if response else generate_simple_response(data, question)
    except Exception as e:
        return generate_simple_response(data, question)
