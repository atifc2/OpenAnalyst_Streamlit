"""
Generate realistic sample datasets for Open Analyst MVP demo
Includes intentional data quality issues for showcasing cleaning features
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

np.random.seed(42)

# Sample 1: E-commerce Sales Data (with data quality issues)
print("Creating E-commerce Sales dataset...")
dates = pd.date_range(start='2023-01-01', end='2024-10-31', freq='D')
n_records = 650

sales_data = pd.DataFrame({
    'date': np.random.choice(dates, n_records),
    'order_id': [f'ORD{str(i).zfill(6)}' for i in range(1, n_records + 1)],
    'product': np.random.choice(['Laptop', 'Phone', 'Tablet', 'Watch', 'Headphones', 'Camera'], n_records),
    'category': np.random.choice(['Electronics', 'Accessories', 'Wearables'], n_records),
    'quantity': np.random.randint(1, 10, n_records),
    'price': np.random.choice([299, 699, 999, 1299, 149, 899], n_records),
    'region': np.random.choice(['North', 'South', 'East', 'West'], n_records),
    'customer_type': np.random.choice(['New', 'Returning', 'VIP'], n_records),
    'payment_method': np.random.choice(['Credit Card', 'PayPal', 'Debit Card', 'Bank Transfer'], n_records),
})

# Add calculated column
sales_data['total_sale'] = sales_data['quantity'] * sales_data['price']

# Add discount with some NaN values (data quality issue)
sales_data['discount_percent'] = np.random.choice([0, 5, 10, 15, 20, np.nan], n_records, p=[0.4, 0.2, 0.15, 0.1, 0.05, 0.1])

# Add shipping cost with outliers
sales_data['shipping_cost'] = np.random.choice([0, 5, 10, 15, 999], n_records, p=[0.1, 0.3, 0.3, 0.2, 0.1])  # 999 is outlier

# Add some duplicate order_ids (data quality issue)
sales_data.loc[10:15, 'order_id'] = 'ORD000005'

# Add some empty category values
sales_data.loc[50:55, 'category'] = ''

# Sort by date
sales_data = sales_data.sort_values('date').reset_index(drop=True)

sales_data.to_csv('sample_ecommerce_sales.csv', index=False)
print(f"✅ Created sample_ecommerce_sales.csv ({len(sales_data)} rows)")
print(f"   Issues: {sales_data['discount_percent'].isna().sum()} missing discounts, "
      f"{(sales_data['shipping_cost'] == 999).sum()} outlier shipping costs, "
      f"{sales_data.duplicated(subset=['order_id']).sum()} duplicate order IDs")

# Sample 2: Customer Survey Data (with data quality issues)
print("\nCreating Customer Survey dataset...")
n_customers = 800

survey_data = pd.DataFrame({
    'customer_id': [f'CUST{str(i).zfill(5)}' for i in range(1, n_customers + 1)],
    'age': np.random.randint(18, 75, n_customers),
    'gender': np.random.choice(['Male', 'Female', 'Other', 'Prefer not to say'], n_customers),
    'satisfaction_score': np.random.randint(1, 6, n_customers),  # 1-5 scale
    'nps_score': np.random.randint(0, 11, n_customers),  # 0-10 scale
    'product_quality': np.random.randint(1, 6, n_customers),
    'customer_service': np.random.randint(1, 6, n_customers),
    'delivery_speed': np.random.randint(1, 6, n_customers),
    'value_for_money': np.random.randint(1, 6, n_customers),
    'would_recommend': np.random.choice(['Yes', 'No', 'Maybe'], n_customers),
    'purchase_frequency': np.random.choice(['Daily', 'Weekly', 'Monthly', 'Quarterly', 'Rarely'], n_customers),
    'total_purchases': np.random.randint(1, 50, n_customers),
})

# Add some impossible ages (data quality issue)
survey_data.loc[20:25, 'age'] = np.random.choice([0, -5, 150], 6)

# Add missing NPS scores
survey_data.loc[100:150, 'nps_score'] = np.nan

# Add inconsistent text formatting
survey_data.loc[200:210, 'would_recommend'] = survey_data.loc[200:210, 'would_recommend'].str.lower()

# Add some extreme outliers in total_purchases
survey_data.loc[300:305, 'total_purchases'] = np.random.randint(1000, 5000, 6)

survey_data.to_csv('sample_customer_survey.csv', index=False)
print(f"✅ Created sample_customer_survey.csv ({len(survey_data)} rows)")
print(f"   Issues: {(survey_data['age'] <= 0).sum() + (survey_data['age'] > 120).sum()} invalid ages, "
      f"{survey_data['nps_score'].isna().sum()} missing NPS scores, "
      f"{(survey_data['total_purchases'] > 100).sum()} outlier purchase counts")

# Sample 3: Financial Metrics (with data quality issues)
print("\nCreating Financial Metrics dataset...")
months = pd.date_range(start='2022-01-01', end='2024-10-31', freq='M')
n_months = len(months)

financial_data = pd.DataFrame({
    'month': months,
    'revenue': np.random.randint(80000, 180000, n_months),
    'expenses': np.random.randint(40000, 100000, n_months),
    'marketing_spend': np.random.randint(8000, 30000, n_months),
    'customer_acquisition': np.random.randint(150, 600, n_months),
    'churn_rate': np.random.uniform(2.5, 8.5, n_months),
    'employee_count': np.random.randint(50, 150, n_months),
    'support_tickets': np.random.randint(200, 800, n_months),
})

# Calculate derived metrics
financial_data['profit'] = financial_data['revenue'] - financial_data['expenses']
financial_data['profit_margin'] = (financial_data['profit'] / financial_data['revenue'] * 100).round(2)
financial_data['cac'] = (financial_data['marketing_spend'] / financial_data['customer_acquisition']).round(2)

# Add some negative revenue (data quality issue)
financial_data.loc[5:7, 'revenue'] = -50000

# Add missing marketing spend
financial_data.loc[15:18, 'marketing_spend'] = np.nan

# Add impossible churn rate (> 100%)
financial_data.loc[25:27, 'churn_rate'] = np.random.uniform(110, 150, 3)

# Add sudden spike in support tickets (potential issue)
financial_data.loc[20, 'support_tickets'] = 5000

financial_data.to_csv('sample_financial_metrics.csv', index=False)
print(f"✅ Created sample_financial_metrics.csv ({len(financial_data)} rows)")
print(f"   Issues: {(financial_data['revenue'] < 0).sum()} negative revenue entries, "
      f"{financial_data['marketing_spend'].isna().sum()} missing marketing spend, "
      f"{(financial_data['churn_rate'] > 100).sum()} impossible churn rates")

print("\n" + "="*60)
print("✅ All 3 sample datasets created successfully!")
print("="*60)
print("\nDatasets include realistic data quality issues:")
print("  • Missing values (NaN)")
print("  • Outliers and anomalies")
print("  • Duplicate records")
print("  • Invalid values (negative, impossible ranges)")
print("  • Inconsistent formatting")
print("\nThese showcase Open Analyst's data cleaning capabilities!")
