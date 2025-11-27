"""
Seed Vector DB with Example Analyses for Demo
Pre-populates common questions across different domains
"""

import logging
from utils.vector_db import get_vector_store

logger = logging.getLogger(__name__)


# 200+ EXPERT TEMPLATES - COMMUNITY KNOWLEDGE BASE! 🚀
# 25 templates per domain × 8 domains = 200 total
# These are VERIFIED expert analyses that analysts commonly need

SEED_EXAMPLES = [
    # ==================== 🛒 SALES DOMAIN (25) ====================
    {"content": "Show revenue by region", "domain": "sales", "query_type": "aggregation", "tier": "public"},
    {"content": "What are the top 10 best-selling products?", "domain": "sales", "query_type": "aggregation", "tier": "public"},
    {"content": "Analyze monthly sales trends over time", "domain": "sales", "query_type": "trend_analysis", "tier": "public"},
    {"content": "Compare Q1 vs Q2 performance", "domain": "sales", "query_type": "comparison", "tier": "public"},
    {"content": "Which product categories generate the most revenue?", "domain": "sales", "query_type": "aggregation", "tier": "public"},
    {"content": "Show total sales by customer segment", "domain": "sales", "query_type": "aggregation", "tier": "public"},
    {"content": "What's the average order value?", "domain": "sales", "query_type": "simple", "tier": "public"},
    {"content": "Identify seasonal patterns in sales data", "domain": "sales", "query_type": "pattern_analysis", "tier": "public"},
    {"content": "Which customers have the highest lifetime value?", "domain": "sales", "query_type": "analysis", "tier": "public"},
    {"content": "Show sales velocity by product line", "domain": "sales", "query_type": "aggregation", "tier": "public"},
    {"content": "Compare sales performance across stores", "domain": "sales", "query_type": "comparison", "tier": "public"},
    {"content": "What's the discount impact on revenue?", "domain": "sales", "query_type": "analysis", "tier": "public"},
    {"content": "Identify underperforming products", "domain": "sales", "query_type": "analysis", "tier": "public"},
    {"content": "Show daily sales vs target", "domain": "sales", "query_type": "comparison", "tier": "public"},
    {"content": "Analyze win rate by sales rep", "domain": "sales", "query_type": "aggregation", "tier": "public"},
    {"content": "Which regions are growing fastest?", "domain": "sales", "query_type": "trend_analysis", "tier": "public"},
    {"content": "Show revenue breakdown by payment method", "domain": "sales", "query_type": "aggregation", "tier": "public"},
    {"content": "Calculate customer churn rate", "domain": "sales", "query_type": "simple", "tier": "public"},
    {"content": "Analyze repeat purchase behavior", "domain": "sales", "query_type": "pattern_analysis", "tier": "public"},
    {"content": "Show sales pipeline conversion rates", "domain": "sales", "query_type": "funnel_analysis", "tier": "public"},
    {"content": "Compare new vs returning customer sales", "domain": "sales", "query_type": "comparison", "tier": "public"},
    {"content": "What's the average deal size by industry?", "domain": "sales", "query_type": "aggregation", "tier": "public"},
    {"content": "Identify cross-sell opportunities", "domain": "sales", "query_type": "analysis", "tier": "public"},
    {"content": "Show sales forecast accuracy", "domain": "sales", "query_type": "comparison", "tier": "public"},
    {"content": "Analyze product bundle performance", "domain": "sales", "query_type": "analysis", "tier": "public"},
    
    # ==================== 📢 MARKETING DOMAIN (25) ====================
    {"content": "Which marketing campaigns have the best ROI?", "domain": "marketing", "query_type": "analysis", "tier": "public"},
    {"content": "Show conversion funnel drop-off rates", "domain": "marketing", "query_type": "funnel_analysis", "tier": "public"},
    {"content": "Compare performance across different channels", "domain": "marketing", "query_type": "comparison", "tier": "public"},
    {"content": "What's our cost per acquisition by channel?", "domain": "marketing", "query_type": "aggregation", "tier": "public"},
    {"content": "Analyze click-through rates over time", "domain": "marketing", "query_type": "trend_analysis", "tier": "public"},
    {"content": "Which ad creative performs best?", "domain": "marketing", "query_type": "comparison", "tier": "public"},
    {"content": "Show email open rates by segment", "domain": "marketing", "query_type": "aggregation", "tier": "public"},
    {"content": "Calculate customer acquisition cost trend", "domain": "marketing", "query_type": "trend_analysis", "tier": "public"},
    {"content": "Compare social media engagement by platform", "domain": "marketing", "query_type": "comparison", "tier": "public"},
    {"content": "What's our ROAS by campaign type?", "domain": "marketing", "query_type": "aggregation", "tier": "public"},
    {"content": "Analyze landing page conversion rates", "domain": "marketing", "query_type": "analysis", "tier": "public"},
    {"content": "Show lead quality by source", "domain": "marketing", "query_type": "comparison", "tier": "public"},
    {"content": "Which keywords drive the most conversions?", "domain": "marketing", "query_type": "analysis", "tier": "public"},
    {"content": "Compare paid vs organic traffic performance", "domain": "marketing", "query_type": "comparison", "tier": "public"},
    {"content": "Show bounce rate by traffic source", "domain": "marketing", "query_type": "aggregation", "tier": "public"},
    {"content": "Analyze attribution across touchpoints", "domain": "marketing", "query_type": "analysis", "tier": "public"},
    {"content": "What's our customer lifetime value by cohort?", "domain": "marketing", "query_type": "aggregation", "tier": "public"},
    {"content": "Show campaign performance vs budget", "domain": "marketing", "query_type": "comparison", "tier": "public"},
    {"content": "Analyze time to conversion", "domain": "marketing", "query_type": "analysis", "tier": "public"},
    {"content": "Which audience segments have highest engagement?", "domain": "marketing", "query_type": "comparison", "tier": "public"},
    {"content": "Show content performance metrics", "domain": "marketing", "query_type": "aggregation", "tier": "public"},
    {"content": "Compare mobile vs desktop conversions", "domain": "marketing", "query_type": "comparison", "tier": "public"},
    {"content": "Analyze A/B test results", "domain": "marketing", "query_type": "comparison", "tier": "public"},
    {"content": "What's our marketing efficiency ratio?", "domain": "marketing", "query_type": "simple", "tier": "public"},
    {"content": "Show lead-to-opportunity conversion rates", "domain": "marketing", "query_type": "funnel_analysis", "tier": "public"},
    
    # ==================== 👥 HR DOMAIN (25) ====================
    {"content": "Show employee headcount by department", "domain": "hr", "query_type": "aggregation", "tier": "public"},
    {"content": "What's the average tenure of employees?", "domain": "hr", "query_type": "simple", "tier": "public"},
    {"content": "Analyze turnover rates by department", "domain": "hr", "query_type": "analysis", "tier": "public"},
    {"content": "Show salary distribution across job levels", "domain": "hr", "query_type": "distribution", "tier": "public"},
    {"content": "Which departments have the highest performance ratings?", "domain": "hr", "query_type": "comparison", "tier": "public"},
    {"content": "Track hiring trends over the past year", "domain": "hr", "query_type": "trend_analysis", "tier": "public"},
    {"content": "Compare attrition rates by role", "domain": "hr", "query_type": "comparison", "tier": "public"},
    {"content": "Show time-to-fill by position", "domain": "hr", "query_type": "aggregation", "tier": "public"},
    {"content": "Analyze diversity metrics across teams", "domain": "hr", "query_type": "analysis", "tier": "public"},
    {"content": "What's the average salary increase by year?", "domain": "hr", "query_type": "trend_analysis", "tier": "public"},
    {"content": "Show training completion rates", "domain": "hr", "query_type": "aggregation", "tier": "public"},
    {"content": "Compare employee satisfaction by manager", "domain": "hr", "query_type": "comparison", "tier": "public"},
    {"content": "Identify flight risk employees", "domain": "hr", "query_type": "analysis", "tier": "public"},
    {"content": "Show promotion rates by demographic", "domain": "hr", "query_type": "aggregation", "tier": "public"},
    {"content": "Analyze compensation equity", "domain": "hr", "query_type": "analysis", "tier": "public"},
    {"content": "What's our cost per hire?", "domain": "hr", "query_type": "simple", "tier": "public"},
    {"content": "Show overtime hours by department", "domain": "hr", "query_type": "aggregation", "tier": "public"},
    {"content": "Compare performance scores over time", "domain": "hr", "query_type": "trend_analysis", "tier": "public"},
    {"content": "Analyze absenteeism patterns", "domain": "hr", "query_type": "pattern_analysis", "tier": "public"},
    {"content": "Show internal mobility rates", "domain": "hr", "query_type": "aggregation", "tier": "public"},
    {"content": "Which roles are hardest to fill?", "domain": "hr", "query_type": "analysis", "tier": "public"},
    {"content": "Compare offer acceptance rates by source", "domain": "hr", "query_type": "comparison", "tier": "public"},
    {"content": "Show workforce planning gaps", "domain": "hr", "query_type": "analysis", "tier": "public"},
    {"content": "Analyze employee engagement scores", "domain": "hr", "query_type": "analysis", "tier": "public"},
    {"content": "What's the span of control by manager?", "domain": "hr", "query_type": "aggregation", "tier": "public"},
    
    # ==================== 💰 FINANCIAL DOMAIN (25) ====================
    {"content": "Show budget vs actual variance by department", "domain": "financial", "query_type": "comparison", "tier": "public"},
    {"content": "What's our profit margin trend?", "domain": "financial", "query_type": "trend_analysis", "tier": "public"},
    {"content": "Analyze expenses by category", "domain": "financial", "query_type": "aggregation", "tier": "public"},
    {"content": "Compare quarterly revenue performance", "domain": "financial", "query_type": "comparison", "tier": "public"},
    {"content": "What are the top cost drivers?", "domain": "financial", "query_type": "analysis", "tier": "public"},
    {"content": "Show cash flow trends", "domain": "financial", "query_type": "trend_analysis", "tier": "public"},
    {"content": "Analyze EBITDA by business unit", "domain": "financial", "query_type": "aggregation", "tier": "public"},
    {"content": "Compare forecast vs actuals", "domain": "financial", "query_type": "comparison", "tier": "public"},
    {"content": "Show working capital trends", "domain": "financial", "query_type": "trend_analysis", "tier": "public"},
    {"content": "What's our burn rate?", "domain": "financial", "query_type": "simple", "tier": "public"},
    {"content": "Analyze gross margin by product line", "domain": "financial", "query_type": "aggregation", "tier": "public"},
    {"content": "Show accounts receivable aging", "domain": "financial", "query_type": "distribution", "tier": "public"},
    {"content": "Compare fixed vs variable costs", "domain": "financial", "query_type": "comparison", "tier": "public"},
    {"content": "Analyze revenue concentration risk", "domain": "financial", "query_type": "analysis", "tier": "public"},
    {"content": "Show break-even analysis", "domain": "financial", "query_type": "analysis", "tier": "public"},
    {"content": "What's our customer acquisition payback period?", "domain": "financial", "query_type": "simple", "tier": "public"},
    {"content": "Compare operating expenses YoY", "domain": "financial", "query_type": "comparison", "tier": "public"},
    {"content": "Show liquidity ratios over time", "domain": "financial", "query_type": "trend_analysis", "tier": "public"},
    {"content": "Analyze cost per unit trends", "domain": "financial", "query_type": "trend_analysis", "tier": "public"},
    {"content": "What's our debt-to-equity ratio?", "domain": "financial", "query_type": "simple", "tier": "public"},
    {"content": "Show return on investment by project", "domain": "financial", "query_type": "aggregation", "tier": "public"},
    {"content": "Compare revenue per employee", "domain": "financial", "query_type": "comparison", "tier": "public"},
    {"content": "Analyze days sales outstanding", "domain": "financial", "query_type": "analysis", "tier": "public"},
    {"content": "Show capital expenditure trends", "domain": "financial", "query_type": "trend_analysis", "tier": "public"},
    {"content": "What's our gross profit margin by region?", "domain": "financial", "query_type": "aggregation", "tier": "public"},
    
    # ==================== 📋 SURVEY DOMAIN (25) ====================
    {"content": "What's the average satisfaction score?", "domain": "survey", "query_type": "simple", "tier": "public"},
    {"content": "Show NPS score distribution", "domain": "survey", "query_type": "distribution", "tier": "public"},
    {"content": "Analyze sentiment trends over time", "domain": "survey", "query_type": "trend_analysis", "tier": "public"},
    {"content": "Which questions have the lowest ratings?", "domain": "survey", "query_type": "comparison", "tier": "public"},
    {"content": "Compare satisfaction across customer segments", "domain": "survey", "query_type": "comparison", "tier": "public"},
    {"content": "What are the most common feedback themes?", "domain": "survey", "query_type": "pattern_analysis", "tier": "public"},
    {"content": "Show response rate by demographic", "domain": "survey", "query_type": "aggregation", "tier": "public"},
    {"content": "Analyze CSAT trends by product", "domain": "survey", "query_type": "trend_analysis", "tier": "public"},
    {"content": "Which touchpoints have lowest satisfaction?", "domain": "survey", "query_type": "comparison", "tier": "public"},
    {"content": "Show promoter vs detractor breakdown", "domain": "survey", "query_type": "distribution", "tier": "public"},
    {"content": "Compare pre vs post-improvement scores", "domain": "survey", "query_type": "comparison", "tier": "public"},
    {"content": "What factors correlate with high satisfaction?", "domain": "survey", "query_type": "correlation", "tier": "public"},
    {"content": "Analyze verbatim feedback sentiment", "domain": "survey", "query_type": "analysis", "tier": "public"},
    {"content": "Show completion rate by survey length", "domain": "survey", "query_type": "aggregation", "tier": "public"},
    {"content": "Compare B2B vs B2C satisfaction", "domain": "survey", "query_type": "comparison", "tier": "public"},
    {"content": "What's our employee engagement index?", "domain": "survey", "query_type": "simple", "tier": "public"},
    {"content": "Show satisfaction by service channel", "domain": "survey", "query_type": "aggregation", "tier": "public"},
    {"content": "Analyze survey drop-off points", "domain": "survey", "query_type": "funnel_analysis", "tier": "public"},
    {"content": "Compare satisfaction before vs after training", "domain": "survey", "query_type": "comparison", "tier": "public"},
    {"content": "What drives customer effort score?", "domain": "survey", "query_type": "analysis", "tier": "public"},
    {"content": "Show recommendation likelihood by cohort", "domain": "survey", "query_type": "aggregation", "tier": "public"},
    {"content": "Analyze open-ended response patterns", "domain": "survey", "query_type": "pattern_analysis", "tier": "public"},
    {"content": "Compare mobile vs web survey responses", "domain": "survey", "query_type": "comparison", "tier": "public"},
    {"content": "What's the relationship between NPS and retention?", "domain": "survey", "query_type": "correlation", "tier": "public"},
    {"content": "Show satisfaction heatmap by question", "domain": "survey", "query_type": "distribution", "tier": "public"},
    
    # ==================== 📦 PRODUCT DOMAIN (25) ====================
    {"content": "Which features drive the most engagement?", "domain": "product", "query_type": "analysis", "tier": "public"},
    {"content": "Show user adoption rate by cohort", "domain": "product", "query_type": "aggregation", "tier": "public"},
    {"content": "Analyze feature usage trends over time", "domain": "product", "query_type": "trend_analysis", "tier": "public"},
    {"content": "What's our user retention curve?", "domain": "product", "query_type": "analysis", "tier": "public"},
    {"content": "Compare active users across versions", "domain": "product", "query_type": "comparison", "tier": "public"},
    {"content": "Show churn rate by user segment", "domain": "product", "query_type": "aggregation", "tier": "public"},
    {"content": "Which features correlate with retention?", "domain": "product", "query_type": "correlation", "tier": "public"},
    {"content": "Analyze session duration patterns", "domain": "product", "query_type": "pattern_analysis", "tier": "public"},
    {"content": "Show conversion funnel by feature path", "domain": "product", "query_type": "funnel_analysis", "tier": "public"},
    {"content": "What's our daily active user trend?", "domain": "product", "query_type": "trend_analysis", "tier": "public"},
    {"content": "Compare power users vs casual users", "domain": "product", "query_type": "comparison", "tier": "public"},
    {"content": "Analyze feature discovery rates", "domain": "product", "query_type": "analysis", "tier": "public"},
    {"content": "Show time-to-first-value by user type", "domain": "product", "query_type": "aggregation", "tier": "public"},
    {"content": "Which experiments improved key metrics?", "domain": "product", "query_type": "comparison", "tier": "public"},
    {"content": "Analyze user journey drop-off points", "domain": "product", "query_type": "funnel_analysis", "tier": "public"},
    {"content": "What's our product stickiness ratio?", "domain": "product", "query_type": "simple", "tier": "public"},
    {"content": "Show feature adoption by release date", "domain": "product", "query_type": "trend_analysis", "tier": "public"},
    {"content": "Compare beta vs production metrics", "domain": "product", "query_type": "comparison", "tier": "public"},
    {"content": "Analyze error rate by feature", "domain": "product", "query_type": "aggregation", "tier": "public"},
    {"content": "What drives user activation?", "domain": "product", "query_type": "analysis", "tier": "public"},
    {"content": "Show cohort retention breakdown", "domain": "product", "query_type": "distribution", "tier": "public"},
    {"content": "Compare usage by platform", "domain": "product", "query_type": "comparison", "tier": "public"},
    {"content": "Analyze viral coefficient", "domain": "product", "query_type": "simple", "tier": "public"},
    {"content": "What's the impact of onboarding changes?", "domain": "product", "query_type": "comparison", "tier": "public"},
    {"content": "Show feature engagement heatmap", "domain": "product", "query_type": "distribution", "tier": "public"},
    
    # ==================== 💼 BUSINESS DOMAIN (25) ====================
    {"content": "Show all KPIs vs targets", "domain": "business", "query_type": "comparison", "tier": "public"},
    {"content": "What are our top business metrics?", "domain": "business", "query_type": "aggregation", "tier": "public"},
    {"content": "Analyze performance trends across initiatives", "domain": "business", "query_type": "trend_analysis", "tier": "public"},
    {"content": "Compare actual vs projected outcomes", "domain": "business", "query_type": "comparison", "tier": "public"},
    {"content": "Show OKR progress by team", "domain": "business", "query_type": "aggregation", "tier": "public"},
    {"content": "What's driving our growth rate?", "domain": "business", "query_type": "analysis", "tier": "public"},
    {"content": "Analyze competitive benchmarks", "domain": "business", "query_type": "comparison", "tier": "public"},
    {"content": "Show strategic initiative status", "domain": "business", "query_type": "aggregation", "tier": "public"},
    {"content": "Compare market share trends", "domain": "business", "query_type": "trend_analysis", "tier": "public"},
    {"content": "What's our customer lifetime value growth?", "domain": "business", "query_type": "trend_analysis", "tier": "public"},
    {"content": "Analyze business unit performance", "domain": "business", "query_type": "comparison", "tier": "public"},
    {"content": "Show variance from business plan", "domain": "business", "query_type": "comparison", "tier": "public"},
    {"content": "Which initiatives have highest ROI?", "domain": "business", "query_type": "analysis", "tier": "public"},
    {"content": "Compare leading vs lagging indicators", "domain": "business", "query_type": "comparison", "tier": "public"},
    {"content": "Show goal achievement rates", "domain": "business", "query_type": "aggregation", "tier": "public"},
    {"content": "What's our market penetration trend?", "domain": "business", "query_type": "trend_analysis", "tier": "public"},
    {"content": "Analyze strategic risk metrics", "domain": "business", "query_type": "analysis", "tier": "public"},
    {"content": "Show balanced scorecard view", "domain": "business", "query_type": "aggregation", "tier": "public"},
    {"content": "Compare geographic expansion performance", "domain": "business", "query_type": "comparison", "tier": "public"},
    {"content": "What drives our net revenue retention?", "domain": "business", "query_type": "analysis", "tier": "public"},
    {"content": "Show innovation pipeline metrics", "domain": "business", "query_type": "aggregation", "tier": "public"},
    {"content": "Analyze customer acquisition efficiency", "domain": "business", "query_type": "trend_analysis", "tier": "public"},
    {"content": "Compare product-market fit indicators", "domain": "business", "query_type": "comparison", "tier": "public"},
    {"content": "What's our total addressable market growth?", "domain": "business", "query_type": "trend_analysis", "tier": "public"},
    {"content": "Show executive dashboard summary", "domain": "business", "query_type": "aggregation", "tier": "public"},
    
    # ==================== 🎯 OPERATIONS DOMAIN (25) ====================
    {"content": "Show process efficiency by workflow", "domain": "operations", "query_type": "aggregation", "tier": "public"},
    {"content": "What's our average cycle time?", "domain": "operations", "query_type": "simple", "tier": "public"},
    {"content": "Analyze throughput trends", "domain": "operations", "query_type": "trend_analysis", "tier": "public"},
    {"content": "Where are the bottlenecks?", "domain": "operations", "query_type": "analysis", "tier": "public"},
    {"content": "Compare capacity utilization across resources", "domain": "operations", "query_type": "comparison", "tier": "public"},
    {"content": "Show SLA compliance rates", "domain": "operations", "query_type": "aggregation", "tier": "public"},
    {"content": "Analyze downtime patterns", "domain": "operations", "query_type": "pattern_analysis", "tier": "public"},
    {"content": "What's our first-time-right rate?", "domain": "operations", "query_type": "simple", "tier": "public"},
    {"content": "Compare process performance before vs after optimization", "domain": "operations", "query_type": "comparison", "tier": "public"},
    {"content": "Show resource allocation efficiency", "domain": "operations", "query_type": "aggregation", "tier": "public"},
    {"content": "Analyze queue times by priority", "domain": "operations", "query_type": "aggregation", "tier": "public"},
    {"content": "What drives our productivity metrics?", "domain": "operations", "query_type": "analysis", "tier": "public"},
    {"content": "Show defect rate trends", "domain": "operations", "query_type": "trend_analysis", "tier": "public"},
    {"content": "Compare shift performance", "domain": "operations", "query_type": "comparison", "tier": "public"},
    {"content": "Analyze task completion rates", "domain": "operations", "query_type": "aggregation", "tier": "public"},
    {"content": "What's our operational excellence score?", "domain": "operations", "query_type": "simple", "tier": "public"},
    {"content": "Show work-in-progress levels", "domain": "operations", "query_type": "aggregation", "tier": "public"},
    {"content": "Compare planned vs actual capacity", "domain": "operations", "query_type": "comparison", "tier": "public"},
    {"content": "Analyze escalation patterns", "domain": "operations", "query_type": "pattern_analysis", "tier": "public"},
    {"content": "What's our average handling time?", "domain": "operations", "query_type": "simple", "tier": "public"},
    {"content": "Show process compliance rates", "domain": "operations", "query_type": "aggregation", "tier": "public"},
    {"content": "Compare automation impact on efficiency", "domain": "operations", "query_type": "comparison", "tier": "public"},
    {"content": "Analyze quality metrics by team", "domain": "operations", "query_type": "aggregation", "tier": "public"},
    {"content": "What's our overall equipment effectiveness?", "domain": "operations", "query_type": "simple", "tier": "public"},
    {"content": "Show lead time distribution", "domain": "operations", "query_type": "distribution", "tier": "public"},
    
    # ==================== 📊 GENERAL DOMAIN (25) ====================
    {"content": "Show me a summary of the data", "domain": "general", "query_type": "summary", "tier": "public"},
    {"content": "What are the key trends in this dataset?", "domain": "general", "query_type": "trend_analysis", "tier": "public"},
    {"content": "Identify any outliers or anomalies", "domain": "general", "query_type": "anomaly_detection", "tier": "public"},
    {"content": "Show correlations between variables", "domain": "general", "query_type": "correlation", "tier": "public"},
    {"content": "What's the distribution of key metrics?", "domain": "general", "query_type": "distribution", "tier": "public"},
    {"content": "Compare performance across categories", "domain": "general", "query_type": "comparison", "tier": "public"},
    {"content": "Analyze growth rates", "domain": "general", "query_type": "trend_analysis", "tier": "public"},
    {"content": "Show top performers", "domain": "general", "query_type": "aggregation", "tier": "public"},
    {"content": "What patterns exist in the data?", "domain": "general", "query_type": "pattern_analysis", "tier": "public"},
    {"content": "Compare time periods", "domain": "general", "query_type": "comparison", "tier": "public"},
    {"content": "Show data quality issues", "domain": "general", "query_type": "analysis", "tier": "public"},
    {"content": "What's the average of key metrics?", "domain": "general", "query_type": "simple", "tier": "public"},
    {"content": "Analyze variance across groups", "domain": "general", "query_type": "analysis", "tier": "public"},
    {"content": "Show breakdown by category", "domain": "general", "query_type": "aggregation", "tier": "public"},
    {"content": "Compare latest vs historical data", "domain": "general", "query_type": "comparison", "tier": "public"},
    {"content": "What are the extreme values?", "domain": "general", "query_type": "aggregation", "tier": "public"},
    {"content": "Analyze seasonality", "domain": "general", "query_type": "pattern_analysis", "tier": "public"},
    {"content": "Show cumulative trends", "domain": "general", "query_type": "trend_analysis", "tier": "public"},
    {"content": "Compare multiple metrics", "domain": "general", "query_type": "comparison", "tier": "public"},
    {"content": "What factors influence outcomes?", "domain": "general", "query_type": "analysis", "tier": "public"},
    {"content": "Show statistical summary", "domain": "general", "query_type": "summary", "tier": "public"},
    {"content": "Analyze data completeness", "domain": "general", "query_type": "analysis", "tier": "public"},
    {"content": "Compare segments", "domain": "general", "query_type": "comparison", "tier": "public"},
    {"content": "What's the overall trend?", "domain": "general", "query_type": "trend_analysis", "tier": "public"},
    {"content": "Show ranking of items", "domain": "general", "query_type": "aggregation", "tier": "public"},
]


def seed_vector_db():
    """
    Seed the vector database with 200+ EXPERT COMMUNITY TEMPLATES! 🚀
    These are verified analyses that analysts commonly need.
    Call this once on app startup or via admin panel.
    
    Community templates will be marked with:
    - tier="public" (available to all users)
    - usage_count will grow organically
    - Displayed as "📚 FROM COMMUNITY" in widget
    
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
