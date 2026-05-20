"""Question intent and SQL relevance guards for BI responses."""

import re
import unicodedata
from dataclasses import dataclass
from typing import List, Optional, Tuple


def _normalize_text(text: str) -> str:
    """Normalize text for keyword matching."""
    normalized = unicodedata.normalize("NFD", (text or "").lower())
    normalized = "".join(character for character in normalized if unicodedata.category(character) != "Mn")
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


@dataclass(frozen=True)
class IntentRule:
    """Intent pattern with SQL relevance requirements."""

    name: str
    keywords: List[str]
    required_sql_tokens: List[str]


INTENT_RULES: List[IntentRule] = [
    IntentRule(
        name="overdue_customers",
        keywords=["client", "customer", "retard", "impaye", "impay", "overdue", "late", "past due"],
        required_sql_tokens=["D_CUSTOMERLEDGERENTRY", "DUE DATE", "OPEN", "DOCUMENT NO_"],
    ),
    IntentRule(
        name="top_customers",
        keywords=["top", "client", "customer", "best", "leading"],
        required_sql_tokens=["SUM", "GROUP BY", "ORDER BY", "D_CUSTOMER"],
    ),
    IntentRule(
        name="loyal_customers",
        keywords=["loyal", "fidele", "fidele", "best", "high value", "major", "key"],
        required_sql_tokens=["SUM", "GROUP BY", "ORDER BY", "D_CUSTOMER"],
    ),
    IntentRule(
        name="monthly_amounts",
        keywords=["montant", "mois", "monthly", "month", "par mois"],
        required_sql_tokens=["SUM", "GROUP BY", "ORDER BY", "AMOUNT"],
    ),
    IntentRule(
        name="by_customer",
        keywords=["par client", "by customer", "client", "customer"],
        required_sql_tokens=["SUM", "GROUP BY", "ORDER BY", "CUSTOMER"],
    ),
    IntentRule(
        name="year_comparison",
        keywords=["vs", "versus", "compare", "year", "annee", "année", "revenue"],
        required_sql_tokens=["YEAR(", "SUM", "GROUP BY"],
    ),
    IntentRule(
        name="ledger_entries",
        keywords=["ledger", "ecriture", "entries", "entry", "recent", "latest", "list", "show", "display"],
        required_sql_tokens=["ENTRY NO_", "POSTING DATE", "DOCUMENT NO_"],
    ),
    IntentRule(
        name="item_locations",
        keywords=["item", "article", "location", "warehouse", "store"],
        required_sql_tokens=["ITEM NO_", "LOCATION CODE", "COUNT(", "SUM("],
    ),
]


def detect_intent(question: str) -> Optional[IntentRule]:
    """Return the first matching intent rule, if any."""
    normalized = _normalize_text(question)
    if not normalized:
        return None

    for rule in INTENT_RULES:
        if all(keyword not in normalized for keyword in rule.keywords):
            continue

        # Keep the intent strict enough to avoid accidental matches.
        if rule.name == "overdue_customers":
            if not any(token in normalized for token in ["retard", "impaye", "impay", "overdue", "late", "past due"]):
                continue
        elif rule.name == "top_customers":
            if "top" not in normalized:
                continue
        elif rule.name == "monthly_amounts":
            if not any(token in normalized for token in ["montant", "mois", "monthly", "month"]):
                continue
        elif rule.name == "by_customer":
            if "client" not in normalized and "customer" not in normalized:
                continue
        elif rule.name == "year_comparison":
            if not re.search(r"\b(vs|versus|compare|year|ca|annee|année|revenue)\b", normalized):
                continue
        elif rule.name == "ledger_entries":
            if not any(token in normalized for token in ["ledger", "entry", "entries", "recent", "latest", "list", "show", "display", "ecriture"]):
                continue
        elif rule.name == "item_locations":
            if not any(token in normalized for token in ["item", "article", "location", "warehouse", "store"]):
                continue

        return rule

    return None


def sql_matches_intent(sql_query: str, question: str) -> Tuple[bool, str]:
    """Validate that a generated SQL query matches the detected intent."""
    intent = detect_intent(question)
    if intent is None:
        return True, ""

    sql_upper = _normalize_text(sql_query).upper()
    missing_tokens = [token for token in intent.required_sql_tokens if token not in sql_upper]

    if missing_tokens:
        return False, f"SQL does not match intent '{intent.name}'. Missing tokens: {', '.join(missing_tokens)}"

    return True, ""


def has_template_for_question(question: str) -> bool:
    """Return True when the question should be handled by deterministic templates."""
    return detect_intent(question) is not None
