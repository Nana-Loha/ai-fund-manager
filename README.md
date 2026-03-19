# AlphaMemo — AI Research Copilot

> **AI 405 - AI Impacts and Applications | Final Project**
>
> **Author:** Pitchanan Lohavanichbutr
>
> **Bellevue College | March 2026**

An educational AI application that combines market price data, financial headlines,
and technical features to generate structured investment research memos and
practice-trading signals. Built as a class project for an AI Ethics course.

> ⚠️ **This is an educational prototype for practice trading and research only.
> It is not investment advice and does not place live trades.**

---

## How to Run

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Set your API key (optional — app works without it)
```bash
export ANTHROPIC_API_KEY=your-key-here
# OR enter it directly in the app sidebar
```

### 3. Start the app
```bash
streamlit run streamlit_app.py
```

### 4. Deploy to Streamlit Cloud (optional)

To deploy your app publicly to **Streamlit Cloud**:

1. **Push this repo to your GitHub account** (already done ✅)
   - Your repo: https://github.com/Nana-Loha/ai-fund-manager (private)

2. **Connect to Streamlit Cloud:**
   - Go to https://share.streamlit.io
   - Sign in with GitHub
   - Click **"New app"**
   - Select:
     - **Repository:** `Nana-Loha/ai-fund-manager`
     - **Branch:** `main`
     - **Main file path:** `app/streamlit_app.py`

3. **Set secrets (if using Claude API):**
   - In the Streamlit Cloud dashboard, go to **App settings → Secrets**
   - Add:
     ```toml
     ANTHROPIC_API_KEY = "your-anthropic-api-key-here"
     ```

4. **Deploy!**
   - Click **"Deploy"** and wait ~2 minutes
   - Your app will be live at: `https://share.streamlit.io/<username>/<app-name>`

---

## What it does

1. **Fetches real stock price data** via Yahoo Finance (yfinance)
2. **Loads recent news headlines** from Yahoo Finance
3. **Computes technical signals** — momentum, moving averages, volatility, volume
4. **Generates a structured research summary** — using Claude API if a key is provided, otherwise a transparent rule-based formula
5. **Simulates historical strategy performance** with trading fee assumptions
6. **Displays results** in a Streamlit dashboard with plain-English explanations

---

## Project Structure

```
ai-fund-manager/
├── app/
│   ├── streamlit_app.py      # Main UI
│   ├── config.py             # Settings
│   ├── data/
│   │   ├── market_data.py    # Price data loader (yfinance)
│   │   └── text_data.py      # News headlines loader
│   ├── features/
│   │   └── technicals.py     # Technical signal calculation
│   ├── llm/
│   │   ├── summarize.py      # Memo generator (Claude API + fallback)
│   │   └── stance_engine.py  # Rule-based signal scoring
│   └── backtest/
│       ├── strategy.py       # Position logic
│       └── metrics.py        # Performance metrics
├── data/
│   └── eval/
│       └── sample_news.json  # Fallback sample headlines
├── requirements.txt
├── .env.example
└── README.md
```

---

## Tools & Resources Used

| Tool | Purpose |
|------|---------|
| Python 3.11 | Core language |
| Streamlit | Web UI framework |
| yfinance | Real-time stock prices and news |
| pandas / numpy | Data processing |
| plotly | Interactive charts |
| Anthropic Claude API | AI memo generation and news sentiment analysis |

### References

- Yang et al. (2023) — Instruct-FinGPT: Financial Sentiment Analysis by Instruction Tuning of General-Purpose LLMs — arXiv:2306.12659
- Kim, Muhn & Nikolaev (2024) — Financial Statement Analysis with Large Language Models — arXiv:2407.17866
- Investopedia — Technical Analysis — https://www.investopedia.com/terms/t/technicalanalysis.asp

---

## AI Tools Disclosure

| Tool | Role |
|------|------|
| Claude (claude.ai) | AI assistant for architecture design, debugging, ethical analysis, and iterative development review |
| GitHub Copilot (VS Code) | In-editor code completion and suggestions |
| Anthropic Claude API | Runtime — generates research memos and analyzes news sentiment |

> The developer led all product decisions, testing, and ethical analysis.
> AI tools assisted but did not replace human judgment.

---

## Ethical Safeguards

- ✅ Practice mode only — no real money or live trading
- ✅ Cannot buy or sell real stocks
- ✅ AI confidence limited to 85% maximum to prevent overconfidence
- ✅ Trading fees included in all simulated results
- ✅ Signals use previous day's data to prevent look-ahead bias
- ✅ Analysis method always disclosed (Claude AI vs basic formula)
- ✅ All AI decisions explained in plain English (Explainable AI)
- ✅ Works for any stock — no favorites or bias toward specific tickers
- ✅ Prominent disclaimers on every page

---

## Known Limitations

- News headlines from Yahoo Finance may include general market news, not only company-specific news
- Sentiment keyword list (basic mode) was manually defined — not statistically trained
- The ±2 signal threshold and 45% confidence baseline are design choices, not optimized values
- Price data may be delayed up to 15 minutes
- Company data availability varies for small-cap stocks
