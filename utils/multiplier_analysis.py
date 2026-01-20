from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from utils.analysis import evaluate_performance
from utils.data_loader import load_and_prepare_data
from utils.scoring import scores_to_logits

Sample = Tuple[int, int, float]


@dataclass(frozen=True)
class PredictionContext:
    train_df: pd.DataFrame
    test_df: pd.DataFrame
    train_samples: List[Sample]
    test_samples: List[Sample]
    train_predictions: np.ndarray
    test_predictions: np.ndarray
    least_model_name: str
    train_least_predictions: np.ndarray
    test_least_predictions: np.ndarray
    train_metrics: Dict[str, float]
    test_metrics: Dict[str, float]
    train_least_metrics: Dict[str, float]
    test_least_metrics: Dict[str, float]


def load_multiplier_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = {"multiplier", "repo_a", "repo_b"} - set(df.columns)
    if missing:
        missing_list = ", ".join(sorted(missing))
        raise ValueError(f"{path} is missing columns: {missing_list}")
    return df


def clean_multipliers(df: pd.DataFrame, report: bool = True) -> pd.DataFrame:
    df = df.copy()
    df["multiplier"] = pd.to_numeric(df["multiplier"], errors="coerce")
    invalid = df["multiplier"].isna().sum()
    non_positive = (df["multiplier"] <= 0).sum()
    if report and invalid:
        print(f"  Dropped invalid multipliers: {invalid}")
    if report and non_positive:
        print(f"  Dropped non-positive multipliers: {non_positive}")
    return df[df["multiplier"] > 0]


def summarize_multipliers(df: pd.DataFrame, name: str) -> None:
    print(f"\n{name.upper()} SET:")
    print(f"  Total samples: {len(df)}")
    df = clean_multipliers(df)
    print(f"  Valid multipliers: {len(df)}")
    if df.empty:
        print("  No valid multipliers to analyze.")
        return
    multipliers = df["multiplier"].to_numpy()
    log_multipliers = np.log(multipliers)

    _print_stats("Multiplier Statistics", multipliers, 2)
    _print_stats("Log(Multiplier) Statistics", log_multipliers, 4)
    _print_extremes(df, 100)
    _print_distribution(multipliers)


def extract_human_ai_multipliers(
    df: pd.DataFrame, predictions: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    multipliers = pd.to_numeric(df["multiplier"], errors="coerce")
    mask = multipliers > 0
    human_values = multipliers[mask].to_numpy()
    if len(predictions) != len(df):
        raise ValueError(
            "Predictions length does not match data length: "
            f"{len(predictions)} vs {len(df)}"
        )
    ai_values = np.exp(np.abs(predictions[np.asarray(mask)]))
    return human_values, ai_values


def analyze_real_errors(
    train_path: Path,
    test_path: Path,
    scoring_results_path: Path,
    scores_cache_path: Path,
) -> PredictionContext:
    model_names, optimal_weights = _load_scoring_summary(scoring_results_path)
    train_samples, test_samples, train_df, test_df, all_repos = _load_samples(
        train_path, test_path
    )
    cache = _load_scores_cache(scores_cache_path)
    distributions = _load_distributions_from_cache(
        cache, model_names, len(all_repos)
    )
    logits = scores_to_logits(distributions)

    min_weight_idx = int(np.argmin(np.array(optimal_weights)))
    least_model_name = model_names[min_weight_idx]
    least_logits = logits[min_weight_idx]
    train_least_predictions = np.array(
        [least_logits[idx_b] - least_logits[idx_a] for idx_a, idx_b, _ in train_samples]
    )
    test_least_predictions = np.array(
        [least_logits[idx_b] - least_logits[idx_a] for idx_a, idx_b, _ in test_samples]
    )

    train_predictions = print_error_report(
        "train",
        train_samples,
        train_df,
        logits,
        model_names,
        optimal_weights,
    )
    test_predictions = print_error_report(
        "test",
        test_samples,
        test_df,
        logits,
        model_names,
        optimal_weights,
    )
    train_metrics = _metrics_from_predictions(train_samples, train_predictions)
    test_metrics = _metrics_from_predictions(test_samples, test_predictions)
    train_least_metrics = _metrics_from_predictions(
        train_samples, train_least_predictions
    )
    test_least_metrics = _metrics_from_predictions(
        test_samples, test_least_predictions
    )
    _print_single_model_metrics(
        "train",
        train_samples,
        train_least_predictions,
        least_model_name,
    )
    _print_single_model_metrics(
        "test",
        test_samples,
        test_least_predictions,
        least_model_name,
    )

    return PredictionContext(
        train_df=train_df,
        test_df=test_df,
        train_samples=train_samples,
        test_samples=test_samples,
        train_predictions=train_predictions,
        test_predictions=test_predictions,
        least_model_name=least_model_name,
        train_least_predictions=train_least_predictions,
        test_least_predictions=test_least_predictions,
        train_metrics=train_metrics,
        test_metrics=test_metrics,
        train_least_metrics=train_least_metrics,
        test_least_metrics=test_least_metrics,
    )


def _print_single_model_metrics(
    name: str,
    samples: List[Sample],
    predictions: np.ndarray,
    model_name: str,
) -> None:
    metrics = _metrics_from_predictions(samples, predictions)
    print(f"\n{name.upper()} SET (least weight model: {model_name})")
    print(f"  Samples evaluated: {metrics['num_samples']}")
    print(f"  Agreement rate:    {metrics['agreement_rate']:.2%}")
    print(f"  Correlation:       {metrics['correlation']:.4f}")
    print(f"  MSE:               {metrics['mse']:.4f}")
    print(f"  RMSE:              {metrics['rmse']:.4f}")
    print(f"  MAE:               {metrics['mae']:.4f}")


def _metrics_from_predictions(
    samples: List[Sample],
    predictions: np.ndarray,
) -> Dict[str, float]:
    human_judgments = np.array([log_mult for _, _, log_mult in samples])
    if len(human_judgments) == 0:
        return {
            "mse": float("nan"),
            "rmse": float("nan"),
            "mae": float("nan"),
            "agreement_rate": float("nan"),
            "correlation": float("nan"),
            "num_samples": 0,
        }
    errors = predictions - human_judgments
    mse = float(np.mean(errors ** 2))
    mae = float(np.mean(np.abs(errors)))
    rmse = float(np.sqrt(mse))
    agreement_rate = float(np.mean(np.sign(predictions) == np.sign(human_judgments)))
    if len(human_judgments) < 2:
        correlation = float("nan")
    else:
        correlation = float(np.corrcoef(predictions, human_judgments)[0, 1])
    return {
        "mse": mse,
        "rmse": rmse,
        "mae": mae,
        "agreement_rate": agreement_rate,
        "correlation": correlation,
        "num_samples": int(len(human_judgments)),
    }


def print_error_report(
    name: str,
    samples: List[Sample],
    df: pd.DataFrame,
    logits: List[List[float]],
    model_names: List[str],
    optimal_weights: List[float],
) -> np.ndarray:
    ai_comparisons = _build_ai_comparisons(samples, logits, model_names)
    metrics = evaluate_performance(
        samples,
        ai_comparisons,
        optimal_weights,
        model_names,
    )

    print(f"\n{name.upper()} SET (weighted ensemble predictions):")
    print(f"  Samples evaluated: {metrics['num_samples']}")
    print(f"  Agreement rate:    {metrics['agreement_rate']:.2%}")
    print(f"  Correlation:       {metrics['correlation']:.4f}")
    print(f"  MSE:               {metrics['mse']:.4f}")
    print(f"  RMSE:              {metrics['rmse']:.4f}")
    print(f"  MAE:               {metrics['mae']:.4f}")

    predictions = _weighted_predictions(
        ai_comparisons,
        model_names,
        optimal_weights,
    )
    human_judgments = np.array([log_mult for _, _, log_mult in samples])
    errors = predictions - human_judgments
    squared_errors = errors ** 2
    top_n = min(5, len(samples))
    if top_n == 0:
        print("\n  No samples available for error analysis.")
        return predictions

    top_errors_idx = np.argsort(squared_errors)[-top_n:][::-1]
    print(f"\n  Top {top_n} contributors to squared error:")
    for rank, idx in enumerate(top_errors_idx, 1):
        _, _, human_log = samples[idx]
        row = df.iloc[idx]
        repo_a = str(row["repo_a"]).split("/")[-1]
        repo_b = str(row["repo_b"]).split("/")[-1]
        human_desc = _describe_judgment(
            repo_a, repo_b, human_log, float(row["multiplier"])
        )
        pred_desc = _describe_judgment(repo_a, repo_b, predictions[idx])
        error_contribution = squared_errors[idx]
        print(f"    {rank}. {repo_a:25s} vs {repo_b:25s}")
        print(
            f"       Human: {human_desc} (log={human_log:.4f})\n"
            f"       LLM:   {pred_desc} (log={predictions[idx]:.4f})\n"
            f"       Squared Error: {error_contribution:.4f}"
        )
    return predictions


def _print_stats(label: str, values: np.ndarray, decimals: int) -> None:
    print(f"\n  {label}:")
    if values.size == 0:
        print("    n/a")
        return
    fmt = f"{{:.{decimals}f}}"
    print(f"    Min:       {fmt.format(values.min())}")
    print(f"    Max:       {fmt.format(values.max())}")
    print(f"    Mean:      {fmt.format(values.mean())}")
    print(f"    Median:    {fmt.format(np.median(values))}")
    print(f"    Std Dev:   {fmt.format(values.std())}")


def _print_extremes(df: pd.DataFrame, threshold: float) -> None:
    print(f"\n  Extreme Values (>{threshold:g}x):")
    extreme = df[df["multiplier"] > threshold].sort_values(
        "multiplier", ascending=False
    )
    if extreme.empty:
        print("    None")
        return
    for _, row in extreme.iterrows():
        repo_a = str(row["repo_a"]).split("/")[-1]
        repo_b = str(row["repo_b"]).split("/")[-1]
        print(f"    {row['multiplier']:.0f}x: {repo_a:30s} vs {repo_b}")


def _print_distribution(multipliers: np.ndarray) -> None:
    print("\n  Distribution:")
    total = len(multipliers)
    if total == 0:
        print("    No valid multipliers.")
        return
    ranges = [
        ("<=1x", multipliers <= 1),
        ("1-2x", (multipliers > 1) & (multipliers <= 2)),
        ("2-5x", (multipliers > 2) & (multipliers <= 5)),
        ("5-10x", (multipliers > 5) & (multipliers <= 10)),
        ("10-50x", (multipliers > 10) & (multipliers <= 50)),
        ("50-100x", (multipliers > 50) & (multipliers <= 100)),
        (">100x", multipliers > 100),
    ]
    for label, mask in ranges:
        count = int(mask.sum())
        pct = count / total * 100
        print(f"    {label:8s} {count:6d} samples ({pct:5.1f}%)")


def _load_scoring_summary(path: Path) -> Tuple[List[str], List[float]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing scoring results file: {path}")
    with path.open() as handle:
        data = json.load(handle)
    missing = {"model_names", "optimal_weights"} - set(data.keys())
    if missing:
        missing_list = ", ".join(sorted(missing))
        raise ValueError(f"{path} is missing keys: {missing_list}")
    model_names = data["model_names"]
    optimal_weights = [float(w) for w in data["optimal_weights"]]
    if len(model_names) != len(optimal_weights):
        raise ValueError(
            "Model names and optimal weights have different lengths: "
            f"{len(model_names)} vs {len(optimal_weights)}"
        )
    return model_names, optimal_weights


def _load_scores_cache(path: Path) -> Dict[str, List[float]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing scores cache file: {path}")
    with path.open() as handle:
        cache = json.load(handle)
    if not isinstance(cache, dict):
        raise ValueError(f"Scores cache is not a dict: {path}")
    return cache


def _load_samples(
    train_path: Path, test_path: Path
) -> Tuple[List[Sample], List[Sample], pd.DataFrame, pd.DataFrame, List[str]]:
    train_samples, train_repo_to_idx, train_idx_to_repo, train_df = (
        load_and_prepare_data(str(train_path))
    )
    test_samples, test_repo_to_idx, test_idx_to_repo, test_df = (
        load_and_prepare_data(str(test_path))
    )
    all_repos = sorted(set(train_repo_to_idx.keys()) | set(test_repo_to_idx.keys()))
    repo_to_idx = {repo: idx for idx, repo in enumerate(all_repos)}

    def _remap_samples(
        samples: List[Sample],
        idx_to_repo: Dict[int, str],
    ) -> List[Sample]:
        return [
            (repo_to_idx[idx_to_repo[idx_a]], repo_to_idx[idx_to_repo[idx_b]], log_mult)
            for idx_a, idx_b, log_mult in samples
        ]

    train_samples = _remap_samples(train_samples, train_idx_to_repo)
    test_samples = _remap_samples(test_samples, test_idx_to_repo)
    return train_samples, test_samples, train_df, test_df, all_repos


def _load_distributions_from_cache(
    cache: Dict[str, List[float]],
    model_names: List[str],
    repo_count: int,
) -> Dict[str, List[float]]:
    distributions: Dict[str, List[float]] = {}
    missing = []
    bad_lengths = []
    for model_name in model_names:
        cache_key = f"{model_name}:scores:{repo_count}"
        scores = cache.get(cache_key)
        if scores is None:
            missing.append(model_name)
            continue
        if len(scores) != repo_count:
            bad_lengths.append((model_name, len(scores)))
            continue
        distributions[model_name] = scores
    if missing:
        missing_list = ", ".join(missing)
        raise ValueError(
            "Missing cached scores for models: "
            f"{missing_list} (expected repo count {repo_count})"
        )
    if bad_lengths:
        details = ", ".join(f"{name}={length}" for name, length in bad_lengths)
        raise ValueError(
            "Cached scores have unexpected lengths (expected "
            f"{repo_count}): {details}"
        )
    return distributions


def _build_ai_comparisons(
    samples: List[Sample],
    logits: List[List[float]],
    model_names: List[str],
) -> Dict[str, List[float]]:
    ai_comparisons: Dict[str, List[float]] = {}
    for i, model_name in enumerate(model_names):
        model_logits = logits[i]
        predictions = [
            model_logits[idx_b] - model_logits[idx_a]
            for idx_a, idx_b, _ in samples
        ]
        ai_comparisons[model_name] = predictions
    return ai_comparisons


def _weighted_predictions(
    ai_comparisons: Dict[str, List[float]],
    model_names: List[str],
    optimal_weights: List[float],
) -> np.ndarray:
    if not model_names:
        return np.array([])
    num_samples = len(ai_comparisons[model_names[0]])
    weighted = np.zeros(num_samples)
    for weight, model_name in zip(optimal_weights, model_names):
        weighted += weight * np.array(ai_comparisons[model_name])
    return weighted


def _describe_judgment(
    repo_a: str,
    repo_b: str,
    log_value: float,
    multiplier: Optional[float] = None,
) -> str:
    if log_value == 0:
        return "tie"
    if multiplier is None:
        multiplier = float(np.exp(abs(log_value)))
    better = repo_b if log_value > 0 else repo_a
    return f"{better} {multiplier:.1f}x"
