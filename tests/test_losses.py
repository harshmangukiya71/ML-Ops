"""
Unit tests for loss functions.
"""

import sys
import os
import pytest
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.training.losses import sharpe_loss, improved_objective, smoothness_penalty
from src.models.spt_model import SPTModel
from src.models.functional_spt import FunctionalSPT


T, N, F = 100, 5, 8   # small tensors for speed


@pytest.fixture
def random_weights_returns():
    torch.manual_seed(0)
    raw_w = torch.softmax(torch.randn(T, N), dim=1)
    returns = torch.randn(T, N) * 0.01
    return raw_w, returns


@pytest.fixture
def spt_model():
    return SPTModel(n_features=F, hidden_dims=(16, 8), dropout=0.0)


@pytest.fixture
def fspt_model():
    return FunctionalSPT(hidden_dim=8, output_dim=4)


def test_sharpe_loss_is_scalar(random_weights_returns, spt_model):
    w, r = random_weights_returns
    loss = sharpe_loss(w, r, spt_model)
    assert loss.shape == torch.Size([]), "sharpe_loss must return a scalar"


def test_sharpe_loss_is_finite(random_weights_returns, spt_model):
    w, r = random_weights_returns
    loss = sharpe_loss(w, r, spt_model)
    assert torch.isfinite(loss), "sharpe_loss must be finite"


def test_sharpe_loss_backward(random_weights_returns, spt_model):
    X = torch.randn(T, N, F)
    r = torch.randn(T, N) * 0.01
    w = spt_model(X)
    loss = sharpe_loss(w, r, spt_model)
    loss.backward()   # must not raise
    for p in spt_model.parameters():
        assert p.grad is not None, "All params should have gradients"


def test_improved_objective_is_scalar(random_weights_returns):
    w, r = random_weights_returns
    mu = torch.softmax(torch.randn(T, N), dim=1)
    obj = improved_objective(w, r, mu)
    assert obj.shape == torch.Size([]), "improved_objective must return a scalar"


def test_improved_objective_is_finite(random_weights_returns):
    w, r = random_weights_returns
    mu = torch.softmax(torch.randn(T, N), dim=1)
    obj = improved_objective(w, r, mu)
    assert torch.isfinite(obj), "improved_objective must be finite"


def test_smoothness_penalty(fspt_model):
    x = torch.rand(T, N)
    pen = smoothness_penalty(fspt_model, x)
    assert pen.shape == torch.Size([]), "smoothness_penalty must return a scalar"
    assert pen >= 0, "smoothness_penalty must be non-negative"
