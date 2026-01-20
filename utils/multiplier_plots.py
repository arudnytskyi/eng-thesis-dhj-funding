from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from utils.multiplier_analysis import Sample, extract_human_ai_multipliers

COLOR_HUMAN = "#3b5b92"
COLOR_ENSEMBLE = "#c96f3c"
COLOR_LEAST = "#2f8f6b"
HIST_BINS = 40
AGREEMENT_BINS = 10
ERROR_BINS = 50
METRICS_COMPARISON_RATE_YMIN = 0.4
METRICS_COMPARISON_RATE_YMAX = 0.8
AGREEMENT_RATE_YMIN = 0.0
AGREEMENT_RATE_YMAX = 1.0
METRIC_LABELS = [
    ("agreement_rate", "Agreement rate", "Higher is better"),
    ("correlation", "Correlation", "Higher is better"),
    ("rmse", "RMSE", "Lower is better"),
    ("mae", "MAE", "Lower is better"),
]


def plot_human_ai_distributions(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    train_predictions: np.ndarray,
    test_predictions: np.ndarray,
    train_least_predictions: np.ndarray,
    test_least_predictions: np.ndarray,
    least_model_name: str,
    ensemble_output_path: Path,
    least_output_path: Path,
) -> None:
    train_human, train_ai = extract_human_ai_multipliers(
        train_df, train_predictions
    )
    test_human, test_ai = extract_human_ai_multipliers(
        test_df, test_predictions
    )
    _, train_least = extract_human_ai_multipliers(
        train_df, train_least_predictions
    )
    _, test_least = extract_human_ai_multipliers(
        test_df, test_least_predictions
    )
    human_values = np.concatenate([train_human, test_human])
    ai_values = np.concatenate([train_ai, test_ai])
    least_values = np.concatenate([train_least, test_least])

    plot_distribution_pair(
        human_values,
        ai_values,
        "DHJ",
        COLOR_ENSEMBLE,
        "Human vs AI Ensemble Multiplier Distribution",
        ensemble_output_path,
    )
    plot_distribution_pair(
        human_values,
        least_values,
        f"AI-only (least-weighted: {least_model_name})",
        COLOR_LEAST,
        "Human vs AI (Least-Weight Model) Multiplier Distribution",
        least_output_path,
    )


def plot_distribution_pair(
    human_values: np.ndarray,
    ai_values: np.ndarray,
    ai_label: str,
    ai_color: str,
    title: str,
    output_path: Path,
) -> None:
    if human_values.size == 0 or ai_values.size == 0:
        print("No valid multipliers to plot for human vs AI comparison.")
        return
    min_val = min(human_values.min(), ai_values.min())
    max_val = max(human_values.max(), ai_values.max())
    bins = _log_bins(min_val, max_val, HIST_BINS)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(
        human_values,
        bins=bins,
        alpha=0.65,
        color=COLOR_HUMAN,
        label="Human",
        density=False,
    )
    ax.hist(
        ai_values,
        bins=bins,
        alpha=0.55,
        color=ai_color,
        label=ai_label,
        density=False,
    )
    ax.set_xscale("log")
    ax.set_xlabel("Multiplier magnitude (log scale)")
    ax.set_ylabel("Count")
    ax.legend()
    ax.grid(True, axis="y", linestyle="--", linewidth=0.5, alpha=0.4)
    fig.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    print(f"Saved plot: {output_path}")


def plot_agreement_by_multiplier(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    train_samples: List[Sample],
    test_samples: List[Sample],
    train_predictions: np.ndarray,
    test_predictions: np.ndarray,
    train_least_predictions: np.ndarray,
    test_least_predictions: np.ndarray,
    least_model_name: str,
    output_path: Path,
) -> None:
    train_mult, train_human_log, train_pred = _prepare_agreement_arrays(
        train_df, train_samples, train_predictions
    )
    test_mult, test_human_log, test_pred = _prepare_agreement_arrays(
        test_df, test_samples, test_predictions
    )
    train_least_mult, train_least_human_log, train_least_pred = (
        _prepare_agreement_arrays(
            train_df, train_samples, train_least_predictions
        )
    )
    test_least_mult, test_least_human_log, test_least_pred = (
        _prepare_agreement_arrays(
            test_df, test_samples, test_least_predictions
        )
    )
    human_mult = np.concatenate([train_mult, test_mult])
    human_log = np.concatenate([train_human_log, test_human_log])
    ensemble_pred = np.concatenate([train_pred, test_pred])
    least_mult = np.concatenate([train_least_mult, test_least_mult])
    least_human_log = np.concatenate([train_least_human_log, test_least_human_log])
    least_pred = np.concatenate([train_least_pred, test_least_pred])

    if human_mult.size == 0 or least_mult.size == 0:
        print("No valid multipliers to plot agreement rates.")
        return

    min_val = min(human_mult.min(), least_mult.min())
    max_val = max(human_mult.max(), least_mult.max())
    bins = _log_bins(min_val, max_val, AGREEMENT_BINS)

    centers, ensemble_rates = _compute_binned_agreement(
        human_mult, human_log, ensemble_pred, bins
    )
    _, least_rates = _compute_binned_agreement(
        least_mult, least_human_log, least_pred, bins
    )
    valid_ensemble = ~np.isnan(ensemble_rates)
    valid_least = ~np.isnan(least_rates)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(
        centers[valid_ensemble],
        ensemble_rates[valid_ensemble],
        marker="o",
        color=COLOR_ENSEMBLE,
        label="DHJ",
    )
    ax.plot(
        centers[valid_least],
        least_rates[valid_least],
        marker="s",
        color=COLOR_LEAST,
        label=f"AI-only (least-weighted: {least_model_name})",
    )
    ax.set_xscale("log")
    ax.set_ylim(AGREEMENT_RATE_YMIN, AGREEMENT_RATE_YMAX)
    ax.set_xlabel("Human multiplier magnitude (log scale)")
    ax.set_ylabel("Agreement rate")
    ax.legend()
    ax.grid(True, axis="y", linestyle="--", linewidth=0.5, alpha=0.4)
    fig.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    print(f"Saved plot: {output_path}")


def plot_error_by_magnitude(
    df: pd.DataFrame,
    samples: List[Sample],
    predictions: np.ndarray,
    output_path: Path,
    title: str,
    metric: str = "mae",
    least_predictions: Optional[np.ndarray] = None,
    least_label: Optional[str] = None,
) -> None:
    if len(samples) != len(predictions) or len(df) != len(predictions):
        raise ValueError(
            "Data length mismatch for error plot: "
            f"df={len(df)} samples={len(samples)} preds={len(predictions)}"
        )
    if least_predictions is not None and len(least_predictions) != len(predictions):
        raise ValueError(
            "Data length mismatch for error plot: "
            f"least_preds={len(least_predictions)} preds={len(predictions)}"
        )
    multipliers = pd.to_numeric(df["multiplier"], errors="coerce")
    mask = multipliers > 0
    human_mult = multipliers[mask].to_numpy()
    human_log = np.array([log_mult for _, _, log_mult in samples])[mask.to_numpy()]
    pred_log = predictions[mask.to_numpy()]
    least_pred_log = (
        least_predictions[mask.to_numpy()] if least_predictions is not None else None
    )
    if human_mult.size == 0:
        print("No valid multipliers to plot error by magnitude.")
        return
    metric = metric.strip().lower()
    if metric not in {"mae", "rmse"}:
        raise ValueError(f"Unsupported error metric: {metric}")

    min_val = human_mult.min()
    max_val = human_mult.max()
    bins = _log_bins(min_val, max_val, ERROR_BINS)

    centers = np.sqrt(bins[:-1] * bins[1:])
    def compute_binned_error(pred_values: np.ndarray) -> np.ndarray:
        binned_errors = []
        for left, right in zip(bins[:-1], bins[1:]):
            bin_mask = (human_mult >= left) & (human_mult < right)
            if not np.any(bin_mask):
                binned_errors.append(np.nan)
                continue
            residual = pred_values[bin_mask] - human_log[bin_mask]
            if metric == "mae":
                binned_errors.append(float(np.mean(np.abs(residual))))
            else:
                binned_errors.append(float(np.sqrt(np.mean(residual ** 2))))
        return np.array(binned_errors)

    ensemble_errors = compute_binned_error(pred_log)
    series = [
        (
            "DHJ",
            ensemble_errors,
            COLOR_ENSEMBLE if least_pred_log is not None else COLOR_HUMAN,
            "o",
        )
    ]
    if least_pred_log is not None:
        series.append(
            (
                least_label or "AI-only (least-weighted)",
                compute_binned_error(least_pred_log),
                COLOR_LEAST,
                "s",
            )
        )
    y_label = (
        "Mean absolute error (log scale)"
        if metric == "mae"
        else "Root mean squared error (log scale)"
    )

    fig, ax = plt.subplots(figsize=(8, 4.5))
    for label, errors, color, marker in series:
        valid = ~np.isnan(errors)
        ax.plot(
            centers[valid],
            errors[valid],
            marker=marker,
            color=color,
            label=label,
        )
    ax.set_xscale("log")
    ax.set_xlabel("Human multiplier magnitude (log scale)")
    ax.set_ylabel(y_label)
    if len(series) > 1:
        ax.legend()
    ax.grid(True, axis="y", linestyle="--", linewidth=0.5, alpha=0.4)
    fig.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    print(f"Saved plot: {output_path}")


def plot_metrics_comparison(
    train_metrics: Dict[str, float],
    test_metrics: Dict[str, float],
    train_least_metrics: Dict[str, float],
    test_least_metrics: Dict[str, float],
    least_model_name: str,
    output_path: Path,
) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(10, 6))
    axes = axes.flatten()
    x = np.arange(2)
    width = 0.35

    for ax, (key, label, direction) in zip(axes, METRIC_LABELS):
        ensemble_vals = [train_metrics[key], test_metrics[key]]
        least_vals = [train_least_metrics[key], test_least_metrics[key]]
        ax.bar(
            x - width / 2,
            ensemble_vals,
            width,
            color=COLOR_ENSEMBLE,
            label="DHJ",
        )
        ax.bar(
            x + width / 2,
            least_vals,
            width,
            color=COLOR_LEAST,
            label=f"AI-only (least-weighted: {least_model_name})",
        )
        ax.set_xticks(x)
        ax.set_xticklabels(["Train", "Test"])
        ax.grid(True, axis="y", linestyle="--", linewidth=0.5, alpha=0.4)
        if key in {"agreement_rate", "correlation"}:
            ax.set_ylim(
                METRICS_COMPARISON_RATE_YMIN,
                METRICS_COMPARISON_RATE_YMAX,
            )

    axes[0].legend(loc="upper right", fontsize=8)
    fig.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    print(f"Saved plot: {output_path}")


def _prepare_agreement_arrays(
    df: pd.DataFrame,
    samples: List[Sample],
    predictions: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    if len(samples) != len(predictions) or len(df) != len(predictions):
        raise ValueError(
            "Data length mismatch for agreement plot: "
            f"df={len(df)} samples={len(samples)} preds={len(predictions)}"
        )
    multipliers = pd.to_numeric(df["multiplier"], errors="coerce")
    mask = multipliers > 0
    human_mult = multipliers[mask].to_numpy()
    human_log = np.array([log_mult for _, _, log_mult in samples])[mask.to_numpy()]
    pred_log = predictions[mask.to_numpy()]
    return human_mult, human_log, pred_log


def _compute_binned_agreement(
    multipliers: np.ndarray,
    human_log: np.ndarray,
    pred_log: np.ndarray,
    bins: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    rates = []
    centers = np.sqrt(bins[:-1] * bins[1:])
    human_sign = np.sign(human_log)
    pred_sign = np.sign(pred_log)
    for left, right in zip(bins[:-1], bins[1:]):
        mask = (multipliers >= left) & (multipliers < right)
        if not np.any(mask):
            rates.append(np.nan)
            continue
        rates.append(np.mean(human_sign[mask] == pred_sign[mask]))
    return centers, np.array(rates)


def _log_bins(min_val: float, max_val: float, num_bins: int) -> np.ndarray:
    if min_val == max_val:
        return np.array([min_val * 0.9, min_val * 1.1])
    return np.logspace(np.log10(min_val), np.log10(max_val), num_bins)
