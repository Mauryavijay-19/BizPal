import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error


def build_features(daily_df, date_col='date', target_col='sales'):
    """
    Engineers time-based features (day-of-week, month, lag-7,
    rolling 7-day average) needed for sales forecasting.
    Drops rows where these features can't yet be computed.
    """
    df = daily_df.sort_values(date_col).copy()
    df['dayofweek'] = df[date_col].dt.dayofweek
    df['month'] = df[date_col].dt.month
    df['lag_7'] = df[target_col].shift(7)
    df['rolling_mean_7'] = df[target_col].rolling(window=7).mean()
    return df.dropna().reset_index(drop=True)


def train_forecast_model(featured_df, date_col='date', target_col='sales', split_date='2017-01-01'):
    """
    Trains a Random Forest Regressor on engineered features using a
    chronological train/test split, and evaluates it against a naive
    lag-7 baseline. Returns the trained model and a metrics summary.
    """
    features = ['dayofweek', 'month', 'lag_7', 'rolling_mean_7']

    train = featured_df[featured_df[date_col] < split_date]
    test = featured_df[featured_df[date_col] >= split_date]

    X_train, y_train = train[features], train[target_col]
    X_test, y_test = test[features], test[target_col]

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))

    baseline_mae = mean_absolute_error(y_test, test['lag_7'])
    improvement = round((1 - mae / baseline_mae) * 100, 2)

    metrics = {
        'mae': mae,
        'rmse': rmse,
        'baseline_mae': baseline_mae,
        'improvement_pct': improvement,
        'test_size': len(test),
    }
    return model, metrics

def predict_next_day_demand(daily_item_df, model_path, date_col='date', target_col='sales'):
    """
    Predicts next-day demand for a single item using its saved
    forecasting model. Builds one feature row from the most recent
    known data (lag_7, rolling_mean_7) and predicts forward.
    """
    df = daily_item_df.sort_values(date_col).copy()

    last_date = df[date_col].max()
    next_date = last_date + pd.Timedelta(days=1)

    lag_7 = df[df[date_col] == last_date - pd.Timedelta(days=6)][target_col].values[0]
    rolling_mean_7 = df[target_col].tail(7).mean()

    features = pd.DataFrame({
        'dayofweek': [next_date.dayofweek],
        'month': [next_date.month],
        'lag_7': [lag_7],
        'rolling_mean_7': [rolling_mean_7]
    })

    model = joblib.load(model_path)
    predicted_demand = model.predict(features)[0]

    return round(predicted_demand, 2)


##Gradient Boosting Regressor version of the model training function
def _time_based_split(featured_df, date_col, target_col, split_date, features):
    """
    Splits chronologically: everything before split_date is training data,
    everything from split_date onward is test data. Never shuffled, to
    avoid leaking future information into training.
    """
    train = featured_df[featured_df[date_col] < split_date]
    test = featured_df[featured_df[date_col] >= split_date]
    return train[features], train[target_col], test[features], test[target_col]


def _compute_metrics(y_true, y_pred):
    """
    Computes MAE, RMSE, and MAPE. MAPE excludes rows where the actual
    value is zero (common in daily sales data), since MAPE divides by
    the actual value and is undefined at zero.
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))

    nonzero = y_true != 0
    excluded = int((~nonzero).sum())
    mape = (np.mean(np.abs((y_true[nonzero] - y_pred[nonzero]) / y_true[nonzero])) * 100
            if nonzero.sum() > 0 else None)

    return {'mae': mae, 'rmse': rmse, 'mape': mape, 'mape_excluded_zero_rows': excluded}


def train_and_compare_models(featured_df, date_col='date', target_col='sales', split_date='2017-01-01'):
    """
    Trains Random Forest (Model 1) and Gradient Boosting (Model 2) on
    identical features and an identical chronological split, evaluates
    both with MAE/RMSE/MAPE, and selects the better model using MAE
    (RMSE as tiebreaker if the MAE difference is under 0.5%).

    Fully independent of train_forecast_model() -- does not call or
    modify it, so the existing Random Forest pathway is unaffected.
    """
    features = ['dayofweek', 'month', 'lag_7', 'rolling_mean_7']
    X_train, y_train, X_test, y_test = _time_based_split(
        featured_df, date_col, target_col, split_date, features
    )

    rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
    rf_model.fit(X_train, y_train)
    rf_metrics = _compute_metrics(y_test, rf_model.predict(X_test))

    gb_model = GradientBoostingRegressor(n_estimators=100, random_state=42)
    gb_model.fit(X_train, y_train)
    gb_metrics = _compute_metrics(y_test, gb_model.predict(X_test))

    mae_diff_pct = abs(rf_metrics['mae'] - gb_metrics['mae']) / max(rf_metrics['mae'], gb_metrics['mae']) * 100

    if mae_diff_pct < 0.5:
        selected = 'RandomForest' if rf_metrics['rmse'] <= gb_metrics['rmse'] else 'GradientBoosting'
        reason = f"MAE was within 0.5% ({mae_diff_pct:.2f}% difference), so RMSE was used as the tiebreaker."
    else:
        selected = 'RandomForest' if rf_metrics['mae'] < gb_metrics['mae'] else 'GradientBoosting'
        reason = f"Selected on lower MAE ({mae_diff_pct:.2f}% better than the alternative)."

    return {
        'random_forest': {'model': rf_model, 'metrics': rf_metrics},
        'gradient_boosting': {'model': gb_model, 'metrics': gb_metrics},
        'selected': selected,
        'selection_reason': reason,
        'test_size': len(y_test),
    }