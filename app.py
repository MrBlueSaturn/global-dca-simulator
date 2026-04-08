"""
╔══════════════════════════════════════════════════════════════════╗
║  APEX INVEST v2.1 — Pro Portfolio & DCA Simulator               ║
║  Fixed & Enhanced | Data: Yahoo Finance, World Bank             ║
╚══════════════════════════════════════════════════════════════════╝

Run: streamlit run apex_invest_v2.py
Requirements:
    pip install streamlit yfinance pandas numpy plotly requests scipy
"""

# ── Compatibility fix: must be FIRST import ──────────────────────
from __future__ import annotations
from typing import Optional, Dict, Tuple
import warnings
warnings.filterwarnings("ignore")

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import requests
from datetime import datetime, timedelta
from scipy.optimize import minimize

# ── Pandas version compatibility ─────────────────────────────────
_PD_VERSION = tuple(int(x) for x in pd.__version__.split(".")[:2])
RESAMPLE_ME = "ME" if _PD_VERSION >= (2, 2) else "M"

# ════════════════════════════════════════════════════════════════
# 0. PAGE CONFIG
# ════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="APEX Invest | Global DCA & Portfolio Platform",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ════════════════════════════════════════════════════════════════
# 1. CUSTOM CSS — Dark Luxury Theme
# ════════════════════════════════════════════════════════════════
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;600;700&family=DM+Mono:wght@400;500&display=swap');

  html, body, [class*="css"] { font-family: 'DM Sans', sans-serif !important; }
  .stApp { background: #0A0A0F; }

  section[data-testid="stSidebar"] { background: #0F0F18 !important; border-right: 1px solid #1E1E2E; }

  .apex-card {
    background: linear-gradient(135deg, #13131F 0%, #1A1A2E 100%);
    border: 1px solid #2A2A4A; border-radius: 14px;
    padding: 18px 22px; margin-bottom: 12px;
    position: relative; overflow: hidden;
  }
  .apex-card::before {
    content: ''; position: absolute; top: 0; left: 0;
    width: 4px; height: 100%;
    background: linear-gradient(180deg, #00D4FF, #7C3AED);
    border-radius: 14px 0 0 14px;
  }
  .apex-card-gold::before  { background: linear-gradient(180deg, #FFD700, #FF8C00); }
  .apex-card-green::before { background: linear-gradient(180deg, #00FF87, #00C851); }
  .apex-card-red::before   { background: linear-gradient(180deg, #FF4C4C, #C0392B); }
  .apex-card-blue::before  { background: linear-gradient(180deg, #00D4FF, #0066FF); }

  .apex-label { color: #6B7280; font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 600; margin-bottom: 6px; }
  .apex-value { color: #F9FAFB; font-size: 26px; font-weight: 700; font-family: 'DM Mono', monospace; }
  .apex-sub   { color: #9CA3AF; font-size: 12px; margin-top: 4px; }
  .green { color: #00FF87 !important; }
  .red   { color: #FF4C4C !important; }
  .gold  { color: #FFD700 !important; }
  .blue  { color: #00D4FF !important; }

  .source-badge {
    display: inline-block; background: #1E1E38; border: 1px solid #3B3B6B;
    border-radius: 6px; padding: 3px 10px; font-size: 11px; color: #9CA3AF;
    font-family: 'DM Mono', monospace; margin: 2px;
  }
  .apex-header {
    background: linear-gradient(135deg, #0D0D1A 0%, #13132B 100%);
    border: 1px solid #1E1E3E; border-radius: 16px;
    padding: 24px 32px; margin-bottom: 24px;
  }
  .apex-title    { color: #F9FAFB; font-size: 32px; font-weight: 700; margin: 0; }
  .apex-subtitle { color: #6B7280; font-size: 14px; margin-top: 6px; }

  .info-box {
    background: #0F1F3D; border: 1px solid #1E3A6E; border-radius: 10px;
    padding: 12px 16px; font-size: 13px; color: #93C5FD; margin: 8px 0;
  }
  .warn-box {
    background: #2D1B00; border: 1px solid #78350F; border-radius: 10px;
    padding: 12px 16px; font-size: 13px; color: #FCD34D; margin: 8px 0;
  }
  .stTabs [data-baseweb="tab-list"] { background: #0F0F18; border-radius: 10px; padding: 4px; }
  .stTabs [data-baseweb="tab"]      { color: #6B7280; border-radius: 8px; }
  .stTabs [aria-selected="true"]    { background: #1E1E3E !important; color: #00D4FF !important; }
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# 2. LANGUAGE TOGGLE & i18n
# ════════════════════════════════════════════════════════════════
lang = st.sidebar.radio("🌐 Language / ภาษา", ["ไทย", "English"])
L: Dict[str, Tuple[str, str]] = {
    "title":    ("🏛️ APEX Invest — แพลตฟอร์มวิเคราะห์การลงทุนระดับโลก",
                 "🏛️ APEX Invest — Global Investment Analysis Platform"),
    "subtitle": ("ระบบวิเคราะห์พอร์ตโฟลิโอและจำลอง DCA ด้วยข้อมูลจากแหล่งที่น่าเชื่อถือระดับโลก",
                 "Portfolio analysis & DCA simulation powered by globally trusted data sources"),
    "monthly":  ("💵 เงิน DCA รายเดือน (บาท)", "💵 Monthly DCA Amount (THB)"),
    "years":    ("📅 ช่วงเวลาย้อนหลัง (ปี)",   "📅 Historical Period (Years)"),
    "rfr":      ("🏦 อัตราดอกเบี้ยไร้ความเสี่ยง (%/yr)", "🏦 Risk-Free Rate (%/yr)"),
    "logscale": ("📐 แกน Y แบบ Log Scale",       "📐 Logarithmic Y-Axis"),
    "loading":  ("⏳ กำลังวิเคราะห์ข้อมูลระดับลึก...", "⏳ Fetching & analyzing market data..."),
}
T = lambda k: L[k][0] if lang == "ไทย" else L[k][1]

RISK_FREE = st.sidebar.slider(T("rfr"), 0.0, 8.0, 3.0, 0.25) / 100

# ════════════════════════════════════════════════════════════════
# 3. ASSET UNIVERSE
# ════════════════════════════════════════════════════════════════
ASSETS: Dict[str, Dict[str, str]] = {
    "🇺🇸 ตลาดสหรัฐฯ (US Market)": {
        "🇺🇸 S&P 500 (VOO)": "VOO", "🇺🇸 S&P 500 (SPY)": "SPY",
        "🇺🇸 NASDAQ 100 (QQQ)": "QQQ", "🇺🇸 Dow Jones (DIA)": "DIA",
        "🇺🇸 Russell 2000 (IWM)": "IWM", "🇺🇸 Total Market (VTI)": "VTI",
    },
    "🌍 ตลาดโลก (Global Market)": {
        "🌍 All-World (VT)": "VT", "🌏 ตลาดเกิดใหม่ (EEM)": "EEM",
        "🌎 Developed ex-US (VEA)": "VEA", "🇬🇧 UK FTSE (EWU)": "EWU",
        "🇩🇪 Germany (EWG)": "EWG",  "🇨🇳 China (MCHI)": "MCHI",
    },
    "🇯🇵 ตลาดญี่ปุ่น (Japan)": {
        "🇯🇵 Nikkei 225 (^N225)": "^N225", "🇯🇵 Toyota (7203.T)": "7203.T",
        "🇯🇵 Sony (6758.T)": "6758.T",    "🇯🇵 SoftBank (9984.T)": "9984.T",
        "🇯🇵 Hitachi (6501.T)": "6501.T",
    },
    "🇹🇭 ตลาดไทย (Thailand)": {
        "🇹🇭 SET50 (^SET50.BK)": "^SET50.BK", "🇹🇭 PTT (PTT.BK)": "PTT.BK",
        "🇹🇭 KBANK (KBANK.BK)": "KBANK.BK",   "🇹🇭 SCB (SCB.BK)": "SCB.BK",
        "🇹🇭 ADVANC (ADVANC.BK)": "ADVANC.BK","🇹🇭 AOT (AOT.BK)": "AOT.BK",
    },
    "💻 เทคโนโลยี (Tech Stocks)": {
        "🍎 Apple (AAPL)": "AAPL",   "🤖 NVIDIA (NVDA)": "NVDA",
        "🪟 Microsoft (MSFT)": "MSFT","🔍 Alphabet (GOOGL)": "GOOGL",
        "📦 Amazon (AMZN)": "AMZN",  "🔋 Tesla (TSLA)": "TSLA",
        "🤖 Meta (META)": "META",
    },
    "🏗️ Sector ETFs": {
        "💻 Tech (XLK)": "XLK",       "🏦 Finance (XLF)": "XLF",
        "⚡ Energy (XLE)": "XLE",     "🏥 Health (XLV)": "XLV",
        "🏘️ Real Estate (XLRE)": "XLRE","🛡️ Defence (XLI)": "XLI",
    },
    "🏦 ตราสารหนี้ (Fixed Income)": {
        "📊 US Long Bond (TLT)": "TLT","📊 US Agg Bond (AGG)": "AGG",
        "📊 High Yield (HYG)": "HYG", "📊 EM Bond (EMB)": "EMB",
        "📊 Short-Term (SHY)": "SHY",
    },
    "🥇 สินค้าโภคภัณฑ์ (Commodities)": {
        "🟡 Gold (GLD)": "GLD",       "⚪ Silver (SLV)": "SLV",
        "🛢️ Oil (USO)": "USO",        "🌽 Agriculture (DBA)": "DBA",
        "🏭 Copper (CPER)": "CPER",
    },
    "🏠 อสังหาริมทรัพย์ (REITs)": {
        "🏠 US REIT (VNQ)": "VNQ",    "🌏 Global REIT (VNQI)": "VNQI",
    },
    "₿ สกุลเงินดิจิทัล (Crypto)": {
        "₿ Bitcoin (BTC-USD)": "BTC-USD","Ξ Ethereum (ETH-USD)": "ETH-USD",
        "🔵 BNB (BNB-USD)": "BNB-USD",   "🔴 Solana (SOL-USD)": "SOL-USD",
    },
    "🚀 Thematic ETFs": {
        "🧬 ARK Innovation (ARKK)": "ARKK","🤖 Robotics/AI (BOTZ)": "BOTZ",
        "🌿 Clean Energy (ICLN)": "ICLN",  "🛡️ Cybersecurity (CIBR)": "CIBR",
    },
}

FLAT_ASSETS: Dict[str, str] = {}
for _cat, _items in ASSETS.items():
    FLAT_ASSETS.update(_items)

# ════════════════════════════════════════════════════════════════
# 4. DATA SOURCES REGISTRY
# ════════════════════════════════════════════════════════════════
DATA_SOURCES = {
    "Yahoo Finance": {
        "url": "https://finance.yahoo.com",
        "type": "Market Price Data",
        "coverage": "US, JP, TH, Global ETFs, Crypto",
        "lag": "~15 min delay (free tier)",
        "library": "yfinance (Python)",
    },
    "World Bank Open Data": {
        "url": "https://data.worldbank.org",
        "type": "Macroeconomic Indicators",
        "coverage": "Global — GDP, Inflation, Interest Rates",
        "lag": "Annual updates",
        "library": "REST API (requests)",
    },
    "FRED (Federal Reserve)": {
        "url": "https://fred.stlouisfed.org",
        "type": "US Monetary Data (proxied via yfinance)",
        "coverage": "US Treasury Yields (^TNX, ^IRX)",
        "lag": "~1 day",
        "library": "yfinance",
    },
}

# ════════════════════════════════════════════════════════════════
# 5. SIDEBAR — Controls
# ════════════════════════════════════════════════════════════════
st.sidebar.markdown("---")
monthly_invest = st.sidebar.number_input(T("monthly"), min_value=500, value=5000, step=500)
years = st.sidebar.slider(T("years"), 1, 25, 5)
log_scale = st.sidebar.toggle(T("logscale"), False)

st.sidebar.markdown("---")
st.sidebar.markdown("**📂 เลือกสินทรัพย์ตามหมวดหมู่**" if lang == "ไทย" else "**📂 Select Assets by Category**")

selected_assets: list[str] = []
for category, items in ASSETS.items():
    with st.sidebar.expander(category, expanded=False):
        for name, ticker in items.items():
            if st.checkbox(name, key=f"cb_{ticker}", value=(ticker in ["VOO", "BTC-USD"])):
                if name not in selected_assets:
                    selected_assets.append(name)

benchmark_ticker = "SPY"

st.sidebar.markdown("---")
st.sidebar.markdown("**⚙️ Monte Carlo Settings**")
mc_simulations = st.sidebar.select_slider(
    "จำนวน Simulations", options=[50, 100, 200, 500, 1000], value=200
)
mc_years = st.sidebar.slider("ระยะเวลาจำลอง (ปี)", 1, 30, 10)
inflation_rate = st.sidebar.slider("อัตราเงินเฟ้อ (%/yr)", 0.0, 10.0, 3.0, 0.5) / 100

# ════════════════════════════════════════════════════════════════
# 6. HEADER
# ════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="apex-header">
  <div class="apex-title">{T("title")}</div>
  <div class="apex-subtitle">{T("subtitle")}</div>
  <div style="margin-top:12px;">
    <span class="source-badge">📡 Yahoo Finance</span>
    <span class="source-badge">🌍 World Bank</span>
    <span class="source-badge">🏛️ FRED (US Treasury)</span>
    <span class="source-badge">📐 scipy Optimization</span>
    <span class="source-badge">🎲 Monte Carlo GBM</span>
    <span class="source-badge">🐍 pandas {pd.__version__}</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# 7. DATA FETCHING ENGINE  (FIX: type hints, resample, MultiIndex)
# ════════════════════════════════════════════════════════════════
end_date = datetime.today()
start_date = end_date - timedelta(days=years * 365 + 60)


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_price(ticker: str, start, end) -> Optional[pd.Series]:
    """Fetch monthly closing prices from Yahoo Finance. Robust MultiIndex handling."""
    try:
        raw = yf.download(
            ticker, start=start, end=end,
            interval="1d", progress=False, auto_adjust=True,
        )
        if raw is None or raw.empty:
            return None

        # ── Handle MultiIndex (yfinance ≥ 0.2.x returns MultiIndex columns) ──
        if isinstance(raw.columns, pd.MultiIndex):
            if "Close" in raw.columns.get_level_values(0):
                close = raw["Close"]
                # Could be DataFrame with one column or Series
                if isinstance(close, pd.DataFrame):
                    close = close.iloc[:, 0]
            else:
                return None
        else:
            if "Close" not in raw.columns:
                return None
            close = raw["Close"]

        close = close.squeeze()  # ensure Series
        close = close.dropna()
        if len(close) < 6:
            return None

        return close.resample(RESAMPLE_ME).last()
    except Exception:
        return None


@st.cache_data(ttl=86400, show_spinner=False)
def fetch_worldbank_inflation(country_code: str = "TH") -> Optional[pd.DataFrame]:
    """Fetch annual CPI inflation from World Bank Open Data API."""
    try:
        url = (
            f"https://api.worldbank.org/v2/country/{country_code}"
            f"/indicator/FP.CPI.TOTL.ZG?format=json&per_page=30&mrv=20"
        )
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if not data or len(data) < 2 or not data[1]:
            return None
        records = [
            {"year": int(d["date"]), "inflation": d["value"]}
            for d in data[1] if d["value"] is not None
        ]
        df = pd.DataFrame(records).sort_values("year")
        return df
    except Exception:
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_macro_series() -> Dict[str, pd.Series]:
    """Fetch macro indicators: US10Y, US3M, Gold."""
    out: Dict[str, pd.Series] = {}
    for label, ticker in [
        ("US 10Y Treasury (^TNX)", "^TNX"),
        ("US 3M T-Bill (^IRX)", "^IRX"),
        ("Gold Spot (GC=F)", "GC=F"),
    ]:
        try:
            raw = yf.download(ticker, period="5y", interval="1mo",
                              progress=False, auto_adjust=True)
            if raw is not None and not raw.empty:
                if isinstance(raw.columns, pd.MultiIndex):
                    s = raw["Close"].iloc[:, 0]
                else:
                    s = raw["Close"]
                out[label] = s.squeeze().dropna()
        except Exception:
            pass
    return out


# ════════════════════════════════════════════════════════════════
# 8. CALCULATION ENGINE
# ════════════════════════════════════════════════════════════════
def compute_dca(prices: pd.Series, monthly: float) -> pd.DataFrame:
    df = prices.dropna().to_frame("Price")
    df["Shares_Bought"] = monthly / df["Price"]
    df["Total_Shares"]  = df["Shares_Bought"].cumsum()
    df["Invested"]      = monthly * np.arange(1, len(df) + 1)
    df["Value"]         = df["Total_Shares"] * df["Price"]
    df["Return_Monthly"]= df["Value"].pct_change().fillna(0)
    df["Peak"]          = df["Value"].cummax()
    df["Drawdown"]      = (df["Value"] - df["Peak"]) / df["Peak"] * 100
    return df


def compute_metrics(df: pd.DataFrame, rf: float = 0.03) -> Dict:
    final_val = df["Value"].iloc[-1]
    total_inv = df["Invested"].iloc[-1]
    profit    = final_val - total_inv
    roi       = profit / total_inv * 100 if total_inv > 0 else 0
    n_months  = len(df)
    years_act = n_months / 12

    cagr = ((final_val / total_inv) ** (1 / years_act) - 1) * 100 if years_act > 0.08 and total_inv > 0 else 0

    r       = df["Return_Monthly"]
    ann_ret = r.mean() * 12
    ann_std = r.std() * np.sqrt(12)
    volatility = ann_std * 100

    sharpe   = (ann_ret - rf) / ann_std if ann_std > 0 else 0
    downside = r[r < 0].std() * np.sqrt(12)
    sortino  = (ann_ret - rf) / downside if downside > 0 else 0

    mdd      = df["Drawdown"].min()
    calmar   = ann_ret / abs(mdd / 100) if mdd != 0 else 0

    var_95   = np.percentile(r, 5) * 100
    cvar_95  = r[r <= np.percentile(r, 5)].mean() * 100
    win_rate = (r > 0).mean() * 100

    return {
        "Final Value": final_val, "Total Invested": total_inv,
        "Profit": profit, "ROI (%)": roi, "CAGR (%)": cagr,
        "Volatility (%)": volatility, "Sharpe Ratio": sharpe,
        "Sortino Ratio": sortino, "Calmar Ratio": calmar,
        "Max Drawdown (%)": mdd, "VaR 95% (monthly %)": var_95,
        "CVaR 95% (monthly %)": cvar_95, "Win Rate (%)": win_rate,
        "Months": n_months,
    }


def compute_beta_alpha(
    portfolio_returns: pd.Series,
    benchmark_returns: pd.Series,
    rf: float = 0.03,
) -> Tuple[float, float]:
    common_idx = portfolio_returns.index.intersection(benchmark_returns.index)
    if len(common_idx) < 6:
        return (np.nan, np.nan)
    p = portfolio_returns.loc[common_idx]
    b = benchmark_returns.loc[common_idx]
    cov_matrix = np.cov(p, b)
    beta  = cov_matrix[0, 1] / cov_matrix[1, 1] if cov_matrix[1, 1] != 0 else np.nan
    alpha = (p.mean() - rf / 12) - beta * (b.mean() - rf / 12)
    return beta, alpha * 12 * 100


def efficient_frontier_simulation(
    returns_df: pd.DataFrame, n: int = 1000, rf: float = 0.03
) -> pd.DataFrame:
    if returns_df.shape[1] < 2:
        return pd.DataFrame()
    cols     = returns_df.columns.tolist()
    mean_ret = returns_df.mean() * 12
    cov      = returns_df.cov() * 12
    results  = []
    for _ in range(n):
        w = np.random.dirichlet(np.ones(len(cols)))
        r = np.dot(w, mean_ret)
        v = np.sqrt(w @ cov.values @ w)
        s = (r - rf) / v if v > 0 else 0
        results.append({
            "Return": r * 100, "Volatility": v * 100, "Sharpe": s,
            **{f"W_{c}": round(wi * 100, 1) for c, wi in zip(cols, w)},
        })
    return pd.DataFrame(results)


def monte_carlo_dca(
    current_value: float, monthly: float,
    mu_monthly: float, vol_monthly: float,
    months: int, sims: int,
) -> np.ndarray:
    matrix = np.zeros((months + 1, sims))
    matrix[0] = current_value
    for t in range(1, months + 1):
        z      = np.random.standard_normal(sims)
        growth = np.exp((mu_monthly - 0.5 * vol_monthly ** 2) + vol_monthly * z)
        matrix[t] = matrix[t - 1] * growth + monthly
    return matrix


# ── Helper: hex → rgba string for fill ──────────────────────────
def hex_to_rgba(hex_color: str, alpha: float = 0.15) -> str:
    """Convert '#RRGGBB' or 'rgb(...)' to 'rgba(..., alpha)'."""
    h = hex_color.strip()
    if h.startswith("rgba"):
        return h
    if h.startswith("rgb("):
        return h.replace("rgb(", "rgba(").replace(")", f", {alpha})")
    if h.startswith("#"):
        h = h.lstrip("#")
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"rgba({r},{g},{b},{alpha})"
    return f"rgba(100,100,200,{alpha})"


# ════════════════════════════════════════════════════════════════
# 9. MAIN APPLICATION
# ════════════════════════════════════════════════════════════════
if not selected_assets:
    st.markdown("""
    <div class="info-box">
        👈 <b>กรุณาเลือกสินทรัพย์จากแถบซ้าย</b> — คลิก expander ตามหมวดหมู่แล้วติ๊กถูก<br>
        Please select assets from the left sidebar to begin analysis.
    </div>
    """, unsafe_allow_html=True)
    st.stop()

tabs = st.tabs([
    "📈 Historical DCA",
    "🧠 Advanced Metrics",
    "📊 Portfolio Analytics",
    "📅 Rolling Analysis",
    "🔮 Monte Carlo",
    "🎯 Goal Planner",
    "🌍 Macro Dashboard",
    "💾 Data & Sources",
])

with st.spinner(T("loading")):
    all_df: Dict[str, pd.DataFrame]   = {}
    all_metrics: Dict[str, Dict]      = {}
    all_returns: Dict[str, pd.Series] = {}
    failed: list[str] = []

    # Benchmark
    bm_prices  = fetch_price(benchmark_ticker, start_date, end_date)
    bm_df      = compute_dca(bm_prices, monthly_invest) if bm_prices is not None else None
    bm_returns = bm_df["Return_Monthly"] if bm_df is not None else None

    for asset_name in selected_assets:
        ticker = FLAT_ASSETS.get(asset_name)
        if not ticker:
            failed.append(asset_name); continue
        prices = fetch_price(ticker, start_date, end_date)
        if prices is None:
            failed.append(asset_name); continue
        df = compute_dca(prices, monthly_invest)
        if len(df) < 3:
            failed.append(asset_name); continue

        all_df[asset_name]   = df
        metrics              = compute_metrics(df, rf=RISK_FREE)
        if bm_returns is not None:
            beta, alpha = compute_beta_alpha(df["Return_Monthly"], bm_returns, RISK_FREE)
        else:
            beta, alpha = np.nan, np.nan
        metrics["Beta (vs SPY)"] = beta
        metrics["Alpha (Ann %)"] = alpha
        metrics["Asset"]         = asset_name
        all_metrics[asset_name]  = metrics
        all_returns[asset_name]  = df["Return_Monthly"]

if failed:
    st.markdown(
        f'<div class="warn-box">⚠️ ไม่สามารถดึงข้อมูลของ: <b>{", ".join(failed)}</b><br>'
        "อาจเกิดจาก Ticker ผิด, ข้อมูลไม่เพียงพอ, หรือ Yahoo Finance ขัดข้องชั่วคราว</div>",
        unsafe_allow_html=True,
    )

if not all_df:
    st.error("❌ ไม่สามารถโหลดข้อมูลได้เลย กรุณาลองใหม่อีกครั้ง")
    st.stop()

returns_df = pd.DataFrame(all_returns).dropna(how="all")
COLORS     = px.colors.qualitative.Bold


# ════════════════════════════════════════════════════════════════
# TAB 1: Historical DCA Performance
# ════════════════════════════════════════════════════════════════
with tabs[0]:
    st.subheader("📈 Historical DCA Portfolio Value")

    fig = go.Figure()
    for i, (name, df) in enumerate(all_df.items()):
        short = name.split("(")[0].strip()
        fig.add_trace(go.Scatter(
            x=df.index, y=df["Value"], mode="lines", name=short,
            line=dict(color=COLORS[i % len(COLORS)], width=2.5),
            hovertemplate=f"<b>{short}</b><br>%{{x|%b %Y}}<br>มูลค่า: ฿%{{y:,.0f}}<extra></extra>",
        ))

    first_df = list(all_df.values())[0]
    fig.add_trace(go.Scatter(
        x=first_df.index, y=first_df["Invested"],
        mode="lines", name="💵 เงินต้นสะสม (Cash)",
        line=dict(color="#4B5563", dash="dot", width=1.5),
        hovertemplate="<b>เงินต้น</b><br>%{x|%b %Y}<br>฿%{y:,.0f}<extra></extra>",
    ))

    fig.update_layout(
        template="plotly_dark", paper_bgcolor="#0A0A0F", plot_bgcolor="#0F0F18",
        hovermode="x unified", height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis_type="log" if log_scale else "linear",
        yaxis_title="Portfolio Value (THB)", xaxis_title="Date",
        margin=dict(l=20, r=20, t=20, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Summary Cards ────────────────────────────────────────────
    if all_metrics:
        sorted_metrics = sorted(all_metrics.values(), key=lambda x: x["ROI (%)"], reverse=True)
        best  = sorted_metrics[0]
        worst = sorted_metrics[-1]

        def card(col, label, value, sub="", variant=""):
            col.markdown(
                f'<div class="apex-card apex-card-{variant}">'
                f'<div class="apex-label">{label}</div>'
                f'<div class="apex-value">{value}</div>'
                f'<div class="apex-sub">{sub}</div></div>',
                unsafe_allow_html=True,
            )

        col1, col2, col3, col4 = st.columns(4)
        card(col1, "🏆 Best Asset",       best["Asset"].split("(")[0][:20],
             f'ROI: {best["ROI (%)"]:+.1f}%', "gold")
        card(col2, "💰 Best Final Value", f'฿{best["Final Value"]:,.0f}',
             f'Invested ฿{best["Total Invested"]:,.0f}', "green")
        card(col3, "📈 Best CAGR",        f'{best["CAGR (%)"]:+.2f}%',
             "Annualized growth rate", "blue")
        card(col4, "⚠️ Most Volatile",    worst["Asset"].split("(")[0][:20],
             f'Vol: {worst["Volatility (%)"]:,.1f}%', "red")

    # ── Drawdown Chart ───────────────────────────────────────────
    st.markdown("#### 📉 Drawdown History")
    fig_dd = go.Figure()
    for i, (name, df) in enumerate(all_df.items()):
        short = name.split("(")[0].strip()
        fig_dd.add_trace(go.Scatter(
            x=df.index, y=df["Drawdown"], mode="lines", name=short,
            fill="tozeroy", line=dict(color=COLORS[i % len(COLORS)], width=1.5),
            hovertemplate=f"<b>{short}</b><br>%{{x|%b %Y}}<br>Drawdown: %{{y:.2f}}%<extra></extra>",
        ))
    fig_dd.update_layout(
        template="plotly_dark", paper_bgcolor="#0A0A0F", plot_bgcolor="#0F0F18",
        height=300, hovermode="x unified",
        yaxis_title="Drawdown (%)", xaxis_title="Date",
        margin=dict(l=20, r=20, t=10, b=20),
    )
    st.plotly_chart(fig_dd, use_container_width=True)

    # ── NEW: Year-over-Year Return bar chart ──────────────────────
    st.markdown("#### 📊 Annual Return by Year")
    annual_fig = go.Figure()
    for i, (name, df) in enumerate(all_df.items()):
        annual = df["Return_Monthly"].resample("YE" if _PD_VERSION >= (2, 2) else "Y").apply(
            lambda x: (1 + x).prod() - 1
        ) * 100
        annual.index = annual.index.year
        short = name.split("(")[0].strip()
        annual_fig.add_trace(go.Bar(
            x=annual.index, y=annual.values, name=short,
            marker_color=COLORS[i % len(COLORS)],
            hovertemplate=f"<b>{short}</b><br>ปี: %{{x}}<br>ผลตอบแทน: %{{y:.2f}}%<extra></extra>",
        ))
    annual_fig.add_hline(y=0, line_color="#4B5563", line_width=1)
    annual_fig.update_layout(
        template="plotly_dark", paper_bgcolor="#0A0A0F", plot_bgcolor="#0F0F18",
        barmode="group", height=350,
        xaxis_title="Year", yaxis_title="Annual Return (%)",
        margin=dict(l=20, r=20, t=10, b=20),
    )
    st.plotly_chart(annual_fig, use_container_width=True)


# ════════════════════════════════════════════════════════════════
# TAB 2: Advanced Metrics Table
# ════════════════════════════════════════════════════════════════
with tabs[1]:
    st.subheader("🧠 Deep Financial Analysis Matrix")

    rows = []
    for m in all_metrics.values():
        rows.append({
            "Asset":         m["Asset"].split("(")[0].strip(),
            "Invested (฿)":  f'฿{m["Total Invested"]:,.0f}',
            "Final Value":   f'฿{m["Final Value"]:,.0f}',
            "Profit (฿)":   f'฿{m["Profit"]:,.0f}',
            "ROI":           f'{m["ROI (%)"]:+.2f}%',
            "CAGR":          f'{m["CAGR (%)"]:+.2f}%',
            "Volatility":    f'{m["Volatility (%)"]:,.2f}%',
            "Sharpe":        f'{m["Sharpe Ratio"]:.3f}',
            "Sortino":       f'{m["Sortino Ratio"]:.3f}',
            "Calmar":        f'{m["Calmar Ratio"]:.3f}',
            "Max DD":        f'{m["Max Drawdown (%)"]:,.2f}%',
            "VaR 95%":       f'{m["VaR 95% (monthly %)"]:,.2f}%',
            "CVaR 95%":      f'{m["CVaR 95% (monthly %)"]:,.2f}%',
            "Win Rate":      f'{m["Win Rate (%)"]:,.1f}%',
            "Beta":          f'{m["Beta (vs SPY)"]:.3f}' if not np.isnan(m["Beta (vs SPY)"]) else "N/A",
            "Alpha (Ann)":   f'{m["Alpha (Ann %)"]:.2f}%' if not np.isnan(m["Alpha (Ann %)"]) else "N/A",
        })

    df_table = pd.DataFrame(rows)
    st.dataframe(df_table, use_container_width=True, hide_index=True, height=350)

    st.markdown("---")

    # ── Radar / Spider chart  (FIX: use hex_to_rgba) ────────────
    if len(all_metrics) >= 2:
        st.markdown("#### 🕸️ Risk-Return Radar (Normalized)")
        metrics_for_radar = ["CAGR (%)", "Sharpe Ratio", "Sortino Ratio",
                             "Win Rate (%)", "Volatility (%)"]
        radar_labels = ["CAGR", "Sharpe", "Sortino", "Win Rate", "Volatility↓"]

        all_vals = {k: [all_metrics[n][k] for n in all_metrics] for k in metrics_for_radar}
        mn = {k: min(v) for k, v in all_vals.items()}
        mx = {k: max(v) for k, v in all_vals.items()}

        fig_radar = go.Figure()
        for i, name in enumerate(all_metrics):
            def norm(k, invert=False, _name=name):
                rng = mx[k] - mn[k]
                v   = (all_metrics[_name][k] - mn[k]) / rng if rng != 0 else 0.5
                return 1 - v if invert else v

            vals = [norm("CAGR (%)"), norm("Sharpe Ratio"), norm("Sortino Ratio"),
                    norm("Win Rate (%)"), norm("Volatility (%)", invert=True)]
            vals += [vals[0]]
            lbls  = radar_labels + [radar_labels[0]]
            short = name.split("(")[0].strip()[:18]
            color = COLORS[i % len(COLORS)]

            fig_radar.add_trace(go.Scatterpolar(
                r=vals, theta=lbls, fill="toself", name=short,
                line=dict(color=color),
                fillcolor=hex_to_rgba(color, 0.15),  # ← FIX
            ))

        fig_radar.update_layout(
            template="plotly_dark", paper_bgcolor="#0A0A0F",
            polar=dict(bgcolor="#0F0F18",
                       radialaxis=dict(visible=True, range=[0, 1])),
            height=420, showlegend=True,
            margin=dict(l=40, r=40, t=40, b=40),
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    # ── Metrics Glossary ─────────────────────────────────────────
    with st.expander("📚 อธิบายตัวชี้วัดทั้งหมด (Metrics Glossary)"):
        st.markdown("""
| Metric | ความหมาย | เกณฑ์ที่ดี |
|--------|-----------|------------|
| **CAGR** | อัตราการเติบโตเฉลี่ยทบต้นต่อปี | > 8% |
| **Sharpe** | ผลตอบแทนต่อความเสี่ยงรวม | > 1.0 ดี, > 2.0 ดีมาก |
| **Sortino** | ผลตอบแทนต่อ downside risk | > 1.5 ดี |
| **Calmar** | ผลตอบแทนต่อ Max Drawdown | > 0.5 |
| **Volatility** | ค่าเบี่ยงเบนมาตรฐานรายปี | ขึ้นกับ tolerance |
| **Max Drawdown** | ขาดทุนสูงสุดจากจุดสูงสุด | < -20% ระวัง |
| **VaR 95%** | ขาดทุนรายเดือนใน 95% ของเวลา | — |
| **CVaR 95%** | ขาดทุนเฉลี่ยใน worst 5% | ดีกว่า VaR สำหรับ tail risk |
| **Beta** | ความสัมพันธ์กับตลาด (SPY) | < 1 = ผันผวนน้อยกว่าตลาด |
| **Alpha** | ผลตอบแทนส่วนเกินเมื่อปรับ Beta | > 0% = ชนะ benchmark |
| **Win Rate** | % เดือนที่ portfolio กำไร | > 55% ดี |
        """)


# ════════════════════════════════════════════════════════════════
# TAB 3: Portfolio Analytics
# ════════════════════════════════════════════════════════════════
with tabs[2]:
    col_l, col_r = st.columns(2, gap="medium")

    with col_l:
        st.subheader("🔗 Correlation Heatmap")
        if len(returns_df.columns) >= 2:
            corr = returns_df.dropna().corr()
            short_names = [c.split("(")[0].strip()[:15] for c in corr.columns]
            fig_corr = go.Figure(go.Heatmap(
                z=corr.values, x=short_names, y=short_names,
                colorscale="RdBu", zmid=0, zmin=-1, zmax=1,
                text=np.round(corr.values, 2), texttemplate="%{text}",
                hovertemplate="<b>%{x}</b> vs <b>%{y}</b><br>Correlation: %{z:.3f}<extra></extra>",
            ))
            fig_corr.update_layout(
                template="plotly_dark", paper_bgcolor="#0A0A0F", plot_bgcolor="#0F0F18",
                height=380, margin=dict(l=20, r=20, t=20, b=20),
                xaxis=dict(tickangle=-35), font=dict(size=11),
            )
            st.plotly_chart(fig_corr, use_container_width=True)
            st.markdown('<div class="info-box">💡 ใกล้ -1 = สวนทาง (ช่วย Diversify) | ใกล้ +1 = เดียวกัน</div>',
                        unsafe_allow_html=True)
        else:
            st.info("เลือกอย่างน้อย 2 สินทรัพย์เพื่อดู Correlation")

    with col_r:
        st.subheader("🎯 Return Distribution")
        fig_dist = go.Figure()
        for i, (name, ret) in enumerate(all_returns.items()):
            short = name.split("(")[0].strip()
            fig_dist.add_trace(go.Histogram(
                x=ret * 100, name=short, opacity=0.7,
                marker_color=COLORS[i % len(COLORS)],
                nbinsx=30, histnorm="probability density",
                hovertemplate=f"<b>{short}</b><br>Return: %{{x:.1f}}%<extra></extra>",
            ))
        fig_dist.update_layout(
            template="plotly_dark", paper_bgcolor="#0A0A0F", plot_bgcolor="#0F0F18",
            barmode="overlay", height=380,
            xaxis_title="Monthly Return (%)", yaxis_title="Density",
            margin=dict(l=20, r=20, t=20, b=20),
        )
        st.plotly_chart(fig_dist, use_container_width=True)

    # ── Efficient Frontier ────────────────────────────────────────
    st.markdown("---")
    st.subheader("🏔️ Efficient Frontier (Modern Portfolio Theory)")
    if len(returns_df.columns) >= 2:
        with st.spinner("Simulating 1,000 random portfolios..."):
            ef_df = efficient_frontier_simulation(returns_df.dropna(), n=1000, rf=RISK_FREE)

        if not ef_df.empty:
            fig_ef = go.Figure()
            fig_ef.add_trace(go.Scatter(
                x=ef_df["Volatility"], y=ef_df["Return"], mode="markers",
                marker=dict(color=ef_df["Sharpe"], colorscale="Viridis", size=5,
                            opacity=0.7, colorbar=dict(title="Sharpe"), showscale=True),
                hovertemplate="Vol: %{x:.2f}%<br>Return: %{y:.2f}%<br>Sharpe: %{marker.color:.3f}<extra></extra>",
                name="Random Portfolios",
            ))
            max_s = ef_df.loc[ef_df["Sharpe"].idxmax()]
            fig_ef.add_trace(go.Scatter(
                x=[max_s["Volatility"]], y=[max_s["Return"]],
                mode="markers+text", name="⭐ Max Sharpe",
                marker=dict(color="gold", size=15, symbol="star"),
                text=["Max Sharpe"], textposition="top center",
            ))
            for i, name in enumerate(all_metrics):
                m = all_metrics[name]
                short = name.split("(")[0].strip()[:12]
                fig_ef.add_trace(go.Scatter(
                    x=[m["Volatility (%)"]], y=[m["CAGR (%)"]],
                    mode="markers+text", name=short,
                    marker=dict(color=COLORS[i % len(COLORS)], size=12, symbol="diamond"),
                    text=[short], textposition="top right",
                ))
            fig_ef.update_layout(
                template="plotly_dark", paper_bgcolor="#0A0A0F", plot_bgcolor="#0F0F18",
                height=450,
                xaxis_title="Annualized Volatility (%)", yaxis_title="Annualized Return (%)",
                margin=dict(l=20, r=20, t=20, b=20),
            )
            st.plotly_chart(fig_ef, use_container_width=True)

            w_cols = [c for c in max_s.index if c.startswith("W_")]
            if w_cols:
                st.markdown("**⭐ Max Sharpe Portfolio Weights:**")
                weight_dict = {c.replace("W_", "").split("(")[0].strip(): f"{max_s[c]:.1f}%" for c in w_cols}
                st.json(weight_dict)
    else:
        st.info("เลือกอย่างน้อย 2 สินทรัพย์เพื่อดู Efficient Frontier")


# ════════════════════════════════════════════════════════════════
# TAB 4: Rolling Analysis
# ════════════════════════════════════════════════════════════════
with tabs[3]:
    st.subheader("📅 Rolling Analysis")
    roll_window = st.selectbox("Rolling Window (months)", [6, 12, 24], index=1)

    fig_roll = make_subplots(
        rows=3, cols=1, shared_xaxes=True,
        subplot_titles=("Rolling Return (%)", "Rolling Volatility (%)", "Rolling Sharpe Ratio"),
        vertical_spacing=0.08,
    )
    for i, (name, df) in enumerate(all_df.items()):
        r     = df["Return_Monthly"]
        short = name.split("(")[0].strip()
        roll_ret    = r.rolling(roll_window).mean() * 12 * 100
        roll_vol    = r.rolling(roll_window).std() * np.sqrt(12) * 100
        roll_sharpe = (r.rolling(roll_window).mean() * 12 - RISK_FREE) / (r.rolling(roll_window).std() * np.sqrt(12))
        c = COLORS[i % len(COLORS)]
        fig_roll.add_trace(go.Scatter(x=df.index, y=roll_ret,    name=short, line=dict(color=c)), row=1, col=1)
        fig_roll.add_trace(go.Scatter(x=df.index, y=roll_vol,    name=short, line=dict(color=c), showlegend=False), row=2, col=1)
        fig_roll.add_trace(go.Scatter(x=df.index, y=roll_sharpe, name=short, line=dict(color=c), showlegend=False), row=3, col=1)

    fig_roll.add_hline(y=0, line_dash="dot", line_color="#4B5563", row=3, col=1)
    fig_roll.add_hline(y=1, line_dash="dot", line_color="#00D4FF",
                       annotation_text="Sharpe=1", row=3, col=1)
    fig_roll.update_layout(
        template="plotly_dark", paper_bgcolor="#0A0A0F", plot_bgcolor="#0F0F18",
        height=650, hovermode="x unified",
        margin=dict(l=20, r=20, t=60, b=20),
    )
    st.plotly_chart(fig_roll, use_container_width=True)

    # ── Monthly Returns Heatmap ───────────────────────────────────
    if len(all_df) >= 1:
        st.markdown("---")
        st.subheader("📅 Monthly Returns Heatmap")
        heatmap_asset = st.selectbox("เลือกสินทรัพย์สำหรับ Heatmap:", list(all_df.keys()))
        df_h  = all_df[heatmap_asset]
        df_h2 = df_h["Return_Monthly"].to_frame("ret").copy()
        df_h2["Year"]  = df_h2.index.year
        df_h2["Month"] = df_h2.index.month
        pivot = df_h2.pivot_table(index="Year", columns="Month",
                                  values="ret", aggfunc="mean") * 100
        month_labels = ["Jan","Feb","Mar","Apr","May","Jun",
                        "Jul","Aug","Sep","Oct","Nov","Dec"]
        pivot.columns = month_labels[: len(pivot.columns)]
        fig_hm = go.Figure(go.Heatmap(
            z=pivot.values, x=pivot.columns.tolist(), y=pivot.index.tolist(),
            colorscale="RdYlGn", zmid=0,
            text=np.round(pivot.values, 1), texttemplate="%{text}%",
            hovertemplate="Year: %{y}<br>Month: %{x}<br>Return: %{z:.2f}%<extra></extra>",
        ))
        fig_hm.update_layout(
            template="plotly_dark", paper_bgcolor="#0A0A0F",
            height=max(250, 35 * len(pivot)),
            xaxis_title="Month", yaxis_title="Year",
            margin=dict(l=20, r=20, t=20, b=20),
        )
        st.plotly_chart(fig_hm, use_container_width=True)


# ════════════════════════════════════════════════════════════════
# TAB 5: Monte Carlo Simulation
# ════════════════════════════════════════════════════════════════
with tabs[4]:
    st.subheader("🔮 Monte Carlo Future Projection (GBM)")
    st.markdown(
        f'<div class="info-box">📌 ใช้ <b>Geometric Brownian Motion (GBM)</b> จำลอง '
        f'<b>{mc_simulations:,} เส้นทาง</b> ใน <b>{mc_years} ปี</b> — ไม่ใช่การรับประกันผลตอบแทน</div>',
        unsafe_allow_html=True,
    )

    mc_target          = st.selectbox("เลือกสินทรัพย์สำหรับ Monte Carlo:", list(all_df.keys()))
    show_inflation_adj = st.toggle("📉 แสดง Inflation-Adjusted (Real Value)", value=True)

    mc_m    = all_metrics[mc_target]
    mu_m    = mc_m["CAGR (%)"] / 100 / 12
    vol_m   = mc_m["Volatility (%)"] / 100 / np.sqrt(12)
    last_val= mc_m["Final Value"]
    months_future = mc_years * 12

    np.random.seed(42)
    sims = monte_carlo_dca(last_val, monthly_invest, mu_m, vol_m, months_future, mc_simulations)

    if show_inflation_adj:
        inf_monthly   = (1 + inflation_rate) ** (1 / 12)
        deflator      = np.array([inf_monthly ** t for t in range(months_future + 1)])
        sims_display  = sims / deflator[:, None]
    else:
        sims_display  = sims

    pct_05 = np.percentile(sims_display, 5,  axis=1)
    pct_25 = np.percentile(sims_display, 25, axis=1)
    pct_50 = np.percentile(sims_display, 50, axis=1)
    pct_75 = np.percentile(sims_display, 75, axis=1)
    pct_95 = np.percentile(sims_display, 95, axis=1)
    x_axis = list(range(months_future + 1))

    fig_mc = go.Figure()
    for i in range(min(100, mc_simulations)):
        fig_mc.add_trace(go.Scatter(
            x=x_axis, y=sims_display[:, i], mode="lines",
            line=dict(color="rgba(0,212,255,0.04)", width=1),
            showlegend=False, hoverinfo="skip",
        ))
    fig_mc.add_trace(go.Scatter(
        x=x_axis + x_axis[::-1], y=list(pct_95) + list(pct_05)[::-1],
        fill="toself", fillcolor="rgba(0,212,255,0.08)",
        line=dict(color="transparent"), name="5th–95th Percentile", hoverinfo="skip",
    ))
    fig_mc.add_trace(go.Scatter(
        x=x_axis + x_axis[::-1], y=list(pct_75) + list(pct_25)[::-1],
        fill="toself", fillcolor="rgba(0,212,255,0.15)",
        line=dict(color="transparent"), name="25th–75th Percentile", hoverinfo="skip",
    ))
    for pct, name_pct, color, width in [
        (pct_05, "Pessimistic (5th)",  "#FF4C4C", 2),
        (pct_25, "Bear (25th)",         "#FFA500", 2),
        (pct_50, "Median (50th)",       "#FFD700", 3),
        (pct_75, "Bull (75th)",         "#00FF87", 2),
        (pct_95, "Optimistic (95th)",   "#00D4FF", 2),
    ]:
        fig_mc.add_trace(go.Scatter(
            x=x_axis, y=pct, mode="lines", name=name_pct,
            line=dict(color=color, width=width),
            hovertemplate=f"<b>{name_pct}</b><br>เดือนที่ %{{x}}<br>฿%{{y:,.0f}}<extra></extra>",
        ))

    future_invested = [last_val + monthly_invest * t for t in range(months_future + 1)]
    fig_mc.add_trace(go.Scatter(
        x=x_axis, y=future_invested, mode="lines", name="Cash (DCA only)",
        line=dict(color="#4B5563", dash="dot", width=1.5),
        hovertemplate="เดือนที่ %{x}<br>Cash: ฿%{y:,.0f}<extra></extra>",
    ))

    label_suffix = " (Real/Inflation-Adjusted)" if show_inflation_adj else ""
    fig_mc.update_layout(
        template="plotly_dark", paper_bgcolor="#0A0A0F", plot_bgcolor="#0F0F18",
        height=520, hovermode="x unified",
        xaxis_title=f"Months into Future ({mc_years} Years)",
        yaxis_title=f"Portfolio Value THB{label_suffix}",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=50, b=20),
    )
    st.plotly_chart(fig_mc, use_container_width=True)

    col1, col2, col3, col4, col5 = st.columns(5)
    for col, pct_label, val, label, cls in [
        (col1, "5th",  pct_05[-1], "Pessimistic", "red"),
        (col2, "25th", pct_25[-1], "Bear Case",   ""),
        (col3, "50th", pct_50[-1], "Median",      "gold"),
        (col4, "75th", pct_75[-1], "Bull Case",   ""),
        (col5, "95th", pct_95[-1], "Optimistic",  "green"),
    ]:
        col.markdown(
            f'<div class="apex-card"><div class="apex-label">{label} ({pct_label} pct)</div>'
            f'<div class="apex-value {cls}">฿{val:,.0f}</div>'
            f'<div class="apex-sub">in {mc_years} yrs</div></div>',
            unsafe_allow_html=True,
        )

    goal_amount = st.number_input(
        "🎯 ตั้งเป้าหมาย: ฿ เท่าไหร่?", min_value=100_000, value=5_000_000, step=100_000,
    )
    prob = (sims_display[-1] >= goal_amount).mean() * 100
    box_class = "info-box" if prob >= 50 else "warn-box"
    st.markdown(
        f'<div class="{box_class}">🎯 โอกาสที่พอร์ตจะถึง <b>฿{goal_amount:,.0f}</b> ใน {mc_years} ปี = '
        f'<b>{prob:.1f}%</b> &nbsp;({mc_simulations:,} simulations)</div>',
        unsafe_allow_html=True,
    )


# ════════════════════════════════════════════════════════════════
# TAB 6: Goal Planner
# ════════════════════════════════════════════════════════════════
with tabs[5]:
    st.subheader("🎯 Goal Planner — คำนวณเงินที่ต้องลงทุน")
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("#### 💡 คำนวณเงิน DCA รายเดือนที่ต้องการ")
        goal_target = st.number_input("เป้าหมายมูลค่าพอร์ต (฿)", min_value=100_000,
                                      value=10_000_000, step=500_000)
        goal_years  = st.slider("ระยะเวลา (ปี)", 1, 40, 20)
        goal_asset  = st.selectbox("อ้างอิง CAGR จากสินทรัพย์:", list(all_metrics.keys()))
        goal_cagr   = all_metrics[goal_asset]["CAGR (%)"] / 100
        r_m         = goal_cagr / 12
        goal_n      = goal_years * 12
        current_port= all_metrics[goal_asset]["Final Value"]
        fv_current  = current_port * (1 + r_m) ** goal_n
        remaining   = goal_target - fv_current

        if remaining <= 0:
            pmt_required = 0.0
        elif r_m != 0:
            pmt_required = remaining * r_m / ((1 + r_m) ** goal_n - 1)
        else:
            pmt_required = remaining / goal_n

        st.markdown(
            f'<div class="apex-card apex-card-gold">'
            f'<div class="apex-label">เงิน DCA รายเดือนที่ต้องการ</div>'
            f'<div class="apex-value gold">฿ {max(0.0, pmt_required):,.0f}</div>'
            f'<div class="apex-sub">CAGR สมมติ: {goal_cagr*100:.2f}%/yr | เป้าหมาย: ฿{goal_target:,.0f} ใน {goal_years} ปี</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if fv_current >= goal_target:
            st.success(f"✅ พอร์ตปัจจุบัน (฿{current_port:,.0f}) จะเติบโตถึงเป้าหมายโดยไม่ต้องลงทุนเพิ่ม!")

    with col_b:
        st.markdown("#### 📊 Savings Roadmap")
        top_pmt = max(50_001, pmt_required * 2)
        pmts    = np.arange(500, top_pmt, 500)
        final_values = []
        for p in pmts:
            if r_m != 0:
                fv = current_port * (1 + r_m) ** goal_n + p * ((1 + r_m) ** goal_n - 1) / r_m
            else:
                fv = current_port + p * goal_n
            final_values.append(fv)

        fig_goal = go.Figure()
        fig_goal.add_trace(go.Scatter(
            x=pmts, y=final_values, mode="lines",
            fill="tozeroy", fillcolor="rgba(0,212,255,0.1)",
            line=dict(color="#00D4FF", width=2.5),
            hovertemplate="DCA: ฿%{x:,.0f}/mo<br>Final Value: ฿%{y:,.0f}<extra></extra>",
        ))
        fig_goal.add_hline(y=goal_target, line_color="gold", line_dash="dash",
                           annotation_text=f"Goal: ฿{goal_target:,.0f}", annotation_position="right")
        if pmt_required > 0:
            fig_goal.add_vline(x=pmt_required, line_color="#00FF87", line_dash="dot",
                               annotation_text=f"฿{pmt_required:,.0f}/mo")
        fig_goal.update_layout(
            template="plotly_dark", paper_bgcolor="#0A0A0F", plot_bgcolor="#0F0F18",
            height=380, xaxis_title="Monthly DCA (฿)", yaxis_title="Projected Value (฿)",
            margin=dict(l=20, r=20, t=20, b=20),
        )
        st.plotly_chart(fig_goal, use_container_width=True)

    # ── Lump Sum vs DCA ──────────────────────────────────────────
    st.markdown("---")
    st.subheader("⚖️ Lump Sum vs DCA Comparison")
    lump_asset  = st.selectbox("สินทรัพย์:", list(all_df.keys()), key="lump_sel")
    df_ls       = all_df[lump_asset]
    lump_amount = df_ls["Invested"].iloc[-1]
    lump_growth = lump_amount * (df_ls["Price"] / df_ls["Price"].iloc[0])

    fig_lump = go.Figure()
    fig_lump.add_trace(go.Scatter(x=df_ls.index, y=df_ls["Value"],  name="DCA Strategy",
                                  line=dict(color="#00D4FF", width=2.5)))
    fig_lump.add_trace(go.Scatter(x=df_ls.index, y=lump_growth,    name="Lump Sum (Day 1)",
                                  line=dict(color="#FFD700", width=2.5)))
    fig_lump.add_trace(go.Scatter(x=df_ls.index, y=df_ls["Invested"], name="Cash (No Investment)",
                                  line=dict(color="#4B5563", dash="dot", width=1.5)))
    fig_lump.update_layout(
        template="plotly_dark", paper_bgcolor="#0A0A0F", plot_bgcolor="#0F0F18",
        height=380, hovermode="x unified",
        xaxis_title="Date", yaxis_title="Value (THB)",
        margin=dict(l=20, r=20, t=20, b=20),
    )
    st.plotly_chart(fig_lump, use_container_width=True)

    dca_final = df_ls["Value"].iloc[-1]
    ls_final  = lump_growth.iloc[-1]
    winner    = "DCA" if dca_final > ls_final else "Lump Sum"
    diff      = abs(dca_final - ls_final)
    st.markdown(
        f'<div class="info-box">📊 <b>{winner}</b> ชนะในช่วงเวลาที่เลือก | ส่วนต่าง: <b>฿{diff:,.0f}</b></div>',
        unsafe_allow_html=True,
    )


# ════════════════════════════════════════════════════════════════
# TAB 7: Macro Dashboard
# ════════════════════════════════════════════════════════════════
with tabs[6]:
    st.subheader("🌍 Global Macro Dashboard")
    col1, col2 = st.columns(2)

    def inflation_bar(col, country_code, title):
        with col:
            st.markdown(f"#### {title}")
            data = fetch_worldbank_inflation(country_code)
            if data is not None and not data.empty:
                fig = go.Figure(go.Bar(
                    x=data["year"], y=data["inflation"],
                    marker=dict(color=data["inflation"], colorscale="RdYlGn_r", cmin=0, cmax=9),
                    hovertemplate="ปี: %{x}<br>เงินเฟ้อ: %{y:.2f}%<extra></extra>",
                ))
                fig.update_layout(
                    template="plotly_dark", paper_bgcolor="#0A0A0F", plot_bgcolor="#0F0F18",
                    height=300, xaxis_title="Year", yaxis_title="CPI Inflation (%)",
                    margin=dict(l=20, r=20, t=10, b=20),
                )
                st.plotly_chart(fig, use_container_width=True)
                st.caption("📡 Source: World Bank Open Data API | FP.CPI.TOTL.ZG")
            else:
                st.warning("ไม่สามารถดึงข้อมูล World Bank ได้")

    inflation_bar(col1, "TH", "🇹🇭 Thailand CPI Inflation")
    inflation_bar(col2, "US", "🇺🇸 US CPI Inflation")

    st.markdown("---")
    st.markdown("#### 📊 US Interest Rates & Gold (Yahoo Finance / FRED Proxy)")
    macro_data = fetch_macro_series()
    if macro_data:
        fig_macro = go.Figure()
        colors_macro = ["#00D4FF", "#FFD700", "#00FF87"]
        for i, (label, series) in enumerate(macro_data.items()):
            kwargs = dict(yaxis="y2") if "Gold" in label else {}
            fig_macro.add_trace(go.Scatter(
                x=series.index, y=series.values, name=label,
                line=dict(color=colors_macro[i % 3], width=2), **kwargs,
            ))
        fig_macro.update_layout(
            template="plotly_dark", paper_bgcolor="#0A0A0F", plot_bgcolor="#0F0F18",
            height=380, hovermode="x unified",
            yaxis=dict(title="Yield (%)"),
            yaxis2=dict(title="Gold (USD)", overlaying="y", side="right"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=60, t=50, b=20),
        )
        st.plotly_chart(fig_macro, use_container_width=True)
        st.caption("📡 Source: ^TNX, ^IRX, GC=F via Yahoo Finance | yfinance library")
    else:
        st.info("Macro data temporarily unavailable")


# ════════════════════════════════════════════════════════════════
# TAB 8: Data & Sources
# ════════════════════════════════════════════════════════════════
with tabs[7]:
    st.subheader("💾 Raw Data Export")

    # ── FIX: safe DataFrame construction ────────────────────────
    export_frames: Dict[str, pd.Series] = {}
    for name, df in all_df.items():
        short = name.split("(")[0].strip()
        export_frames[short] = df["Value"]

    export_df = pd.DataFrame(export_frames)
    first_name = list(all_df.keys())[0]
    invested_series = all_df[first_name]["Invested"].reindex(export_df.index)
    export_df["Cash_Invested"] = invested_series.values
    export_df.index = export_df.index.strftime("%Y-%m")
    export_df = export_df.round(2)

    st.dataframe(export_df, use_container_width=True)
    csv = export_df.to_csv().encode("utf-8")
    st.download_button("💾 Download Portfolio Data (.csv)", csv,
                       "apex_portfolio_data.csv", "text/csv")

    metrics_export = pd.DataFrame([
        {"Asset": m["Asset"], **{k: v for k, v in m.items() if k != "Asset"}}
        for m in all_metrics.values()
    ])
    metrics_csv = metrics_export.to_csv(index=False).encode("utf-8")
    st.download_button("📊 Download Metrics Summary (.csv)", metrics_csv,
                       "apex_metrics_summary.csv", "text/csv")

    st.markdown("---")
    st.subheader("📡 Data Sources & Transparency")
    for source, info in DATA_SOURCES.items():
        with st.expander(f"🔗 {source}"):
            st.markdown(f"""
| Field | Detail |
|-------|--------|
| **URL** | [{info['url']}]({info['url']}) |
| **Type** | {info['type']} |
| **Coverage** | {info['coverage']} |
| **Data Lag** | {info['lag']} |
| **Library** | `{info['library']}` |
            """)

    st.markdown("---")
    st.markdown("#### ⚠️ Legal Disclaimer")
    st.markdown("""
<div class="warn-box">
⚠️ <b>คำเตือนสำคัญ:</b> แพลตฟอร์มนี้มีวัตถุประสงค์เพื่อ<b>การศึกษาและการวิจัยเท่านั้น</b>
ผลการดำเนินงานในอดีตไม่รับประกันผลในอนาคต
Monte Carlo Simulation เป็นการจำลองทางสถิติ ไม่ใช่การพยากรณ์
โปรดปรึกษาผู้แนะนำการลงทุนที่ได้รับใบอนุญาตก่อนตัดสินใจลงทุน<br><br>
This platform is for <b>educational and research purposes only</b>. Past performance does not guarantee
future results. Consult a licensed financial advisor before investing.
</div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(f"""
<div style="text-align:center; color:#4B5563; font-size:12px; font-family:'DM Mono',monospace;">
APEX Invest v2.1 | Streamlit + Python | Data: Yahoo Finance, World Bank, FRED<br>
pandas {pd.__version__} | Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")} UTC+7
</div>
    """, unsafe_allow_html=True)
