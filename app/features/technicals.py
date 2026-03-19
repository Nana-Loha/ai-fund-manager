from __future__ import annotations

import pandas as pd

from app.config import TRADING_DAYS


def add_features(prices: pd.DataFrame) -> pd.DataFrame:
    df = prices.copy()
    df["return_1d"] = df["Close"].pct_change()
    df["return_20d"] = df["Close"].pct_change(20)
    df["ma_20"] = df["Close"].rolling(20).mean()
    df["ma_50"] = df["Close"].rolling(50).mean()
    df["ma_200"] = df["Close"].rolling(200).mean()
    df["volatility_20d"] = df["return_1d"].rolling(20).std() * (TRADING_DAYS ** 0.5)
    df["volume_avg_20"] = df["Volume"].rolling(20).mean()
    df["volume_change"] = df["Volume"] / df["volume_avg_20"] - 1
    df["trend_signal"] = (
        (df["Close"] > df["ma_50"]).astype(int) + (df["ma_50"] > df["ma_200"]).astype(int)
    )
    return df


def latest_feature_snapshot(feature_df: pd.DataFrame) -> dict[str, float]:
    latest = feature_df.dropna().iloc[-1]
    return {
        "close": float(latest["Close"]),
        "return_20d": float(latest["return_20d"]),
        "volatility_20d": float(latest["volatility_20d"]),
        "ma_50_gap": float(latest["Close"] / latest["ma_50"] - 1),
        "ma_200_gap": float(latest["Close"] / latest["ma_200"] - 1),
        "volume_change": float(latest["volume_change"]),
        "trend_signal": float(latest["trend_signal"]),
    }
