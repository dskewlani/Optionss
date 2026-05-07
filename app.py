import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import concurrent.futures
import threading
import json
import os
import requests
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="Equity Trader Pro",
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
.badge-buy     { background: rgba(0,255,136,0.15); color: var(--green);  border: 1px solid var(--green); }
.badge-sell    { background: rgba(255,51,102,0.15); color: var(--red);   border: 1px solid var(--red); }
.badge-neutral { background: rgba(255,215,0,0.15);  color: var(--yellow); border: 1px solid var(--yellow); }

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
</style>
""", unsafe_allow_html=True)

# ─── Session State Init ───────────────────────────────────────────────────────
def init_state():
    defaults = {
        "portfolio":      [],
        "history":        [],
        "watchlist":      [],
        "auto_trading":   False,
        "auto_trade_end": None,
        "auto_trade_log": [],
        "auto_pnl":       0.0,
        "capital":        100000.0,
        "used_capital":   0.0,
        "nse_symbols":    [],
        "nse_fetched_at": None,
        "_auto_duration": 15,
        "_auto_capital":  5000.0,
        "_auto_max_pos":  10,
        "_auto_min_str":  65,
        "last_scan_results": [],
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
    "^NSEI","^NSEBANK","^BSESN",
]


@st.cache_data(ttl=3600)
def fetch_nse_all_symbols():
    """Fetch complete NSE equity symbol list; falls back to hardcoded list."""
    try:
        headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.nseindia.com"}
        url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            from io import StringIO
            df = pd.read_csv(StringIO(resp.text))
            symbols = [s.strip() + ".NS" for s in df["SYMBOL"].dropna().tolist()]
            symbols += ["^NSEI", "^NSEBANK", "^BSESN"]
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
    """Return last price as float, or None on any failure."""
    try:
        t = yf.Ticker(symbol)
        price = t.fast_info.last_price
        if price is None:
            return None
        price = float(price)
        return price if np.isfinite(price) and price > 0 else None
    except Exception:
        return None


def _safe_float(series_or_val):
    try:
        val = float(series_or_val.iloc[-1]) if isinstance(series_or_val, pd.Series) else float(series_or_val)
        return val if np.isfinite(val) else 0.0
    except Exception:
        return 0.0


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

        # Previous close for day change %
        prev_close = close.shift(1)
        day_change_pct = ((close - prev_close) / prev_close.replace(0, np.nan)) * 100

        return {
            "rsi":            _safe_float(rsi),
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
        }
    except Exception:
        return {}


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
        }
    except Exception:
        return {}


def score_signal(indicators, fundamentals):
    """
    Scores BUY / SELL signals for EQUITY trading.
    Returns (buy_score, sell_score, reasoning_list, composite_strength 0-100).
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

    # RSI
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

    # MACD
    if macd > macd_sig and macd_hist > 0:
        buy_score  += 2; reasoning.append("MACD bullish crossover → BUY +2")
    elif macd < macd_sig and macd_hist < 0:
        sell_score += 2; reasoning.append("MACD bearish crossover → SELL +2")

    # Bollinger Bands
    if bb_pct < 0.1:
        buy_score  += 2; reasoning.append(f"Price at lower BB ({bb_pct:.2f}) — oversold band → BUY +2")
    elif bb_pct > 0.9:
        sell_score += 2; reasoning.append(f"Price at upper BB ({bb_pct:.2f}) — overbought band → SELL +2")

    # Stochastic
    if stoch_k < 20 and stoch_k > stoch_d:
        buy_score  += 2; reasoning.append(f"Stoch K={stoch_k:.1f} oversold + crossing up → BUY +2")
    elif stoch_k > 80 and stoch_k < stoch_d:
        sell_score += 2; reasoning.append(f"Stoch K={stoch_k:.1f} overbought + crossing down → SELL +2")

    # EMA stack
    if close > 0 and ema9 > 0 and ema21 > 0 and ema50 > 0:
        if close > ema9 > ema21 > ema50:
            buy_score  += 3; reasoning.append("Strong bullish EMA stack (price > 9>21>50) → BUY +3")
        elif close < ema9 < ema21 < ema50:
            sell_score += 3; reasoning.append("Strong bearish EMA stack (price < 9<21<50) → SELL +3")
        elif ema200 > 0 and close > ema50 > ema200:
            buy_score  += 1; reasoning.append("Above EMA50 & EMA200 (long-term uptrend) → BUY +1")
        elif ema200 > 0 and close < ema50 < ema200:
            sell_score += 1; reasoning.append("Below EMA50 & EMA200 (long-term downtrend) → SELL +1")

    # ADX — trend strength
    if adx > 25:
        if plus_di > minus_di:
            buy_score  += 2; reasoning.append(f"ADX={adx:.1f} strong uptrend, +DI>{minus_di:.1f} → BUY +2")
        else:
            sell_score += 2; reasoning.append(f"ADX={adx:.1f} strong downtrend, -DI>{plus_di:.1f} → SELL +2")

    # Williams %R
    if williams_r < -80:
        buy_score  += 1; reasoning.append(f"Williams R={williams_r:.1f} oversold → BUY +1")
    elif williams_r > -20:
        sell_score += 1; reasoning.append(f"Williams R={williams_r:.1f} overbought → SELL +1")

    # CCI
    if cci < -100:
        buy_score  += 1; reasoning.append(f"CCI={cci:.1f} oversold → BUY +1")
    elif cci > 100:
        sell_score += 1; reasoning.append(f"CCI={cci:.1f} overbought → SELL +1")

    # Volume confirmation
    if vol_ratio > 1.5:
        if buy_score > sell_score:
            buy_score  += 1; reasoning.append(f"High volume ({vol_ratio:.1f}x avg) confirms bullish move → BUY +1")
        elif sell_score > buy_score:
            sell_score += 1; reasoning.append(f"High volume ({vol_ratio:.1f}x avg) confirms bearish move → SELL +1")

    # Fundamentals: P/E
    pe = fundamentals.get("pe", None)
    if pe is not None:
        try:
            pe = float(pe)
            if np.isfinite(pe) and pe > 0:
                if pe < 15:
                    buy_score  += 1; reasoning.append(f"Low P/E ({pe:.1f}) — fundamentally cheap → BUY +1")
                elif pe > 50:
                    sell_score += 1; reasoning.append(f"High P/E ({pe:.1f}) — overvalued → SELL +1")
        except (TypeError, ValueError):
            pass

    # 52-week proximity
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
                    sell_score += 1; reasoning.append(f"Near 52-week HIGH ({fw_pct*100:.0f}% from low) — caution → SELL +1")
        except (TypeError, ValueError):
            pass

    # Composite strength (0–100)
    total = max(buy_score + sell_score + 1, 1)
    if buy_score > sell_score:
        composite = min(100, int((buy_score / total) * 100))
    elif sell_score > buy_score:
        composite = min(100, int((sell_score / total) * 100))
    else:
        composite = 50

    return buy_score, sell_score, reasoning, composite


def get_recommendation(symbol):
    df           = fetch_price_data(symbol, period="3mo", interval="1d")
    indicators   = compute_indicators(df)
    fundamentals = get_fundamentals(symbol)
    buy_score, sell_score, reasoning, composite = score_signal(indicators, fundamentals)

    price = indicators.get("close", 0) or 0
    if not price or not np.isfinite(float(price)) or float(price) <= 0:
        price = get_live_price(symbol) or 0
    price = float(price)

    atr = float(indicators.get("atr", 0) or 0)
    if not np.isfinite(atr) or atr <= 0:
        atr = price * 0.02

    # Determine recommendation
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

    return {
        "symbol":         symbol,
        "cmp":            price,           # Current Market Price
        "price":          price,
        "recommendation": rec,
        "strength":       strength,
        "target":         target,
        "stop":           stop,
        "buy_score":      buy_score,
        "sell_score":     sell_score,
        "day_change":     float(day_change),
        "vol_ratio":      float(vol_ratio),
        "indicators":     indicators,
        "fundamentals":   fundamentals,
        "reasoning":      reasoning,
        "name":           fundamentals.get("name", symbol),
        "sector":         fundamentals.get("sector", "N/A"),
    }


# ─── Parallel Scan — sorted by SIGNAL STRENGTH (strongest first) ──────────────

def _scan_single(symbol):
    try:
        return get_recommendation(symbol)
    except Exception:
        return None


def scan_symbols_parallel(symbols, max_workers=30):
    """
    Scans ALL provided symbols in parallel.
    Returns results sorted by:
      1. Non-NEUTRAL first
      2. Signal strength DESCENDING (strongest signal at top)
    """
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {executor.submit(_scan_single, sym): sym for sym in symbols}
        for future in concurrent.futures.as_completed(future_map):
            try:
                res = future.result()
                if res and res.get("price") and res["price"] > 0:
                    results.append(res)
            except Exception:
                continue

    # ── Sort: strongest actionable signal first ──────────────────────────────
    def sort_key(x):
        is_neutral = 1 if x["recommendation"] == "NEUTRAL" else 0
        strength   = -x.get("strength", 0)   # descending
        return (is_neutral, strength)

    results.sort(key=sort_key)
    return results


# ─── Equity Trade Builder ─────────────────────────────────────────────────────

def build_trade_from_rec(rec, capital_per_trade):
    """Build an equity trade dict from a recommendation."""
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

    trade_type = rec["recommendation"]   # "BUY" or "SELL"

    try:
        capital_per_trade = float(capital_per_trade)
    except (TypeError, ValueError):
        capital_per_trade = 5000.0

    qty = max(1, int(capital_per_trade / price))

    return {
        "id":          f"{rec['symbol']}_{trade_type}_{int(time.time() * 1000)}",
        "symbol":      rec["symbol"],
        "name":        rec.get("name", rec["symbol"]),
        "type":        trade_type,
        "cmp":         price,
        "entry_price": price,
        "qty":         qty,
        "invested":    round(qty * price, 2),
        "target":      rec.get("target") or price,
        "stop":        rec.get("stop")   or price,
        "entry_time":  datetime.now().strftime("%H:%M:%S"),
        "status":      "OPEN",
        "pnl":         0.0,
        "reasoning":   rec.get("reasoning", []),
        "indicators":  rec.get("indicators", {}),
        "strength":    rec.get("strength", 0),
        "buy_score":   rec.get("buy_score", 0),
        "sell_score":  rec.get("sell_score", 0),
        "sector":      rec.get("sector", "N/A"),
        "day_change":  rec.get("day_change", 0),
    }


# ─── Auto Trading Engine ──────────────────────────────────────────────────────

def auto_trade_step_multi(all_symbols, capital_per_trade, max_open_positions, min_strength):
    """
    Scans all symbols in parallel, selects strongest-signal stocks,
    opens equity positions (BUY / SELL short).
    """
    scan_limit      = min(len(all_symbols), 500)
    symbols_to_scan = all_symbols[:scan_limit]

    # Full parallel scan — already sorted by strength descending
    recommendations = scan_symbols_parallel(symbols_to_scan, max_workers=30)

    new_trades    = []
    existing_keys = {p["symbol"] + p["type"] for p in st.session_state.portfolio}

    for rec in recommendations:
        if len(st.session_state.portfolio) + len(new_trades) >= max_open_positions:
            break
        if rec.get("recommendation") == "NEUTRAL":
            continue
        if rec.get("strength", 0) < min_strength:
            break   # list is sorted; once below threshold, stop
        key = rec["symbol"] + rec["recommendation"]
        if key in existing_keys:
            continue
        try:
            trade = build_trade_from_rec(rec, capital_per_trade)
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
        pnl   = (price - entry) * qty if pos["type"] == "BUY" else (entry - price) * qty

        closed.append({**pos, "exit_price": price,
                       "exit_time": datetime.now().strftime("%H:%M:%S"),
                       "pnl": round(pnl, 2), "status": "CLOSED"})
        total_pnl += pnl

    st.session_state.history.extend(closed)
    st.session_state.portfolio    = []
    st.session_state.used_capital = 0.0
    return closed, total_pnl


def generate_trade_report(closed_trades, total_pnl, duration_mins):
    lines = [
        "=" * 70,
        "      EQUITY TRADER PRO — AUTO TRADING SESSION REPORT",
        "=" * 70,
        f"Generated   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Duration    : {duration_mins} minutes",
        f"Total Trades: {len(closed_trades)}",
        f"Net P&L     : ₹{total_pnl:,.2f}",
        "",
    ]
    for i, t in enumerate(closed_trades, 1):
        lines += [
            "─" * 70,
            f"Trade #{i}  |  {t.get('name', t['symbol'])}  ({t['symbol']})  |  {t['type']}",
            f"  Sector      : {t.get('sector','N/A')}",
            f"  Entry Time  : {t.get('entry_time','N/A')}",
            f"  Exit Time   : {t.get('exit_time','N/A')}",
            f"  CMP (Entry) : ₹{t.get('entry_price',0):,.2f}",
            f"  Exit Price  : ₹{t.get('exit_price','N/A')}",
            f"  Qty         : {t.get('qty',0)} shares",
            f"  Invested    : ₹{t.get('invested',0):,.2f}",
            f"  Signal Str  : {t.get('strength',0)}%",
            f"  P&L         : ₹{t.get('pnl',0):,.2f}  {'✅' if t.get('pnl',0) >= 0 else '❌'}",
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
📈 Equity Trader Pro</h1>
<p style='color:#64748b;font-size:0.85rem;margin-top:0;'>
AI-Powered BUY & SELL Intelligence · Full NSE Equity Universe · Sorted by Strongest Signal</p>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    starting_capital = st.number_input("💰 Capital (₹)", value=100000, step=10000)
    st.session_state.capital = float(starting_capital)
    capital_per_trade = st.number_input("Per-Trade Capital (₹)", value=5000, step=1000)

    st.markdown("---")
    st.markdown("### 🌐 NSE Universe")

    if st.button("🔄 Refresh NSE Symbol List", use_container_width=True):
        fetch_nse_all_symbols.clear()
        st.session_state.nse_symbols = []

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
        "Scan top N symbols (by list order)",
        min_value=20, max_value=min(500, len(all_nse)),
        value=150, step=10,
        help="Larger = more opportunities found but slower.",
    )

    min_signal_strength = st.slider("Min Signal Strength for Auto Trade", 50, 90, 65, 5)
    max_open_positions  = st.slider("Max Simultaneous Open Positions", 1, 30, 10, 1)

    st.markdown("---")
    st.markdown("### 📊 Portfolio Summary")
    total_hist_pnl = sum(t.get("pnl", 0) for t in st.session_state.history)
    open_pnl = sum(t.get("pnl", 0) for t in st.session_state.portfolio)
    st.metric("Open Positions", len(st.session_state.portfolio))
    st.metric("Closed Trades",  len(st.session_state.history))
    st.metric("Unrealised P&L", f"₹{open_pnl:,.2f}",
              delta="↑" if open_pnl >= 0 else "↓")
    st.metric("Realized P&L",   f"₹{total_hist_pnl:,.2f}",
              delta="↑" if total_hist_pnl >= 0 else "↓")

# Build effective scan universe
effective_scan_universe = list(dict.fromkeys(
    pinned_symbols + [s for s in all_nse if s not in pinned_symbols]
))[: scan_top_n + len(pinned_symbols)]

# ── Main Tabs ─────────────────────────────────────────────────────────────────
tabs = st.tabs(["🔍 Signal Scanner", "⚡ Auto Trading", "📋 Watchlist", "💼 Portfolio", "📜 History"])

# ──────────────────────────────────────────────────────────────────────────────
# TAB 1 — Signal Scanner
# ──────────────────────────────────────────────────────────────────────────────
with tabs[0]:
    st.markdown('<div class="section-title">📡 Live Equity Signal Scanner — Full NSE (Strongest First)</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="scan-info">🌐 Scanning from <b>{len(effective_scan_universe)}</b> NSE symbols. '
        f'Results are sorted by <b>signal strength (strongest at top)</b>, not alphabetically.</div>',
        unsafe_allow_html=True,
    )

    col_scan, col_sym = st.columns([1, 3])
    with col_scan:
        scan_btn = st.button("🔄 Scan NSE Universe", use_container_width=True)
    with col_sym:
        single_sym = st.selectbox("Quick Analyse Single Symbol", [""] + effective_scan_universe)

    if scan_btn or (single_sym and single_sym != ""):
        symbols = [single_sym] if (single_sym and single_sym != "") else effective_scan_universe
        with st.spinner(f"🔭 Parallel-scanning {len(symbols)} NSE symbols (strongest signals first)…"):
            prog_bar = st.progress(0)
            results  = scan_symbols_parallel(symbols, max_workers=30)
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

        # ── Summary Table ────────────────────────────────────────────────────
        st.markdown("#### 📊 Signal Summary Table (Strongest First)")
        table_data = []
        for rec in results:
            if rec["recommendation"] == "NEUTRAL":
                continue
            day_chg = rec.get("day_change", 0) or 0
            table_data.append({
                "Symbol":       rec["symbol"].replace(".NS",""),
                "CMP (₹)":     f"₹{rec['cmp']:,.2f}",
                "Signal":       rec["recommendation"],
                "Strength (%)": rec["strength"],
                "Target (₹)":  f"₹{rec['target']:,.2f}",
                "Stop (₹)":    f"₹{rec['stop']:,.2f}",
                "Day Chg (%)":  f"{day_chg:+.2f}%",
                "Vol Ratio":    f"{rec.get('vol_ratio',1):.1f}x",
                "Sector":       rec.get("sector","N/A"),
            })
        if table_data:
            df_table = pd.DataFrame(table_data)
            st.dataframe(df_table, use_container_width=True, hide_index=True)
        st.markdown("<br>", unsafe_allow_html=True)

        # ── Detailed Cards ───────────────────────────────────────────────────
        st.markdown("#### 🔎 Detailed Signal Cards")
        sorted_results = (
            [r for r in results if r["recommendation"] != "NEUTRAL"]
            + [r for r in results if r["recommendation"] == "NEUTRAL"]
        )

        for rec in sorted_results:
            icon      = "🟢" if rec["recommendation"] == "BUY" else ("🔴" if rec["recommendation"] == "SELL" else "🟡")
            day_chg   = rec.get("day_change", 0) or 0
            chg_icon  = "▲" if day_chg >= 0 else "▼"
            chg_color = "green" if day_chg >= 0 else "red"

            with st.expander(
                f"{icon} {rec['symbol'].replace('.NS','')} | "
                f"CMP ₹{rec['cmp']:,.2f} ({chg_icon}{abs(day_chg):.2f}%) | "
                f"{rec['recommendation']} | Strength {rec['strength']}%"
            ):
                # CMP + core metrics
                c1, c2, c3, c4, c5, c6 = st.columns(6)
                c1.metric("CMP",       f"₹{rec['cmp']:,.2f}")
                c2.metric("Signal",    rec["recommendation"])
                c3.metric("Strength",  f"{rec['strength']}%")
                c4.metric("Target",    f"₹{rec['target']:,.2f}")
                c5.metric("Stop Loss", f"₹{rec['stop']:,.2f}")
                c6.metric("Day Chg",   f"{day_chg:+.2f}%",
                          delta=f"{day_chg:+.2f}%")

                # Strength bar
                bar_color = "#00ff88" if rec["recommendation"] == "BUY" else "#ff3366"
                st.markdown(
                    f'<div class="strength-bar-wrap"><div class="strength-bar-fill" '
                    f'style="width:{rec["strength"]}%;background:{bar_color};"></div></div>',
                    unsafe_allow_html=True,
                )
                st.markdown("<br>", unsafe_allow_html=True)

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
                                trade = build_trade_from_rec(rec, capital_per_trade)
                            except Exception:
                                trade = None
                            if trade:
                                st.session_state.portfolio.append(trade)
                                st.success(f"✅ {rec['recommendation']} executed on {rec['symbol']}!")
                            else:
                                st.error("Could not build trade — check price data.")
    else:
        st.info("👆 Click **Scan NSE Universe** or select a symbol above to begin analysis.")

# ──────────────────────────────────────────────────────────────────────────────
# TAB 2 — Auto Trading
# ──────────────────────────────────────────────────────────────────────────────
with tabs[1]:
    st.markdown('<div class="section-title">⚡ AI Equity Auto Trading Engine — Strongest Signals Only</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="auto-trade-box">'
        f'<h2 style="color:#00d4ff;font-family:Syne;font-weight:800;">🤖 Autonomous Multi-Position Equity AI</h2>'
        f'<p style="color:#94a3b8;">Scans <b>{len(effective_scan_universe)}</b> NSE stocks every cycle · '
        f'Selects only the <b>strongest signal stocks</b> (sorted by strength, not alphabetical) · '
        f'Opens BUY/SELL positions · Manages live P&L · Auto-exits on target/stop.</p></div>',
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    if not st.session_state.auto_trading:
        _, col_t2, _ = st.columns([1, 2, 1])
        with col_t2:
            auto_mins    = st.number_input("⏱️ Duration (minutes)", min_value=1, max_value=480, value=15, step=5)
            auto_capital = st.number_input("💰 Capital per trade (₹)", min_value=1000, value=5000, step=1000)
            auto_max_pos = st.number_input("📊 Max simultaneous positions", min_value=1, max_value=50,
                                           value=max_open_positions, step=1)
            auto_min_str = st.number_input("🎯 Min signal strength (%)", min_value=50, max_value=95,
                                           value=min_signal_strength, step=5)
            st.markdown(
                f'<div class="scan-info">🔭 Will scan <b>{len(effective_scan_universe)}</b> symbols · '
                f'Picks <b>top {int(auto_max_pos)} strongest signals ≥ {int(auto_min_str)}%</b></div>',
                unsafe_allow_html=True,
            )
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🚀 START AUTO TRADING", use_container_width=True):
                st.session_state.auto_trading    = True
                st.session_state.auto_trade_end  = datetime.now() + timedelta(minutes=int(auto_mins))
                st.session_state.auto_trade_log  = []
                st.session_state.auto_pnl        = 0.0
                st.session_state._auto_duration  = int(auto_mins)
                st.session_state._auto_capital   = float(auto_capital)
                st.session_state._auto_max_pos   = int(auto_max_pos)
                st.session_state._auto_min_str   = int(auto_min_str)
                st.rerun()
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

            if len(st.session_state.portfolio) < _max_pos:
                with st.spinner(f"🔭 Scanning {len(effective_scan_universe)} NSE stocks for strongest signals…"):
                    try:
                        new_trades = auto_trade_step_multi(
                            effective_scan_universe,
                            capital_per_trade=_capital,
                            max_open_positions=_max_pos,
                            min_strength=_min_str,
                        )
                    except Exception as e:
                        new_trades = []
                        st.warning(f"Scan error (skipping cycle): {e}")

                existing = {p["symbol"] + p["type"] for p in st.session_state.portfolio}
                for t in new_trades:
                    key = t["symbol"] + t["type"]
                    if key not in existing:
                        st.session_state.portfolio.append(t)
                        st.session_state.auto_trade_log.append(t)
                        existing.add(key)

            # Update P&L and check exits
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

                if pos["type"] == "BUY":
                    pos["pnl"] = round((price - entry) * qty, 2)
                    hit_exit   = price >= pos.get("target", price + 1) or price <= pos.get("stop", 0)
                else:  # SELL short
                    pos["pnl"] = round((entry - price) * qty, 2)
                    hit_exit   = price <= pos.get("target", 0) or price >= pos.get("stop", price + 1)

                if hit_exit:
                    st.session_state.history.append({
                        **pos, "exit_price": price,
                        "exit_time": datetime.now().strftime("%H:%M:%S"),
                        "status": "CLOSED",
                    })
                else:
                    still_open.append(pos)
            st.session_state.portfolio = still_open

            # Live positions table
            st.markdown("### 📊 Live Positions (with CMP)")
            if st.session_state.portfolio:
                df_pos = pd.DataFrame(st.session_state.portfolio)
                # ensure CMP column
                if "cmp" not in df_pos.columns:
                    df_pos["cmp"] = df_pos["entry_price"]
                disp = [c for c in ["symbol","type","cmp","entry_price","qty","invested",
                                     "target","stop","pnl","strength","sector"] if c in df_pos.columns]
                rename_map = {"cmp": "CMP (₹)", "entry_price": "Entry (₹)", "pnl": "P&L (₹)",
                              "strength": "Signal %", "sector": "Sector"}
                st.dataframe(df_pos[disp].rename(columns=rename_map), use_container_width=True)
            else:
                st.info("No open positions. Scanning for signals on next cycle…")

            st.markdown("### 📋 Auto Trade Log (most recent — sorted by signal strength)")
            for t in reversed(st.session_state.auto_trade_log[-20:]):
                badge = "🟢 BUY" if t["type"] == "BUY" else "🔴 SELL"
                st.markdown(
                    f"- {badge} **{t['symbol'].replace('.NS','')}** | "
                    f"CMP ₹{t['cmp']:,.2f} | "
                    f"Strength **{t['strength']}%** | "
                    f"Qty {t['qty']} @ ₹{t['entry_price']:.2f}"
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
        st.markdown(f'<h3 class="{color}">Session ended. Net P&L: ₹{pnl:,.2f}</h3>', unsafe_allow_html=True)
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
            cmp = get_live_price(w["symbol"]) or 0
            badge = "🟢" if w["type"] == "BUY" else "🔴"
            col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 1, 1, 1, 1, 1, 1])
            col1.markdown(f"**{badge} {w['symbol'].replace('.NS','')}**")
            col2.markdown(f'<span class="cmp-badge">₹{cmp:,.2f}</span>', unsafe_allow_html=True)
            col3.markdown(f"Target: ₹{w['target']:.2f}")
            col4.markdown(f"Stop: ₹{w['stop']:.2f}")
            col5.markdown(f"Qty: {w.get('qty',1)}")
            if col6.button("Execute", key=f"wbuy_{i}"):
                qty = w.get("qty", 1)
                st.session_state.portfolio.append({
                    "id":          f"{w['symbol']}_{w['type']}_{int(time.time())}",
                    "symbol":      w["symbol"],
                    "name":        w["symbol"],
                    "type":        w["type"],
                    "cmp":         cmp,
                    "entry_price": cmp,
                    "qty":         qty,
                    "invested":    round(qty * cmp, 2),
                    "target":      w["target"] or cmp * 1.02,
                    "stop":        w["stop"]   or cmp * 0.98,
                    "entry_time":  datetime.now().strftime("%H:%M:%S"),
                    "status":      "OPEN", "pnl": 0.0,
                    "reasoning":   [], "indicators": {}, "strength": 0, "sector": "N/A",
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
        total_live_pnl = 0.0
        for pos in st.session_state.portfolio:
            cmp = get_live_price(pos["symbol"]) or pos.get("entry_price", 0)
            try:
                cmp = float(cmp)
            except (TypeError, ValueError):
                cmp = float(pos.get("entry_price", 0))
            pos["cmp"] = cmp
            entry = float(pos.get("entry_price", 0))
            qty   = int(pos.get("qty", 1))
            pnl   = (cmp - entry) * qty if pos["type"] == "BUY" else (entry - cmp) * qty
            pos["pnl"]     = round(pnl, 2)
            total_live_pnl += pnl

        pnl_color = "green" if total_live_pnl >= 0 else "red"
        total_invested = sum(p.get("invested", 0) for p in st.session_state.portfolio)
        pnl_pct = (total_live_pnl / total_invested * 100) if total_invested > 0 else 0

        pc1, pc2, pc3 = st.columns(3)
        pc1.markdown(f'<div class="metric-card"><div class="metric-value accent">₹{total_invested:,.0f}</div><div class="metric-label">Total Invested</div></div>', unsafe_allow_html=True)
        pnl_col_val = "green" if total_live_pnl >= 0 else "red"
        pc2.markdown(f'<div class="metric-card"><div class="metric-value {pnl_col_val}">₹{total_live_pnl:,.2f}</div><div class="metric-label">Unrealised P&L</div></div>', unsafe_allow_html=True)
        pc3.markdown(f'<div class="metric-card"><div class="metric-value {pnl_col_val}">{pnl_pct:+.2f}%</div><div class="metric-label">Return %</div></div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        for pos in st.session_state.portfolio:
            badge = "🟢 BUY" if pos["type"] == "BUY" else "🔴 SELL"
            pnl_sign = "+" if pos.get("pnl", 0) >= 0 else ""
            with st.expander(
                f"{badge} {pos['symbol'].replace('.NS','')} | "
                f"CMP ₹{pos.get('cmp', pos.get('entry_price',0)):,.2f} | "
                f"P&L: {pnl_sign}₹{pos.get('pnl',0):,.2f}"
            ):
                ltp = pos.get("cmp", pos.get("entry_price", 0))
                pc1, pc2, pc3, pc4, pc5, pc6 = st.columns(6)
                pc1.metric("Entry Price",  f"₹{pos.get('entry_price',0):.2f}")
                pc2.metric("CMP",          f"₹{float(ltp):.2f}")
                pc3.metric("Qty",          pos.get("qty", 1))
                pc4.metric("Target",       f"₹{pos.get('target',0):.2f}")
                pc5.metric("Stop Loss",    f"₹{pos.get('stop',0):.2f}")
                pc6.metric("P&L",          f"₹{pos.get('pnl',0):,.2f}")

                if pos.get("reasoning"):
                    st.markdown("**Signal Reasoning:**")
                    for r in pos["reasoning"][:5]:
                        st.markdown(f"• {r}")

                if st.button("Square Off", key=f"sq_{pos['id']}"):
                    exit_price = float(get_live_price(pos["symbol"]) or pos.get("entry_price", 0))
                    entry      = float(pos.get("entry_price", 0))
                    qty        = int(pos.get("qty", 1))
                    final_pnl  = (exit_price - entry) * qty if pos["type"] == "BUY" else (entry - exit_price) * qty
                    st.session_state.history.append({
                        **pos, "exit_price": exit_price,
                        "exit_time": datetime.now().strftime("%H:%M:%S"),
                        "pnl": round(final_pnl, 2), "status": "CLOSED",
                    })
                    st.session_state.portfolio = [p for p in st.session_state.portfolio if p["id"] != pos["id"]]
                    st.success(f"Squared off {pos['symbol']} {pos['type']} | P&L: ₹{final_pnl:,.2f}")
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
                title="Cumulative P&L", paper_bgcolor="#111827",
                plot_bgcolor="#111827", font=dict(color="#e2e8f0"),
                xaxis=dict(gridcolor="#1e293b"), yaxis=dict(gridcolor="#1e293b"),
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
                                "qty","invested","entry_time","exit_time","pnl","status","sector"]
                   if c in hist_df.columns]
        rename  = {"entry_price":"Entry(₹)","cmp":"CMP(₹)","exit_price":"Exit(₹)","pnl":"P&L(₹)"}
        st.dataframe(hist_df[disp].rename(columns=rename), use_container_width=True)

        wins      = len([t for t in st.session_state.history if t.get("pnl", 0) >= 0])
        losses    = len(st.session_state.history) - wins
        total_pnl = sum(t.get("pnl", 0) for t in st.session_state.history)
        win_rate  = (wins / len(st.session_state.history) * 100) if st.session_state.history else 0

        hc1, hc2, hc3, hc4, hc5 = st.columns(5)
        hc1.metric("Total Trades", len(st.session_state.history))
        hc2.metric("Winners",      wins)
        hc3.metric("Losers",       losses)
        hc4.metric("Win Rate",     f"{win_rate:.1f}%")
        hc5.metric("Net P&L",      f"₹{total_pnl:,.2f}")

        # P&L by type chart
        if "type" in hist_df.columns:
            type_pnl = hist_df.groupby("type")["pnl"].sum().reset_index()
            fig2 = px.bar(type_pnl, x="type", y="pnl", color="type",
                          color_discrete_map={"BUY": "#00ff88", "SELL": "#ff3366"},
                          title="P&L by Trade Type")
            fig2.update_layout(paper_bgcolor="#111827", plot_bgcolor="#111827",
                               font=dict(color="#e2e8f0"))
            st.plotly_chart(fig2, use_container_width=True)

        st.download_button(
            "📥 Download History CSV",
            data=hist_df.to_csv(index=False),
            file_name=f"equity_trade_history_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )

        if st.button("🗑️ Clear History"):
            st.session_state.history = []
            st.rerun()
