"""
Visualization for norm growth experiments.

Generates publication-quality plots for the LatticeFold norm growth analysis:
- Norm trajectory plots (log scale)
- Heatmaps of final norm vs parameters
- Growth rate comparison across strategies
- Distribution histograms
"""

import numpy as np
import matplotlib.pyplot as plt

from .monte_carlo import ParameterResult


# Style configuration
COLORS = {
    "naive": "#dc2626",  # red
    2: "#2563eb",  # blue
    4: "#16a34a",  # green
    8: "#9333ea",  # purple
    16: "#ea580c",  # orange
}

LABELS = {
    0: "Naive (no decomp)",
    2: "B=2",
    4: "B=4",
    8: "B=8",
    16: "B=16",
}


def get_color(base: int) -> str:
    if base == 0:
        return COLORS["naive"]
    return COLORS.get(base, "#6b7280")


def get_label(base: int) -> str:
    return LABELS.get(base, f"B={base}")


def plot_norm_trajectories(
    results: list[ParameterResult],
    ring_dim: int,
    modulus: int,
    num_folds: int,
    save_path: str | None = None,
):
    """Plot mean L2 norm trajectories for different bases at fixed (n, q, N).

    This is the key visualization: how does norm grow over fold steps
    for naive vs decompose-then-fold with different bases?
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    filtered = [
        r
        for r in results
        if r.ring_dim == ring_dim and r.modulus == modulus and r.num_folds == num_folds
    ]

    for r in sorted(filtered, key=lambda x: x.base):
        steps = np.arange(1, r.num_folds + 1)
        color = get_color(r.base)
        label = get_label(r.base)

        axes[0].semilogy(steps, r.mean_l2_trajectory, color=color, label=label, linewidth=2)
        axes[1].semilogy(steps, r.mean_linf_trajectory, color=color, label=label, linewidth=2)

    q_bits = int(np.log2(modulus))
    for ax, norm_name in zip(axes, ["L2", "L∞"]):
        ax.set_xlabel("Fold step", fontsize=12)
        ax.set_ylabel(f"Mean {norm_name} norm (log scale)", fontsize=12)
        ax.set_title(f"{norm_name} Norm Growth (n={ring_dim}, q=2^{q_bits})", fontsize=14)
        ax.legend(fontsize=11)
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.show()


def plot_growth_rate_comparison(
    results: list[ParameterResult],
    num_folds: int,
    save_path: str | None = None,
):
    """Bar chart comparing log growth rates across parameters and strategies."""
    filtered = [r for r in results if r.num_folds == num_folds]
    if not filtered:
        print(f"No results for num_folds={num_folds}")
        return

    bases = sorted(set(r.base for r in filtered))
    ring_dims = sorted(set(r.ring_dim for r in filtered))
    moduli = sorted(set(r.modulus for r in filtered))

    fig, axes = plt.subplots(1, len(moduli), figsize=(7 * len(moduli), 6), sharey=True)
    if len(moduli) == 1:
        axes = [axes]

    for ax, q in zip(axes, moduli):
        q_bits = int(np.log2(q))
        x = np.arange(len(ring_dims))
        width = 0.8 / len(bases)

        for i, base in enumerate(bases):
            rates = []
            for n in ring_dims:
                match = [
                    r for r in filtered if r.ring_dim == n and r.modulus == q and r.base == base
                ]
                rates.append(match[0].l2_log_growth_rate if match else 0)

            offset = (i - len(bases) / 2 + 0.5) * width
            ax.bar(
                x + offset, rates, width, label=get_label(base), color=get_color(base), alpha=0.85
            )

        ax.set_xlabel("Ring dimension n", fontsize=12)
        ax.set_xticks(x)
        ax.set_xticklabels([str(n) for n in ring_dims])
        ax.set_title(f"q = 2^{q_bits}, {num_folds} folds", fontsize=14)
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3, axis="y")

    axes[0].set_ylabel("Log growth rate (slope of log||W_n|| vs n)", fontsize=12)
    plt.suptitle("Norm Growth Rate by Strategy", fontsize=16, y=1.02)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.show()


def plot_heatmap(
    results: list[ParameterResult],
    num_folds: int,
    metric: str = "l2_p99",
    save_path: str | None = None,
):
    """Heatmap of final norm across (base, ring_dim) for a fixed modulus and fold count.

    Args:
        results: Experiment results.
        num_folds: Filter to this fold count.
        metric: Which metric to plot (l2_mean, l2_p99, linf_max, etc.)
        save_path: Optional path to save figure.
    """
    filtered = [r for r in results if r.num_folds == num_folds]
    moduli = sorted(set(r.modulus for r in filtered))

    fig, axes = plt.subplots(1, len(moduli), figsize=(7 * len(moduli), 5))
    if len(moduli) == 1:
        axes = [axes]

    for ax, q in zip(axes, moduli):
        q_results = [r for r in filtered if r.modulus == q]
        bases = sorted(set(r.base for r in q_results))
        ring_dims = sorted(set(r.ring_dim for r in q_results))

        data = np.zeros((len(bases), len(ring_dims)))
        for i, base in enumerate(bases):
            for j, n in enumerate(ring_dims):
                match = [r for r in q_results if r.base == base and r.ring_dim == n]
                if match:
                    data[i, j] = getattr(match[0], metric)

        # Use log scale for the colormap
        data_log = np.log10(data + 1)

        im = ax.imshow(data_log, aspect="auto", cmap="YlOrRd")
        ax.set_xticks(range(len(ring_dims)))
        ax.set_xticklabels([str(n) for n in ring_dims])
        ax.set_yticks(range(len(bases)))
        ax.set_yticklabels([get_label(b) for b in bases])
        ax.set_xlabel("Ring dimension n")
        q_bits = int(np.log2(q))
        ax.set_title(f"q=2^{q_bits}, {num_folds} folds")

        # Annotate with actual values
        for i in range(len(bases)):
            for j in range(len(ring_dims)):
                val = data[i, j]
                text = f"{val:.0f}" if val < 1e6 else f"{val:.1e}"
                ax.text(j, i, text, ha="center", va="center", fontsize=9)

        plt.colorbar(im, ax=ax, label=f"log10({metric})")

    plt.suptitle(f"Norm Heatmap: {metric}", fontsize=14, y=1.02)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.show()
