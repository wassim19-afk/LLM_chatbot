# services/insights_service.py
# This module generates business insights from SQL query results.
# It sends the query and results to the LLM to analyze and provide meaningful insights.

from decimal import Decimal
import re
from typing import List, Dict, Any, Optional, Tuple

from services.llm_service import call_ollama
from utils.prompts import INSIGHTS_GENERATION_PROMPT

CURRENCY = "FCFA"


def _format_amount(value) -> str:
    """Format a numeric amount with correct currency and locale."""
    try:
        v = float(value)
        if abs(v) >= 1_000:
            return f"{v:,.0f} {CURRENCY}"
        return f"{v:,.2f} {CURRENCY}"
    except Exception:
        return str(value)


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

    if not isinstance(data, list) or not data:
        return str(data) if data else "Aucune donnée n'a été trouvée."

    # Check if this is an OVERDUE customers query
    if question and _is_overdue_query(question):
        return _format_overdue_response(data)

    # Check if this is a VENDOR query
    if question and _is_vendor_query(question):
        return _format_vendor_response(data, question)

    # Check if this is a SALESPEOPLE query
    if question and _is_salespeople_query(question):
        return _format_salespeople_response(data, question)

    # Check if this is a PAYMENTS query
    if question and _is_payments_query(question):
        return _format_payments_response(data)

    # Check if this is a BALANCE query
    if question and _is_balance_query(question):
        return _format_balance_response(data)

    # Check if this is a STOCK query
    if question and _is_stock_query(question):
        return _format_stock_response(data, question)

    # Check if this is a PURCHASES query
    if question and _is_purchases_query(question):
        return _format_purchases_response(data, question)

    # Check if this is a DISBURSEMENTS query
    if question and _is_disbursements_query(question):
        return _format_disbursements_response(data, question)

    # Check if this is an EXPIRED PRODUCTS query
    if question and _is_expired_products_query(question):
        return _format_expired_products_response(data, question)

    # Check if this is a SALES DETAIL query
    if question and _is_sales_detail_query(question):
        return _format_sales_detail_response(data, question)

    # Check if this is a TOP N PRODUCTS query
    if question and _is_top_products_query(question):
        return _format_top_products_response(data, question)

    # Check if this is a TOP N CUSTOMERS query
    if question and _is_top_customers_query(question):
        return _format_top_customers_response(data, question)
    
    # Check if this is a YEAR COMPARISON query (e.g. "CA 2023 vs 2024")
    if question and _is_year_comparison_query(question):
        return _format_year_comparison_response(data)

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
        except Exception:
            pass
    
    return base_response


def _is_vendor_query(question: str) -> bool:
    q = question.lower()
    return bool(re.search(r'fournisseur|vendor|supplier|achat|purchase', q))


def _format_vendor_response(data: List[Dict[str, Any]], question: str) -> str:
    if not data:
        return "Aucun fournisseur trouvé."
    is_overdue = bool(re.search(r'retard|impaye|overdue|late', question.lower()))
    label = "fournisseurs en retard de paiement" if is_overdue else "principaux fournisseurs"
    match = re.search(r'\b(\d+)\b', question)
    top_n = int(match.group(1)) if match else len(data)
    lines = [f"Voici les {min(top_n, len(data))} {label} :"]
    for idx, row in enumerate(data[:top_n], 1):
        name = row.get('Vendor Name') or row.get('Vendor No_') or 'Inconnu'
        amount = row.get('Total Achats') or row.get('Montant Du') or row.get('Purchase (LCY)')
        nb = row.get('Nb Factures') or row.get('Nb Ecritures')
        due = row.get('Echeance La Plus Ancienne') or row.get('Due Date')
        amount_str = _format_amount(amount) if amount is not None else 'N/A'
        nb_str = f" · {int(nb)} écritures" if nb is not None else ""
        due_str = f" · éch. {str(due)[:10]}" if due else ""
        lines.append(f"{idx}. {name}: {amount_str}{nb_str}{due_str}")
    return "\n".join(lines)


def _is_salespeople_query(question: str) -> bool:
    q = question.lower()
    return bool(re.search(r'vendeur|commercial|salesperson|salesrep|representant', q))


def _format_salespeople_response(data: List[Dict[str, Any]], question: str) -> str:
    if not data:
        return "Aucun vendeur trouvé."
    match = re.search(r'\b(\d+)\b', question)
    top_n = int(match.group(1)) if match else len(data)
    lines = [f"Voici les {min(top_n, len(data))} meilleurs vendeurs :"]
    for idx, row in enumerate(data[:top_n], 1):
        name = row.get('Vendeur') or row.get('Salesperson Code') or 'Inconnu'
        ca = row.get('Total CA') or row.get('Amount')
        nb_t = row.get('Nb Transactions')
        nb_c = row.get('Nb Clients')
        ca_str = _format_amount(ca) if ca is not None else 'N/A'
        nb_t_str = f" · {int(nb_t)} transactions" if nb_t is not None else ""
        nb_c_str = f" · {int(nb_c)} clients" if nb_c is not None else ""
        lines.append(f"{idx}. {name}: {ca_str}{nb_t_str}{nb_c_str}")
    return "\n".join(lines)


def _is_payments_query(question: str) -> bool:
    q = question.lower()
    return bool(re.search(r'paiement|payment|encaissement|recouvrement|recu|credit amount', q))


def _format_payments_response(data: List[Dict[str, Any]]) -> str:
    if not data:
        return "Aucun paiement trouvé."
    lines = [f"Voici les encaissements par client ({len(data)} clients) :"]
    for idx, row in enumerate(data[:20], 1):
        name = row.get('Customer Name') or row.get('Customer No_') or 'Inconnu'
        amount = row.get('Total Encaisse') or row.get('Credit Amount')
        nb = row.get('Nb Paiements')
        last = row.get('Dernier Paiement')
        amount_str = _format_amount(amount) if amount is not None else 'N/A'
        nb_str = f" · {int(nb)} paiements" if nb is not None else ""
        last_str = f" · dernier: {str(last)[:10]}" if last else ""
        lines.append(f"{idx}. {name}: {amount_str}{nb_str}{last_str}")
    return "\n".join(lines)


def _is_balance_query(question: str) -> bool:
    q = question.lower()
    return bool(re.search(r'\bbalance\b|solde|encours', q))


def _format_balance_response(data: List[Dict[str, Any]]) -> str:
    if not data:
        return "Aucun solde trouvé."
    lines = [f"Solde client ({len(data)} clients avec encours ouvert) :"]
    for idx, row in enumerate(data[:20], 1):
        name = row.get('Customer Name') or row.get('Customer No_') or 'Inconnu'
        solde = row.get('Solde') or row.get('Balance')
        nb = row.get('Nb Ecritures')
        solde_str = _format_amount(solde) if solde is not None else 'N/A'
        nb_str = f" · {int(nb)} écritures" if nb is not None else ""
        lines.append(f"{idx}. {name}: {solde_str}{nb_str}")
    return "\n".join(lines)


def _is_stock_query(question: str) -> bool:
    q = question.lower()
    return bool(re.search(r'stock|inventaire|inventory|rupture|repture|rupure|roupture|entrepot|warehouse|niveau.?stock', q))


def _format_stock_response(data: List[Dict[str, Any]], question: str) -> str:
    if not data:
        return "Aucun article en stock trouvé."
    match = re.search(r'\b(\d+)\b', question)
    top_n = int(match.group(1)) if match else min(20, len(data))
    low_stock = bool(re.search(r'rupture|repture|rupure|faible|bas|bientot|bientôt|critique|low', question.lower()))
    header = f"Articles bientôt en rupture de stock ({min(top_n, len(data))} articles, stock le plus bas) :" if low_stock else f"Voici le stock des {min(top_n, len(data))} principaux articles :"
    lines = [header]
    for idx, row in enumerate(data[:top_n], 1):
        name = row.get('Produit') or row.get('Description') or row.get('Item No_') or 'Inconnu'
        loc = row.get('Location Code') or ''
        qty = row.get('Stock Total') or row.get('Quantity') or row.get('Remaining Quantity')
        qty_str = f"{float(qty):,.0f} unités" if qty is not None else 'N/A'
        loc_str = f" [{loc}]" if loc else ""
        lines.append(f"{idx}. {name}{loc_str}: {qty_str}")
    return "\n".join(lines)


def _is_purchases_query(question: str) -> bool:
    q = question.lower()
    return bool(re.search(r'\bachat|achats|purchase|purchases\b', q))


def _format_purchases_response(data: List[Dict[str, Any]], question: str) -> str:
    if not data:
        return "Aucun achat trouvé."
    match = re.search(r'\b(\d+)\b', question)
    top_n = int(match.group(1)) if match else min(10, len(data))
    lines = [f"Voici les {min(top_n, len(data))} principaux achats par fournisseur :"]
    for idx, row in enumerate(data[:top_n], 1):
        name = row.get('Fournisseur') or row.get('Vendor No_') or 'Inconnu'
        amount = row.get('Montant Achats') or row.get('Purchase Amount (Actual)')
        year = row.get('Annee') or row.get('Year') or ''
        amount_str = _format_amount(amount) if amount is not None else 'N/A'
        year_str = f" ({int(year)})".replace('(0)', '') if year else ''
        lines.append(f"{idx}. {name}: {amount_str}{year_str}")
    return "\n".join(lines)


def _is_disbursements_query(question: str) -> bool:
    q = question.lower()
    return bool(re.search(r'decaissement|décaissement|paiement.?fournisseur|vendor.?payment|cash.?out|sortie.?caisse', q))


def _format_disbursements_response(data: List[Dict[str, Any]], question: str) -> str:
    if not data:
        return "Aucun décaissement trouvé."
    match = re.search(r'\b(\d+)\b', question)
    top_n = int(match.group(1)) if match else min(10, len(data))
    lines = [f"Voici les {min(top_n, len(data))} principaux décaissements fournisseurs :"]
    for idx, row in enumerate(data[:top_n], 1):
        name = row.get('Fournisseur') or row.get('Vendor No_') or 'Inconnu'
        amount = row.get('Montant Decaissement') or row.get('Amount')
        nb = row.get('Nb Paiements')
        amount_str = _format_amount(amount) if amount is not None else 'N/A'
        nb_str = f" · {int(nb)} paiements" if nb is not None else ""
        lines.append(f"{idx}. {name}: {amount_str}{nb_str}")
    return "\n".join(lines)


def _is_expired_products_query(question: str) -> bool:
    q = question.lower()
    return bool(re.search(r'perime|périmé|expire|expiré|obsolete', q) and re.search(r'produit|article|item', q))


def _format_expired_products_response(data: List[Dict[str, Any]], question: str) -> str:
    if not data:
        return "Aucun produit trouvé avec ces critères."
    match = re.search(r'\b(\d+)\b', question)
    top_n = int(match.group(1)) if match else min(10, len(data))
    q_lower = question.lower()
    near_expiry = bool(re.search(r'bientot|bientôt|soon|prochainement|va expirer|va perimer', q_lower))
    if near_expiry:
        header = f"⚠️ Produits bientôt obsolètes (30-180 jours sans mouvement) — Top {min(top_n, len(data))} :"
    else:
        header = f"🗑️ Produits périmés/obsolètes (+365 jours sans mouvement) — Top {min(top_n, len(data))} :"
    lines = [header]
    for idx, row in enumerate(data[:top_n], 1):
        name = row.get('Produit') or row.get('Description') or row.get('Item No_') or 'Inconnu'
        stock = row.get('Stock Actuel')
        last_move = row.get('Dernier Mouvement')
        days = row.get('Jours Sans Mouvement')
        stock_str = f"{float(stock):,.0f} unités" if stock is not None else 'N/A'
        days_str = f" ({int(days)} jours sans mouvement)" if days is not None else ""
        lines.append(f"{idx}. {name}: {stock_str}{days_str}")
    return "\n".join(lines)


def _is_sales_detail_query(question: str) -> bool:
    q = question.lower()
    return bool(
        re.search(r'vente|ventes|fact.?sales|chiffre.?vente', q)
        and re.search(r'produit|article|item|top|detail|liste', q)
    )


def _format_sales_detail_response(data: List[Dict[str, Any]], question: str) -> str:
    if not data:
        return "Aucune vente trouvée."
    match = re.search(r'\b(\d+)\b', question)
    top_n = int(match.group(1)) if match else min(10, len(data))
    lines = [f"Voici les {min(top_n, len(data))} produits les plus vendus (Fact_Sales) :"]
    for idx, row in enumerate(data[:top_n], 1):
        name = row.get('Produit') or row.get('Description') or row.get('Item No_') or 'Inconnu'
        amount = row.get('Montant Ventes') or row.get('Sales Amount (Actual)')
        qty = row.get('Quantite Vendue')
        amount_str = _format_amount(amount) if amount is not None else 'N/A'
        qty_str = f" · {float(qty):,.0f} unités" if qty is not None else ""
        lines.append(f"{idx}. {name}: {amount_str}{qty_str}")
    return "\n".join(lines)


def _is_top_products_query(question: str) -> bool:
    """Detect top products / best-selling / most profitable products questions."""
    q = question.lower()
    return bool(
        re.search(r'(produit|product|article|item)', q)
        and re.search(r'(top|plus vendu|vendu|vente|best|populaire|rentable|profitable|profit|marge)', q)
    )


def _format_top_products_response(data: List[Dict[str, Any]], question: str) -> str:
    """Format response for top products query."""
    if not data:
        return "Aucun produit trouvé."

    match = re.search(r'\b(\d+)\b', question.lower())
    top_n = int(match.group(1)) if match else len(data)
    is_profit_query = bool(re.search(r'rentable|profitable|profit|marge', question.lower()))
    label = "les plus rentables" if is_profit_query else "les plus vendus"
    lines = [f"Voici les {min(top_n, len(data))} produits {label} :"]

    for idx, row in enumerate(data[:top_n], 1):
        desc = (row.get('Description') or row.get('description')
                or row.get('No_') or row.get('Item No_') or 'Inconnu')
        profit = row.get('Total Profit')
        sales = (row.get('Total Ventes') or row.get('Sales Amount (Actual)')
                 or row.get('Montant'))
        qty = row.get('Quantite Vendue') or row.get('Valued Quantity')

        if sales is None:
            for v in row.values():
                if isinstance(v, (int, float, Decimal)) and v > 0:
                    sales = v
                    break

        if is_profit_query and profit is not None:
            main_str = f"marge {_format_amount(profit)}"
            sales_str = f" · ventes {_format_amount(sales)}" if sales is not None else ""
        else:
            main_str = _format_amount(sales) if sales is not None else 'N/A'
            sales_str = ""
        qty_str = f" · {int(qty):,} unités" if qty is not None else ""
        lines.append(f"{idx}. {desc}: {main_str}{sales_str}{qty_str}")

    return "\n".join(lines)


def _is_overdue_query(question: str) -> bool:
    """Detect overdue/late payment questions."""
    q = question.lower()
    return bool(re.search(r'retard|overdue|impay|late|echeance|échéance|past.?due|en souffrance', q))


def _format_overdue_response(data: List[Dict[str, Any]]) -> str:
    """Format response for overdue customers query."""
    if not data:
        return "Aucun client en retard de paiement trouvé."

    lines = [f"Voici les {len(data)} clients avec des paiements en retard :"]
    for idx, row in enumerate(data[:20], 1):
        name = (row.get('Customer Name') or row.get('Name') or row.get('name')
                or row.get('Nom') or row.get('Customer No_') or 'Inconnu')
        amount = (row.get('Montant Restant') or row.get('Remaining Amount')
                  or row.get('Outstanding Amount') or row.get('Amount'))
        nb = row.get('Nb Ecritures') or row.get('Nb_Ecritures')
        due = row.get('Echeance La Plus Ancienne') or row.get('Due Date')

        amount_str = _format_amount(amount) if amount is not None else 'N/A'
        nb_str = f" · {int(nb)} écritures" if nb is not None else ""
        due_str = ""
        if due:
            try:
                from datetime import datetime, date
                if isinstance(due, (datetime, date)):
                    due_str = f" · échéance depuis {due.strftime('%d/%m/%Y')}"
                else:
                    due_str = f" · échéance depuis {str(due)[:10]}"
            except Exception:
                pass
        lines.append(f"{idx}. {name}: {amount_str}{nb_str}{due_str}")
    return "\n".join(lines)


def _is_top_customers_query(question: str) -> bool:
    """Detect if question is asking for top N customers (incl. fidele/loyal/meilleur)."""
    q = question.lower()
    # Explicit top N pattern
    if re.search(r'top\s*(\d+)?\s*(client|customer|vente|sale)', q):
        return True
    # Loyalty / best customers pattern
    if re.search(r'(fid[eè]le|loyal|meilleur|most loyal|high.?value).{0,40}(client|customer)', q):
        return True
    if re.search(r'(client|customer).{0,40}(fid[eè]le|loyal|meilleur|most loyal)', q):
        return True
    return False


def _is_year_comparison_query(question: str) -> bool:
    """Detect year-over-year comparison questions."""
    q = question.lower()
    return bool(re.search(r'(vs|versus|compar|evolution|progression)', q)
                and re.search(r'(20\d{2})', q))


def _format_year_comparison_response(data: List[Dict[str, Any]]) -> str:
    """Format year-over-year CA comparison."""
    if not data:
        return "Aucune donnée trouvée."

    lines = []
    prev_amount = None
    prev_year = None

    valid_rows = [r for r in data if isinstance(r, dict)]
    if not valid_rows:
        return str(data[0]) if data else "Aucune donnée trouvée."

    for row in sorted(valid_rows, key=lambda r: str(r.get('Year') or r.get('year') or '')):
        year = row.get('Year') or row.get('year') or row.get('Annee') or row.get('Date')
        amount = None
        for col in ['CA Total', "Chiffre d'affaires CA", 'Total Amount', 'Total', 'Montant', 'Revenue', 'Amount']:
            if row.get(col) is not None:
                amount = row[col]
                break
        if amount is None:
            skip_keys = {'Year', 'year', 'Annee', 'annee', 'Month', 'month'}
            for k, v in row.items():
                if k in skip_keys:
                    continue
                if isinstance(v, (int, float)) and v != 0:
                    amount = v
                    break

        year_str = str(year) if year is not None else 'N/A'
        amount_str = _format_amount(amount) if amount is not None else 'N/A'

        if prev_amount is not None and amount is not None and prev_amount != 0:
            try:
                delta = ((float(amount) - float(prev_amount)) / abs(float(prev_amount))) * 100
                sign = '+' if delta >= 0 else ''
                evol = f" ({sign}{delta:.1f}% vs {prev_year})"
            except Exception:
                evol = ""
        else:
            evol = ""

        lines.append(f"{year_str} : {amount_str}{evol}")
        prev_amount = amount
        prev_year = year_str

    return "Comparaison du chiffre d'affaires :\n" + "\n".join(lines)


def _is_monthly_yearly_query(question: str) -> bool:
    """Detect if question is asking for monthly/yearly breakdown."""
    normalized = question.lower()
    # Check for patterns indicating monthly/yearly breakdown
    return bool(re.search(r'(mois|month|par mois|par\s*an|par\s*annee|annual|yearly|by\s*year|dernier|derniers|12\s*mois)', normalized))


def _format_top_customers_response(data: List[Dict[str, Any]], question: str) -> str:
    """Format response for TOP N customers queries."""
    if not data or len(data) == 0:
        return "Aucun client trouvé."
    
    # Extract number from question (top 5, 5 clients, les 10 premiers...)
    match = re.search(r'\b(\d+)\b', question.lower())
    top_n = int(match.group(1)) if match else len(data)
    
    # Choose appropriate label
    q_lower = question.lower()
    if re.search(r'fid[eè]le|loyal|meilleur', q_lower):
        label = f"les {min(top_n, len(data))} clients les plus fidèles"
    else:
        label = f"les {min(top_n, len(data))} meilleurs clients"
    lines = [f"Voici {label}:"]
    
    for idx, row in enumerate(data[:top_n], 1):
        # Try to get customer name
        name = (row.get('Name') or row.get('name') or row.get('Nom')
                or row.get('Customer Name') or row.get('customer_name') or 'Unknown')
        # Try to get amount — cover all column names from templates
        amount = (row.get('Total Amount') or row.get('Total Sales Amount')
                  or row.get('Total_Sales_Amount') or row.get('total_amount')
                  or row.get('Montant') or row.get('Revenue') or row.get('Sales'))
        # Generic fallback: first numeric value in row
        if amount is None:
            for v in row.values():
                if isinstance(v, (int, float, Decimal)) and v != 0:
                    amount = v
                    break
        if amount is None:
            amount = 'N/A'
        
        amount_formatted = _format_amount(amount) if amount != 'N/A' else 'N/A'
        nb_tx = row.get('Nb Transactions') or row.get('nb_transactions') or row.get('Transaction Count')
        tx_str = f" · {int(nb_tx)} transactions" if nb_tx is not None else ""
        lines.append(f"{idx}. {name}: {amount_formatted}{tx_str}")
    
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
        for col in ['CA Total', 'Total Amount', 'Total_Amount', 'Total', "Chiffre d'affaires CA", 'Montant', 'Revenue', 'Sales']:
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
        
        amount_formatted = _format_amount(amount) if amount not in (None, 'N/A') else 'N/A'
        
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
                return label_key, f"{_format_amount(label_value)} in {year_str}"

    if isinstance(label_value, (int, float)) and label_value < 0:
        return label_key, f"{_format_amount(label_value)}"

    if isinstance(label_value, (int, float)):
        return label_key, _format_amount(label_value)

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
