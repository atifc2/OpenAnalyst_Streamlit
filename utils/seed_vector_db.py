"""
Seed Vector DB with Example Analyses for Demo
Pre-populates common questions across different domains
"""

import logging
from utils.vector_db import get_vector_store

logger = logging.getLogger(__name__)


# Example analyses for each domain
SEED_EXAMPLES = [
    # SALES DOMAIN
    {
        "content": "Show revenue by region",
        "domain": "sales",
        "query_type": "aggregation"
    },
    {
        "content": "What are the top 10 best-selling products?",
        "domain": "sales",
        "query_type": "aggregation"
    },
    {
        "content": "Analyze monthly sales trends over time",
        "domain": "sales",
        "query_type": "trend_analysis"
    },
    {
        "content": "Compare Q1 vs Q2 performance",
        "domain": "sales",
        "query_type": "comparison"
    },
    {
        "content": "Which product categories generate the most revenue?",
        "domain": "sales",
        "query_type": "aggregation"
    },
    {
        "content": "Show total sales by customer segment",
        "domain": "sales",
        "query_type": "aggregation"
    },
    {
        "content": "What's the average order value?",
        "domain": "sales",
        "query_type": "simple"
    },
    {
        "content": "Identify seasonal patterns in sales data",
        "domain": "sales",
        "query_type": "pattern_analysis"
    },
    
    # MARKETING DOMAIN
    {
        "content": "Which marketing campaigns have the best ROI?",
        "domain": "marketing",
        "query_type": "analysis"
    },
    {
        "content": "Show conversion funnel drop-off rates",
        "domain": "marketing",
        "query_type": "funnel_analysis"
    },
    {
        "content": "Compare performance across different channels",
        "domain": "marketing",
        "query_type": "comparison"
    },
    {
        "content": "What's our cost per acquisition by channel?",
        "domain": "marketing",
        "query_type": "aggregation"
    },
    {
        "content": "Analyze click-through rates over time",
        "domain": "marketing",
        "query_type": "trend_analysis"
    },
    {
        "content": "Which ad creative performs best?",
        "domain": "marketing",
        "query_type": "comparison"
    },
    
    # HR DOMAIN
    {
        "content": "Show employee headcount by department",
        "domain": "hr",
        "query_type": "aggregation"
    },
    {
        "content": "What's the average tenure of employees?",
        "domain": "hr",
        "query_type": "simple"
    },
    {
        "content": "Analyze turnover rates by department",
        "domain": "hr",
        "query_type": "analysis"
    },
    {
        "content": "Show salary distribution across job levels",
        "domain": "hr",
        "query_type": "distribution"
    },
    {
        "content": "Which departments have the highest performance ratings?",
        "domain": "hr",
        "query_type": "comparison"
    },
    {
        "content": "Track hiring trends over the past year",
        "domain": "hr",
        "query_type": "trend_analysis"
    },
    
    # FINANCIAL DOMAIN
    {
        "content": "Show budget vs actual variance by department",
        "domain": "financial",
        "query_type": "comparison"
    },
    {
        "content": "What's our profit margin trend?",
        "domain": "financial",
        "query_type": "trend_analysis"
    },
    {
        "content": "Analyze expenses by category",
        "domain": "financial",
        "query_type": "aggregation"
    },
    {
        "content": "Compare quarterly revenue performance",
        "domain": "financial",
        "query_type": "comparison"
    },
    {
        "content": "What are the top cost drivers?",
        "domain": "financial",
        "query_type": "analysis"
    },
    {
        "content": "Show cash flow trends",
        "domain": "financial",
        "query_type": "trend_analysis"
    },
    
    # SURVEY DOMAIN
    {
        "content": "What's the average satisfaction score?",
        "domain": "survey",
        "query_type": "simple"
    },
    {
        "content": "Show NPS score distribution",
        "domain": "survey",
        "query_type": "distribution"
    },
    {
        "content": "Analyze sentiment trends over time",
        "domain": "survey",
        "query_type": "trend_analysis"
    },
    {
        "content": "Which questions have the lowest ratings?",
        "domain": "survey",
        "query_type": "comparison"
    },
    {
        "content": "Compare satisfaction across customer segments",
        "domain": "survey",
        "query_type": "comparison"
    },
    {
        "content": "What are the most common feedback themes?",
        "domain": "survey",
        "query_type": "pattern_analysis"
    },
    
    # GENERAL (applies to any data)
    {
        "content": "Show me a summary of the data",
        "domain": "general",
        "query_type": "summary"
    },
    {
        "content": "What are the key trends in this dataset?",
        "domain": "general",
        "query_type": "trend_analysis"
    },
    {
        "content": "Identify any outliers or anomalies",
        "domain": "general",
        "query_type": "anomaly_detection"
    },
    {
        "content": "Show correlations between variables",
        "domain": "general",
        "query_type": "correlation"
    },
]


def seed_vector_db():
    """
    Seed the vector database with example analyses.
    Call this once on app startup or via admin panel.
    
    Returns:
        bool: True if seeding successful
    """
    try:
        vector_store = get_vector_store()
        
        if not vector_store or not vector_store.client:
            logger.warning("Vector store not available, skipping seeding")
            return False
        
        # Check if already seeded (look for any example_analysis type)
        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            results = vector_store.client.scroll(
                collection_name=vector_store.collection_name,
                scroll_filter=Filter(
                    must=[FieldCondition(key="type", match=MatchValue(value="example_analysis"))]
                ),
                limit=1
            )
            
            if results[0]:  # Already has seed data
                logger.info("Vector DB already seeded with examples")
                return True
                
        except Exception as e:
            logger.debug(f"Could not check for existing seeds: {e}")
        
        # Seed with examples
        success = vector_store.seed_example_analyses(SEED_EXAMPLES)
        
        if success:
            logger.info(f"Successfully seeded {len(SEED_EXAMPLES)} example analyses")
            return True
        else:
            logger.warning("Failed to seed vector DB")
            return False
            
    except Exception as e:
        logger.error(f"Error seeding vector DB: {e}")
        return False


if __name__ == "__main__":
    # Test seeding
    logging.basicConfig(level=logging.INFO)
    result = seed_vector_db()
    print(f"Seeding result: {result}")
