"""
Domain Detection for Smart AI Optimization
Automatically detects what kind of data the user has uploaded.
"""

import pandas as pd
import logging

logger = logging.getLogger(__name__)


def detect_data_domain(df):
    """
    Auto-detect the domain/type of data based on column names and patterns.
    
    Returns one of: 'sales', 'marketing', 'hr', 'financial', 'survey', 'general'
    
    Args:
        df: pandas DataFrame to analyze
        
    Returns:
        dict with 'domain' (str), 'confidence' (float), 'detected_patterns' (list)
    """
    
    if df is None or df.empty:
        return {"domain": "general", "confidence": 0.0, "detected_patterns": []}
    
    # Normalize column names for matching
    columns = set(df.columns.str.lower().str.replace('_', '').str.replace(' ', ''))
    
    # Define domain patterns with weighted keywords - 8 DOMAINS!
    DOMAIN_PATTERNS = {
        "sales": [
            {"keywords": ['revenue', 'sales', 'orders', 'products', 'totalsale', 'orderid', 'invoice'], "weight": 3},
            {"keywords": ['price', 'quantity', 'discount', 'amount', 'payment', 'shipping'], "weight": 2},
            {"keywords": ['customer', 'date', 'region', 'category', 'item', 'store'], "weight": 1}
        ],
        "marketing": [
            {"keywords": ['campaign', 'impressions', 'clicks', 'conversions', 'leads', 'ctr', 'cpc'], "weight": 3},
            {"keywords": ['cost', 'roi', 'roas', 'spend', 'budget', 'adgroup'], "weight": 2},
            {"keywords": ['channel', 'source', 'medium', 'device', 'audience', 'landing'], "weight": 1}
        ],
        "hr": [
            {"keywords": ['employee', 'salary', 'department', 'hiredate', 'workforce', 'headcount'], "weight": 3},
            {"keywords": ['performance', 'rating', 'manager', 'position', 'title', 'level'], "weight": 2},
            {"keywords": ['tenure', 'turnover', 'promotion', 'team', 'office', 'location'], "weight": 1}
        ],
        "financial": [
            {"keywords": ['revenue', 'expense', 'profit', 'loss', 'ebitda', 'margin'], "weight": 3},
            {"keywords": ['budget', 'actual', 'variance', 'forecast', 'ytd', 'qtr'], "weight": 2},
            {"keywords": ['account', 'costcenter', 'glcode', 'ledger', 'journal', 'transaction'], "weight": 1}
        ],
        "survey": [
            {"keywords": ['rating', 'score', 'satisfaction', 'feedback', 'nps', 'response'], "weight": 3},
            {"keywords": ['question', 'answer', 'respondent', 'survey', 'poll', 'opinion'], "weight": 2},
            {"keywords": ['sentiment', 'comment', 'text', 'agree', 'disagree', 'likely'], "weight": 1}
        ],
        "product": [
            {"keywords": ['feature', 'userid', 'engagement', 'adoption', 'retention', 'churn', 'active'], "weight": 3},
            {"keywords": ['version', 'release', 'feedback', 'usage', 'session', 'event', 'funnel'], "weight": 2},
            {"keywords": ['cohort', 'segment', 'experiment', 'variant', 'abtest', 'metric'], "weight": 1}
        ],
        "business": [
            {"keywords": ['kpi', 'metric', 'target', 'actual', 'variance', 'goal', 'objective'], "weight": 3},
            {"keywords": ['performance', 'trend', 'forecast', 'projection', 'growth', 'decline'], "weight": 2},
            {"keywords": ['dashboard', 'report', 'analysis', 'insight', 'benchmark', 'scorecard'], "weight": 1}
        ],
        "operations": [
            {"keywords": ['process', 'efficiency', 'throughput', 'cycletime', 'bottleneck', 'capacity'], "weight": 3},
            {"keywords": ['utilization', 'productivity', 'downtime', 'uptime', 'sla', 'quality'], "weight": 2},
            {"keywords": ['workflow', 'task', 'status', 'priority', 'resource', 'allocation'], "weight": 1}
        ]
    }
    
    # Score each domain
    domain_scores = {}
    domain_matches = {}
    
    for domain, patterns in DOMAIN_PATTERNS.items():
        score = 0
        matched_keywords = []
        
        for pattern in patterns:
            # Check how many keywords from this pattern match
            pattern_keywords = set(pattern["keywords"])
            matches = columns & pattern_keywords
            
            if matches:
                score += len(matches) * pattern["weight"]
                matched_keywords.extend(matches)
        
        domain_scores[domain] = score
        domain_matches[domain] = matched_keywords
    
    # Find best matching domain
    best_domain = max(domain_scores, key=domain_scores.get)
    best_score = domain_scores[best_domain]
    
    # Calculate confidence (normalize to 0-1 range)
    # Confidence threshold: need at least score of 3 (one high-weight match)
    # Calculate max possible score for this domain
    max_possible_score = sum(p["weight"] * len(p["keywords"]) for p in DOMAIN_PATTERNS[best_domain])
    confidence = min(best_score / 10.0, 1.0) if best_score >= 3 else 0.0
    
    # If confidence is too low, return "general"
    if confidence < 0.3:
        logger.info(f"Low confidence ({confidence:.2f}) for domain detection, defaulting to 'general'")
        return {
            "domain": "general",
            "confidence": confidence,
            "detected_patterns": [],
            "all_scores": domain_scores
        }
    
    logger.info(f"Detected domain: {best_domain} (confidence: {confidence:.2f})")
    
    return {
        "domain": best_domain,
        "confidence": confidence,
        "detected_patterns": domain_matches[best_domain],
        "all_scores": domain_scores
    }


def get_schema_signature(df):
    """
    Create a schema signature for column matching.
    Returns a sorted, pipe-separated string of column names (normalized).
    
    Args:
        df: pandas DataFrame
        
    Returns:
        str: Schema signature like "category|date|price|product|quantity|region"
    """
    if df is None or df.empty:
        return ""
    
    # Normalize and sort column names
    normalized_cols = [col.lower().strip().replace(' ', '_') for col in df.columns]
    return "|".join(sorted(normalized_cols))


def calculate_schema_similarity(schema1, schema2):
    """
    Calculate similarity between two schema signatures.
    Uses Jaccard similarity (intersection over union).
    
    Args:
        schema1: First schema signature (pipe-separated columns)
        schema2: Second schema signature (pipe-separated columns)
        
    Returns:
        float: Similarity score between 0.0 and 1.0
    """
    if not schema1 or not schema2:
        return 0.0
    
    cols1 = set(schema1.split('|'))
    cols2 = set(schema2.split('|'))
    
    if not cols1 or not cols2:
        return 0.0
    
    intersection = len(cols1 & cols2)
    union = len(cols1 | cols2)
    
    return intersection / union if union > 0 else 0.0


def get_domain_emoji(domain):
    """Get emoji icon for domain type - 8 DOMAINS!"""
    emoji_map = {
        "sales": "🛒",
        "marketing": "📢",
        "hr": "👥",
        "financial": "💰",
        "survey": "📋",
        "product": "📦",
        "business": "💼",
        "operations": "🎯",
        "general": "📊"
    }
    return emoji_map.get(domain, "📊")


def get_domain_color(domain):
    """Get color for domain indicator - 8 DOMAINS!"""
    color_map = {
        "sales": "#4CAF50",      # Green
        "marketing": "#FF9800",  # Orange
        "hr": "#2196F3",         # Blue
        "financial": "#9C27B0",  # Purple
        "survey": "#FF5722",     # Red
        "product": "#00BCD4",    # Cyan
        "business": "#795548",   # Brown
        "operations": "#FFC107", # Amber
        "general": "#607D8B"     # Gray
    }
    return color_map.get(domain, "#607D8B")


if __name__ == "__main__":
    # Test the domain detector
    
    # Test sales data
    sales_df = pd.DataFrame({
        'order_id': [1, 2, 3],
        'product': ['A', 'B', 'C'],
        'quantity': [10, 20, 30],
        'price': [100, 200, 300],
        'revenue': [1000, 4000, 9000],
        'region': ['North', 'South', 'East']
    })
    
    result = detect_data_domain(sales_df)
    print(f"Sales Test: {result}")
    print(f"Schema: {get_schema_signature(sales_df)}")
    
    # Test marketing data
    marketing_df = pd.DataFrame({
        'campaign': ['A', 'B', 'C'],
        'impressions': [1000, 2000, 3000],
        'clicks': [100, 200, 300],
        'conversions': [10, 20, 30],
        'cost': [500, 1000, 1500],
        'channel': ['Google', 'Facebook', 'LinkedIn']
    })
    
    result = detect_data_domain(marketing_df)
    print(f"\nMarketing Test: {result}")
    
    # Test general data
    general_df = pd.DataFrame({
        'id': [1, 2, 3],
        'name': ['A', 'B', 'C'],
        'value': [100, 200, 300]
    })
    
    result = detect_data_domain(general_df)
    print(f"\nGeneral Test: {result}")
