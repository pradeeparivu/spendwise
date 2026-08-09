import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import datetime, date
import os
import json

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SpendWise",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Constants ─────────────────────────────────────────────────────────────────
DATA_FILE = "transactions.csv"
INCOME_CATEGORIES = ["Salary", "Freelance", "Investment", "Gift", "Other Income"]
EXPENSE_CATEGORIES = ["Food", "Rent", "Transport", "Shopping", "Entertainment", "Health", "Utilities", "Other"]

PALETTE = {
    "bg":      "#0F1117",
    "card":    "#1A1D27",
    "border":  "#2A2D3A",
    "green":   "#22D3A0",
    "red":     "#F25C5C",
    "blue":    "#5C9EF2",
    "purple":  "#A78BFA",
    "text":    "#E8EAF0",
    "muted":   "#7A7F94",
}

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@500;700&display=swap');

html, body, [data-testid="stAppViewContainer"] {{
    background-color: {PALETTE['bg']};
    color: {PALETTE['text']};
    font-family: 'Inter', sans-serif;
}}

[data-testid="stSidebar"] {{
    background-color: {PALETTE['card']};
    border-right: 1px solid {PALETTE['border']};
}}

h1, h2, h3 {{
    font-family: 'Space Grotesk', sans-serif;
    color: {PALETTE['text']};
}}

.metric-card {{
    background: {PALETTE['card']};
    border: 1px solid {PALETTE['border']};
    border-radius: 14px;
    padding: 22px 24px;
    margin-bottom: 12px;
}}

.metric-label {{
    font-size: 12px;
    font-weight: 500;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: {PALETTE['muted']};
    margin-bottom: 6px;
}}

.metric-value {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 32px;
    font-weight: 700;
    line-height: 1;
}}

.metric-green {{ color: {PALETTE['green']}; }}
.metric-red   {{ color: {PALETTE['red']}; }}
.metric-blue  {{ color: {PALETTE['blue']}; }}

.section-title {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: {PALETTE['muted']};
    margin: 24px 0 12px;
}}

.tx-row {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: {PALETTE['card']};
    border: 1px solid {PALETTE['border']};
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 8px;
}}

.tx-cat  {{ font-size: 13px; font-weight: 500; color: {PALETTE['text']}; }}
.tx-date {{ font-size: 12px; color: {PALETTE['muted']}; }}
.tx-note {{ font-size: 12px; color: {PALETTE['muted']}; font-style: italic; }}
.tx-amt-income  {{ font-weight: 700; color: {PALETTE['green']}; font-family: 'Space Grotesk', sans-serif; }}
.tx-amt-expense {{ font-weight: 700; color: {PALETTE['red']};   font-family: 'Space Grotesk', sans-serif; }}

.stButton > button {{
    background: {PALETTE['green']};
    color: #0F1117;
    border: none;
    border-radius: 8px;
    font-weight: 700;
    font-family: 'Space Grotesk', sans-serif;
    padding: 10px 20px;
    width: 100%;
    transition: opacity 0.15s;
}}
.stButton > button:hover {{ opacity: 0.85; color: #0F1117; }}

.stSelectbox > div > div, .stNumberInput > div > div > input, .stTextInput > div > div > input {{
    background: {PALETTE['bg']} !important;
    border: 1px solid {PALETTE['border']} !important;
    border-radius: 8px !important;
    color: {PALETTE['text']} !important;
}}

[data-testid="stDateInput"] input {{
    background: {PALETTE['bg']} !important;
    border: 1px solid {PALETTE['border']} !important;
    border-radius: 8px !important;
    color: {PALETTE['text']} !important;
}}

.stRadio > div {{ gap: 10px; }}
.stRadio label {{ color: {PALETTE['text']} !important; }}

div[data-testid="stMetric"] {{
    background: {PALETTE['card']};
    border: 1px solid {PALETTE['border']};
    border-radius: 14px;
    padding: 16px 20px;
}}

.budget-bar-bg {{
    background: {PALETTE['border']};
    border-radius: 99px;
    height: 8px;
    width: 100%;
    margin-top: 8px;
}}

footer {{ display: none; }}
</style>
""", unsafe_allow_html=True)

# ── Data helpers ──────────────────────────────────────────────────────────────
def load_data() -> pd.DataFrame:
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE, parse_dates=["date"])
        return df
    return pd.DataFrame(columns=["date", "type", "category", "amount", "note"])

def save_data(df: pd.DataFrame):
    df.to_csv(DATA_FILE, index=False)

def add_transaction(df, tx_date, tx_type, category, amount, note):
    new_row = pd.DataFrame([{
        "date": pd.to_datetime(tx_date),
        "type": tx_type,
        "category": category,
        "amount": amount,
        "note": note,
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    save_data(df)
    return df

# ── Load state ────────────────────────────────────────────────────────────────
if "df" not in st.session_state:
    st.session_state.df = load_data()

df = st.session_state.df

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💸 SpendWise")
    st.markdown(f"<p style='color:{PALETTE['muted']};font-size:13px;margin-top:-8px'>Personal Finance Tracker</p>", unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("### Add Transaction")

    tx_type = st.radio("Type", ["Income", "Expense"], horizontal=True)
    cats = INCOME_CATEGORIES if tx_type == "Income" else EXPENSE_CATEGORIES
    category = st.selectbox("Category", cats)
    amount   = st.number_input("Amount (₹)", min_value=0.01, step=100.0, format="%.2f")
    tx_date  = st.date_input("Date", value=date.today())
    note     = st.text_input("Note (optional)", placeholder="e.g. Lunch with team")

    if st.button("Add Transaction"):
        if amount > 0:
            st.session_state.df = add_transaction(
                st.session_state.df, tx_date, tx_type, category, amount, note
            )
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
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Income</div>
            <div class="metric-value metric-green">₹{total_income:,.0f}</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Expenses</div>
            <div class="metric-value metric-red">₹{total_expense:,.0f}</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        color = "metric-green" if net_savings >= 0 else "metric-red"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Net Savings</div>
            <div class="metric-value {color}">₹{net_savings:,.0f}</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Savings Rate</div>
            <div class="metric-value metric-blue">{savings_rate:.1f}%</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts ──────────────────────────────────────────────────────────────
    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        st.markdown('<div class="section-title">Spending by Category</div>', unsafe_allow_html=True)
        if not expense_df.empty:
            cat_totals = expense_df.groupby("category")["amount"].sum().sort_values(ascending=True)
            fig, ax = plt.subplots(figsize=(6, max(3, len(cat_totals) * 0.55)))
            fig.patch.set_facecolor(PALETTE["card"])
            ax.set_facecolor(PALETTE["card"])
            colors = [PALETTE["red"], PALETTE["purple"], PALETTE["blue"],
                      "#F2965C", "#5CF2D3", "#F2C45C", "#A0F25C", "#F25C9E"]
            bars = ax.barh(cat_totals.index, cat_totals.values,
                           color=colors[:len(cat_totals)], height=0.55, zorder=3)
            for bar, val in zip(bars, cat_totals.values):
                ax.text(bar.get_width() + max(cat_totals.values) * 0.01, bar.get_y() + bar.get_height() / 2,
                        f"₹{val:,.0f}", va="center", ha="left",
                        color=PALETTE["text"], fontsize=10, fontweight="600")
            ax.set_xlim(0, max(cat_totals.values) * 1.25)
            ax.tick_params(axis="y", colors=PALETTE["text"], labelsize=11)
            ax.tick_params(axis="x", colors=PALETTE["muted"], labelsize=9)
            ax.spines[["top","right","left","bottom"]].set_visible(False)
            ax.xaxis.set_visible(False)
            ax.yaxis.set_tick_params(length=0)
            fig.tight_layout()
            st.pyplot(fig)
        else:
            st.markdown(f"<p style='color:{PALETTE['muted']}'>No expense data yet.</p>", unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="section-title">Income vs Expenses</div>', unsafe_allow_html=True)
        fig2, ax2 = plt.subplots(figsize=(4, 4))
        fig2.patch.set_facecolor(PALETTE["card"])
        ax2.set_facecolor(PALETTE["card"])
        sizes  = [total_income, total_expense] if total_income and total_expense else [total_income or 1, total_expense or 0]
        clrs   = [PALETTE["green"], PALETTE["red"]]
        wedges, _ = ax2.pie(sizes, colors=clrs, startangle=90,
                             wedgeprops=dict(width=0.55, edgecolor=PALETTE["card"], linewidth=3))
        legend_patches = [
            mpatches.Patch(color=PALETTE["green"], label=f"Income  ₹{total_income:,.0f}"),
            mpatches.Patch(color=PALETTE["red"],   label=f"Expenses ₹{total_expense:,.0f}"),
        ]
        ax2.legend(handles=legend_patches, loc="lower center",
                   bbox_to_anchor=(0.5, -0.12), ncol=1,
                   frameon=False, fontsize=10,
                   labelcolor=PALETTE["text"])
        ax2.set_title(f"₹{net_savings:,.0f}\nSaved", color=PALETTE["text"],
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
                <span class="tx-cat">{row['category']}</span>
                {note_html}
                <br>
                <span class="tx-date">{pd.to_datetime(row['date']).strftime('%d %b %Y')}</span>
            </div>
            <span class="{amt_class}">{sign}₹{row['amount']:,.2f}</span>
        </div>""", unsafe_allow_html=True)

    # ── Delete last ─────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🗑️ Delete Last Transaction"):
        if not st.session_state.df.empty:
            st.session_state.df = st.session_state.df.iloc[:-1].reset_index(drop=True)
            save_data(st.session_state.df)
            st.rerun()
