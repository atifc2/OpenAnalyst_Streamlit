"""
Auto-Insights Engine - Generate Instant Key Insights on Data Load
Automatically analyzes data and surfaces key findings.

FEATURES:
- Domain-specific insight templates
- Statistical anomaly detection
- Key metric highlighting
- Trend identification
- Data quality alerts

This provides VALUE IMMEDIATELY when user uploads data!
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


# Domain-specific insight generators
DOMAIN_INSIGHT_TEMPLATES = {
    "sales": [
        {"name": "total_revenue", "metric": "revenue", "operation": "sum", "format": "currency"},
        {"name": "avg_order_value", "metric": "revenue", "operation": "mean", "format": "currency"},
        {"name": "top_product", "metric": "product", "operation": "mode", "format": "text"},
        {"name": "top_region", "metric": "region", "group_by": "region", "agg": "revenue", "operation": "max", "format": "text"},
        {"name": "order_count", "metric": "any", "operation": "count", "format": "number"},
    ],
    "marketing": [
        {"name": "total_spend", "metric": "cost", "operation": "sum", "format": "currency"},
        {"name": "total_conversions", "metric": "conversions", "operation": "sum", "format": "number"},
        {"name": "avg_cpa", "metric": ["cost", "conversions"], "operation": "ratio", "format": "currency"},
        {"name": "best_channel", "metric": "channel", "group_by": "channel", "agg": "conversions", "operation": "max", "format": "text"},
        {"name": "avg_ctr", "metric": ["clicks", "impressions"], "operation": "ratio_pct", "format": "percentage"},
    ],
    "hr": [
        {"name": "total_employees", "metric": "employee", "operation": "count_unique", "format": "number"},
        {"name": "avg_salary", "metric": "salary", "operation": "mean", "format": "currency"},
        {"name": "largest_dept", "metric": "department", "operation": "mode", "format": "text"},
        {"name": "avg_tenure", "metric": "tenure", "operation": "mean", "format": "years"},
        {"name": "salary_range", "metric": "salary", "operation": "range", "format": "currency_range"},
    ],
    "financial": [
        {"name": "total_revenue", "metric": "revenue", "operation": "sum", "format": "currency"},
        {"name": "total_expenses", "metric": "expense", "operation": "sum", "format": "currency"},
        {"name": "profit_margin", "metric": ["revenue", "expense"], "operation": "margin", "format": "percentage"},
        {"name": "avg_budget", "metric": "budget", "operation": "mean", "format": "currency"},
        {"name": "variance", "metric": ["actual", "budget"], "operation": "variance", "format": "currency"},
    ],
    "survey": [
        {"name": "avg_rating", "metric": "rating", "operation": "mean", "format": "score"},
        {"name": "response_count", "metric": "any", "operation": "count", "format": "number"},
        {"name": "nps_score", "metric": "rating", "operation": "nps", "format": "score"},
        {"name": "top_score", "metric": "rating", "operation": "max", "format": "score"},
        {"name": "low_score", "metric": "rating", "operation": "min", "format": "score"},
    ],
    "product": [
        {"name": "total_users", "metric": "user", "operation": "count_unique", "format": "number"},
        {"name": "avg_sessions", "metric": "session", "operation": "mean", "format": "number"},
        {"name": "most_used_feature", "metric": "feature", "operation": "mode", "format": "text"},
        {"name": "retention_rate", "metric": "retention", "operation": "mean", "format": "percentage"},
        {"name": "churn_rate", "metric": "churn", "operation": "mean", "format": "percentage"},
    ],
    "business": [
        {"name": "key_kpi_avg", "metric": "kpi", "operation": "mean", "format": "number"},
        {"name": "target_achievement", "metric": ["actual", "target"], "operation": "ratio_pct", "format": "percentage"},
        {"name": "growth_rate", "metric": "growth", "operation": "mean", "format": "percentage"},
        {"name": "performance_score", "metric": "performance", "operation": "mean", "format": "score"},
    ],
    "operations": [
        {"name": "avg_cycle_time", "metric": "cycle_time", "operation": "mean", "format": "time"},
        {"name": "throughput", "metric": "throughput", "operation": "sum", "format": "number"},
        {"name": "sla_compliance", "metric": "sla", "operation": "mean", "format": "percentage"},
        {"name": "efficiency_rate", "metric": "efficiency", "operation": "mean", "format": "percentage"},
    ],
    "general": [
        {"name": "row_count", "metric": "any", "operation": "count", "format": "number"},
        {"name": "column_count", "metric": "any", "operation": "column_count", "format": "number"},
        {"name": "numeric_summary", "metric": "any", "operation": "describe", "format": "summary"},
    ],
}

# Column type synonyms for matching
COLUMN_SYNONYMS = {
    "revenue": ["revenue", "sales", "total_sale", "amount", "value", "income"],
    "cost": ["cost", "spend", "expense", "investment", "budget"],
    "product": ["product", "item", "sku", "product_name"],
    "region": ["region", "area", "territory", "location", "country"],
    "employee": ["employee", "staff", "worker", "emp_id"],
    "salary": ["salary", "compensation", "pay", "wage"],
    "department": ["department", "dept", "team", "division"],
    "tenure": ["tenure", "years", "experience", "service_years"],
    "rating": ["rating", "score", "satisfaction", "nps"],
    "channel": ["channel", "source", "medium", "platform"],
    "conversions": ["conversions", "conversion", "leads", "signups"],
    "clicks": ["clicks", "click"],
    "impressions": ["impressions", "views"],
    "user": ["user", "customer", "client", "account"],
    "session": ["session", "visit", "engagement"],
    "feature": ["feature", "module", "function"],
    "retention": ["retention", "retained"],
    "churn": ["churn", "churned", "attrition"],
    "budget": ["budget", "planned", "forecast"],
    "actual": ["actual", "realized", "result"],
    "target": ["target", "goal", "objective"],
    "expense": ["expense", "cost", "expenditure"],
    "growth": ["growth", "increase", "change"],
    "performance": ["performance", "score", "rating"],
    "kpi": ["kpi", "metric", "indicator"],
    "cycle_time": ["cycle_time", "time", "duration", "processing_time"],
    "throughput": ["throughput", "output", "production"],
    "sla": ["sla", "compliance", "on_time"],
    "efficiency": ["efficiency", "utilization", "productivity"],
}


class AutoInsightsEngine:
    """
    Generates instant insights when data is loaded.
    """
    
    def __init__(self, df: pd.DataFrame, domain: str = "general"):
        """
        Initialize with DataFrame and domain.
        
        Args:
            df: pandas DataFrame
            domain: Detected data domain
        """
        self.df = df
        self.domain = domain
        self.columns = df.columns.tolist()
        self.columns_lower = [col.lower() for col in self.columns]
        
        # Build column mapping
        self.column_mapping = self._build_column_mapping()
    
    def _build_column_mapping(self) -> Dict[str, str]:
        """Map column types to actual column names."""
        mapping = {}
        
        for col_type, synonyms in COLUMN_SYNONYMS.items():
            for synonym in synonyms:
                synonym_lower = synonym.lower()
                
                for i, actual_col in enumerate(self.columns_lower):
                    if synonym_lower in actual_col or actual_col in synonym_lower:
                        mapping[col_type] = self.columns[i]
                        break
                
                if col_type in mapping:
                    break
        
        return mapping
    
    def _get_column(self, col_type: str) -> Optional[str]:
        """Get actual column name for a column type."""
        return self.column_mapping.get(col_type)
    
    def generate_insights(self, max_insights: int = 5) -> List[Dict]:
        """
        Generate key insights for the dataset.
        
        Args:
            max_insights: Maximum number of insights to return
            
        Returns:
            List of insight dictionaries
        """
        insights = []
        
        # Get domain-specific templates
        templates = DOMAIN_INSIGHT_TEMPLATES.get(self.domain, DOMAIN_INSIGHT_TEMPLATES["general"])
        
        for template in templates:
            if len(insights) >= max_insights:
                break
            
            insight = self._generate_insight(template)
            if insight:
                insights.append(insight)
        
        # Add statistical insights if we have room
        if len(insights) < max_insights:
            stat_insights = self._generate_statistical_insights(max_insights - len(insights))
            insights.extend(stat_insights)
        
        # Add data quality insights
        quality_insights = self._generate_quality_insights()
        if quality_insights:
            insights.append(quality_insights)
        
        return insights[:max_insights]
    
    def _generate_insight(self, template: Dict) -> Optional[Dict]:
        """Generate a single insight from a template."""
        try:
            operation = template.get("operation")
            metric = template.get("metric")
            format_type = template.get("format", "number")
            
            # Handle different operations
            if operation == "sum":
                return self._sum_insight(template)
            elif operation == "mean":
                return self._mean_insight(template)
            elif operation == "count":
                return self._count_insight(template)
            elif operation == "count_unique":
                return self._count_unique_insight(template)
            elif operation == "mode":
                return self._mode_insight(template)
            elif operation == "max":
                return self._max_insight(template)
            elif operation == "min":
                return self._min_insight(template)
            elif operation == "range":
                return self._range_insight(template)
            elif operation == "ratio":
                return self._ratio_insight(template)
            elif operation == "ratio_pct":
                return self._ratio_pct_insight(template)
            elif operation == "margin":
                return self._margin_insight(template)
            elif operation == "variance":
                return self._variance_insight(template)
            elif operation == "nps":
                return self._nps_insight(template)
            elif operation == "column_count":
                return {"title": "Columns", "value": len(self.df.columns), "icon": "📋", "format": "number"}
            elif operation == "describe":
                return None  # Skip describe for now
            
            return None
            
        except Exception as e:
            logger.debug(f"Could not generate insight: {e}")
            return None
    
    def _format_value(self, value: float, format_type: str) -> str:
        """Format a value based on its type."""
        if pd.isna(value):
            return "N/A"
        
        if format_type == "currency":
            if abs(value) >= 1_000_000:
                return f"${value/1_000_000:,.1f}M"
            elif abs(value) >= 1_000:
                return f"${value:,.0f}"
            else:
                return f"${value:,.2f}"
        elif format_type == "number":
            if abs(value) >= 1_000_000:
                return f"{value/1_000_000:,.1f}M"
            elif abs(value) >= 1_000:
                return f"{value:,.0f}"
            else:
                return f"{value:,.2f}"
        elif format_type == "percentage":
            return f"{value:.1f}%"
        elif format_type == "score":
            return f"{value:.2f}/5" if value <= 5 else f"{value:.1f}"
        elif format_type == "years":
            return f"{value:.1f} years"
        elif format_type == "time":
            return f"{value:.1f} hrs"
        else:
            return str(value)
    
    # ============= INSIGHT GENERATORS =============
    
    def _sum_insight(self, template: Dict) -> Optional[Dict]:
        """Generate sum insight."""
        col = self._get_column(template["metric"])
        if not col or col not in self.df.columns:
            return None
        
        if not pd.api.types.is_numeric_dtype(self.df[col]):
            return None
        
        value = self.df[col].sum()
        formatted = self._format_value(value, template["format"])
        
        return {
            "title": f"Total {template['name'].replace('_', ' ').title()}",
            "value": formatted,
            "raw_value": value,
            "icon": "💰" if "revenue" in template["name"] else "📊",
            "column": col
        }
    
    def _mean_insight(self, template: Dict) -> Optional[Dict]:
        """Generate mean insight."""
        col = self._get_column(template["metric"])
        if not col or col not in self.df.columns:
            return None
        
        if not pd.api.types.is_numeric_dtype(self.df[col]):
            return None
        
        value = self.df[col].mean()
        formatted = self._format_value(value, template["format"])
        
        return {
            "title": f"Avg {template['name'].replace('_', ' ').title()}",
            "value": formatted,
            "raw_value": value,
            "icon": "📈",
            "column": col
        }
    
    def _count_insight(self, template: Dict) -> Optional[Dict]:
        """Generate count insight."""
        value = len(self.df)
        formatted = self._format_value(value, "number")
        
        return {
            "title": "Total Records",
            "value": formatted,
            "raw_value": value,
            "icon": "📋"
        }
    
    def _count_unique_insight(self, template: Dict) -> Optional[Dict]:
        """Generate unique count insight."""
        col = self._get_column(template["metric"])
        if not col or col not in self.df.columns:
            return None
        
        value = self.df[col].nunique()
        formatted = self._format_value(value, "number")
        
        return {
            "title": f"Unique {col.replace('_', ' ').title()}s",
            "value": formatted,
            "raw_value": value,
            "icon": "👥" if "employee" in col.lower() or "user" in col.lower() else "🔢",
            "column": col
        }
    
    def _mode_insight(self, template: Dict) -> Optional[Dict]:
        """Generate mode (most common value) insight."""
        col = self._get_column(template["metric"])
        if not col or col not in self.df.columns:
            return None
        
        mode = self.df[col].mode()
        if len(mode) == 0:
            return None
        
        value = mode.iloc[0]
        count = self.df[col].value_counts().iloc[0]
        
        return {
            "title": f"Top {col.replace('_', ' ').title()}",
            "value": f"{value} ({count:,})",
            "raw_value": value,
            "icon": "🏆",
            "column": col
        }
    
    def _max_insight(self, template: Dict) -> Optional[Dict]:
        """Generate max insight with group by."""
        group_col = self._get_column(template.get("group_by"))
        agg_col = self._get_column(template.get("agg"))
        
        if not group_col or not agg_col:
            return None
        
        grouped = self.df.groupby(group_col)[agg_col].sum()
        top = grouped.idxmax()
        value = grouped.max()
        
        return {
            "title": f"Top {group_col.replace('_', ' ').title()}",
            "value": f"{top} (${value:,.0f})",
            "raw_value": top,
            "icon": "📍",
            "column": group_col
        }
    
    def _min_insight(self, template: Dict) -> Optional[Dict]:
        """Generate min insight."""
        col = self._get_column(template["metric"])
        if not col or col not in self.df.columns:
            return None
        
        if not pd.api.types.is_numeric_dtype(self.df[col]):
            return None
        
        value = self.df[col].min()
        formatted = self._format_value(value, template["format"])
        
        return {
            "title": f"Min {col.replace('_', ' ').title()}",
            "value": formatted,
            "raw_value": value,
            "icon": "⬇️",
            "column": col
        }
    
    def _range_insight(self, template: Dict) -> Optional[Dict]:
        """Generate range insight."""
        col = self._get_column(template["metric"])
        if not col or col not in self.df.columns:
            return None
        
        if not pd.api.types.is_numeric_dtype(self.df[col]):
            return None
        
        min_val = self.df[col].min()
        max_val = self.df[col].max()
        
        return {
            "title": f"{col.replace('_', ' ').title()} Range",
            "value": f"${min_val:,.0f} - ${max_val:,.0f}",
            "raw_value": (min_val, max_val),
            "icon": "↔️",
            "column": col
        }
    
    def _ratio_insight(self, template: Dict) -> Optional[Dict]:
        """Generate ratio insight."""
        metrics = template["metric"]
        if len(metrics) != 2:
            return None
        
        num_col = self._get_column(metrics[0])
        denom_col = self._get_column(metrics[1])
        
        if not num_col or not denom_col:
            return None
        
        num_sum = self.df[num_col].sum()
        denom_sum = self.df[denom_col].sum()
        
        if denom_sum == 0:
            return None
        
        value = num_sum / denom_sum
        formatted = self._format_value(value, template["format"])
        
        return {
            "title": template["name"].replace("_", " ").title(),
            "value": formatted,
            "raw_value": value,
            "icon": "📐"
        }
    
    def _ratio_pct_insight(self, template: Dict) -> Optional[Dict]:
        """Generate ratio as percentage insight."""
        metrics = template["metric"]
        if len(metrics) != 2:
            return None
        
        num_col = self._get_column(metrics[0])
        denom_col = self._get_column(metrics[1])
        
        if not num_col or not denom_col:
            return None
        
        num_sum = self.df[num_col].sum()
        denom_sum = self.df[denom_col].sum()
        
        if denom_sum == 0:
            return None
        
        value = (num_sum / denom_sum) * 100
        formatted = f"{value:.1f}%"
        
        return {
            "title": template["name"].replace("_", " ").title(),
            "value": formatted,
            "raw_value": value,
            "icon": "📊"
        }
    
    def _margin_insight(self, template: Dict) -> Optional[Dict]:
        """Generate profit margin insight."""
        metrics = template["metric"]
        if len(metrics) != 2:
            return None
        
        rev_col = self._get_column(metrics[0])
        cost_col = self._get_column(metrics[1])
        
        if not rev_col or not cost_col:
            return None
        
        revenue = self.df[rev_col].sum()
        cost = self.df[cost_col].sum()
        
        if revenue == 0:
            return None
        
        margin = ((revenue - cost) / revenue) * 100
        
        # Determine emoji based on margin health
        icon = "✅" if margin > 20 else "⚠️" if margin > 0 else "❌"
        
        return {
            "title": "Profit Margin",
            "value": f"{margin:.1f}%",
            "raw_value": margin,
            "icon": icon
        }
    
    def _variance_insight(self, template: Dict) -> Optional[Dict]:
        """Generate budget variance insight."""
        metrics = template["metric"]
        if len(metrics) != 2:
            return None
        
        actual_col = self._get_column(metrics[0])
        budget_col = self._get_column(metrics[1])
        
        if not actual_col or not budget_col:
            return None
        
        actual = self.df[actual_col].sum()
        budget = self.df[budget_col].sum()
        
        variance = actual - budget
        variance_pct = (variance / budget * 100) if budget != 0 else 0
        
        icon = "✅" if variance >= 0 else "⚠️"
        
        return {
            "title": "Budget Variance",
            "value": f"{'+' if variance >= 0 else ''}{self._format_value(variance, 'currency')} ({variance_pct:+.1f}%)",
            "raw_value": variance,
            "icon": icon
        }
    
    def _nps_insight(self, template: Dict) -> Optional[Dict]:
        """Generate NPS score insight."""
        col = self._get_column(template["metric"])
        if not col or col not in self.df.columns:
            return None
        
        # NPS calculation: (Promoters - Detractors) / Total * 100
        # Assuming 0-10 scale: 9-10 = Promoters, 7-8 = Passive, 0-6 = Detractors
        ratings = self.df[col].dropna()
        
        if len(ratings) == 0:
            return None
        
        # Normalize to 0-10 if needed
        max_rating = ratings.max()
        if max_rating <= 5:
            ratings = ratings * 2  # Scale up 5-point to 10-point
        
        promoters = (ratings >= 9).sum()
        detractors = (ratings <= 6).sum()
        total = len(ratings)
        
        nps = ((promoters - detractors) / total) * 100
        
        icon = "🎉" if nps > 50 else "😊" if nps > 0 else "😟"
        
        return {
            "title": "NPS Score",
            "value": f"{nps:.0f}",
            "raw_value": nps,
            "icon": icon
        }
    
    def _generate_statistical_insights(self, max_count: int) -> List[Dict]:
        """Generate statistical insights for numeric columns."""
        insights = []
        
        numeric_cols = self.df.select_dtypes(include=['number']).columns
        
        for col in numeric_cols[:max_count]:
            # Check for outliers
            q1 = self.df[col].quantile(0.25)
            q3 = self.df[col].quantile(0.75)
            iqr = q3 - q1
            outliers = ((self.df[col] < q1 - 1.5 * iqr) | (self.df[col] > q3 + 1.5 * iqr)).sum()
            
            if outliers > 0 and outliers / len(self.df) > 0.01:  # More than 1% outliers
                insights.append({
                    "title": f"Outliers in {col}",
                    "value": f"{outliers} ({outliers/len(self.df)*100:.1f}%)",
                    "icon": "⚠️",
                    "type": "warning"
                })
        
        return insights
    
    def _generate_quality_insights(self) -> Optional[Dict]:
        """Generate data quality insights."""
        # Check for missing values
        missing = self.df.isnull().sum().sum()
        total_cells = self.df.size
        missing_pct = (missing / total_cells) * 100
        
        if missing_pct > 0:
            return {
                "title": "Data Completeness",
                "value": f"{100 - missing_pct:.1f}%",
                "icon": "✅" if missing_pct < 5 else "⚠️",
                "type": "quality"
            }
        
        return None
    
    def get_summary_card(self) -> Dict:
        """
        Get a summary card for the dataset.
        Returns a formatted summary suitable for display.
        """
        insights = self.generate_insights(max_insights=4)
        
        return {
            "domain": self.domain,
            "row_count": len(self.df),
            "column_count": len(self.df.columns),
            "insights": insights,
            "generated_at": datetime.now().isoformat()
        }


def generate_auto_insights(df: pd.DataFrame, domain: str = "general", max_insights: int = 5) -> List[Dict]:
    """
    Convenience function to generate auto insights.
    
    Args:
        df: pandas DataFrame
        domain: Data domain
        max_insights: Maximum insights to return
        
    Returns:
        List of insight dictionaries
    """
    engine = AutoInsightsEngine(df, domain)
    return engine.generate_insights(max_insights)


def render_insights_html(insights: List[Dict]) -> str:
    """
    Render insights as HTML cards for Streamlit.
    
    Args:
        insights: List of insight dictionaries
        
    Returns:
        HTML string
    """
    if not insights:
        return ""
    
    cards_html = ""
    for insight in insights:
        icon = insight.get("icon", "📊")
        title = insight.get("title", "")
        value = insight.get("value", "")
        
        cards_html += f"""
        <div style='
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 12px 16px;
            border-radius: 10px;
            margin: 4px;
            min-width: 120px;
            text-align: center;
            color: white;
        '>
            <div style='font-size: 1.5em;'>{icon}</div>
            <div style='font-size: 0.75em; opacity: 0.9;'>{title}</div>
            <div style='font-size: 1.2em; font-weight: bold;'>{value}</div>
        </div>
        """
    
    return f"<div style='display: flex; flex-wrap: wrap; gap: 8px;'>{cards_html}</div>"


# ============= TEST =============
if __name__ == "__main__":
    # Create test data
    test_df = pd.DataFrame({
        'product_name': ['Laptop', 'Phone', 'Tablet', 'Monitor', 'Keyboard'] * 20,
        'region': ['North', 'South', 'East', 'West', 'Central'] * 20,
        'total_sale': [1000, 500, 300, 400, 100] * 20,
        'quantity': [10, 20, 15, 8, 25] * 20,
        'customer_id': list(range(100)),
    })
    
    print("=" * 60)
    print("AUTO-INSIGHTS ENGINE TEST")
    print("=" * 60)
    
    engine = AutoInsightsEngine(test_df, domain="sales")
    
    print(f"\nColumn Mapping: {engine.column_mapping}")
    print(f"\nGenerated Insights:")
    
    insights = engine.generate_insights(max_insights=6)
    for insight in insights:
        print(f"  {insight['icon']} {insight['title']}: {insight['value']}")
    
    print(f"\n\nSummary Card:")
    summary = engine.get_summary_card()
    print(f"  Domain: {summary['domain']}")
    print(f"  Rows: {summary['row_count']}")
    print(f"  Columns: {summary['column_count']}")
    print(f"  Insights: {len(summary['insights'])}")
