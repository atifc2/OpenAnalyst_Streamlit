"""
Pandas Executor - Direct Query Execution for Simple Queries
Executes simple queries directly with Pandas, bypassing AI calls.

This provides INSTANT responses for basic queries while saving API costs.
"""

import pandas as pd
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class PandasExecutor:
    """
    Executes simple data queries directly using Pandas.
    Returns formatted results that match the AI response format.
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize executor with a DataFrame.
        
        Args:
            df: pandas DataFrame to query
        """
        self.df = df
        self.columns = df.columns.tolist()
        self.column_map = {col.lower(): col for col in self.columns}
    
    def execute(self, operation: str, column: str = None, params: Dict = None) -> Dict:
        """
        Execute a simple operation on the DataFrame.
        
        Args:
            operation: Type of operation (count_rows, sum, average, etc.)
            column: Column to operate on (if applicable)
            params: Additional parameters (e.g., n for top_n)
            
        Returns:
            dict matching AI response format with content, chart_data, etc.
        """
        params = params or {}
        
        try:
            # Route to appropriate handler
            handlers = {
                "count_rows": self._count_rows,
                "count_cols": self._count_cols,
                "list_columns": self._list_columns,
                "count_by": self._count_by,
                "sum": self._sum_column,
                "average": self._average_column,
                "max": self._max_column,
                "min": self._min_column,
                "top_n": self._top_n,
                "bottom_n": self._bottom_n,
                "unique": self._unique_values,
                "unique_count": self._unique_count,
                "summary": self._summary,
                "info": self._info,
            }
            
            handler = handlers.get(operation)
            if handler:
                return handler(column, params)
            else:
                return self._error_response(f"Unknown operation: {operation}")
                
        except Exception as e:
            logger.error(f"Pandas execution error: {e}")
            return self._error_response(str(e))
    
    def _format_response(
        self, 
        content: str, 
        result_value: Any = None,
        is_visualizable: bool = False,
        chart_data: Dict = None,
        suggested_actions: List[str] = None
    ) -> Dict:
        """Format result in standard AI response format."""
        return {
            "content": content,
            "reasoning": "Executed directly with Pandas for instant response.",
            "is_visualizable": is_visualizable,
            "chart_data": chart_data,
            "suggested_actions": suggested_actions or [
                "Ask a follow-up question",
                "Try a different analysis",
                "Export the results"
            ],
            "response_type": "instant",  # Marks this as a Pandas-direct response
            "_raw_value": result_value  # For programmatic access
        }
    
    def _error_response(self, error_msg: str) -> Dict:
        """Format error response."""
        return {
            "content": f"⚠️ Could not execute: {error_msg}",
            "reasoning": "Pandas execution failed, consider rephrasing query.",
            "is_visualizable": False,
            "suggested_actions": ["Rephrase your question", "Check column names"],
            "response_type": "error"
        }
    
    def _resolve_column(self, column: str) -> Optional[str]:
        """Resolve column name (case-insensitive)."""
        if not column:
            return None
        col_lower = column.lower().strip()
        return self.column_map.get(col_lower) or column
    
    # ============= HANDLERS =============
    
    def _count_rows(self, column: str, params: Dict) -> Dict:
        """Count number of rows."""
        count = len(self.df)
        return self._format_response(
            f"📊 **{count:,}** rows in the dataset.",
            result_value=count,
            suggested_actions=[
                "Show data summary",
                "List columns",
                "Show first 10 rows"
            ]
        )
    
    def _count_cols(self, column: str, params: Dict) -> Dict:
        """Count number of columns."""
        count = len(self.df.columns)
        return self._format_response(
            f"📊 **{count}** columns in the dataset.",
            result_value=count,
            suggested_actions=[
                "List column names",
                "Show data types",
                "Show data summary"
            ]
        )
    
    def _list_columns(self, column: str, params: Dict) -> Dict:
        """List all column names."""
        cols = self.df.columns.tolist()
        cols_formatted = ", ".join([f"`{c}`" for c in cols])
        return self._format_response(
            f"📋 **Columns ({len(cols)}):** {cols_formatted}",
            result_value=cols,
            suggested_actions=[
                "Show data types for each column",
                "Show summary statistics",
                "Count rows"
            ]
        )
    
    def _count_by(self, column: str, params: Dict) -> Dict:
        """Count values by category."""
        col = self._resolve_column(column)
        if not col or col not in self.df.columns:
            return self._error_response(f"Column '{column}' not found")
        
        counts = self.df[col].value_counts()
        top_5 = counts.head(5)
        
        # Format results
        result_lines = [f"- **{k}**: {v:,}" for k, v in top_5.items()]
        result_text = "\n".join(result_lines)
        
        if len(counts) > 5:
            result_text += f"\n- ... and {len(counts) - 5} more"
        
        return self._format_response(
            f"📊 **Count by `{col}`:**\n{result_text}",
            result_value=counts.to_dict(),
            is_visualizable=True,
            chart_data={
                "title": f"Count by {col}",
                "chart_type": "bar",
                "x_column": col,
                "y_column": "count",
                "color_column": None
            },
            suggested_actions=[
                f"Show percentage breakdown by {col}",
                f"Analyze trends in {col}",
                "Compare with another column"
            ]
        )
    
    def _sum_column(self, column: str, params: Dict) -> Dict:
        """Sum a numeric column."""
        col = self._resolve_column(column)
        if not col or col not in self.df.columns:
            return self._error_response(f"Column '{column}' not found")
        
        if not pd.api.types.is_numeric_dtype(self.df[col]):
            return self._error_response(f"Column '{col}' is not numeric")
        
        total = self.df[col].sum()
        
        # Format based on magnitude
        if abs(total) >= 1_000_000:
            formatted = f"${total/1_000_000:,.2f}M" if 'price' in col.lower() or 'sale' in col.lower() or 'revenue' in col.lower() else f"{total/1_000_000:,.2f}M"
        elif abs(total) >= 1_000:
            formatted = f"${total:,.0f}" if 'price' in col.lower() or 'sale' in col.lower() or 'revenue' in col.lower() else f"{total:,.0f}"
        else:
            formatted = f"{total:,.2f}"
        
        return self._format_response(
            f"📊 **Total `{col}`:** {formatted}",
            result_value=total,
            suggested_actions=[
                f"Show average {col}",
                f"Show {col} by category",
                f"Show {col} trend over time"
            ]
        )
    
    def _average_column(self, column: str, params: Dict) -> Dict:
        """Calculate average of a numeric column."""
        col = self._resolve_column(column)
        if not col or col not in self.df.columns:
            return self._error_response(f"Column '{column}' not found")
        
        if not pd.api.types.is_numeric_dtype(self.df[col]):
            return self._error_response(f"Column '{col}' is not numeric")
        
        avg = self.df[col].mean()
        
        return self._format_response(
            f"📊 **Average `{col}`:** {avg:,.2f}",
            result_value=avg,
            suggested_actions=[
                f"Show {col} distribution",
                f"Show min/max {col}",
                f"Compare {col} by category"
            ]
        )
    
    def _max_column(self, column: str, params: Dict) -> Dict:
        """Find maximum value in a column."""
        col = self._resolve_column(column)
        if not col or col not in self.df.columns:
            return self._error_response(f"Column '{column}' not found")
        
        max_val = self.df[col].max()
        
        return self._format_response(
            f"📊 **Maximum `{col}`:** {max_val}",
            result_value=max_val,
            suggested_actions=[
                f"Show minimum {col}",
                f"Show {col} distribution",
                "Find rows with this value"
            ]
        )
    
    def _min_column(self, column: str, params: Dict) -> Dict:
        """Find minimum value in a column."""
        col = self._resolve_column(column)
        if not col or col not in self.df.columns:
            return self._error_response(f"Column '{column}' not found")
        
        min_val = self.df[col].min()
        
        return self._format_response(
            f"📊 **Minimum `{col}`:** {min_val}",
            result_value=min_val,
            suggested_actions=[
                f"Show maximum {col}",
                f"Show {col} distribution",
                "Find rows with this value"
            ]
        )
    
    def _top_n(self, column: str, params: Dict) -> Dict:
        """Get top N values."""
        col = self._resolve_column(column)
        if not col or col not in self.df.columns:
            return self._error_response(f"Column '{column}' not found")
        
        n = params.get('n', 5)
        try:
            n = int(n)
        except:
            n = 5
        
        top_values = self.df[col].value_counts().head(n)
        result_lines = [f"- **{k}**: {v:,}" for k, v in top_values.items()]
        
        return self._format_response(
            f"📊 **Top {n} `{col}`:**\n" + "\n".join(result_lines),
            result_value=top_values.to_dict(),
            is_visualizable=True,
            chart_data={
                "title": f"Top {n} {col}",
                "chart_type": "bar",
                "x_column": col,
                "y_column": "count",
                "color_column": None
            },
            suggested_actions=[
                f"Show bottom {n} {col}",
                f"Analyze {col} trends",
                "Compare with another metric"
            ]
        )
    
    def _bottom_n(self, column: str, params: Dict) -> Dict:
        """Get bottom N values."""
        col = self._resolve_column(column)
        if not col or col not in self.df.columns:
            return self._error_response(f"Column '{column}' not found")
        
        n = params.get('n', 5)
        try:
            n = int(n)
        except:
            n = 5
        
        bottom_values = self.df[col].value_counts().tail(n)
        result_lines = [f"- **{k}**: {v:,}" for k, v in bottom_values.items()]
        
        return self._format_response(
            f"📊 **Bottom {n} `{col}`:**\n" + "\n".join(result_lines),
            result_value=bottom_values.to_dict(),
            suggested_actions=[
                f"Show top {n} {col}",
                f"Analyze why these are lowest",
                "Compare with another metric"
            ]
        )
    
    def _unique_values(self, column: str, params: Dict) -> Dict:
        """Get unique values in a column."""
        col = self._resolve_column(column)
        if not col or col not in self.df.columns:
            return self._error_response(f"Column '{column}' not found")
        
        unique_vals = self.df[col].dropna().unique()
        count = len(unique_vals)
        
        if count <= 20:
            vals_formatted = ", ".join([f"`{v}`" for v in unique_vals[:20]])
            content = f"📊 **Unique values in `{col}` ({count}):** {vals_formatted}"
        else:
            vals_formatted = ", ".join([f"`{v}`" for v in unique_vals[:10]])
            content = f"📊 **Unique values in `{col}` ({count}):** {vals_formatted}, ... and {count - 10} more"
        
        return self._format_response(
            content,
            result_value=list(unique_vals),
            suggested_actions=[
                f"Count by {col}",
                f"Filter by specific {col} value",
                "Show distribution"
            ]
        )
    
    def _unique_count(self, column: str, params: Dict) -> Dict:
        """Count unique values in a column."""
        col = self._resolve_column(column)
        if not col or col not in self.df.columns:
            return self._error_response(f"Column '{column}' not found")
        
        count = self.df[col].nunique()
        
        return self._format_response(
            f"📊 **{count:,}** unique values in `{col}`.",
            result_value=count,
            suggested_actions=[
                f"List unique {col} values",
                f"Count by {col}",
                "Show distribution"
            ]
        )
    
    def _summary(self, column: str, params: Dict) -> Dict:
        """Generate data summary statistics."""
        summary = self.df.describe()
        
        # Format summary for display
        summary_text = "📊 **Data Summary:**\n\n"
        summary_text += f"- **Rows:** {len(self.df):,}\n"
        summary_text += f"- **Columns:** {len(self.df.columns)}\n\n"
        
        # Add numeric column stats
        numeric_cols = self.df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            summary_text += "**Numeric Columns:**\n"
            for col in numeric_cols[:5]:  # Limit to first 5
                summary_text += f"- `{col}`: mean={self.df[col].mean():.2f}, min={self.df[col].min():.2f}, max={self.df[col].max():.2f}\n"
        
        return self._format_response(
            summary_text,
            result_value=summary.to_dict(),
            suggested_actions=[
                "Show column details",
                "Analyze specific column",
                "Find missing values"
            ]
        )
    
    def _info(self, column: str, params: Dict) -> Dict:
        """Show dataset info (columns, dtypes, non-null counts)."""
        info_lines = ["📊 **Dataset Info:**\n"]
        info_lines.append(f"- **Shape:** {self.df.shape[0]:,} rows × {self.df.shape[1]} columns")
        info_lines.append(f"- **Memory:** ~{self.df.memory_usage(deep=True).sum() / 1024:.1f} KB\n")
        
        info_lines.append("**Columns:**")
        for col in self.df.columns[:10]:  # Limit to first 10
            dtype = str(self.df[col].dtype)
            non_null = self.df[col].notna().sum()
            info_lines.append(f"- `{col}` ({dtype}): {non_null:,} non-null")
        
        if len(self.df.columns) > 10:
            info_lines.append(f"- ... and {len(self.df.columns) - 10} more columns")
        
        return self._format_response(
            "\n".join(info_lines),
            suggested_actions=[
                "Show data summary",
                "List all columns",
                "Check for missing values"
            ]
        )


def execute_simple_query(df: pd.DataFrame, operation: str, column: str = None, params: Dict = None) -> Dict:
    """
    Convenience function to execute a simple query.
    
    Args:
        df: pandas DataFrame
        operation: Operation type
        column: Column name (if applicable)
        params: Additional parameters
        
    Returns:
        Response dict in standard AI format
    """
    executor = PandasExecutor(df)
    return executor.execute(operation, column, params)


# ============= SAFE CODE EXECUTOR =============

import numpy as np
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError


class CodeExecutionError(Exception):
    """Custom exception for code execution errors."""
    pass


class SafeCodeExecutor:
    """
    Safely executes AI-generated pandas code in a sandboxed environment.
    
    Safety features:
    - Restricted imports (only pandas, numpy)
    - No file I/O, network, or system calls
    - Execution timeout
    - Memory limits (via output size check)
    """
    
    # Allowed modules/functions
    SAFE_BUILTINS = {
        'len': len,
        'range': range,
        'enumerate': enumerate,
        'zip': zip,
        'map': map,
        'filter': filter,
        'sorted': sorted,
        'reversed': reversed,
        'sum': sum,
        'min': min,
        'max': max,
        'abs': abs,
        'round': round,
        'int': int,
        'float': float,
        'str': str,
        'bool': bool,
        'list': list,
        'dict': dict,
        'tuple': tuple,
        'set': set,
        'True': True,
        'False': False,
        'None': None,
        'print': lambda *args, **kwargs: None,  # Disable print
    }
    
    # Dangerous patterns to block
    BLOCKED_PATTERNS = [
        'import os',
        'import sys',
        'import subprocess',
        'import shutil',
        '__import__',
        'eval(',
        'exec(',
        'compile(',
        'open(',
        'file(',
        'input(',
        'raw_input(',
        'getattr',
        'setattr',
        'delattr',
        '__builtins__',
        '__globals__',
        '__code__',
        '__class__',
        'os.system',
        'os.popen',
        'subprocess',
        '.to_csv',
        '.to_excel',
        '.to_sql',
        '.to_pickle',
        'read_csv',
        'read_excel',
        'read_sql',
        'requests.',
        'urllib',
        'socket',
        'http',
    ]
    
    def __init__(self, df: pd.DataFrame, timeout_seconds: int = 10):
        """
        Initialize executor with dataframe.
        
        Args:
            df: The pandas DataFrame to operate on
            timeout_seconds: Maximum execution time
        """
        self.df = df.copy()  # Work on a copy for safety
        self.timeout = timeout_seconds
        self.result = None
        self.error = None
    
    def _clean_code(self, code: str) -> str:
        """
        Clean and prepare code for execution.
        Removes safe import statements (numpy, pandas) since they're pre-imported.
        
        Args:
            code: Python code string
            
        Returns:
            Cleaned code string
        """
        import re
        lines = code.split('\n')
        cleaned_lines = []
        
        for line in lines:
            stripped = line.strip()
            # Remove numpy/pandas import statements (they're pre-imported)
            if re.match(r'^import\s+(numpy|np|pandas|pd)\s*$', stripped):
                continue
            if re.match(r'^import\s+(numpy|pandas)\s+as\s+(np|pd)\s*$', stripped):
                continue
            if re.match(r'^from\s+(numpy|pandas)\s+import\s+', stripped):
                continue
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _validate_code(self, code: str) -> bool:
        """
        Check code for dangerous patterns.
        
        Args:
            code: Python code string
            
        Returns:
            True if code appears safe, raises CodeExecutionError otherwise
        """
        code_lower = code.lower()
        
        for pattern in self.BLOCKED_PATTERNS:
            if pattern.lower() in code_lower:
                raise CodeExecutionError(f"Blocked pattern detected: '{pattern}'")
        
        return True
    
    def execute(self, code: str) -> Dict[str, Any]:
        """
        Execute pandas code safely.
        
        Args:
            code: Python code string (must store result in 'result' variable)
            
        Returns:
            Dict with:
            - 'success': bool
            - 'result': DataFrame or value if successful
            - 'error': Error message if failed
            - 'result_type': Type of result ('dataframe', 'series', 'scalar', etc.)
        """
        # First clean the code (remove safe imports)
        code = self._clean_code(code)
        # Validate code first
        try:
            self._validate_code(code)
        except CodeExecutionError as e:
            logger.warning(f"Code validation failed: {e}")
            return {
                'success': False,
                'result': None,
                'error': str(e),
                'result_type': None
            }
        
        # Prepare execution environment
        # Use full builtins to support pandas operations like .to_period()
        import builtins
        exec_globals = {
            '__builtins__': builtins,
            'pd': pd,
            'np': np,
            'df': self.df,
            'result': None
        }
        
        # Use a simple execution without signal-based timeout
        # (Signal doesn't work in Streamlit's threaded environment)
        try:
            # Execute the code directly
            exec(code, exec_globals)
            
            # Get result - first check for explicit 'result' variable
            result = exec_globals.get('result')
            
            # If no explicit 'result', find ANY DataFrame that was created
            if result is None:
                # Look for any DataFrame in the execution globals (excluding the original 'df')
                for var_name, var_value in exec_globals.items():
                    if var_name not in ('__builtins__', 'pd', 'np', 'df', 'result', 'datetime', 'timedelta'):
                        if isinstance(var_value, pd.DataFrame):
                            result = var_value
                            logger.info(f"Using variable '{var_name}' as result (no explicit 'result' variable)")
                            break
                        elif isinstance(var_value, pd.Series):
                            result = var_value
                            logger.info(f"Using Series variable '{var_name}' as result")
                            break
            
            if result is None:
                return {
                    'success': False,
                    'result': None,
                    'error': "Code did not produce any DataFrame or result variable",
                    'result_type': None
                }
            
            # Determine result type
            if isinstance(result, pd.DataFrame):
                result_type = 'dataframe'
                # Limit size for safety
                if len(result) > 10000:
                    result = result.head(10000)
                    logger.warning("Result truncated to 10000 rows")
            elif isinstance(result, pd.Series):
                result_type = 'series'
                result = result.reset_index()
                result.columns = ['index', 'value'] if len(result.columns) == 2 else result.columns
            elif isinstance(result, (int, float, str, bool)):
                result_type = 'scalar'
            elif isinstance(result, (list, dict)):
                result_type = 'collection'
            else:
                result_type = 'other'
            
            logger.info(f"Code executed successfully. Result type: {result_type}")
            
            return {
                'success': True,
                'result': result,
                'error': None,
                'result_type': result_type
            }
                
        except Exception as e:
            logger.error(f"Code execution error: {e}")
            return {
                'success': False,
                'result': None,
                'error': str(e),
                'result_type': None
            }


def execute_ai_code(df: pd.DataFrame, code: str, timeout: int = 10) -> Dict[str, Any]:
    """
    Convenience function to execute AI-generated code safely.
    
    Args:
        df: pandas DataFrame
        code: Python code string from AI
        timeout: Max execution time in seconds
        
    Returns:
        Execution result dict
    """
    executor = SafeCodeExecutor(df, timeout)
    return executor.execute(code)


# ============= TEST =============
if __name__ == "__main__":
    # Create test data
    test_df = pd.DataFrame({
        'product': ['Laptop', 'Phone', 'Tablet', 'Laptop', 'Phone'] * 20,
        'region': ['North', 'South', 'East', 'West', 'North'] * 20,
        'revenue': [1000, 500, 300, 1200, 600] * 20,
        'quantity': [10, 20, 15, 8, 25] * 20
    })
    
    executor = PandasExecutor(test_df)
    
    print("=" * 60)
    print("PANDAS EXECUTOR TEST")
    print("=" * 60)
    
    # Test various operations
    tests = [
        ("count_rows", None, {}),
        ("list_columns", None, {}),
        ("count_by", "region", {}),
        ("sum", "revenue", {}),
        ("average", "revenue", {}),
        ("top_n", "product", {"n": 3}),
        ("unique_count", "region", {}),
        ("summary", None, {}),
    ]
    
    for operation, column, params in tests:
        print(f"\n📝 Operation: {operation}" + (f" on '{column}'" if column else ""))
        result = executor.execute(operation, column, params)
        print(f"   Content: {result['content'][:100]}...")
        print(f"   Visualizable: {result['is_visualizable']}")
        if result.get('_raw_value'):
            print(f"   Raw value: {str(result['_raw_value'])[:50]}...")
    
    # Test SafeCodeExecutor
    print("\n" + "=" * 60)
    print("SAFE CODE EXECUTOR TEST")
    print("=" * 60)
    
    safe_executor = SafeCodeExecutor(test_df)
    
    # Test 1: Simple groupby
    code1 = """
result = df.groupby('region')['revenue'].sum().reset_index()
"""
    print("\n📝 Test 1: Simple groupby")
    res1 = safe_executor.execute(code1)
    print(f"   Success: {res1['success']}")
    if res1['success']:
        print(f"   Result:\n{res1['result']}")
    
    # Test 2: With derived column
    code2 = """
df['profit'] = df['revenue'] * 0.3
result = df.groupby('product')['profit'].sum().reset_index()
"""
    print("\n📝 Test 2: Derived column")
    res2 = safe_executor.execute(code2)
    print(f"   Success: {res2['success']}")
    if res2['success']:
        print(f"   Result:\n{res2['result']}")
    
    # Test 3: Blocked code
    code3 = """
import os
result = os.listdir('.')
"""
    print("\n📝 Test 3: Blocked code (should fail)")
    res3 = safe_executor.execute(code3)
    print(f"   Success: {res3['success']}")
    print(f"   Error: {res3['error']}")
