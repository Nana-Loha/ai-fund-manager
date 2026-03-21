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

## 🚀 Open the App

The app is live and ready to use — no installation needed.

🔗 **[Open AlphaMemo on Streamlit Cloud](https://ai-fund-manager-bplg9p6xjaezrfjcwjhwt7.streamlit.app/)**

### How to use:
1. Open the link above in your browser
2. Enter a stock ticker (e.g. `AAPL`, `TSLA`, `NVDA`) in the sidebar
3. *(Optional)* Enter your Anthropic API key in the sidebar to enable AI-powered memos
4. Click **"Analyze"** to generate your research memo

---

## 📋 Project Definition & Scope

**AlphaMemo** is an educational tool designed to simulate how an AI-assisted fund manager might analyze stocks. It is built for students and learners who want to understand how AI can be applied to financial research — without the risks of real investing.

**Core features:**
- Fetches real stock price data via Yahoo Finance (yfinance)
- Loads recent news headlines from Yahoo Finance
- Computes technical signals — momentum, moving averages, volatility, volume
- Generates a structured research memo using Claude API (or a transparent rule-based fallback)
- Simulates historical strategy performance with trading fee assumptions
- Displays results in a Streamlit dashboard with plain-English explanations

**Out of scope:** This app cannot place real trades, manage real money, or connect to brokerage accounts.

---

### Tools Used

| Tool | Purpose |
|------|---------|
| Python 3.11 | Core language |
| Streamlit | Web UI framework |
| yfinance | Real-time stock prices and news |
| pandas / numpy | Data processing |
| plotly | Interactive charts |
| Anthropic Claude API | AI memo generation and news sentiment analysis |


---

## 📁 Project Structure

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

## 🤖 AI Tools Disclosure

| Tool | Role |
|------|------|
| Claude (claude.ai) | AI assistant for architecture design, debugging, ethical analysis, and iterative development review |
| GitHub Copilot (VS Code) | In-editor code completion and suggestions |
| Anthropic Claude API | Runtime — generates research memos and analyzes news sentiment |

> The developer led all product decisions, testing, and ethical analysis.
> AI tools assisted but did not replace human judgment.

---

## 📚 References

- Yang et al. (2023) — *Instruct-FinGPT: Financial Sentiment Analysis by Instruction Tuning of General-Purpose LLMs* — arXiv:2306.12659
- Kim, Muhn & Nikolaev (2024) — *Financial Statement Analysis with Large Language Models* — arXiv:2407.17866
- Investopedia — Technical Analysis — https://www.investopedia.com/terms/t/technicalanalysis.asp

---

## ✅ Known Limitations

- News headlines from Yahoo Finance may include general market news, not only company-specific news
- Sentiment keyword list (basic mode) was manually defined — not statistically trained
- The ±2 signal threshold and 45% confidence baseline are design choices, not optimized values
- Price data may be delayed up to 15 minutes
- Company data availability varies for small-cap stocks
