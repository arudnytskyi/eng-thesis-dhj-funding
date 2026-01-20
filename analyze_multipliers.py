#!/usr/bin/env python3
"""Analyze the distribution of multipliers and real LLM prediction errors."""

import numpy as np
import pandas as pd

from config import (
    PLOTS_DIR,
    SCORES_CACHE_FILE,
    SCORING_RESULTS_FILE,
    TEST_CSV,
    TRAIN_CSV,
)
from utils.multiplier_analysis import (
    analyze_real_errors,
    load_multiplier_data,
    summarize_multipliers,
)
from utils.multiplier_plots import (
    plot_agreement_by_multiplier,
    plot_error_by_magnitude,
    plot_human_ai_distributions,
    plot_metrics_comparison,
)


def main() -> int:
    print("=" * 80)
    print("MULTIPLIER DISTRIBUTION ANALYSIS")
    print("=" * 80)

    train_df = load_multiplier_data(TRAIN_CSV)
    test_df = load_multiplier_data(TEST_CSV)

    summarize_multipliers(train_df, "train")
    summarize_multipliers(test_df, "test")

    print("\n" + "=" * 80)
    print("REAL LLM ERROR METRICS")
    print("=" * 80)

    prediction_context = analyze_real_errors(
        TRAIN_CSV,
        TEST_CSV,
        SCORING_RESULTS_FILE,
        SCORES_CACHE_FILE,
    )

    print("\n" + "=" * 80)
    print("PLOTS")
    print("=" * 80)

    plot_human_ai_distributions(
        prediction_context.train_df,
        prediction_context.test_df,
        prediction_context.train_predictions,
        prediction_context.test_predictions,
        prediction_context.train_least_predictions,
        prediction_context.test_least_predictions,
        prediction_context.least_model_name,
        PLOTS_DIR / "human_vs_ai_ensemble_multiplier_distribution.svg",
        PLOTS_DIR / "human_vs_ai_least_multiplier_distribution.svg",
    )
    plot_agreement_by_multiplier(
        prediction_context.train_df,
        prediction_context.test_df,
        prediction_context.train_samples,
        prediction_context.test_samples,
        prediction_context.train_predictions,
        prediction_context.test_predictions,
        prediction_context.train_least_predictions,
        prediction_context.test_least_predictions,
        prediction_context.least_model_name,
        PLOTS_DIR / "agreement_rate_by_multiplier.svg",
    )

    combined_df = pd.concat(
        [prediction_context.train_df, prediction_context.test_df],
        ignore_index=True,
    )
    combined_samples = (
        prediction_context.train_samples + prediction_context.test_samples
    )
    combined_predictions = np.concatenate(
        [prediction_context.train_predictions, prediction_context.test_predictions]
    )
    combined_least_predictions = np.concatenate(
        [
            prediction_context.train_least_predictions,
            prediction_context.test_least_predictions,
        ]
    )
    plot_error_by_magnitude(
        combined_df,
        combined_samples,
        combined_predictions,
        PLOTS_DIR / "error_by_magnitude_ensemble.svg",
        "AI Error vs Magnitude",
        least_predictions=combined_least_predictions,
        least_label=(
            f"AI-only (least-weighted: {prediction_context.least_model_name})"
        ),
    )
    plot_error_by_magnitude(
        combined_df,
        combined_samples,
        combined_predictions,
        PLOTS_DIR / "error_by_magnitude_ensemble_rmse.svg",
        "AI RMSE vs Magnitude",
        metric="rmse",
        least_predictions=combined_least_predictions,
        least_label=(
            f"AI-only (least-weighted: {prediction_context.least_model_name})"
        ),
    )
    plot_metrics_comparison(
        prediction_context.train_metrics,
        prediction_context.test_metrics,
        prediction_context.train_least_metrics,
        prediction_context.test_least_metrics,
        prediction_context.least_model_name,
        PLOTS_DIR / "metrics_comparison.svg",
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
