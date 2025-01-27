import pandas as pd
import streamlit as st
import plotly.express as px
import numpy as np

# Configure Streamlit page
st.set_page_config(page_title="Business Performance Dashboard", layout="wide")

# Load data
company_df = pd.read_csv("/Financials.csv")

# Preprocessing
# Strip leading/trailing spaces from column names
company_df.columns = company_df.columns.str.strip()

# Step 1: Correcting Data Types and Fixing the Year Column
# Convert 'Year' column to integer after rounding to fix any floating-point anomalies
company_df['Year'] = company_df['Year'].round().astype(int)

# Ensure 'Month Number' is an integer
company_df['Month Number'] = company_df['Month Number'].astype(int)

# Convert 'Date' to datetime format if not already done
company_df['Date'] = pd.to_datetime(company_df['Date'], errors='coerce')

# Step 2: Clean Numeric Columns
# List of columns that should be numeric
numeric_columns = ['Units Sold', 'Manufacturing Price', 'Sale Price', 'Gross Sales', 'Discounts', 'Sales', 'COGS', 'Profit']

# Replace common non-numeric strings with NaN or 0
for column in numeric_columns:
    if column in company_df.columns:
        company_df[column] = company_df[column].replace(
            {'\$': '', ',': '', '-': '', '': np.nan, 'N/A': np.nan, 'None': np.nan, '---': np.nan}, regex=True
        )

# Convert to numeric after cleaning
for column in numeric_columns:
    if column in company_df.columns:
        company_df[column] = pd.to_numeric(company_df[column], errors='coerce')

# Step 3: Data Validation
# Ensure no negative values in columns that should not be negative
for column in numeric_columns:
    if column in company_df.columns:
        if (company_df[column] < 0).any():
            print(f"Negative values found in {column}. Correcting them to zero.")
            company_df[column] = company_df[column].apply(lambda x: max(x, 0))
    else:
        print(f"Column '{column}' not found in DataFrame.")

# Recalculate Profit for rows where it is currently NaN
company_df['Profit'] = company_df.apply(
    lambda row: row['Sales'] - row['COGS'] if pd.isna(row['Profit']) else row['Profit'],
    axis=1
)

# Check if any NaNs remain in the Profit column
nan_summary_after_fix = company_df['Profit'].isna().sum()

# Step 4: Handle Outliers
# Function to detect outliers using the IQR method
def detect_outliers(company_df, columns):
    outliers = {}
    for column in columns:
        Q1 = company_df[column].quantile(0.25)
        Q3 = company_df[column].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        outliers[column] = company_df[(company_df[column] < lower_bound) | (company_df[column] > upper_bound)]
    return outliers

# Detect outliers in numeric columns
outliers = detect_outliers(company_df, numeric_columns)

# Handle outliers by capping them to the IQR range
for column in numeric_columns:
    Q1 = company_df[column].quantile(0.25)
    Q3 = company_df[column].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    company_df[column] = np.where(company_df[column] < lower_bound, lower_bound, company_df[column])
    company_df[column] = np.where(company_df[column] > upper_bound, upper_bound, company_df[column])

# Dashboard Title
st.title("Business Performance Dashboard")

# Metrics
total_sales = company_df["Sales"].sum()
total_profit = company_df["Profit"].sum()
total_discounts = company_df["Discounts"].sum()

col1, col2, col3 = st.columns(3)
col1.metric("Total Sales", f"${total_sales:,.2f}")
col2.metric("Total Profit", f"${total_profit:,.2f}")
col3.metric("Total Discounts", f"${total_discounts:,.2f}")

# Sales and Profit by Month
st.subheader("Sales and Profit Trends by Month")
monthly_data = company_df.groupby(["Year", "Month Number", "Month Name"]).agg(
    {"Sales": "sum", "Profit": "sum"}
).reset_index()
monthly_data = monthly_data.sort_values(by=["Year", "Month Number"])

fig = px.line(
    monthly_data,
    x="Month Name",
    y=["Sales", "Profit"],
    color="Year",
    labels={"value": "Amount ($)", "Month Name": "Month"},
    title="Monthly Sales and Profit Trends",
)
st.plotly_chart(fig, use_container_width=True)

# Segment Analysis
st.subheader("Performance by Segment")
segment_data = company_df.groupby("Segment").agg(
    {"Sales": "sum", "Profit": "sum", "Discounts": "sum"}
).reset_index()
fig_segment = px.bar(
    segment_data,
    x="Segment",
    y=["Sales", "Profit", "Discounts"],
    barmode="group",
    labels={"value": "Amount ($)", "Segment": "Business Segment"},
    title="Sales, Profit, and Discounts by Segment",
)
st.plotly_chart(fig_segment, use_container_width=True)

# Country Analysis
st.subheader("Performance by Country")
country_data = company_df.groupby("Country").agg({"Sales": "sum", "Profit": "sum"}).reset_index()
fig_country = px.choropleth(
    country_data,
    locations="Country",
    locationmode="country names",
    color="Sales",
    hover_name="Country",
    title="Total Sales by Country",
    color_continuous_scale="Viridis",
)
st.plotly_chart(fig_country, use_container_width=True)

# Product Analysis
st.subheader("Top Performing Products")
product_data = company_df.groupby("Product").agg({"Sales": "sum", "Profit": "sum"}).reset_index()
top_products = product_data.nlargest(10, "Sales")
fig_product = px.bar(
    top_products,
    x="Product",
    y="Sales",
    color="Profit",
    labels={"Sales": "Sales ($)", "Product": "Product Name"},
    title="Top 10 Products by Sales",
)
st.plotly_chart(fig_product, use_container_width=True)

# Raw Data Table
st.subheader("Raw Data")
st.dataframe(company_df)
