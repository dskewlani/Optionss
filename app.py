import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import threading
import json
import os
from scipy.stats import norm
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="Options Trader Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap');

:root {
    --bg: #0a0e1a;
    --surface: #111827;
    --border: #1e293b;
    --accent: #00d4ff;
    --green: #00ff88;
    --red: #ff3366;
    --yellow: #ffd700;
    --text: #e2e8f0;
    --muted: #64748b;
}

html, body, [class*="css"] {
    font-family: 'Syne', sans-serif;
    background-color: var(--bg);
    color: var(--text);
}

.stApp { background: var(--bg); }

.metric-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px;
    text-align: center;
    position: relative;
    overflow: hidden;
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--accent), var(--green));
}
.metric-value { font-size: 1.8rem; font-weight: 800; font-family: 'JetBrains Mono'; }
.metric-label { font-size: 0.75rem; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; }
.green { color: var(--green); }
.red { color: var(--red); }
.yellow { color: var(--yellow); }
.accent { color: var(--accent); }

.signal-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 700;
    font-family: 'JetBrains Mono';
    text-transform: uppercase;
}
.badge-call { background: rgba(0,255,136,0.15); color: var(--green); border: 1px solid var(--green); }
.badge-put { background: rgba(255,51,102,0.15); color: var(--red); border: 1px solid var(--red); }
.badge-neutral { background: rgba(255,215,0,0.15); color: var(--yellow); border: 1px solid var(--yellow); }

.trade-row {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px 16px;
    margin: 6px 0;
    display: flex;
    align-items: center;
    gap: 12px;
}

.auto-trade-box {
    background: linear-gradient(135deg, rgba(0,212,255,0.05), rgba(0,255,136,0.05));
    border: 1px solid var(--accent);
    border-radius: 16px;
    padding: 24px;
    text-align: center;
}

.section-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--accent);
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border);
}

.stButton > button {
    background: linear-gradient(135deg, #00d4ff, #00ff88);
    color: #0a0e1a;
    font-weight: 700;
    font-family: 'Syne';
    border: none;
    border-radius: 8px;
    padding: 10px 24px;
}
.stButton > button:hover { opacity: 0.85; }

.danger-btn > button {
    background: linear-gradient(135deg, #ff3366, #ff6b35) !important;
    color: white !important;
}

.scrollable {
    max-height: 420px;
    overflow-y: auto;
}
</style>
""", unsafe_allow_html=True)

# ─── Session State Init ────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "portfolio": [],            # list of open positions
        "history": [],              # closed trades
        "watchlist": [],            # {"symbol": "RELIANCE.NS", "type": "CALL/PUT", "strike": x, "expiry": "..."}
        "auto_trading": False,
        "auto_trade_end": None,
        "auto_trade_log": [],       # reasoning log
        "auto_pnl": 0.0,
        "capital": 100000.0,        # starting capital in INR
        "used_capital": 0.0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ─── Core Functions ────────────────────────────────────────────────────────────

INDIAN_STOCKS = [
    "RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS",
    "SBIN.NS","BAJFINANCE.NS","WIPRO.NS","AXISBANK.NS","KOTAKBANK.NS",
    "LT.NS","HCLTECH.NS","ASIANPAINT.NS","MARUTI.NS","TITAN.NS",
    "SUNPHARMA.NS","BHARTIARTL.NS","NESTLEIND.NS","ULTRACEMCO.NS","POWERGRID.NS",
    "NIFTY50","BANKNIFTY","SENSEX"
]

@st.cache_data(ttl=60)
def fetch_price_data(symbol, period="3mo", interval="1d"):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        if df.empty:
            return None
        df.index = pd.to_datetime(df.index)
        return df
    except Exception:
        return None

@st.cache_data(ttl=30)
def get_live_price(symbol):
    try:
        t = yf.Ticker(symbol)
        info = t.fast_info
        return float(info.last_price)
    except Exception:
        return None

def compute_indicators(df):
    """Compute all technical indicators."""
    if df is None or len(df) < 20:
        return {}
    
    close = df['Close']
    high = df['High']
    low = df['Low']
    volume = df['Volume']

    # RSI
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(span=14).mean()
    loss = (-delta.clip(upper=0)).ewm(span=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    # MACD
    ema12 = close.ewm(span=12).mean()
    ema26 = close.ewm(span=26).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9).mean()
    hist = macd - signal

    # Bollinger Bands
    sma20 = close.rolling(20).mean()
    std20 = close.rolling(20).std()
    bb_upper = sma20 + 2 * std20
    bb_lower = sma20 - 2 * std20
    bb_pct = (close - bb_lower) / (bb_upper - bb_lower)

    # ATR
    tr = pd.DataFrame({
        'hl': high - low,
        'hc': (high - close.shift()).abs(),
        'lc': (low - close.shift()).abs()
    }).max(axis=1)
    atr = tr.rolling(14).mean()

    # EMA stack
    ema9 = close.ewm(span=9).mean()
    ema21 = close.ewm(span=21).mean()
    ema50 = close.ewm(span=50).mean()
    ema200 = close.ewm(span=200).mean()

    # Stochastic
    low14 = low.rolling(14).min()
    high14 = high.rolling(14).max()
    stoch_k = 100 * (close - low14) / (high14 - low14)
    stoch_d = stoch_k.rolling(3).mean()

    # Volume MA
    vol_ma = volume.rolling(20).mean()
    vol_ratio = volume / vol_ma

    # Williams %R
    williams_r = -100 * (high14 - close) / (high14 - low14)

    # CCI
    tp = (high + low + close) / 3
    cci = (tp - tp.rolling(20).mean()) / (0.015 * tp.rolling(20).std())

    # ADX
    plus_dm = high.diff().clip(lower=0)
    minus_dm = (-low.diff()).clip(lower=0)
    atr_14 = atr
    plus_di = 100 * (plus_dm.ewm(span=14).mean() / atr_14)
    minus_di = 100 * (minus_dm.ewm(span=14).mean() / atr_14)
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    adx = dx.ewm(span=14).mean()

    return {
        "rsi": float(rsi.iloc[-1]),
        "macd": float(macd.iloc[-1]),
        "macd_signal": float(signal.iloc[-1]),
        "macd_hist": float(hist.iloc[-1]),
        "bb_pct": float(bb_pct.iloc[-1]),
        "bb_upper": float(bb_upper.iloc[-1]),
        "bb_lower": float(bb_lower.iloc[-1]),
        "bb_mid": float(sma20.iloc[-1]),
        "atr": float(atr.iloc[-1]),
        "ema9": float(ema9.iloc[-1]),
        "ema21": float(ema21.iloc[-1]),
        "ema50": float(ema50.iloc[-1]),
        "ema200": float(ema200.iloc[-1]),
        "stoch_k": float(stoch_k.iloc[-1]),
        "stoch_d": float(stoch_d.iloc[-1]),
        "vol_ratio": float(vol_ratio.iloc[-1]),
        "williams_r": float(williams_r.iloc[-1]),
        "cci": float(cci.iloc[-1]),
        "adx": float(adx.iloc[-1]),
        "plus_di": float(plus_di.iloc[-1]),
        "minus_di": float(minus_di.iloc[-1]),
        "close": float(close.iloc[-1]),
        "sma20": float(sma20.iloc[-1]),
    }

def get_fundamentals(symbol):
    try:
        t = yf.Ticker(symbol)
        info = t.info
        return {
            "pe": info.get("trailingPE", None),
            "pb": info.get("priceToBook", None),
            "roe": info.get("returnOnEquity", None),
            "debt_equity": info.get("debtToEquity", None),
            "eps": info.get("trailingEps", None),
            "beta": info.get("beta", None),
            "market_cap": info.get("marketCap", None),
            "52w_high": info.get("fiftyTwoWeekHigh", None),
            "52w_low": info.get("fiftyTwoWeekLow", None),
            "avg_vol": info.get("averageVolume", None),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
        }
    except Exception:
        return {}

def score_signal(indicators, fundamentals):
    """
    Multi-factor scoring engine.
    Returns (call_score, put_score, reasoning_list)
    """
    call_score = 0
    put_score = 0
    reasoning = []

    if not indicators:
        return 0, 0, ["Insufficient data"]

    rsi = indicators.get("rsi", 50)
    macd = indicators.get("macd", 0)
    macd_signal = indicators.get("macd_signal", 0)
    macd_hist = indicators.get("macd_hist", 0)
    bb_pct = indicators.get("bb_pct", 0.5)
    stoch_k = indicators.get("stoch_k", 50)
    stoch_d = indicators.get("stoch_d", 50)
    vol_ratio = indicators.get("vol_ratio", 1)
    williams_r = indicators.get("williams_r", -50)
    cci = indicators.get("cci", 0)
    adx = indicators.get("adx", 20)
    plus_di = indicators.get("plus_di", 25)
    minus_di = indicators.get("minus_di", 25)
    close = indicators.get("close", 0)
    ema9 = indicators.get("ema9", 0)
    ema21 = indicators.get("ema21", 0)
    ema50 = indicators.get("ema50", 0)
    ema200 = indicators.get("ema200", 0)
    atr = indicators.get("atr", 0)

    # ── RSI ──
    if rsi < 30:
        call_score += 3; reasoning.append(f"RSI={rsi:.1f} — Oversold → CALL +3")
    elif rsi < 40:
        call_score += 1; reasoning.append(f"RSI={rsi:.1f} — Mildly oversold → CALL +1")
    elif rsi > 70:
        put_score += 3; reasoning.append(f"RSI={rsi:.1f} — Overbought → PUT +3")
    elif rsi > 60:
        put_score += 1; reasoning.append(f"RSI={rsi:.1f} — Mildly overbought → PUT +1")
    else:
        reasoning.append(f"RSI={rsi:.1f} — Neutral")

    # ── MACD ──
    if macd > macd_signal and macd_hist > 0:
        call_score += 2; reasoning.append(f"MACD bullish crossover → CALL +2")
    elif macd < macd_signal and macd_hist < 0:
        put_score += 2; reasoning.append(f"MACD bearish crossover → PUT +2")

    # ── Bollinger Bands ──
    if bb_pct < 0.1:
        call_score += 2; reasoning.append(f"Price at lower BB ({bb_pct:.2f}) → CALL +2")
    elif bb_pct > 0.9:
        put_score += 2; reasoning.append(f"Price at upper BB ({bb_pct:.2f}) → PUT +2")

    # ── Stochastic ──
    if stoch_k < 20 and stoch_k > stoch_d:
        call_score += 2; reasoning.append(f"Stoch K={stoch_k:.1f} oversold + crossing up → CALL +2")
    elif stoch_k > 80 and stoch_k < stoch_d:
        put_score += 2; reasoning.append(f"Stoch K={stoch_k:.1f} overbought + crossing down → PUT +2")

    # ── EMA Trend ──
    if close > ema9 > ema21 > ema50:
        call_score += 3; reasoning.append(f"Strong bullish EMA stack (price > 9>21>50) → CALL +3")
    elif close < ema9 < ema21 < ema50:
        put_score += 3; reasoning.append(f"Strong bearish EMA stack (price < 9<21<50) → PUT +3")
    elif close > ema50 > ema200:
        call_score += 1; reasoning.append(f"Above EMA50 & EMA200 → CALL +1")
    elif close < ema50 < ema200:
        put_score += 1; reasoning.append(f"Below EMA50 & EMA200 → PUT +1")

    # ── ADX + DI ──
    if adx > 25:
        if plus_di > minus_di:
            call_score += 2; reasoning.append(f"ADX={adx:.1f} strong trend, +DI>{minus_di:.1f} → CALL +2")
        else:
            put_score += 2; reasoning.append(f"ADX={adx:.1f} strong trend, -DI>{plus_di:.1f} → PUT +2")

    # ── Williams %R ──
    if williams_r < -80:
        call_score += 1; reasoning.append(f"Williams R={williams_r:.1f} oversold → CALL +1")
    elif williams_r > -20:
        put_score += 1; reasoning.append(f"Williams R={williams_r:.1f} overbought → PUT +1")

    # ── CCI ──
    if cci < -100:
        call_score += 1; reasoning.append(f"CCI={cci:.1f} oversold → CALL +1")
    elif cci > 100:
        put_score += 1; reasoning.append(f"CCI={cci:.1f} overbought → PUT +1")

    # ── Volume ──
    if vol_ratio > 1.5:
        if call_score > put_score:
            call_score += 1; reasoning.append(f"High volume ({vol_ratio:.1f}x avg) confirms bullish → CALL +1")
        elif put_score > call_score:
            put_score += 1; reasoning.append(f"High volume ({vol_ratio:.1f}x avg) confirms bearish → PUT +1")

    # ── Fundamentals ──
    beta = fundamentals.get("beta", 1)
    pe = fundamentals.get("pe", None)
    if pe and pe < 15:
        call_score += 1; reasoning.append(f"Low P/E ({pe:.1f}) → fundamentally cheap → CALL +1")
    elif pe and pe > 50:
        put_score += 1; reasoning.append(f"High P/E ({pe:.1f}) → overvalued → PUT +1")

    return call_score, put_score, reasoning

def get_recommendation(symbol):
    """Full recommendation with target."""
    df = fetch_price_data(symbol, period="3mo", interval="1d")
    indicators = compute_indicators(df)
    fundamentals = get_fundamentals(symbol)
    call_score, put_score, reasoning = score_signal(indicators, fundamentals)
    price = indicators.get("close", 0) or get_live_price(symbol) or 0
    atr = indicators.get("atr", price * 0.02)

    if call_score > put_score and call_score >= 5:
        rec = "CALL"
        strength = min(100, int((call_score / (call_score + put_score + 1)) * 100))
        target = round(price * (1 + 0.015 * (call_score / 5)), 2)
        stop = round(price - 1.5 * atr, 2)
    elif put_score > call_score and put_score >= 5:
        rec = "PUT"
        strength = min(100, int((put_score / (call_score + put_score + 1)) * 100))
        target = round(price * (1 - 0.015 * (put_score / 5)), 2)
        stop = round(price + 1.5 * atr, 2)
    else:
        rec = "NEUTRAL"
        strength = 50
        target = price
        stop = price

    return {
        "symbol": symbol,
        "price": price,
        "recommendation": rec,
        "strength": strength,
        "target": target,
        "stop": stop,
        "call_score": call_score,
        "put_score": put_score,
        "indicators": indicators,
        "fundamentals": fundamentals,
        "reasoning": reasoning,
    }

# ─── Black-Scholes for option premium estimation ───────────────────────────────
def bs_price(S, K, T, r, sigma, option_type="call"):
    if T <= 0 or sigma <= 0:
        return max(0, S - K) if option_type == "call" else max(0, K - S)
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    if option_type == "call":
        return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    else:
        return K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

def estimate_iv(df):
    if df is None or len(df) < 2:
        return 0.25
    returns = df['Close'].pct_change().dropna()
    return float(returns.std() * np.sqrt(252))

def get_nearby_strikes(price, n=5, step_pct=0.01):
    step = max(50, round(price * step_pct / 50) * 50)
    atm = round(price / step) * step
    return [atm + step * i for i in range(-n, n+1)]

# ─── Auto Trading Engine ────────────────────────────────────────────────────────
def auto_trade_step(symbols, capital_per_trade=5000):
    """Execute one auto-trade cycle. Returns list of new trades."""
    new_trades = []
    for symbol in symbols[:5]:  # limit to 5 per cycle
        try:
            rec = get_recommendation(symbol)
            if rec["recommendation"] == "NEUTRAL":
                continue
            if rec["strength"] < 60:
                continue

            price = rec["price"]
            if not price or price == 0:
                continue

            opt_type = rec["recommendation"]
            strike = round(price / 50) * 50
            expiry_days = 7
            T = expiry_days / 365
            sigma = estimate_iv(fetch_price_data(symbol, "1mo", "1d"))
            premium = bs_price(price, strike, T, 0.065, sigma, opt_type.lower())
            lots = max(1, int(capital_per_trade / (premium * 50)))

            trade = {
                "id": f"{symbol}_{opt_type}_{int(time.time())}",
                "symbol": symbol,
                "type": opt_type,
                "strike": strike,
                "entry_price": price,
                "premium": round(premium, 2),
                "lots": lots,
                "qty": lots * 50,
                "target": rec["target"],
                "stop": rec["stop"],
                "entry_time": datetime.now().strftime("%H:%M:%S"),
                "status": "OPEN",
                "pnl": 0.0,
                "reasoning": rec["reasoning"],
                "indicators": rec["indicators"],
                "strength": rec["strength"],
            }
            new_trades.append(trade)
        except Exception:
            continue
    return new_trades

def square_off_positions(log_entries):
    """Close all open positions and return P&L + log."""
    closed = []
    total_pnl = 0
    for pos in st.session_state.portfolio:
        price = get_live_price(pos["symbol"]) or pos["entry_price"]
        if pos["type"] == "CALL":
            pnl = (price - pos["entry_price"]) * pos["qty"]
        else:
            pnl = (pos["entry_price"] - price) * pos["qty"]
        
        pos_closed = {**pos, "exit_price": price, "exit_time": datetime.now().strftime("%H:%M:%S"),
                      "pnl": round(pnl, 2), "status": "CLOSED"}
        closed.append(pos_closed)
        total_pnl += pnl
    
    st.session_state.history.extend(closed)
    st.session_state.portfolio = []
    st.session_state.used_capital = 0.0
    return closed, total_pnl

def generate_trade_report(closed_trades, total_pnl, duration_mins):
    """Generate a downloadable text report."""
    lines = []
    lines.append("=" * 70)
    lines.append("         OPTIONS TRADER PRO — AUTO TRADING REPORT")
    lines.append("=" * 70)
    lines.append(f"Generated  : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Duration   : {duration_mins} minutes")
    lines.append(f"Total Trades: {len(closed_trades)}")
    lines.append(f"Net P&L    : ₹{total_pnl:,.2f}")
    lines.append("")

    for i, t in enumerate(closed_trades, 1):
        lines.append(f"─" * 70)
        lines.append(f"Trade #{i}  |  {t['symbol']}  |  {t['type']}")
        lines.append(f"  Strike     : ₹{t['strike']}")
        lines.append(f"  Entry Time : {t.get('entry_time', 'N/A')}")
        lines.append(f"  Exit Time  : {t.get('exit_time', 'N/A')}")
        lines.append(f"  Entry Price: ₹{t['entry_price']}")
        lines.append(f"  Exit Price : ₹{t.get('exit_price', 'N/A')}")
        lines.append(f"  Premium    : ₹{t.get('premium', 0)}")
        lines.append(f"  Lots × Qty : {t.get('lots',1)} × {t.get('qty',50)}")
        lines.append(f"  Signal Strength: {t.get('strength', 0)}%")
        lines.append(f"  P&L        : ₹{t['pnl']:,.2f}  {'✅' if t['pnl'] >= 0 else '❌'}")
        lines.append("")
        lines.append("  SIGNAL REASONING:")
        for r in t.get("reasoning", []):
            lines.append(f"    • {r}")
        lines.append("")
        inds = t.get("indicators", {})
        if inds:
            lines.append("  KEY INDICATORS AT ENTRY:")
            lines.append(f"    RSI       : {inds.get('rsi', 'N/A'):.1f}" if inds.get('rsi') else "    RSI: N/A")
            lines.append(f"    MACD      : {inds.get('macd', 'N/A'):.4f}" if inds.get('macd') else "")
            lines.append(f"    BB %      : {inds.get('bb_pct', 'N/A'):.2f}" if inds.get('bb_pct') else "")
            lines.append(f"    ADX       : {inds.get('adx', 'N/A'):.1f}" if inds.get('adx') else "")
            lines.append(f"    Stoch K/D : {inds.get('stoch_k', 0):.1f} / {inds.get('stoch_d', 0):.1f}")
            lines.append(f"    Vol Ratio : {inds.get('vol_ratio', 1):.2f}x")
        lines.append("")

    lines.append("=" * 70)
    lines.append("END OF REPORT")
    return "\n".join(lines)

# ══════════════════════════════════════════════════════════════════════════════
#  UI
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<h1 style='font-family:Syne;font-weight:800;font-size:2.2rem;background:linear-gradient(90deg,#00d4ff,#00ff88);
-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:4px;'>
⚡ Options Trader Pro</h1>
<p style='color:#64748b;font-size:0.85rem;margin-top:0;'>AI-Powered Call & Put Intelligence · Indian Markets</p>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    starting_capital = st.number_input("💰 Capital (₹)", value=100000, step=10000)
    st.session_state.capital = float(starting_capital)
    capital_per_trade = st.number_input("Per-Trade Capital (₹)", value=5000, step=1000)
    
    st.markdown("---")
    st.markdown("### 📡 Market Universe")
    selected_stocks = st.multiselect(
        "Stocks to Monitor",
        INDIAN_STOCKS,
        default=["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS"]
    )
    
    st.markdown("---")
    st.markdown("### 📊 Portfolio Summary")
    open_pos = len(st.session_state.portfolio)
    total_hist_pnl = sum(t.get("pnl", 0) for t in st.session_state.history)
    st.metric("Open Positions", open_pos)
    st.metric("Closed Trades", len(st.session_state.history))
    st.metric("Realized P&L", f"₹{total_hist_pnl:,.2f}", delta=f"{'↑' if total_hist_pnl >= 0 else '↓'}")

# ── Main Tabs ──────────────────────────────────────────────────────────────────
tabs = st.tabs(["🔍 Signal Scanner", "⚡ Auto Trading", "📋 Watchlist", "💼 Portfolio", "📜 History"])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — Signal Scanner
# ─────────────────────────────────────────────────────────────────────────────
with tabs[0]:
    st.markdown('<div class="section-title">📡 Live Option Signal Scanner</div>', unsafe_allow_html=True)

    col_scan, col_sym = st.columns([1, 3])
    with col_scan:
        scan_btn = st.button("🔄 Scan All Stocks", use_container_width=True)
    with col_sym:
        single_sym = st.selectbox("Quick Analyse", [""] + INDIAN_STOCKS)

    if scan_btn or (single_sym and single_sym != ""):
        symbols = [single_sym] if single_sym else selected_stocks
        results = []
        with st.spinner("Analysing signals…"):
            prog = st.progress(0)
            for i, sym in enumerate(symbols):
                rec = get_recommendation(sym)
                results.append(rec)
                prog.progress((i + 1) / len(symbols))
        prog.empty()

        # Summary metrics
        calls = [r for r in results if r["recommendation"] == "CALL"]
        puts = [r for r in results if r["recommendation"] == "PUT"]
        neutrals = [r for r in results if r["recommendation"] == "NEUTRAL"]

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f'<div class="metric-card"><div class="metric-value accent">{len(results)}</div><div class="metric-label">Scanned</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="metric-card"><div class="metric-value green">{len(calls)}</div><div class="metric-label">CALL Signals</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="metric-card"><div class="metric-value red">{len(puts)}</div><div class="metric-label">PUT Signals</div></div>', unsafe_allow_html=True)
        with c4:
            st.markdown(f'<div class="metric-card"><div class="metric-value yellow">{len(neutrals)}</div><div class="metric-label">Neutral</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        for rec in results:
            badge_cls = "badge-call" if rec["recommendation"] == "CALL" else ("badge-put" if rec["recommendation"] == "PUT" else "badge-neutral")
            color = "green" if rec["recommendation"] == "CALL" else ("red" if rec["recommendation"] == "PUT" else "yellow")

            with st.expander(f"{'🟢' if rec['recommendation']=='CALL' else '🔴' if rec['recommendation']=='PUT' else '🟡'} {rec['symbol']} | ₹{rec['price']:,.2f} | {rec['recommendation']} | Strength {rec['strength']}%"):
                c1, c2, c3, c4, c5 = st.columns(5)
                c1.metric("LTP", f"₹{rec['price']:,.2f}")
                c2.metric("Signal", rec["recommendation"])
                c3.metric("Target", f"₹{rec['target']:,.2f}")
                c4.metric("Stop Loss", f"₹{rec['stop']:,.2f}")
                c5.metric("Strength", f"{rec['strength']}%")

                ind = rec["indicators"]
                if ind:
                    st.markdown("**Technical Indicators**")
                    ic1, ic2, ic3, ic4, ic5, ic6 = st.columns(6)
                    ic1.metric("RSI", f"{ind.get('rsi',0):.1f}")
                    ic2.metric("MACD", f"{ind.get('macd',0):.3f}")
                    ic3.metric("ADX", f"{ind.get('adx',0):.1f}")
                    ic4.metric("BB%", f"{ind.get('bb_pct',0):.2f}")
                    ic5.metric("Stoch K", f"{ind.get('stoch_k',0):.1f}")
                    ic6.metric("Vol Ratio", f"{ind.get('vol_ratio',1):.1f}x")

                st.markdown("**Signal Reasoning**")
                for r in rec["reasoning"]:
                    col_icon = "🟢" if "CALL" in r else ("🔴" if "PUT" in r else "⚪")
                    st.markdown(f"{col_icon} {r}")

                fund = rec["fundamentals"]
                if fund:
                    with st.expander("📊 Fundamentals"):
                        fc1, fc2, fc3, fc4 = st.columns(4)
                        fc1.metric("P/E", f"{fund.get('pe','N/A')}")
                        fc2.metric("Beta", f"{fund.get('beta','N/A')}")
                        fc3.metric("EPS", f"{fund.get('eps','N/A')}")
                        fc4.metric("P/B", f"{fund.get('pb','N/A')}")

                # Add to watchlist / manual buy
                bc1, bc2 = st.columns(2)
                with bc1:
                    if st.button(f"➕ Add to Watchlist", key=f"wl_{rec['symbol']}"):
                        entry = {
                            "symbol": rec["symbol"],
                            "type": rec["recommendation"] if rec["recommendation"] != "NEUTRAL" else "CALL",
                            "strike": round(rec["price"] / 50) * 50,
                            "target": rec["target"],
                            "stop": rec["stop"],
                            "added": datetime.now().strftime("%H:%M:%S"),
                        }
                        st.session_state.watchlist.append(entry)
                        st.success("Added to watchlist!")
                with bc2:
                    if rec["recommendation"] != "NEUTRAL":
                        if st.button(f"🚀 Buy {rec['recommendation']}", key=f"buy_{rec['symbol']}"):
                            price = rec["price"]
                            df_tmp = fetch_price_data(rec["symbol"], "1mo", "1d")
                            sigma = estimate_iv(df_tmp)
                            strike = round(price / 50) * 50
                            premium = bs_price(price, strike, 7/365, 0.065, sigma, rec["recommendation"].lower())
                            trade = {
                                "id": f"{rec['symbol']}_{rec['recommendation']}_{int(time.time())}",
                                "symbol": rec["symbol"],
                                "type": rec["recommendation"],
                                "strike": strike,
                                "entry_price": price,
                                "premium": round(premium, 2),
                                "lots": 1,
                                "qty": 50,
                                "target": rec["target"],
                                "stop": rec["stop"],
                                "entry_time": datetime.now().strftime("%H:%M:%S"),
                                "status": "OPEN",
                                "pnl": 0.0,
                                "reasoning": rec["reasoning"],
                                "indicators": rec["indicators"],
                                "strength": rec["strength"],
                            }
                            st.session_state.portfolio.append(trade)
                            st.success(f"✅ Bought {rec['recommendation']} on {rec['symbol']}!")

    else:
        st.info("👆 Click **Scan All Stocks** or select a symbol above to begin analysis.")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — Auto Trading
# ─────────────────────────────────────────────────────────────────────────────
with tabs[1]:
    st.markdown('<div class="section-title">⚡ AI Auto Trading Engine</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="auto-trade-box">
    <h2 style='color:#00d4ff;font-family:Syne;font-weight:800;'>🤖 Autonomous Options AI</h2>
    <p style='color:#94a3b8;'>The engine scans all stocks every 60 seconds, picks the highest-confidence CALL/PUT signals,
    executes trades, manages positions, and squares off everything when time is up.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if not st.session_state.auto_trading:
        col_t1, col_t2, col_t3 = st.columns([1, 1, 1])
        with col_t2:
            auto_mins = st.number_input("⏱️ Duration (minutes)", min_value=1, max_value=480, value=15, step=5)
            auto_capital = st.number_input("💰 Capital per trade (₹)", min_value=1000, value=5000, step=1000)
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🚀 START AUTO TRADING", use_container_width=True):
                st.session_state.auto_trading = True
                st.session_state.auto_trade_end = datetime.now() + timedelta(minutes=auto_mins)
                st.session_state.auto_trade_log = []
                st.session_state.auto_pnl = 0.0
                st.session_state._auto_duration = auto_mins
                st.session_state._auto_capital = auto_capital
                st.rerun()
    else:
        end_time = st.session_state.auto_trade_end
        remaining = max(0, (end_time - datetime.now()).total_seconds())
        elapsed = st.session_state._auto_duration * 60 - remaining
        progress = elapsed / (st.session_state._auto_duration * 60)

        # Status bar
        c1, c2, c3, c4 = st.columns(4)
        mins_left = int(remaining // 60)
        secs_left = int(remaining % 60)
        c1.metric("⏱ Time Left", f"{mins_left}m {secs_left}s")
        c2.metric("Open Trades", len(st.session_state.portfolio))
        live_pnl = sum(t.get("pnl", 0) for t in st.session_state.portfolio)
        c3.metric("Live P&L", f"₹{live_pnl:,.2f}", delta="▲" if live_pnl >= 0 else "▼")
        c4.metric("Realized P&L", f"₹{sum(t.get('pnl',0) for t in st.session_state.history):,.2f}")

        st.progress(min(progress, 1.0))

        if remaining <= 0:
            # Square off
            st.warning("⏰ Time up! Squaring off all positions…")
            closed_trades, total_pnl = square_off_positions(st.session_state.auto_trade_log)
            report = generate_trade_report(
                closed_trades, total_pnl, st.session_state._auto_duration
            )
            st.session_state.auto_trading = False
            st.session_state._last_report = report
            st.session_state._last_pnl = total_pnl
            st.rerun()
        else:
            # Execute a cycle
            if len(st.session_state.portfolio) < 10:
                new_trades = auto_trade_step(
                    selected_stocks,
                    st.session_state.get("_auto_capital", 5000)
                )
                for t in new_trades:
                    # Check not already in portfolio
                    existing = [p["symbol"] + p["type"] for p in st.session_state.portfolio]
                    if t["symbol"] + t["type"] not in existing:
                        st.session_state.portfolio.append(t)
                        st.session_state.auto_trade_log.append(t)

            # Update live PnL on open positions
            for pos in st.session_state.portfolio:
                price = get_live_price(pos["symbol"]) or pos["entry_price"]
                if pos["type"] == "CALL":
                    pos["pnl"] = round((price - pos["entry_price"]) * pos["qty"], 2)
                    # auto stop / target
                    if price >= pos["target"] or price <= pos["stop"]:
                        hist_entry = {**pos, "exit_price": price,
                                      "exit_time": datetime.now().strftime("%H:%M:%S"), "status": "CLOSED"}
                        st.session_state.history.append(hist_entry)
                        st.session_state.portfolio = [p for p in st.session_state.portfolio if p["id"] != pos["id"]]
                else:
                    pos["pnl"] = round((pos["entry_price"] - price) * pos["qty"], 2)
                    if price <= pos["target"] or price >= pos["stop"]:
                        hist_entry = {**pos, "exit_price": price,
                                      "exit_time": datetime.now().strftime("%H:%M:%S"), "status": "CLOSED"}
                        st.session_state.history.append(hist_entry)
                        st.session_state.portfolio = [p for p in st.session_state.portfolio if p["id"] != pos["id"]]

            # Show open positions
            st.markdown("### 📊 Live Positions")
            if st.session_state.portfolio:
                df_pos = pd.DataFrame(st.session_state.portfolio)[
                    ["symbol","type","strike","entry_price","lots","qty","target","stop","pnl","strength"]
                ]
                st.dataframe(df_pos, use_container_width=True)
            else:
                st.info("Scanning for signals…")

            # Trade log
            st.markdown("### 📋 Auto Trade Log")
            if st.session_state.auto_trade_log:
                for t in reversed(st.session_state.auto_trade_log[-10:]):
                    badge = "🟢 CALL" if t["type"] == "CALL" else "🔴 PUT"
                    st.markdown(f"- {badge} **{t['symbol']}** | Strike ₹{t['strike']} | Strength {t['strength']}% | Entry ₹{t['entry_price']:.2f}")

            col_stop1, col_stop2 = st.columns([1, 3])
            with col_stop1:
                st.markdown('<div class="danger-btn">', unsafe_allow_html=True)
                if st.button("🛑 STOP & SQUARE OFF", use_container_width=True):
                    closed_trades, total_pnl = square_off_positions(st.session_state.auto_trade_log)
                    report = generate_trade_report(
                        closed_trades, total_pnl, st.session_state._auto_duration
                    )
                    st.session_state.auto_trading = False
                    st.session_state._last_report = report
                    st.session_state._last_pnl = total_pnl
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            time.sleep(10)
            st.rerun()

    # Report download (after session ends)
    if not st.session_state.auto_trading and "_last_report" in st.session_state:
        pnl = st.session_state._last_pnl
        color = "green" if pnl >= 0 else "red"
        st.markdown(f'<h3 class="{color}">Session ended. Net P&L: ₹{pnl:,.2f}</h3>', unsafe_allow_html=True)
        st.download_button(
            "📥 Download Trade Report (.txt)",
            data=st.session_state._last_report,
            file_name=f"options_trade_report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain",
            use_container_width=True,
        )

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — Watchlist
# ─────────────────────────────────────────────────────────────────────────────
with tabs[2]:
    st.markdown('<div class="section-title">👁️ Options Watchlist</div>', unsafe_allow_html=True)

    # Add to watchlist manually
    with st.expander("➕ Add Option to Watchlist"):
        wc1, wc2, wc3, wc4, wc5 = st.columns(5)
        w_sym = wc1.selectbox("Symbol", INDIAN_STOCKS, key="w_sym")
        w_type = wc2.selectbox("Type", ["CALL", "PUT"], key="w_type")
        w_strike = wc3.number_input("Strike (₹)", min_value=0.0, value=0.0, key="w_strike")
        w_target = wc4.number_input("Target (₹)", min_value=0.0, value=0.0, key="w_target")
        w_stop = wc5.number_input("Stop Loss (₹)", min_value=0.0, value=0.0, key="w_stop")
        if st.button("Add to Watchlist", use_container_width=True):
            st.session_state.watchlist.append({
                "symbol": w_sym, "type": w_type, "strike": w_strike,
                "target": w_target, "stop": w_stop,
                "added": datetime.now().strftime("%H:%M:%S")
            })
            st.success("Added!")

    if not st.session_state.watchlist:
        st.info("Your watchlist is empty. Add stocks from the Signal Scanner or manually above.")
    else:
        for i, w in enumerate(st.session_state.watchlist):
            price = get_live_price(w["symbol"]) or 0
            badge = "🟢" if w["type"] == "CALL" else "🔴"
            col1, col2, col3, col4, col5, col6, col7 = st.columns([2,1,1,1,1,1,1])
            col1.markdown(f"**{badge} {w['symbol']}**")
            col2.markdown(f"LTP: **₹{price:,.2f}**")
            col3.markdown(f"Strike: {w['strike']}")
            col4.markdown(f"Target: {w['target']}")
            col5.markdown(f"Stop: {w['stop']}")
            if col6.button("Buy", key=f"wbuy_{i}"):
                df_tmp = fetch_price_data(w["symbol"], "1mo", "1d")
                sigma = estimate_iv(df_tmp)
                strike = w["strike"] if w["strike"] else round(price / 50) * 50
                premium = bs_price(price, strike, 7/365, 0.065, sigma, w["type"].lower())
                trade = {
                    "id": f"{w['symbol']}_{w['type']}_{int(time.time())}",
                    "symbol": w["symbol"], "type": w["type"],
                    "strike": strike, "entry_price": price,
                    "premium": round(premium, 2), "lots": 1, "qty": 50,
                    "target": w["target"] or price * 1.02,
                    "stop": w["stop"] or price * 0.98,
                    "entry_time": datetime.now().strftime("%H:%M:%S"),
                    "status": "OPEN", "pnl": 0.0, "reasoning": [], "indicators": {}, "strength": 0,
                }
                st.session_state.portfolio.append(trade)
                st.success(f"Bought {w['type']} on {w['symbol']}!")
            if col7.button("❌", key=f"wdel_{i}"):
                st.session_state.watchlist.pop(i)
                st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 — Portfolio
# ─────────────────────────────────────────────────────────────────────────────
with tabs[3]:
    st.markdown('<div class="section-title">💼 Live Portfolio</div>', unsafe_allow_html=True)

    if not st.session_state.portfolio:
        st.info("No open positions. Buy an option from the Signal Scanner or Watchlist.")
    else:
        total_live_pnl = 0
        for pos in st.session_state.portfolio:
            price = get_live_price(pos["symbol"]) or pos["entry_price"]
            if pos["type"] == "CALL":
                pnl = (price - pos["entry_price"]) * pos["qty"]
            else:
                pnl = (pos["entry_price"] - price) * pos["qty"]
            pos["pnl"] = round(pnl, 2)
            total_live_pnl += pnl

        pnl_color = "green" if total_live_pnl >= 0 else "red"
        st.markdown(f'<h3 class="{pnl_color}">Total Live P&L: ₹{total_live_pnl:,.2f}</h3>', unsafe_allow_html=True)

        for pos in st.session_state.portfolio:
            badge = "🟢 CALL" if pos["type"] == "CALL" else "🔴 PUT"
            pnl_cls = "green" if pos["pnl"] >= 0 else "red"
            with st.expander(f"{badge} {pos['symbol']} | Strike ₹{pos['strike']} | P&L: ₹{pos['pnl']:,.2f}"):
                pc1, pc2, pc3, pc4, pc5 = st.columns(5)
                pc1.metric("Entry", f"₹{pos['entry_price']:.2f}")
                pc2.metric("LTP", f"₹{get_live_price(pos['symbol']) or pos['entry_price']:.2f}")
                pc3.metric("Target", f"₹{pos['target']:.2f}")
                pc4.metric("Stop", f"₹{pos['stop']:.2f}")
                pc5.metric("P&L", f"₹{pos['pnl']:,.2f}")

                if st.button(f"Square Off", key=f"sq_{pos['id']}"):
                    exit_price = get_live_price(pos["symbol"]) or pos["entry_price"]
                    if pos["type"] == "CALL":
                        final_pnl = (exit_price - pos["entry_price"]) * pos["qty"]
                    else:
                        final_pnl = (pos["entry_price"] - exit_price) * pos["qty"]
                    hist_entry = {**pos, "exit_price": exit_price,
                                  "exit_time": datetime.now().strftime("%H:%M:%S"),
                                  "pnl": round(final_pnl, 2), "status": "CLOSED"}
                    st.session_state.history.append(hist_entry)
                    st.session_state.portfolio = [p for p in st.session_state.portfolio if p["id"] != pos["id"]]
                    st.success(f"Squared off {pos['symbol']} {pos['type']} | P&L: ₹{final_pnl:,.2f}")
                    st.rerun()

        # PnL chart
        if len(st.session_state.history) >= 2:
            hist_df = pd.DataFrame(st.session_state.history)
            hist_df["cumulative"] = hist_df["pnl"].cumsum()
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                y=hist_df["cumulative"], mode="lines+markers",
                line=dict(color="#00d4ff", width=2),
                fill="tozeroy", fillcolor="rgba(0,212,255,0.1)"
            ))
            fig.update_layout(
                title="Cumulative P&L", paper_bgcolor="#111827",
                plot_bgcolor="#111827", font=dict(color="#e2e8f0"),
                xaxis=dict(gridcolor="#1e293b"), yaxis=dict(gridcolor="#1e293b")
            )
            st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 5 — History
# ─────────────────────────────────────────────────────────────────────────────
with tabs[4]:
    st.markdown('<div class="section-title">📜 Trade History</div>', unsafe_allow_html=True)

    if not st.session_state.history:
        st.info("No closed trades yet.")
    else:
        hist_df = pd.DataFrame(st.session_state.history)
        display_cols = [c for c in ["symbol","type","strike","entry_price","exit_price",
                                     "lots","qty","entry_time","exit_time","pnl","status"] if c in hist_df.columns]
        st.dataframe(hist_df[display_cols], use_container_width=True)

        wins = len([t for t in st.session_state.history if t.get("pnl", 0) >= 0])
        losses = len(st.session_state.history) - wins
        total_pnl = sum(t.get("pnl", 0) for t in st.session_state.history)

        hc1, hc2, hc3, hc4 = st.columns(4)
        hc1.metric("Total Trades", len(st.session_state.history))
        hc2.metric("Winners", wins)
        hc3.metric("Losers", losses)
        hc4.metric("Net P&L", f"₹{total_pnl:,.2f}")

        # Download history
        csv = hist_df.to_csv(index=False)
        st.download_button("📥 Download History CSV", data=csv,
                           file_name=f"trade_history_{datetime.now().strftime('%Y%m%d')}.csv",
                           mime="text/csv")

        if st.button("🗑️ Clear History"):
            st.session_state.history = []
            st.rerun()