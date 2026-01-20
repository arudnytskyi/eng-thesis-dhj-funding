#!/usr/bin/env python3
"""Analyze time between consecutive jury decisions using timestamps."""

import random
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from config import DECISION_TIMES_PLOT, TEST_CSV, TRAIN_CSV


def _format_timedelta(delta: pd.Timedelta) -> str:
    if pd.isna(delta):
        return "n/a"
    total_seconds = int(delta.total_seconds())
    if total_seconds < 0:
        total_seconds = abs(total_seconds)
    days, rem = divmod(total_seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)
    parts: list[str] = []
    if days:
        parts.append(f"{days}d")
    if hours or parts:
        parts.append(f"{hours}h")
    if minutes or parts:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    return " ".join(parts)


def _load(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = {"timestamp", "juror"} - set(df.columns)
    if missing:
        missing_list = ", ".join(sorted(missing))
        raise ValueError(f"{path} is missing columns: {missing_list}")
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    return df


def _filter_outliers_iqr(
    deltas: pd.Series, iqr_multiplier: float
) -> pd.Series:
    if deltas.empty:
        return deltas
    q1 = deltas.quantile(0.25)
    q3 = deltas.quantile(0.75)
    iqr = q3 - q1
    if iqr <= pd.Timedelta(0):
        return deltas
    lower = q1 - iqr_multiplier * iqr
    upper = q3 + iqr_multiplier * iqr
    return deltas[(deltas >= lower) & (deltas <= upper)]


def _apply_filters(
    deltas: pd.Series,
    max_gap: pd.Timedelta | None,
    omit_outliers: bool,
    iqr_multiplier: float,
) -> tuple[pd.Series, dict[str, int]]:
    removed: dict[str, int] = {}
    filtered = deltas
    if max_gap is not None:
        before = len(filtered)
        filtered = filtered[filtered <= max_gap]
        removed["max_gap"] = before - len(filtered)
    if omit_outliers:
        before = len(filtered)
        filtered = _filter_outliers_iqr(filtered, iqr_multiplier)
        removed["outliers"] = before - len(filtered)
    return filtered, removed


def _summarize(
    df: pd.DataFrame,
    max_gap: pd.Timedelta | None,
    per_juror: bool,
    omit_outliers: bool,
    iqr_multiplier: float,
) -> None:
    df = df.sort_values(["juror", "timestamp"], kind="mergesort")
    df["decision_delta"] = df.groupby("juror")["timestamp"].diff()

    invalid_timestamps = df["timestamp"].isna().sum()
    deltas = df["decision_delta"].dropna()
    deltas, removed = _apply_filters(deltas, max_gap, omit_outliers, iqr_multiplier)

    print(f"  Total rows: {len(df)}")
    print(f"  Jurors: {df['juror'].nunique()}")
    print(f"  Missing/invalid timestamps: {invalid_timestamps}")
    if max_gap is not None:
        print(f"  Max gap filter: {max_gap}")
        if removed.get("max_gap"):
            print(f"    Removed by max gap: {removed['max_gap']}")
    if omit_outliers:
        print(f"  Outlier filter: IQR x {iqr_multiplier:g}")
        if removed.get("outliers"):
            print(f"    Removed outliers: {removed['outliers']}")
    print(f"  Inter-decision gaps: {len(deltas)}")

    if deltas.empty:
        print("  No decision deltas available.")
        return

    stats = {
        "min": deltas.min(),
        "max": deltas.max(),
        "mean": deltas.mean(),
        "median": deltas.median(),
        "p75": deltas.quantile(0.75),
        "p90": deltas.quantile(0.90),
    }

    print("\n  Decision time stats:")
    for label, value in stats.items():
        print(f"    {label:>6}: {_format_timedelta(value)}")

    if per_juror:
        per_df = df.dropna(subset=["decision_delta"]).copy()
        per_deltas, _ = _apply_filters(
            per_df["decision_delta"], max_gap, omit_outliers, iqr_multiplier
        )
        per_df = per_df.loc[per_deltas.index]
        per = (
            per_df.groupby("juror")["decision_delta"]
            .agg(["count", "mean", "median"])
            .sort_values("median")
        )
        print("\n  Per-juror median decision time (fastest to slowest):")
        for juror, row in per.iterrows():
            print(
                f"    {juror:12s} count={int(row['count']):3d} "
                f"median={_format_timedelta(row['median'])} "
                f"mean={_format_timedelta(row['mean'])}"
            )


def _plot_decision_times(
    df: pd.DataFrame,
    max_gap: pd.Timedelta | None,
    omit_outliers: bool,
    iqr_multiplier: float,
    show_mean_line: bool,
    output_path: Path,
) -> None:
    df = df.sort_values(["juror", "timestamp"], kind="mergesort").copy()
    df["decision_delta"] = df.groupby("juror")["timestamp"].diff()
    plot_df = df.dropna(subset=["decision_delta"]).copy()
    filtered, _ = _apply_filters(
        plot_df["decision_delta"], max_gap, omit_outliers, iqr_multiplier
    )
    plot_df = plot_df.loc[filtered.index]

    if plot_df.empty:
        print(f"No decision deltas to plot.")
        return

    plot_df["delta_minutes"] = plot_df["decision_delta"].dt.total_seconds() / 60.0
    juror_order = (
        plot_df.groupby("juror")["delta_minutes"]
        .median()
        .sort_values()
        .index.tolist()
    )

    fig_width = max(10.0, len(juror_order) * 0.35)
    fig, ax = plt.subplots(figsize=(fig_width, 6))
    rng = random.Random(0)

    for idx, juror in enumerate(juror_order):
        values = plot_df.loc[plot_df["juror"] == juror, "delta_minutes"].tolist()
        jitter = [rng.uniform(-0.25, 0.25) for _ in values]
        xs = [idx + offset for offset in jitter]
        ax.scatter(xs, values, s=12, alpha=0.55, color="#3b5b92")
        median = pd.Series(values).median()
        ax.hlines(median, idx - 0.3, idx + 0.3, color="#111111", linewidth=1.0)

    ax.set_xlabel("Juror (sorted by median decision time)")
    ax.set_ylabel("Decision time in minutes")
    if show_mean_line:
        mean_minutes = plot_df["delta_minutes"].mean()
        ax.axhline(
            mean_minutes,
            color="#d1495b",
            linewidth=1.2,
            linestyle="--",
            label=f"Overall mean: {mean_minutes:.1f} min",
        )
        ax.legend(loc="upper right", fontsize=8, frameon=False)
    ax.set_xticks(range(len(juror_order)))
    ax.set_xticklabels(juror_order, rotation=90, fontsize=8)
    ax.grid(True, axis="y", linestyle="--", linewidth=0.5, alpha=0.4)
    fig.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    print(f"Saved plot: {output_path}")


if __name__ == "__main__":
    max_gap = pd.Timedelta("30m")
    per_juror = False
    omit_outliers = True
    iqr_multiplier = 1.5
    show_mean_line = True

    print("=" * 80)
    print("DECISION TIME ANALYSIS")
    print("=" * 80)

    train_df = _load(TRAIN_CSV)
    test_df = _load(TEST_CSV)
    combined_df = pd.concat([train_df, test_df], ignore_index=True)

    _summarize(
        combined_df,
        max_gap,
        per_juror,
        omit_outliers,
        iqr_multiplier,
    )
    _plot_decision_times(
        combined_df,
        max_gap,
        omit_outliers,
        iqr_multiplier,
        show_mean_line,
        DECISION_TIMES_PLOT,
    )
