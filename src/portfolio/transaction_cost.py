"""
Transaction cost module.
Cost is charged only on rebalance days, not daily.
"""

import logging
from typing import Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def apply_transaction_cost(
    portfolio_returns: pd.Series,
    weights:           pd.DataFrame,
    cost_rate:         float = 0.001,
    holding_days:      int   = 21,
) -> Tuple[pd.Series, pd.Series]:
    """
    Subtract transaction costs from portfolio returns.
    Cost is only charged on rebalance days (every holding_days).

    Parameters
    ----------
    portfolio_returns : gross daily return series
    weights           : rebalanced weight DataFrame
    cost_rate         : fraction of turnover charged (e.g. 0.001 = 0.1%)
    holding_days      : rebalance frequency in days

    Returns
    -------
    (net_returns, turnover_series)
    """
    # Turnover = sum of absolute weight changes
    turnover = weights.diff().abs().sum(axis=1)

    # Charge only on rebalance days
    trade_mask = np.zeros(len(turnover))
    trade_mask[::holding_days] = 1
    turnover = (turnover * trade_mask).fillna(0)

    transaction_cost = cost_rate * turnover
    transaction_cost = transaction_cost.reindex(portfolio_returns.index).fillna(0)

    net_returns = portfolio_returns - transaction_cost

    avg_turnover  = float(turnover[turnover > 0].mean())
    total_cost    = float(transaction_cost.sum())
    logger.info(
        "Transaction cost applied — rate=%.3f%% | avg rebalance turnover=%.4f | total cost drag=%.4f",
        cost_rate * 100, avg_turnover, total_cost,
    )
    return net_returns, turnover
