from utils.ai_core import get_ai_response
import ast
import pandas as pd
import streamlit as st
from io import BytesIO
import json
import numpy as np

@st.cache_data
def read_and_clean_files(uploaded_files):
    """
    Reads and cleans uploaded CSV/Excel files.
    Returns a dict where keys are "filename|sheetname" and values are dicts with:
    - df: cleaned DataFrame
    - raw_df: original DataFrame before cleaning
    - junk_log: cleaning operations log
    - derived_columns: list of auto-generated column names
    """
    all_dfs = {}
    for uploaded_file in uploaded_files:
        try:
            if uploaded_file.name.endswith(".csv"):
                # Read CSV with error handling for different encodings
                try:
                    raw_df = pd.read_csv(uploaded_file, encoding='utf-8')
                except UnicodeDecodeError:
                    uploaded_file.seek(0)  # Reset file pointer
                    raw_df = pd.read_csv(uploaded_file, encoding='latin-1')
                
                # Track original columns
                original_columns = set(raw_df.columns)
                
                # Clean and derive
                cleaned_df, junk_log = clean_df(raw_df)
                cleaned_df = create_derived_columns(cleaned_df)
                
                # Identify derived columns
                derived_columns = list(set(cleaned_df.columns) - original_columns)
                
                all_dfs[f"{uploaded_file.name}|Sheet1"] = {
                    "df": cleaned_df,
                    "raw_df": raw_df,
                    "junk_log": junk_log,
                    "derived_columns": derived_columns
                }
                
            elif uploaded_file.name.endswith(".xlsx"):
                xls = pd.ExcelFile(uploaded_file)
                for sheet in xls.sheet_names:
                    raw_df = pd.read_excel(xls, sheet_name=sheet)
                    
                    # Track original columns
                    original_columns = set(raw_df.columns)
                    
                    # Clean and derive
                    cleaned_df, junk_log = clean_df(raw_df)
                    cleaned_df = create_derived_columns(cleaned_df)
                    
                    # Identify derived columns
                    derived_columns = list(set(cleaned_df.columns) - original_columns)
                    
                    all_dfs[f"{uploaded_file.name}|{sheet}"] = {
                        "df": cleaned_df,
                        "raw_df": raw_df,
                        "junk_log": junk_log,
                        "derived_columns": derived_columns
                    }
        except Exception as e:
            st.error(f"Failed to process {uploaded_file.name}: {e}")
            # Log the full error for debugging
            import traceback
            st.error(f"Full error: {traceback.format_exc()}")
    return all_dfs

# Check if columns are generic (all numbers, all unnamed, or empty)
def is_generic_header(cols):
    return all(
        str(col).strip().lower().startswith('unnamed')
        or str(col).strip() == ''
        or str(col).strip().isdigit()
        for col in cols
    )

def clean_df(df_raw, header_scan_rows=10):
    df = df_raw.copy()
    junk_log = {"dropped_rows": [], "dropped_columns": []}

    # Remove completely empty rows and columns first
    empty_rows = df.index[df.isnull().all(axis=1)].tolist()
    for i in empty_rows:
        junk_log["dropped_rows"].append((i, df.iloc[i].to_dict()))
    df = df.dropna(how='all')
    empty_cols = [col for col in df.columns if df[col].isnull().all()]
    for col in empty_cols:
        junk_log["dropped_columns"].append((col, df[col].tolist()))
    df = df.dropna(axis=1, how='all')

    if df.shape[0] == 0:
        return df, junk_log

    def header_score(row):
        non_empty = row.notna().sum()
        unique = row.nunique()
        header_keywords = ["date", "year", "value", "change", "p", "amount", "price"]
        header_like = sum(str(x).strip().lower() in header_keywords for x in row if pd.notna(x))
        long_text_penalty = sum(len(str(x)) > 20 for x in row if pd.notna(x))
        score = non_empty + unique + 2 * header_like - long_text_penalty
        return score

    def clean_colname(col):
        # Replace nan/None/empty with 'unnamed'
        if pd.isna(col) or str(col).strip() == "":
            return "unnamed"
        return str(col).strip()

    # --- Scan first N rows and pick the one with the highest score as header ---
    scan_limit = min(header_scan_rows, len(df))
    best_row = 0
    best_score = float('-inf')
    for i in range(scan_limit):
        score = header_score(df.iloc[i])
        if score > best_score:
            best_score = score
            best_row = i
    header_row = best_row

    if is_generic_header(df.columns):
        # Scan first N rows and pick the one with the highest score as header
        scan_limit = min(header_scan_rows, len(df))
        best_row = 0
        best_score = float('-inf')
        for i in range(scan_limit):
            score = header_score(df.iloc[i])
            if score > best_score:
                best_score = score
                best_row = i
        header_row = best_row

        # Set header from best row
        for i in range(header_row):
            junk_log["dropped_rows"].append((i, df.iloc[i].to_dict()))
        df.columns = [clean_colname(col) for col in df.iloc[header_row]]
        # Deduplicate columns
        seen = {}
        new_cols = []
        for col in df.columns:
            if col not in seen:
                seen[col] = 0
                new_cols.append(col)
            else:
                seen[col] += 1
                new_cols.append(f"{col}.{seen[col]}")
        df.columns = new_cols
        df = df.iloc[header_row + 1:].reset_index(drop=True)
    else:
        # Just clean and deduplicate column names, don't change header
        df.columns = [clean_colname(col) for col in df.columns]
        seen = {}
        new_cols = []
        for col in df.columns:
            if col not in seen:
                seen[col] = 0
                new_cols.append(col)
            else:
                seen[col] += 1
                new_cols.append(f"{col}.{seen[col]}")
        df.columns = new_cols

    # --- Drop columns starting with 'Unnamed:' (case-insensitive) ---
    unnamed_cols = [col for col in df.columns if str(col).strip().lower().startswith('unnamed:')]
    for col in unnamed_cols:
        junk_log["dropped_columns"].append((col, df[col].tolist()))
    df = df.drop(columns=unnamed_cols, errors='ignore')

    # --- Strip whitespace from all object/string columns ---
    for col in df.select_dtypes(include=['object', 'string']).columns:
        if isinstance(df[col], pd.Series):
            df[col] = df[col].astype(str).str.strip()

    try:
        df = df.convert_dtypes()
    except Exception:
        pass

    return df, junk_log

def get_clean_csv_download(df):
    """
    Converts a DataFrame to CSV format for download.
    """
    output = BytesIO()
    df.to_csv(output, index=False, encoding='utf-8')
    return output.getvalue()

def create_data_profile(df, df_key):
    """
    Creates a JSON profile of the DataFrame for the AI.
    Includes: filename, row/column counts, column info, and sample data.
    """
    try:
        # Get sample data with better handling of special types
        sample_data = df.head(3).to_dict(orient='records')
        
        # Build column info with more details
        columns_info = []
        for col in df.columns:
            col_info = {
                "name": col,
                "dtype": str(df[col].dtype),
                "non_null_count": int(df[col].notna().sum()),
                "unique_count": int(df[col].nunique())
            }
            
            # Add value range for numeric columns
            if pd.api.types.is_numeric_dtype(df[col]):
                col_info["min"] = float(df[col].min()) if pd.notna(df[col].min()) else None
                col_info["max"] = float(df[col].max()) if pd.notna(df[col].max()) else None
                col_info["mean"] = float(df[col].mean()) if pd.notna(df[col].mean()) else None
            
            # Mark derived columns for clarity
            if col in ['total_sale', 'month', 'year', 'month_name', 'invoice_date_month', 'invoice_date_year', 'invoice_date_month_name']:
                col_info["derived"] = True
            
            columns_info.append(col_info)
        
        profile = {
            "filename": df_key,
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": columns_info,
            "sample_data": sample_data
        }
        
        return json.dumps(profile, indent=2, default=str)
    
    except Exception as e:
        # Fallback to basic profile if detailed one fails
        st.warning(f"Could not create detailed profile: {e}")
        basic_profile = {
            "filename": df_key,
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": [{"name": col, "dtype": str(df[col].dtype)} for col in df.columns],
            "sample_data": []
        }
        return json.dumps(basic_profile, indent=2, default=str)

def create_derived_columns(df):
    """Automatically create common derived columns"""
    df_copy = df.copy()
    
    # Create total_sale if quantity and price exist
    if 'quantity' in df_copy.columns and 'price' in df_copy.columns:
        df_copy['total_sale'] = df_copy['quantity'] * df_copy['price']
    
    # Parse dates and create time-based columns
    date_columns = ['invoice_date', 'date', 'timestamp', 'created_at']
    for col in date_columns:
        if col in df_copy.columns:
            try:
                df_copy[col] = pd.to_datetime(df_copy[col], errors='coerce')
                # Create month, year, day columns
                df_copy[f'{col}_month'] = df_copy[col].dt.month
                df_copy[f'{col}_year'] = df_copy[col].dt.year
                df_copy[f'{col}_day'] = df_copy[col].dt.day
                df_copy[f'{col}_month_name'] = df_copy[col].dt.month_name()
                
                # For invoice_date specifically, create simplified names
                if col == 'invoice_date':
                    df_copy['month'] = df_copy[col].dt.month
                    df_copy['year'] = df_copy[col].dt.year
                    df_copy['month_name'] = df_copy[col].dt.month_name()
                    
            except Exception:
                continue
    
    return df_copy

def clean_dataframe(df):
    """Clean the dataframe by applying transformations"""
    df, _ = clean_df(df)
    df = create_derived_columns(df)
    return df