"""
Smart Chart Generator - Creates charts from AI insights and auto-bins data

This module handles:
1. Parsing AI text responses to extract forecast/prediction data
2. Auto-binning numeric columns (age groups, price ranges, etc.)
3. Creating temporary dataframes from parsed data for charting

Used when AI generates insights but the chart columns don't exist in original data.
"""

import re
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SmartChartGenerator:
    """
    Generates charts from AI insights by parsing text and creating computed data.
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize with the current dataframe.
        
        Args:
            df: The original dataset
        """
        self.df = df
        self.columns = df.columns.tolist() if df is not None else []
        self.numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist() if df is not None else []
        self.date_columns = self._detect_date_columns()
    
    def _detect_date_columns(self) -> List[str]:
        """Detect columns that contain date/datetime data."""
        date_cols = []
        if self.df is None:
            return date_cols
        
        for col in self.df.columns:
            if self.df[col].dtype == 'datetime64[ns]':
                date_cols.append(col)
            elif self.df[col].dtype == 'object':
                # Try to parse as date
                try:
                    sample = self.df[col].dropna().head(10)
                    if len(sample) > 0:
                        pd.to_datetime(sample)
                        date_cols.append(col)
                except:
                    pass
        return date_cols
    
    def parse_forecast_from_text(self, ai_response: str) -> Optional[pd.DataFrame]:
        """
        Parse forecast/prediction data from AI response text.
        
        Looks for patterns like:
        - "August 2024: 367,318"
        - "Month 1: $50,000"
        - "Q1 2024: 1.2M"
        
        Args:
            ai_response: The AI's text response containing forecast data
            
        Returns:
            DataFrame with parsed forecast data, or None if no data found
        """
        forecast_data = []
        
        # Pattern 1: "Month Year: Value" (e.g., "August 2024: 367,318")
        pattern1 = r'(\w+)\s*(\d{4})\s*[:\-]\s*\$?([\d,]+(?:\.\d+)?)'
        matches1 = re.findall(pattern1, ai_response)
        
        if matches1:
            for month, year, value in matches1:
                try:
                    # Parse month name
                    month_num = datetime.strptime(month[:3], '%b').month if len(month) >= 3 else None
                    if month_num:
                        date_str = f"{year}-{month_num:02d}-01"
                        value_clean = float(value.replace(',', ''))
                        forecast_data.append({
                            'period': f"{month} {year}",
                            'date': pd.to_datetime(date_str),
                            'projected_value': value_clean
                        })
                except Exception as e:
                    logger.debug(f"Could not parse: {month} {year}: {value} - {e}")
        
        # Pattern 2: "Week/Month N: Value"
        pattern2 = r'(Week|Month|Quarter|Q)\s*(\d+)\s*[:\-]\s*\$?([\d,]+(?:\.\d+)?)'
        matches2 = re.findall(pattern2, ai_response, re.IGNORECASE)
        
        if matches2 and not forecast_data:
            for period_type, num, value in matches2:
                try:
                    value_clean = float(value.replace(',', ''))
                    forecast_data.append({
                        'period': f"{period_type} {num}",
                        'period_num': int(num),
                        'projected_value': value_clean
                    })
                except Exception as e:
                    logger.debug(f"Could not parse: {period_type} {num}: {value} - {e}")
        
        # Pattern 3: Simple numbered projections
        pattern3 = r'(\d+)\s*[:\-\.]\s*\$?([\d,]+(?:\.\d+)?)\s*(?:revenue|sales|units)?'
        if not forecast_data:
            matches3 = re.findall(pattern3, ai_response, re.IGNORECASE)
            if len(matches3) >= 3:  # Need at least 3 data points
                for i, (period, value) in enumerate(matches3[:12]):  # Max 12 periods
                    try:
                        value_clean = float(value.replace(',', ''))
                        if value_clean > 100:  # Filter out small numbers that might be noise
                            forecast_data.append({
                                'period': f"Period {i+1}",
                                'period_num': i + 1,
                                'projected_value': value_clean
                            })
                    except:
                        pass
        
        if forecast_data:
            df_forecast = pd.DataFrame(forecast_data)
            logger.info(f"Parsed {len(df_forecast)} forecast data points from AI response")
            return df_forecast
        
        return None
    
    def create_age_bins(self, column: str = None, bins: List[int] = None) -> pd.DataFrame:
        """
        Create age group bins from a numeric column.
        
        Args:
            column: Column name to bin (auto-detect if None)
            bins: Custom bin edges (default: [0, 18, 25, 35, 45, 55, 65, 100])
            
        Returns:
            DataFrame with age_group column added
        """
        # Auto-detect age column
        if column is None:
            age_candidates = ['age', 'Age', 'AGE', 'customer_age', 'user_age', 'respondent_age']
            for col in age_candidates:
                if col in self.columns:
                    column = col
                    break
            
            # If no obvious age column, look for numeric column with reasonable range
            if column is None:
                for col in self.numeric_columns:
                    col_lower = col.lower()
                    if 'age' in col_lower:
                        column = col
                        break
        
        if column is None or column not in self.columns:
            logger.warning(f"No age column found. Available: {self.columns}")
            return self.df
        
        # Default age bins
        if bins is None:
            bins = [0, 18, 25, 35, 45, 55, 65, 100]
        
        labels = []
        for i in range(len(bins) - 1):
            if bins[i+1] == 100:
                labels.append(f"{bins[i]}+")
            else:
                labels.append(f"{bins[i]}-{bins[i+1]-1}")
        
        df_copy = self.df.copy()
        df_copy['age_group'] = pd.cut(
            df_copy[column], 
            bins=bins, 
            labels=labels, 
            right=False
        )
        
        logger.info(f"Created age_group bins from '{column}': {labels}")
        return df_copy
    
    def create_price_bins(self, column: str = None, num_bins: int = 5) -> pd.DataFrame:
        """
        Create price range bins from a numeric column.
        
        Args:
            column: Column name to bin (auto-detect if None)
            num_bins: Number of bins to create
            
        Returns:
            DataFrame with price_range column added
        """
        # Auto-detect price column
        if column is None:
            price_candidates = ['price', 'Price', 'PRICE', 'amount', 'total', 'revenue', 'cost', 'value']
            for col in price_candidates:
                if col in self.columns:
                    column = col
                    break
            
            if column is None:
                for col in self.numeric_columns:
                    col_lower = col.lower()
                    if any(x in col_lower for x in ['price', 'amount', 'total', 'revenue', 'cost', 'value']):
                        column = col
                        break
        
        if column is None or column not in self.columns:
            logger.warning(f"No price column found. Available: {self.columns}")
            return self.df
        
        df_copy = self.df.copy()
        df_copy['price_range'] = pd.qcut(
            df_copy[column], 
            q=num_bins, 
            labels=[f"Range {i+1}" for i in range(num_bins)],
            duplicates='drop'
        )
        
        logger.info(f"Created price_range bins from '{column}'")
        return df_copy
    
    def create_date_bins(self, column: str = None, freq: str = 'M') -> pd.DataFrame:
        """
        Create date/time bins (daily, weekly, monthly, quarterly).
        
        Args:
            column: Date column to bin (auto-detect if None)
            freq: Frequency - 'D' (day), 'W' (week), 'M' (month), 'Q' (quarter)
            
        Returns:
            DataFrame with period column added
        """
        # Auto-detect date column
        if column is None:
            if self.date_columns:
                column = self.date_columns[0]
            else:
                date_candidates = ['date', 'Date', 'DATE', 'order_date', 'created_at', 'timestamp']
                for col in date_candidates:
                    if col in self.columns:
                        column = col
                        break
        
        if column is None or column not in self.columns:
            logger.warning(f"No date column found. Available: {self.columns}")
            return self.df
        
        df_copy = self.df.copy()
        
        # Ensure column is datetime
        if df_copy[column].dtype != 'datetime64[ns]':
            df_copy[column] = pd.to_datetime(df_copy[column])
        
        freq_names = {'D': 'day', 'W': 'week', 'M': 'month', 'Q': 'quarter'}
        freq_name = freq_names.get(freq, 'period')
        
        df_copy[freq_name] = df_copy[column].dt.to_period(freq).astype(str)
        
        logger.info(f"Created {freq_name} bins from '{column}'")
        return df_copy
    
    def auto_bin_for_query(self, query: str) -> Tuple[pd.DataFrame, str]:
        """
        Automatically detect what binning is needed based on the query.
        
        Args:
            query: User's natural language query
            
        Returns:
            Tuple of (modified dataframe, name of new column created)
        """
        query_lower = query.lower()
        
        # Age grouping
        if any(x in query_lower for x in ['age group', 'age bracket', 'by age', 'age range', 'age distribution']):
            df_binned = self.create_age_bins()
            if 'age_group' in df_binned.columns:
                return df_binned, 'age_group'
        
        # Price/value grouping
        if any(x in query_lower for x in ['price range', 'price bracket', 'by price', 'price distribution']):
            df_binned = self.create_price_bins()
            if 'price_range' in df_binned.columns:
                return df_binned, 'price_range'
        
        # Time grouping
        if any(x in query_lower for x in ['by month', 'monthly', 'per month']):
            df_binned = self.create_date_bins(freq='M')
            if 'month' in df_binned.columns:
                return df_binned, 'month'
        
        if any(x in query_lower for x in ['by week', 'weekly', 'per week']):
            df_binned = self.create_date_bins(freq='W')
            if 'week' in df_binned.columns:
                return df_binned, 'week'
        
        if any(x in query_lower for x in ['by quarter', 'quarterly', 'per quarter']):
            df_binned = self.create_date_bins(freq='Q')
            if 'quarter' in df_binned.columns:
                return df_binned, 'quarter'
        
        if any(x in query_lower for x in ['by day', 'daily', 'per day']):
            df_binned = self.create_date_bins(freq='D')
            if 'day' in df_binned.columns:
                return df_binned, 'day'
        
        # No binning needed
        return self.df, None
    
    def generate_chart_data(self, ai_response: str, query: str) -> Dict[str, Any]:
        """
        Main method: Generate chart-ready data from AI response and query.
        
        This is called when "Generate Chart from Insight" is clicked.
        
        Args:
            ai_response: The AI's text response
            query: The original user query
            
        Returns:
            Dict with:
            - 'df': DataFrame ready for charting
            - 'chart_type': Suggested chart type
            - 'x_column': Column for X axis
            - 'y_column': Column for Y axis
            - 'title': Chart title
            - 'source': 'parsed' if from AI text, 'binned' if from auto-binning, 'original' otherwise
        """
        result = {
            'df': None,
            'chart_type': 'bar',
            'x_column': None,
            'y_column': None,
            'title': 'Generated Chart',
            'source': 'original'
        }
        
        query_lower = query.lower()
        
        # Check for forecast/prediction queries
        if any(x in query_lower for x in ['forecast', 'predict', 'projection', 'next month', 'future', 'trend']):
            forecast_df = self.parse_forecast_from_text(ai_response)
            if forecast_df is not None and len(forecast_df) > 0:
                result['df'] = forecast_df
                result['x_column'] = 'period'
                result['y_column'] = 'projected_value'
                result['chart_type'] = 'line'
                result['title'] = 'Forecast Projection'
                result['source'] = 'parsed'
                logger.info(f"Generated forecast chart with {len(forecast_df)} data points")
                return result
        
        # Check if auto-binning is needed
        df_binned, new_column = self.auto_bin_for_query(query)
        if new_column:
            result['df'] = df_binned
            result['x_column'] = new_column
            result['source'] = 'binned'
            result['title'] = f'Distribution by {new_column.replace("_", " ").title()}'
            
            # Find appropriate y-column
            if any(x in query_lower for x in ['count', 'how many', 'number of']):
                result['y_column'] = None  # Will use count
                result['chart_type'] = 'bar'
            else:
                # Find a numeric column to aggregate
                for col in ['total_sales', 'revenue', 'amount', 'value', 'price', 'quantity']:
                    if col in df_binned.columns:
                        result['y_column'] = col
                        break
                if result['y_column'] is None and self.numeric_columns:
                    result['y_column'] = self.numeric_columns[0]
            
            logger.info(f"Generated binned chart: {new_column} vs {result['y_column']}")
            return result
        
        # Default: return original df
        result['df'] = self.df
        return result


def get_smart_chart_data(df: pd.DataFrame, ai_response: str, query: str) -> Dict[str, Any]:
    """
    Convenience function to generate chart data.
    
    Args:
        df: Original dataframe
        ai_response: AI's text response
        query: User's original query
        
    Returns:
        Chart data dict ready for visualization
    """
    generator = SmartChartGenerator(df)
    return generator.generate_chart_data(ai_response, query)
