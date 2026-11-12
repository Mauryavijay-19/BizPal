import numpy as np
import pandas as pd


def generate_price_table(items, seed=42, price_range=(10 , 70), margin_range=(0.6, 0.8)):
    """
    Generates a synthetic but realistic price table for a list of items,
    since public retail datasets rarely include real pricing data.
    Returns a DataFrame with columns: item, price, cost.
    """
    np.random.seed(seed)
    price_table = pd.DataFrame({
        'item': sorted(items),
        'price': np.random.uniform(price_range[0], price_range[1], size=len(items)).round(2)
    })
    price_table['cost'] = (
        price_table['price'] * np.random.uniform(margin_range[0], margin_range[1], size=len(items))
    ).round(2)
    return price_table


def compute_kpis(sales_df, price_table):
    """
    Merges cleaned sales data with item pricing and computes
    revenue, profit, and top-performing products.
    Returns the enriched DataFrame and a summary dict of KPIs.
    """
    merged = sales_df.merge(price_table, on='item', how='left')
    merged['revenue'] = merged['sales'] * merged['price']
    merged['profit'] = merged['sales'] * (merged['price'] - merged['cost'])

    top_products = (merged.groupby('item')['revenue']
                    .sum()
                    .sort_values(ascending=False)
                    .head(5))

    summary = {
        'total_revenue': merged['revenue'].sum(),
        'total_profit': merged['profit'].sum(),
        'top_products': top_products,
    }
    return merged, summary