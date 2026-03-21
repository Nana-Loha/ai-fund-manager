from __future__ import annotations

import json
import os
import urllib.request

from app.llm.stance_engine import score_features, stance_from_score
from app.config import ANTHROPIC_API_KEY


def build_memo(ticker: str, headlines: list[str], snapshot: dict[str, float]) -> dict:
    """
    Build a structured investment research memo.
    If API key available: Claude scores sentiment AND writes memo in one call.
    Fallback: keyword-based sentiment + rule-based memo.
    """
    api_key = ANTHROPIC_API_KEY or os.environ.get("ANTHROPIC_API_KEY", "")
    feature_score = score_features(snapshot)

    if api_key:
        # Claude handles BOTH sentiment scoring AND memo writing in one API call
        result = _call_claude_full(ticker, headlines, snapshot, feature_score, api_key)
        text_score    = result.get("sentiment_score", 0)
        total_score   = text_score + feature_score
        stance        = stance_from_score(total_score)
        confidence    = min(0.85, 0.45 + abs(total_score) * 0.08)
        llm_analysis  = result
        memo_source   = "claude-api"
        found_positive = result.get("positive_words_found", [])
        found_negative = result.get("negative_words_found", [])
    else:
        # Fallback: keyword-based scoring
        from app.llm.stance_engine import score_text
        text_score    = score_text(headlines)
        total_score   = text_score + feature_score
        stance        = stance_from_score(total_score)
        confidence    = min(0.85, 0.45 + abs(total_score) * 0.08)
        llm_analysis  = _rule_based_analysis(ticker, headlines, snapshot, stance, confidence)
        memo_source   = "rule-based"
        found_positive = []
        found_negative = []
        for headline in headlines:
            words = {token.strip(".,:;!?").lower() for token in headline.split()}
            found_positive += list(words & POSITIVE_WORDS)
            found_negative += list(words & NEGATIVE_WORDS)

    memo = {
        "ticker":       ticker.upper(),
        "stance":       stance,
        "confidence":   round(confidence, 2),
        "thesis":       llm_analysis.get("thesis", []),
        "catalysts":    llm_analysis.get("catalysts", []),
        "risks":        llm_analysis.get("risks", []),
        "feature_summary": {
            "momentum":   f"20-day return {snapshot['return_20d']:.1%}",
            "trend":      f"Price vs MA50 {snapshot['ma_50_gap']:.1%}, price vs MA200 {snapshot['ma_200_gap']:.1%}",
            "volume":     f"Volume change vs 20-day average {snapshot['volume_change']:.1%}",
            "volatility": f"20-day annualized volatility {snapshot['volatility_20d']:.1%}",
        },
        "paper_trade_action": _paper_trade_action(stance, confidence),
        "memo_source":  memo_source,
        "risk_note":    "Educational prototype for paper trading only. Not investment advice.",
        "scores": {
            "text_score":    text_score,
            "feature_score": feature_score,
            "total_score":   total_score,
        },
        # For XAI display — actual words found (Claude-detected or empty for fallback)
        "found_positive": found_positive,
        "found_negative": found_negative,
        "sentiment_source": "claude-ai" if api_key else "keyword-list",
    }
    return memo


def _call_claude_full(
    ticker: str,
    headlines: list[str],
    snapshot: dict[str, float],
    feature_score: int,
    api_key: str,
) -> dict:
    """
    Single Claude API call that does BOTH:
    1. Sentiment scoring of headlines (replaces keyword list)
    2. Memo generation (thesis, catalysts, risks)
    """
    headline_text = "\n".join(f"- {h}" for h in headlines)

    prompt = f"""You are a quantitative research analyst. Analyze the following data for {ticker.upper()}.

RECENT HEADLINES:
{headline_text}

MARKET FEATURES:
- 20-day return: {snapshot['return_20d']:.1%}
- Annualized volatility: {snapshot['volatility_20d']:.1%}
- Price vs 50-day MA: {snapshot['ma_50_gap']:.1%}
- Price vs 200-day MA: {snapshot['ma_200_gap']:.1%}
- Volume change vs 20-day avg: {snapshot['volume_change']:.1%}
- Trend signal (0-2): {snapshot['trend_signal']:.0f}
- Technical feature score (already computed): {feature_score:+d}

TASK: Return ONLY a valid JSON object with NO markdown, NO preamble.

{{
  "sentiment_score": <integer: positive headline sentiment score. Count meaningful positive signals (earnings beat, revenue growth, new product, partnership, upgrade, expansion) as +1 each. Count meaningful negative signals (miss, lawsuit, investigation, decline, downgrade, loss, layoffs) as -1 each. Net total.>,
  "positive_words_found": ["<exact phrase or word from headline that is positive>", ...],
  "negative_words_found": ["<exact phrase or word from headline that is negative>", ...],
  "sentiment_reasoning": "<1 sentence explaining the overall headline tone>",
  "thesis": ["<sentence 1 about overall setup>", "<sentence 2>"],
  "catalysts": ["<what could drive price up 1>", "<catalyst 2>", "<catalyst 3>"],
  "risks": ["<what could go wrong 1>", "<risk 2>", "<risk 3>"]
}}

Rules:
- sentiment_score must be an integer (e.g. -2, 0, 3)
- positive_words_found and negative_words_found: list actual phrases from headlines, not generic words
- Use only the provided data. Do not invent facts.
- Do not provide personal financial advice.
- Keep each item to one clear sentence.
"""

    payload = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 800,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data      = json.loads(resp.read().decode("utf-8"))
            raw_text  = data["content"][0]["text"].strip()
            if raw_text.startswith("```"):
                raw_text = raw_text.split("```")[1]
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:]
            result = json.loads(raw_text)
            # Ensure sentiment_score is int
            result["sentiment_score"] = int(result.get("sentiment_score", 0))
            return result
    except Exception as e:
        # Graceful fallback
        from app.llm.stance_engine import score_text
        return {
            "sentiment_score":    score_text(headlines),
            "positive_words_found": [],
            "negative_words_found": [],
            "sentiment_reasoning": "Fallback to keyword scoring due to API error.",
            "thesis":    [f"{ticker.upper()} analysis based on available market data."],
            "catalysts": ["See technical feature snapshot for details."],
            "risks":     ["API error occurred — memo is rule-based fallback."],
        }


def _rule_based_analysis(
    ticker: str,
    headlines: list[str],
    snapshot: dict[str, float],
    stance: str,
    confidence: float,
) -> dict:
    """Fallback rule-based memo generation (no API key required)."""
    thesis = [
        f"{ticker.upper()} shows a {stance} setup based on blended market features and headline tone.",
        f"20-day return is {snapshot['return_20d']:.1%} with annualized volatility at {snapshot['volatility_20d']:.1%}.",
    ]
    catalysts = []
    if snapshot["return_20d"] > 0:
        catalysts.append("Recent momentum is positive over the last 20 trading days.")
    if snapshot["ma_50_gap"] > 0:
        catalysts.append("Price is trading above the 50-day moving average.")
    if snapshot["volume_change"] > 0.2:
        catalysts.append("Volume is elevated, which may confirm the current move.")
    catalysts.extend(headlines[:2])
    catalysts = catalysts[:3] or ["No clear positive catalysts detected."]

    risks = []
    if snapshot["volatility_20d"] > 0.35:
        risks.append("Short-term volatility is elevated and could weaken conviction.")
    if snapshot["ma_200_gap"] < 0:
        risks.append("Longer-term trend remains fragile relative to the 200-day moving average.")
    for headline in headlines:
        if any(t in headline.lower() for t in ("risk", "lawsuit", "pressure", "slowdown", "cuts", "miss", "investigation", "drop", "fall", "behind")):
            risks.append(headline)
            if len(risks) >= 3:
                break
    risks = risks[:3] or ["Headline flow is limited; signal may be unstable."]
    return {"thesis": thesis, "catalysts": catalysts, "risks": risks}


def _paper_trade_action(stance: str, confidence: float) -> str:
    if stance == "bullish":
        return "long_small" if confidence < 0.65 else "long"
    if stance == "bearish":
        return "short_small" if confidence < 0.65 else "short"
    return "hold"
