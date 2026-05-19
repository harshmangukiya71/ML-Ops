"""
Main training entrypoint.

Usage:
    python train.py --model spt_model --config config/spt_model.yaml
    python train.py --model functional_spt --config config/functional_spt.yaml
    python train.py --model spt_model --force-refresh   # re-download data
"""

import argparse
import logging
import random
import sys
from pathlib import Path

import numpy as np
import torch
import yaml


# ─────────────────────────────────────────────────────────────
# Argument parsing
# ─────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description="Train a portfolio ML model")
    p.add_argument(
        "--model", required=True,
        choices=["spt_model", "functional_spt"],
        help="Which model to train",
    )
    p.add_argument(
        "--config", default=None,
        help="Path to YAML config (default: config/<model>.yaml)",
    )
    p.add_argument(
        "--force-refresh", action="store_true",
        help="Force re-download of market data",
    )
    p.add_argument(
        "--log-dir", default=None,
        help="Override log directory from config",
    )
    return p.parse_args()


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def load_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


# ─────────────────────────────────────────────────────────────
# SPT Model training
# ─────────────────────────────────────────────────────────────

def train_spt(cfg: dict, force_refresh: bool, run_id: str) -> dict:
    from src.data.downloader import download_prices
    from src.data.features import build_features_spt, prepare_tensors_spt
    from src.models.spt_model import SPTModel
    from src.training.losses import sharpe_loss
    from src.training.trainer import Trainer
    from src.training.evaluate import compute_metrics, assert_sharpe_threshold
    from src.portfolio.rebalancing import apply_rebalancing_spt
    from src.portfolio.transaction_cost import apply_transaction_cost
    from src.utils.metrics_store import MetricsStore
    import pandas as pd

    log = logging.getLogger("train.spt")
    store = MetricsStore(run_id=run_id, metrics_dir=cfg["output"]["metrics_dir"])

    # ── Data ──────────────────────────────────────────────
    log.info("=== [1/5] Downloading data ===")
    prices = download_prices(
        stocks=cfg["data"]["stocks"],
        start=cfg["data"]["start_date"],
        cache_dir=cfg["data"]["cache_dir"],
        force_refresh=force_refresh,
    )

    # ── Features ──────────────────────────────────────────
    log.info("=== [2/5] Building features ===")
    features, returns = build_features_spt(prices)
    tensors = prepare_tensors_spt(
        features, returns,
        train_end=cfg["data"]["train_end"],
        test_start=cfg["data"]["test_start"],
    )

    # ── Model ─────────────────────────────────────────────
    log.info("=== [3/5] Initializing model ===")
    model = SPTModel(
        n_features=cfg["model"]["n_features"],
        hidden_dims=tuple(cfg["model"]["hidden_dims"]),
        dropout=cfg["model"]["dropout"],
    )
    log.info("Parameters: %d", sum(p.numel() for p in model.parameters()))

    optimizer = torch.optim.Adam(model.parameters(), lr=cfg["training"]["lr"])
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer,
        T_max=cfg["training"]["epochs"],
        eta_min=cfg["training"]["lr_min"],
    )

    trainer = Trainer(
        model=model,
        optimizer=optimizer,
        scheduler=scheduler,
        patience=cfg["training"]["patience"],
        checkpoint_dir=cfg["output"]["checkpoint_dir"],
        model_name="spt_model",
    )

    # ── Training ──────────────────────────────────────────
    log.info("=== [4/5] Training ===")
    X_train_t = tensors["X_train_t"]
    R_train_t = tensors["R_train_t"]

    def loss_fn():
        weights = model(X_train_t)
        return sharpe_loss(
            weights, R_train_t, model,
            l2_lambda=cfg["training"]["l2_lambda"],
            dd_lambda=cfg["training"]["dd_lambda"],
        )

    def monitor_fn():
        weights = model(X_train_t)
        Rp = (weights * R_train_t).sum(dim=1)
        sharpe = Rp.mean() / (Rp.std() + 1e-8)
        return float(sharpe.item()) * np.sqrt(252)

    result = trainer.train(
        epochs=cfg["training"]["epochs"],
        loss_fn=loss_fn,
        monitor_fn=monitor_fn,
        log_every=100,
        checkpoint_meta={
            "n_features":  cfg["model"]["n_features"],
            "hidden_dims": cfg["model"]["hidden_dims"],
            "dropout":     cfg["model"]["dropout"],
        },
    )

    # ── Evaluation ────────────────────────────────────────
    log.info("=== [5/5] Evaluating on test set ===")
    model.eval()
    port_series, weights_df = apply_rebalancing_spt(
        model=model,
        X_test_t=tensors["X_test_t"],
        R_test_t=tensors["R_test_t"],
        test_dates=tensors["test_dates"],
        rebalance_freq=cfg["portfolio"]["rebalance_freq"],
        min_weight=cfg["portfolio"]["min_weight"],
        max_weight=cfg["portfolio"]["max_weight"],
    )

    net_returns, turnover = apply_transaction_cost(
        portfolio_returns=port_series,
        weights=weights_df,
        cost_rate=cfg["portfolio"]["transaction_cost"],
        holding_days=cfg["portfolio"]["rebalance_freq"],
    )

    net_series = pd.Series(net_returns.values, index=port_series.index, name="SPT Model")
    metrics_df = compute_metrics(net_series.to_frame())
    sharpe_val = float(metrics_df.loc["SPT Model", "Sharpe"])

    store.log_dict({
        "sharpe":           sharpe_val,
        "annual_return":    float(metrics_df.loc["SPT Model", "Arithmetic Return"]),
        "volatility":       float(metrics_df.loc["SPT Model", "Volatility"]),
        "max_drawdown":     float(metrics_df.loc["SPT Model", "Max Drawdown"]),
        "best_train_epoch": result["best_epoch"],
        "train_sharpe":     result["best_monitor"],
    })
    store.save()

    assert_sharpe_threshold(sharpe_val, cfg["output"]["sharpe_threshold"], strategy="SPT Model")

    log.info("SPT Model training complete. Test Sharpe: %.4f", sharpe_val)
    return {"sharpe": sharpe_val, "metrics": metrics_df}


# ─────────────────────────────────────────────────────────────
# Functional SPT training
# ─────────────────────────────────────────────────────────────

def train_functional_spt(cfg: dict, force_refresh: bool, run_id: str) -> dict:
    from src.data.downloader import download_prices
    from src.data.features import build_features_functional_spt
    from src.models.functional_spt import FunctionalSPT
    from src.training.losses import improved_objective, smoothness_penalty
    from src.training.trainer import Trainer
    from src.training.evaluate import compute_metrics, assert_sharpe_threshold
    from src.portfolio.rebalancing import apply_rebalancing_functional
    from src.portfolio.transaction_cost import apply_transaction_cost
    from src.utils.metrics_store import MetricsStore
    import torch

    log = logging.getLogger("train.functional_spt")
    store = MetricsStore(run_id=run_id, metrics_dir=cfg["output"]["metrics_dir"])

    # ── Data ──────────────────────────────────────────────
    log.info("=== [1/5] Downloading data ===")
    prices = download_prices(
        stocks=cfg["data"]["stocks"],
        start=cfg["data"]["start_date"],
        cache_dir=cfg["data"]["cache_dir"],
        force_refresh=force_refresh,
    )

    # ── Features ──────────────────────────────────────────
    log.info("=== [2/5] Building features ===")
    feat = build_features_functional_spt(
        prices=prices,
        momentum_window=cfg["features"]["momentum_window"],
        vol_window=cfg["features"]["vol_window"],
        rank_alpha=cfg["features"]["rank_alpha"],
        market_weight_alpha=cfg["features"]["market_weight_alpha"],
        use_garch=cfg["features"]["use_garch"],
        garch_p=cfg["garch"]["p"],
        garch_q=cfg["garch"]["q"],
    )
    x, returns, mu, garch_rank = (
        feat["x"], feat["returns"], feat["mu"], feat["garch_rank"]
    )

    split = cfg["data"]["split_date"]
    x_train, x_test         = x.loc[:split], x.loc[split:]
    ret_train, ret_test     = returns.loc[:split], returns.loc[split:]
    mu_train, mu_test       = mu.loc[:split], mu.loc[split:]
    garch_train, garch_test = garch_rank.loc[:split], garch_rank.loc[split:]

    x_train_t   = torch.tensor(x_train.values,   dtype=torch.float32)
    ret_train_t = torch.tensor(ret_train.values,  dtype=torch.float32)
    mu_train_t  = torch.tensor(mu_train.values,   dtype=torch.float32)
    garch_train_t = torch.tensor(garch_train.values, dtype=torch.float32)

    # ── Model ─────────────────────────────────────────────
    log.info("=== [3/5] Initializing model ===")
    model = FunctionalSPT(
        hidden_dim=cfg["model"]["hidden_dim"],
        output_dim=cfg["model"]["output_dim"],
        garch_penalty=cfg["portfolio"]["garch_penalty"],
    )
    log.info("Parameters: %d", sum(p.numel() for p in model.parameters()))

    optimizer = torch.optim.Adam(model.parameters(), lr=cfg["training"]["lr"])
    scheduler = torch.optim.lr_scheduler.CosineAnnealingWarmRestarts(
        optimizer,
        T_0=cfg["training"]["T_0"],
        T_mult=cfg["training"]["T_mult"],
        eta_min=cfg["training"]["lr_min"],
    )

    trainer = Trainer(
        model=model,
        optimizer=optimizer,
        scheduler=scheduler,
        patience=cfg["training"]["patience"],
        checkpoint_dir=cfg["output"]["checkpoint_dir"],
        model_name="functional_spt",
    )

    # ── Training ──────────────────────────────────────────
    log.info("=== [4/5] Training ===")
    gamma         = cfg["training"]["gamma"]
    sharpe_lambda = cfg["training"]["sharpe_lambda"]
    lam_smooth    = cfg["training"]["lambda_smooth"]

    def loss_fn():
        weights = model(x_train_t, garch_train_t)
        obj = improved_objective(
            weights, ret_train_t, mu_train_t,
            gamma=gamma, sharpe_lambda=sharpe_lambda,
        )
        smooth = smoothness_penalty(model, x_train_t)
        return -obj + lam_smooth * smooth

    def monitor_fn():
        weights = model(x_train_t, garch_train_t)
        obj = improved_objective(
            weights, ret_train_t, mu_train_t,
            gamma=gamma, sharpe_lambda=sharpe_lambda,
        )
        return float(obj.item())

    result = trainer.train(
        epochs=cfg["training"]["epochs"],
        loss_fn=loss_fn,
        monitor_fn=monitor_fn,
        log_every=200,
        checkpoint_meta={
            "hidden_dim": cfg["model"]["hidden_dim"],
            "output_dim": cfg["model"]["output_dim"],
        },
    )

    # ── Evaluation ────────────────────────────────────────
    log.info("=== [5/5] Evaluating on test set ===")
    model.eval()
    comparison, final_weights = apply_rebalancing_functional(
        model=model,
        x_data=x_test,
        returns_data=ret_test,
        market_weights=mu_test,
        garch_data=garch_test,
        holding_days=cfg["portfolio"]["holding_days"],
        vol_target=cfg["portfolio"]["vol_target"],
        vol_min_scale=cfg["portfolio"]["vol_scaling_min"],
        vol_max_scale=cfg["portfolio"]["vol_scaling_max"],
    )

    net_spt, turnover = apply_transaction_cost(
        portfolio_returns=comparison["Functional SPT"],
        weights=final_weights,
        cost_rate=cfg["portfolio"]["transaction_cost"],
        holding_days=cfg["portfolio"]["holding_days"],
    )
    comparison["Functional SPT (After Cost)"] = net_spt
    comparison = comparison.dropna()

    metrics_df = compute_metrics(comparison)
    sharpe_val = float(metrics_df.loc["Functional SPT (After Cost)", "Sharpe"])

    store.log_dict({
        "sharpe_gross":       float(metrics_df.loc["Functional SPT", "Sharpe"]),
        "sharpe_net":         sharpe_val,
        "annual_return_net":  float(metrics_df.loc["Functional SPT (After Cost)", "Arithmetic Return"]),
        "volatility_net":     float(metrics_df.loc["Functional SPT (After Cost)", "Volatility"]),
        "max_drawdown_net":   float(metrics_df.loc["Functional SPT (After Cost)", "Max Drawdown"]),
        "market_sharpe":      float(metrics_df.loc["Market", "Sharpe"]),
        "best_train_epoch":   result["best_epoch"],
        "best_objective":     result["best_monitor"],
    })
    store.save()

    assert_sharpe_threshold(
        sharpe_val, cfg["output"]["sharpe_threshold"], strategy="Functional SPT"
    )

    log.info("Functional SPT training complete. Test Sharpe (net): %.4f", sharpe_val)
    return {"sharpe": sharpe_val, "metrics": metrics_df}


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

def main():
    args = parse_args()

    config_path = args.config or f"config/{args.model}.yaml"
    cfg = load_config(config_path)

    log_dir = args.log_dir or cfg["output"]["log_dir"]

    from src.utils.logger import setup_logger
    logger, run_id = setup_logger(name=f"train.{args.model}", log_dir=log_dir)

    logger.info("Starting training | model=%s | run_id=%s", args.model, run_id)

    seed = cfg["training"].get("seed", 42)
    set_seed(seed)
    logger.info("Seed set to %d", seed)

    try:
        if args.model == "spt_model":
            result = train_spt(cfg, args.force_refresh, run_id)
        else:
            result = train_functional_spt(cfg, args.force_refresh, run_id)

        print("\n" + "=" * 60)
        print(f"Training complete — run_id: {run_id}")
        print(f"Test Sharpe: {result['sharpe']:.4f}")
        print("=" * 60)
        print(result["metrics"].round(4).to_string())

    except ValueError as e:
        # CI threshold failure
        logger.error("CI threshold check failed: %s", e)
        sys.exit(1)
    except Exception as e:
        logger.exception("Training failed: %s", e)
        sys.exit(2)


if __name__ == "__main__":
    main()
