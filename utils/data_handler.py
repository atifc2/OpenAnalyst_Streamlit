import pandas as pd
import streamlit as st
from io import BytesIO
import json

@st.cache_data
def read_and_clean_files(uploaded_files):
    """
    Reads and cleans uploaded CSV/Excel files.
    Returns a dict where keys are "filename|sheetname" and values are cleaned DataFrames.
    """
    all_dfs = {}
    for uploaded_file in uploaded_files:
        try:
            if uploaded_file.name.endswith(".csv"):
                # Read CSV with error handling for different encodings
                try:
                    df = pd.read_csv(uploaded_file, encoding='utf-8')
                except UnicodeDecodeError:
                    uploaded_file.seek(0)  # Reset file pointer
                    df = pd.read_csv(uploaded_file, encoding='latin-1')
                
                all_dfs[f"{uploaded_file.name}|Sheet1"] = clean_df(df)
                
            elif uploaded_file.name.endswith(".xlsx"):
                xls = pd.ExcelFile(uploaded_file)
                for sheet in xls.sheet_names:
                    df = pd.read_excel(xls, sheet_name=sheet)
                    all_dfs[f"{uploaded_file.name}|{sheet}"] = clean_df(df)
        except Exception as e:
            st.error(f"Failed to process {uploaded_file.name}: {e}")
            # Log the full error for debugging
            import traceback
            st.error(f"Full error: {traceback.format_exc()}")
    
    return all_dfs

def clean_df(df_raw):
    """
    Cleans a raw DataFrame:
    - Removes completely empty rows and columns
    - Strips whitespace from column names
    - Converts to appropriate dtypes
    """
    df = df_raw.copy()
    
    # Remove empty rows and columns
    df = df.dropna(how='all').dropna(axis=1, how='all')
    
    # Clean column names
    df.columns = [str(col).strip() for col in df.columns]
    
    # Convert dtypes (but catch errors if it fails)
    try:
        df = df.convert_dtypes()
    except Exception as e:
        st.warning(f"Could not auto-convert data types: {e}")
        # Continue with original types
    
    return df

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