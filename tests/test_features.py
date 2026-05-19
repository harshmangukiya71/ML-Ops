"""
Unit tests for feature engineering.
"""

import numpy as np
import pandas as pd
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.data.features import (
    compute_rsi,
    rank_transform,
    build_features_spt,
    build_features_functional_spt,
)


@pytest.fixture
def sample_prices():
    np.random.seed(42)
    dates = pd.date_range("2010-01-01", periods=200, freq="B")
    data = np.random.lognormal(mean=0, sigma=0.01, size=(200, 5)).cumprod(axis=0) * 100
    return pd.DataFrame(data, index=dates, columns=["A", "B", "C", "D", "E"])


def test_compute_rsi_shape(sample_prices):
    rsi = compute_rsi(sample_prices, window=14)
    assert rsi.shape == sample_prices.shape, "RSI must have same shape as input"


def test_compute_rsi_range(sample_prices):
    rsi = compute_rsi(sample_prices, window=14).dropna()
    assert (rsi >= 0).all().all(), "RSI must be >= 0"
    assert (rsi <= 1).all().all(), "RSI must be <= 1"


def test_rank_transform_row_bounds(sample_prices):
    ranked = rank_transform(sample_prices, alpha=2.0)
    daily_max = ranked.max(axis=1)
    assert (daily_max <= 1.0 + 1e-9).all(), "Rank max must be <= 1"
    assert (ranked.min(axis=1) >= 0).all(), "Rank min must be >= 0"


def test_build_features_spt_returns_aligned(sample_prices):
    features, returns = build_features_spt(sample_prices)
    assert set(features.index) == set(returns.index), "Features and returns must be aligned"


def test_build_features_spt_column_count(sample_prices):
    features, _ = build_features_spt(sample_prices)
    # 8 features × 5 stocks = 40 columns
    assert features.shape[1] == 8 * len(sample_prices.columns)


def test_build_features_spt_no_nan(sample_prices):
    features, returns = build_features_spt(sample_prices)
    assert not features.isnull().all(axis=1).any(), "Fully-NaN rows should be dropped"


def test_build_features_functional_spt(sample_prices):
    result = build_features_functional_spt(
        sample_prices,
        use_garch=False,   # skip GARCH in unit tests
    )
    assert "x" in result
    assert "returns" in result
    assert "mu" in result
    assert "garch_rank" in result

    x = result["x"].dropna()
    mu = result["mu"].loc[x.index]

    # Market weights must sum to 1 per day
    row_sums = mu.sum(axis=1)
    assert (abs(row_sums - 1.0) < 1e-6).all(), "Market weights must sum to 1"
