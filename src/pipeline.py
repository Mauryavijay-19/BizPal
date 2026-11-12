import os
from src.kpi import generate_price_table, compute_kpis
from src.inventory import generate_stock_levels, flag_inventory_status, apply_forecast_based_supply
from src.forecasting import predict_next_day_demand
from src.advisor import generate_recommendations


def generate_business_report(sales_df, models_dir='../models', reorder_threshold_days=5):
    """
    Runs the full BizPal pipeline end-to-end: pricing -> KPIs ->
    inventory status -> forecast-aware inventory -> recommendations.
    Takes a single store's cleaned daily sales data (item, date, sales)
    and returns everything a dashboard needs in one dict.

    Only items with a saved model in `models_dir` get forecast-aware
    treatment; all others gracefully fall back to historical average
    (see apply_forecast_based_supply).
    """
    items = sales_df['item'].unique()
    price_table = generate_price_table(items)
    kpi_data, kpi_summary = compute_kpis(sales_df, price_table)
    top_revenue_items = kpi_summary['top_products'].index.tolist()

    item_velocity = generate_stock_levels(sales_df)
    inventory_status = flag_inventory_status(item_velocity, reorder_threshold_days)

    forecasted_demand = {}
    for item_id in top_revenue_items:
        model_path = os.path.join(models_dir, f'item_{item_id}_model.pkl')
        if os.path.exists(model_path):
            item_df = sales_df[sales_df['item'] == item_id]
            forecasted_demand[item_id] = predict_next_day_demand(item_df, model_path)

    inventory_forecasted = apply_forecast_based_supply(
        inventory_status, forecasted_demand, reorder_threshold_days
    )

    recommendations = generate_recommendations(inventory_forecasted, top_revenue_items)

    return {
        'kpi_data': kpi_data,
        'kpi_summary': kpi_summary,
        'top_revenue_items': top_revenue_items,
        'inventory': inventory_forecasted,
        'recommendations': recommendations,
    }