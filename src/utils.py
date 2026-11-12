def format_inr(value):
    """Formats large currency values using the Indian numbering system (Lakh/Crore)."""
    if value >= 1_00_00_000:
        return f"₹{value / 1_00_00_000:.2f} Cr"
    elif value >= 1_00_000:
        return f"₹{value / 1_00_000:.2f} L"
    return f"₹{value:,.0f}"