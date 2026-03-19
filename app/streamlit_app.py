from __future__ import annotations

import os
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.backtest.metrics import compute_metrics
from app.backtest.strategy import run_backtest
from app.config import DEFAULT_PERIOD, DEFAULT_TICKER, TRANSACTION_COST_BPS
from app.data.market_data import load_market_data
from app.data.text_data import load_text_bundle
from app.features.technicals import add_features, latest_feature_snapshot
from app.llm.summarize import build_memo

st.set_page_config(page_title="AlphaMemo – AI Fund Manager", layout="wide", page_icon="📊")

# ══════════════════════════════════════════════════════════════════════════════
# CACHED DATA FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=900, show_spinner=False)
def cached_market_data(ticker: str, period: str):
    return load_market_data(ticker, period=period)

@st.cache_data(ttl=3600, show_spinner=False)
def cached_headlines(ticker: str):
    return load_text_bundle(ticker)

@st.cache_data(ttl=3600, show_spinner=False)
def cached_company_info(ticker: str):
    try:
        import yfinance as yf
        info = yf.Ticker(ticker).info
        return {
            "name":       info.get("longName") or info.get("shortName") or ticker,
            "sector":     info.get("sector", "N/A"),
            "industry":   info.get("industry", "N/A"),
            "country":    info.get("country", "N/A"),
            "market_cap": info.get("marketCap"),
            "employees":  info.get("fullTimeEmployees"),
            "website":    info.get("website", ""),
            "summary":    info.get("longBusinessSummary", ""),
            "exchange":   info.get("exchange", ""),
            "currency":   info.get("currency", "USD"),
            "52w_high":   info.get("fiftyTwoWeekHigh"),
            "52w_low":    info.get("fiftyTwoWeekLow"),
            "pe_ratio":   info.get("trailingPE"),
            "dividend":   info.get("dividendYield"),
        }
    except Exception:
        return None

def fmt_market_cap(mc):
    if not mc: return "N/A"
    if mc >= 1_000_000_000_000: return f"${mc/1_000_000_000_000:.1f}T"
    if mc >= 1_000_000_000:     return f"${mc/1_000_000_000:.1f}B"
    if mc >= 1_000_000:         return f"${mc/1_000_000:.1f}M"
    return f"${mc:,.0f}"

def fmt_action(action: str) -> str:
    mapping = {
        "long":       "Buy",
        "long_small": "Buy (small position)",
        "short":      "Sell / Avoid",
        "short_small":"Sell (small position)",
        "hold":       "Hold — no action",
    }
    return mapping.get(action, action.replace("_", " ").title())

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.header("⚙️ Settings")

    dark_mode = st.toggle("🌙 Dark Mode", value=False)

    trader_type = st.radio(
        "👤 I am a...",
        options=["Short-term Trader", "Long-term Investor"],
        help="Short-term = days to weeks.\nLong-term = months to years.\nThis changes how the results are explained to you.",
    )

    with st.expander("ℹ️ How to use this app", expanded=False):
        st.markdown("""
**AlphaMemo** reads news and price data for any stock and gives you a research summary.

**Steps:**
1. Type a stock symbol (e.g. `AAPL`, `TSLA`, `SONY`)
2. Choose whether you are a short-term or long-term investor
3. Click **▶ Run analysis**

**What you will see:**
- 🏢 Company overview — what the company does
- 📋 Research summary with buy/sell suggestion
- 🔍 Full explanation of how the AI decided
- 📈 Price chart and performance history

> ⚠️ For learning only. Not real investment advice.
        """)

    ticker_input = st.text_input(
        "Stock symbol",
        value=DEFAULT_TICKER,
        placeholder="e.g. AAPL, MSFT, SONY, ONDS",
        help="Type any stock symbol. Works for US stocks and many international ones.",
    )
    ticker = ticker_input.upper().strip()

    period = st.selectbox(
        "How far back to look",
        options=["6mo", "1y", "2y"],
        index=1,
        format_func=lambda x: {"6mo": "6 months", "1y": "1 year", "2y": "2 years"}[x],
    )

    # Transaction cost
    st.markdown("**💸 Trading Fees**")
    is_short = trader_type == "Short-term Trader"
    cost_preset = st.selectbox(
        "My broker charges...",
        options=[
            "Almost nothing (e.g. Robinhood) — 0.05%",
            "Standard broker — 0.10%",
            "Active trading account — 0.20%",
            "Small or rare stocks — 0.30%",
            "Let me set my own",
        ],
        index=2 if is_short else 1,
        help="Every time you buy or sell a stock, you pay a small fee.\nShort-term traders pay more because they trade more often."
    )
    preset_map = {
        "Almost nothing (e.g. Robinhood) — 0.05%": 5,
        "Standard broker — 0.10%": 10,
        "Active trading account — 0.20%": 20,
        "Small or rare stocks — 0.30%": 30,
    }
    if "Let me set" in cost_preset:
        transaction_cost_bps = st.slider(
            "Fee per trade (0.01% steps)", 0, 50, TRANSACTION_COST_BPS,
            help="Slide to set your trading fee. 10 = 0.10% per trade."
        )
    else:
        transaction_cost_bps = preset_map[cost_preset]
        st.caption(f"✅ Fee: **{transaction_cost_bps/100:.2f}% per trade**")

    with st.expander("❓ What is a trading fee?"):
        st.markdown(f"""
Every time you buy or sell a stock, your broker charges a small fee.

**Example with your current setting ({transaction_cost_bps/100:.2f}% per trade):**
- You buy $1,000 of stock → pay **${transaction_cost_bps/10:.1f}** in fees
- You sell $1,000 of stock → pay **${transaction_cost_bps/10:.1f}** in fees
- Total round trip cost = **${transaction_cost_bps/5:.1f}**

This is automatically deducted from all backtest results so you see realistic numbers.
        """)

    st.divider()
    st.subheader("🔑 Claude AI Key")
    api_key_input = st.text_input(
        "Anthropic API key (optional)", type="password",
        help="Without a key: uses a simple formula to score news.\nWith a key: Claude AI reads and understands the news properly.",
        value=os.environ.get("ANTHROPIC_API_KEY", ""),
    )
    if api_key_input:
        os.environ["ANTHROPIC_API_KEY"] = api_key_input

    run = st.button("▶ Run analysis", type="primary", use_container_width=True)
    if st.button("🔄 Refresh & re-fetch data", use_container_width=True,
                 help="Use this if results look outdated or you just added/removed an API key"):
        st.cache_data.clear()
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# THEME
# ══════════════════════════════════════════════════════════════════════════════
if dark_mode:
    plot_template = "plotly_dark"
    price_colors  = ["#00D4FF", "#FF6B35", "#00FF88"]
    equity_colors = ["#00D4FF", "#FF4444"]
    st.markdown("<style>.stApp{background-color:#0E1117;color:#FAFAFA;}</style>", unsafe_allow_html=True)
else:
    plot_template = "plotly_white"
    price_colors  = ["#1565C0", "#E65100", "#2E7D32"]
    equity_colors = ["#1565C0", "#C62828"]

# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════
st.title("📊 AlphaMemo — AI Research Copilot")
st.caption("Educational prototype for research support and practice trading only. Not real investment advice.")

st.warning("""
⚠️ **Please read before using:**
- 📡 Stock prices from **Yahoo Finance** — may be up to **15 minutes old**
- 📰 News may not include the **very latest** headlines
- 📉 All performance results are **historical simulations** — past results do not predict the future
- 🕒 All signals look at **the last 20 trading days only** — short-term view
- 🚫 **Do not use this app for real money decisions**
""")

# ══════════════════════════════════════════════════════════════════════════════
# API KEY NOTICE
# ══════════════════════════════════════════════════════════════════════════════
api_key_present = bool(os.environ.get("ANTHROPIC_API_KEY", ""))
if not api_key_present:
    st.info("""
ℹ️ **Running in basic mode — no AI key provided**

- 📐 News is scored using a simple word-matching formula (not AI)
- 📋 Research summary is generated by fixed rules (not AI)
- 📊 Stock prices and company info still come from **Yahoo Finance** (real data)

To enable full Claude AI analysis: enter your Anthropic API key in the sidebar, then click **🔄 Refresh & re-fetch data**.
    """)

# ══════════════════════════════════════════════════════════════════════════════
# ONBOARDING
# ══════════════════════════════════════════════════════════════════════════════
if not run:
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.info("**Step 1** 📝\n\nType a stock symbol in the sidebar\n\ne.g. `AAPL` = Apple, `TSLA` = Tesla")
    with col_b:
        st.info("**Step 2** 👤\n\nChoose Short-term or Long-term\n\nThe app explains results differently for each")
    with col_c:
        st.info("**Step 3** ▶️\n\nClick **Run analysis**\n\nGet your company overview + research summary")
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# VALIDATE
# ══════════════════════════════════════════════════════════════════════════════
if not ticker:
    st.error("⚠️ Please enter a stock symbol (e.g. AAPL, MSFT, TSLA).")
    st.stop()
if len(ticker) > 10:
    st.error(f"⚠️ '{ticker}' doesn't look like a valid stock symbol. Symbols are usually 1–5 characters.")
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# DATA PIPELINE
# ══════════════════════════════════════════════════════════════════════════════
with st.spinner(f"🔍 Looking up {ticker}…"):
    company_info = cached_company_info(ticker)

with st.spinner(f"📡 Loading price data for {ticker}…"):
    market_data = cached_market_data(ticker, period or DEFAULT_PERIOD)

if market_data.prices.empty:
    st.error(f"⚠️ Could not find price data for **{ticker}**. Please check the symbol.\n\nExamples: `AAPL`, `MSFT`, `NVDA`, `TSLA`, `SONY`")
    st.stop()

with st.spinner("⚙️ Calculating signals…"):
    prices     = market_data.prices
    feature_df = add_features(prices)
    snapshot   = latest_feature_snapshot(feature_df)

with st.spinner("📰 Loading news headlines…"):
    headlines = cached_headlines(ticker)

# Build memo with smart cache
headlines_key = str(sorted(headlines))
snapshot_key  = str({k: round(v, 4) for k, v in snapshot.items()})
cache_key     = f"{ticker}_{period}_{headlines_key[:50]}_{snapshot_key[:50]}"

if st.session_state.get("_memo_cache_key") != cache_key:
    with st.spinner("🤖 Generating research summary…"):
        memo = build_memo(ticker, headlines, snapshot)
        st.session_state["_memo_result"]    = memo
        st.session_state["_memo_cache_key"] = cache_key
else:
    memo = st.session_state["_memo_result"]

with st.spinner("📊 Running performance simulation…"):
    backtest_df = run_backtest(feature_df.dropna().copy(), transaction_cost_bps=transaction_cost_bps)
    metrics     = compute_metrics(backtest_df)

# ══════════════════════════════════════════════════════════════════════════════
# SYNTHETIC DATA WARNING
# ══════════════════════════════════════════════════════════════════════════════
if market_data.source == "synthetic":
    st.error(f"""
⚠️ **WARNING — Using simulated price data for {ticker}**

Yahoo Finance could not download real prices right now. The app is using fake generated prices to show how it works.

- 📉 The price chart does NOT show real prices
- 📊 All performance results are based on fake data
- ❌ Do NOT use this analysis for any trading decisions

**Try:** Check your internet connection, verify the stock symbol, or try again in a few minutes.
    """)

# ══════════════════════════════════════════════════════════════════════════════
# COMPANY OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
st.divider()
st.subheader("🏢 Company Overview")

if company_info and company_info.get("name"):
    co = company_info
    st.markdown(f"### {co['name']} `{ticker}`")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("🏭 Sector",       co["sector"])
    c2.metric("🌍 Country",      co["country"])
    c3.metric("💰 Market Value", fmt_market_cap(co["market_cap"]))
    c4.metric("📈 1-Year High",  f"${co['52w_high']:.2f}" if co["52w_high"] else "N/A")
    c5.metric("📉 1-Year Low",   f"${co['52w_low']:.2f}"  if co["52w_low"]  else "N/A")

    col_left, col_right = st.columns(2)
    with col_left:
        if co["employees"]:
            st.caption(f"👥 Employees: **{co['employees']:,}**")
        if co["pe_ratio"]:
            label = "expensive vs earnings" if co["pe_ratio"] > 30 else "reasonable" if co["pe_ratio"] > 10 else "cheap vs earnings"
            st.caption(f"📊 Price-to-Earnings: **{co['pe_ratio']:.1f}x** — {label}")
        if co["dividend"]:
            # yfinance returns dividend yield as a decimal (e.g. 0.005 = 0.5%)
            # Some tickers return it already as percentage (e.g. 0.5 = 0.5%)
            # We normalize: if value < 0.2 it's likely decimal format → multiply by 100
            div_pct = co["dividend"] * 100 if co["dividend"] < 0.2 else co["dividend"]
            st.caption(f"💵 Dividend yield: **{div_pct:.2f}% per year**")
        if co["website"]:
            st.caption(f"🔗 [Official Website]({co['website']})")
    with col_right:
        if co["industry"]:
            st.caption(f"🏗️ Industry: **{co['industry']}**")
        if co["exchange"]:
            st.caption(f"🏦 Listed on: **{co['exchange']}** ({co['currency']})")

    if co["summary"]:
        with st.expander("📖 What does this company do?", expanded=True):
            sentences = co["summary"].replace("  ", " ").split(". ")
            brief = ". ".join(sentences[:3]) + ("." if len(sentences) > 3 else "")
            st.write(brief)
            if len(sentences) > 3:
                with st.expander("Read full description…"):
                    st.write(co["summary"])
    else:
        st.info(f"No description available for {ticker} from Yahoo Finance.")
else:
    st.info(f"Detailed company data not available for **{ticker}** (common for smaller stocks).")
    if headlines:
        with st.expander("📖 What do we know from the news?", expanded=True):
            st.caption("Based on recent headlines:")
            for h in headlines[:5]:
                st.write(f"• {h}")
    st.caption(f"💡 Tip: Search **'{ticker} stock'** on Google to learn more about this company.")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# STANCE INTERPRETATION
# ══════════════════════════════════════════════════════════════════════════════
stance = memo["stance"]

interpretation = {
    ("bullish", True):  ("🟢 POSITIVE SIGNAL — Good for short-term traders",
                         "Price momentum is rising and the stock is above its key price averages. Short-term traders may consider buying."),
    ("bullish", False): ("🟡 POSITIVE SIGNAL — But use caution as a long-term investor",
                         "Short-term momentum looks good, but the stock may already be near a peak. Long-term investors should consider waiting for a better entry price."),
    ("bearish", True):  ("🔴 NEGATIVE SIGNAL — Caution for short-term traders",
                         "Price momentum is falling and the stock is below its key price averages. Short-term traders should avoid buying."),
    ("bearish", False): ("🟡 NEGATIVE SIGNAL — Possible long-term opportunity",
                         "Short-term momentum is weak, but long-term investors may see this as a chance to buy at a lower price if the company is fundamentally strong."),
    ("neutral", True):  ("🟡 NO CLEAR SIGNAL — Wait and see (short-term)",
                         "Mixed signals. Short-term traders should wait for a clearer trend before acting."),
    ("neutral", False): ("🟡 NO CLEAR SIGNAL — Steady for long-term investors",
                         "No strong signal either way. Long-term investors can continue holding if already invested."),
}
interp_title, interp_desc = interpretation.get((stance, is_short), ("⚪ Unknown", ""))
action_label = fmt_action(memo["paper_trade_action"])

if stance == "bullish" and is_short:
    st.success(f"**{interp_title}**\n\n{interp_desc}\n\n📌 Suggested practice trade: **{action_label}** | Confidence: **{memo['confidence']:.0%}**")
elif stance == "bearish":
    st.error(f"**{interp_title}**\n\n{interp_desc}\n\n📌 Suggested practice trade: **{action_label}** | Confidence: **{memo['confidence']:.0%}**")
else:
    st.warning(f"**{interp_title}**\n\n{interp_desc}\n\n📌 Suggested practice trade: **{action_label}** | Confidence: **{memo['confidence']:.0%}**")

if is_short:
    st.caption("⚠️ *This signal looks at the last 20 trading days only. It does not reflect the company's long-term health or financial results.*")
else:
    st.caption("⚠️ *As a long-term investor, focus on company fundamentals and earnings growth — not short-term price movements.*")

# ══════════════════════════════════════════════════════════════════════════════
# KPI STRIP
# ══════════════════════════════════════════════════════════════════════════════
st.divider()
col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Signal", stance.title(),
    help="🟢 Positive = price signals suggest stock may go up\n🔴 Negative = price signals suggest stock may go down\n🟡 Neutral = no clear direction\n\nBased on last 20 trading days only.")
col2.metric("Confidence", f"{memo['confidence']:.0%}",
    help="How strongly the signals agree.\n\n✅ 70–85% = strong agreement\n⚠️ 45–65% = weak agreement\n\nMaximum is 85% — the app never claims to be certain.\nFormula: 45% + (score × 8%), max 85%")
col3.metric("Simulated Return", f"{metrics['strategy_return']:.1%}",
    help="If you had followed this strategy over the selected period, this is how much you would have gained or lost.\n\n✅ Positive = made money\n❌ Negative = lost money\n\n⚠️ Past results do NOT predict the future.")
col4.metric("Risk-Adjusted Score", f"{metrics['sharpe']:.2f}",
    help="Measures return vs risk.\n\n✅ Above 1.0 = good (reward worth the risk)\n⚠️ 0 to 1.0 = okay\n❌ Below 0 = risk was not worth it\n\nAlso called Sharpe Ratio by professionals.")
col5.metric("Worst Loss", f"{metrics['max_drawdown']:.1%}",
    help="The biggest loss from peak to bottom during the period.\n\nExample: Portfolio went $100 → $80 = −20%\n\n✅ Closer to 0% = safer strategy\n❌ −20% or worse = high risk\n\nAlso called Max Drawdown by professionals.")
col6.metric("Win Rate", f"{metrics['hit_rate']:.1%}",
    help="% of trading days the strategy made money.\n\n✅ Above 50% = strategy won more days than it lost\n❌ Below 50% = lost more days than it won")

memo_source = "🤖 Claude AI" if memo.get("memo_source") == "claude-api" else "📐 Basic formula"
st.caption(f"Analysis: **{memo_source}** | Prices: **Yahoo Finance** (up to 15 min delay) | Data: **{market_data.source}**")
st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# MAIN LAYOUT
# ══════════════════════════════════════════════════════════════════════════════
left, right = st.columns([1.1, 0.9])

with left:
    st.subheader("📋 Research Summary")
    stance_emoji = {"bullish": "🟢", "bearish": "🔴", "neutral": "🟡"}.get(stance, "⚪")
    st.markdown(f"**{stance_emoji} {stance.title()}** | Confidence: {memo['confidence']:.0%} | Suggestion: **{action_label}**")

    with st.expander("📌 Main view — Why this signal?", expanded=True):
        for line in memo.get("thesis", []):
            st.write(f"• {line}")

    with st.expander("🚀 What could push the price up?", expanded=True):
        for line in memo.get("catalysts", []):
            st.write(f"• {line}")

    with st.expander("⚠️ What could push the price down?", expanded=True):
        for line in memo.get("risks", []):
            st.write(f"• {line}")

    # ── Full AI Explanation ────────────────────────────────────────────────────
    with st.expander("🔍 Why did the AI give this signal? (Full explanation)", expanded=True):
        st.markdown("**Here is exactly how the AI decided — step by step:**")
        st.caption("The AI reads news headlines and checks recent price data. Each finding adds or subtracts points. The total score decides the signal.")

        scores        = memo.get("scores", {})
        text_score    = scores.get("text_score", 0)
        feature_score = scores.get("feature_score", 0)
        total_score   = scores.get("total_score", 0)
        confidence    = memo["confidence"]

        # Step 1 — News
        sentiment_source = memo.get("sentiment_source", "keyword-list")
        found_positive   = memo.get("found_positive", [])
        found_negative   = memo.get("found_negative", [])
        sentiment_reason = memo.get("sentiment_reasoning", "")

        if sentiment_source == "claude-ai":
            st.markdown("**Step 1 — What did the AI find in the news?**")
            st.caption("🤖 Claude AI read each headline and identified meaningful signals — not a fixed word list.")
        else:
            st.markdown("**Step 1 — What words were found in the news?**")
            st.caption("📐 Basic mode: news is scored by matching against a list of positive and negative financial words.")

        col_xai1, col_xai2 = st.columns(2)
        with col_xai1:
            if found_positive:
                pos_text = ", ".join(f"`{w}`" for w in found_positive)
                st.success(f"✅ **Good signals found** (+1 each):\n\n{pos_text}")
            else:
                st.info("✅ No positive signals found in the news")
        with col_xai2:
            if found_negative:
                neg_text = ", ".join(f"`{w}`" for w in found_negative)
                st.error(f"❌ **Concerning signals found** (−1 each):\n\n{neg_text}")
            else:
                st.info("❌ No negative signals found in the news")

        if sentiment_reason:
            st.caption(f"💬 AI summary: *{sentiment_reason}*")

        if text_score > 0:
            st.success(f"📰 News score = **+{text_score}** → News looks more positive than negative")
        elif text_score < 0:
            st.error(f"📰 News score = **{text_score}** → News looks more negative than positive")
        else:
            st.warning(f"📰 News score = **{text_score}** → News is neutral — no strong signal")

        st.divider()

        # Step 2 — Price signals
        st.markdown("**Step 2 — What does the price data show?**")

        r20    = snapshot["return_20d"]
        ma50g  = snapshot["ma_50_gap"]
        ma200g = snapshot["ma_200_gap"]
        vol    = snapshot["volatility_20d"]
        volch  = snapshot["volume_change"]

        tech_rows = []
        if r20 > 0.03:
            tech_rows.append(("📈 20-day price change", f"+{r20:.1%}", "+1", "✅ Price has risen strongly recently"))
        elif r20 < -0.03:
            tech_rows.append(("📉 20-day price change", f"{r20:.1%}", "−1", "❌ Price has fallen strongly recently"))
        else:
            tech_rows.append(("➡️ 20-day price change", f"{r20:.1%}", "0", "⚠️ Price change too small to signal"))

        if ma50g > 0 and ma200g > 0:
            tech_rows.append(("📊 Price vs averages", f"50-day: {ma50g:+.1%} / 200-day: {ma200g:+.1%}", "+1", "✅ Price is above both averages — upward trend"))
        elif ma50g < 0 and ma200g < 0:
            tech_rows.append(("📊 Price vs averages", f"50-day: {ma50g:+.1%} / 200-day: {ma200g:+.1%}", "−1", "❌ Price is below both averages — downward trend"))
        else:
            tech_rows.append(("📊 Price vs averages", f"50-day: {ma50g:+.1%} / 200-day: {ma200g:+.1%}", "0", "⚠️ Mixed — price between the two averages"))

        if vol > 0.45:
            tech_rows.append(("🌪️ Price swings (volatility)", f"{vol:.1%} annualized", "−1", "❌ Price is swinging too much — signal less reliable"))
        else:
            tech_rows.append(("🌪️ Price swings (volatility)", f"{vol:.1%} annualized", "0", "✅ Price swings are within normal range"))

        if volch > 0.25:
            tech_rows.append(("📦 Trading activity", f"+{volch:.1%} vs average", "+1", "✅ More people trading than usual — confirms the move"))
        elif volch < -0.25:
            tech_rows.append(("📦 Trading activity", f"{volch:.1%} vs average", "−1", "❌ Fewer people trading than usual — move may not hold"))
        else:
            tech_rows.append(("📦 Trading activity", f"{volch:.1%} vs average", "0", "⚠️ Normal trading activity — no extra signal"))

        tech_df = pd.DataFrame(tech_rows, columns=["Factor", "Value", "Points", "What it means"])
        st.dataframe(tech_df, hide_index=True)

        if feature_score > 0:
            st.success(f"📊 Price signal score = **+{feature_score}**")
        elif feature_score < 0:
            st.error(f"📊 Price signal score = **{feature_score}**")
        else:
            st.warning(f"📊 Price signal score = **{feature_score}**")

        st.divider()

        # Step 3 — Final decision
        st.markdown("**Step 3 — Final Decision**")
        st.markdown(f"""
| What was checked | Score |
|-----------------|-------|
| 📰 News signals | **{text_score:+d}** |
| 📊 Price signals | **{feature_score:+d}** |
| 🎯 **Total** | **{total_score:+d}** |
        """)

        st.markdown("**Why does it need +2 or more to say Positive (Bullish)?**")
        st.info("""
The app checks **4 price factors** (recent price change, price vs averages, price swings, trading activity).
Each can add +1 or subtract −1.

We require at least **2 out of 4 factors to agree** before calling it Positive or Negative.
If only 1 factor fires, the signal stays Neutral — to avoid false alarms.

> ⚠️ *This +2 threshold is a design choice by the developer — not a result of scientific training on market data. A future version could learn the best threshold automatically.*
        """)

        st.markdown("**Why does confidence start at 45%?**")
        st.info(f"""
**Formula:** Start at 45% + add 8% for each point of score → maximum 85%

**Your result:** 45% + ({total_score} × 8%) = {45 + abs(total_score)*8:.0f}% → **{confidence:.0%}**

- Starts at **45%** (below 50%) when score = 0, meaning *"no strong signal — stay cautious"*
- Each extra point of score adds **8% more confidence**
- Capped at **85%** — the app should never claim to be certain, because markets are unpredictable

> ⚠️ *The 45% starting point and 8% per step are design choices, not statistically proven values.*
        """)

        if total_score >= 2:
            st.success(f"✅ Total score = **{total_score:+d}** → **POSITIVE (Bullish)** with **{confidence:.0%}** confidence")
        elif total_score <= -2:
            st.error(f"❌ Total score = **{total_score:+d}** → **NEGATIVE (Bearish)** with **{confidence:.0%}** confidence")
        else:
            st.warning(f"⚠️ Total score = **{total_score:+d}** → **NEUTRAL** with **{confidence:.0%}** confidence")

    with st.expander("📰 News headlines used"):
        st.caption("⚠️ From Yahoo Finance. May not include the very latest news.")
        for item in headlines:
            st.write(f"- {item}")

    st.caption(f"⚠️ {memo.get('risk_note', '')}")

with right:
    st.subheader("📈 Price History & Averages")
    st.caption("Blue = actual price. The two lines are price averages. Price above both lines = positive trend.")
    chart_df = feature_df.dropna().reset_index()
    date_col = chart_df.columns[0]
    fig_price = go.Figure()
    fig_price.add_trace(go.Scatter(x=chart_df[date_col], y=chart_df["Close"],
        name="Stock Price", line=dict(color=price_colors[0], width=2.5)))
    fig_price.add_trace(go.Scatter(x=chart_df[date_col], y=chart_df["ma_50"],
        name="50-day average", line=dict(color=price_colors[1], width=2, dash="dash")))
    fig_price.add_trace(go.Scatter(x=chart_df[date_col], y=chart_df["ma_200"],
        name="200-day average", line=dict(color=price_colors[2], width=2, dash="dot")))
    fig_price.update_layout(template=plot_template, yaxis_title="Price ($)",
        legend=dict(orientation="h", y=-0.2), margin=dict(l=0, r=0, t=10, b=0), height=320)
    st.plotly_chart(fig_price)

    st.subheader("💰 Strategy Performance")
    st.caption("Blue = AlphaMemo strategy. Red = just buying and holding. Blue above red = strategy is doing better.")
    curve_df  = backtest_df.reset_index()
    date_col2 = curve_df.columns[0]
    fig_equity = go.Figure()
    fig_equity.add_trace(go.Scatter(x=curve_df[date_col2], y=curve_df["equity_curve"],
        name="AlphaMemo Strategy", line=dict(color=equity_colors[0], width=2.5)))
    fig_equity.add_trace(go.Scatter(x=curve_df[date_col2], y=curve_df["benchmark_curve"],
        name="Buy & Hold", line=dict(color=equity_colors[1], width=2, dash="dash")))
    fig_equity.update_layout(template=plot_template, yaxis_title="Growth of $1",
        legend=dict(orientation="h", y=-0.2), margin=dict(l=0, r=0, t=10, b=0), height=320)
    st.plotly_chart(fig_equity)

# ══════════════════════════════════════════════════════════════════════════════
# PRICE DATA DETAILS
# ══════════════════════════════════════════════════════════════════════════════
with st.expander("🔬 Price Data Details"):
    if market_data.source == "synthetic":
        st.warning("⚠️ These numbers are **SIMULATED** — not real market data.")
    else:
        st.caption("These are the exact numbers the analysis system used to calculate the signal.")
    snap_readable = pd.DataFrame({
        "What was measured": ["Current Price", "20-day Price Change", "Price Volatility",
                              "vs 50-day Average", "vs 200-day Average", "Trading Activity", "Trend Strength"],
        "Value": [f"${snapshot['close']:.2f}", f"{snapshot['return_20d']:.1%}", f"{snapshot['volatility_20d']:.1%}",
                  f"{snapshot['ma_50_gap']:.1%}", f"{snapshot['ma_200_gap']:.1%}",
                  f"{snapshot['volume_change']:.1%}", f"{snapshot['trend_signal']:.0f} / 2"],
        "What it means": [
            "Latest stock price from Yahoo Finance",
            "How much the price changed over the last 20 trading days",
            "How much the price swings up and down — higher = riskier",
            "Price is this much above (+) or below (−) its 50-day average price",
            "Price is this much above (+) or below (−) its 200-day average price",
            "How much more or less people are trading vs the last 20 days",
            "0 = no uptrend  |  1 = weak uptrend  |  2 = strong uptrend",
        ]
    })
    st.dataframe(snap_readable, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# PERFORMANCE HISTORY
# ══════════════════════════════════════════════════════════════════════════════
with st.expander("📊 Historical Performance — How would this strategy have done?"):
    st.caption(f"⚠️ Simulated results using historical data only. Trading fee: {transaction_cost_bps/100:.2f}% per trade deducted.")
    st.caption("Past performance does NOT guarantee future results.")
    metrics_readable = pd.DataFrame({
        "Metric": ["Strategy Return", "Buy & Hold Return", "Risk-Adjusted Score",
                   "Worst Loss", "Win Rate", "How often traded"],
        "Value": [f"{metrics['strategy_return']:.1%}", f"{metrics['benchmark_return']:.1%}",
                  f"{metrics['sharpe']:.2f}", f"{metrics['max_drawdown']:.1%}",
                  f"{metrics['hit_rate']:.1%}", f"{metrics['turnover']:.1f}x/year"],
        "Plain English": [
            "Total gain or loss following the strategy (after fees)",
            "Total gain or loss if you just bought and held the stock",
            "How much return you got per unit of risk — above 1.0 is good",
            "The biggest drop from peak to bottom during this period",
            "% of days the strategy made money — above 50% is good",
            "How many times per year the strategy changed its position",
        ]
    })
    st.dataframe(metrics_readable, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# HOW THE STRATEGY WORKS
# ══════════════════════════════════════════════════════════════════════════════
st.subheader("📋 How the Strategy Works")
st.caption("These are the exact rules the app uses. Nothing is hidden.")
st.markdown(f"""
| Condition | Suggestion | Why |
|-----------|------------|-----|
| Price up 3%+ in 20 days AND above both averages | **Buy** | Strong upward trend |
| Price down 3%+ in 20 days AND below both averages | **Sell / Avoid** | Strong downward trend |
| Everything else | **Hold — no action** | No clear signal |

- All signals are checked using data from the **previous day** to avoid using future information
- Trading fee of **{transaction_cost_bps/100:.2f}% per trade** is deducted from all results
""")

# ══════════════════════════════════════════════════════════════════════════════
# FOOTER — Safety & Disclaimer
# ══════════════════════════════════════════════════════════════════════════════
st.divider()
col_f1, col_f2 = st.columns(2)
with col_f1:
    st.markdown("**🛡️ Safety & Ethics**")
    st.caption("✅ Practice mode only — no real money involved")
    st.caption("✅ Cannot buy or sell real stocks")
    st.caption("✅ AI confidence limited to 85% maximum")
    st.caption("✅ Trading fees included in all results")
    st.caption("✅ Works for any stock — no favorites or bias")
    st.caption("✅ All AI decisions explained in plain English")
with col_f2:
    st.markdown("**⚠️ Disclaimer**")
    st.caption("AlphaMemo is an educational prototype for practice trading and research only.")
    st.caption("NOT financial advice. NOT suitable for real money decisions.")
    st.caption("Stock prices from Yahoo Finance — may be delayed up to 15 minutes.")
    st.caption("Past performance does NOT guarantee future results.")
    st.caption("Always consult a licensed financial advisor before investing.")
