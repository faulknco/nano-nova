"""
Publication-quality figures from Rust norm growth sweep data.

Reads CSV output from: results/norm_growth/summary.csv and results/norm_growth/trajectories/
Produces figures for ZKProof 8 submission.

Usage:
    cd ~/Projects/nano-nova
    python notebooks/07_publication_figures.py

Or run cells interactively in an IDE.
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
        "savefig.bbox_inches": "tight",
    }
)

DATA_DIR = Path("results/norm_growth")
FIG_DIR = Path("results/norm_growth/figures")
FIG_DIR.mkdir(parents=True, exist_ok=True)

# %% Load summary data
summary = pd.read_csv(DATA_DIR / "summary.csv")
print(f"Loaded {len(summary)} parameter combos")
print(f"Ring dims: {sorted(summary['n'].unique())}")
print(f"Moduli: {sorted(summary['q'].unique())}")
print(f"Bases: {sorted(summary['base'].unique())}")
print(f"Fold counts: {sorted(summary['num_folds'].unique())}")
print(summary.head())


# %% Figure 1: Norm trajectories — naive vs decomposed (fixed n, q)
def plot_trajectories(n, q, num_folds, bases=None):
    """Plot L2 norm trajectories for different bases at fixed n, q, folds."""
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

        ax1.semilogy(
            traj["fold_step"], traj["l2_mean"], style, label=f"{label} (mean)", alpha=alpha
        )
        ax1.semilogy(traj["fold_step"], traj["l2_p99"], ":", alpha=0.4)

        ax2.semilogy(
            traj["fold_step"], traj["linf_mean"], style, label=f"{label} (mean)", alpha=alpha
        )
        ax2.semilogy(traj["fold_step"], traj["linf_p99"], ":", alpha=0.4)

    ax1.set_xlabel("Fold Step")
    ax1.set_ylabel("L2 Norm")
    ax1.set_title(f"L2 Norm Growth (n={n}, q={q})")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    ax2.set_xlabel("Fold Step")
    ax2.set_ylabel("L∞ Norm")
    ax2.set_title(f"L∞ Norm Growth (n={n}, q={q})")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    fig.suptitle(f"Norm Trajectories: n={n}, q={q}, {num_folds} folds, 1000 trials", y=1.02)
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


# %% Figure 2: Growth rate heatmap — base vs ring dimension
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

    # Annotate cells
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


# %% Figure 3: Final norm distributions — bar chart
def plot_final_norms(num_folds):
    """Bar chart comparing final L2 p99 across bases for each n."""
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
                vals.append(row["l2_p99"].values[0] if not row.empty else 0)
            label = "naive" if base == 0 else f"B={base}"
            ax.bar(x + i * width, vals, width, label=label, alpha=0.8)

        ax.set_xlabel("Ring Dimension")
        ax.set_ylabel("Final L2 Norm (p99)")
        ax.set_title(f"q={q}")
        ax.set_xticks(x + width * (len(bases) - 1) / 2)
        ax.set_xticklabels(dims)
        ax.set_yscale("log")
        ax.legend()
        ax.grid(True, alpha=0.3, axis="y")

    fig.suptitle(f"Final L2 Norm (p99) after {num_folds} folds, 1000 trials", y=1.02)
    fig.tight_layout()
    return fig


fig = plot_final_norms(max_folds)
fig.savefig(FIG_DIR / "final_norms.png")
plt.close(fig)
print("Saved final_norms.png")


# %% Figure 4: Tightness analysis — empirical p99 vs theoretical bound
def plot_tightness(q, num_folds):
    """Compare empirical p99 linf vs theoretical worst-case bound."""
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
                empirical.append(row["linf_p99"].values[0])
                # Theoretical worst case: n * (B-1) * num_folds
                # (very conservative — assumes all challenges are +1 and accumulate)
                theoretical.append(n * (base - 1))
            else:
                empirical.append(0)
                theoretical.append(0)

        ax.bar(x + i * width, empirical, width, label=f"B={base} (empirical p99)", alpha=0.8)
        ax.scatter(x + i * width + width / 2, theoretical, marker="_", s=200, color="red", zorder=5)

    ax.set_xlabel("Ring Dimension")
    ax.set_ylabel("L∞ Norm")
    ax.set_title(f"Empirical p99 vs Theoretical Bound (q={q}, {num_folds} folds)")
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


# %% Figure 5: Scaling with ring dimension
def plot_scaling():
    """How does final L2 norm scale with n for fixed base and fold count?"""
    subset = summary[summary["num_folds"] == max_folds]
    q_vals = sorted(subset["q"].unique())
    bases = [b for b in sorted(subset["base"].unique()) if b > 0]

    fig, axes = plt.subplots(1, len(q_vals), figsize=(7 * len(q_vals), 5))
    if len(q_vals) == 1:
        axes = [axes]

    for ax, q in zip(axes, q_vals):
        q_sub = subset[subset["q"] == q]
        dims = sorted(q_sub["n"].unique())

        for base in bases:
            vals = []
            for n in dims:
                row = q_sub[(q_sub["base"] == base) & (q_sub["n"] == n)]
                vals.append(row["l2_mean"].values[0] if not row.empty else np.nan)
            ax.loglog(dims, vals, "o-", label=f"B={base}")

        # Reference line: sqrt(n) scaling
        if len(dims) >= 2:
            ref = [vals[0] * (n / dims[0]) ** 0.5 for n in dims]
            ax.loglog(dims, ref, "k--", alpha=0.4, label="~sqrt(n) reference")

        ax.set_xlabel("Ring Dimension (n)")
        ax.set_ylabel("Final L2 Norm (mean)")
        ax.set_title(f"q={q}")
        ax.legend()
        ax.grid(True, alpha=0.3)

    fig.suptitle(f"Norm Scaling with Ring Dimension ({max_folds} folds, 1000 trials)", y=1.02)
    fig.tight_layout()
    return fig


fig = plot_scaling()
fig.savefig(FIG_DIR / "scaling.png")
plt.close(fig)
print("Saved scaling.png")

# %% Summary table for paper
print("\n=== Summary Table ===")
print(
    summary[
        ["n", "q", "base", "num_folds", "l2_mean", "l2_p99", "linf_p99", "log_growth_rate"]
    ].to_string(index=False)
)
print(f"\nFigures saved to: {FIG_DIR}")
