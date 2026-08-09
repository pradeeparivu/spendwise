import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import datetime, date
import os

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SpendWise",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Constants ─────────────────────────────────────────────────────────────────
DATA_FILE = "transactions.csv"
INCOME_CATEGORIES  = ["Salary", "Freelance", "Investment", "Gift", "Other Income"]
EXPENSE_CATEGORIES = ["Food", "Rent", "Transport", "Shopping", "Entertainment", "Health", "Utilities", "Other"]

DARK = {
    "bg":     "#0F1117", "card":   "#1A1D27", "border": "#2A2D3A",
    "green":  "#22D3A0", "red":    "#F25C5C", "blue":   "#5C9EF2",
    "purple": "#A78BFA", "text":   "#E8EAF0", "muted":  "#7A7F94",
    "btn_txt":"#0F1117",
}
LIGHT = {
    "bg":     "#F4F6FB", "card":   "#FFFFFF", "border": "#DDE1EE",
    "green":  "#0F9E73", "red":    "#D63B3B", "blue":   "#2B6FD6",
    "purple": "#6D4FC2", "text":   "#1A1D27", "muted":  "#6B7280",
    "btn_txt":"#FFFFFF",
}

# ── Theme state ───────────────────────────────────────────────────────────────
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

P = DARK if st.session_state.dark_mode else LIGHT

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@500;700&display=swap');

html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
    background-color: {P['bg']} !important;
    color: {P['text']};
    font-family: 'Inter', sans-serif;
}}
[data-testid="stSidebar"] {{
    background-color: {P['card']} !important;
    border-right: 1px solid {P['border']};
}}
[data-testid="stSidebar"] * {{ color: {P['text']} !important; }}
h1, h2, h3 {{ font-family: 'Space Grotesk', sans-serif; color: {P['text']}; }}

.metric-card {{
    background: {P['card']}; border: 1px solid {P['border']};
    border-radius: 14px; padding: 22px 24px; margin-bottom: 12px;
}}
.metric-label {{
    font-size: 12px; font-weight: 500; letter-spacing: 0.08em;
    text-transform: uppercase; color: {P['muted']}; margin-bottom: 6px;
}}
.metric-value {{ font-family: 'Space Grotesk', sans-serif; font-size: 32px; font-weight: 700; line-height: 1; }}
.metric-green {{ color: {P['green']}; }}
.metric-red   {{ color: {P['red']}; }}
.metric-blue  {{ color: {P['blue']}; }}

.section-title {{
    font-family: 'Space Grotesk', sans-serif; font-size: 13px; font-weight: 600;
    letter-spacing: 0.1em; text-transform: uppercase; color: {P['muted']}; margin: 24px 0 12px;
}}
.tx-row {{
    display: flex; align-items: center; justify-content: space-between;
    background: {P['card']}; border: 1px solid {P['border']};
    border-radius: 10px; padding: 12px 16px; margin-bottom: 8px;
}}
.tx-cat  {{ font-size: 13px; font-weight: 500; color: {P['text']}; }}
.tx-date {{ font-size: 12px; color: {P['muted']}; }}
.tx-note {{ font-size: 12px; color: {P['muted']}; font-style: italic; }}
.tx-amt-income  {{ font-weight: 700; color: {P['green']}; font-family: 'Space Grotesk', sans-serif; }}
.tx-amt-expense {{ font-weight: 700; color: {P['red']};   font-family: 'Space Grotesk', sans-serif; }}

.stButton > button {{
    background: {P['green']}; color: {P['btn_txt']}; border: none;
    border-radius: 8px; font-weight: 700; font-family: 'Space Grotesk', sans-serif;
    padding: 10px 20px; width: 100%; transition: opacity 0.15s;
}}
.stButton > button:hover {{ opacity: 0.85; color: {P['btn_txt']}; }}

.stSelectbox > div > div, .stNumberInput > div > div > input, .stTextInput > div > div > input {{
    background: {P['bg']} !important; border: 1px solid {P['border']} !important;
    border-radius: 8px !important; color: {P['text']} !important;
}}
[data-testid="stDateInput"] input {{
    background: {P['bg']} !important; border: 1px solid {P['border']} !important;
    border-radius: 8px !important; color: {P['text']} !important;
}}
.stRadio > div {{ gap: 10px; }}
.stRadio label {{ color: {P['text']} !important; }}
div[data-testid="stMetric"] {{
    background: {P['card']}; border: 1px solid {P['border']};
    border-radius: 14px; padding: 16px 20px;
}}
footer {{ display: none; }}
</style>
""", unsafe_allow_html=True)

# ── Data helpers ──────────────────────────────────────────────────────────────
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE, parse_dates=["date"])
    return pd.DataFrame(columns=["date", "type", "category", "amount", "note"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def add_transaction(df, tx_date, tx_type, category, amount, note):
    new_row = pd.DataFrame([{"date": pd.to_datetime(tx_date), "type": tx_type,
                              "category": category, "amount": amount, "note": note}])
    df = pd.concat([df, new_row], ignore_index=True)
    save_data(df)
    return df

# ── Load state ────────────────────────────────────────────────────────────────
if "df" not in st.session_state:
    st.session_state.df = load_data()
df = st.session_state.df

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    # Title + theme toggle on same row
    title_col, toggle_col = st.columns([2, 1])
    with title_col:
        st.markdown("## 💸 SpendWise")
        st.markdown(f"<p style='color:{P['muted']};font-size:13px;margin-top:-8px'>Finance Tracker</p>", unsafe_allow_html=True)
    with toggle_col:
        st.markdown("<br>", unsafe_allow_html=True)
        icon = "☀️" if st.session_state.dark_mode else "🌙"
        if st.button(icon, help="Toggle light/dark mode"):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()

    st.markdown("---")
    st.markdown("### Add Transaction")

    tx_type  = st.radio("Type", ["Income", "Expense"], horizontal=True)
    cats     = INCOME_CATEGORIES if tx_type == "Income" else EXPENSE_CATEGORIES
    category = st.selectbox("Category", cats)
    amount   = st.number_input("Amount (₹)", min_value=0.01, step=100.0, format="%.2f")
    tx_date  = st.date_input("Date", value=date.today())
    note     = st.text_input("Note (optional)", placeholder="e.g. Lunch with team")

    if st.button("Add Transaction"):
        if amount > 0:
            st.session_state.df = add_transaction(st.session_state.df, tx_date, tx_type, category, amount, note)
            df = st.session_state.df
            st.success("Transaction added!")
        else:
            st.error("Amount must be greater than 0.")

    st.markdown("---")
    st.markdown("### Filter by Month")
    months = ["All"]
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        months += sorted(df["date"].dt.to_period("M").astype(str).unique(), reverse=True)
    selected_month = st.selectbox("Month", months)

# ── Filter ────────────────────────────────────────────────────────────────────
filtered = df.copy()
if selected_month != "All" and not df.empty:
    filtered = df[df["date"].dt.to_period("M").astype(str) == selected_month]

# ── Main area ─────────────────────────────────────────────────────────────────
st.markdown("# Dashboard")

if filtered.empty:
    st.info("No transactions yet. Add your first one from the sidebar! 👈")
else:
    income_df  = filtered[filtered["type"] == "Income"]
    expense_df = filtered[filtered["type"] == "Expense"]

    total_income  = income_df["amount"].sum()
    total_expense = expense_df["amount"].sum()
    net_savings   = total_income - total_expense
    savings_rate  = (net_savings / total_income * 100) if total_income > 0 else 0

    # ── KPI cards ──────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    for col, label, value, cls in [
        (c1, "Total Income",   f"₹{total_income:,.0f}",  "metric-green"),
        (c2, "Total Expenses", f"₹{total_expense:,.0f}", "metric-red"),
        (c3, "Net Savings",    f"₹{net_savings:,.0f}",   "metric-green" if net_savings >= 0 else "metric-red"),
        (c4, "Savings Rate",   f"{savings_rate:.1f}%",   "metric-blue"),
    ]:
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value {cls}">{value}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts ──────────────────────────────────────────────────────────────
    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        st.markdown('<div class="section-title">Spending by Category</div>', unsafe_allow_html=True)
        if not expense_df.empty:
            cat_totals = expense_df.groupby("category")["amount"].sum().sort_values(ascending=True)
            fig, ax = plt.subplots(figsize=(6, max(3, len(cat_totals) * 0.55)))
            fig.patch.set_facecolor(P["card"])
            ax.set_facecolor(P["card"])
            bar_colors = [P["red"], P["purple"], P["blue"], "#F2965C", "#5CF2D3", "#F2C45C", "#A0F25C", "#F25C9E"]
            bars = ax.barh(cat_totals.index, cat_totals.values, color=bar_colors[:len(cat_totals)], height=0.55, zorder=3)
            for bar, val in zip(bars, cat_totals.values):
                ax.text(bar.get_width() + max(cat_totals.values) * 0.01,
                        bar.get_y() + bar.get_height() / 2,
                        f"₹{val:,.0f}", va="center", ha="left",
                        color=P["text"], fontsize=10, fontweight="600")
            ax.set_xlim(0, max(cat_totals.values) * 1.25)
            ax.tick_params(axis="y", colors=P["text"], labelsize=11)
            ax.tick_params(axis="x", colors=P["muted"], labelsize=9)
            ax.spines[["top","right","left","bottom"]].set_visible(False)
            ax.xaxis.set_visible(False)
            ax.yaxis.set_tick_params(length=0)
            fig.tight_layout()
            st.pyplot(fig)
        else:
            st.markdown(f"<p style='color:{P['muted']}'>No expense data yet.</p>", unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="section-title">Income vs Expenses</div>', unsafe_allow_html=True)
        fig2, ax2 = plt.subplots(figsize=(4, 4))
        fig2.patch.set_facecolor(P["card"])
        ax2.set_facecolor(P["card"])
        sizes = [total_income or 1, total_expense or 0]
        wedges, _ = ax2.pie(sizes, colors=[P["green"], P["red"]], startangle=90,
                             wedgeprops=dict(width=0.55, edgecolor=P["card"], linewidth=3))
        legend_patches = [
            mpatches.Patch(color=P["green"], label=f"Income  ₹{total_income:,.0f}"),
            mpatches.Patch(color=P["red"],   label=f"Expenses ₹{total_expense:,.0f}"),
        ]
        ax2.legend(handles=legend_patches, loc="lower center", bbox_to_anchor=(0.5, -0.12),
                   ncol=1, frameon=False, fontsize=10, labelcolor=P["text"])
        ax2.set_title(f"₹{net_savings:,.0f}\nSaved", color=P["text"],
                      fontsize=14, fontweight="bold", y=0.45, va="center")
        fig2.tight_layout()
        st.pyplot(fig2)

    # ── Transaction list ────────────────────────────────────────────────────
    st.markdown('<div class="section-title">Recent Transactions</div>', unsafe_allow_html=True)
    recent = filtered.sort_values("date", ascending=False).head(20)

    for _, row in recent.iterrows():
        is_income = row["type"] == "Income"
        amt_class = "tx-amt-income" if is_income else "tx-amt-expense"
        sign      = "+" if is_income else "−"
        note_html = f'<span class="tx-note"> · {row["note"]}</span>' if pd.notna(row["note"]) and str(row["note"]).strip() else ""
        st.markdown(f"""
        <div class="tx-row">
            <div>
                <span class="tx-cat">{row['category']}</span>{note_html}<br>
                <span class="tx-date">{pd.to_datetime(row['date']).strftime('%d %b %Y')}</span>
            </div>
            <span class="{amt_class}">{sign}₹{row['amount']:,.2f}</span>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🗑️ Delete Last Transaction"):
        if not st.session_state.df.empty:
            st.session_state.df = st.session_state.df.iloc[:-1].reset_index(drop=True)
            save_data(st.session_state.df)
            st.rerun()
