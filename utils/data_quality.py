"""
Data quality analysis and scoring module
Provides comprehensive data quality metrics and comparisons
"""

import pandas as pd
import numpy as np

def format_memory_size(bytes_size):
    """Convert bytes to human-readable format (KB, MB, GB)"""
    if bytes_size < 1024:
        return f"{bytes_size} B"
    elif bytes_size < 1024 ** 2:
        kb = bytes_size / 1024
        return f"{kb:.1f} KB"
    elif bytes_size < 1024 ** 3:
        mb = bytes_size / (1024 ** 2)
        kb = bytes_size / 1024
        return f"{mb:.1f} MB ({kb:,.0f} KB)"
    else:
        gb = bytes_size / (1024 ** 3)
        mb = bytes_size / (1024 ** 2)
        return f"{gb:.2f} GB ({mb:,.1f} MB)"

def calculate_data_quality_score(raw_df, cleaned_df, derived_columns=None):
    """
    Calculate comprehensive data quality score (0-100)
    
    Args:
        raw_df: Original dataframe before cleaning
        cleaned_df: Cleaned dataframe after processing
        derived_columns: List of column names that were auto-generated
    
    Returns:
        dict with overall score and component breakdowns
    """
    if derived_columns is None:
        derived_columns = []
    
    # Component 1: Completeness (30% weight)
    raw_missing = raw_df.isnull().sum().sum()
    cleaned_missing = cleaned_df.isnull().sum().sum()
    total_cells = raw_df.shape[0] * raw_df.shape[1]
    
    if total_cells > 0:
        completeness = ((total_cells - cleaned_missing) / total_cells) * 100
    else:
        completeness = 100
    
    # Component 2: Uniqueness (25% weight)
    raw_duplicates = raw_df.duplicated().sum()
    cleaned_duplicates = cleaned_df.duplicated().sum()
    
    if raw_df.shape[0] > 0:
        uniqueness = ((cleaned_df.shape[0] - cleaned_duplicates) / cleaned_df.shape[0]) * 100
    else:
        uniqueness = 100
    
    # Component 3: Validity (25% weight)
    # Check for outliers using IQR method
    numeric_cols = cleaned_df.select_dtypes(include=[np.number]).columns
    outlier_count = 0
    total_numeric_values = 0
    
    for col in numeric_cols:
        if col not in derived_columns:  # Don't penalize derived columns
            Q1 = cleaned_df[col].quantile(0.25)
            Q3 = cleaned_df[col].quantile(0.75)
            IQR = Q3 - Q1
            outliers = ((cleaned_df[col] < (Q1 - 3 * IQR)) | (cleaned_df[col] > (Q3 + 3 * IQR))).sum()
            outlier_count += outliers
            total_numeric_values += cleaned_df[col].notna().sum()
    
    if total_numeric_values > 0:
        validity = (1 - (outlier_count / total_numeric_values)) * 100
    else:
        validity = 100
    
    # Component 4: Consistency (20% weight)
    # Check for column naming, text case, etc.
    consistency_score = 100
    
    # Penalize for inconsistent column naming
    has_spaces = sum(1 for col in cleaned_df.columns if ' ' in str(col))
    mixed_case = sum(1 for col in cleaned_df.columns if not str(col).islower() and not str(col).isupper())
    
    if len(cleaned_df.columns) > 0:
        consistency_score -= (has_spaces / len(cleaned_df.columns)) * 50
        consistency_score -= (mixed_case / len(cleaned_df.columns)) * 50
    
    consistency_score = max(0, consistency_score)
    
    # Bonus: Enrichment (added value through derived columns)
    enrichment_bonus = min(len(derived_columns), 5)  # Max +5 points
    
    # Calculate weighted final score
    final_score = (
        completeness * 0.30 +
        uniqueness * 0.25 +
        validity * 0.25 +
        consistency_score * 0.20
    ) + enrichment_bonus
    
    final_score = min(100, max(0, final_score))  # Clamp to 0-100
    
    return {
        'overall_score': round(final_score, 1),
        'components': {
            'completeness': {
                'score': round(completeness, 1),
                'weight': 30,
                'details': {
                    'raw_missing': int(raw_missing),
                    'cleaned_missing': int(cleaned_missing),
                    'cells_filled': int(raw_missing - cleaned_missing)
                }
            },
            'uniqueness': {
                'score': round(uniqueness, 1),
                'weight': 25,
                'details': {
                    'raw_duplicates': int(raw_duplicates),
                    'cleaned_duplicates': int(cleaned_duplicates),
                    'duplicates_removed': int(raw_duplicates - cleaned_duplicates)
                }
            },
            'validity': {
                'score': round(validity, 1),
                'weight': 25,
                'details': {
                    'outliers_detected': int(outlier_count),
                    'numeric_values': int(total_numeric_values),
                    'outlier_percentage': round((outlier_count / total_numeric_values * 100) if total_numeric_values > 0 else 0, 2)
                }
            },
            'consistency': {
                'score': round(consistency_score, 1),
                'weight': 20,
                'details': {
                    'columns_with_spaces': int(has_spaces),
                    'mixed_case_columns': int(mixed_case),
                    'total_columns': len(cleaned_df.columns)
                }
            }
        },
        'enrichment_bonus': enrichment_bonus,
        'derived_columns_count': len(derived_columns)
    }

def get_cleaning_stats(raw_df, cleaned_df):
    """
    Compare raw and cleaned dataframes
    
    Returns:
        dict with before/after statistics
    """
    raw_memory = raw_df.memory_usage(deep=True).sum()
    cleaned_memory = cleaned_df.memory_usage(deep=True).sum()
    
    return {
        'rows': {
            'before': raw_df.shape[0],
            'after': cleaned_df.shape[0],
            'change': cleaned_df.shape[0] - raw_df.shape[0],
            'change_pct': round(((cleaned_df.shape[0] - raw_df.shape[0]) / raw_df.shape[0] * 100) if raw_df.shape[0] > 0 else 0, 2)
        },
        'columns': {
            'before': raw_df.shape[1],
            'after': cleaned_df.shape[1],
            'change': cleaned_df.shape[1] - raw_df.shape[1],
            'change_pct': round(((cleaned_df.shape[1] - raw_df.shape[1]) / raw_df.shape[1] * 100) if raw_df.shape[1] > 0 else 0, 2)
        },
        'missing': {
            'before': int(raw_df.isnull().sum().sum()),
            'after': int(cleaned_df.isnull().sum().sum()),
            'change': int(cleaned_df.isnull().sum().sum() - raw_df.isnull().sum().sum()),
            'change_pct': round(((cleaned_df.isnull().sum().sum() - raw_df.isnull().sum().sum()) / raw_df.isnull().sum().sum() * 100) if raw_df.isnull().sum().sum() > 0 else 0, 2)
        },
        'duplicates': {
            'before': int(raw_df.duplicated().sum()),
            'after': int(cleaned_df.duplicated().sum()),
            'change': int(cleaned_df.duplicated().sum() - raw_df.duplicated().sum()),
            'change_pct': round(((cleaned_df.duplicated().sum() - raw_df.duplicated().sum()) / raw_df.duplicated().sum() * 100) if raw_df.duplicated().sum() > 0 else 0, 2)
        },
        'memory': {
            'before': raw_memory,
            'after': cleaned_memory,
            'change': cleaned_memory - raw_memory,
            'change_pct': round(((cleaned_memory - raw_memory) / raw_memory * 100) if raw_memory > 0 else 0, 2),
            'before_formatted': format_memory_size(raw_memory),
            'after_formatted': format_memory_size(cleaned_memory)
        }
    }

def get_star_rating(score):
    """Convert score to star rating"""
    if score >= 90:
        return "⭐⭐⭐⭐⭐"
    elif score >= 75:
        return "⭐⭐⭐⭐"
    elif score >= 60:
        return "⭐⭐⭐"
    elif score >= 40:
        return "⭐⭐"
    else:
        return "⭐"

def identify_derived_columns(raw_df, cleaned_df):
    """
    Identify columns that were auto-generated during cleaning
    
    Returns:
        list of dicts with column name and derivation logic
    """
    derived = []
    raw_cols = set(raw_df.columns)
    cleaned_cols = set(cleaned_df.columns)
    
    new_cols = cleaned_cols - raw_cols
    
    for col in new_cols:
        derivation = {'name': col, 'logic': 'Unknown derivation', 'source_columns': []}
        
        # Check for common patterns
        if 'total' in col.lower() or 'sum' in col.lower():
            # Look for multiplication patterns (quantity * price)
            possible_sources = [c for c in raw_cols if any(word in c.lower() for word in ['quantity', 'qty', 'price', 'rate', 'amount'])]
            if len(possible_sources) >= 2:
                derivation['logic'] = f"Calculated from {' × '.join(possible_sources[:2])}"
                derivation['source_columns'] = possible_sources[:2]
        
        elif col.lower() in ['month', 'year', 'quarter', 'day', 'day_of_week', 'weekday']:
            # Date-derived columns
            date_cols = [c for c in raw_cols if 'date' in c.lower() or 'time' in c.lower()]
            if date_cols:
                derivation['logic'] = f"Extracted from {date_cols[0]}"
                derivation['source_columns'] = [date_cols[0]]
        
        elif 'category' in col.lower() or 'group' in col.lower() or 'segment' in col.lower():
            # Categorization
            derivation['logic'] = "Categorical grouping applied"
        
        derived.append(derivation)
    
    return derived
