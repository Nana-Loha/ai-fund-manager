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

## 🛠️ Design & Development Process

### Tools Used

| Tool | Purpose |
|------|---------|
| Python 3.11 | Core language |
| Streamlit | Web UI framework |
| yfinance | Real-time stock prices and news |
| pandas / numpy | Data processing |
| plotly | Interactive charts |
| Anthropic Claude API | AI memo generation and news sentiment analysis |

### Steps Taken

1. **Defined the problem** — identified what a fund manager needs: price data, news, and signals
2. **Designed the architecture** — modular structure with separate layers for data, features, LLM, and backtesting
3. **Built the data pipeline** — connected Yahoo Finance for prices and headlines
4. **Added technical indicators** — momentum, moving averages, volatility, volume signals
5. **Integrated Claude API** — for AI-generated memos, with a rule-based fallback when no API key is provided
6. **Built the backtest engine** — to simulate past performance with trading fees
7. **Deployed to Streamlit Cloud** — for easy public access

### Learning Curve

The biggest challenge was building a reliable fallback system — the app needed to work even without a Claude API key. This required designing a transparent rule-based formula that mirrors the AI's logic in a simpler form.

### Pros & Cons of Using AI Tools for Development

| Pros | Cons |
|------|------|
| Faster architecture decisions | Risk of over-relying on AI suggestions |
| Faster debugging | Some suggestions needed validation before use |
| Better code structure ideas | AI didn't always understand project-specific context |
| Helped write documentation | Required careful human review at every step |

> All product decisions, testing, and ethical analysis were led by the developer. AI tools assisted but did not replace human judgment.

---

## ⚖️ Ethical Impact Analysis

### Potential Harms

- **Over-reliance on AI signals** — Users may treat AI-generated memos as financial advice and make real monetary decisions based on them, leading to financial loss
- **Algorithmic bias** — The sentiment keyword list (basic mode) was manually defined and may unintentionally favor certain market narratives over others
- **Misinformation risk** — Yahoo Finance news may include general market news unrelated to the specific stock, potentially skewing sentiment analysis
- **Accessibility gap** — Users without financial literacy may misinterpret confidence scores as guarantees rather than estimates
- **Data delay risk** — Price data may be delayed up to 15 minutes, which could mislead users into thinking they have real-time information

### Who Is Most at Risk

Students, beginner investors, and users unfamiliar with the limitations of AI in financial contexts are most vulnerable to misinterpreting the app's outputs as reliable investment advice.

---

## 🔒 Data Privacy & Collection

- **No personal data is collected** — the app does not ask for names, emails, or account information
- **No data is stored** — all analysis is done in-session and discarded when the user closes the app
- **API key handling** — the Anthropic API key is entered locally by the user and sent only directly to Anthropic's servers; it is never logged or stored by this app
- **Public data only** — all stock prices and news headlines are sourced from Yahoo Finance's publicly available data
- **No tracking** — the app does not use cookies, analytics, or user tracking of any kind

---

## 🛡️ Ethical Mitigation Strategies

| Risk | Mitigation |
|------|-----------|
| Users treating signals as financial advice | Prominent disclaimers on every page; app described as educational only |
| AI overconfidence | AI confidence capped at 85% maximum to prevent false certainty |
| Look-ahead bias in backtesting | Signals use only previous day's data |
| Hidden methodology | Analysis method always disclosed — users can see whether Claude AI or the basic formula generated the result |
| Unfair fee assumptions | Trading fees included in all simulated results to reflect realistic costs |
| Lack of explainability | All AI decisions explained in plain English (Explainable AI principle) |
| Ticker bias | App works for any valid stock ticker — no favorites or hardcoded preferences |

---

## 🔮 Future Considerations & Scalability

### Short-Term Improvements
- Replace the manually-defined sentiment keyword list with a statistically trained sentiment model (e.g., FinBERT)
- Add support for portfolio-level analysis across multiple stocks simultaneously
- Improve news filtering to return only company-specific headlines, not general market news

### Long-Term Scalability
- Integrate SEC filings (10-K, 10-Q) for deeper fundamental analysis alongside technical signals
- Add user authentication to allow saving and comparing research memos over time
- Support international markets and currencies beyond US equities
- Build an API layer so other developers can integrate AlphaMemo's signals into their own tools

### Ethical Considerations for Scaling
- If this app were to serve a large user base, independent auditing of AI signal accuracy would be required
- A feedback mechanism should be added so users can report misleading or harmful outputs
- Regulatory compliance (e.g., SEC disclaimer requirements) would need to be reviewed before any commercial deployment

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
