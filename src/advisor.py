def generate_recommendations(inventory_df, top_revenue_items,
                              status_col='status_forecasted',
                              days_col='days_of_supply_forecasted',
                              demand_col='forecasted_daily_demand',
                              avg_col='avg_daily_sales'):
    """
    Generates plain-language, prioritized recommendations by combining
    forecast-aware inventory status with revenue importance.
    Returns a list of dicts, sorted High -> Medium -> Low priority.
    """
    recommendations = []

    for _, row in inventory_df.iterrows():
        item = row['item']
        status = row[status_col]
        days_left = row[days_col]
        is_top_revenue = item in top_revenue_items
        demand_trend = 'rising' if row[demand_col] > row[avg_col] else 'easing'

        if status == 'Reorder Now':
            priority = 'High'
            message = f"Item {item}: only {days_left} days of stock left — reorder now."
            if is_top_revenue:
                message += " This is a top revenue driver, so a stockout here has high business impact."

        elif status == 'Monitor':
            priority = 'Medium'
            message = f"Item {item}: stock is moderate ({days_left} days left), demand is {demand_trend}."
            if is_top_revenue:
                message += " Keep a closer eye on it since it's a top revenue product."

        else:  # Healthy
            priority = 'Low'
            message = f"Item {item}: stock is healthy ({days_left} days left)."
            if is_top_revenue and demand_trend == 'rising':
                message += " Demand is trending up for this top revenue product — consider a larger reorder buffer next cycle."

        recommendations.append({
            'item': item,
            'priority': priority,
            'status': status,
            'message': message
        })

    priority_order = {'High': 0, 'Medium': 1, 'Low': 2}
    recommendations.sort(key=lambda r: priority_order[r['priority']])
    return recommendations