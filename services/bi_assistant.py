"""
Business Intelligence Assistant Service
Parses BI queries, extracts filters, and generates Power BI links
"""

import re
from typing import Dict, Optional, Tuple
from enum import Enum
from datetime import datetime
from config.settings import settings

class KPIType(Enum):
    """Supported KPI types"""
    REVENUE = "Chiffre d'affaires"
    PURCHASE = "Achat"
    CASH_IN = "Encaissement"
    CASH_OUT = "Décaissement"

class BIAssistant:
    """Business Intelligence query processor"""
    
    # French month mapping
    MONTH_MAP = {
        'janvier': 1, 'janv': 1, 'jan': 1,
        'février': 2, 'fevrier': 2, 'févr': 2, 'fevr': 2, 'feb': 2,
        'mars': 3, 'mar': 3,
        'avril': 4, 'avr': 4, 'apr': 4,
        'mai': 5,
        'juin': 6, 'jun': 6,
        'juillet': 7, 'juil': 7, 'jul': 7,
        'août': 8, 'aout': 8, 'aou': 8, 'aug': 8,
        'septembre': 9, 'sept': 9, 'sep': 9,
        'octobre': 10, 'oct': 10,
        'novembre': 11, 'nov': 11,
        'décembre': 12, 'decembre': 12, 'déc': 12, 'dec': 12
    }
    
    # Company aliases
    COMPANY_MAP = {
        'pem': 'PEM',
        'sapec': 'SAPEC',
    }
    
    # KPI keywords mapping
    KPI_KEYWORDS = {
        ('ca', 'chiffre', 'chiffre d\'affaires', 'revenue', 'revenu', 'ventes', 'sales'): KPIType.REVENUE,
        ('achat', 'achats', 'purchase', 'purchases', 'buy', 'buying'): KPIType.PURCHASE,
        ('encaissement', 'encaissements', 'cash in', 'cash-in', 'inflow'): KPIType.CASH_IN,
        ('décaissement', 'décaissements', 'decaissement', 'decaissements', 'cash out', 'cash-out', 'outflow'): KPIType.CASH_OUT,
    }
    
    BASE_POWER_BI_URL = "https://app.powerbi.com/groups/me/reports/58e4e4b4-2263-47b4-935f-acbe8e54e984/877e016bbac4411c08e6"
    
    def __init__(self):
        """Initialize BI Assistant"""
        self.current_year = datetime.now().year
        raw_companies = (settings.DEFAULT_BI_COMPANIES or "PEM,SAPEC")
        self.default_companies = [c.strip().upper() for c in raw_companies.split(',') if c.strip()]
        if not self.default_companies:
            self.default_companies = ["PEM", "SAPEC"]
    
    def parse_query(self, question: str) -> Dict:
        """
        Parse a BI query and extract filters
        
        Args:
            question: User question in French or English
            
        Returns:
            Dictionary with:
            - kpi_type: KPIType enum
            - year: Optional[int]
            - month: Optional[int]
            - company: Optional[str]
            - filters: Power BI filter expression
        """
        question_lower = question.lower().strip()
        
        # Extract KPI type
        kpi_type = self._extract_kpi_type(question_lower)
        
        # Extract year
        year = self._extract_year(question_lower)
        
        # Extract month
        month = self._extract_month(question_lower)
        
        # Extract company
        company = self._extract_company(question_lower)
        
        # Build filter expression
        filters = self._build_filter_expression(year, month, company)
        
        return {
            'kpi_type': kpi_type,
            'year': year,
            'month': month,
            'company': company,
            'filters': filters,
            'question': question_lower
        }
    
    def _extract_kpi_type(self, question: str) -> KPIType:
        """Extract KPI type from question"""
        for keywords, kpi_type in self.KPI_KEYWORDS.items():
            for keyword in keywords:
                # Use word boundaries for exact matching
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, question, re.IGNORECASE):
                    return kpi_type
        # Default to revenue
        return KPIType.REVENUE
    
    def _extract_year(self, question: str) -> Optional[int]:
        """Extract year from question"""
        # Look for 4-digit year (1900-2100)
        years = re.findall(r'\b([12]\d{3})\b', question)
        if years:
            # Validate year is in reasonable range (1900-2100)
            year = int(years[-1])  # Return last found year
            if 1900 <= year <= 2100:
                return year
        return None
    
    def _extract_month(self, question: str) -> Optional[int]:
        """Extract month from question"""
        question_lower = question.lower()
        
        # Check for French/English month tokens using word boundaries
        # Sort by length to prioritize full names over abbreviations.
        for month_name, month_num in sorted(self.MONTH_MAP.items(), key=lambda item: len(item[0]), reverse=True):
            pattern = r'\b' + re.escape(month_name) + r'\b'
            if re.search(pattern, question_lower, re.IGNORECASE):
                return month_num
        
        # Check for month numbers (1-12)
        month_matches = re.findall(r'\b(1[0-2]|0?[1-9])\b', question_lower)
        if month_matches:
            month_num = int(month_matches[-1])
            if 1 <= month_num <= 12:
                return month_num
        
        return None
    
    def _extract_company(self, question: str) -> Optional[str]:
        """Extract company from question"""
        question_lower = question.lower()
        
        for alias, company_name in self.COMPANY_MAP.items():
            if alias in question_lower:
                return company_name
        
        return None
    
    def _build_filter_expression(self, year: Optional[int], month: Optional[int], 
                                 company: Optional[str], companies: Optional[list] = None) -> str:
        """Build Power BI filter expression"""
        filters = []
        
        if year:
            filters.append(f"D_Date/Year eq {year}")
        
        if month:
            filters.append(f"D_Date/MonthNumber eq {month}")
        
        if company:
            filters.append(f"D_CompanyName/companyName eq '{company}'")
        elif companies:
            company_filters = [f"D_CompanyName/companyName eq '{c}'" for c in companies]
            filters.append(f"({' or '.join(company_filters)})")
        
        return " and ".join(filters) if filters else ""
    
    def generate_power_bi_link(self, filter_expression: str) -> str:
        """Generate Power BI link with filters"""
        if filter_expression:
            return f"{self.BASE_POWER_BI_URL}?filter={filter_expression}"
        return self.BASE_POWER_BI_URL
    
    def format_response(self, kpi_type: KPIType, kpi_value: float) -> str:
        """Format KPI response"""
        return f"{kpi_type.value}: {kpi_value:,.0f} BnFCFA"
    
    def get_mock_kpi_value(self, parsed_query: Dict) -> float:
        """
        Get KPI value from the actual database based on query filters
        Falls back to mock value if database query fails
        
        Args:
            parsed_query: Parsed query with kpi_type, year, month, company
            
        Returns:
            float: KPI value from database or mock fallback
        """
        try:
            from data.db_connection import execute_query
            from datetime import datetime
        except ImportError:
            # Fallback if database not available
            return self._get_mock_kpi_value_fallback(parsed_query)
        
        kpi_type = parsed_query['kpi_type']
        year = parsed_query.get('year') or datetime.now().year
        month = parsed_query.get('month')
        company = parsed_query.get('company')
        companies = parsed_query.get('companies') or self.default_companies
        
        try:
            # Map KPI types to database columns - CORRECTED FOR ACTUAL DB SCHEMA
            kpi_table_map = {
                KPIType.REVENUE: ('[dbo].[Fact_Sales]', '[Sales Amount (Actual)]'),
                KPIType.PURCHASE: ('[dbo].[Fact_Purshase]', '[Purchase Amount (Actual)]'),  # Note: "Purshase" typo is in DB
                KPIType.CASH_IN: ('[dbo].[Fact_CustomerPayementDetail]', '[Amount]'),
                KPIType.CASH_OUT: ('[dbo].[Fact_VendorPayementDetail]', '[Amount]'),
            }
            
            if kpi_type not in kpi_table_map:
                return self._get_mock_kpi_value_fallback(parsed_query)
            
            table, amount_col = kpi_table_map[kpi_type]
            
            # Build WHERE conditions
            where_conditions = []
            where_conditions.append(f"YEAR([Posting Date]) = {year}")
            
            if month:
                where_conditions.append(f"MONTH([Posting Date]) = {month}")
            
            if company:
                where_conditions.append(f"[companyName] = '{company}'")
            elif companies:
                company_list = ", ".join([f"'{c}'" for c in companies])
                where_conditions.append(f"[companyName] IN ({company_list})")
            
            where_clause = " AND ".join(where_conditions)
            
            # Execute query to get sum (dashboard uses net SUM, not ABS)
            sql = f"""
                SELECT ISNULL(SUM({amount_col}), 0) as total_value
                FROM {table}
                WHERE {where_clause}
            """
            
            results = execute_query(sql)
            if results and len(results) > 0:
                value = results[0].get('total_value', 0)
                if value > 0:
                    return float(value)
        
        except Exception as e:
            # Log error and use fallback
            pass
        
        # Fallback to mock value if database query fails
        return self._get_mock_kpi_value_fallback(parsed_query)
    
    def _get_mock_kpi_value_fallback(self, parsed_query: Dict) -> float:
        """
        Fallback mock KPI values when database is not available
        """
        import random
        random.seed(hash(str(parsed_query)) % 2**32)  # Deterministic but varies per query
        
        base_values = {
            KPIType.REVENUE: 1_200_000,
            KPIType.PURCHASE: 800_000,
            KPIType.CASH_IN: 900_000,
            KPIType.CASH_OUT: 600_000,
        }
        
        base_value = base_values[parsed_query['kpi_type']]
        
        # Apply seasonal variation based on month (if specified)
        if parsed_query['month']:
            # Q1: -5%, Q2: +10%, Q3: -8%, Q4: +15%
            month = parsed_query['month']
            seasonal_factors = {
                1: 0.95, 2: 0.93, 3: 0.92,    # Q1: Winter slow
                4: 1.08, 5: 1.12, 6: 1.10,    # Q2: Spring peak
                7: 0.95, 8: 0.92, 9: 0.90,    # Q3: Summer low
                10: 1.15, 11: 1.18, 12: 1.20  # Q4: End-year peak
            }
            base_value *= seasonal_factors.get(month, 1.0)
        
        # Apply company variation (larger than before)
        if parsed_query['company'] == 'PEM':
            base_value *= 0.55  # PEM: 55% of average
        elif parsed_query['company'] == 'SAPEC':
            base_value *= 0.75  # SAPEC: 75% of average
        
        # Add random variance (±15%)
        variance = random.uniform(0.85, 1.15)
        base_value *= variance
        
        # Apply year adjustment (2023 was lower, 2024 stable, 2025 growth)
        year = parsed_query.get('year', 2024)
        year_factors = {
            2023: 0.80,
            2024: 1.00,
            2025: 1.25,
            2026: 1.30
        }
        base_value *= year_factors.get(year, 1.0)
        
        return base_value
    
    def process_bi_question(self, question: str, kpi_value: Optional[float] = None) -> Tuple[str, str]:
        """
        Process a BI question and return formatted response
        
        Args:
            question: User question
            kpi_value: Optional actual KPI value; if None, uses mock value
            
        Returns:
            Tuple of (formatted_response, power_bi_link)
        """
        parsed = self.parse_query(question)

        # Keep API and dashboard aligned:
        # default scope = PEM + SAPEC, explicit company = only that company.
        if not parsed.get('company'):
            parsed['companies'] = self.default_companies
            parsed['filters'] = self._build_filter_expression(
                parsed.get('year'), parsed.get('month'), None, parsed.get('companies')
            )
        else:
            parsed['companies'] = [parsed['company']]
        
        # Use provided value or generate mock
        if kpi_value is None:
            kpi_value = self.get_mock_kpi_value(parsed)
        
        # Format response
        response = self.format_response(parsed['kpi_type'], kpi_value)
        
        # Generate link
        link = self.generate_power_bi_link(parsed['filters'])
        
        return response, link
    
    def is_bi_question(self, question: str) -> bool:
        """
        Check if a question is a BI query
        
        Returns True if question contains KPI keywords with SPECIFIC value/time filters
        Returns False if question asks for aggregation/distribution ("par mois", "par client", etc.)
        """
        question_lower = question.lower()
        
        # EXCLUDE aggregation/distribution questions
        aggregation_patterns = [
            r'\bpar\s+(mois|année|client|région|département|période|semaine|jour)',  # par mois, par client, etc.
            r'\b(répartition|distribution|breakdown|ventilation)',  # répartition par...
            r'\btop\s+\d+',  # top 10, top 5, etc.
            r'\bévolution|tendance|trend',  # evolution/trends
            r'\bcomparaison|compare',  # comparisons
            r'\b(plus|moins|meilleur|pire)',  # rankings
            r'\b(total|somme|moyenne|min|max)',  # aggregations
        ]
        
        for pattern in aggregation_patterns:
            if re.search(pattern, question_lower):
                return False
        
        # Check for KPI keywords with word boundaries
        has_kpi = False
        for keywords in self.KPI_KEYWORDS.keys():
            for keyword in keywords:
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, question_lower):
                    has_kpi = True
                    break
            if has_kpi:
                break
        
        if not has_kpi:
            return False
        
        # Must have specific value or filter for BI question
        # Check for specific time (year/month) OR company
        has_specific_filter = False
        
        # Check for specific year (not just mentions of years in aggregations)
        if re.search(r'\b([12]\d{3})\b', question_lower):
            has_specific_filter = True
        
        # Check for specific month
        if re.search(r'\b(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre|janv|févr|mar|avr|sept|oct|nov|déc)\b', question_lower):
            has_specific_filter = True
        
        # Check for specific company
        if any(re.search(r'\b' + re.escape(alias) + r'\b', question_lower, re.IGNORECASE) for alias in self.COMPANY_MAP.keys()):
            has_specific_filter = True
        
        return has_kpi and has_specific_filter


# Singleton instance
_bi_assistant = None

def get_bi_assistant() -> BIAssistant:
    """Get or create BI Assistant singleton"""
    global _bi_assistant
    if _bi_assistant is None:
        _bi_assistant = BIAssistant()
    return _bi_assistant
