from __future__ import annotations

import numpy as np
import pandas as pd

from app.config import TRADING_DAYS


def compute_metrics(backtest_df: pd.DataFrame) -> dict[str, float]:
    returns = backtest_df["strategy_return"]
    benchmark = backtest_df["asset_return"]
    equity = backtest_df["equity_curve"]

    sharpe = 0.0
    if returns.std() > 0:
        sharpe = (returns.mean() / returns.std()) * np.sqrt(TRADING_DAYS)

    drawdown = equity / equity.cummax() - 1

    return {
        "strategy_return": float(equity.iloc[-1] - 1),
        "benchmark_return": float((1 + benchmark).cumprod().iloc[-1] - 1),
        "sharpe": float(sharpe),
        "max_drawdown": float(drawdown.min()),
        "hit_rate": float((returns > 0).mean()),
        "turnover": float(backtest_df["turnover"].mean() * TRADING_DAYS),
    }
