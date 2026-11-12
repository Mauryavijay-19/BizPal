import re
from src.utils import format_inr


def answer_question(question, report):
    """
    Rule-based Q&A over BizPal's already-computed report data.
    Matches keywords/synonyms in the question and routes to the
    matching piece of data. Never touches raw sales data.
    """
    q = question.lower()

    item_match = re.search(r'item\s*(\d+)|#(\d+)', q)
    if item_match:
        item_id = int(item_match.group(1) or item_match.group(2))
        inv = report['inventory']
        row = inv[inv['item'] == item_id]
        if row.empty:
            return f"I don't have data for item {item_id}."
        row = row.iloc[0]
        return (
            f"Item {item_id} has {row['current_stock']:.0f} units on hand, "
            f"about {row['days_of_supply_forecasted']:.1f} days of supply left, "
            f"and is currently flagged '{row['status_forecasted']}'."
        )

    revenue_kw = ['revenue', 'sales total', 'total sales', 'how much did i make', 'turnover']
    profit_kw = ['profit', 'margin', 'earnings']
    top_kw = ['top product', 'best seller', 'best selling', 'top item', 'most revenue']
    reorder_kw = ['reorder', 'low stock', 'running low', 'restock', 'out of stock']
    monitor_kw = ['monitor', 'watch', 'keep an eye']
    forecast_kw = ['forecast', 'trend', 'demand', 'predict', 'going up', 'going down']

    if any(kw in q for kw in revenue_kw):
        return f"Your total revenue is {format_inr(report['kpi_summary']['total_revenue'])} over the recorded period."

    if any(kw in q for kw in profit_kw):
        return f"Your total profit is {format_inr(report['kpi_summary']['total_profit'])} over the recorded period."

    if any(kw in q for kw in top_kw):
        top_items = report['top_revenue_items']
        return f"Your top revenue product is Item {top_items[0]}, followed by items {', '.join(str(i) for i in top_items[1:])}."

    if any(kw in q for kw in reorder_kw):
        high = [r for r in report['recommendations'] if r['priority'] == 'High']
        if not high:
            return "Nothing needs reordering right now — all items have healthy stock."
        items = ', '.join(f"Item {r['item']}" for r in high)
        return f"{len(high)} item(s) need reordering now: {items}."

    if any(kw in q for kw in monitor_kw):
        medium = [r for r in report['recommendations'] if r['priority'] == 'Medium']
        return f"{len(medium)} item(s) are in the Monitor zone — moderate stock, worth watching."

    if any(kw in q for kw in forecast_kw):
        inv = report['inventory']
        modeled = inv[inv['item'].isin(report['top_revenue_items'])]
        easing = modeled[modeled['forecasted_daily_demand'] < modeled['avg_daily_sales']]
        rising = modeled[modeled['forecasted_daily_demand'] > modeled['avg_daily_sales']]
        return (
            f"Among your top revenue items, {len(easing)} show easing demand and "
            f"{len(rising)} show rising demand compared to their historical average."
        )

    return (
        "I can help with questions about revenue, profit, top products, "
        "inventory status, and forecasts. Try asking something like "
        "'what needs reordering?' or 'what's my total revenue?'"
    )