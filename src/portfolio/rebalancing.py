"""
Portfolio rebalancing with volatility targeting.
"""

import logging
from typing import Optional, Tuple

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

logger = logging.getLogger(__name__)


def apply_rebalancing_spt(
    model:          nn.Module,
    X_test_t:       torch.Tensor,
    R_test_t:       torch.Tensor,
    test_dates:     list,
    rebalance_freq: int   = 21,
    min_weight:     float = 0.02,
    max_weight:     float = 0.20,
) -> Tuple[pd.Series, pd.DataFrame]:
    """
    Apply SPT Model weights with periodic rebalancing and position constraints.

    Returns
    -------
    (portfolio_returns_series, weights_dataframe)
    """
    with torch.no_grad():
        daily_weights = model(X_test_t).numpy()

    # Hold weights for rebalance_freq days
    monthly_weights = []
    for i in range(0, len(daily_weights), rebalance_freq):
        w = daily_weights[i]
        repeat_block = np.tile(w, (rebalance_freq, 1))
        monthly_weights.append(repeat_block)

    weights_np = np.vstack(monthly_weights)[: len(daily_weights)]

    # Position constraints
    weights_np = np.clip(weights_np, min_weight, max_weight)
    weights_np = weights_np / weights_np.sum(axis=1, keepdims=True)

    R_test_np = R_test_t.numpy()
    returns   = np.sum(weights_np * R_test_np, axis=1)

    port_series = pd.Series(returns, index=test_dates)
    weights_df  = pd.DataFrame(weights_np, index=test_dates)

    logger.info(
        "SPT rebalancing complete — %d days, freq=%d",
        len(port_series), rebalance_freq,
    )
    return port_series, weights_df


def apply_rebalancing_functional(
    model:         nn.Module,
    x_data:        pd.DataFrame,
    returns_data:  pd.DataFrame,
    market_weights: pd.DataFrame,
    garch_data:    Optional[pd.DataFrame] = None,
    holding_days:  int   = 21,
    vol_target:    float = 0.15,
    vol_min_scale: float = 0.5,
    vol_max_scale: float = 2.0,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Apply Functional SPT weights with optional GARCH adjustment,
    periodic rebalancing, and volatility targeting.

    Returns
    -------
    (comparison_df with ['Functional SPT', 'Market'], rebalanced_weights_df)
    """
    x_tensor = torch.tensor(x_data.values, dtype=torch.float32)

    garch_tensor = None
    if garch_data is not None:
        garch_tensor = torch.tensor(garch_data.values, dtype=torch.float32)

    with torch.no_grad():
        all_weights = model(x_tensor, garch_tensor).numpy()

    weights_df = pd.DataFrame(
        all_weights,
        index=x_data.index,
        columns=x_data.columns,
    )

    # Rebalance: hold for holding_days before updating
    rebalanced = weights_df.copy()
    for i in range(0, len(weights_df), holding_days):
        rebalanced.iloc[i : i + holding_days] = weights_df.iloc[i]

    port_ret   = (rebalanced.shift(1) * returns_data).sum(axis=1)
    market_ret = (market_weights.shift(1) * returns_data).sum(axis=1)

    # Volatility targeting
    realized_vol = port_ret.rolling(20).std() * np.sqrt(252)
    scaling      = (vol_target / (realized_vol + 1e-8)).clip(vol_min_scale, vol_max_scale)
    port_ret     = port_ret * scaling

    comparison = pd.concat([port_ret, market_ret], axis=1)
    comparison.columns = ["Functional SPT", "Market"]
    comparison = comparison.dropna()

    logger.info(
        "Functional SPT rebalancing complete — %d days, holding=%d, vol_target=%.2f",
        len(comparison), holding_days, vol_target,
    )
    return comparison, rebalanced
