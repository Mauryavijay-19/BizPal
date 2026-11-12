import sqlite3
import pandas as pd
from datetime import datetime

DB_PATH = 'bizpal.db'


def get_connection(db_path=DB_PATH):
    return sqlite3.connect(db_path)


def initialize_db(db_path=DB_PATH):
    """Creates all BizPal tables if they don't already exist, matching the SRS's data model."""
    conn = get_connection(db_path)
    cur = conn.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS store (
        store_id INTEGER PRIMARY KEY, name TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS product (
        item_id INTEGER PRIMARY KEY, price REAL, cost REAL)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS sales_transaction (
        id INTEGER PRIMARY KEY AUTOINCREMENT, store_id INTEGER,
        item_id INTEGER, date TEXT, sales INTEGER)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS report (
        report_id INTEGER PRIMARY KEY AUTOINCREMENT, store_id INTEGER,
        generated_at TEXT, total_revenue REAL, total_profit REAL)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS inventory_item (
        id INTEGER PRIMARY KEY AUTOINCREMENT, report_id INTEGER, item_id INTEGER,
        current_stock REAL, days_of_supply REAL, status TEXT,
        FOREIGN KEY (report_id) REFERENCES report(report_id))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS forecast_result (
        id INTEGER PRIMARY KEY AUTOINCREMENT, report_id INTEGER, item_id INTEGER,
        forecasted_demand REAL,
        FOREIGN KEY (report_id) REFERENCES report(report_id))""")

    conn.commit()
    conn.close()


def save_report(store_id, cleaned_df, price_table, report, db_path=DB_PATH):
    """
    Persists one full report run: store info, products, sales transactions,
    a report summary row, and its inventory/forecast snapshot.
    Clears this store's previous sales_transaction rows first, so re-running
    the app doesn't keep duplicating the same 5 years of data.
    """
    conn = get_connection(db_path)
    cur = conn.cursor()

    cur.execute("INSERT OR REPLACE INTO store (store_id, name) VALUES (?, ?)",
                (store_id, f"Store {store_id}"))

    for _, row in price_table.iterrows():
        cur.execute("INSERT OR REPLACE INTO product (item_id, price, cost) VALUES (?, ?, ?)",
                    (int(row['item']), float(row['price']), float(row['cost'])))

    cur.execute("DELETE FROM sales_transaction WHERE store_id = ?", (store_id,))
    df = cleaned_df.copy()
    df['date_str'] = df['date'].dt.strftime('%Y-%m-%d')
    tx_rows = list(zip([store_id] * len(df), df['item'].astype(int), df['date_str'], df['sales'].astype(int)))
    cur.executemany(
        "INSERT INTO sales_transaction (store_id, item_id, date, sales) VALUES (?, ?, ?, ?)", tx_rows
    )

    generated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cur.execute(
        "INSERT INTO report (store_id, generated_at, total_revenue, total_profit) VALUES (?, ?, ?, ?)",
        (store_id, generated_at, report['kpi_summary']['total_revenue'], report['kpi_summary']['total_profit'])
    )
    report_id = cur.lastrowid

    for _, row in report['inventory'].iterrows():
        cur.execute(
            "INSERT INTO inventory_item (report_id, item_id, current_stock, days_of_supply, status) VALUES (?, ?, ?, ?, ?)",
            (report_id, int(row['item']), float(row['current_stock']),
             float(row['days_of_supply_forecasted']), row['status_forecasted'])
        )
        if row['item'] in report['top_revenue_items']:
            cur.execute(
                "INSERT INTO forecast_result (report_id, item_id, forecasted_demand) VALUES (?, ?, ?)",
                (report_id, int(row['item']), float(row['forecasted_daily_demand']))
            )

    conn.commit()
    conn.close()
    return report_id


def get_report_history(db_path=DB_PATH):
    """Returns all past report runs, most recent first."""
    conn = get_connection(db_path)
    df = pd.read_sql_query(
        "SELECT report_id, store_id, generated_at, total_revenue, total_profit FROM report ORDER BY generated_at DESC",
        conn
    )
    conn.close()
    return df