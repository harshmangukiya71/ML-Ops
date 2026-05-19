"""
Generic Trainer class for both portfolio models.
Handles: early stopping, best-model checkpointing,
         gradient clipping, LR scheduling, epoch logging.
"""

import logging
import time
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import torch
import torch.nn as nn

logger = logging.getLogger(__name__)


class EarlyStopping:
    """Tracks improvement and signals when to stop."""

    def __init__(self, patience: int = 150, mode: str = "max"):
        self.patience = patience
        self.mode     = mode
        self.best     = float("-inf") if mode == "max" else float("inf")
        self.counter  = 0
        self.improved = False

    def step(self, value: float) -> bool:
        """Returns True if training should stop."""
        if self.mode == "max":
            improved = value > self.best
        else:
            improved = value < self.best

        if improved:
            self.best    = value
            self.counter = 0
            self.improved = True
        else:
            self.counter += 1
            self.improved = False

        return self.counter >= self.patience


class Trainer:
    """
    Generic trainer that works for both SPTModel and FunctionalSPT.

    Parameters
    ----------
    model         : nn.Module to train
    optimizer     : torch optimizer
    scheduler     : optional LR scheduler
    patience      : early stopping patience
    checkpoint_dir: where to save best model
    model_name    : used for checkpoint filename
    max_grad_norm : gradient clipping norm
    """

    def __init__(
        self,
        model:          nn.Module,
        optimizer:      torch.optim.Optimizer,
        scheduler:      Optional[Any] = None,
        patience:       int  = 150,
        checkpoint_dir: str  = "checkpoints",
        model_name:     str  = "model",
        max_grad_norm:  float = 1.0,
    ):
        self.model          = model
        self.optimizer      = optimizer
        self.scheduler      = scheduler
        self.early_stopping = EarlyStopping(patience=patience, mode="max")
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.model_name     = model_name
        self.max_grad_norm  = max_grad_norm
        self.history: List[Dict] = []

    def train(
        self,
        epochs:          int,
        loss_fn:         Callable[[], torch.Tensor],
        monitor_fn:      Callable[[], float],
        log_every:       int  = 100,
        checkpoint_meta: Optional[Dict] = None,
    ) -> Dict:
        """
        Run training loop.

        Parameters
        ----------
        epochs       : max training epochs
        loss_fn      : callable returning scalar loss (no args — capture externally)
        monitor_fn   : callable returning float to monitor for early stopping / best model
        log_every    : log every N epochs
        checkpoint_meta : extra metadata stored in checkpoint

        Returns
        -------
        dict with training summary
        """
        best_state    = deepcopy(self.model.state_dict())
        best_epoch    = 0
        start_time    = time.time()

        logger.info(
            "Training %s for up to %d epochs (patience=%d)",
            self.model_name, epochs, self.early_stopping.patience,
        )

        for epoch in range(epochs):
            self.model.train()
            self.optimizer.zero_grad()

            loss = loss_fn()
            loss.backward()

            torch.nn.utils.clip_grad_norm_(
                self.model.parameters(), max_norm=self.max_grad_norm
            )
            self.optimizer.step()
            if self.scheduler is not None:
                self.scheduler.step()

            self.model.eval()
            with torch.no_grad():
                monitored = monitor_fn()

            # Record history
            row = {
                "epoch":    epoch,
                "loss":     loss.item(),
                "monitor":  monitored,
                "lr":       self.optimizer.param_groups[0]["lr"],
            }
            self.history.append(row)

            # Early stopping
            stop = self.early_stopping.step(monitored)
            if self.early_stopping.improved:
                best_state = deepcopy(self.model.state_dict())
                best_epoch = epoch

            if epoch % log_every == 0:
                elapsed = time.time() - start_time
                logger.info(
                    "Epoch %4d | loss=%.6f | monitor=%.6f | lr=%.2e | elapsed=%.0fs",
                    epoch, loss.item(), monitored, row["lr"], elapsed,
                )

            if stop:
                logger.info("Early stopping triggered at epoch %d", epoch)
                break

        # Restore best weights
        self.model.load_state_dict(best_state)
        self.model.eval()

        elapsed_total = time.time() - start_time
        logger.info(
            "Training complete. Best epoch: %d | Best monitor: %.6f | Time: %.0fs",
            best_epoch, self.early_stopping.best, elapsed_total,
        )

        # Save checkpoint
        ckpt_path = self.checkpoint_dir / f"{self.model_name}_best.pt"
        meta = {
            "best_epoch":    best_epoch,
            "best_monitor":  self.early_stopping.best,
            "elapsed_sec":   round(elapsed_total),
            **(checkpoint_meta or {}),
        }
        if hasattr(self.model, "save"):
            self.model.save(str(ckpt_path), metadata=meta)
        else:
            torch.save({"state_dict": self.model.state_dict(), "metadata": meta}, ckpt_path)
            logger.info("Checkpoint saved → %s", ckpt_path)

        return {
            "best_epoch":   best_epoch,
            "best_monitor": self.early_stopping.best,
            "elapsed_sec":  round(elapsed_total),
            "checkpoint":   str(ckpt_path),
            "history":      self.history,
        }
