"""
Portfolio evaluation metrics.
Pure functions — no side effects.
"""

import logging
from typing import Dict

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def max_drawdown(returns_series: pd.Series) -> float:
    """Maximum drawdown from a returns series."""
    cumulative  = (1 + returns_series).cumprod()
    rolling_max = cumulative.cummax()
    drawdown    = (cumulative - rolling_max) / rolling_max
    return float(drawdown.min())


def compute_metrics(returns: pd.DataFrame) -> pd.DataFrame:
    """
    Compute annualized performance metrics for each strategy column.

    Parameters
    ----------
    returns : pd.DataFrame  (date × strategy)

    Returns
    -------
    pd.DataFrame  (metric × strategy)
    """
    annual_return = returns.mean() * 252
    annual_vol    = returns.std() * np.sqrt(252)
    sharpe        = annual_return / (annual_vol + 1e-8)
    geo           = np.log(1 + returns).mean() * 252
    max_dd        = returns.apply(max_drawdown)

    summary = pd.DataFrame(
        {
            "Arithmetic Return": annual_return,
            "Geometric Return":  geo,
            "Volatility":        annual_vol,
            "Sharpe":            sharpe,
            "Max Drawdown":      max_dd,
        }
    ).sort_values("Sharpe", ascending=False)

    logger.info("Performance metrics:\n%s", summary.round(4).to_string())
    return summary


def growth_of_one(returns: pd.DataFrame) -> pd.DataFrame:
    """Convert returns to cumulative wealth starting at ₹1."""
    wealth = (1 + returns).cumprod()
    return wealth / wealth.iloc[0]


def assert_sharpe_threshold(sharpe: float, threshold: float, strategy: str = "") -> None:
    """
    Raise ValueError if Sharpe is below threshold.
    Used by CI/CD to fail the build on model regression.
    """
    if sharpe < threshold:
        msg = (
            f"[CI FAIL] {strategy} Sharpe {sharpe:.4f} < "
            f"threshold {threshold:.4f}"
        )
        logger.error(msg)
        raise ValueError(msg)
    logger.info("[CI PASS] %s Sharpe %.4f ≥ threshold %.4f", strategy, sharpe, threshold)
