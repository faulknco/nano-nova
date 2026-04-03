"""
Publication-quality figures from Rust norm growth sweep data.

Reads CSV output from: results/norm_growth_v2/summary.csv and trajectories/
Produces figures for ZKProof 8 submission.

Key metric: digit_l2 (max digit-vector L2 norm) is the correct comparison.
- For naive (base=0): digit_l2 == l2 (no decomposition)
- For decomposed (base>0): digit_l2 << l2 — this is the 40-100x reduction finding

Usage:
    cd ~/Projects/nano-nova
    python notebooks/07_publication_figures.py
"""

# %% Imports and config
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.rcParams.update(
    {
        "figure.figsize": (10, 6),
        "font.size": 12,
        "axes.labelsize": 14,
        "axes.titlesize": 14,
        "legend.fontsize": 11,
        "figure.dpi": 150,
        "savefig.dpi": 300,
    }
)

DATA_DIR = Path("results/norm_growth_v2")
FIG_DIR = Path("results/norm_growth_v2/figures")
FIG_DIR.mkdir(parents=True, exist_ok=True)

# %% Load summary data
summary = pd.read_csv(DATA_DIR / "summary.csv")
print(f"Loaded {len(summary)} parameter combos")
print(f"Ring dims: {sorted(summary['n'].unique())}")
print(f"Moduli: {sorted(summary['q'].unique())}")
print(f"Bases: {sorted(summary['base'].unique())}")
print(f"Fold counts: {sorted(summary['num_folds'].unique())}")
print(summary.head())


# %% Figure 1: Norm trajectories — naive vs decomposed (digit_l2 is the right metric)
def plot_trajectories(n, q, num_folds, bases=None):
    """Plot norm trajectories for different bases at fixed n, q, folds.

    For naive: plots l2_mean (no decomposition).
    For decomposed: plots digit_l2_mean — the max digit-vector L2 norm, which is
    the quantity LatticeFold's security proof bounds. This is 40-100x smaller than
    the recomposed norm and is the correct comparison to naive l2.
    """
    if bases is None:
        bases = sorted(summary["base"].unique())

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    for base in bases:
        fname = f"{n}_{q}_{base}_{num_folds}.csv"
        traj_path = DATA_DIR / "trajectories" / fname
        if not traj_path.exists():
            print(f"  Skipping {fname} (not found)")
            continue

        traj = pd.read_csv(traj_path)
        label = "naive" if base == 0 else f"B={base}"
        style = "--" if base == 0 else "-"
        alpha = 0.6 if base == 0 else 0.9

        # Use digit_l2 for decomposed (the security-relevant quantity),
        # l2 for naive (they are equal for base=0).
        if base == 0:
            y_mean = traj["l2_mean"]
            y_p99 = traj["l2_p99"]
        else:
            y_mean = traj["digit_l2_mean"]
            y_p99 = traj["digit_l2_p99"]

        ax1.semilogy(traj["fold_step"], y_mean, style, label=f"{label} (mean)", alpha=alpha)
        ax1.semilogy(traj["fold_step"], y_p99, ":", alpha=0.4)

        ax2.semilogy(
            traj["fold_step"], traj["linf_mean"], style, label=f"{label} (mean)", alpha=alpha
        )
        ax2.semilogy(traj["fold_step"], traj["linf_p99"], ":", alpha=0.4)

    ax1.set_xlabel("Fold Step")
    ax1.set_ylabel("L2 Norm (digit vectors)")
    ax1.set_title(f"Digit L2 Norm Growth (n={n}, q={q})")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    ax2.set_xlabel("Fold Step")
    ax2.set_ylabel("L∞ Norm")
    ax2.set_title(f"L∞ Norm Growth (n={n}, q={q})")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    fig.suptitle(
        f"Norm Trajectories: n={n}, q={q}, {num_folds} folds, 1000 trials\n"
        f"(decomposed: digit norms; naive: witness norms)",
        y=1.04,
    )
    fig.tight_layout()
    return fig


# Generate trajectory plots for each (n, q) at max fold count
max_folds = summary["num_folds"].max()
for n in sorted(summary["n"].unique()):
    for q in sorted(summary["q"].unique()):
        fig = plot_trajectories(n, q, max_folds)
        fig.savefig(FIG_DIR / f"trajectories_n{n}_q{q}.png")
        plt.close(fig)
        print(f"Saved trajectories_n{n}_q{q}.png")


# %% Figure 2: Reduction ratio — naive l2 / decomposed digit_l2 (the key finding)
def plot_reduction_ratio(num_folds):
    """Bar chart showing how many times smaller digit norms are vs naive.

    This is the central empirical finding: decompose-then-fold keeps digit norms
    significantly smaller than naive folding, and the gap grows with more folds.
    """
    subset = summary[summary["num_folds"] == num_folds]
    dims = sorted(subset["n"].unique())
    q_vals = sorted(subset["q"].unique())
    decomposed_bases = [b for b in sorted(subset["base"].unique()) if b > 0]

    fig, axes = plt.subplots(1, len(q_vals), figsize=(8 * len(q_vals), 5))
    if len(q_vals) == 1:
        axes = [axes]

    for ax, q in zip(axes, q_vals):
        x = np.arange(len(dims))
        width = 0.18

        for i, base in enumerate(decomposed_bases):
            ratios = []
            for n in dims:
                naive_row = subset[(subset["base"] == 0) & (subset["n"] == n) & (subset["q"] == q)]
                decomp_row = subset[
                    (subset["base"] == base) & (subset["n"] == n) & (subset["q"] == q)
                ]
                if not naive_row.empty and not decomp_row.empty:
                    naive_l2 = naive_row["l2_p99"].values[0]
                    digit_l2 = decomp_row["digit_l2_p99"].values[0]
                    ratios.append(naive_l2 / digit_l2 if digit_l2 > 0 else 0)
                else:
                    ratios.append(0)

            ax.bar(x + i * width, ratios, width, label=f"B={base}", alpha=0.8)

        ax.axhline(1.0, color="red", linestyle="--", linewidth=1, alpha=0.6, label="no reduction")
        ax.set_xlabel("Ring Dimension")
        ax.set_ylabel("Naive L2 p99 / Decomposed Digit L2 p99")
        ax.set_title(f"q={q}")
        ax.set_xticks(x + width * (len(decomposed_bases) - 1) / 2)
        ax.set_xticklabels(dims)
        ax.legend()
        ax.grid(True, alpha=0.3, axis="y")

    fig.suptitle(
        f"Norm Reduction Ratio: naive vs decompose-then-fold ({num_folds} folds, 1000 trials)\n"
        f"Higher = more reduction from decomposition",
        y=1.04,
    )
    fig.tight_layout()
    return fig


fig = plot_reduction_ratio(max_folds)
fig.savefig(FIG_DIR / "reduction_ratio.png")
plt.close(fig)
print("Saved reduction_ratio.png")


# %% Figure 3: Growth rate heatmap — base vs ring dimension
def plot_growth_heatmap(q, num_folds):
    """Heatmap of log growth rate: rows=base, cols=ring_dim."""
    subset = summary[(summary["q"] == q) & (summary["num_folds"] == num_folds)]
    if subset.empty:
        print(f"No data for q={q}, folds={num_folds}")
        return None

    bases = sorted(subset["base"].unique())
    dims = sorted(subset["n"].unique())

    grid = np.full((len(bases), len(dims)), np.nan)
    for i, base in enumerate(bases):
        for j, n in enumerate(dims):
            row = subset[(subset["base"] == base) & (subset["n"] == n)]
            if not row.empty:
                grid[i, j] = row["log_growth_rate"].values[0]

    fig, ax = plt.subplots(figsize=(8, 5))
    im = ax.imshow(grid, aspect="auto", cmap="RdYlGn_r")
    ax.set_xticks(range(len(dims)))
    ax.set_xticklabels(dims)
    ax.set_yticks(range(len(bases)))
    ax.set_yticklabels(["naive" if b == 0 else f"B={b}" for b in bases])
    ax.set_xlabel("Ring Dimension (n)")
    ax.set_ylabel("Decomposition Base")
    ax.set_title(f"Log Growth Rate (q={q}, {num_folds} folds)")

    for i in range(len(bases)):
        for j in range(len(dims)):
            if not np.isnan(grid[i, j]):
                ax.text(j, i, f"{grid[i, j]:.4f}", ha="center", va="center", fontsize=9)

    fig.colorbar(im, label="log growth rate (lower = better)")
    fig.tight_layout()
    return fig


for q in sorted(summary["q"].unique()):
    fig = plot_growth_heatmap(q, max_folds)
    if fig:
        fig.savefig(FIG_DIR / f"heatmap_q{q}.png")
        plt.close(fig)
        print(f"Saved heatmap_q{q}.png")


# %% Figure 4: Final digit norm distributions — bar chart
def plot_final_digit_norms(num_folds):
    """Bar chart comparing final digit L2 p99 across bases for each n.

    Uses digit_l2_p99 for decomposed and l2_p99 for naive — apples-to-apples
    comparison of the security-relevant norm in each strategy.
    """
    subset = summary[summary["num_folds"] == num_folds]
    bases = sorted(subset["base"].unique())
    dims = sorted(subset["n"].unique())
    q_vals = sorted(subset["q"].unique())

    fig, axes = plt.subplots(1, len(q_vals), figsize=(7 * len(q_vals), 5))
    if len(q_vals) == 1:
        axes = [axes]

    for ax, q in zip(axes, q_vals):
        x = np.arange(len(dims))
        width = 0.15
        for i, base in enumerate(bases):
            vals = []
            for n in dims:
                row = subset[(subset["base"] == base) & (subset["n"] == n) & (subset["q"] == q)]
                if not row.empty:
                    # digit_l2_p99 is the correct metric for both naive and decomposed
                    vals.append(row["digit_l2_p99"].values[0])
                else:
                    vals.append(0)
            label = "naive" if base == 0 else f"B={base}"
            ax.bar(x + i * width, vals, width, label=label, alpha=0.8)

        ax.set_xlabel("Ring Dimension")
        ax.set_ylabel("Digit L2 Norm (p99)")
        ax.set_title(f"q={q}")
        ax.set_xticks(x + width * (len(bases) - 1) / 2)
        ax.set_xticklabels(dims)
        ax.set_yscale("log")
        ax.legend()
        ax.grid(True, alpha=0.3, axis="y")

    fig.suptitle(
        f"Final Digit L2 Norm (p99) after {num_folds} folds, 1000 trials\n"
        f"(naive = witness norm; decomposed = max digit norm)",
        y=1.04,
    )
    fig.tight_layout()
    return fig


fig = plot_final_digit_norms(max_folds)
fig.savefig(FIG_DIR / "final_norms.png")
plt.close(fig)
print("Saved final_norms.png")


# %% Figure 5: Tightness analysis — empirical digit linf p99 vs theoretical bound
def plot_tightness(q, num_folds):
    """Compare empirical digit linf p99 vs theoretical worst-case bound."""
    subset = summary[
        (summary["q"] == q) & (summary["num_folds"] == num_folds) & (summary["base"] > 0)
    ]
    if subset.empty:
        return None

    fig, ax = plt.subplots(figsize=(10, 5))

    bases = sorted(subset["base"].unique())
    dims = sorted(subset["n"].unique())
    x = np.arange(len(dims))
    width = 0.12

    for i, base in enumerate(bases):
        empirical = []
        theoretical = []
        for n in dims:
            row = subset[(subset["base"] == base) & (subset["n"] == n)]
            if not row.empty:
                empirical.append(row["digit_linf_p99"].values[0])
                # Theoretical worst case for digit linf: base/2 (centered digits in [-B/2, B/2])
                theoretical.append(base / 2)
            else:
                empirical.append(0)
                theoretical.append(0)

        ax.bar(x + i * width, empirical, width, label=f"B={base} (empirical p99)", alpha=0.8)
        ax.scatter(
            x + i * width + width / 2,
            theoretical,
            marker="_",
            s=200,
            color="red",
            zorder=5,
        )

    ax.set_xlabel("Ring Dimension")
    ax.set_ylabel("Digit L∞ Norm")
    ax.set_title(
        f"Digit L∞ p99 vs Theoretical Bound B/2 (q={q}, {num_folds} folds)\n"
        f"Red marks = theoretical bound B/2 (lower is tighter)"
    )
    ax.set_xticks(x + width * (len(bases) - 1) / 2)
    ax.set_xticklabels(dims)
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")

    fig.tight_layout()
    return fig


for q in sorted(summary["q"].unique()):
    fig = plot_tightness(q, max_folds)
    if fig:
        fig.savefig(FIG_DIR / f"tightness_q{q}.png")
        plt.close(fig)
        print(f"Saved tightness_q{q}.png")


# %% Figure 6: Scaling with ring dimension
def plot_scaling():
    """How does final digit L2 norm scale with n for fixed base and fold count?"""
    subset = summary[summary["num_folds"] == max_folds]
    q_vals = sorted(subset["q"].unique())
    bases = [b for b in sorted(subset["base"].unique()) if b > 0]

    fig, axes = plt.subplots(1, len(q_vals), figsize=(7 * len(q_vals), 5))
    if len(q_vals) == 1:
        axes = [axes]

    for ax, q in zip(axes, q_vals):
        q_sub = subset[subset["q"] == q]
        dims = sorted(q_sub["n"].unique())

        # Naive reference (using l2_mean = digit_l2_mean for base=0)
        naive_vals = []
        for n in dims:
            row = q_sub[(q_sub["base"] == 0) & (q_sub["n"] == n)]
            naive_vals.append(row["l2_mean"].values[0] if not row.empty else np.nan)
        ax.loglog(dims, naive_vals, "k--", label="naive", alpha=0.7, linewidth=2)

        for base in bases:
            vals = []
            for n in dims:
                row = q_sub[(q_sub["base"] == base) & (q_sub["n"] == n)]
                vals.append(row["digit_l2_mean"].values[0] if not row.empty else np.nan)
            ax.loglog(dims, vals, "o-", label=f"B={base}")

        # sqrt(n) reference line from naive
        if len(dims) >= 2 and naive_vals[0] is not None:
            ref = [naive_vals[0] * (n / dims[0]) ** 0.5 for n in dims]
            ax.loglog(dims, ref, ":", alpha=0.4, color="gray", label="~sqrt(n) ref")

        ax.set_xlabel("Ring Dimension (n)")
        ax.set_ylabel("Digit L2 Norm (mean)")
        ax.set_title(f"q={q}")
        ax.legend()
        ax.grid(True, alpha=0.3)

    fig.suptitle(f"Digit Norm Scaling with Ring Dimension ({max_folds} folds, 1000 trials)", y=1.02)
    fig.tight_layout()
    return fig


fig = plot_scaling()
fig.savefig(FIG_DIR / "scaling.png")
plt.close(fig)
print("Saved scaling.png")


# %% Summary table for paper
print("\n=== Summary Table (key metrics) ===")
print(
    summary[
        [
            "n",
            "q",
            "base",
            "num_folds",
            "l2_p99",
            "digit_l2_p99",
            "digit_linf_p99",
            "log_growth_rate",
        ]
    ].to_string(index=False)
)
print(f"\nFigures saved to: {FIG_DIR}")
