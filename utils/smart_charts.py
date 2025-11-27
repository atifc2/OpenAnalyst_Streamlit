"""
Smart Charts - Intelligent Chart Type Selection
Automatically selects the best chart type based on data characteristics.

CHART SELECTION LOGIC:
- Time series data → Line chart
- Categorical comparison → Bar chart
- Distribution analysis → Histogram
- Part-of-whole → Pie chart
- Correlation/relationships → Scatter plot
- Rankings → Horizontal bar
- Many categories → Treemap/sunburst

This ensures OPTIMAL VISUALIZATION without user guessing!
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# Chart type definitions with scoring criteria
CHART_TYPES = {
    "bar": {
        "name": "Bar Chart",
        "best_for": "Comparing categories",
        "icon": "📊",
        "criteria": {
            "categorical_x": 3,  # High score if x is categorical
            "numeric_y": 2,
            "few_categories": 2,  # 3-15 categories
            "comparison_query": 2,
        }
    },
    "line": {
        "name": "Line Chart",
        "best_for": "Trends over time",
        "icon": "📈",
        "criteria": {
            "datetime_x": 4,  # High priority for time data
            "numeric_y": 2,
            "ordered_x": 3,
            "trend_query": 2,
        }
    },
    "scatter": {
        "name": "Scatter Plot",
        "best_for": "Relationships between variables",
        "icon": "⚬",
        "criteria": {
            "numeric_x": 3,
            "numeric_y": 3,
            "many_points": 2,  # Good for large datasets
            "correlation_query": 3,
        }
    },
    "histogram": {
        "name": "Histogram",
        "best_for": "Distribution of values",
        "icon": "📊",
        "criteria": {
            "numeric_column": 4,
            "single_variable": 2,
            "distribution_query": 3,
        }
    },
    "pie": {
        "name": "Pie Chart",
        "best_for": "Parts of a whole",
        "icon": "🥧",
        "criteria": {
            "categorical": 2,
            "few_categories": 3,  # 2-7 categories ideal
            "percentage_query": 3,
            "composition_query": 2,
        }
    },
    "box": {
        "name": "Box Plot",
        "best_for": "Statistical distribution",
        "icon": "📦",
        "criteria": {
            "numeric_y": 3,
            "categorical_x": 2,
            "outlier_query": 3,
            "distribution_query": 2,
        }
    },
    "area": {
        "name": "Area Chart",
        "best_for": "Cumulative trends",
        "icon": "📊",
        "criteria": {
            "datetime_x": 3,
            "numeric_y": 2,
            "cumulative_query": 3,
            "stacked_query": 2,
        }
    },
    "heatmap": {
        "name": "Heatmap",
        "best_for": "Matrix data visualization",
        "icon": "🗺️",
        "criteria": {
            "two_categorical": 3,
            "numeric_values": 2,
            "correlation_query": 2,
        }
    },
}

# Query keywords that suggest specific chart types
QUERY_KEYWORDS = {
    "trend": ["trend", "over time", "timeline", "growth", "change", "monthly", "yearly", "daily", "weekly"],
    "comparison": ["compare", "vs", "versus", "difference", "between", "by", "per"],
    "distribution": ["distribution", "spread", "histogram", "frequency", "how many", "count"],
    "composition": ["breakdown", "composition", "proportion", "percentage", "share", "part of"],
    "correlation": ["correlation", "relationship", "scatter", "vs", "affect", "impact"],
    "ranking": ["top", "bottom", "best", "worst", "rank", "leader", "lowest", "highest"],
    "outlier": ["outlier", "anomaly", "unusual", "extreme", "box"],
}


class SmartChartSelector:
    """
    Intelligently selects the best chart type for given data and query.
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize with DataFrame.
        
        Args:
            df: pandas DataFrame to analyze
        """
        self.df = df
        self.columns = df.columns.tolist()
        
        # Analyze column types
        self.column_types = self._analyze_column_types()
    
    def _analyze_column_types(self) -> Dict[str, str]:
        """
        Analyze and categorize column types.
        
        Returns:
            dict mapping column names to types (numeric, categorical, datetime, boolean)
        """
        types = {}
        
        for col in self.columns:
            if pd.api.types.is_datetime64_any_dtype(self.df[col]):
                types[col] = "datetime"
            elif pd.api.types.is_numeric_dtype(self.df[col]):
                # Check if it's actually categorical (few unique values)
                unique_ratio = self.df[col].nunique() / len(self.df)
                if unique_ratio < 0.05 and self.df[col].nunique() < 20:
                    types[col] = "categorical"
                else:
                    types[col] = "numeric"
            elif pd.api.types.is_bool_dtype(self.df[col]):
                types[col] = "boolean"
            else:
                # Check if it could be datetime
                try:
                    pd.to_datetime(self.df[col].head(10))
                    types[col] = "datetime"
                except:
                    types[col] = "categorical"
        
        return types
    
    def select_chart(
        self, 
        x_column: Optional[str] = None, 
        y_column: Optional[str] = None,
        color_column: Optional[str] = None,
        query: str = ""
    ) -> Dict:
        """
        Select the best chart type for the given configuration.
        
        Args:
            x_column: Column for x-axis
            y_column: Column for y-axis
            color_column: Column for color grouping
            query: User's natural language query (for intent detection)
            
        Returns:
            dict with chart_type, confidence, reasoning, and suggestions
        """
        scores = {}
        
        for chart_type, config in CHART_TYPES.items():
            score = self._calculate_chart_score(
                chart_type, config, x_column, y_column, color_column, query
            )
            scores[chart_type] = score
        
        # Find best chart type
        best_chart = max(scores, key=scores.get)
        best_score = scores[best_chart]
        
        # Calculate confidence (normalize to 0-1)
        max_possible = sum(CHART_TYPES[best_chart]["criteria"].values())
        confidence = min(best_score / max_possible, 1.0) if max_possible > 0 else 0.5
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            best_chart, x_column, y_column, color_column, query
        )
        
        # Get alternative suggestions
        alternatives = sorted(scores, key=scores.get, reverse=True)[1:3]
        
        return {
            "chart_type": best_chart,
            "confidence": confidence,
            "reasoning": reasoning,
            "alternatives": alternatives,
            "scores": scores,
            "icon": CHART_TYPES[best_chart]["icon"],
            "best_for": CHART_TYPES[best_chart]["best_for"]
        }
    
    def _calculate_chart_score(
        self,
        chart_type: str,
        config: Dict,
        x_column: Optional[str],
        y_column: Optional[str],
        color_column: Optional[str],
        query: str
    ) -> float:
        """Calculate score for a specific chart type."""
        score = 0
        criteria = config["criteria"]
        query_lower = query.lower() if query else ""
        
        # Get column types
        x_type = self.column_types.get(x_column) if x_column else None
        y_type = self.column_types.get(y_column) if y_column else None
        
        # Categorical X
        if "categorical_x" in criteria and x_type == "categorical":
            score += criteria["categorical_x"]
        
        # Datetime X
        if "datetime_x" in criteria and x_type == "datetime":
            score += criteria["datetime_x"]
        
        # Numeric X
        if "numeric_x" in criteria and x_type == "numeric":
            score += criteria["numeric_x"]
        
        # Numeric Y
        if "numeric_y" in criteria and y_type == "numeric":
            score += criteria["numeric_y"]
        
        # Ordered X (for line charts)
        if "ordered_x" in criteria:
            if x_type == "datetime" or (x_column and "month" in x_column.lower()):
                score += criteria["ordered_x"]
        
        # Few categories (2-15)
        if "few_categories" in criteria and x_column:
            n_categories = self.df[x_column].nunique() if x_column in self.df.columns else 0
            if 2 <= n_categories <= 15:
                score += criteria["few_categories"]
        
        # Many points (good for scatter)
        if "many_points" in criteria and len(self.df) > 50:
            score += criteria["many_points"]
        
        # Query keyword matching
        for keyword_type, keywords in QUERY_KEYWORDS.items():
            criteria_key = f"{keyword_type}_query"
            if criteria_key in criteria:
                if any(kw in query_lower for kw in keywords):
                    score += criteria[criteria_key]
        
        return score
    
    def _generate_reasoning(
        self,
        chart_type: str,
        x_column: Optional[str],
        y_column: Optional[str],
        color_column: Optional[str],
        query: str
    ) -> str:
        """Generate human-readable reasoning for chart selection."""
        reasons = []
        
        x_type = self.column_types.get(x_column) if x_column else None
        y_type = self.column_types.get(y_column) if y_column else None
        
        if chart_type == "line":
            if x_type == "datetime":
                reasons.append(f"`{x_column}` is a time-based column")
            reasons.append("Line charts are ideal for showing trends over time")
        
        elif chart_type == "bar":
            if x_type == "categorical":
                reasons.append(f"`{x_column}` is categorical with {self.df[x_column].nunique()} categories")
            reasons.append("Bar charts excel at comparing values across categories")
        
        elif chart_type == "scatter":
            if x_type == "numeric" and y_type == "numeric":
                reasons.append("Both axes are numeric - perfect for showing relationships")
            reasons.append("Scatter plots reveal correlations and patterns")
        
        elif chart_type == "histogram":
            reasons.append("Histograms show the distribution of values")
            if y_column and y_type == "numeric":
                reasons.append(f"`{y_column}` is numeric")
        
        elif chart_type == "pie":
            if x_column and self.df[x_column].nunique() <= 7:
                reasons.append(f"Only {self.df[x_column].nunique()} categories - pie charts work well")
            reasons.append("Pie charts show proportions of a whole")
        
        elif chart_type == "box":
            reasons.append("Box plots show distribution statistics and outliers")
        
        return " | ".join(reasons) if reasons else f"{chart_type} chart selected based on data structure"
    
    def suggest_columns(self, query: str = "") -> Dict:
        """
        Suggest which columns to use for x, y, and color.
        
        Args:
            query: User's query for context
            
        Returns:
            dict with suggested columns and chart configuration
        """
        query_lower = query.lower() if query else ""
        
        # Find datetime columns (prefer for x-axis with trends)
        datetime_cols = [c for c, t in self.column_types.items() if t == "datetime"]
        
        # Find numeric columns (prefer for y-axis)
        numeric_cols = [c for c, t in self.column_types.items() if t == "numeric"]
        
        # Find categorical columns (for grouping/color)
        categorical_cols = [c for c, t in self.column_types.items() if t == "categorical"]
        
        # Determine best configuration based on query and available columns
        suggestion = {"x_column": None, "y_column": None, "color_column": None}
        
        # Check for trend queries
        if any(kw in query_lower for kw in QUERY_KEYWORDS["trend"]):
            if datetime_cols:
                suggestion["x_column"] = datetime_cols[0]
            elif categorical_cols:
                # Look for time-like categorical (month, quarter, etc.)
                for col in categorical_cols:
                    if any(t in col.lower() for t in ["month", "year", "quarter", "date"]):
                        suggestion["x_column"] = col
                        break
            
            if numeric_cols:
                # Prefer revenue/sales type columns
                for col in numeric_cols:
                    if any(t in col.lower() for t in ["revenue", "sales", "total", "amount"]):
                        suggestion["y_column"] = col
                        break
                if not suggestion["y_column"]:
                    suggestion["y_column"] = numeric_cols[0]
        
        # Check for comparison queries
        elif any(kw in query_lower for kw in QUERY_KEYWORDS["comparison"]):
            if categorical_cols:
                # Look for category-like columns
                for col in categorical_cols:
                    if any(t in col.lower() for t in ["region", "category", "product", "type", "department"]):
                        suggestion["x_column"] = col
                        break
                if not suggestion["x_column"]:
                    suggestion["x_column"] = categorical_cols[0]
            
            if numeric_cols:
                suggestion["y_column"] = numeric_cols[0]
            
            # Add color if multiple categories
            if len(categorical_cols) > 1:
                suggestion["color_column"] = categorical_cols[1]
        
        # Default: categorical x, numeric y
        else:
            if categorical_cols:
                suggestion["x_column"] = categorical_cols[0]
            if numeric_cols:
                suggestion["y_column"] = numeric_cols[0]
        
        # Select chart based on suggestions
        chart_result = self.select_chart(
            x_column=suggestion["x_column"],
            y_column=suggestion["y_column"],
            color_column=suggestion["color_column"],
            query=query
        )
        
        return {
            **suggestion,
            **chart_result
        }
    
    def get_column_summary(self) -> Dict:
        """Get a summary of column types for UI display."""
        summary = {
            "datetime": [],
            "numeric": [],
            "categorical": [],
            "boolean": []
        }
        
        for col, col_type in self.column_types.items():
            summary[col_type].append(col)
        
        return summary


def select_smart_chart(
    df: pd.DataFrame,
    x_column: Optional[str] = None,
    y_column: Optional[str] = None,
    color_column: Optional[str] = None,
    query: str = ""
) -> Dict:
    """
    Convenience function to select the best chart type.
    
    Args:
        df: pandas DataFrame
        x_column: Column for x-axis
        y_column: Column for y-axis  
        color_column: Column for color
        query: User's query
        
    Returns:
        Chart selection result
    """
    selector = SmartChartSelector(df)
    return selector.select_chart(x_column, y_column, color_column, query)


def suggest_chart_config(df: pd.DataFrame, query: str = "") -> Dict:
    """
    Convenience function to get full chart configuration suggestions.
    
    Args:
        df: pandas DataFrame
        query: User's natural language query
        
    Returns:
        Full chart configuration with suggested columns and type
    """
    selector = SmartChartSelector(df)
    return selector.suggest_columns(query)


# ============= TEST =============
if __name__ == "__main__":
    # Create test data
    test_df = pd.DataFrame({
        'product': ['Laptop', 'Phone', 'Tablet', 'Monitor', 'Keyboard'] * 20,
        'region': ['North', 'South', 'East', 'West', 'Central'] * 20,
        'revenue': [1000, 500, 300, 400, 100] * 20,
        'quantity': [10, 20, 15, 8, 25] * 20,
        'date': pd.date_range('2023-01-01', periods=100, freq='D'),
        'score': [4.5, 3.8, 4.2, 3.5, 4.0] * 20,
    })
    
    print("=" * 60)
    print("SMART CHART SELECTOR TEST")
    print("=" * 60)
    
    selector = SmartChartSelector(test_df)
    
    print(f"\nColumn Types:")
    for col, col_type in selector.column_types.items():
        print(f"  {col}: {col_type}")
    
    # Test queries
    test_queries = [
        "show revenue trend over time",
        "compare revenue by region",
        "distribution of scores",
        "top products by revenue",
        "correlation between quantity and revenue",
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: '{query}'")
        result = selector.suggest_columns(query)
        print(f"   Chart: {result['chart_type']} {result['icon']}")
        print(f"   X: {result['x_column']}, Y: {result['y_column']}")
        print(f"   Confidence: {result['confidence']:.0%}")
        print(f"   Reasoning: {result['reasoning']}")
