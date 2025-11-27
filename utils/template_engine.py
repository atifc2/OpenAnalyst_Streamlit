"""
Template Engine - Execute Community Templates with Smart Column Mapping
Maps generic template queries to user's specific column names.

FLOW:
1. Match user query to community template (via vector search)
2. Map template columns to user's actual columns (fuzzy matching)
3. Execute the mapped template
4. Return formatted results

This enables INSTANT execution of 200+ expert templates!
"""

import re
import logging
import pandas as pd
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# Column type synonyms for smart mapping
COLUMN_SYNONYMS = {
    # Revenue/Sales
    "revenue": ["revenue", "sales", "total_sale", "amount", "value", "price", "income", "turnover"],
    "quantity": ["quantity", "qty", "count", "units", "volume", "orders"],
    
    # Categories
    "region": ["region", "area", "territory", "location", "zone", "geography", "country", "state", "city"],
    "product": ["product", "item", "sku", "product_name", "product_id", "goods", "merchandise"],
    "category": ["category", "type", "class", "group", "segment", "classification"],
    "channel": ["channel", "source", "medium", "platform", "touchpoint"],
    
    # Time
    "date": ["date", "datetime", "timestamp", "time", "created", "updated", "invoice_date", "order_date"],
    "month": ["month", "month_name", "invoice_date_month", "period"],
    "year": ["year", "invoice_date_year", "fiscal_year"],
    
    # Customer
    "customer": ["customer", "client", "user", "account", "customer_id", "buyer", "consumer"],
    "customer_type": ["customer_type", "segment", "tier", "level", "customer_segment"],
    
    # HR
    "employee": ["employee", "staff", "worker", "emp_id", "employee_id", "associate"],
    "department": ["department", "dept", "team", "division", "unit", "group"],
    "salary": ["salary", "compensation", "pay", "wage", "earnings", "income"],
    
    # Survey
    "rating": ["rating", "score", "satisfaction", "satisfaction_score", "nps", "csat"],
    "feedback": ["feedback", "comment", "response", "review", "text", "verbatim"],
    
    # Marketing
    "campaign": ["campaign", "campaign_name", "ad", "promotion", "initiative"],
    "impressions": ["impressions", "views", "reach", "exposure"],
    "clicks": ["clicks", "click", "interactions", "engagements"],
    "conversions": ["conversions", "conversion", "leads", "signups", "sales"],
    "cost": ["cost", "spend", "budget", "investment", "expense"],
}

# Template definitions with column requirements
TEMPLATE_DEFINITIONS = {
    # ==================== SALES TEMPLATES ====================
    "revenue by region": {
        "required_columns": ["revenue", "region"],
        "operation": "groupby_sum",
        "group_by": "region",
        "agg_column": "revenue",
        "chart_type": "bar",
        "title": "Revenue by Region"
    },
    "top 10 products": {
        "required_columns": ["product", "revenue"],
        "operation": "top_n",
        "group_by": "product",
        "agg_column": "revenue",
        "n": 10,
        "chart_type": "bar",
        "title": "Top 10 Products by Revenue"
    },
    "sales trend": {
        "required_columns": ["date", "revenue"],
        "operation": "groupby_sum",
        "group_by": "date",
        "agg_column": "revenue",
        "chart_type": "line",
        "title": "Sales Trend Over Time"
    },
    "monthly sales": {
        "required_columns": ["month", "revenue"],
        "operation": "groupby_sum",
        "group_by": "month",
        "agg_column": "revenue",
        "chart_type": "bar",
        "title": "Monthly Sales"
    },
    "average order value": {
        "required_columns": ["revenue"],
        "operation": "mean",
        "agg_column": "revenue",
        "chart_type": None,
        "title": "Average Order Value"
    },
    
    # ==================== MARKETING TEMPLATES ====================
    "campaign roi": {
        "required_columns": ["campaign", "revenue", "cost"],
        "operation": "custom",
        "custom_func": "calculate_roi",
        "chart_type": "bar",
        "title": "Campaign ROI"
    },
    "conversion funnel": {
        "required_columns": ["impressions", "clicks", "conversions"],
        "operation": "funnel",
        "stages": ["impressions", "clicks", "conversions"],
        "chart_type": "bar",
        "title": "Conversion Funnel"
    },
    "cost per acquisition": {
        "required_columns": ["cost", "conversions"],
        "operation": "division",
        "numerator": "cost",
        "denominator": "conversions",
        "chart_type": None,
        "title": "Cost Per Acquisition"
    },
    
    # ==================== HR TEMPLATES ====================
    "headcount by department": {
        "required_columns": ["department"],
        "operation": "count_by",
        "group_by": "department",
        "chart_type": "bar",
        "title": "Headcount by Department"
    },
    "average tenure": {
        "required_columns": ["tenure"],
        "operation": "mean",
        "agg_column": "tenure",
        "chart_type": None,
        "title": "Average Employee Tenure"
    },
    "salary distribution": {
        "required_columns": ["salary"],
        "operation": "distribution",
        "agg_column": "salary",
        "chart_type": "histogram",
        "title": "Salary Distribution"
    },
    
    # ==================== SURVEY TEMPLATES ====================
    "average satisfaction": {
        "required_columns": ["rating"],
        "operation": "mean",
        "agg_column": "rating",
        "chart_type": None,
        "title": "Average Satisfaction Score"
    },
    "nps distribution": {
        "required_columns": ["rating"],
        "operation": "distribution",
        "agg_column": "rating",
        "chart_type": "histogram",
        "title": "NPS Score Distribution"
    },
    "satisfaction by segment": {
        "required_columns": ["rating", "customer_type"],
        "operation": "groupby_mean",
        "group_by": "customer_type",
        "agg_column": "rating",
        "chart_type": "bar",
        "title": "Satisfaction by Customer Segment"
    },
    
    # ==================== FINANCIAL TEMPLATES ====================
    "budget vs actual": {
        "required_columns": ["budget", "actual"],
        "operation": "comparison",
        "compare_cols": ["budget", "actual"],
        "chart_type": "bar",
        "title": "Budget vs Actual"
    },
    "profit margin": {
        "required_columns": ["revenue", "cost"],
        "operation": "custom",
        "custom_func": "calculate_margin",
        "chart_type": None,
        "title": "Profit Margin"
    },
    "expense breakdown": {
        "required_columns": ["category", "cost"],
        "operation": "groupby_sum",
        "group_by": "category",
        "agg_column": "cost",
        "chart_type": "pie",
        "title": "Expense Breakdown by Category"
    },
}


class TemplateEngine:
    """
    Executes community templates with smart column mapping.
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize with user's DataFrame.
        
        Args:
            df: pandas DataFrame with user's data
        """
        self.df = df
        self.columns = df.columns.tolist()
        self.columns_lower = [col.lower() for col in self.columns]
        
        # Build column mapping
        self.column_mapping = self._build_column_mapping()
    
    def _build_column_mapping(self) -> Dict[str, str]:
        """
        Build mapping from template column types to actual column names.
        Uses fuzzy matching with synonyms.
        
        Returns:
            dict mapping column types to actual column names
        """
        mapping = {}
        
        for col_type, synonyms in COLUMN_SYNONYMS.items():
            # Check each synonym against actual columns
            for synonym in synonyms:
                synonym_lower = synonym.lower()
                
                # Exact match
                if synonym_lower in self.columns_lower:
                    idx = self.columns_lower.index(synonym_lower)
                    mapping[col_type] = self.columns[idx]
                    break
                
                # Partial match (column contains synonym)
                for i, actual_col in enumerate(self.columns_lower):
                    if synonym_lower in actual_col or actual_col in synonym_lower:
                        mapping[col_type] = self.columns[i]
                        break
                
                if col_type in mapping:
                    break
        
        logger.info(f"Column mapping: {mapping}")
        return mapping
    
    def can_execute_template(self, template_key: str) -> Tuple[bool, List[str]]:
        """
        Check if we have the required columns to execute a template.
        
        Args:
            template_key: Template identifier
            
        Returns:
            tuple of (can_execute: bool, missing_columns: list)
        """
        template = TEMPLATE_DEFINITIONS.get(template_key)
        if not template:
            return False, [f"Unknown template: {template_key}"]
        
        required = template.get("required_columns", [])
        missing = []
        
        for col_type in required:
            if col_type not in self.column_mapping:
                missing.append(col_type)
        
        return len(missing) == 0, missing
    
    def execute_template(self, template_key: str) -> Dict:
        """
        Execute a template and return results.
        
        Args:
            template_key: Template identifier
            
        Returns:
            dict with results in standard AI response format
        """
        template = TEMPLATE_DEFINITIONS.get(template_key)
        if not template:
            return self._error_response(f"Unknown template: {template_key}")
        
        can_execute, missing = self.can_execute_template(template_key)
        if not can_execute:
            return self._error_response(
                f"Missing columns for '{template_key}': {', '.join(missing)}. "
                f"Available mappings: {self.column_mapping}"
            )
        
        try:
            operation = template.get("operation")
            
            if operation == "groupby_sum":
                return self._groupby_sum(template)
            elif operation == "groupby_mean":
                return self._groupby_mean(template)
            elif operation == "top_n":
                return self._top_n(template)
            elif operation == "count_by":
                return self._count_by(template)
            elif operation == "mean":
                return self._mean(template)
            elif operation == "distribution":
                return self._distribution(template)
            elif operation == "division":
                return self._division(template)
            elif operation == "funnel":
                return self._funnel(template)
            elif operation == "comparison":
                return self._comparison(template)
            elif operation == "custom":
                return self._custom(template)
            else:
                return self._error_response(f"Unsupported operation: {operation}")
                
        except Exception as e:
            logger.error(f"Template execution error: {e}")
            return self._error_response(str(e))
    
    def _get_column(self, col_type: str) -> str:
        """Get actual column name for a column type."""
        return self.column_mapping.get(col_type)
    
    def _format_response(
        self, 
        content: str, 
        result_value: any = None,
        is_visualizable: bool = False,
        chart_data: Dict = None,
        suggested_actions: List[str] = None
    ) -> Dict:
        """Format result in standard AI response format."""
        return {
            "content": content,
            "reasoning": "Executed from community template for instant response.",
            "is_visualizable": is_visualizable,
            "chart_data": chart_data,
            "suggested_actions": suggested_actions or [
                "Drill down into specific segment",
                "Compare with another metric",
                "Show trend over time"
            ],
            "response_type": "template",
            "_raw_value": result_value
        }
    
    def _error_response(self, error_msg: str) -> Dict:
        """Format error response."""
        return {
            "content": f"⚠️ Template error: {error_msg}",
            "reasoning": "Template execution failed.",
            "is_visualizable": False,
            "suggested_actions": ["Try a different query", "Check data columns"],
            "response_type": "error"
        }
    
    # ============= OPERATION HANDLERS =============
    
    def _groupby_sum(self, template: Dict) -> Dict:
        """Group by and sum."""
        group_col = self._get_column(template["group_by"])
        agg_col = self._get_column(template["agg_column"])
        
        result = self.df.groupby(group_col)[agg_col].sum().sort_values(ascending=False)
        
        # Format top results
        top_5 = result.head(5)
        lines = [f"- **{k}**: {v:,.2f}" for k, v in top_5.items()]
        content = f"📊 **{template['title']}:**\n" + "\n".join(lines)
        
        if len(result) > 5:
            content += f"\n- ... and {len(result) - 5} more"
        
        return self._format_response(
            content,
            result_value=result.to_dict(),
            is_visualizable=True,
            chart_data={
                "title": template["title"],
                "chart_type": template.get("chart_type", "bar"),
                "x_column": group_col,
                "y_column": agg_col,
                "color_column": None
            }
        )
    
    def _groupby_mean(self, template: Dict) -> Dict:
        """Group by and average."""
        group_col = self._get_column(template["group_by"])
        agg_col = self._get_column(template["agg_column"])
        
        result = self.df.groupby(group_col)[agg_col].mean().sort_values(ascending=False)
        
        lines = [f"- **{k}**: {v:.2f}" for k, v in result.head(5).items()]
        content = f"📊 **{template['title']}:**\n" + "\n".join(lines)
        
        return self._format_response(
            content,
            result_value=result.to_dict(),
            is_visualizable=True,
            chart_data={
                "title": template["title"],
                "chart_type": template.get("chart_type", "bar"),
                "x_column": group_col,
                "y_column": agg_col,
                "color_column": None
            }
        )
    
    def _top_n(self, template: Dict) -> Dict:
        """Get top N by aggregation."""
        group_col = self._get_column(template["group_by"])
        agg_col = self._get_column(template["agg_column"])
        n = template.get("n", 10)
        
        result = self.df.groupby(group_col)[agg_col].sum().nlargest(n)
        
        lines = [f"{i}. **{k}**: {v:,.2f}" for i, (k, v) in enumerate(result.items(), 1)]
        content = f"📊 **{template['title']}:**\n" + "\n".join(lines)
        
        return self._format_response(
            content,
            result_value=result.to_dict(),
            is_visualizable=True,
            chart_data={
                "title": template["title"],
                "chart_type": template.get("chart_type", "bar"),
                "x_column": group_col,
                "y_column": agg_col,
                "color_column": None
            }
        )
    
    def _count_by(self, template: Dict) -> Dict:
        """Count by category."""
        group_col = self._get_column(template["group_by"])
        
        result = self.df[group_col].value_counts()
        
        lines = [f"- **{k}**: {v:,}" for k, v in result.head(10).items()]
        content = f"📊 **{template['title']}:**\n" + "\n".join(lines)
        
        return self._format_response(
            content,
            result_value=result.to_dict(),
            is_visualizable=True,
            chart_data={
                "title": template["title"],
                "chart_type": template.get("chart_type", "bar"),
                "x_column": group_col,
                "y_column": "count",
                "color_column": None
            }
        )
    
    def _mean(self, template: Dict) -> Dict:
        """Calculate average."""
        agg_col = self._get_column(template["agg_column"])
        
        result = self.df[agg_col].mean()
        
        content = f"📊 **{template['title']}:** {result:.2f}"
        
        return self._format_response(
            content,
            result_value=result,
            is_visualizable=False
        )
    
    def _distribution(self, template: Dict) -> Dict:
        """Show distribution."""
        agg_col = self._get_column(template["agg_column"])
        
        stats = {
            "mean": self.df[agg_col].mean(),
            "median": self.df[agg_col].median(),
            "std": self.df[agg_col].std(),
            "min": self.df[agg_col].min(),
            "max": self.df[agg_col].max(),
        }
        
        content = f"📊 **{template['title']}:**\n"
        content += f"- Mean: {stats['mean']:.2f}\n"
        content += f"- Median: {stats['median']:.2f}\n"
        content += f"- Std Dev: {stats['std']:.2f}\n"
        content += f"- Range: {stats['min']:.2f} - {stats['max']:.2f}"
        
        return self._format_response(
            content,
            result_value=stats,
            is_visualizable=True,
            chart_data={
                "title": template["title"],
                "chart_type": "histogram",
                "x_column": agg_col,
                "y_column": None,
                "color_column": None
            }
        )
    
    def _division(self, template: Dict) -> Dict:
        """Calculate ratio."""
        num_col = self._get_column(template["numerator"])
        denom_col = self._get_column(template["denominator"])
        
        total_num = self.df[num_col].sum()
        total_denom = self.df[denom_col].sum()
        
        if total_denom == 0:
            return self._error_response(f"Cannot divide by zero ({denom_col} sum is 0)")
        
        result = total_num / total_denom
        
        content = f"📊 **{template['title']}:** ${result:.2f}"
        
        return self._format_response(
            content,
            result_value=result,
            is_visualizable=False
        )
    
    def _funnel(self, template: Dict) -> Dict:
        """Show funnel stages."""
        stages = template.get("stages", [])
        
        funnel_data = []
        for i, stage in enumerate(stages):
            col = self._get_column(stage)
            if col:
                total = self.df[col].sum()
                funnel_data.append({"stage": stage, "value": total})
        
        # Calculate conversion rates
        lines = []
        for i, stage_data in enumerate(funnel_data):
            rate = ""
            if i > 0 and funnel_data[i-1]["value"] > 0:
                conv_rate = stage_data["value"] / funnel_data[i-1]["value"] * 100
                rate = f" ({conv_rate:.1f}% from previous)"
            lines.append(f"- **{stage_data['stage'].title()}**: {stage_data['value']:,.0f}{rate}")
        
        content = f"📊 **{template['title']}:**\n" + "\n".join(lines)
        
        return self._format_response(
            content,
            result_value=funnel_data,
            is_visualizable=True,
            chart_data={
                "title": template["title"],
                "chart_type": "bar",
                "x_column": "stage",
                "y_column": "value",
                "color_column": None
            }
        )
    
    def _comparison(self, template: Dict) -> Dict:
        """Compare two columns."""
        compare_cols = template.get("compare_cols", [])
        
        lines = []
        for col_type in compare_cols:
            col = self._get_column(col_type)
            if col:
                total = self.df[col].sum()
                lines.append(f"- **{col_type.title()}**: {total:,.2f}")
        
        if len(compare_cols) >= 2:
            col1 = self._get_column(compare_cols[0])
            col2 = self._get_column(compare_cols[1])
            if col1 and col2:
                diff = self.df[col2].sum() - self.df[col1].sum()
                variance_pct = (diff / self.df[col1].sum() * 100) if self.df[col1].sum() != 0 else 0
                lines.append(f"- **Variance**: {diff:,.2f} ({variance_pct:+.1f}%)")
        
        content = f"📊 **{template['title']}:**\n" + "\n".join(lines)
        
        return self._format_response(
            content,
            is_visualizable=True,
            chart_data={
                "title": template["title"],
                "chart_type": "bar",
                "x_column": "metric",
                "y_column": "value",
                "color_column": None
            }
        )
    
    def _custom(self, template: Dict) -> Dict:
        """Execute custom function."""
        func_name = template.get("custom_func")
        
        if func_name == "calculate_roi":
            return self._calculate_roi(template)
        elif func_name == "calculate_margin":
            return self._calculate_margin(template)
        else:
            return self._error_response(f"Unknown custom function: {func_name}")
    
    def _calculate_roi(self, template: Dict) -> Dict:
        """Calculate ROI by campaign."""
        campaign_col = self._get_column("campaign")
        revenue_col = self._get_column("revenue")
        cost_col = self._get_column("cost")
        
        grouped = self.df.groupby(campaign_col).agg({
            revenue_col: 'sum',
            cost_col: 'sum'
        })
        grouped['roi'] = ((grouped[revenue_col] - grouped[cost_col]) / grouped[cost_col] * 100)
        grouped = grouped.sort_values('roi', ascending=False)
        
        lines = [f"- **{k}**: {v['roi']:.1f}% ROI" for k, v in grouped.head(5).iterrows()]
        content = f"📊 **{template['title']}:**\n" + "\n".join(lines)
        
        return self._format_response(
            content,
            result_value=grouped['roi'].to_dict(),
            is_visualizable=True,
            chart_data={
                "title": template["title"],
                "chart_type": "bar",
                "x_column": campaign_col,
                "y_column": "roi",
                "color_column": None
            }
        )
    
    def _calculate_margin(self, template: Dict) -> Dict:
        """Calculate profit margin."""
        revenue_col = self._get_column("revenue")
        cost_col = self._get_column("cost")
        
        total_revenue = self.df[revenue_col].sum()
        total_cost = self.df[cost_col].sum()
        profit = total_revenue - total_cost
        margin = (profit / total_revenue * 100) if total_revenue != 0 else 0
        
        content = f"📊 **{template['title']}:**\n"
        content += f"- Revenue: ${total_revenue:,.2f}\n"
        content += f"- Cost: ${total_cost:,.2f}\n"
        content += f"- Profit: ${profit:,.2f}\n"
        content += f"- **Margin: {margin:.1f}%**"
        
        return self._format_response(
            content,
            result_value={"margin": margin, "profit": profit},
            is_visualizable=False
        )


def find_matching_template(query: str, domain: str = "general") -> Optional[str]:
    """
    Find a template that matches the user's query.
    
    Args:
        query: User's natural language query
        domain: Data domain
        
    Returns:
        Template key if found, None otherwise
    """
    query_lower = query.lower()
    
    for template_key in TEMPLATE_DEFINITIONS.keys():
        # Check if template key words are in query
        key_words = set(template_key.split())
        query_words = set(query_lower.split())
        
        # Match if all key words present or if key is substring
        if key_words.issubset(query_words) or template_key in query_lower:
            return template_key
    
    return None


def execute_template(df: pd.DataFrame, template_key: str) -> Dict:
    """
    Convenience function to execute a template.
    
    Args:
        df: pandas DataFrame
        template_key: Template identifier
        
    Returns:
        Response dict
    """
    engine = TemplateEngine(df)
    return engine.execute_template(template_key)


# ============= TEST =============
if __name__ == "__main__":
    # Create test data
    test_df = pd.DataFrame({
        'product_name': ['Laptop', 'Phone', 'Tablet', 'Monitor', 'Keyboard'] * 20,
        'region': ['North', 'South', 'East', 'West', 'Central'] * 20,
        'total_sale': [1000, 500, 300, 400, 100] * 20,
        'quantity': [10, 20, 15, 8, 25] * 20,
        'month_name': ['Jan', 'Feb', 'Mar', 'Apr', 'May'] * 20,
        'customer_type': ['Enterprise', 'SMB', 'Consumer', 'Enterprise', 'SMB'] * 20,
    })
    
    engine = TemplateEngine(test_df)
    
    print("=" * 60)
    print("TEMPLATE ENGINE TEST")
    print("=" * 60)
    
    print(f"\nColumn Mapping: {engine.column_mapping}")
    
    # Test templates
    templates_to_test = [
        "revenue by region",
        "top 10 products",
        "average order value",
        "headcount by department",  # Will fail - no department
    ]
    
    for template_key in templates_to_test:
        print(f"\n📝 Template: '{template_key}'")
        
        can_execute, missing = engine.can_execute_template(template_key)
        print(f"   Can execute: {can_execute}")
        if not can_execute:
            print(f"   Missing: {missing}")
            continue
        
        result = engine.execute_template(template_key)
        print(f"   Result: {result['content'][:100]}...")
        print(f"   Visualizable: {result['is_visualizable']}")
