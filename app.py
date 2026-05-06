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
from scipy.stats import norm
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="Options Trader Pro",
    page_icon="📊",
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
.badge-call    { background: rgba(0,255,136,0.15); color: var(--green);  border: 1px solid var(--green); }
.badge-put     { background: rgba(255,51,102,0.15); color: var(--red);   border: 1px solid var(--red); }
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
        url  = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            from io import StringIO
            df      = pd.read_csv(StringIO(resp.text))
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
        df     = ticker.history(period=period, interval=interval)
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
        t     = yf.Ticker(symbol)
        price = t.fast_info.last_price
        if price is None:
            return None
        price = float(price)
        return price if np.isfinite(price) and price > 0 else None
    except Exception:
        return None


def _safe_float(series_or_val):
    """Last element of a Series (or scalar) → float; 0.0 on error."""
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
        tr  = pd.concat([
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

        return {
            "rsi":         _safe_float(rsi),
            "macd":        _safe_float(macd),
            "macd_signal": _safe_float(signal),
            "macd_hist":   _safe_float(hist),
            "bb_pct":      _safe_float(bb_pct),
            "bb_upper":    _safe_float(bb_upper),
            "bb_lower":    _safe_float(bb_lower),
            "bb_mid":      _safe_float(sma20),
            "atr":         _safe_float(atr),
            "ema9":        _safe_float(ema9),
            "ema21":       _safe_float(ema21),
            "ema50":       _safe_float(ema50),
            "ema200":      _safe_float(ema200),
            "stoch_k":     _safe_float(stoch_k),
            "stoch_d":     _safe_float(stoch_d),
            "vol_ratio":   _safe_float(vol_ratio),
            "williams_r":  _safe_float(williams_r),
            "cci":         _safe_float(cci),
            "adx":         _safe_float(adx),
            "plus_di":     _safe_float(plus_di),
            "minus_di":    _safe_float(minus_di),
            "close":       _safe_float(close),
            "sma20":       _safe_float(sma20),
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
        }
    except Exception:
        return {}


def score_signal(indicators, fundamentals):
    call_score = 0
    put_score  = 0
    reasoning  = []

    if not indicators:
        return 0, 0, ["Insufficient data"]

    # Helper: get indicator value with safe fallback
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
        call_score += 3; reasoning.append(f"RSI={rsi:.1f} — Oversold → CALL +3")
    elif rsi < 40:
        call_score += 1; reasoning.append(f"RSI={rsi:.1f} — Mildly oversold → CALL +1")
    elif rsi > 70:
        put_score  += 3; reasoning.append(f"RSI={rsi:.1f} — Overbought → PUT +3")
    elif rsi > 60:
        put_score  += 1; reasoning.append(f"RSI={rsi:.1f} — Mildly overbought → PUT +1")
    else:
        reasoning.append(f"RSI={rsi:.1f} — Neutral")

    # MACD
    if macd > macd_sig and macd_hist > 0:
        call_score += 2; reasoning.append("MACD bullish crossover → CALL +2")
    elif macd < macd_sig and macd_hist < 0:
        put_score  += 2; reasoning.append("MACD bearish crossover → PUT +2")

    # Bollinger Bands
    if bb_pct < 0.1:
        call_score += 2; reasoning.append(f"Price at lower BB ({bb_pct:.2f}) → CALL +2")
    elif bb_pct > 0.9:
        put_score  += 2; reasoning.append(f"Price at upper BB ({bb_pct:.2f}) → PUT +2")

    # Stochastic
    if stoch_k < 20 and stoch_k > stoch_d:
        call_score += 2; reasoning.append(f"Stoch K={stoch_k:.1f} oversold + crossing up → CALL +2")
    elif stoch_k > 80 and stoch_k < stoch_d:
        put_score  += 2; reasoning.append(f"Stoch K={stoch_k:.1f} overbought + crossing down → PUT +2")

    # EMA stack
    if close > 0 and ema9 > 0 and ema21 > 0 and ema50 > 0:
        if close > ema9 > ema21 > ema50:
            call_score += 3; reasoning.append("Strong bullish EMA stack (price > 9>21>50) → CALL +3")
        elif close < ema9 < ema21 < ema50:
            put_score  += 3; reasoning.append("Strong bearish EMA stack (price < 9<21<50) → PUT +3")
        elif ema200 > 0 and close > ema50 > ema200:
            call_score += 1; reasoning.append("Above EMA50 & EMA200 → CALL +1")
        elif ema200 > 0 and close < ema50 < ema200:
            put_score  += 1; reasoning.append("Below EMA50 & EMA200 → PUT +1")

    # ADX
    if adx > 25:
        if plus_di > minus_di:
            call_score += 2; reasoning.append(f"ADX={adx:.1f} strong trend, +DI>{minus_di:.1f} → CALL +2")
        else:
            put_score  += 2; reasoning.append(f"ADX={adx:.1f} strong trend, -DI>{plus_di:.1f} → PUT +2")

    # Williams %R
    if williams_r < -80:
        call_score += 1; reasoning.append(f"Williams R={williams_r:.1f} oversold → CALL +1")
    elif williams_r > -20:
        put_score  += 1; reasoning.append(f"Williams R={williams_r:.1f} overbought → PUT +1")

    # CCI
    if cci < -100:
        call_score += 1; reasoning.append(f"CCI={cci:.1f} oversold → CALL +1")
    elif cci > 100:
        put_score  += 1; reasoning.append(f"CCI={cci:.1f} overbought → PUT +1")

    # Volume confirmation
    if vol_ratio > 1.5:
        if call_score > put_score:
            call_score += 1; reasoning.append(f"High volume ({vol_ratio:.1f}x avg) confirms bullish → CALL +1")
        elif put_score > call_score:
            put_score  += 1; reasoning.append(f"High volume ({vol_ratio:.1f}x avg) confirms bearish → PUT +1")

    # Fundamentals: P/E
    pe = fundamentals.get("pe", None)
    if pe is not None:
        try:
            pe = float(pe)
            if np.isfinite(pe):
                if pe < 15:
                    call_score += 1; reasoning.append(f"Low P/E ({pe:.1f}) → fundamentally cheap → CALL +1")
                elif pe > 50:
                    put_score  += 1; reasoning.append(f"High P/E ({pe:.1f}) → overvalued → PUT +1")
        except (TypeError, ValueError):
            pass

    return call_score, put_score, reasoning


def get_recommendation(symbol):
    df           = fetch_price_data(symbol, period="3mo", interval="1d")
    indicators   = compute_indicators(df)
    fundamentals = get_fundamentals(symbol)
    call_score, put_score, reasoning = score_signal(indicators, fundamentals)

    price = indicators.get("close", 0) or 0
    if not price or not np.isfinite(float(price)) or float(price) <= 0:
        price = get_live_price(symbol) or 0
    price = float(price)

    atr = float(indicators.get("atr", 0) or 0)
    if not np.isfinite(atr) or atr <= 0:
        atr = price * 0.02

    total = max(call_score + put_score + 1, 1)

    if call_score > put_score and call_score >= 5:
        rec      = "CALL"
        strength = min(100, int((call_score / total) * 100))
        target   = round(price * (1 + 0.015 * (call_score / 5)), 2) if price > 0 else 0
        stop     = round(price - 1.5 * atr, 2)                        if price > 0 else 0
    elif put_score > call_score and put_score >= 5:
        rec      = "PUT"
        strength = min(100, int((put_score / total) * 100))
        target   = round(price * (1 - 0.015 * (put_score / 5)), 2)  if price > 0 else 0
        stop     = round(price + 1.5 * atr, 2)                        if price > 0 else 0
    else:
        rec      = "NEUTRAL"
        strength = 50
        target   = price
        stop     = price

    return {
        "symbol":         symbol,
        "price":          price,
        "recommendation": rec,
        "strength":       strength,
        "target":         target,
        "stop":           stop,
        "call_score":     call_score,
        "put_score":      put_score,
        "indicators":     indicators,
        "fundamentals":   fundamentals,
        "reasoning":      reasoning,
    }


# ─── Black-Scholes (fully hardened) ──────────────────────────────────────────

def bs_price(S, K, T, r, sigma, option_type="call"):
    """
    Black-Scholes pricing with comprehensive guards.
    Returns intrinsic value on any invalid / edge-case input.
    """
    def intrinsic():
        try:
            if option_type == "call":
                return float(max(0.0, S - K))
            return float(max(0.0, K - S))
        except Exception:
            return 0.0

    # Coerce all inputs to float first
    try:
        S     = float(S)
        K     = float(K)
        T     = float(T)
        r     = float(r)
        sigma = float(sigma)
    except (TypeError, ValueError):
        return 0.0

    # Validate — any bad value → intrinsic fallback
    if (
        not np.isfinite(S)     or S     <= 0
        or not np.isfinite(K)  or K     <= 0
        or not np.isfinite(T)  or T     <= 0
        or not np.isfinite(sigma) or sigma <= 0
        or not np.isfinite(r)
    ):
        return intrinsic()

    denom = sigma * np.sqrt(T)
    if denom <= 0 or not np.isfinite(denom):
        return intrinsic()

    try:
        d1    = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / denom
        d2    = d1 - denom
        if option_type == "call":
            price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        else:
            price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        return float(price) if np.isfinite(price) else intrinsic()
    except Exception:
        return intrinsic()


def estimate_iv(df):
    """
    Annualised historical volatility from daily returns.
    Always returns a positive finite value (clamped to 5%–500%).
    """
    try:
        if df is None or len(df) < 2:
            return 0.25
        returns = df['Close'].astype(float).pct_change().dropna()
        if returns.empty:
            return 0.25
        iv = float(returns.std() * np.sqrt(252))
        if not np.isfinite(iv) or iv <= 0:
            return 0.25
        return max(0.05, min(iv, 5.0))
    except Exception:
        return 0.25


# ─── Parallel scan ────────────────────────────────────────────────────────────

def _scan_single(symbol):
    try:
        return get_recommendation(symbol)
    except Exception:
        return None


def scan_symbols_parallel(symbols, max_workers=20):
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
    results.sort(
        key=lambda x: (0 if x["recommendation"] == "NEUTRAL" else 1, x["strength"]),
        reverse=True,
    )
    return results


# ─── Trade builder ────────────────────────────────────────────────────────────

def build_trade_from_rec(rec, capital_per_trade):
    """Build a trade dict from a recommendation. Returns None if not actionable."""
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

    opt_type = rec["recommendation"]
    strike   = round(price / 50) * 50
    if strike <= 0:
        strike = max(1, round(price))

    T     = 7 / 365.0
    df_s  = fetch_price_data(rec["symbol"], "1mo", "1d")
    sigma = estimate_iv(df_s)                       # guaranteed > 0

    premium = bs_price(price, strike, T, 0.065, sigma, opt_type.lower())
    premium = max(premium, price * 0.005)            # absolute floor

    try:
        capital_per_trade = float(capital_per_trade)
    except (TypeError, ValueError):
        capital_per_trade = 5000.0

    lots = max(1, int(capital_per_trade / max(premium * 50, 1.0)))

    return {
        "id":          f"{rec['symbol']}_{opt_type}_{int(time.time() * 1000)}",
        "symbol":      rec["symbol"],
        "type":        opt_type,
        "strike":      strike,
        "entry_price": price,
        "premium":     round(premium, 2),
        "lots":        lots,
        "qty":         lots * 50,
        "target":      rec.get("target") or price,
        "stop":        rec.get("stop")   or price,
        "entry_time":  datetime.now().strftime("%H:%M:%S"),
        "status":      "OPEN",
        "pnl":         0.0,
        "reasoning":   rec.get("reasoning", []),
        "indicators":  rec.get("indicators", {}),
        "strength":    rec.get("strength", 0),
        "call_score":  rec.get("call_score", 0),
        "put_score":   rec.get("put_score", 0),
    }


# ─── Auto Trading Engine ──────────────────────────────────────────────────────

def auto_trade_step_multi(all_symbols, capital_per_trade, max_open_positions, min_strength):
    scan_limit      = min(len(all_symbols), 300)
    symbols_to_scan = all_symbols[:scan_limit]
    recommendations = scan_symbols_parallel(symbols_to_scan, max_workers=30)

    new_trades    = []
    existing_keys = {p["symbol"] + p["type"] for p in st.session_state.portfolio}

    for rec in recommendations:
        if len(st.session_state.portfolio) + len(new_trades) >= max_open_positions:
            break
        if rec.get("recommendation") == "NEUTRAL":
            continue
        if rec.get("strength", 0) < min_strength:
            continue
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
        qty   = int(pos.get("qty", 50))
        pnl   = (price - entry) * qty if pos["type"] == "CALL" else (entry - price) * qty
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
        "         OPTIONS TRADER PRO — AUTO TRADING REPORT",
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
            f"Trade #{i}  |  {t['symbol']}  |  {t['type']}",
            f"  Strike      : ₹{t.get('strike','N/A')}",
            f"  Entry Time  : {t.get('entry_time','N/A')}",
            f"  Exit Time   : {t.get('exit_time','N/A')}",
            f"  Entry Price : ₹{t.get('entry_price',0)}",
            f"  Exit Price  : ₹{t.get('exit_price','N/A')}",
            f"  Premium     : ₹{t.get('premium',0)}",
            f"  Lots × Qty  : {t.get('lots',1)} × {t.get('qty',50)}",
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
⚡ Options Trader Pro</h1>
<p style='color:#64748b;font-size:0.85rem;margin-top:0;'>
AI-Powered Call & Put Intelligence · Full NSE Universe</p>
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
        value=100, step=10,
        help="Larger = more opportunities found but slower.",
    )

    min_signal_strength = st.slider("Min Signal Strength for Auto Trade", 50, 90, 65, 5)
    max_open_positions  = st.slider("Max Simultaneous Open Positions", 1, 30, 10, 1)

    st.markdown("---")
    st.markdown("### 📊 Portfolio Summary")
    total_hist_pnl = sum(t.get("pnl", 0) for t in st.session_state.history)
    st.metric("Open Positions", len(st.session_state.portfolio))
    st.metric("Closed Trades",  len(st.session_state.history))
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
    st.markdown('<div class="section-title">📡 Live Option Signal Scanner — Full NSE</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="scan-info">🌐 Scanning from <b>{len(effective_scan_universe)}</b> NSE symbols. '
        f'Adjust <b>Scan top N</b> in the sidebar to widen or narrow the universe.</div>',
        unsafe_allow_html=True,
    )

    col_scan, col_sym = st.columns([1, 3])
    with col_scan:
        scan_btn = st.button("🔄 Scan NSE Universe", use_container_width=True)
    with col_sym:
        single_sym = st.selectbox("Quick Analyse Single Symbol", [""] + effective_scan_universe)

    if scan_btn or (single_sym and single_sym != ""):
        symbols = [single_sym] if (single_sym and single_sym != "") else effective_scan_universe
        with st.spinner(f"Parallel-scanning {len(symbols)} symbols…"):
            prog_bar = st.progress(0)
            results  = scan_symbols_parallel(symbols, max_workers=30)
            prog_bar.progress(1.0)
        prog_bar.empty()

        calls    = [r for r in results if r["recommendation"] == "CALL"]
        puts     = [r for r in results if r["recommendation"] == "PUT"]
        neutrals = [r for r in results if r["recommendation"] == "NEUTRAL"]

        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f'<div class="metric-card"><div class="metric-value accent">{len(results)}</div><div class="metric-label">Scanned</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-card"><div class="metric-value green">{len(calls)}</div><div class="metric-label">CALL Signals</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="metric-card"><div class="metric-value red">{len(puts)}</div><div class="metric-label">PUT Signals</div></div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="metric-card"><div class="metric-value yellow">{len(neutrals)}</div><div class="metric-label">Neutral</div></div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        sorted_results = (
            [r for r in results if r["recommendation"] != "NEUTRAL"]
            + [r for r in results if r["recommendation"] == "NEUTRAL"]
        )

        for rec in sorted_results:
            icon = "🟢" if rec["recommendation"] == "CALL" else ("🔴" if rec["recommendation"] == "PUT" else "🟡")
            with st.expander(
                f"{icon} {rec['symbol']} | ₹{rec['price']:,.2f} | "
                f"{rec['recommendation']} | Strength {rec['strength']}%"
            ):
                c1, c2, c3, c4, c5 = st.columns(5)
                c1.metric("LTP",       f"₹{rec['price']:,.2f}")
                c2.metric("Signal",    rec["recommendation"])
                c3.metric("Target",    f"₹{rec['target']:,.2f}")
                c4.metric("Stop Loss", f"₹{rec['stop']:,.2f}")
                c5.metric("Strength",  f"{rec['strength']}%")

                ind = rec["indicators"]
                if ind:
                    st.markdown("**Technical Indicators**")
                    ic1, ic2, ic3, ic4, ic5, ic6 = st.columns(6)
                    ic1.metric("RSI",       f"{ind.get('rsi',0):.1f}")
                    ic2.metric("MACD",      f"{ind.get('macd',0):.3f}")
                    ic3.metric("ADX",       f"{ind.get('adx',0):.1f}")
                    ic4.metric("BB%",       f"{ind.get('bb_pct',0):.2f}")
                    ic5.metric("Stoch K",   f"{ind.get('stoch_k',0):.1f}")
                    ic6.metric("Vol Ratio", f"{ind.get('vol_ratio',1):.1f}x")

                st.markdown("**Signal Reasoning**")
                for r in rec["reasoning"]:
                    col_icon = "🟢" if "CALL" in r else ("🔴" if "PUT" in r else "⚪")
                    st.markdown(f"{col_icon} {r}")

                fund = rec["fundamentals"]
                if fund:
                    with st.expander("📊 Fundamentals"):
                        fc1, fc2, fc3, fc4 = st.columns(4)
                        fc1.metric("P/E",  f"{fund.get('pe','N/A')}")
                        fc2.metric("Beta", f"{fund.get('beta','N/A')}")
                        fc3.metric("EPS",  f"{fund.get('eps','N/A')}")
                        fc4.metric("P/B",  f"{fund.get('pb','N/A')}")

                bc1, bc2 = st.columns(2)
                with bc1:
                    if st.button("➕ Add to Watchlist", key=f"wl_{rec['symbol']}"):
                        st.session_state.watchlist.append({
                            "symbol": rec["symbol"],
                            "type":   rec["recommendation"] if rec["recommendation"] != "NEUTRAL" else "CALL",
                            "strike": round(rec["price"] / 50) * 50,
                            "target": rec["target"],
                            "stop":   rec["stop"],
                            "added":  datetime.now().strftime("%H:%M:%S"),
                        })
                        st.success("Added to watchlist!")
                with bc2:
                    if rec["recommendation"] != "NEUTRAL":
                        if st.button(f"🚀 Buy {rec['recommendation']}", key=f"buy_{rec['symbol']}"):
                            try:
                                trade = build_trade_from_rec(rec, capital_per_trade)
                            except Exception:
                                trade = None
                            if trade:
                                st.session_state.portfolio.append(trade)
                                st.success(f"✅ Bought {rec['recommendation']} on {rec['symbol']}!")
                            else:
                                st.error("Could not build trade — check price/volatility data.")
    else:
        st.info("👆 Click **Scan NSE Universe** or select a symbol above to begin analysis.")

# ──────────────────────────────────────────────────────────────────────────────
# TAB 2 — Auto Trading
# ──────────────────────────────────────────────────────────────────────────────
with tabs[1]:
    st.markdown('<div class="section-title">⚡ AI Multi-Option Auto Trading Engine</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="auto-trade-box">'
        f'<h2 style="color:#00d4ff;font-family:Syne;font-weight:800;">🤖 Autonomous Multi-Position Options AI</h2>'
        f'<p style="color:#94a3b8;">Scans <b>{len(effective_scan_universe)}</b> NSE symbols every cycle, '
        f'opens multiple positions simultaneously, manages live P&L, auto-exits on target/stop.</p></div>',
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
                f'Max <b>{int(auto_max_pos)}</b> positions · Min strength <b>{int(auto_min_str)}%</b></div>',
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
                with st.spinner(f"🔭 Scanning {len(effective_scan_universe)} NSE symbols…"):
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
                entry = float(pos.get("entry_price", 0))
                qty   = int(pos.get("qty", 50))

                if pos["type"] == "CALL":
                    pos["pnl"] = round((price - entry) * qty, 2)
                    hit_exit   = price >= pos.get("target", price + 1) or price <= pos.get("stop", 0)
                else:
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

            st.markdown("### 📊 Live Positions")
            if st.session_state.portfolio:
                df_pos = pd.DataFrame(st.session_state.portfolio)
                disp   = [c for c in ["symbol","type","strike","entry_price","lots","qty",
                                       "target","stop","pnl","strength"] if c in df_pos.columns]
                st.dataframe(df_pos[disp], use_container_width=True)
            else:
                st.info("No open positions. Scanning for signals on next cycle…")

            st.markdown("### 📋 Auto Trade Log (most recent)")
            for t in reversed(st.session_state.auto_trade_log[-20:]):
                badge = "🟢 CALL" if t["type"] == "CALL" else "🔴 PUT"
                st.markdown(
                    f"- {badge} **{t['symbol']}** | Strike ₹{t['strike']} | "
                    f"Strength {t['strength']}% | Entry ₹{t['entry_price']:.2f}"
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
            file_name=f"options_trade_report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain",
            use_container_width=True,
        )

# ──────────────────────────────────────────────────────────────────────────────
# TAB 3 — Watchlist
# ──────────────────────────────────────────────────────────────────────────────
with tabs[2]:
    st.markdown('<div class="section-title">👁️ Options Watchlist</div>', unsafe_allow_html=True)

    with st.expander("➕ Add Option to Watchlist"):
        wc1, wc2, wc3, wc4, wc5 = st.columns(5)
        w_sym    = wc1.selectbox("Symbol",       effective_scan_universe[:500], key="w_sym")
        w_type   = wc2.selectbox("Type",         ["CALL", "PUT"], key="w_type")
        w_strike = wc3.number_input("Strike (₹)",    min_value=0.0, value=0.0, key="w_strike")
        w_target = wc4.number_input("Target (₹)",    min_value=0.0, value=0.0, key="w_target")
        w_stop   = wc5.number_input("Stop Loss (₹)", min_value=0.0, value=0.0, key="w_stop")
        if st.button("Add to Watchlist", use_container_width=True):
            st.session_state.watchlist.append({
                "symbol": w_sym, "type": w_type, "strike": w_strike,
                "target": w_target, "stop": w_stop,
                "added":  datetime.now().strftime("%H:%M:%S"),
            })
            st.success("Added!")

    if not st.session_state.watchlist:
        st.info("Your watchlist is empty.")
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
                df_tmp  = fetch_price_data(w["symbol"], "1mo", "1d")
                sigma   = estimate_iv(df_tmp)
                strike  = float(w["strike"]) if w["strike"] else round(price / 50) * 50
                if not strike or strike <= 0:
                    strike = max(1.0, round(price))
                premium = bs_price(price, strike, 7 / 365, 0.065, sigma, w["type"].lower())
                premium = max(premium, price * 0.005)
                st.session_state.portfolio.append({
                    "id":          f"{w['symbol']}_{w['type']}_{int(time.time())}",
                    "symbol":      w["symbol"], "type": w["type"],
                    "strike":      strike, "entry_price": price,
                    "premium":     round(premium, 2), "lots": 1, "qty": 50,
                    "target":      w["target"] or price * 1.02,
                    "stop":        w["stop"]   or price * 0.98,
                    "entry_time":  datetime.now().strftime("%H:%M:%S"),
                    "status":      "OPEN", "pnl": 0.0,
                    "reasoning":   [], "indicators": {}, "strength": 0,
                })
                st.success(f"Bought {w['type']} on {w['symbol']}!")
            if col7.button("❌", key=f"wdel_{i}"):
                st.session_state.watchlist.pop(i)
                st.rerun()

# ──────────────────────────────────────────────────────────────────────────────
# TAB 4 — Portfolio
# ──────────────────────────────────────────────────────────────────────────────
with tabs[3]:
    st.markdown('<div class="section-title">💼 Live Portfolio</div>', unsafe_allow_html=True)

    if not st.session_state.portfolio:
        st.info("No open positions.")
    else:
        total_live_pnl = 0.0
        for pos in st.session_state.portfolio:
            price = get_live_price(pos["symbol"]) or pos.get("entry_price", 0)
            try:
                price = float(price)
            except (TypeError, ValueError):
                price = float(pos.get("entry_price", 0))
            entry = float(pos.get("entry_price", 0))
            qty   = int(pos.get("qty", 50))
            pnl   = (price - entry) * qty if pos["type"] == "CALL" else (entry - price) * qty
            pos["pnl"]     = round(pnl, 2)
            total_live_pnl += pnl

        pnl_color = "green" if total_live_pnl >= 0 else "red"
        st.markdown(f'<h3 class="{pnl_color}">Total Live P&L: ₹{total_live_pnl:,.2f}</h3>', unsafe_allow_html=True)

        for pos in st.session_state.portfolio:
            badge = "🟢 CALL" if pos["type"] == "CALL" else "🔴 PUT"
            with st.expander(
                f"{badge} {pos['symbol']} | Strike ₹{pos['strike']} | P&L: ₹{pos.get('pnl',0):,.2f}"
            ):
                ltp = get_live_price(pos["symbol"]) or pos.get("entry_price", 0)
                pc1, pc2, pc3, pc4, pc5 = st.columns(5)
                pc1.metric("Entry",  f"₹{pos.get('entry_price',0):.2f}")
                pc2.metric("LTP",    f"₹{float(ltp):.2f}")
                pc3.metric("Target", f"₹{pos.get('target',0):.2f}")
                pc4.metric("Stop",   f"₹{pos.get('stop',0):.2f}")
                pc5.metric("P&L",    f"₹{pos.get('pnl',0):,.2f}")

                if st.button("Square Off", key=f"sq_{pos['id']}"):
                    exit_price = float(get_live_price(pos["symbol"]) or pos.get("entry_price", 0))
                    entry      = float(pos.get("entry_price", 0))
                    qty        = int(pos.get("qty", 50))
                    final_pnl  = (exit_price - entry) * qty if pos["type"] == "CALL" else (entry - exit_price) * qty
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
        disp    = [c for c in ["symbol","type","strike","entry_price","exit_price",
                                "lots","qty","entry_time","exit_time","pnl","status"]
                   if c in hist_df.columns]
        st.dataframe(hist_df[disp], use_container_width=True)

        wins      = len([t for t in st.session_state.history if t.get("pnl", 0) >= 0])
        losses    = len(st.session_state.history) - wins
        total_pnl = sum(t.get("pnl", 0) for t in st.session_state.history)

        hc1, hc2, hc3, hc4 = st.columns(4)
        hc1.metric("Total Trades", len(st.session_state.history))
        hc2.metric("Winners",      wins)
        hc3.metric("Losers",       losses)
        hc4.metric("Net P&L",      f"₹{total_pnl:,.2f}")

        st.download_button(
            "📥 Download History CSV",
            data=hist_df.to_csv(index=False),
            file_name=f"trade_history_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )

        if st.button("🗑️ Clear History"):
            st.session_state.history = []
            st.rerun()
