# 💸 SpendWise — Personal Finance Tracker

A clean, mobile-friendly finance tracker built with Python & Streamlit.

## Features
- ➕ Log income and expenses with categories
- 📊 Visual charts — spending breakdown & income vs expenses donut
- 📅 Filter transactions by month
- 💾 Data saved locally as CSV (persists between sessions)
- 📱 Works on mobile browsers when deployed

## Tech Stack
- **Python** — core logic
- **Streamlit** — web UI
- **Pandas** — data handling
- **Matplotlib** — charts

## Run Locally

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app
streamlit run app.py
```

Then open http://localhost:8501 in your browser.

## Deploy (Free)

1. Push this folder to a GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Set main file as `app.py`
5. Click **Deploy** — you get a public URL!

## Project Structure

```
finance-tracker/
├── app.py              # Main Streamlit app
├── requirements.txt    # Python dependencies
├── README.md           # This file
└── transactions.csv    # Auto-created when you add transactions
```
