from src.report_export import generate_pdf_report, generate_excel_report
import plotly.express as px
import streamlit as st
import pandas as pd
from datetime import datetime
from src.data_cleaning import clean_sales_data
from src.pipeline import generate_business_report
import streamlit.components.v1 as components


from src.utils import format_inr
from src.chatbot import answer_question

def stamp_html(status):
    css_class = {
        'Reorder Now': 'stamp-danger',
        'Monitor': 'stamp-warn',
        'Healthy': 'stamp-good'
    }.get(status, 'stamp-warn')
    return f'<span class="stamp {css_class}">{status}</span>'


def render_inventory_table(inventory_df):
    priority_order = {'Reorder Now': 0, 'Monitor': 1, 'Healthy': 2}
    df = inventory_df.copy()
    df['sort_key'] = df['status_forecasted'].map(priority_order)
    df = df.sort_values(['sort_key', 'days_of_supply_forecasted'])

    rows = ""
    for _, row in df.iterrows():
        rows += (
            f"<tr><td>Item {row['item']}</td>"
            f"<td>{row['current_stock']:.0f} units</td>"
            f"<td>{row['days_of_supply_forecasted']:.1f} days</td>"
            f"<td>{stamp_html(row['status_forecasted'])}</td></tr>"
        )

    return (
        f"<table class='inventory-table'>"
        f"<thead><tr><th>Item</th><th>Stock on Hand</th>"
        f"<th>Days of Supply</th><th>Status</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
    )


def render_inventory_chart(inventory_df):
    df = inventory_df.copy()
    df['item_label'] = df['item'].astype(str)
    df = df.sort_values('days_of_supply_forecasted')

    color_map = {'Reorder Now': '#B23A2E', 'Monitor': '#C98A1F', 'Healthy': '#2F6F4E'}

    fig = px.bar(
        df, x='item_label', y='days_of_supply_forecasted',
        color='status_forecasted', color_discrete_map=color_map,
        category_orders={'item_label': df['item_label'].tolist()},
        labels={
            'days_of_supply_forecasted': 'Days of Supply Remaining',
            'item_label': 'Item', 'status_forecasted': 'Status'
        }
    )
    fig.add_hline(
        y=5, line_dash='dash', line_color="#81231B",
        annotation_text='Reorder threshold (5 days)', annotation_position='top left'
    )
    fig.update_layout(
        plot_bgcolor='#FFFFFF', paper_bgcolor='#F2F4F1',
        font=dict(family='IBM Plex Sans, sans-serif', color='#1C2541'),
        height=420, margin=dict(t=40, l=10, r=10, b=10),
        legend_title_text='Status'
    )
    fig.update_xaxes(tickangle=-45, title='Item')
    return fig

st.set_page_config(
    page_title="BizPal — Retail Intelligence",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded"
)
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'report_history' not in st.session_state:
    st.session_state.report_history = []
if st.session_state.get('clear_chat_input', False):
    st.session_state.chat_input = ""
    st.session_state.clear_chat_input = False

def render_forecast_chart(cleaned_df, inventory_df, item_id):
    item_df = cleaned_df[cleaned_df['item'] == item_id].sort_values('date').tail(60)
    row = inventory_df[inventory_df['item'] == item_id].iloc[0]
    forecast_date = item_df['date'].max() + pd.Timedelta(days=1)
    forecast_value = row['forecasted_daily_demand']

    fig = px.line(item_df, x='date', y='sales', labels={'sales': 'Units Sold', 'date': 'Date'})
    fig.update_traces(line_color='#1C2541', name='Actual', showlegend=True)

    fig.add_scatter(
        x=[item_df['date'].max(), forecast_date],
        y=[item_df['sales'].iloc[-1], forecast_value],
        mode='lines+markers',
        line=dict(color='#E2892B', dash='dash'),
        marker=dict(size=9, color='#E2892B'),
        name='Forecast'
    )
    fig.update_layout(
        plot_bgcolor='#FFFFFF', paper_bgcolor='#F2F4F1',
        font=dict(family='IBM Plex Sans, sans-serif', color='#1C2541'),
        height=380, margin=dict(t=30, l=10, r=10, b=10),
    )
    return fig

# ---------- Custom theming ----------
def load_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

    :root {
        --ink: #1C2541;
        --muted-ink: #5B6478;
        --paper: #F2F4F1;
        --paper-raised: #FFFFFF;
        --accent: #E2892B;
        --good: #2F6F4E;
        --warn: #C98A1F;
        --danger: #B23A2E;
        --border: #DDDFD9;
    }

    .block-container{
        padding-top: 3rem !important;
    }

    .stApp {
        background-color: var(--paper);
        font-family: 'IBM Plex Sans', sans-serif;
        color: var(--ink);
    }

    .stApp [data-testid="stMarkdownContainer"] p,
    .stApp label,
    .stApp .stButton button {
        color: var(--ink) !important;
    }

    h1, h2, h3 {
        font-family: 'Fraunces', Georgia, serif !important;
        color: var(--ink) !important;
        font-weight: 600 !important;
    }

    .bizpal-hero {
        border-bottom: 3px double var(--ink);
        padding-bottom: 1rem;
        margin-bottom: 2rem;
    }
    .bizpal-hero h1 { font-size: 2.6rem; margin-bottom: 0.2rem; }
    .bizpal-hero p {
        font-family: 'IBM Plex Mono', monospace;
        color: var(--muted-ink);
        font-size: 0.95rem;
        letter-spacing: 0.02em;
        margin: 0;
    }

    /* Receipt-stub KPI cards — the signature element */
    .kpi-card {
        background: var(--paper-raised);
        border: 1px solid var(--border);
        border-radius: 4px 4px 0 0;
        padding: 1.2rem 1.2rem 1rem 1.2rem;
        position: relative;
        box-shadow: 0 2px 6px rgba(28,37,65,0.06);
        transition: transform 0.15s ease;
        min-height: 110px;
    }
    .kpi-card:hover { transform: translateY(-2px); }
    .kpi-card::after {
        content: "";
        display: block;
        position: absolute;
        left: 0; right: 0; bottom: -8px;
        height: 8px;
        background-image: radial-gradient(circle at 6px 0, transparent 5px, var(--paper) 5.5px);
        background-size: 12px 8px;
        background-repeat: repeat-x;
    }
    .kpi-label {
        font-family: 'IBM Plex Mono', monospace;
        text-transform: uppercase;
        font-size: 0.72rem;
        letter-spacing: 0.08em;
        color: var(--muted-ink);
        margin-bottom: 0.4rem;
    }
    .kpi-value {
        font-family: 'Fraunces', Georgia, serif;
        font-size: 1.3rem;
        font-weight: 600;
        color: var(--ink);
        line-height: 1.25;
        overflow-wrap: break-word;
    }
    .kpi-sub {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.78rem;
        color: var(--muted-ink);
        margin-top: 0.3rem;
    }

    /* Ink-stamp status badges — used from Day 10 onward */
    .stamp {
        display: inline-block;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.72rem;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        padding: 0.15rem 0.5rem;
        border: 1.5px solid currentColor;
        border-radius: 2px;
        transform: rotate(-1.5deg);
        font-weight: 600;
    }
    .stamp-danger { color: var(--danger); }
    .stamp-warn { color: var(--warn); }
    .stamp-good { color: var(--good); }

    section[data-testid="stSidebar"] [data-testid="stFileUploader"] span,
    section[data-testid="stSidebar"] [data-testid="stFileUploader"] small,
    section[data-testid="stSidebar"] [data-testid="stFileUploader"] p {
        color: var(--ink) !important;
    }
    .inventory-table {
        width: 100%;
        border-collapse: collapse;
        font-family: 'IBM Plex Sans', sans-serif;
        background: var(--paper-raised);
    }
    .inventory-table th {
        text-align: left;
        font-family: 'IBM Plex Mono', monospace;
        text-transform: uppercase;
        font-size: 0.72rem;
        letter-spacing: 0.06em;
        color: var(--muted-ink);
        border-bottom: 2px solid var(--ink);
        padding: 0.6rem 0.8rem;
        position: sticky;
        top: 0;
        background: var(--paper-raised);
    }
    .inventory-table td {
        padding: 0.55rem 0.8rem;
        border-bottom: 1px solid var(--border);
        font-size: 0.92rem;
    }
    .inventory-table tbody tr:hover { background: var(--paper); }

    .table-scroll {
        max-height: 420px;
        overflow-y: auto;
        border: 1px solid var(--border);
        border-radius: 4px;
        margin-bottom: 1.5rem;
    }

    .rec-row {
        display: flex;
        align-items: center;
        gap: 0.8rem;
        padding: 0.55rem 0;
        border-bottom: 1px solid var(--border);
    }
    .rec-message {
        font-size: 0.92rem;
        color: var(--ink);
    }

    [data-testid="stPopover"] button {
        background-color: var(--accent) !important;
        color: #FFFFFF !important;
        border: none !important;
        font-weight: 600 !important;
    }

        
    </style>
    """, unsafe_allow_html=True)

load_css()

# ---------- Hero ----------
st.markdown("""
<div class="bizpal-hero">
    <h1>BizPal</h1>
    <p>SEE WHAT'S SELLING, WHAT'S LOW, AND WHAT TO DO NEXT</p>
</div>
""", unsafe_allow_html=True)

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("### 🧾 BizPal")
    st.caption("AI-powered business intelligence for small retail")
    uploaded_file = st.file_uploader("Upload sales CSV", type=["csv"])

# ---------- Main content ----------
if uploaded_file is None:
    st.info("Upload a sales CSV from the sidebar to get started.")
else:
    raw_df = pd.read_csv(uploaded_file, parse_dates=['date'])

    missing = {'date', 'item', 'sales'} - set(raw_df.columns)
    if missing:
        st.error(f"Missing required columns: {missing}. Expected: date, item, sales (and optionally store).")
        st.stop()

    if 'store' in raw_df.columns:
        store_df = raw_df[raw_df['store'] == 1].copy()
        st.sidebar.caption("Scoped to Store 1 — matches your SRS's single-store design and your trained forecasting models.")
    else:
        store_df = raw_df.copy()

    cleaned_df, cleaning_report = clean_sales_data(store_df)
    report = generate_business_report(cleaned_df, models_dir='models')

    if st.session_state.get('last_saved_file') != uploaded_file.name:
        st.session_state.report_history.append({
            'report_id': len(st.session_state.report_history) + 1,
            'store_id': 1,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_revenue': report['kpi_summary']['total_revenue'],
            'total_profit': report['kpi_summary']['total_profit'],
        })
        st.session_state.last_saved_file = uploaded_file.name

    with st.container():
        st.markdown('<div id="bizpal-chat-marker"></div>', unsafe_allow_html=True)
        with st.popover("💬 Ask BizPal"):
            st.markdown("**Ask BizPal**")
            for entry in st.session_state.chat_history[-6:]:
                st.markdown(f"**You:** {entry['question']}")
                st.markdown(f"**BizPal:** {entry['answer']}")

            user_question = st.text_input("Type a question...", key="chat_input")
            if st.button("Send", key="chat_send") and user_question.strip():
                answer = answer_question(user_question, report)
                st.session_state.chat_history.append({'question': user_question, 'answer': answer})
                st.session_state.clear_chat_input = True
                st.rerun()

    components.html("""
    <script>
    function fixChatWidget() {
        const doc = window.parent.document;
        const marker = doc.getElementById('bizpal-chat-marker');
        if (!marker) return;
        const container = marker.closest('div[data-testid="stVerticalBlock"]');
        if (!container) return;
        container.style.position = 'fixed';
        container.style.bottom = '24px';
        container.style.right = '24px';
        container.style.width = 'auto';
        container.style.zIndex = '9999';
    }
    fixChatWidget();
    const observer = new MutationObserver(fixChatWidget);
    observer.observe(window.parent.document.body, {childList: true, subtree: true, attributes: true});
    </script>
    """, height=0, width=0)    



    st.markdown("## Overview")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Total Revenue</div>
            <div class="kpi-value">{format_inr(report['kpi_summary']['total_revenue'])}</div>
            <div class="kpi-sub">2013-2017</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Total Profit</div>
            <div class="kpi-value">{format_inr(report['kpi_summary']['total_profit'])}</div>
            <div class="kpi-sub">2013-2017</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        top_item = report['top_revenue_items'][0]
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Top Product</div>
            <div class="kpi-value">Item {top_item}</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        reorder_count = sum(1 for r in report['recommendations'] if r['priority'] == 'High')
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Needs Reorder</div>
            <div class="kpi-value">{reorder_count}</div>
            <div class="kpi-sub">items at High priority</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("## Inventory & Reorder Status")

    status_filter = st.radio(
        "Filter by status",
        options=["All", "Reorder Now", "Monitor", "Healthy"],
        horizontal=True
    )

    inventory_df = report['inventory']
    filtered_inventory = (
        inventory_df if status_filter == "All"
        else inventory_df[inventory_df['status_forecasted'] == status_filter]
    )

    if filtered_inventory.empty:
        st.info("No items match this filter.")
    else:
        st.plotly_chart(render_inventory_chart(filtered_inventory), use_container_width=True)
        st.markdown(
            f'<div class="table-scroll">{render_inventory_table(filtered_inventory)}</div>',
            unsafe_allow_html=True
        )
    st.markdown("---")
   
    st.markdown("## Forecast Trends")
    st.caption("Only shown for your top-5 revenue items — the ones with trained forecasting models.")
    selected_item = st.selectbox("Select item", report['top_revenue_items'])
    st.plotly_chart(
        render_forecast_chart(cleaned_df, report['inventory'], selected_item),
        use_container_width=True
    )    

    st.markdown("---")

    st.markdown("## Recommendations")
    priority_class = {'High': 'stamp-danger', 'Medium': 'stamp-warn', 'Low': 'stamp-good'}
    top_recommendations = report['recommendations'][:6]
    remaining_recommendations = report['recommendations'][6:]

    for r in top_recommendations:
        st.markdown(f"""
        <div class="rec-row">
            <span class="stamp {priority_class[r['priority']]}">{r['priority']}</span>
            <span class="rec-message">{r['message']}</span>
        </div>
        """, unsafe_allow_html=True)

    if remaining_recommendations:
        with st.expander(f"Show all {len(report['recommendations'])} recommendations"):
            for r in remaining_recommendations:
                st.markdown(f"""
                <div class="rec-row">
                    <span class="stamp {priority_class[r['priority']]}">{r['priority']}</span>
                    <span class="rec-message">{r['message']}</span>
                </div>
                """, unsafe_allow_html=True)

    

    st.markdown("---")
    st.markdown("## Report History")

    history_df = pd.DataFrame(st.session_state.report_history)
    if history_df.empty:
        st.caption("No past reports yet — this is your first run.")
    else:
        display_history = history_df.copy()
        display_history['total_revenue'] = display_history['total_revenue'].apply(format_inr)
        display_history['total_profit'] = display_history['total_profit'].apply(format_inr)
        st.dataframe(display_history, use_container_width=True, hide_index=True)

    st.markdown("## Export Report")
    col_pdf, col_xlsx = st.columns(2)
    with col_pdf:
        st.download_button("📄 Download PDF Report", data=generate_pdf_report(report),
                            file_name="bizpal_report.pdf", mime="application/pdf")
    with col_xlsx:
        st.download_button("📊 Download Excel Report", data=generate_excel_report(report),
                            file_name="bizpal_report.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
