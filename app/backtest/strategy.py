from __future__ import annotations

import pandas as pd


def build_positions(feature_df: pd.DataFrame) -> pd.Series:
    positions = pd.Series(0.0, index=feature_df.index)
    bullish = (
        (feature_df["return_20d"] > 0.03)
        & (feature_df["Close"] > feature_df["ma_50"])
        & (feature_df["Close"] > feature_df["ma_200"])
    )
    bearish = (
        (feature_df["return_20d"] < -0.03)
        & (feature_df["Close"] < feature_df["ma_50"])
        & (feature_df["Close"] < feature_df["ma_200"])
    )
    positions[bullish] = 1.0
    positions[bearish] = -1.0
    return positions.ffill().fillna(0.0)


def run_backtest(feature_df: pd.DataFrame, transaction_cost_bps: float = 10) -> pd.DataFrame:
    df = feature_df.copy()
    df["position"] = build_positions(df).shift(1).fillna(0.0)
    df["asset_return"] = df["Close"].pct_change().fillna(0.0)
    df["turnover"] = df["position"].diff().abs().fillna(0.0)
    cost = df["turnover"] * (transaction_cost_bps / 10_000)
    df["strategy_return"] = df["position"] * df["asset_return"] - cost
    df["equity_curve"] = (1 + df["strategy_return"]).cumprod()
    df["benchmark_curve"] = (1 + df["asset_return"]).cumprod()
    return df
