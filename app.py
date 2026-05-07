import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import concurrent.futures
import json
import os
import requests
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="Equity Trader Pro v2",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
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
    --orange: #ff9500;
    --purple: #a855f7;
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
.purple { color: var(--purple); }

.signal-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 700;
    font-family: 'JetBrains Mono';
    text-transform: uppercase;
}
.badge-buy     { background: rgba(0,255,136,0.15); color: var(--green);  border: 1px solid var(--green); }
.badge-sell    { background: rgba(255,51,102,0.15); color: var(--red);   border: 1px solid var(--red); }
.badge-neutral { background: rgba(255,215,0,0.15);  color: var(--yellow); border: 1px solid var(--yellow); }

.market-mood-bullish {
    background: linear-gradient(135deg, rgba(0,255,136,0.1), rgba(0,212,255,0.05));
    border: 1px solid rgba(0,255,136,0.4);
    border-radius: 12px; padding: 12px 18px; text-align: center;
}
.market-mood-bearish {
    background: linear-gradient(135deg, rgba(255,51,102,0.1), rgba(255,107,53,0.05));
    border: 1px solid rgba(255,51,102,0.4);
    border-radius: 12px; padding: 12px 18px; text-align: center;
}
.market-mood-sideways {
    background: linear-gradient(135deg, rgba(255,215,0,0.1), rgba(255,149,0,0.05));
    border: 1px solid rgba(255,215,0,0.4);
    border-radius: 12px; padding: 12px 18px; text-align: center;
}
.vix-high {
    background: rgba(255,51,102,0.1); border: 1px solid rgba(255,51,102,0.4);
    border-radius: 8px; padding: 8px 14px; font-size: 0.85rem; color: var(--red);
}
.vix-low {
    background: rgba(0,255,136,0.1); border: 1px solid rgba(0,255,136,0.4);
    border-radius: 8px; padding: 8px 14px; font-size: 0.85rem; color: var(--green);
}
.vix-mid {
    background: rgba(255,215,0,0.1); border: 1px solid rgba(255,215,0,0.4);
    border-radius: 8px; padding: 8px 14px; font-size: 0.85rem; color: var(--yellow);
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

.scan-info {
    background: rgba(0,212,255,0.07);
    border: 1px solid rgba(0,212,255,0.3);
    border-radius: 10px;
    padding: 14px 18px;
    font-size: 0.85rem;
    color: #94a3b8;
    margin-bottom: 12px;
}

.warning-box {
    background: rgba(255,149,0,0.07);
    border: 1px solid rgba(255,149,0,0.3);
    border-radius: 10px;
    padding: 14px 18px;
    font-size: 0.85rem;
    color: #fbbf24;
    margin-bottom: 12px;
}

.cmp-badge {
    background: rgba(0,212,255,0.12);
    border: 1px solid rgba(0,212,255,0.4);
    border-radius: 8px;
    padding: 3px 10px;
    font-family: 'JetBrains Mono';
    font-size: 0.9rem;
    color: var(--accent);
    font-weight: 700;
}

.strength-bar-wrap {
    background: #1e293b;
    border-radius: 6px;
    height: 8px;
    width: 100%;
    overflow: hidden;
    margin-top: 4px;
}
.strength-bar-fill {
    height: 8px;
    border-radius: 6px;
    background: linear-gradient(90deg, #00d4ff, #00ff88);
}

.sector-chip {
    display: inline-block;
    background: rgba(168,85,247,0.15);
    border: 1px solid rgba(168,85,247,0.4);
    color: #a855f7;
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 0.72rem;
    font-weight: 700;
    font-family: 'JetBrains Mono';
    text-transform: uppercase;
}

.candle-pattern {
    display: inline-block;
    background: rgba(255,215,0,0.15);
    border: 1px solid rgba(255,215,0,0.4);
    color: #ffd700;
    border-radius: 6px;
    padding: 2px 10px;
    font-size: 0.75rem;
    font-weight: 700;
    margin: 2px;
}

.divergence-box {
    background: rgba(0,212,255,0.07);
    border-left: 3px solid var(--accent);
    border-radius: 0 8px 8px 0;
    padding: 8px 14px;
    font-size: 0.82rem;
    margin: 4px 0;
}

.trailing-stop-active {
    background: rgba(0,255,136,0.07);
    border: 1px solid rgba(0,255,136,0.3);
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 0.8rem;
    color: var(--green);
}

.kelly-info {
    background: rgba(168,85,247,0.07);
    border: 1px solid rgba(168,85,247,0.3);
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 0.82rem;
    color: #c084fc;
}
</style>
""", unsafe_allow_html=True)

# ─── Session State Init ───────────────────────────────────────────────────────
def init_state():
    defaults = {
        "portfolio":         [],
        "history":           [],
        "watchlist":         [],
        "auto_trading":      False,
        "auto_trade_end":    None,
        "auto_trade_log":    [],
        "auto_pnl":          0.0,
        "capital":           100000.0,
        "used_capital":      0.0,
        "nse_symbols":       [],
        "nse_fetched_at":    None,
        "_auto_duration":    15,
        "_auto_capital":     5000.0,
        "_auto_max_pos":     10,
        "_auto_min_str":     65,
        "last_scan_results": [],
        "trade_journal":     [],
        "win_rate_by_stock": {},
        "session_start":     None,
        "kelly_win_rate":    0.55,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ─── NSE Symbol Fetching ──────────────────────────────────────────────────────
FALLBACK_NSE_SYMBOLS = [
    "RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS","SBIN.NS",
    "BAJFINANCE.NS","WIPRO.NS","AXISBANK.NS","KOTAKBANK.NS","LT.NS","HCLTECH.NS",
    "ASIANPAINT.NS","MARUTI.NS","TITAN.NS","SUNPHARMA.NS","BHARTIARTL.NS",
    "NESTLEIND.NS","ULTRACEMCO.NS","POWERGRID.NS","NTPC.NS","ONGC.NS","BPCL.NS",
    "COALINDIA.NS","IOC.NS","GAIL.NS","ADANIENT.NS","ADANIPORTS.NS","ADANIGREEN.NS",
    "TATAMOTORS.NS","TATASTEEL.NS","TATACONSUM.NS","CIPLA.NS","DIVISLAB.NS",
    "DRREDDY.NS","APOLLOHOSP.NS","HINDALCO.NS","JSWSTEEL.NS","TECHM.NS",
    "HDFCLIFE.NS","SBILIFE.NS","BAJAJFINSV.NS","EICHERMOT.NS","HEROMOTOCO.NS",
    "BRITANNIA.NS","PIDILITIND.NS","DABUR.NS","MARICO.NS","COLPAL.NS",
    "HAVELLS.NS","VOLTAS.NS","BERGEPAINT.NS","GODREJCP.NS","GRASIM.NS",
    "INDUSINDBK.NS","BANDHANBNK.NS","FEDERALBNK.NS","IDFCFIRSTB.NS","PNB.NS",
    "BANKBARODA.NS","CANBK.NS","UNIONBANK.NS","SAIL.NS","NMDC.NS",
    "RECLTD.NS","PFC.NS","IRFC.NS","NHPC.NS","SJVN.NS",
    "ZOMATO.NS","NYKAA.NS","PAYTM.NS","POLICYBZR.NS","DELHIVERY.NS",
    "IRCTC.NS","HAPPSTMNDS.NS","PERSISTENT.NS","COFORGE.NS","MPHASIS.NS",
    "LTIM.NS","OFSS.NS","KPITTECH.NS","TATAELXSI.NS",
    "DIXON.NS","AMBER.NS","CROMPTON.NS","BLUESTARCO.NS",
    "PAGEIND.NS","RELAXO.NS","BATA.NS","TRENT.NS",
    "DMART.NS","ABFRL.NS","MANYAVAR.NS","SHOPERSTOP.NS",
    "INDIGO.NS","CONCOR.NS","BLUEDART.NS","GICRE.NS",
    "NIACL.NS","HDFCAMC.NS","NIPPONLIFE.NS",
    "ASTRAL.NS","POLYCAB.NS",
    "CUMMINSIND.NS","BHEL.NS","ABB.NS","SIEMENS.NS",
    "AMBUJACEM.NS","ACC.NS","SHREECEM.NS","RAMCOCEM.NS",
    "MUTHOOTFIN.NS","CHOLAFIN.NS","SHRIRAMFIN.NS",
    "AUROPHARMA.NS","TORNTPHARM.NS","LUPIN.NS","BIOCON.NS","IPCALAB.NS",
    "ALKEM.NS","GLENMARK.NS","ZYDUSLIFE.NS",
    "^NSEI","^NSEBANK","^BSESN","^INDIAVIX",
]

@st.cache_data(ttl=3600)
def fetch_nse_all_symbols():
    try:
        headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.nseindia.com"}
        url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            from io import StringIO
            df = pd.read_csv(StringIO(resp.text))
            symbols = [s.strip() + ".NS" for s in df["SYMBOL"].dropna().tolist()]
            symbols += ["^NSEI", "^NSEBANK", "^BSESN", "^INDIAVIX"]
            return symbols
    except Exception:
        pass
    return FALLBACK_NSE_SYMBOLS

def get_nse_symbols():
    symbols = fetch_nse_all_symbols()
    return symbols if symbols else FALLBACK_NSE_SYMBOLS

# ─── Core Data Functions ──────────────────────────────────────────────────────
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
        price = t.fast_info.last_price
        if price is None:
            return None
        price = float(price)
        return price if np.isfinite(price) and price > 0 else None
    except Exception:
        return None

def _safe_float(series_or_val, default=0.0):
    try:
        val = float(series_or_val.iloc[-1]) if isinstance(series_or_val, pd.Series) else float(series_or_val)
        return val if np.isfinite(val) else default
    except Exception:
        return default

# ─── Market Context Functions ─────────────────────────────────────────────────
@st.cache_data(ttl=300)
def get_market_mood():
    """Fetch Nifty50 trend and India VIX for market context filter."""
    try:
        nifty = yf.Ticker("^NSEI")
        nifty_data = nifty.history(period="5d", interval="1d")
        vix = yf.Ticker("^INDIAVIX")
        vix_data = vix.history(period="2d", interval="1d")

        mood = "SIDEWAYS"
        nifty_change = 0.0
        vix_level = 15.0

        if not nifty_data.empty and len(nifty_data) >= 2:
            close = nifty_data["Close"].astype(float)
            nifty_change = float(((close.iloc[-1] - close.iloc[-2]) / close.iloc[-2]) * 100)
            ema5 = close.ewm(span=5, adjust=False).mean()
            if close.iloc[-1] > ema5.iloc[-1] and nifty_change > 0.3:
                mood = "BULLISH"
            elif close.iloc[-1] < ema5.iloc[-1] and nifty_change < -0.3:
                mood = "BEARISH"
            else:
                mood = "SIDEWAYS"

        if not vix_data.empty:
            vix_level = float(vix_data["Close"].iloc[-1])

        return {"mood": mood, "nifty_change": nifty_change, "vix": vix_level}
    except Exception:
        return {"mood": "UNKNOWN", "nifty_change": 0.0, "vix": 15.0}

@st.cache_data(ttl=3600)
def get_sector_momentum():
    """Compute which sectors are performing best today."""
    sector_etfs = {
        "Banking":    "^NSEBANK",
        "IT":         "INFY.NS",
        "Pharma":     "SUNPHARMA.NS",
        "Auto":       "MARUTI.NS",
        "Energy":     "ONGC.NS",
        "FMCG":       "NESTLEIND.NS",
        "Metal":      "TATASTEEL.NS",
        "Infra":      "LT.NS",
    }
    results = {}
    for sector, sym in sector_etfs.items():
        try:
            t = yf.Ticker(sym)
            df = t.history(period="5d", interval="1d")
            if not df.empty and len(df) >= 2:
                chg = float(((df["Close"].iloc[-1] - df["Close"].iloc[-2]) / df["Close"].iloc[-2]) * 100)
                results[sector] = chg
        except Exception:
            results[sector] = 0.0
    return dict(sorted(results.items(), key=lambda x: x[1], reverse=True))

def get_top_sectors(n=3):
    """Return top N performing sectors."""
    sm = get_sector_momentum()
    return list(sm.keys())[:n]

# ─── Momentum Ranking ─────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def compute_momentum_rank(symbols, top_pct=0.25):
    """Return set of symbols in top X% by 1-month momentum."""
    momentum = {}
    def _get_mom(sym):
        try:
            df = yf.Ticker(sym).history(period="1mo", interval="1d")
            if not df.empty and len(df) >= 2:
                chg = float(((df["Close"].iloc[-1] - df["Close"].iloc[0]) / df["Close"].iloc[0]) * 100)
                return sym, chg
        except Exception:
            pass
        return sym, 0.0

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:
        for sym, chg in ex.map(_get_mom, symbols[:200]):
            momentum[sym] = chg

    sorted_syms = sorted(momentum, key=lambda x: momentum[x], reverse=True)
    cutoff = max(1, int(len(sorted_syms) * top_pct))
    return set(sorted_syms[:cutoff])

# ─── Candlestick Pattern Detection ───────────────────────────────────────────
def detect_candlestick_patterns(df):
    """Detect key reversal/continuation patterns. Returns list of (pattern, signal) tuples."""
    if df is None or len(df) < 3:
        return []
    patterns = []
    o = df["Open"].astype(float)
    h = df["High"].astype(float)
    l = df["Low"].astype(float)
    c = df["Close"].astype(float)

    try:
        # Last 3 candles
        o1, o2, o3 = o.iloc[-3], o.iloc[-2], o.iloc[-1]
        h1, h2, h3 = h.iloc[-3], h.iloc[-2], h.iloc[-1]
        l1, l2, l3 = l.iloc[-3], l.iloc[-2], l.iloc[-1]
        c1, c2, c3 = c.iloc[-3], c.iloc[-2], c.iloc[-1]

        body2 = abs(c2 - o2)
        body3 = abs(c3 - o3)
        range2 = h2 - l2 if (h2 - l2) > 0 else 0.001
        range3 = h3 - l3 if (h3 - l3) > 0 else 0.001

        # Doji (last candle)
        if body3 / range3 < 0.1:
            patterns.append(("Doji", "NEUTRAL", "Indecision — possible reversal"))

        # Hammer (bullish reversal)
        lower_wick3 = min(o3, c3) - l3
        upper_wick3 = h3 - max(o3, c3)
        if lower_wick3 > 2 * body3 and upper_wick3 < body3 and c2 < o2:
            patterns.append(("Hammer", "BUY", "Bullish reversal pattern"))

        # Shooting Star (bearish)
        if upper_wick3 > 2 * body3 and lower_wick3 < body3 and c2 > o2:
            patterns.append(("Shooting Star", "SELL", "Bearish reversal at top"))

        # Bullish Engulfing
        if c2 < o2 and c3 > o3 and o3 < c2 and c3 > o2:
            patterns.append(("Bullish Engulfing", "BUY", "Strong bullish reversal"))

        # Bearish Engulfing
        if c2 > o2 and c3 < o3 and o3 > c2 and c3 < o2:
            patterns.append(("Bearish Engulfing", "SELL", "Strong bearish reversal"))

        # Morning Star (bullish 3-candle)
        if c1 < o1 and body2 < (h2 - l2) * 0.3 and c3 > o3 and c3 > (o1 + c1) / 2:
            patterns.append(("Morning Star", "BUY", "Powerful 3-candle bullish reversal"))

        # Evening Star (bearish 3-candle)
        if c1 > o1 and body2 < (h2 - l2) * 0.3 and c3 < o3 and c3 < (o1 + c1) / 2:
            patterns.append(("Evening Star", "SELL", "Powerful 3-candle bearish reversal"))

    except Exception:
        pass
    return patterns

# ─── RSI Divergence Detection ─────────────────────────────────────────────────
def detect_rsi_divergence(df, rsi_series):
    """Detect bullish/bearish RSI divergence over last 20 bars."""
    if df is None or len(df) < 15 or rsi_series is None or len(rsi_series) < 15:
        return None
    try:
        close  = df["Close"].astype(float).values[-20:]
        rsi    = rsi_series.values[-20:]

        # Find last 2 price troughs (lows)
        low_idx  = [i for i in range(1, len(close) - 1) if close[i] < close[i-1] and close[i] < close[i+1]]
        high_idx = [i for i in range(1, len(close) - 1) if close[i] > close[i-1] and close[i] > close[i+1]]

        if len(low_idx) >= 2:
            i1, i2 = low_idx[-2], low_idx[-1]
            # Bullish divergence: price lower low but RSI higher low
            if close[i2] < close[i1] and rsi[i2] > rsi[i1] and (rsi[i1] < 50):
                return ("BULLISH_DIVERGENCE", "BUY", f"RSI bullish divergence — price LL, RSI HL")

        if len(high_idx) >= 2:
            i1, i2 = high_idx[-2], high_idx[-1]
            # Bearish divergence: price higher high but RSI lower high
            if close[i2] > close[i1] and rsi[i2] < rsi[i1] and (rsi[i1] > 50):
                return ("BEARISH_DIVERGENCE", "SELL", f"RSI bearish divergence — price HH, RSI LH")
    except Exception:
        pass
    return None

# ─── Support & Resistance ─────────────────────────────────────────────────────
def compute_support_resistance(df, lookback=60):
    """Find key support and resistance levels from recent highs/lows."""
    if df is None or len(df) < 20:
        return None, None
    try:
        recent = df.tail(lookback)
        highs  = recent["High"].astype(float)
        lows   = recent["Low"].astype(float)

        # Pivot highs and lows
        pivot_highs = []
        pivot_lows  = []
        for i in range(2, len(highs) - 2):
            if highs.iloc[i] == highs.iloc[i-2:i+3].max():
                pivot_highs.append(float(highs.iloc[i]))
            if lows.iloc[i] == lows.iloc[i-2:i+3].min():
                pivot_lows.append(float(lows.iloc[i]))

        resistance = float(np.mean(pivot_highs[-3:])) if pivot_highs else float(highs.max())
        support    = float(np.mean(pivot_lows[-3:]))  if pivot_lows  else float(lows.min())
        return support, resistance
    except Exception:
        return None, None

# ─── Fibonacci Retracement ────────────────────────────────────────────────────
def compute_fibonacci(df, lookback=60):
    """Compute 38.2%, 50%, 61.8% fib levels from swing high/low."""
    if df is None or len(df) < 20:
        return {}
    try:
        recent   = df.tail(lookback)
        swing_h  = float(recent["High"].max())
        swing_l  = float(recent["Low"].min())
        diff     = swing_h - swing_l
        return {
            "fib_382": swing_h - 0.382 * diff,
            "fib_500": swing_h - 0.500 * diff,
            "fib_618": swing_h - 0.618 * diff,
            "swing_h": swing_h,
            "swing_l": swing_l,
        }
    except Exception:
        return {}

# ─── Volume Profile (simplified) ──────────────────────────────────────────────
def compute_volume_profile(df):
    """Find HVN (high volume node) price range."""
    if df is None or len(df) < 20:
        return None, None
    try:
        close  = df["Close"].astype(float)
        volume = df["Volume"].astype(float)
        bins   = pd.cut(close, bins=10)
        vol_by_price = volume.groupby(bins).sum()
        hvn_bin = vol_by_price.idxmax()
        hvn_mid = (hvn_bin.left + hvn_bin.right) / 2
        return float(hvn_bin.left), float(hvn_bin.right)
    except Exception:
        return None, None

# ─── Market Mode Detection ────────────────────────────────────────────────────
def detect_market_mode(indicators):
    """Detect if stock is trending or ranging."""
    adx    = indicators.get("adx", 20)
    bb_pct = indicators.get("bb_pct", 0.5)
    try:
        adx    = float(adx)
        bb_pct = float(bb_pct)
    except (TypeError, ValueError):
        return "RANGING"
    if adx > 25:
        return "TRENDING"
    elif adx < 20:
        return "RANGING"
    return "NEUTRAL_MODE"

# ─── Brokerage & Cost Simulation ─────────────────────────────────────────────
def compute_trade_cost(price, qty, trade_type="BUY"):
    """Simulate realistic Zerodha brokerage + STT + charges."""
    turnover   = price * qty
    brokerage  = min(20.0, turnover * 0.0003)      # ₹20 or 0.03%
    stt        = turnover * 0.001 if trade_type == "BUY" else turnover * 0.001
    exchange   = turnover * 0.0000345
    sebi       = turnover * 0.000001
    gst        = (brokerage + exchange + sebi) * 0.18
    stamp_duty = turnover * 0.00015 if trade_type == "BUY" else 0
    total_cost = brokerage + stt + exchange + sebi + gst + stamp_duty
    return round(total_cost, 2)

# ─── Kelly Criterion Position Sizing ─────────────────────────────────────────
def kelly_position_size(base_capital, win_rate, reward_risk, signal_strength):
    """
    Kelly fraction adjusted for signal strength.
    f = win_rate - (1 - win_rate) / reward_risk
    Capped at 25% of capital and scaled by signal strength.
    """
    try:
        if reward_risk <= 0:
            return base_capital
        f = win_rate - (1 - win_rate) / reward_risk
        f = max(0.05, min(0.25, f))   # cap between 5% and 25%
        strength_mult = 0.5 + (signal_strength / 100) * 0.5  # 0.5x to 1.0x
        kelly_capital = base_capital * f * strength_mult
        return round(max(1000.0, kelly_capital), 2)
    except Exception:
        return base_capital

# ─── Compute Indicators (enhanced) ───────────────────────────────────────────
def compute_indicators(df):
    if df is None or len(df) < 20:
        return {}
    try:
        close  = df['Close'].astype(float)
        high   = df['High'].astype(float)
        low    = df['Low'].astype(float)
        volume = df['Volume'].astype(float)

        # RSI
        delta = close.diff()
        gain  = delta.clip(lower=0).ewm(span=14, adjust=False).mean()
        loss  = (-delta.clip(upper=0)).ewm(span=14, adjust=False).mean()
        rs    = gain / loss.replace(0, np.nan)
        rsi   = 100 - (100 / (1 + rs))

        # MACD
        ema12  = close.ewm(span=12, adjust=False).mean()
        ema26  = close.ewm(span=26, adjust=False).mean()
        macd   = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False).mean()
        hist   = macd - signal

        # Bollinger Bands
        sma20    = close.rolling(20).mean()
        std20    = close.rolling(20).std()
        bb_upper = sma20 + 2 * std20
        bb_lower = sma20 - 2 * std20
        bb_range = (bb_upper - bb_lower).replace(0, np.nan)
        bb_pct   = (close - bb_lower) / bb_range

        # ATR
        tr = pd.concat([
            high - low,
            (high - close.shift()).abs(),
            (low  - close.shift()).abs(),
        ], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()

        # EMAs
        ema9   = close.ewm(span=9,   adjust=False).mean()
        ema21  = close.ewm(span=21,  adjust=False).mean()
        ema50  = close.ewm(span=50,  adjust=False).mean()
        ema200 = close.ewm(span=200, adjust=False).mean()

        # Stochastic
        low14       = low.rolling(14).min()
        high14      = high.rolling(14).max()
        stoch_range = (high14 - low14).replace(0, np.nan)
        stoch_k     = 100 * (close - low14) / stoch_range
        stoch_d     = stoch_k.rolling(3).mean()

        # Volume ratio
        vol_ma    = volume.rolling(20).mean().replace(0, np.nan)
        vol_ratio = volume / vol_ma

        # Williams %R
        wr_range   = (high14 - low14).replace(0, np.nan)
        williams_r = -100 * (high14 - close) / wr_range

        # CCI
        tp     = (high + low + close) / 3
        tp_std = tp.rolling(20).std().replace(0, np.nan)
        cci    = (tp - tp.rolling(20).mean()) / (0.015 * tp_std)

        # ADX / DI
        plus_dm  = high.diff().clip(lower=0)
        minus_dm = (-low.diff()).clip(lower=0)
        atr_safe = atr.replace(0, np.nan)
        plus_di  = 100 * (plus_dm.ewm(span=14, adjust=False).mean()  / atr_safe)
        minus_di = 100 * (minus_dm.ewm(span=14, adjust=False).mean() / atr_safe)
        di_sum   = (plus_di + minus_di).replace(0, np.nan)
        dx       = 100 * (plus_di - minus_di).abs() / di_sum
        adx      = dx.ewm(span=14, adjust=False).mean()

        # Momentum: 1-month return
        momentum_1m = float(((close.iloc[-1] - close.iloc[-21]) / close.iloc[-21]) * 100) if len(close) >= 21 else 0.0
        momentum_3m = float(((close.iloc[-1] - close.iloc[-63]) / close.iloc[-63]) * 100) if len(close) >= 63 else 0.0

        # Previous close for day change %
        prev_close      = close.shift(1)
        day_change_pct  = ((close - prev_close) / prev_close.replace(0, np.nan)) * 100

        return {
            "rsi":            _safe_float(rsi),
            "rsi_series":     rsi,           # keep series for divergence
            "macd":           _safe_float(macd),
            "macd_signal":    _safe_float(signal),
            "macd_hist":      _safe_float(hist),
            "bb_pct":         _safe_float(bb_pct),
            "bb_upper":       _safe_float(bb_upper),
            "bb_lower":       _safe_float(bb_lower),
            "bb_mid":         _safe_float(sma20),
            "atr":            _safe_float(atr),
            "ema9":           _safe_float(ema9),
            "ema21":          _safe_float(ema21),
            "ema50":          _safe_float(ema50),
            "ema200":         _safe_float(ema200),
            "stoch_k":        _safe_float(stoch_k),
            "stoch_d":        _safe_float(stoch_d),
            "vol_ratio":      _safe_float(vol_ratio),
            "williams_r":     _safe_float(williams_r),
            "cci":            _safe_float(cci),
            "adx":            _safe_float(adx),
            "plus_di":        _safe_float(plus_di),
            "minus_di":       _safe_float(minus_di),
            "close":          _safe_float(close),
            "sma20":          _safe_float(sma20),
            "day_change_pct": _safe_float(day_change_pct),
            "prev_close":     _safe_float(prev_close),
            "volume":         _safe_float(volume),
            "momentum_1m":    momentum_1m,
            "momentum_3m":    momentum_3m,
        }
    except Exception:
        return {}

# ─── Multi-Timeframe Confirmation ─────────────────────────────────────────────
def get_multi_tf_bias(symbol):
    """
    Returns (bias, confirmation_count) where bias is 'BUY'/'SELL'/'MIXED'.
    Checks 15min, 1hr, daily.
    """
    tf_signals = []
    for period, interval in [("5d","15m"), ("1mo","1h"), ("3mo","1d")]:
        df = fetch_price_data(symbol, period=period, interval=interval)
        if df is None or len(df) < 15:
            continue
        ind = compute_indicators(df)
        if not ind:
            continue
        rsi   = ind.get("rsi", 50)
        macd  = ind.get("macd", 0)
        msig  = ind.get("macd_signal", 0)
        close = ind.get("close", 0)
        ema21 = ind.get("ema21", 0)
        buy_pts  = (1 if rsi < 50 else 0) + (1 if macd > msig else 0) + (1 if close > ema21 else 0)
        sell_pts = (1 if rsi > 50 else 0) + (1 if macd < msig else 0) + (1 if close < ema21 else 0)
        if buy_pts > sell_pts:
            tf_signals.append("BUY")
        elif sell_pts > buy_pts:
            tf_signals.append("SELL")

    if not tf_signals:
        return "MIXED", 0
    buy_count  = tf_signals.count("BUY")
    sell_count = tf_signals.count("SELL")
    if buy_count == len(tf_signals):
        return "BUY", buy_count
    if sell_count == len(tf_signals):
        return "SELL", sell_count
    return "MIXED", max(buy_count, sell_count)

def get_fundamentals(symbol):
    try:
        t    = yf.Ticker(symbol)
        info = t.info
        return {
            "pe":          info.get("trailingPE",       None),
            "pb":          info.get("priceToBook",      None),
            "roe":         info.get("returnOnEquity",   None),
            "debt_equity": info.get("debtToEquity",     None),
            "eps":         info.get("trailingEps",      None),
            "beta":        info.get("beta",             None),
            "market_cap":  info.get("marketCap",        None),
            "52w_high":    info.get("fiftyTwoWeekHigh", None),
            "52w_low":     info.get("fiftyTwoWeekLow",  None),
            "avg_vol":     info.get("averageVolume",    None),
            "sector":      info.get("sector",           "N/A"),
            "industry":    info.get("industry",         "N/A"),
            "dividend":    info.get("dividendYield",    None),
            "name":        info.get("longName",         symbol),
            "earnings_date": info.get("earningsTimestamp", None),
        }
    except Exception:
        return {}

def should_skip_earnings(fundamentals):
    """Return True if earnings within 7 days — skip to avoid gap risk."""
    try:
        ts = fundamentals.get("earnings_date", None)
        if ts is None:
            return False
        earnings_dt = datetime.fromtimestamp(int(ts))
        days_to_earnings = (earnings_dt - datetime.now()).days
        return 0 <= days_to_earnings <= 7
    except Exception:
        return False

# ─── Enhanced Signal Scorer ───────────────────────────────────────────────────
def score_signal(indicators, fundamentals, df=None, market_mood=None,
                 top_sectors=None, use_multi_tf=False, symbol=None,
                 market_mode=None):
    """
    Enhanced signal scoring with:
    - Market context filter (Nifty mood, VIX)
    - Candlestick patterns
    - RSI divergence
    - Support/Resistance distance
    - Fibonacci levels
    - Market mode (trending vs ranging)
    - Sector filter
    - Earnings avoidance
    - Momentum ranking bonus
    """
    buy_score  = 0
    sell_score = 0
    reasoning  = []

    if not indicators:
        return 0, 0, ["Insufficient data"], 0

    def g(key, default=0):
        v = indicators.get(key, default)
        try:
            v = float(v)
            return v if np.isfinite(v) else default
        except (TypeError, ValueError):
            return default

    rsi        = g("rsi",        50)
    macd       = g("macd",        0)
    macd_sig   = g("macd_signal", 0)
    macd_hist  = g("macd_hist",   0)
    bb_pct     = g("bb_pct",      0.5)
    stoch_k    = g("stoch_k",    50)
    stoch_d    = g("stoch_d",    50)
    vol_ratio  = g("vol_ratio",   1)
    williams_r = g("williams_r", -50)
    cci        = g("cci",         0)
    adx        = g("adx",        20)
    plus_di    = g("plus_di",    25)
    minus_di   = g("minus_di",   25)
    close      = g("close",       0)
    ema9       = g("ema9",        0)
    ema21      = g("ema21",       0)
    ema50      = g("ema50",       0)
    ema200     = g("ema200",      0)
    mom_1m     = g("momentum_1m", 0)

    # ── Market Context Filter ─────────────────────────────────────────────────
    if market_mood:
        mood = market_mood.get("mood", "UNKNOWN")
        vix  = market_mood.get("vix", 15)
        if vix > 20:
            sell_score += 1
            reasoning.append(f"⚠️ India VIX={vix:.1f} HIGH (>20) — elevated risk → SELL bias +1")
        elif vix < 13:
            buy_score += 1
            reasoning.append(f"🟢 India VIX={vix:.1f} LOW (<13) — calm market → BUY bias +1")

        if mood == "BEARISH":
            sell_score += 2
            reasoning.append("🔴 Nifty BEARISH — market falling, avoid BUY signals → SELL +2")
        elif mood == "BULLISH":
            buy_score += 1
            reasoning.append("🟢 Nifty BULLISH — market rising, favour BUY signals → BUY +1")

    # ── Sector Filter ─────────────────────────────────────────────────────────
    if top_sectors and fundamentals:
        stock_sector = fundamentals.get("sector", "N/A")
        if any(s.lower() in stock_sector.lower() for s in top_sectors):
            buy_score += 1
            reasoning.append(f"🟢 Sector '{stock_sector}' in TODAY's top performing sectors → BUY +1")

    # ── Earnings Avoidance ────────────────────────────────────────────────────
    if fundamentals and should_skip_earnings(fundamentals):
        reasoning.append("⚠️ Earnings within 7 days — signal reliability reduced")
        sell_score += 1   # add a caution point

    # ── Market Mode (Trend vs Range) ─────────────────────────────────────────
    detected_mode = market_mode or detect_market_mode(indicators)
    reasoning.append(f"📊 Market Mode: {detected_mode}")

    # ── RSI ───────────────────────────────────────────────────────────────────
    if rsi < 30:
        buy_score  += 3; reasoning.append(f"RSI={rsi:.1f} — Oversold → BUY +3")
    elif rsi < 40:
        buy_score  += 1; reasoning.append(f"RSI={rsi:.1f} — Mildly oversold → BUY +1")
    elif rsi > 70:
        sell_score += 3; reasoning.append(f"RSI={rsi:.1f} — Overbought → SELL +3")
    elif rsi > 60:
        sell_score += 1; reasoning.append(f"RSI={rsi:.1f} — Mildly overbought → SELL +1")
    else:
        reasoning.append(f"RSI={rsi:.1f} — Neutral")

    # ── RSI Divergence ────────────────────────────────────────────────────────
    if df is not None:
        rsi_series = indicators.get("rsi_series", None)
        div = detect_rsi_divergence(df, rsi_series)
        if div:
            dtype, dsignal, dmsg = div
            if dsignal == "BUY":
                buy_score  += 3; reasoning.append(f"📐 {dmsg} → BUY +3")
            else:
                sell_score += 3; reasoning.append(f"📐 {dmsg} → SELL +3")

    # ── Candlestick Patterns ──────────────────────────────────────────────────
    if df is not None:
        patterns = detect_candlestick_patterns(df)
        for pname, psignal, pdesc in patterns:
            if psignal == "BUY":
                buy_score  += 2; reasoning.append(f"🕯️ {pname}: {pdesc} → BUY +2")
            elif psignal == "SELL":
                sell_score += 2; reasoning.append(f"🕯️ {pname}: {pdesc} → SELL +2")
            else:
                reasoning.append(f"🕯️ {pname}: {pdesc} (Neutral)")

    # ── MACD ─────────────────────────────────────────────────────────────────
    if macd > macd_sig and macd_hist > 0:
        buy_score  += 2; reasoning.append("MACD bullish crossover → BUY +2")
    elif macd < macd_sig and macd_hist < 0:
        sell_score += 2; reasoning.append("MACD bearish crossover → SELL +2")

    # ── Bollinger Bands ───────────────────────────────────────────────────────
    if bb_pct < 0.1:
        buy_score  += 2; reasoning.append(f"Price at lower BB ({bb_pct:.2f}) → BUY +2")
    elif bb_pct > 0.9:
        sell_score += 2; reasoning.append(f"Price at upper BB ({bb_pct:.2f}) → SELL +2")

    # ── Stochastic ────────────────────────────────────────────────────────────
    if stoch_k < 20 and stoch_k > stoch_d:
        buy_score  += 2; reasoning.append(f"Stoch K={stoch_k:.1f} oversold + crossing up → BUY +2")
    elif stoch_k > 80 and stoch_k < stoch_d:
        sell_score += 2; reasoning.append(f"Stoch K={stoch_k:.1f} overbought + crossing down → SELL +2")

    # ── EMA Stack ─────────────────────────────────────────────────────────────
    if close > 0 and ema9 > 0 and ema21 > 0 and ema50 > 0:
        if close > ema9 > ema21 > ema50:
            buy_score  += 3; reasoning.append("Strong bullish EMA stack (price > 9>21>50) → BUY +3")
        elif close < ema9 < ema21 < ema50:
            sell_score += 3; reasoning.append("Strong bearish EMA stack (price < 9<21<50) → SELL +3")
        elif ema200 > 0 and close > ema50 > ema200:
            buy_score  += 1; reasoning.append("Above EMA50 & EMA200 (long-term uptrend) → BUY +1")
        elif ema200 > 0 and close < ema50 < ema200:
            sell_score += 1; reasoning.append("Below EMA50 & EMA200 (long-term downtrend) → SELL +1")

    # ── ADX ───────────────────────────────────────────────────────────────────
    if adx > 25:
        if plus_di > minus_di:
            buy_score  += 2; reasoning.append(f"ADX={adx:.1f} strong uptrend → BUY +2")
        else:
            sell_score += 2; reasoning.append(f"ADX={adx:.1f} strong downtrend → SELL +2")

    # ── Williams %R ───────────────────────────────────────────────────────────
    if williams_r < -80:
        buy_score  += 1; reasoning.append(f"Williams R={williams_r:.1f} oversold → BUY +1")
    elif williams_r > -20:
        sell_score += 1; reasoning.append(f"Williams R={williams_r:.1f} overbought → SELL +1")

    # ── CCI ───────────────────────────────────────────────────────────────────
    if cci < -100:
        buy_score  += 1; reasoning.append(f"CCI={cci:.1f} oversold → BUY +1")
    elif cci > 100:
        sell_score += 1; reasoning.append(f"CCI={cci:.1f} overbought → SELL +1")

    # ── Volume Confirmation ───────────────────────────────────────────────────
    if vol_ratio > 1.5:
        if buy_score > sell_score:
            buy_score  += 1; reasoning.append(f"High volume ({vol_ratio:.1f}x avg) confirms bullish → BUY +1")
        elif sell_score > buy_score:
            sell_score += 1; reasoning.append(f"High volume ({vol_ratio:.1f}x avg) confirms bearish → SELL +1")

    # ── Momentum Bonus ────────────────────────────────────────────────────────
    if mom_1m > 10:
        buy_score  += 1; reasoning.append(f"Strong 1-month momentum (+{mom_1m:.1f}%) → BUY +1")
    elif mom_1m < -10:
        sell_score += 1; reasoning.append(f"Weak 1-month momentum ({mom_1m:.1f}%) → SELL +1")

    # ── Support & Resistance ──────────────────────────────────────────────────
    if df is not None and close > 0:
        support, resistance = compute_support_resistance(df)
        if support and resistance:
            sr_range = resistance - support
            if sr_range > 0:
                dist_from_support = (close - support) / sr_range
                if dist_from_support < 0.1:
                    buy_score  += 2; reasoning.append(f"🟢 Price near KEY SUPPORT (₹{support:.2f}) → BUY +2")
                elif dist_from_support > 0.9:
                    sell_score += 2; reasoning.append(f"🔴 Price near KEY RESISTANCE (₹{resistance:.2f}) → SELL +2")

    # ── Fibonacci Retracement ─────────────────────────────────────────────────
    if df is not None and close > 0:
        fibs = compute_fibonacci(df)
        for level_name, level_val in [("38.2%", fibs.get("fib_382")),
                                       ("50%",   fibs.get("fib_500")),
                                       ("61.8%", fibs.get("fib_618"))]:
            if level_val and abs(close - level_val) / close < 0.01:
                buy_score  += 2
                reasoning.append(f"📐 Price at Fibonacci {level_name} retracement (₹{level_val:.2f}) → BUY +2")
                break

    # ── Fundamentals: P/E ─────────────────────────────────────────────────────
    pe = fundamentals.get("pe", None)
    if pe is not None:
        try:
            pe = float(pe)
            if np.isfinite(pe) and pe > 0:
                if pe < 15:
                    buy_score  += 1; reasoning.append(f"Low P/E ({pe:.1f}) — cheap → BUY +1")
                elif pe > 50:
                    sell_score += 1; reasoning.append(f"High P/E ({pe:.1f}) — overvalued → SELL +1")
        except (TypeError, ValueError):
            pass

    # ── 52-week proximity ─────────────────────────────────────────────────────
    fw_high = fundamentals.get("52w_high", None)
    fw_low  = fundamentals.get("52w_low",  None)
    if fw_high and fw_low and close > 0:
        try:
            fw_high = float(fw_high)
            fw_low  = float(fw_low)
            fw_range = fw_high - fw_low
            if fw_range > 0:
                fw_pct = (close - fw_low) / fw_range
                if fw_pct < 0.15:
                    buy_score  += 2; reasoning.append(f"Near 52-week LOW ({fw_pct*100:.0f}% from low) → BUY +2")
                elif fw_pct > 0.85:
                    sell_score += 1; reasoning.append(f"Near 52-week HIGH ({fw_pct*100:.0f}% from low) → SELL +1")
        except (TypeError, ValueError):
            pass

    # ── Composite Strength ────────────────────────────────────────────────────
    total = max(buy_score + sell_score + 1, 1)
    if buy_score > sell_score:
        composite = min(100, int((buy_score / total) * 100))
    elif sell_score > buy_score:
        composite = min(100, int((sell_score / total) * 100))
    else:
        composite = 50

    return buy_score, sell_score, reasoning, composite


def get_recommendation(symbol, market_mood=None, top_sectors=None, use_multi_tf=False):
    df           = fetch_price_data(symbol, period="3mo", interval="1d")
    indicators   = compute_indicators(df)
    fundamentals = get_fundamentals(symbol)
    market_mode  = detect_market_mode(indicators) if indicators else "RANGING"

    buy_score, sell_score, reasoning, composite = score_signal(
        indicators, fundamentals, df=df,
        market_mood=market_mood, top_sectors=top_sectors,
        use_multi_tf=use_multi_tf, symbol=symbol,
        market_mode=market_mode,
    )

    # Candlestick patterns (for display)
    patterns = detect_candlestick_patterns(df) if df is not None else []

    # RSI divergence
    rsi_series = indicators.get("rsi_series", None)
    divergence = detect_rsi_divergence(df, rsi_series) if df is not None else None

    # Support/Resistance
    support, resistance = compute_support_resistance(df) if df is not None else (None, None)

    # Fibonacci
    fibs = compute_fibonacci(df) if df is not None else {}

    price = indicators.get("close", 0) or 0
    if not price or not np.isfinite(float(price)) or float(price) <= 0:
        price = get_live_price(symbol) or 0
    price = float(price)

    atr = float(indicators.get("atr", 0) or 0)
    if not np.isfinite(atr) or atr <= 0:
        atr = price * 0.02

    if buy_score > sell_score and buy_score >= 5:
        rec      = "BUY"
        strength = composite
        target   = round(price * (1 + 0.02 * (buy_score / 5)), 2) if price > 0 else 0
        stop     = round(price - 1.5 * atr, 2)                     if price > 0 else 0
    elif sell_score > buy_score and sell_score >= 5:
        rec      = "SELL"
        strength = composite
        target   = round(price * (1 - 0.02 * (sell_score / 5)), 2) if price > 0 else 0
        stop     = round(price + 1.5 * atr, 2)                     if price > 0 else 0
    else:
        rec      = "NEUTRAL"
        strength = composite
        target   = price
        stop     = price

    day_change = indicators.get("day_change_pct", 0) or 0
    vol_ratio  = indicators.get("vol_ratio", 1) or 1
    mom_1m     = indicators.get("momentum_1m", 0) or 0
    mom_3m     = indicators.get("momentum_3m", 0) or 0

    # Reward/risk ratio for Kelly
    rr_ratio = abs(target - price) / abs(price - stop) if (price > 0 and abs(price - stop) > 0) else 1.5

    return {
        "symbol":         symbol,
        "cmp":            price,
        "price":          price,
        "recommendation": rec,
        "strength":       strength,
        "target":         target,
        "stop":           stop,
        "buy_score":      buy_score,
        "sell_score":     sell_score,
        "day_change":     float(day_change),
        "vol_ratio":      float(vol_ratio),
        "momentum_1m":    float(mom_1m),
        "momentum_3m":    float(mom_3m),
        "indicators":     {k: v for k, v in indicators.items() if k != "rsi_series"},
        "fundamentals":   fundamentals,
        "reasoning":      reasoning,
        "name":           fundamentals.get("name", symbol),
        "sector":         fundamentals.get("sector", "N/A"),
        "patterns":       patterns,
        "divergence":     divergence,
        "support":        support,
        "resistance":     resistance,
        "fibs":           fibs,
        "market_mode":    market_mode,
        "rr_ratio":       rr_ratio,
        "atr":            atr,
    }


# ─── Parallel Scan ────────────────────────────────────────────────────────────
def _scan_single(args):
    symbol, market_mood, top_sectors = args
    try:
        return get_recommendation(symbol, market_mood=market_mood, top_sectors=top_sectors)
    except Exception:
        return None

def scan_symbols_parallel(symbols, max_workers=30, market_mood=None, top_sectors=None):
    results = []
    args_list = [(sym, market_mood, top_sectors) for sym in symbols]
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {executor.submit(_scan_single, args): args[0] for args in args_list}
        for future in concurrent.futures.as_completed(future_map):
            try:
                res = future.result()
                if res and res.get("price") and res["price"] > 0:
                    results.append(res)
            except Exception:
                continue

    def sort_key(x):
        is_neutral = 1 if x["recommendation"] == "NEUTRAL" else 0
        strength   = -x.get("strength", 0)
        return (is_neutral, strength)

    results.sort(key=sort_key)
    return results


# ─── Trade Builder with Kelly + Cost ─────────────────────────────────────────
def build_trade_from_rec(rec, base_capital, win_rate=0.55, use_kelly=True):
    if rec.get("recommendation") == "NEUTRAL":
        return None
    if rec.get("strength", 0) < 60:
        return None

    price = rec.get("price") or 0
    try:
        price = float(price)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(price) or price <= 0:
        return None

    trade_type = rec["recommendation"]
    rr_ratio   = rec.get("rr_ratio", 1.5)
    strength   = rec.get("strength", 65)

    # Kelly position sizing
    if use_kelly:
        capital_for_trade = kelly_position_size(base_capital, win_rate, rr_ratio, strength)
    else:
        try:
            capital_for_trade = float(base_capital)
        except (TypeError, ValueError):
            capital_for_trade = 5000.0

    qty  = max(1, int(capital_for_trade / price))
    cost = compute_trade_cost(price, qty, trade_type)

    return {
        "id":            f"{rec['symbol']}_{trade_type}_{int(time.time() * 1000)}",
        "symbol":        rec["symbol"],
        "name":          rec.get("name", rec["symbol"]),
        "type":          trade_type,
        "cmp":           price,
        "entry_price":   price,
        "qty":           qty,
        "invested":      round(qty * price, 2),
        "brokerage":     cost,
        "target":        rec.get("target") or price,
        "stop":          rec.get("stop")   or price,
        "trailing_stop": None,   # activated when profit >= 1%
        "entry_time":    datetime.now().strftime("%H:%M:%S"),
        "entry_dt":      datetime.now(),
        "status":        "OPEN",
        "pnl":           0.0,
        "reasoning":     rec.get("reasoning", []),
        "indicators":    rec.get("indicators", {}),
        "strength":      strength,
        "buy_score":     rec.get("buy_score", 0),
        "sell_score":    rec.get("sell_score", 0),
        "sector":        rec.get("sector", "N/A"),
        "day_change":    rec.get("day_change", 0),
        "patterns":      [p[0] for p in rec.get("patterns", [])],
        "market_mode":   rec.get("market_mode", "N/A"),
        "momentum_1m":   rec.get("momentum_1m", 0),
        "setup_type":    _detect_setup_type(rec),
    }

def _detect_setup_type(rec):
    """Tag the trade setup type for journal analytics."""
    patterns = [p[0] for p in rec.get("patterns", [])]
    div = rec.get("divergence")
    indicators = rec.get("indicators", {})
    adx = indicators.get("adx", 20)

    if div:
        return "divergence"
    if any(p in patterns for p in ["Bullish Engulfing", "Morning Star", "Hammer"]):
        return "reversal"
    if any(p in patterns for p in ["Bearish Engulfing", "Evening Star", "Shooting Star"]):
        return "reversal"
    if adx > 25:
        return "trend-follow"
    if indicators.get("bb_pct", 0.5) < 0.1 or indicators.get("bb_pct", 0.5) > 0.9:
        return "mean-reversion"
    return "breakout"


# ─── Trailing Stop Logic ──────────────────────────────────────────────────────
def update_trailing_stop(pos, current_price):
    """Activate and update trailing stop. Returns updated pos dict."""
    entry  = float(pos.get("entry_price", 0))
    qty    = int(pos.get("qty", 1))
    is_buy = pos["type"] == "BUY"
    atr    = float(pos.get("indicators", {}).get("atr", entry * 0.02) or entry * 0.02)
    if atr <= 0:
        atr = entry * 0.02

    if is_buy:
        pnl_pct = (current_price - entry) / entry * 100 if entry > 0 else 0
        if pnl_pct >= 1.0:                            # activate at 1% profit
            if pos.get("trailing_stop") is None:
                pos["trailing_stop"] = entry           # move to breakeven
            else:
                new_trail = current_price - 1.5 * atr
                if new_trail > pos["trailing_stop"]:
                    pos["trailing_stop"] = round(new_trail, 2)
    else:  # SELL short
        pnl_pct = (entry - current_price) / entry * 100 if entry > 0 else 0
        if pnl_pct >= 1.0:
            if pos.get("trailing_stop") is None:
                pos["trailing_stop"] = entry
            else:
                new_trail = current_price + 1.5 * atr
                if new_trail < pos["trailing_stop"]:
                    pos["trailing_stop"] = round(new_trail, 2)
    return pos

def should_time_exit(pos, max_minutes=45):
    """Time-based exit: if trade hasn't moved in max_minutes, exit."""
    try:
        entry_dt = pos.get("entry_dt")
        if entry_dt is None:
            return False
        elapsed = (datetime.now() - entry_dt).total_seconds() / 60
        if elapsed < max_minutes:
            return False
        # Only exit if price hasn't moved more than 0.5%
        entry = float(pos.get("entry_price", 0))
        cmp   = float(pos.get("cmp", entry))
        if entry > 0 and abs(cmp - entry) / entry < 0.005:
            return True
    except Exception:
        pass
    return False


# ─── Auto Trading Engine ──────────────────────────────────────────────────────
def auto_trade_step_multi(all_symbols, capital_per_trade, max_open_positions,
                           min_strength, market_mood=None, top_sectors=None):
    scan_limit      = min(len(all_symbols), 500)
    symbols_to_scan = all_symbols[:scan_limit]

    recommendations = scan_symbols_parallel(
        symbols_to_scan, max_workers=30,
        market_mood=market_mood, top_sectors=top_sectors,
    )

    new_trades    = []
    existing_keys = {p["symbol"] + p["type"] for p in st.session_state.portfolio}

    # Market mood guard: if BEARISH only allow SELL, if BULLISH only allow BUY
    mood = market_mood.get("mood", "UNKNOWN") if market_mood else "UNKNOWN"
    vix  = market_mood.get("vix", 15) if market_mood else 15

    win_rate = st.session_state.get("kelly_win_rate", 0.55)

    for rec in recommendations:
        if len(st.session_state.portfolio) + len(new_trades) >= max_open_positions:
            break
        if rec.get("recommendation") == "NEUTRAL":
            continue
        if rec.get("strength", 0) < min_strength:
            break

        # VIX guard
        if vix > 25:
            continue  # too risky — skip all new trades

        # Mood alignment
        if mood == "BEARISH" and rec["recommendation"] == "BUY":
            continue
        if mood == "BULLISH" and rec["recommendation"] == "SELL":
            continue

        key = rec["symbol"] + rec["recommendation"]
        if key in existing_keys:
            continue

        try:
            trade = build_trade_from_rec(rec, capital_per_trade, win_rate=win_rate)
        except Exception:
            trade = None
        if trade:
            new_trades.append(trade)
            existing_keys.add(key)

    return new_trades


def square_off_positions(log_entries):
    closed    = []
    total_pnl = 0.0
    for pos in st.session_state.portfolio:
        price = get_live_price(pos["symbol"]) or pos.get("entry_price", 0)
        try:
            price = float(price)
        except (TypeError, ValueError):
            price = float(pos.get("entry_price", 0))

        entry = float(pos.get("entry_price", 0))
        qty   = int(pos.get("qty", 1))
        cost  = float(pos.get("brokerage", 0))
        pnl   = (price - entry) * qty if pos["type"] == "BUY" else (entry - price) * qty
        net_pnl = pnl - cost  # deduct brokerage

        trade_result = {
            **pos, "exit_price": price,
            "exit_time": datetime.now().strftime("%H:%M:%S"),
            "pnl": round(net_pnl, 2), "status": "CLOSED"
        }
        closed.append(trade_result)
        total_pnl += net_pnl

        # Journal entry
        st.session_state.trade_journal.append({
            "symbol":     pos["symbol"],
            "setup_type": pos.get("setup_type", "unknown"),
            "pnl":        round(net_pnl, 2),
            "win":        net_pnl >= 0,
            "strength":   pos.get("strength", 0),
            "sector":     pos.get("sector", "N/A"),
            "date":       datetime.now().strftime("%Y-%m-%d"),
        })

        # Update per-stock win rate
        sym = pos["symbol"]
        if sym not in st.session_state.win_rate_by_stock:
            st.session_state.win_rate_by_stock[sym] = {"wins": 0, "total": 0}
        st.session_state.win_rate_by_stock[sym]["total"] += 1
        if net_pnl >= 0:
            st.session_state.win_rate_by_stock[sym]["wins"] += 1

    # Update global Kelly win rate
    total_trades = len(st.session_state.trade_journal)
    if total_trades > 0:
        total_wins = sum(1 for t in st.session_state.trade_journal if t["win"])
        st.session_state.kelly_win_rate = total_wins / total_trades

    st.session_state.history.extend(closed)
    st.session_state.portfolio    = []
    st.session_state.used_capital = 0.0
    return closed, total_pnl


def generate_trade_report(closed_trades, total_pnl, duration_mins):
    total_brokerage = sum(t.get("brokerage", 0) for t in closed_trades)
    gross_pnl       = total_pnl + total_brokerage
    lines = [
        "=" * 70,
        "      EQUITY TRADER PRO v2 — AUTO TRADING SESSION REPORT",
        "=" * 70,
        f"Generated   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Duration    : {duration_mins} minutes",
        f"Total Trades: {len(closed_trades)}",
        f"Gross P&L   : ₹{gross_pnl:,.2f}",
        f"Brokerage   : ₹{total_brokerage:,.2f}",
        f"Net P&L     : ₹{total_pnl:,.2f}",
        "",
    ]
    for i, t in enumerate(closed_trades, 1):
        lines += [
            "─" * 70,
            f"Trade #{i}  |  {t.get('name', t['symbol'])}  ({t['symbol']})  |  {t['type']}",
            f"  Setup Type  : {t.get('setup_type','N/A')}",
            f"  Sector      : {t.get('sector','N/A')}",
            f"  Market Mode : {t.get('market_mode','N/A')}",
            f"  Entry Time  : {t.get('entry_time','N/A')}",
            f"  Exit Time   : {t.get('exit_time','N/A')}",
            f"  Entry Price : ₹{t.get('entry_price',0):,.2f}",
            f"  Exit Price  : ₹{t.get('exit_price','N/A')}",
            f"  Qty         : {t.get('qty',0)} shares",
            f"  Invested    : ₹{t.get('invested',0):,.2f}",
            f"  Brokerage   : ₹{t.get('brokerage',0):,.2f}",
            f"  Signal Str  : {t.get('strength',0)}%",
            f"  Net P&L     : ₹{t.get('pnl',0):,.2f}  {'✅' if t.get('pnl',0) >= 0 else '❌'}",
            "",
            "  SIGNAL REASONING:",
        ]
        for r in t.get("reasoning", []):
            lines.append(f"    • {r}")
        lines.append("")
        inds = t.get("indicators", {})
        if inds:
            lines.append("  KEY INDICATORS AT ENTRY:")
            if inds.get('rsi'):    lines.append(f"    RSI       : {inds['rsi']:.1f}")
            if inds.get('macd'):   lines.append(f"    MACD      : {inds['macd']:.4f}")
            if inds.get('bb_pct'): lines.append(f"    BB %      : {inds['bb_pct']:.2f}")
            if inds.get('adx'):    lines.append(f"    ADX       : {inds['adx']:.1f}")
            lines.append(f"    Stoch K/D : {inds.get('stoch_k',0):.1f} / {inds.get('stoch_d',0):.1f}")
            lines.append(f"    Vol Ratio : {inds.get('vol_ratio',1):.2f}x")
        if t.get("patterns"):
            lines.append(f"  CANDLESTICK PATTERNS: {', '.join(t['patterns'])}")
        lines.append("")
    lines += ["=" * 70, "END OF REPORT"]
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
#  UI
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<h1 style='font-family:Syne;font-weight:800;font-size:2.2rem;
background:linear-gradient(90deg,#00d4ff,#00ff88);
-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:4px;'>
📈 Equity Trader Pro v2</h1>
<p style='color:#64748b;font-size:0.85rem;margin-top:0;'>
AI-Powered · Multi-Timeframe · Candlestick Patterns · RSI Divergence · Market Mood · Kelly Sizing · Trailing Stops</p>
""", unsafe_allow_html=True)

# ── Market Context Banner ─────────────────────────────────────────────────────
market_mood  = get_market_mood()
top_sectors  = get_top_sectors(3)
mood         = market_mood.get("mood", "UNKNOWN")
vix          = market_mood.get("vix", 15)
nifty_chg    = market_mood.get("nifty_change", 0)

mood_class = "market-mood-bullish" if mood == "BULLISH" else ("market-mood-bearish" if mood == "BEARISH" else "market-mood-sideways")
mood_icon  = "🟢" if mood == "BULLISH" else ("🔴" if mood == "BEARISH" else "🟡")
vix_class  = "vix-low" if vix < 13 else ("vix-high" if vix > 20 else "vix-mid")

mc1, mc2, mc3 = st.columns([2, 1, 2])
with mc1:
    st.markdown(
        f'<div class="{mood_class}"><b style="font-size:1rem;">{mood_icon} Market Mood: {mood}</b><br>'
        f'<span style="font-size:0.8rem;color:#94a3b8;">Nifty {nifty_chg:+.2f}% today</span></div>',
        unsafe_allow_html=True,
    )
with mc2:
    st.markdown(
        f'<div class="{vix_class}"><b>India VIX: {vix:.1f}</b><br>'
        f'<span style="font-size:0.75rem;">{"🔴 High Risk" if vix > 20 else ("🟢 Calm" if vix < 13 else "🟡 Moderate")}</span></div>',
        unsafe_allow_html=True,
    )
with mc3:
    sector_sm = get_sector_momentum()
    top3 = list(sector_sm.items())[:3]
    sector_html = " ".join([
        f'<span class="sector-chip">#{i+1} {s} {c:+.1f}%</span>'
        for i, (s, c) in enumerate(top3)
    ])
    st.markdown(
        f'<div style="background:rgba(0,0,0,0.2);border:1px solid #1e293b;border-radius:10px;padding:10px 14px;">'
        f'<span style="font-size:0.75rem;color:#64748b;">HOT SECTORS TODAY</span><br>{sector_html}</div>',
        unsafe_allow_html=True,
    )

if vix > 20:
    st.markdown(
        '<div class="warning-box">⚠️ <b>HIGH VIX ALERT:</b> India VIX > 20. '
        'Auto trading is restricted. Use wider stops and reduce position size.</div>',
        unsafe_allow_html=True,
    )

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    starting_capital = st.number_input("💰 Capital (₹)", value=100000, step=10000)
    st.session_state.capital = float(starting_capital)
    capital_per_trade = st.number_input("Base Per-Trade Capital (₹)", value=5000, step=1000)

    use_kelly = st.checkbox("🧮 Use Kelly Criterion Sizing", value=True,
                            help="Adjusts trade size based on signal strength and historical win rate")
    use_multi_tf = st.checkbox("🕐 Multi-Timeframe Confirmation", value=False,
                               help="Slower but higher accuracy — confirms signal on 15min+1hr+Daily")
    use_market_filter = st.checkbox("🌐 Market Mood Filter", value=True,
                                    help="Avoid BUY signals when Nifty is bearish")
    use_sector_filter = st.checkbox("🏭 Sector Rotation Filter", value=True,
                                    help="Bonus score for stocks in today's top sectors")
    use_trailing_stop = st.checkbox("🎯 Trailing Stop Loss", value=True,
                                    help="Move stop to breakeven after 1% profit, trail at 2%")
    use_time_exit     = st.checkbox("⏱️ Time-Based Exit (45 min)", value=True,
                                    help="Exit if trade is flat after 45 minutes")
    use_intraday_only = st.checkbox("🔒 Intraday Only (Square off at 3:15 PM)", value=True,
                                    help="Auto square-off all positions by 3:15 PM")

    st.markdown("---")
    st.markdown("### 🌐 NSE Universe")
    if st.button("🔄 Refresh NSE Symbol List", use_container_width=True):
        fetch_nse_all_symbols.clear()
        get_market_mood.clear()
        get_sector_momentum.clear()

    all_nse = get_nse_symbols()
    st.markdown(
        f'<div class="scan-info">📡 <b>{len(all_nse):,}</b> NSE symbols loaded</div>',
        unsafe_allow_html=True,
    )

    st.markdown("**Optional: Pin specific symbols**")
    pinned_symbols = st.multiselect(
        "Always include in scan",
        options=all_nse[:500],
        default=[],
    )

    scan_top_n = st.slider(
        "Scan top N symbols", min_value=20, max_value=min(500, len(all_nse)),
        value=150, step=10,
    )
    min_signal_strength = st.slider("Min Signal Strength", 50, 90, 65, 5)
    max_open_positions  = st.slider("Max Open Positions", 1, 30, 10, 1)

    st.markdown("---")
    st.markdown("### 📊 Session Stats")
    kelly_wr = st.session_state.get("kelly_win_rate", 0.55)
    st.markdown(
        f'<div class="kelly-info">🧮 Kelly Win Rate: <b>{kelly_wr*100:.1f}%</b><br>'
        f'<span style="font-size:0.75rem;">Based on {len(st.session_state.trade_journal)} historical trades</span></div>',
        unsafe_allow_html=True,
    )
    total_hist_pnl = sum(t.get("pnl", 0) for t in st.session_state.history)
    open_pnl       = sum(t.get("pnl", 0) for t in st.session_state.portfolio)
    st.metric("Open Positions", len(st.session_state.portfolio))
    st.metric("Closed Trades",  len(st.session_state.history))
    st.metric("Unrealised P&L", f"₹{open_pnl:,.2f}", delta="↑" if open_pnl >= 0 else "↓")
    st.metric("Realized P&L",   f"₹{total_hist_pnl:,.2f}", delta="↑" if total_hist_pnl >= 0 else "↓")

# Effective scan universe
effective_scan_universe = list(dict.fromkeys(
    pinned_symbols + [s for s in all_nse if s not in pinned_symbols]
))[: scan_top_n + len(pinned_symbols)]

_market_mood_arg   = market_mood if use_market_filter else None
_top_sectors_arg   = top_sectors if use_sector_filter else None

# ─── 3:15 PM Intraday Squareoff ───────────────────────────────────────────────
if use_intraday_only and st.session_state.portfolio:
    now = datetime.now()
    if now.hour == 15 and now.minute >= 15:
        st.warning("⏰ 3:15 PM — Auto squaring off all intraday positions!")
        closed_trades, total_pnl = square_off_positions(st.session_state.auto_trade_log)
        report = generate_trade_report(closed_trades, total_pnl, 0)
        st.session_state.auto_trading = False
        st.session_state._last_report = report
        st.session_state._last_pnl    = total_pnl
        st.rerun()

# ─── Tabs ─────────────────────────────────────────────────────────────────────
tabs = st.tabs([
    "🔍 Signal Scanner", "⚡ Auto Trading", "📋 Watchlist",
    "💼 Portfolio", "📜 History", "📓 Trade Journal"
])

# ──────────────────────────────────────────────────────────────────────────────
# TAB 1 — Signal Scanner
# ──────────────────────────────────────────────────────────────────────────────
with tabs[0]:
    st.markdown('<div class="section-title">📡 Live Equity Signal Scanner — Multi-Factor · Full NSE</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="scan-info">🌐 Scanning from <b>{len(effective_scan_universe)}</b> NSE symbols. '
        f'Enhanced signals: Market Mood ✓ Sector Filter ✓ Candlestick Patterns ✓ RSI Divergence ✓ '
        f'Support/Resistance ✓ Fibonacci ✓</div>',
        unsafe_allow_html=True,
    )

    col_scan, col_sym = st.columns([1, 3])
    with col_scan:
        scan_btn = st.button("🔄 Scan NSE Universe", use_container_width=True)
    with col_sym:
        single_sym = st.selectbox("Quick Analyse Single Symbol", [""] + effective_scan_universe)

    if scan_btn or (single_sym and single_sym != ""):
        symbols = [single_sym] if (single_sym and single_sym != "") else effective_scan_universe
        with st.spinner(f"🔭 Scanning {len(symbols)} symbols with enhanced multi-factor analysis…"):
            prog_bar = st.progress(0)
            results  = scan_symbols_parallel(
                symbols, max_workers=30,
                market_mood=_market_mood_arg,
                top_sectors=_top_sectors_arg,
            )
            prog_bar.progress(1.0)
        prog_bar.empty()
        st.session_state.last_scan_results = results
    else:
        results = st.session_state.get("last_scan_results", [])

    if results:
        buys     = [r for r in results if r["recommendation"] == "BUY"]
        sells    = [r for r in results if r["recommendation"] == "SELL"]
        neutrals = [r for r in results if r["recommendation"] == "NEUTRAL"]

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.markdown(f'<div class="metric-card"><div class="metric-value accent">{len(results)}</div><div class="metric-label">Scanned</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-card"><div class="metric-value green">{len(buys)}</div><div class="metric-label">BUY Signals</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="metric-card"><div class="metric-value red">{len(sells)}</div><div class="metric-label">SELL Signals</div></div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="metric-card"><div class="metric-value yellow">{len(neutrals)}</div><div class="metric-label">Neutral</div></div>', unsafe_allow_html=True)
        avg_str = np.mean([r["strength"] for r in results if r["recommendation"] != "NEUTRAL"]) if (buys or sells) else 0
        c5.markdown(f'<div class="metric-card"><div class="metric-value accent">{avg_str:.0f}%</div><div class="metric-label">Avg Strength</div></div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        # Summary Table
        st.markdown("#### 📊 Signal Summary Table (Strongest First)")
        table_data = []
        for rec in results:
            if rec["recommendation"] == "NEUTRAL":
                continue
            day_chg  = rec.get("day_change", 0) or 0
            mom_1m   = rec.get("momentum_1m", 0) or 0
            patterns = [p[0] for p in rec.get("patterns", [])]
            div      = "✓" if rec.get("divergence") else ""
            table_data.append({
                "Symbol":        rec["symbol"].replace(".NS",""),
                "CMP (₹)":      f"₹{rec['cmp']:,.2f}",
                "Signal":        rec["recommendation"],
                "Strength (%)":  rec["strength"],
                "Target (₹)":   f"₹{rec['target']:,.2f}",
                "Stop (₹)":     f"₹{rec['stop']:,.2f}",
                "Day Chg (%)":   f"{day_chg:+.2f}%",
                "1M Mom (%)":    f"{mom_1m:+.1f}%",
                "Mode":          rec.get("market_mode", "N/A"),
                "Patterns":      ", ".join(patterns) if patterns else "—",
                "Divergence":    div,
                "Sector":        rec.get("sector","N/A"),
            })
        if table_data:
            df_table = pd.DataFrame(table_data)
            st.dataframe(df_table, use_container_width=True, hide_index=True)
        st.markdown("<br>", unsafe_allow_html=True)

        # Detailed Cards
        st.markdown("#### 🔎 Detailed Signal Cards")
        sorted_results = (
            [r for r in results if r["recommendation"] != "NEUTRAL"]
            + [r for r in results if r["recommendation"] == "NEUTRAL"]
        )

        for rec in sorted_results:
            icon      = "🟢" if rec["recommendation"] == "BUY" else ("🔴" if rec["recommendation"] == "SELL" else "🟡")
            day_chg   = rec.get("day_change", 0) or 0
            chg_icon  = "▲" if day_chg >= 0 else "▼"
            patterns  = [p[0] for p in rec.get("patterns", [])]
            pat_str   = f" 🕯️{', '.join(patterns)}" if patterns else ""
            div_str   = " 📐DIV" if rec.get("divergence") else ""

            with st.expander(
                f"{icon} {rec['symbol'].replace('.NS','')} | "
                f"CMP ₹{rec['cmp']:,.2f} ({chg_icon}{abs(day_chg):.2f}%) | "
                f"{rec['recommendation']} | Strength {rec['strength']}%"
                f"{pat_str}{div_str}"
            ):
                c1, c2, c3, c4, c5, c6 = st.columns(6)
                c1.metric("CMP",       f"₹{rec['cmp']:,.2f}")
                c2.metric("Signal",    rec["recommendation"])
                c3.metric("Strength",  f"{rec['strength']}%")
                c4.metric("Target",    f"₹{rec['target']:,.2f}")
                c5.metric("Stop Loss", f"₹{rec['stop']:,.2f}")
                c6.metric("Day Chg",   f"{day_chg:+.2f}%", delta=f"{day_chg:+.2f}%")

                # Strength bar
                bar_color = "#00ff88" if rec["recommendation"] == "BUY" else "#ff3366"
                st.markdown(
                    f'<div class="strength-bar-wrap"><div class="strength-bar-fill" '
                    f'style="width:{rec["strength"]}%;background:{bar_color};"></div></div>',
                    unsafe_allow_html=True,
                )
                st.markdown("<br>", unsafe_allow_html=True)

                # Momentum + Mode + Sector row
                mm1, mm2, mm3, mm4 = st.columns(4)
                mm1.metric("1M Momentum", f"{rec.get('momentum_1m',0):+.1f}%")
                mm2.metric("3M Momentum", f"{rec.get('momentum_3m',0):+.1f}%")
                mm3.metric("Market Mode", rec.get("market_mode", "N/A"))
                mm4.metric("R/R Ratio",   f"{rec.get('rr_ratio',1.5):.2f}")

                # Candlestick patterns
                if patterns:
                    st.markdown("**🕯️ Candlestick Patterns Detected**")
                    pat_html = " ".join([f'<span class="candle-pattern">{p}</span>' for p in patterns])
                    st.markdown(pat_html, unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)

                # RSI Divergence
                if rec.get("divergence"):
                    dtype, dsignal, dmsg = rec["divergence"]
                    div_color = "#00d4ff" if dsignal == "BUY" else "#ff3366"
                    st.markdown(
                        f'<div class="divergence-box" style="border-left-color:{div_color};">'
                        f'📐 <b>{dtype.replace("_"," ")}</b>: {dmsg}</div>',
                        unsafe_allow_html=True,
                    )
                    st.markdown("<br>", unsafe_allow_html=True)

                # Support / Resistance
                support    = rec.get("support")
                resistance = rec.get("resistance")
                if support and resistance:
                    sr1, sr2 = st.columns(2)
                    sr1.metric("Support Level",    f"₹{support:.2f}")
                    sr2.metric("Resistance Level", f"₹{resistance:.2f}")

                # Fibonacci levels
                fibs = rec.get("fibs", {})
                if fibs:
                    fb1, fb2, fb3 = st.columns(3)
                    fb1.metric("Fib 38.2%", f"₹{fibs.get('fib_382',0):.2f}")
                    fb2.metric("Fib 50%",   f"₹{fibs.get('fib_500',0):.2f}")
                    fb3.metric("Fib 61.8%", f"₹{fibs.get('fib_618',0):.2f}")

                # Technical indicators
                ind = rec["indicators"]
                if ind:
                    st.markdown("**📐 Technical Indicators**")
                    ic1, ic2, ic3, ic4, ic5, ic6, ic7 = st.columns(7)
                    ic1.metric("RSI",       f"{ind.get('rsi',0):.1f}")
                    ic2.metric("MACD",      f"{ind.get('macd',0):.3f}")
                    ic3.metric("ADX",       f"{ind.get('adx',0):.1f}")
                    ic4.metric("BB%",       f"{ind.get('bb_pct',0):.2f}")
                    ic5.metric("Stoch K",   f"{ind.get('stoch_k',0):.1f}")
                    ic6.metric("Vol Ratio", f"{ind.get('vol_ratio',1):.1f}x")
                    ic7.metric("CCI",       f"{ind.get('cci',0):.0f}")

                # Signal reasoning
                st.markdown("**💡 Signal Reasoning**")
                for r in rec["reasoning"]:
                    col_icon = "🟢" if "BUY" in r else ("🔴" if "SELL" in r else "⚪")
                    st.markdown(f"{col_icon} {r}")

                # Kelly sizing preview
                kelly_wr = st.session_state.get("kelly_win_rate", 0.55)
                kelly_cap = kelly_position_size(
                    float(capital_per_trade), kelly_wr,
                    rec.get("rr_ratio", 1.5), rec.get("strength", 65)
                )
                estimated_cost = compute_trade_cost(rec["cmp"], max(1, int(kelly_cap / rec["cmp"])), rec["recommendation"])
                st.markdown(
                    f'<div class="kelly-info">🧮 Kelly Position Size: ₹{kelly_cap:,.0f} | '
                    f'Estimated Cost (brokerage+taxes): ₹{estimated_cost:.2f}</div>',
                    unsafe_allow_html=True,
                )

                # Fundamentals
                fund = rec["fundamentals"]
                if fund:
                    with st.expander("📊 Fundamentals & Valuation"):
                        fc1, fc2, fc3, fc4, fc5, fc6 = st.columns(6)
                        fc1.metric("P/E",      f"{fund.get('pe','N/A')}")
                        fc2.metric("P/B",      f"{fund.get('pb','N/A')}")
                        fc3.metric("Beta",     f"{fund.get('beta','N/A')}")
                        fc4.metric("EPS",      f"{fund.get('eps','N/A')}")
                        fc5.metric("52W High", f"₹{fund.get('52w_high','N/A')}")
                        fc6.metric("52W Low",  f"₹{fund.get('52w_low','N/A')}")
                        st.markdown(f"**Sector:** {fund.get('sector','N/A')} | **Industry:** {fund.get('industry','N/A')}")
                        if should_skip_earnings(fund):
                            st.warning("⚠️ Earnings within 7 days — trade with caution!")

                bc1, bc2 = st.columns(2)
                with bc1:
                    if st.button("➕ Add to Watchlist", key=f"wl_{rec['symbol']}"):
                        st.session_state.watchlist.append({
                            "symbol": rec["symbol"],
                            "type":   rec["recommendation"] if rec["recommendation"] != "NEUTRAL" else "BUY",
                            "cmp":    rec["cmp"],
                            "target": rec["target"],
                            "stop":   rec["stop"],
                            "added":  datetime.now().strftime("%H:%M:%S"),
                        })
                        st.success("Added to watchlist!")
                with bc2:
                    if rec["recommendation"] != "NEUTRAL":
                        btn_label = f"🚀 {'BUY' if rec['recommendation']=='BUY' else 'SELL SHORT'} {rec['symbol'].replace('.NS','')}"
                        if st.button(btn_label, key=f"buy_{rec['symbol']}"):
                            try:
                                trade = build_trade_from_rec(rec, capital_per_trade,
                                                             win_rate=st.session_state.get("kelly_win_rate", 0.55),
                                                             use_kelly=use_kelly)
                            except Exception:
                                trade = None
                            if trade:
                                st.session_state.portfolio.append(trade)
                                st.success(f"✅ {rec['recommendation']} executed on {rec['symbol']} | Kelly size: ₹{trade['invested']:,.0f}")
                            else:
                                st.error("Could not build trade — check price data.")
    else:
        st.info("👆 Click **Scan NSE Universe** or select a symbol above to begin analysis.")

# ──────────────────────────────────────────────────────────────────────────────
# TAB 2 — Auto Trading
# ──────────────────────────────────────────────────────────────────────────────
with tabs[1]:
    st.markdown('<div class="section-title">⚡ AI Equity Auto Trading Engine — Enhanced Multi-Factor</div>', unsafe_allow_html=True)

    if mood == "BEARISH":
        st.markdown('<div class="warning-box">🔴 Market is BEARISH — Auto trading will only open SELL signals (short). BUY signals suppressed.</div>', unsafe_allow_html=True)
    if vix > 25:
        st.markdown('<div class="warning-box">⚠️ VIX > 25 — Auto trading PAUSED. Too risky. Wait for VIX to drop below 20.</div>', unsafe_allow_html=True)

    st.markdown(
        f'<div class="auto-trade-box">'
        f'<h2 style="color:#00d4ff;font-family:Syne;font-weight:800;">🤖 Autonomous Multi-Position Equity AI v2</h2>'
        f'<p style="color:#94a3b8;">Scans <b>{len(effective_scan_universe)}</b> NSE stocks · '
        f'Strongest signals only · Kelly position sizing · Trailing stops · '
        f'Time-based exits · Market mood filter · Sector rotation · '
        f'Brokerage simulation · Earnings avoidance</p></div>',
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    if not st.session_state.auto_trading:
        _, col_t2, _ = st.columns([1, 2, 1])
        with col_t2:
            auto_mins    = st.number_input("⏱️ Duration (minutes)", min_value=1, max_value=480, value=15, step=5)
            auto_capital = st.number_input("💰 Base capital per trade (₹)", min_value=1000, value=5000, step=1000)
            auto_max_pos = st.number_input("📊 Max simultaneous positions", min_value=1, max_value=50,
                                           value=max_open_positions, step=1)
            auto_min_str = st.number_input("🎯 Min signal strength (%)", min_value=50, max_value=95,
                                           value=min_signal_strength, step=5)
            st.markdown(
                f'<div class="scan-info">🔭 Will scan <b>{len(effective_scan_universe)}</b> symbols · '
                f'Picks <b>top {int(auto_max_pos)} strongest signals ≥ {int(auto_min_str)}%</b><br>'
                f'Kelly sizing: {"ON ✓" if use_kelly else "OFF"} | '
                f'Market filter: {"ON ✓" if use_market_filter else "OFF"} | '
                f'Sector filter: {"ON ✓" if use_sector_filter else "OFF"}</div>',
                unsafe_allow_html=True,
            )
            st.markdown("<br>", unsafe_allow_html=True)
            if vix <= 25:
                if st.button("🚀 START AUTO TRADING", use_container_width=True):
                    st.session_state.auto_trading    = True
                    st.session_state.auto_trade_end  = datetime.now() + timedelta(minutes=int(auto_mins))
                    st.session_state.auto_trade_log  = []
                    st.session_state.auto_pnl        = 0.0
                    st.session_state._auto_duration  = int(auto_mins)
                    st.session_state._auto_capital   = float(auto_capital)
                    st.session_state._auto_max_pos   = int(auto_max_pos)
                    st.session_state._auto_min_str   = int(auto_min_str)
                    st.session_state.session_start   = datetime.now()
                    st.rerun()
            else:
                st.error("🚫 Auto trading blocked — VIX too high (>25). Wait for volatility to subside.")
    else:
        end_time  = st.session_state.auto_trade_end
        remaining = max(0.0, (end_time - datetime.now()).total_seconds())
        total_sec = st.session_state._auto_duration * 60
        progress  = (total_sec - remaining) / total_sec if total_sec > 0 else 1.0

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("⏱ Time Left",   f"{int(remaining // 60)}m {int(remaining % 60)}s")
        c2.metric("Open Positions", len(st.session_state.portfolio))
        live_pnl = sum(t.get("pnl", 0) for t in st.session_state.portfolio)
        c3.metric("Live P&L",       f"₹{live_pnl:,.2f}", delta="▲" if live_pnl >= 0 else "▼")
        c4.metric("Realized P&L",   f"₹{sum(t.get('pnl',0) for t in st.session_state.history):,.2f}")
        c5.metric("Total Trades",   len(st.session_state.auto_trade_log))
        st.progress(min(progress, 1.0))

        if remaining <= 0:
            st.warning("⏰ Time up! Squaring off all positions…")
            closed_trades, total_pnl = square_off_positions(st.session_state.auto_trade_log)
            report = generate_trade_report(closed_trades, total_pnl, st.session_state._auto_duration)
            st.session_state.auto_trading = False
            st.session_state._last_report = report
            st.session_state._last_pnl    = total_pnl
            st.rerun()
        else:
            _max_pos = st.session_state.get("_auto_max_pos", 10)
            _min_str = st.session_state.get("_auto_min_str", 65)
            _capital = st.session_state.get("_auto_capital", 5000.0)

            if len(st.session_state.portfolio) < _max_pos and vix <= 25:
                with st.spinner(f"🔭 Scanning {len(effective_scan_universe)} stocks…"):
                    try:
                        new_trades = auto_trade_step_multi(
                            effective_scan_universe,
                            capital_per_trade=_capital,
                            max_open_positions=_max_pos,
                            min_strength=_min_str,
                            market_mood=_market_mood_arg,
                            top_sectors=_top_sectors_arg,
                        )
                    except Exception as e:
                        new_trades = []
                        st.warning(f"Scan error: {e}")

                existing = {p["symbol"] + p["type"] for p in st.session_state.portfolio}
                for t in new_trades:
                    key = t["symbol"] + t["type"]
                    if key not in existing:
                        st.session_state.portfolio.append(t)
                        st.session_state.auto_trade_log.append(t)
                        existing.add(key)

            # Update P&L, trailing stop, time exit, target/stop checks
            still_open = []
            for pos in st.session_state.portfolio:
                price = get_live_price(pos["symbol"]) or pos.get("entry_price", 0)
                try:
                    price = float(price)
                except (TypeError, ValueError):
                    price = float(pos.get("entry_price", 0))
                pos["cmp"] = price
                entry = float(pos.get("entry_price", 0))
                qty   = int(pos.get("qty", 1))
                cost  = float(pos.get("brokerage", 0))

                # Trailing stop update
                if use_trailing_stop:
                    pos = update_trailing_stop(pos, price)

                effective_stop = pos.get("trailing_stop") or pos.get("stop", 0)

                if pos["type"] == "BUY":
                    gross_pnl  = (price - entry) * qty
                    pos["pnl"] = round(gross_pnl - cost, 2)
                    hit_exit   = price >= pos.get("target", price + 1) or price <= effective_stop
                else:
                    gross_pnl  = (entry - price) * qty
                    pos["pnl"] = round(gross_pnl - cost, 2)
                    hit_exit   = price <= pos.get("target", 0) or price >= effective_stop

                # Time-based exit
                if use_time_exit and should_time_exit(pos):
                    hit_exit = True
                    pos["exit_reason"] = "time_exit"

                if hit_exit:
                    cost2 = compute_trade_cost(price, qty, pos["type"])
                    net   = pos["pnl"] - cost2
                    st.session_state.history.append({
                        **pos, "exit_price": price,
                        "exit_time": datetime.now().strftime("%H:%M:%S"),
                        "pnl": round(net, 2), "status": "CLOSED",
                    })
                    st.session_state.trade_journal.append({
                        "symbol":     pos["symbol"],
                        "setup_type": pos.get("setup_type", "unknown"),
                        "pnl":        round(net, 2),
                        "win":        net >= 0,
                        "strength":   pos.get("strength", 0),
                        "sector":     pos.get("sector", "N/A"),
                        "date":       datetime.now().strftime("%Y-%m-%d"),
                    })
                else:
                    still_open.append(pos)
            st.session_state.portfolio = still_open

            # Live positions
            st.markdown("### 📊 Live Positions")
            if st.session_state.portfolio:
                df_pos = pd.DataFrame(st.session_state.portfolio)
                if "cmp" not in df_pos.columns:
                    df_pos["cmp"] = df_pos["entry_price"]
                # Add trailing stop column
                if "trailing_stop" not in df_pos.columns:
                    df_pos["trailing_stop"] = None
                disp = [c for c in ["symbol","type","cmp","entry_price","qty","invested",
                                     "target","stop","trailing_stop","pnl","strength","setup_type","sector"]
                        if c in df_pos.columns]
                rename_map = {"cmp":"CMP(₹)","entry_price":"Entry(₹)","pnl":"Net P&L(₹)",
                              "strength":"Signal%","setup_type":"Setup","trailing_stop":"Trail Stop"}
                st.dataframe(df_pos[disp].rename(columns=rename_map), use_container_width=True)
            else:
                st.info("No open positions. Scanning for next cycle…")

            st.markdown("### 📋 Auto Trade Log")
            for t in reversed(st.session_state.auto_trade_log[-20:]):
                badge     = "🟢 BUY" if t["type"] == "BUY" else "🔴 SELL"
                setup     = t.get("setup_type", "")
                trail_str = f" | Trail: ₹{t.get('trailing_stop'):,.2f}" if t.get("trailing_stop") else ""
                st.markdown(
                    f"- {badge} **{t['symbol'].replace('.NS','')}** | "
                    f"₹{t['cmp']:,.2f} | Strength **{t['strength']}%** | "
                    f"Qty {t['qty']} | Setup: {setup}{trail_str}"
                )

            col_stop1, _ = st.columns([1, 3])
            with col_stop1:
                st.markdown('<div class="danger-btn">', unsafe_allow_html=True)
                if st.button("🛑 STOP & SQUARE OFF", use_container_width=True):
                    closed_trades, total_pnl = square_off_positions(st.session_state.auto_trade_log)
                    report = generate_trade_report(closed_trades, total_pnl, st.session_state._auto_duration)
                    st.session_state.auto_trading = False
                    st.session_state._last_report = report
                    st.session_state._last_pnl    = total_pnl
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            time.sleep(10)
            st.rerun()

    if not st.session_state.auto_trading and "_last_report" in st.session_state:
        pnl   = st.session_state._last_pnl
        color = "green" if pnl >= 0 else "red"
        st.markdown(f'<h3 class="{color}">Session ended. Net P&L (after brokerage): ₹{pnl:,.2f}</h3>', unsafe_allow_html=True)
        st.download_button(
            "📥 Download Trade Report (.txt)",
            data=st.session_state._last_report,
            file_name=f"equity_trade_report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain",
            use_container_width=True,
        )

# ──────────────────────────────────────────────────────────────────────────────
# TAB 3 — Watchlist
# ──────────────────────────────────────────────────────────────────────────────
with tabs[2]:
    st.markdown('<div class="section-title">👁️ Equity Watchlist</div>', unsafe_allow_html=True)

    with st.expander("➕ Add Stock to Watchlist"):
        wc1, wc2, wc3, wc4, wc5 = st.columns(5)
        w_sym    = wc1.selectbox("Symbol",       effective_scan_universe[:500], key="w_sym")
        w_type   = wc2.selectbox("Signal",       ["BUY", "SELL"], key="w_type")
        w_target = wc3.number_input("Target (₹)",    min_value=0.0, value=0.0, key="w_target")
        w_stop   = wc4.number_input("Stop Loss (₹)", min_value=0.0, value=0.0, key="w_stop")
        w_qty    = wc5.number_input("Qty (shares)",  min_value=1,   value=1,   step=1, key="w_qty")
        if st.button("Add to Watchlist", use_container_width=True):
            st.session_state.watchlist.append({
                "symbol": w_sym, "type": w_type,
                "target": w_target, "stop": w_stop, "qty": int(w_qty),
                "added":  datetime.now().strftime("%H:%M:%S"),
            })
            st.success("Added!")

    if not st.session_state.watchlist:
        st.info("Your watchlist is empty.")
    else:
        for i, w in enumerate(st.session_state.watchlist):
            cmp   = get_live_price(w["symbol"]) or 0
            badge = "🟢" if w["type"] == "BUY" else "🔴"
            col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 1, 1, 1, 1, 1, 1])
            col1.markdown(f"**{badge} {w['symbol'].replace('.NS','')}**")
            col2.markdown(f'<span class="cmp-badge">₹{cmp:,.2f}</span>', unsafe_allow_html=True)
            col3.markdown(f"Target: ₹{w['target']:.2f}")
            col4.markdown(f"Stop: ₹{w['stop']:.2f}")
            col5.markdown(f"Qty: {w.get('qty',1)}")
            if col6.button("Execute", key=f"wbuy_{i}"):
                qty  = w.get("qty", 1)
                cost = compute_trade_cost(cmp, qty, w["type"])
                st.session_state.portfolio.append({
                    "id":            f"{w['symbol']}_{w['type']}_{int(time.time())}",
                    "symbol":        w["symbol"],
                    "name":          w["symbol"],
                    "type":          w["type"],
                    "cmp":           cmp,
                    "entry_price":   cmp,
                    "qty":           qty,
                    "invested":      round(qty * cmp, 2),
                    "brokerage":     cost,
                    "target":        w["target"] or cmp * 1.02,
                    "stop":          w["stop"]   or cmp * 0.98,
                    "trailing_stop": None,
                    "entry_time":    datetime.now().strftime("%H:%M:%S"),
                    "entry_dt":      datetime.now(),
                    "status":        "OPEN", "pnl": 0.0,
                    "reasoning":     [], "indicators": {}, "strength": 0,
                    "sector":        "N/A", "setup_type": "manual",
                    "patterns":      [], "market_mode": "N/A",
                })
                st.success(f"{w['type']} executed on {w['symbol']}!")
            if col7.button("❌", key=f"wdel_{i}"):
                st.session_state.watchlist.pop(i)
                st.rerun()

# ──────────────────────────────────────────────────────────────────────────────
# TAB 4 — Portfolio
# ──────────────────────────────────────────────────────────────────────────────
with tabs[3]:
    st.markdown('<div class="section-title">💼 Live Equity Portfolio</div>', unsafe_allow_html=True)

    if not st.session_state.portfolio:
        st.info("No open positions.")
    else:
        total_live_pnl  = 0.0
        total_brokerage = 0.0
        for pos in st.session_state.portfolio:
            cmp = get_live_price(pos["symbol"]) or pos.get("entry_price", 0)
            try:
                cmp = float(cmp)
            except (TypeError, ValueError):
                cmp = float(pos.get("entry_price", 0))
            pos["cmp"] = cmp
            entry  = float(pos.get("entry_price", 0))
            qty    = int(pos.get("qty", 1))
            cost   = float(pos.get("brokerage", 0))
            gross  = (cmp - entry) * qty if pos["type"] == "BUY" else (entry - cmp) * qty
            pnl    = gross - cost
            pos["pnl"]     = round(pnl, 2)
            total_live_pnl += pnl
            total_brokerage += cost
            if use_trailing_stop:
                pos = update_trailing_stop(pos, cmp)

        total_invested = sum(p.get("invested", 0) for p in st.session_state.portfolio)
        pnl_pct        = (total_live_pnl / total_invested * 100) if total_invested > 0 else 0

        pc1, pc2, pc3, pc4 = st.columns(4)
        pc1.markdown(f'<div class="metric-card"><div class="metric-value accent">₹{total_invested:,.0f}</div><div class="metric-label">Total Invested</div></div>', unsafe_allow_html=True)
        pnl_col_val = "green" if total_live_pnl >= 0 else "red"
        pc2.markdown(f'<div class="metric-card"><div class="metric-value {pnl_col_val}">₹{total_live_pnl:,.2f}</div><div class="metric-label">Net Unrealised P&L</div></div>', unsafe_allow_html=True)
        pc3.markdown(f'<div class="metric-card"><div class="metric-value {pnl_col_val}">{pnl_pct:+.2f}%</div><div class="metric-label">Return %</div></div>', unsafe_allow_html=True)
        pc4.markdown(f'<div class="metric-card"><div class="metric-value yellow">₹{total_brokerage:,.2f}</div><div class="metric-label">Total Brokerage</div></div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        for pos in st.session_state.portfolio:
            badge    = "🟢 BUY" if pos["type"] == "BUY" else "🔴 SELL"
            pnl_sign = "+" if pos.get("pnl", 0) >= 0 else ""
            trail    = f" | Trail: ₹{pos.get('trailing_stop'):,.2f}" if pos.get("trailing_stop") else ""
            with st.expander(
                f"{badge} {pos['symbol'].replace('.NS','')} | "
                f"CMP ₹{pos.get('cmp', pos.get('entry_price',0)):,.2f} | "
                f"Net P&L: {pnl_sign}₹{pos.get('pnl',0):,.2f}{trail}"
            ):
                ltp = pos.get("cmp", pos.get("entry_price", 0))
                pc1, pc2, pc3, pc4, pc5, pc6 = st.columns(6)
                pc1.metric("Entry Price",  f"₹{pos.get('entry_price',0):.2f}")
                pc2.metric("CMP",          f"₹{float(ltp):.2f}")
                pc3.metric("Qty",          pos.get("qty", 1))
                pc4.metric("Target",       f"₹{pos.get('target',0):.2f}")
                pc5.metric("Stop",         f"₹{pos.get('stop',0):.2f}")
                pc6.metric("Net P&L",      f"₹{pos.get('pnl',0):,.2f}")

                if pos.get("trailing_stop"):
                    st.markdown(
                        f'<div class="trailing-stop-active">🎯 Trailing Stop Active: ₹{pos["trailing_stop"]:,.2f}</div>',
                        unsafe_allow_html=True,
                    )
                if pos.get("patterns"):
                    pat_html = " ".join([f'<span class="candle-pattern">{p}</span>' for p in pos["patterns"]])
                    st.markdown(f"**Patterns at entry:** {pat_html}", unsafe_allow_html=True)
                if pos.get("reasoning"):
                    st.markdown("**Signal Reasoning:**")
                    for r in pos["reasoning"][:5]:
                        st.markdown(f"• {r}")

                if st.button("Square Off", key=f"sq_{pos['id']}"):
                    exit_price = float(get_live_price(pos["symbol"]) or pos.get("entry_price", 0))
                    entry      = float(pos.get("entry_price", 0))
                    qty        = int(pos.get("qty", 1))
                    cost       = float(pos.get("brokerage", 0))
                    cost2      = compute_trade_cost(exit_price, qty, pos["type"])
                    gross      = (exit_price - entry) * qty if pos["type"] == "BUY" else (entry - exit_price) * qty
                    final_pnl  = gross - cost - cost2
                    st.session_state.history.append({
                        **pos, "exit_price": exit_price,
                        "exit_time": datetime.now().strftime("%H:%M:%S"),
                        "pnl": round(final_pnl, 2), "status": "CLOSED",
                    })
                    st.session_state.trade_journal.append({
                        "symbol":     pos["symbol"],
                        "setup_type": pos.get("setup_type", "manual"),
                        "pnl":        round(final_pnl, 2),
                        "win":        final_pnl >= 0,
                        "strength":   pos.get("strength", 0),
                        "sector":     pos.get("sector", "N/A"),
                        "date":       datetime.now().strftime("%Y-%m-%d"),
                    })
                    st.session_state.portfolio = [p for p in st.session_state.portfolio if p["id"] != pos["id"]]
                    st.success(f"Squared off {pos['symbol']} | Net P&L: ₹{final_pnl:,.2f} (after brokerage)")
                    st.rerun()

        if len(st.session_state.history) >= 2:
            hist_df = pd.DataFrame(st.session_state.history)
            hist_df["cumulative"] = hist_df["pnl"].cumsum()
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                y=hist_df["cumulative"], mode="lines+markers",
                line=dict(color="#00d4ff", width=2),
                fill="tozeroy", fillcolor="rgba(0,212,255,0.1)",
            ))
            fig.update_layout(
                title="Cumulative Net P&L (after brokerage)",
                paper_bgcolor="#111827", plot_bgcolor="#111827",
                font=dict(color="#e2e8f0"),
                xaxis=dict(gridcolor="#1e293b"),
                yaxis=dict(gridcolor="#1e293b"),
            )
            st.plotly_chart(fig, use_container_width=True)

# ──────────────────────────────────────────────────────────────────────────────
# TAB 5 — History
# ──────────────────────────────────────────────────────────────────────────────
with tabs[4]:
    st.markdown('<div class="section-title">📜 Trade History</div>', unsafe_allow_html=True)

    if not st.session_state.history:
        st.info("No closed trades yet.")
    else:
        hist_df = pd.DataFrame(st.session_state.history)
        disp    = [c for c in ["symbol","type","entry_price","cmp","exit_price",
                                "qty","invested","brokerage","entry_time","exit_time",
                                "pnl","setup_type","status","sector"]
                   if c in hist_df.columns]
        rename  = {"entry_price":"Entry(₹)","cmp":"CMP(₹)","exit_price":"Exit(₹)",
                   "pnl":"Net P&L(₹)","brokerage":"Brokerage(₹)","setup_type":"Setup"}
        st.dataframe(hist_df[disp].rename(columns=rename), use_container_width=True)

        wins      = len([t for t in st.session_state.history if t.get("pnl", 0) >= 0])
        losses    = len(st.session_state.history) - wins
        total_pnl = sum(t.get("pnl", 0) for t in st.session_state.history)
        total_brk = sum(t.get("brokerage", 0) for t in st.session_state.history)
        win_rate  = (wins / len(st.session_state.history) * 100) if st.session_state.history else 0

        hc1, hc2, hc3, hc4, hc5, hc6 = st.columns(6)
        hc1.metric("Total Trades",  len(st.session_state.history))
        hc2.metric("Winners",       wins)
        hc3.metric("Losers",        losses)
        hc4.metric("Win Rate",      f"{win_rate:.1f}%")
        hc5.metric("Net P&L",       f"₹{total_pnl:,.2f}")
        hc6.metric("Total Charges", f"₹{total_brk:,.2f}")

        if "type" in hist_df.columns:
            type_pnl = hist_df.groupby("type")["pnl"].sum().reset_index()
            fig2 = px.bar(type_pnl, x="type", y="pnl", color="type",
                          color_discrete_map={"BUY": "#00ff88", "SELL": "#ff3366"},
                          title="Net P&L by Trade Type")
            fig2.update_layout(paper_bgcolor="#111827", plot_bgcolor="#111827",
                               font=dict(color="#e2e8f0"))
            st.plotly_chart(fig2, use_container_width=True)

        if "sector" in hist_df.columns:
            sector_pnl = hist_df.groupby("sector")["pnl"].sum().reset_index().sort_values("pnl", ascending=False)
            fig3 = px.bar(sector_pnl, x="sector", y="pnl", color="pnl",
                          color_continuous_scale=["#ff3366","#ffd700","#00ff88"],
                          title="P&L by Sector")
            fig3.update_layout(paper_bgcolor="#111827", plot_bgcolor="#111827",
                               font=dict(color="#e2e8f0"))
            st.plotly_chart(fig3, use_container_width=True)

        st.download_button(
            "📥 Download History CSV",
            data=hist_df.to_csv(index=False),
            file_name=f"equity_trade_history_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )
        if st.button("🗑️ Clear History"):
            st.session_state.history = []
            st.rerun()

# ──────────────────────────────────────────────────────────────────────────────
# TAB 6 — Trade Journal & Analytics
# ──────────────────────────────────────────────────────────────────────────────
with tabs[5]:
    st.markdown('<div class="section-title">📓 Trade Journal & Setup Analytics</div>', unsafe_allow_html=True)

    journal = st.session_state.trade_journal
    if not journal:
        st.info("No journal entries yet. Close some trades to see analytics.")
    else:
        jdf = pd.DataFrame(journal)

        # Setup type performance
        if "setup_type" in jdf.columns and "pnl" in jdf.columns:
            st.markdown("#### 📊 P&L by Setup Type")
            setup_agg = jdf.groupby("setup_type").agg(
                total_pnl=("pnl", "sum"),
                trades=("pnl", "count"),
                win_rate=("win", "mean"),
            ).reset_index()
            setup_agg["win_rate"] = (setup_agg["win_rate"] * 100).round(1)
            st.dataframe(setup_agg.rename(columns={
                "setup_type":"Setup","total_pnl":"Total P&L","trades":"Trades","win_rate":"Win Rate %"
            }), use_container_width=True, hide_index=True)

            fig_setup = px.bar(setup_agg, x="setup_type", y="total_pnl",
                               color="win_rate", color_continuous_scale=["#ff3366","#ffd700","#00ff88"],
                               title="P&L by Trade Setup Type",
                               labels={"total_pnl":"Net P&L (₹)","setup_type":"Setup"})
            fig_setup.update_layout(paper_bgcolor="#111827", plot_bgcolor="#111827",
                                    font=dict(color="#e2e8f0"))
            st.plotly_chart(fig_setup, use_container_width=True)

        # Per-stock win rate
        st.markdown("#### 🏆 Per-Stock Win Rate")
        wr_data = st.session_state.win_rate_by_stock
        if wr_data:
            wr_rows = []
            for sym, data in wr_data.items():
                total = data["total"]
                wins  = data["wins"]
                wr_rows.append({
                    "Symbol":    sym.replace(".NS",""),
                    "Trades":    total,
                    "Wins":      wins,
                    "Win Rate":  f"{wins/total*100:.1f}%" if total > 0 else "N/A",
                    "Reliable":  "✅" if total >= 5 and wins/total > 0.55 else ("⚠️" if total < 5 else "❌"),
                })
            wr_df = pd.DataFrame(wr_rows).sort_values("Wins", ascending=False)
            st.dataframe(wr_df, use_container_width=True, hide_index=True)
            st.markdown(
                '<div class="scan-info">✅ = Win rate > 55% with 5+ trades — reliable signal source. '
                '❌ = Win rate < 55% — consider avoiding. ⚠️ = Less than 5 trades — insufficient data.</div>',
                unsafe_allow_html=True,
            )
        else:
            st.info("No per-stock data yet.")

        # Sector performance
        if "sector" in jdf.columns:
            st.markdown("#### 🏭 Win Rate by Sector")
            sect_agg = jdf.groupby("sector").agg(
                total_pnl=("pnl", "sum"),
                trades=("pnl", "count"),
                win_rate=("win", "mean"),
            ).reset_index()
            sect_agg["win_rate"] = (sect_agg["win_rate"] * 100).round(1)
            st.dataframe(sect_agg.rename(columns={
                "sector":"Sector","total_pnl":"P&L","trades":"Trades","win_rate":"Win%"
            }), use_container_width=True, hide_index=True)

        # Kelly win rate updater
        if len(journal) > 0:
            actual_wr = sum(1 for j in journal if j["win"]) / len(journal)
            st.session_state.kelly_win_rate = actual_wr
            st.markdown(
                f'<div class="kelly-info">🧮 Current Kelly Win Rate: <b>{actual_wr*100:.1f}%</b> '
                f'(from {len(journal)} trades) — used for dynamic position sizing</div>',
                unsafe_allow_html=True,
            )

        if st.button("🗑️ Clear Journal"):
            st.session_state.trade_journal      = []
            st.session_state.win_rate_by_stock  = {}
            st.session_state.kelly_win_rate     = 0.55
            st.rerun()
