# AlphaMemo — AI Research Copilot

An educational AI application that combines market price data, financial headlines,
and technical features to generate structured investment research memos and
paper-trading signals. Built as a class project for an AI Ethics course.

**This is an educational prototype for research support and paper trading only.
It is not investment advice and does not place live trades.**

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
streamlit run app/streamlit_app.py
```

---

## What it does

1. **Fetches historical OHLCV price data** via yfinance (falls back to synthetic data)
2. **Loads financial headlines** from a local JSON dataset
3. **Computes technical features** — momentum, moving averages, volatility, volume
4. **Generates a structured research memo** — using Claude API if a key is provided,
   otherwise a transparent rule-based engine
5. **Backtests the long/neutral/short strategy** with transaction cost assumptions
6. **Displays results** in a Streamlit dashboard with charts and metrics

---

## Project Structure

```
ai-fund-manager/
├── app/
│   ├── streamlit_app.py      # Main UI
│   ├── config.py             # Settings
│   ├── data/
│   │   ├── market_data.py    # Price data loader
│   │   └── text_data.py      # Headlines loader
│   ├── features/
│   │   └── technicals.py     # Feature engineering
│   ├── llm/
│   │   ├── summarize.py      # Memo generator (Claude API + fallback)
│   │   └── stance_engine.py  # Rule-based signal scoring
│   └── backtest/
│       ├── strategy.py       # Position logic
│       └── metrics.py        # Performance metrics
├── data/
│   └── eval/
│       └── sample_news.json  # Sample financial headlines
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
| yfinance | Historical market data |
| pandas / numpy | Data processing |
| plotly | Interactive charts |
| Anthropic Claude API | LLM memo generation |
| Claude (claude.ai) | AI coding assistance |

---

## AI Tools Disclosure

This project was developed with assistance from:
- **Claude (Anthropic)** — used for code generation, architecture suggestions, and debugging
- **Anthropic Claude API** — used at runtime to generate structured research memos

The rule-based stance engine and backtest logic were reviewed and validated manually.
All ethical safeguards (paper trading only, confidence caps, cost assumptions,
look-ahead bias prevention) were explicitly designed and verified by the developer.

---

## Ethical Safeguards

- ✅ Paper trading only — no live brokerage integration
- ✅ Prominent disclaimers on every page
- ✅ Confidence capped at 85% to prevent overconfidence
- ✅ Transaction costs included in all backtest results
- ✅ Positions shifted one day forward to prevent look-ahead bias
- ✅ Memo source disclosed (Claude API vs rule-based)
- ✅ Strategy rules shown in plain language for transparency
