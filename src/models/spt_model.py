"""
SPT CNN Ranker Model.

Deep MLP that takes per-stock feature vectors and outputs
softmax portfolio weights optimized for Sharpe ratio.
"""

import logging
from pathlib import Path
from typing import Dict, Optional

import torch
import torch.nn as nn

logger = logging.getLogger(__name__)


class SPTModel(nn.Module):
    """
    Stock Portfolio Transformer — MLP Ranker.

    Input  : (T, N, F)  — T timesteps, N stocks, F features
    Output : (T, N)     — portfolio weights summing to 1 per day
    """

    def __init__(self, n_features: int = 8, hidden_dims=(64, 32), dropout: float = 0.2):
        super().__init__()
        layers = []
        in_dim = n_features
        for h in hidden_dims:
            layers += [
                nn.Linear(in_dim, h),
                nn.BatchNorm1d(h),
                nn.ReLU(),
                nn.Dropout(dropout),
            ]
            in_dim = h
        layers.append(nn.Linear(in_dim, 1))
        self.net = nn.Sequential(*layers)

    def forward(self, X: torch.Tensor) -> torch.Tensor:
        T, N, F = X.shape
        X_flat  = X.reshape(T * N, F)
        scores  = self.net(X_flat).reshape(T, N)
        return torch.softmax(scores, dim=1)

    # ----------------------------------------------------------
    # Checkpoint helpers
    # ----------------------------------------------------------

    def save(self, path: str, metadata: Optional[Dict] = None) -> None:
        """Save model weights + optional metadata dict."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "state_dict": self.state_dict(),
            "metadata":   metadata or {},
        }
        torch.save(payload, path)
        logger.info("SPTModel saved → %s", path)

    @classmethod
    def load(cls, path: str, **model_kwargs) -> "SPTModel":
        """Load model from checkpoint."""
        payload = torch.load(path, map_location="cpu", weights_only=False)
        meta    = payload.get("metadata", {})

        # Reconstruct from metadata if available, else use kwargs
        n_features  = meta.get("n_features",  model_kwargs.get("n_features", 8))
        hidden_dims = meta.get("hidden_dims",  model_kwargs.get("hidden_dims", (64, 32)))
        dropout     = meta.get("dropout",      model_kwargs.get("dropout", 0.2))

        model = cls(n_features=n_features, hidden_dims=hidden_dims, dropout=dropout)
        model.load_state_dict(payload["state_dict"])
        model.eval()
        logger.info("SPTModel loaded ← %s | metadata: %s", path, meta)
        return model
