"""
Inference entrypoint — load a trained checkpoint and output weights.

Usage:
    python predict.py --model spt_model --checkpoint checkpoints/spt_model_best.pt
    python predict.py --model functional_spt --checkpoint checkpoints/functional_spt_best.pt
    python predict.py --model spt_model --output-dir outputs/
"""

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import yaml


def parse_args():
    p = argparse.ArgumentParser(description="Run portfolio inference")
    p.add_argument("--model", required=True,
                   choices=["spt_model", "functional_spt"])
    p.add_argument("--checkpoint", required=True,
                   help="Path to .pt checkpoint file")
    p.add_argument("--config", default=None,
                   help="Path to YAML config (default: config/<model>.yaml)")
    p.add_argument("--output-dir", default="outputs",
                   help="Where to save weights CSV and metrics JSON")
    p.add_argument("--force-refresh", action="store_true")
    return p.parse_args()


def load_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def predict_spt(cfg: dict, checkpoint: str, output_dir: Path):
    from src.data.downloader import download_prices
    from src.data.features import build_features_spt, prepare_tensors_spt
    from src.models.spt_model import SPTModel
    from src.portfolio.rebalancing import apply_rebalancing_spt
    from src.portfolio.transaction_cost import apply_transaction_cost
    from src.training.evaluate import compute_metrics

    log = logging.getLogger("predict.spt")

    prices = download_prices(
        stocks=cfg["data"]["stocks"],
        start=cfg["data"]["start_date"],
        cache_dir=cfg["data"]["cache_dir"],
    )

    features, returns = build_features_spt(prices)
    tensors = prepare_tensors_spt(
        features, returns,
        train_end=cfg["data"]["train_end"],
        test_start=cfg["data"]["test_start"],
    )

    model = SPTModel.load(checkpoint)
    model.eval()
    log.info("Loaded checkpoint: %s", checkpoint)

    port_series, weights_df = apply_rebalancing_spt(
        model=model,
        X_test_t=tensors["X_test_t"],
        R_test_t=tensors["R_test_t"],
        test_dates=tensors["test_dates"],
        rebalance_freq=cfg["portfolio"]["rebalance_freq"],
        min_weight=cfg["portfolio"]["min_weight"],
        max_weight=cfg["portfolio"]["max_weight"],
    )

    net_returns, _ = apply_transaction_cost(
        portfolio_returns=port_series,
        weights=weights_df,
        cost_rate=cfg["portfolio"]["transaction_cost"],
        holding_days=cfg["portfolio"]["rebalance_freq"],
    )

    # Save outputs
    output_dir.mkdir(parents=True, exist_ok=True)
    weights_df.to_csv(output_dir / "spt_weights.csv")
    net_series = pd.Series(net_returns.values, index=port_series.index, name="SPT Model")
    net_series.to_csv(output_dir / "spt_returns.csv")

    metrics = compute_metrics(net_series.to_frame())
    metrics.to_csv(output_dir / "spt_metrics.csv")

    log.info("Outputs saved to %s", output_dir)
    print("\nSPT Model Inference Complete")
    print(metrics.round(4).to_string())
    return metrics


def predict_functional_spt(cfg: dict, checkpoint: str, output_dir: Path):
    from src.data.downloader import download_prices
    from src.data.features import build_features_functional_spt
    from src.models.functional_spt import FunctionalSPT
    from src.portfolio.rebalancing import apply_rebalancing_functional
    from src.portfolio.transaction_cost import apply_transaction_cost
    from src.training.evaluate import compute_metrics

    log = logging.getLogger("predict.functional_spt")

    prices = download_prices(
        stocks=cfg["data"]["stocks"],
        start=cfg["data"]["start_date"],
        cache_dir=cfg["data"]["cache_dir"],
    )

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

    split = cfg["data"]["split_date"]
    x_test    = feat["x"].loc[split:]
    ret_test  = feat["returns"].loc[split:]
    mu_test   = feat["mu"].loc[split:]
    garch_test = feat["garch_rank"].loc[split:]

    model = FunctionalSPT.load(checkpoint)
    model.eval()
    log.info("Loaded checkpoint: %s", checkpoint)

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

    net_spt, _ = apply_transaction_cost(
        portfolio_returns=comparison["Functional SPT"],
        weights=final_weights,
        cost_rate=cfg["portfolio"]["transaction_cost"],
        holding_days=cfg["portfolio"]["holding_days"],
    )
    comparison["Functional SPT (After Cost)"] = net_spt
    comparison.dropna(inplace=True)

    output_dir.mkdir(parents=True, exist_ok=True)
    final_weights.to_csv(output_dir / "functional_spt_weights.csv")
    comparison.to_csv(output_dir / "functional_spt_returns.csv")

    metrics = compute_metrics(comparison)
    metrics.to_csv(output_dir / "functional_spt_metrics.csv")

    log.info("Outputs saved to %s", output_dir)
    print("\nFunctional SPT Inference Complete")
    print(metrics.round(4).to_string())
    return metrics


def main():
    args = parse_args()
    config_path = args.config or f"config/{args.model}.yaml"
    cfg = load_config(config_path)

    from src.utils.logger import setup_logger
    setup_logger(name=f"predict.{args.model}", log_dir=cfg["output"]["log_dir"])

    output_dir = Path(args.output_dir)

    try:
        if args.model == "spt_model":
            predict_spt(cfg, args.checkpoint, output_dir)
        else:
            predict_functional_spt(cfg, args.checkpoint, output_dir)
    except Exception as e:
        logging.getLogger("predict").exception("Prediction failed: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
