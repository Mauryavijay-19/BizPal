import numpy as np


def generate_stock_levels(sales_df, seed=7, supply_range=(2, 25)):
    """
    Generates a realistic synthetic inventory layer grounded in each
    item's actual sales velocity, since live stock data is not
    publicly available in the source dataset.
    Returns a DataFrame with avg_daily_sales, days_of_supply_on_hand,
    and current_stock per item.
    """
    item_velocity = (sales_df.groupby('item')['sales']
                      .mean()
                      .reset_index()
                      .rename(columns={'sales': 'avg_daily_sales'}))

    np.random.seed(seed)
    item_velocity['days_of_supply_on_hand'] = np.random.uniform(
        supply_range[0], supply_range[1], size=len(item_velocity)
    ).round(1)
    item_velocity['current_stock'] = (
        item_velocity['avg_daily_sales'] * item_velocity['days_of_supply_on_hand']
    ).round().astype(int)

    return item_velocity


def flag_inventory_status(item_velocity_df, reorder_threshold_days=5):
    """
    Classifies each item's inventory status based on days of supply
    remaining, using a configurable reorder threshold (FR-09).
    """
    df = item_velocity_df.copy()

    def get_status(days_left):
        if days_left <= reorder_threshold_days:
            return 'Reorder Now'
        elif days_left <= reorder_threshold_days * 2:
            return 'Monitor'
        else:
            return 'Healthy'

    df['status'] = df['days_of_supply_on_hand'].apply(get_status)
    df['reorder_needed'] = df['status'] == 'Reorder Now'
    return df

def apply_forecast_based_supply(item_velocity_df, forecasted_demand_dict, reorder_threshold_days=5):
    """
    Recomputes days_of_supply_on_hand using forecasted (forward-looking)
    demand instead of historical average, for items where a forecast
    model is available. Falls back to historical average for the rest.
    """
    df = item_velocity_df.copy()
    df['forecasted_daily_demand'] = df['item'].map(forecasted_demand_dict)
    df['forecasted_daily_demand'] = df['forecasted_daily_demand'].fillna(df['avg_daily_sales'])

    df['days_of_supply_forecasted'] = (df['current_stock'] / df['forecasted_daily_demand']).round(1)

    def get_status(days_left):
        if days_left <= reorder_threshold_days:
            return 'Reorder Now'
        elif days_left <= reorder_threshold_days * 2:
            return 'Monitor'
        else:
            return 'Healthy'

    df['status_forecasted'] = df['days_of_supply_forecasted'].apply(get_status)
    df['reorder_needed_forecasted'] = df['status_forecasted'] == 'Reorder Now'

    return df