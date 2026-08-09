import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import date
import gspread
from google.oauth2.service_account import Credentials
import json
import os

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SpendWise", page_icon="💸",
    layout="wide", initial_sidebar_state="expanded",
)

# ── Constants ─────────────────────────────────────────────────────────────────
SHEET_ID           = "1_-agCHngVcvP3LRErDAlcTJzAt5BkxfHtdMqpWHNF5M"
INCOME_CATEGORIES  = ["Salary", "Freelance", "Investment", "Gift", "Other Income"]
EXPENSE_CATEGORIES = ["Food", "Rent", "Transport", "Shopping", "Entertainment", "Health", "Utilities", "Other"]

USERS = {
    "demo": {"password": "demo123", "accounts": ["Demo"],        "is_demo": True},
    "dheeptina":  {"password": "Dhiyazh1006", "accounts": ["Pradeep", "Tina"],"is_demo": False},
}

DARK = {
    "bg":"#0F1117","card":"#1A1D27","border":"#2A2D3A",
    "green":"#22D3A0","red":"#F25C5C","blue":"#5C9EF2",
    "purple":"#A78BFA","text":"#E8EAF0","muted":"#7A7F94","btn_txt":"#0F1117",
}
LIGHT = {
    "bg":"#F4F6FB","card":"#FFFFFF","border":"#DDE1EE",
    "green":"#0F9E73","red":"#D63B3B","blue":"#2B6FD6",
    "purple":"#6D4FC2","text":"#1A1D27","muted":"#6B7280","btn_txt":"#FFFFFF",
}

# ── Session defaults ──────────────────────────────────────────────────────────
for key, val in [("dark_mode",False),("logged_in",False),("username",""),("account","")]:
    if key not in st.session_state:
        st.session_state[key] = val

# ── Remember Me via URL token ────────────────────────────────────────────────
import hashlib, base64

def make_token(username, password):
    raw = f"{username}:{password}:spendwise-secret"
    return base64.urlsafe_b64encode(hashlib.sha256(raw.encode()).digest()).decode()[:20]

def check_token(token):
    for uname, cfg in USERS.items():
        if cfg.get("is_demo"):
            continue
        if make_token(uname, cfg["password"]) == token:
            return uname
    return None

# Check token from query params BEFORE any rerun
if not st.session_state.logged_in:
    params = st.query_params
    if "token" in params:
        uname = check_token(params["token"])
        if uname:
            st.session_state.logged_in  = True
            st.session_state.username   = uname
            st.session_state.account    = USERS[uname]["accounts"][0]
            st.session_state.remember_token = params["token"]
    elif "remember_token" in st.session_state:
        uname = check_token(st.session_state.remember_token)
        if uname:
            st.session_state.logged_in = True
            st.session_state.username  = uname
            st.session_state.account   = USERS[uname]["accounts"][0]

P = DARK if st.session_state.dark_mode else LIGHT

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@500;700&display=swap');
html,body,[data-testid="stAppViewContainer"],[data-testid="stMain"]{{background-color:{P['bg']} !important;color:{P['text']};font-family:'Inter',sans-serif;}}
[data-testid="stSidebar"]{{background-color:{P['card']} !important;border-right:1px solid {P['border']};}}
[data-testid="stSidebar"] *{{color:{P['text']} !important;}}
h1,h2,h3{{font-family:'Space Grotesk',sans-serif;color:{P['text']};}}
.metric-card{{background:{P['card']};border:1px solid {P['border']};border-radius:14px;padding:22px 24px;margin-bottom:12px;}}
.metric-label{{font-size:12px;font-weight:500;letter-spacing:0.08em;text-transform:uppercase;color:{P['muted']};margin-bottom:6px;}}
.metric-value{{font-family:'Space Grotesk',sans-serif;font-size:32px;font-weight:700;line-height:1;}}
.metric-green{{color:{P['green']};}} .metric-red{{color:{P['red']};}} .metric-blue{{color:{P['blue']};}}
.section-title{{font-family:'Space Grotesk',sans-serif;font-size:13px;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:{P['muted']};margin:24px 0 12px;}}
.tx-row{{display:flex;align-items:center;justify-content:space-between;background:{P['card']};border:1px solid {P['border']};border-radius:10px;padding:12px 16px;margin-bottom:8px;}}
.tx-cat{{font-size:13px;font-weight:500;color:{P['text']};}} .tx-date{{font-size:12px;color:{P['muted']};}}
.tx-note{{font-size:12px;color:{P['muted']};font-style:italic;}}
.tx-amt-income{{font-weight:700;color:{P['green']};font-family:'Space Grotesk',sans-serif;}}
.tx-amt-expense{{font-weight:700;color:{P['red']};font-family:'Space Grotesk',sans-serif;}}
.demo-banner{{background:linear-gradient(90deg,{P['blue']}22,{P['purple']}22);border:1px solid {P['blue']}55;border-radius:10px;padding:10px 16px;margin-bottom:16px;font-size:13px;color:{P['blue']};text-align:center;font-weight:500;}}
.demo-hint{{background:{P['bg']};border:1px solid {P['border']};border-radius:10px;padding:12px 16px;margin-top:16px;font-size:12px;color:{P['muted']};text-align:center;}}
.stButton>button{{background:{P['green']};color:{P['btn_txt']};border:none;border-radius:8px;font-weight:700;font-family:'Space Grotesk',sans-serif;padding:10px 20px;width:100%;transition:opacity 0.15s;}}
.stButton>button:hover{{opacity:0.85;color:{P['btn_txt']};}}
.stSelectbox>div>div,.stNumberInput>div>div>input,.stTextInput>div>div>input{{background:{P['bg']} !important;border:1px solid {P['border']} !important;border-radius:8px !important;color:{P['text']} !important;}}
[data-testid="stDateInput"] input{{background:{P['bg']} !important;border:1px solid {P['border']} !important;border-radius:8px !important;color:{P['text']} !important;}}
.stRadio>div{{gap:10px;}} .stRadio label{{color:{P['text']} !important;}}
footer{{display:none;}}
</style>
""", unsafe_allow_html=True)

# ── Google Sheets connection ───────────────────────────────────────────────────
@st.cache_resource
def get_sheet():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    # Try Streamlit secrets first (for deployed app), then local credentials.json
    if "gcp_service_account" in st.secrets:
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
    else:
        creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
    client = gspread.authorize(creds)
    return client.open_by_key(SHEET_ID)

def ensure_worksheet(sheet, name):
    try:
        ws = sheet.worksheet(name)
    except gspread.exceptions.WorksheetNotFound:
        ws = sheet.add_worksheet(title=name, rows=1000, cols=6)
        ws.append_row(["date", "type", "category", "amount", "note"])
    return ws

def load_data_sheet(account):
    try:
        sheet = get_sheet()
        ws    = ensure_worksheet(sheet, account)
        data  = ws.get_all_records()
        if not data:
            return pd.DataFrame(columns=["date","type","category","amount","note"])
        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"])
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
        return df
    except Exception as e:
        st.error(f"Google Sheets error: {e}")
        return pd.DataFrame(columns=["date","type","category","amount","note"])

def save_transaction_sheet(account, tx_date, tx_type, category, amount, note):
    try:
        sheet = get_sheet()
        ws    = ensure_worksheet(sheet, account)
        ws.append_row([str(tx_date), tx_type, category, float(amount), note])
        return True
    except Exception as e:
        st.error(f"Could not save: {e}")
        return False

def delete_row_by_index(account, row_index):
    # row_index is 0-based from dataframe; +2 to account for header row and 1-based sheet index
    try:
        sheet = get_sheet()
        ws    = ensure_worksheet(sheet, account)
        ws.delete_rows(row_index + 2)
        return True
    except Exception as e:
        st.error(f"Could not delete: {e}")
        return False

# ── Demo sample data ──────────────────────────────────────────────────────────
def generate_demo_data():
    today = date.today()
    rows = [
        (today.replace(day=1), "Income",  "Salary",       85000, "Monthly salary"),
        (today.replace(day=5), "Income",  "Freelance",    12000, "Website project"),
        (today.replace(day=10),"Income",  "Investment",    3500, "Dividends"),
        (today.replace(day=1), "Expense", "Rent",         18000, "Monthly rent"),
        (today.replace(day=2), "Expense", "Utilities",     2200, "Electricity & water"),
        (today.replace(day=3), "Expense", "Food",          4500, "Groceries"),
        (today.replace(day=6), "Expense", "Transport",     1800, "Fuel & cab"),
        (today.replace(day=8), "Expense", "Food",          1200, "Dining out"),
        (today.replace(day=12),"Expense", "Health",        2500, "Doctor visit"),
        (today.replace(day=14),"Expense", "Shopping",      3800, "Clothes"),
        (today.replace(day=16),"Expense", "Entertainment", 1500, "Movies & OTT"),
        (today.replace(day=18),"Expense", "Food",           800, "Swiggy orders"),
    ]
    return pd.DataFrame(rows, columns=["date","type","category","amount","note"])

# ══════════════════════════════════════════════════════════════════════════════
# ── LOGIN SCREEN ──────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state.logged_in:
    tcol1, tcol2 = st.columns([9,1])
    with tcol2:
        if st.button("☀️" if st.session_state.dark_mode else "🌙"):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)
    col = st.columns([1,2,1])[1]
    with col:
        st.markdown(f"<h1 style='text-align:center'>💸 SpendWise</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center;color:{P['muted']};margin-bottom:24px'>Your personal finance tracker</p>", unsafe_allow_html=True)
        username    = st.text_input("Username", placeholder="Enter username")
        password    = st.text_input("Password", type="password", placeholder="Enter password")
        remember_me = st.checkbox("Keep me logged in on this device")
        if st.button("Login"):
            uname = username.strip().lower()
            user  = USERS.get(uname)
            if user and password == user["password"]:
                st.session_state.logged_in = True
                st.session_state.username  = uname
                st.session_state.account   = user["accounts"][0]
                if remember_me and not user.get("is_demo"):
                    token = make_token(uname, user["password"])
                    st.session_state.remember_token = token
                    st.query_params["token"] = token
                else:
                    # clear any old token
                    st.session_state.pop("remember_token", None)
                    st.query_params.clear()
                st.rerun()
            else:
                st.error("Invalid username or password.")
        st.markdown(f"""
        <div class="demo-hint">
            🧪 <b>Try the demo</b><br>
            Username: <b>demo</b> &nbsp;|&nbsp; Password: <b>demo123</b>
        </div>""", unsafe_allow_html=True)
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# ── MAIN APP ──────────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════
user_cfg = USERS[st.session_state.username]
is_demo  = user_cfg["is_demo"]
accounts = user_cfg["accounts"]

# Load data
df_key = f"df_{st.session_state.account}"
if df_key not in st.session_state:
    if is_demo:
        st.session_state[df_key] = generate_demo_data()
    else:
        st.session_state[df_key] = load_data_sheet(st.session_state.account)
df = st.session_state[df_key]

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    t1, t2 = st.columns([2,1])
    with t1:
        st.markdown("## 💸 SpendWise")
        st.markdown(f"<p style='color:{P['muted']};font-size:13px;margin-top:-8px'>Hi, {st.session_state.username.capitalize()}!</p>", unsafe_allow_html=True)
    with t2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("☀️" if st.session_state.dark_mode else "🌙"):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()

    st.markdown("---")

    # Account switcher
    if len(accounts) > 1:
        st.markdown("### Account")
        acc_cols = st.columns(len(accounts))
        for i, acc in enumerate(accounts):
            with acc_cols[i]:
                if st.button(acc, use_container_width=True, key=f"acc_{i}"):
                    st.session_state.account = acc
                    new_key = f"df_{acc}"
                    if new_key not in st.session_state:
                        st.session_state[new_key] = load_data_sheet(acc)
                    st.rerun()
        st.markdown(f"**Viewing:** 👤 {st.session_state.account}")
        st.markdown("---")
        df_key = f"df_{st.session_state.account}"
        df     = st.session_state[df_key]

    st.markdown("### Add Transaction")
    if is_demo:
        st.info("🧪 Demo mode — adding transactions is disabled.")
    else:
        tx_type  = st.radio("Type", ["Income","Expense"], horizontal=True)
        cats     = INCOME_CATEGORIES if tx_type == "Income" else EXPENSE_CATEGORIES
        category = st.selectbox("Category", cats)
        amount   = st.number_input("Amount (₹)", min_value=0.01, step=100.0, format="%.2f")
        tx_date  = st.date_input("Date", value=date.today())
        note     = st.text_input("Note (optional)", placeholder="e.g. Lunch with team")

        if st.button("Add Transaction"):
            if amount > 0:
                ok = save_transaction_sheet(st.session_state.account, tx_date, tx_type, category, amount, note)
                if ok:
                    # reload from sheet
                    st.session_state[df_key] = load_data_sheet(st.session_state.account)
                    st.success("Saved to Google Sheets! ✅")
                    st.rerun()
            else:
                st.error("Amount must be greater than 0.")

    st.markdown("---")
    st.markdown("### Filter by Month")
    months = ["All"]
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        months += sorted(df["date"].dt.to_period("M").astype(str).unique(), reverse=True)
    selected_month = st.selectbox("Month", months)

    st.markdown("---")
    if st.button("🔄 Refresh Data"):
        if not is_demo:
            st.session_state[df_key] = load_data_sheet(st.session_state.account)
            st.rerun()

    if st.button("🚪 Logout"):
        st.query_params.clear()
        st.session_state.clear()
        st.rerun()

# ── Filter ────────────────────────────────────────────────────────────────────
filtered = df.copy()
if selected_month != "All" and not df.empty:
    filtered = df[df["date"].dt.to_period("M").astype(str) == selected_month]

# ── Dashboard ─────────────────────────────────────────────────────────────────
st.markdown(f"# 👤 {st.session_state.account} Dashboard")
if is_demo:
    st.markdown(f'<div class="demo-banner">🧪 Demo Mode — sample data shown for preview</div>', unsafe_allow_html=True)

if filtered.empty:
    st.info("No transactions yet. Add your first one from the sidebar! 👈")
else:
    income_df  = filtered[filtered["type"] == "Income"]
    expense_df = filtered[filtered["type"] == "Expense"]
    total_income  = income_df["amount"].sum()
    total_expense = expense_df["amount"].sum()
    net_savings   = total_income - total_expense
    savings_rate  = (net_savings / total_income * 100) if total_income > 0 else 0

    c1,c2,c3,c4 = st.columns(4)
    for col, label, value, cls in [
        (c1,"Total Income",  f"₹{total_income:,.0f}", "metric-green"),
        (c2,"Total Expenses",f"₹{total_expense:,.0f}","metric-red"),
        (c3,"Net Savings",   f"₹{net_savings:,.0f}",  "metric-green" if net_savings>=0 else "metric-red"),
        (c4,"Savings Rate",  f"{savings_rate:.1f}%",  "metric-blue"),
    ]:
        with col:
            st.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value {cls}">{value}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_left, col_right = st.columns([1.2,1])

    with col_left:
        st.markdown('<div class="section-title">Spending by Category</div>', unsafe_allow_html=True)
        if not expense_df.empty:
            cat_totals = expense_df.groupby("category")["amount"].sum().sort_values(ascending=True)
            fig, ax = plt.subplots(figsize=(6, max(3, len(cat_totals)*0.55)))
            fig.patch.set_facecolor(P["card"]); ax.set_facecolor(P["card"])
            bar_colors = [P["red"],P["purple"],P["blue"],"#F2965C","#5CF2D3","#F2C45C","#A0F25C","#F25C9E"]
            bars = ax.barh(cat_totals.index, cat_totals.values, color=bar_colors[:len(cat_totals)], height=0.55, zorder=3)
            for bar, val in zip(bars, cat_totals.values):
                ax.text(bar.get_width()+max(cat_totals.values)*0.01, bar.get_y()+bar.get_height()/2,
                        f"₹{val:,.0f}", va="center", ha="left", color=P["text"], fontsize=10, fontweight="600")
            ax.set_xlim(0, max(cat_totals.values)*1.25)
            ax.tick_params(axis="y", colors=P["text"], labelsize=11)
            ax.spines[["top","right","left","bottom"]].set_visible(False)
            ax.xaxis.set_visible(False); ax.yaxis.set_tick_params(length=0)
            fig.tight_layout(); st.pyplot(fig)

    with col_right:
        st.markdown('<div class="section-title">Income vs Expenses</div>', unsafe_allow_html=True)
        fig2, ax2 = plt.subplots(figsize=(4,4))
        fig2.patch.set_facecolor(P["card"]); ax2.set_facecolor(P["card"])
        ax2.pie([total_income or 1, total_expense or 0], colors=[P["green"],P["red"]], startangle=90,
                wedgeprops=dict(width=0.55, edgecolor=P["card"], linewidth=3))
        ax2.legend(handles=[mpatches.Patch(color=P["green"],label=f"Income  ₹{total_income:,.0f}"),
                             mpatches.Patch(color=P["red"],  label=f"Expenses ₹{total_expense:,.0f}")],
                   loc="lower center", bbox_to_anchor=(0.5,-0.12), ncol=1, frameon=False, fontsize=10, labelcolor=P["text"])
        ax2.set_title(f"₹{net_savings:,.0f}\nSaved", color=P["text"], fontsize=14, fontweight="bold", y=0.45, va="center")
        fig2.tight_layout(); st.pyplot(fig2)

    st.markdown('<div class="section-title">Recent Transactions</div>', unsafe_allow_html=True)

    # confirm state
    if "confirm_delete" not in st.session_state:
        st.session_state.confirm_delete = None

    recent = filtered.sort_values("date", ascending=False).head(20)

    for df_idx, row in recent.iterrows():
        is_inc    = row["type"] == "Income"
        sign      = "+" if is_inc else "−"
        amt_class = "tx-amt-income" if is_inc else "tx-amt-expense"
        note_html = f'<span class="tx-note"> · {row["note"]}</span>' if pd.notna(row["note"]) and str(row["note"]).strip() else ""

        col_info, col_amt, col_btn = st.columns([5, 2, 1])

        with col_info:
            st.markdown(f"""<div style="padding:10px 0">
                <span class="tx-cat">{row['category']}</span>{note_html}<br>
                <span class="tx-date">{pd.to_datetime(row['date']).strftime('%d %b %Y')}</span>
            </div>""", unsafe_allow_html=True)

        with col_amt:
            st.markdown(f"""<div style="padding:14px 0">
                <span class="{amt_class}">{sign}₹{row['amount']:,.2f}</span>
            </div>""", unsafe_allow_html=True)

        with col_btn:
            if not is_demo:
                if st.session_state.confirm_delete == df_idx:
                    # show confirm / cancel
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("✅", key=f"confirm_{df_idx}", help="Confirm delete"):
                            ok = delete_row_by_index(st.session_state.account, df_idx)
                            if ok:
                                st.session_state.confirm_delete = None
                                st.session_state[df_key] = load_data_sheet(st.session_state.account)
                                st.rerun()
                    with c2:
                        if st.button("❌", key=f"cancel_{df_idx}", help="Cancel"):
                            st.session_state.confirm_delete = None
                            st.rerun()
                else:
                    if st.button("🗑️", key=f"del_{df_idx}", help="Delete this transaction"):
                        st.session_state.confirm_delete = df_idx
                        st.rerun()

        st.markdown(f"<hr style='border:none;border-top:1px solid {P['border']};margin:0'>", unsafe_allow_html=True)
