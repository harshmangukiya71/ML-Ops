"""
Unit tests for evaluate and metrics_store modules.
"""

import json
import sys
import os
import tempfile

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.training.evaluate import compute_metrics, max_drawdown, assert_sharpe_threshold
from src.utils.metrics_store import MetricsStore


@pytest.fixture
def sample_returns():
    np.random.seed(7)
    dates = pd.date_range("2021-01-01", periods=250, freq="B")
    data = {
        "Strategy A": np.random.normal(0.0005, 0.01, 250),
        "Strategy B": np.random.normal(0.0002, 0.015, 250),
    }
    return pd.DataFrame(data, index=dates)


def test_compute_metrics_shape(sample_returns):
    metrics = compute_metrics(sample_returns)
    assert set(metrics.index) == {"Strategy A", "Strategy B"}
    assert "Sharpe" in metrics.columns
    assert "Max Drawdown" in metrics.columns


def test_compute_metrics_sharpe_positive(sample_returns):
    metrics = compute_metrics(sample_returns)
    # Strategy A has positive mean → Sharpe should be positive
    assert metrics.loc["Strategy A", "Sharpe"] > 0


def test_max_drawdown_is_negative(sample_returns):
    dd = max_drawdown(sample_returns["Strategy A"])
    assert dd <= 0, "Max drawdown must be <= 0"


def test_max_drawdown_all_positive():
    # Monotonically rising returns → near-zero drawdown
    returns = pd.Series([0.01] * 100)
    dd = max_drawdown(returns)
    assert dd >= -1e-6, "Monotonically positive returns should have ~0 drawdown"


def test_assert_sharpe_passes():
    assert_sharpe_threshold(1.5, 1.0, "Test")   # Should not raise


def test_assert_sharpe_fails():
    with pytest.raises(ValueError, match="CI FAIL"):
        assert_sharpe_threshold(0.3, 1.0, "Test")


def test_metrics_store_roundtrip():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = MetricsStore(run_id="test123", metrics_dir=tmpdir)
        store.log("sharpe", 1.234)
        store.log("volatility", 0.15)
        fpath = store.save()

        with open(fpath) as f:
            data = json.load(f)

        assert data["run_id"] == "test123"
        assert data["metrics"]["sharpe"] == 1.234
        assert data["metrics"]["volatility"] == 0.15
