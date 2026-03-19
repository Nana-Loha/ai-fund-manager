from __future__ import annotations

import contextlib
import io
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from app.config import DATA_DIR, ensure_ssl_ca_bundle


@dataclass
class MarketDataResult:
    prices: pd.DataFrame
    source: str


def load_market_data(ticker: str, period: str = "1y") -> MarketDataResult:
    ticker = ticker.upper().strip()

    try:
        ensure_ssl_ca_bundle()
        import yfinance as yf

        cache_dir = Path(DATA_DIR) / "raw" / "yfinance_tz_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        yf.set_tz_cache_location(str(cache_dir))
        with contextlib.redirect_stderr(io.StringIO()):
            data = yf.download(ticker, period=period, auto_adjust=True, progress=False)
        data = _normalize_columns(data)
        if not data.empty:
            return MarketDataResult(prices=data, source="yfinance")
    except Exception:
        pass

    return MarketDataResult(prices=_synthetic_prices(ticker), source="synthetic")


def _normalize_columns(data: pd.DataFrame) -> pd.DataFrame:
    df = data.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]
    rename_map = {str(col): str(col).title() for col in df.columns}
    df = df.rename(columns=rename_map)
    expected = ["Open", "High", "Low", "Close", "Volume"]
    for column in expected:
        if column not in df.columns and column == "Volume":
            df[column] = 0.0
    return df[expected].dropna(subset=["Close"]).copy()


def _synthetic_prices(ticker: str) -> pd.DataFrame:
    seed = sum(ord(char) for char in ticker)
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=252)

    shocks = rng.normal(loc=0.0005, scale=0.018, size=len(dates))
    close = 100 * np.exp(np.cumsum(shocks))
    open_ = close * (1 + rng.normal(0, 0.003, size=len(dates)))
    high = np.maximum(open_, close) * (1 + rng.uniform(0.001, 0.01, size=len(dates)))
    low = np.minimum(open_, close) * (1 - rng.uniform(0.001, 0.01, size=len(dates)))
    volume = rng.integers(900_000, 5_000_000, size=len(dates))

    return pd.DataFrame(
        {
            "Open": open_,
            "High": high,
            "Low": low,
            "Close": close,
            "Volume": volume,
        },
        index=dates,
    )
