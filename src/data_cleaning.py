import pandas as pd


def clean_sales_data(raw_df):
    """
    Cleans raw retail sales data before analysis.
    Handles column formatting, invalid dates, duplicates,
    missing values, and impossible (negative) sales entries.
    Returns the cleaned DataFrame and a report of what was fixed.
    """
    df = raw_df.copy()
    report = {}

    # 1. Standardize column names
    df.columns = df.columns.str.strip().str.lower()

    # 2. Convert date column to real datetime, invalid dates become NaT
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    report['invalid_dates_found'] = int(df['date'].isnull().sum())

    # 3. Remove exact duplicate rows
    before = len(df)
    df = df.drop_duplicates()
    report['duplicates_removed'] = before - len(df)

    # 4. Drop rows with missing critical values
    before = len(df)
    df = df.dropna(subset=['date', 'store', 'item', 'sales'])
    report['missing_rows_dropped'] = before - len(df)

    # 5. Remove impossible values — sales can never be negative
    before = len(df)
    df = df[df['sales'] >= 0]
    report['negative_sales_removed'] = before - len(df)

    return df.reset_index(drop=True), report