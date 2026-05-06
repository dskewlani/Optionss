# ⚡ Options Trader Pro

AI-powered Call & Put options intelligence for Indian markets — built with Streamlit.

## Features

- 🔍 **Signal Scanner** — Multi-factor technical + fundamental analysis (RSI, MACD, ADX, Bollinger, Stochastic, EMA stack, CCI, Williams %R, Volume, P/E, Beta)
- ⚡ **Auto Trading Engine** — Set a timer, AI picks the best CALL/PUT signals, auto-executes, manages stops/targets, squares off when time expires, and downloads a full reasoning report
- 📋 **Watchlist** — Build custom CALL/PUT watchlists and manually buy/sell
- 💼 **Portfolio** — Real-time P&L on all open positions with one-click square-off
- 📜 **History** — Full trade history with CSV download

---

## 🚀 Run Locally

```bash
git clone https://github.com/YOUR_USERNAME/options-trader-pro.git
cd options-trader-pro
pip install -r requirements.txt
streamlit run app.py
```

Then open `http://localhost:8501` in your browser.

---

## 🌐 Deploy on Streamlit Cloud (Free)

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit — Options Trader Pro"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/options-trader-pro.git
   git push -u origin main
   ```

2. **Go to** [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub

3. Click **"New app"** → select your repo → set **Main file path** to `app.py` → Deploy

4. Your app will be live at `https://YOUR_USERNAME-options-trader-pro-app-XXXXX.streamlit.app`

> ✅ Streamlit Cloud is **free** for public repos and auto-redeploys on every `git push`.

---

## 📁 File Structure

```
options-trader-pro/
├── app.py                  # Main Streamlit app
├── requirements.txt        # Python dependencies
├── .streamlit/
│   └── config.toml         # Theme + server config
└── README.md
```

---

## 🔧 Configuration

Edit inside `app.py`:

| Variable | Default | Description |
|---|---|---|
| `INDIAN_STOCKS` | 20+ stocks | Universe of stocks to scan |
| `starting_capital` | ₹1,00,000 | Capital for the session |
| `capital_per_trade` | ₹5,000 | Allocated per auto-trade |
| `auto_mins` | 15 | Default auto-trade duration |

---

## ⚠️ Disclaimer

This is for **educational and simulation purposes only**. Not financial advice. Options trading involves significant risk of loss. Always consult a SEBI-registered financial advisor before trading.

---

## 📦 Tech Stack

- **Streamlit** — UI and real-time updates
- **yfinance** — Live market data (NSE/BSE)
- **Plotly** — Interactive charts
- **SciPy** — Black-Scholes option pricing
- **Pandas / NumPy** — Data processing
