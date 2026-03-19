from __future__ import annotations


POSITIVE_WORDS = {
    "beats",
    "growth",
    "upgrade",
    "strong",
    "momentum",
    "expands",
    "profit",
    "demand",
    "record",
    "partnership",
}

NEGATIVE_WORDS = {
    "cuts",
    "investigation",
    "lawsuit",
    "weak",
    "downgrade",
    "decline",
    "risk",
    "slowdown",
    "miss",
    "pressure",
}


def score_text(headlines: list[str]) -> int:
    score = 0
    for headline in headlines:
        words = {token.strip(".,:;!?").lower() for token in headline.split()}
        score += len(words & POSITIVE_WORDS)
        score -= len(words & NEGATIVE_WORDS)
    return score


def score_features(snapshot: dict[str, float]) -> int:
    score = 0
    if snapshot["return_20d"] > 0.03:
        score += 1
    elif snapshot["return_20d"] < -0.03:
        score -= 1

    if snapshot["ma_50_gap"] > 0 and snapshot["ma_200_gap"] > 0:
        score += 1
    elif snapshot["ma_50_gap"] < 0 and snapshot["ma_200_gap"] < 0:
        score -= 1

    if snapshot["volatility_20d"] > 0.45:
        score -= 1

    if snapshot["volume_change"] > 0.25:
        score += 1
    elif snapshot["volume_change"] < -0.25:
        score -= 1

    return score


def stance_from_score(total_score: int) -> str:
    if total_score >= 2:
        return "bullish"
    if total_score <= -2:
        return "bearish"
    return "neutral"
