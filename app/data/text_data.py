from __future__ import annotations

import json
from pathlib import Path

from app.config import EVAL_DIR, ensure_ssl_ca_bundle


def load_text_bundle(ticker: str) -> list[str]:
    """
    Try to fetch real headlines from yfinance first.
    Falls back to sample_news.json if yfinance has no news.
    """
    ticker = ticker.upper().strip()

    # ── Try yfinance news first ───────────────────────────────────────────────
    try:
        ensure_ssl_ca_bundle()
        import yfinance as yf
        stock = yf.Ticker(ticker)
        news = stock.news
        if news and len(news) > 0:
            headlines = []
            for item in news[:5]:  # take top 5 articles
                # yfinance news structure varies by version
                content = item.get("content", {})
                title = (
                    content.get("title")
                    or item.get("title")
                    or item.get("headline")
                    or ""
                )
                if title:
                    headlines.append(title)
            if headlines:
                return headlines
    except Exception:
        pass

    # ── Fallback to sample_news.json ─────────────────────────────────────────
    path = Path(EVAL_DIR) / "sample_news.json"
    try:
        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        bundle = payload.get(ticker)
        if bundle:
            return bundle
        return payload["DEFAULT"]
    except Exception:
        return [
            "No recent headlines available for this ticker.",
            "Consider checking financial news sources for the latest updates.",
        ]
