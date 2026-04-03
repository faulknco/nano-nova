"""
Phase boundary analysis: locating B_c(n, q) — the decomposition base threshold
where LatticeFold norm growth transitions from the "ordered" (flat) phase to
the "disordered" (explosive) phase.

Spin glass analogy:
  - B_c ↔ critical temperature T_c in the Edwards-Anderson model
  - log_growth_rate ↔ spin glass order parameter q_EA
  - Flat region (B < B_c) ↔ ordered/frozen phase (q_EA > 0)
  - Explosive region (B > B_c) ↔ paramagnetic phase (q_EA → 0)

Note: we use num_folds=1000 rows for B_c detection (most stable growth rate).
      Base B=0 is the naive (no decomposition) baseline — excluded from phase fit.

Usage:
    uv run python notebooks/09_phase_boundary.py
"""

import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

RESULTS_DIR = Path(__file__).parent.parent / "results" / "norm_growth_v2"
FIGURES_DIR = RESULTS_DIR / "figures"
FIGURES_DIR.mkdir(exist_ok=True)

FOLDS_FOR_FIT = 1000  # use deepest fold count for most stable growth rate
NAIVE_BASE = 0  # base=0 is the no-decomposition baseline


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def piecewise_linear(x, x_c, slope_left, slope_right, intercept):
    """Two-segment linear fit — finds the breakpoint x_c (= B_c)."""
    return np.where(
        x < x_c,
        intercept + slope_left * x,
        intercept + slope_left * x_c + slope_right * (x - x_c),
    )


def find_b_c(bases: np.ndarray, rates: np.ndarray) -> float:
    """
    Fit a piecewise linear model to log_growth_rate vs B.
    Returns the breakpoint B_c (float, interpolated between integer bases).
    Falls back to the base with the largest rate jump if fitting fails.
    """
    if len(bases) < 4:
        return float(bases[np.argmax(np.diff(rates))] + 1)

    x0 = [np.median(bases), 0.0, np.ptp(rates) / np.ptp(bases), rates[0]]
    bounds = ([bases[0], -np.inf, -np.inf, -np.inf], [bases[-1], np.inf, np.inf, np.inf])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            popt, _ = curve_fit(piecewise_linear, bases, rates, p0=x0, bounds=bounds, maxfev=5000)
            return float(np.clip(popt[0], bases[0], bases[-1]))
        except RuntimeError:
            jumps = np.diff(rates)
            return float(bases[np.argmax(jumps)] + 0.5)


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

df = pd.read_csv(RESULTS_DIR / "summary.csv")
df_deep = df[(df["base"] != NAIVE_BASE) & (df["num_folds"] == FOLDS_FOR_FIT)].copy()

ns = sorted(df_deep["n"].unique())
qs = sorted(df_deep["q"].unique())

q_labels = {q: f"q=2^{int(np.log2(q))}" if (q & (q - 1)) == 0 else f"q={q:,}" for q in qs}

# ---------------------------------------------------------------------------
# Figure 1: log_growth_rate vs B (one panel per q, lines per n)
# ---------------------------------------------------------------------------

fig, axes = plt.subplots(1, len(qs), figsize=(6 * len(qs), 5), sharey=False)
if len(qs) == 1:
    axes = [axes]

colors = plt.cm.viridis(np.linspace(0.15, 0.85, len(ns)))
b_c_table = {}

for ax, q in zip(axes, qs):
    for color, n in zip(colors, ns):
        subset = df_deep[(df_deep["n"] == n) & (df_deep["q"] == q)].sort_values("base")
        if subset.empty:
            continue

        bases = subset["base"].to_numpy()
        rates = subset["log_growth_rate"].to_numpy()

        ax.plot(bases, rates, "o-", color=color, label=f"n={n}", linewidth=1.8, markersize=5)

        b_c = find_b_c(bases, rates)
        b_c_table[(n, q)] = b_c

        # Mark B_c with a vertical dashed line (one per n, semi-transparent)
        ax.axvline(b_c, color=color, linestyle="--", linewidth=0.8, alpha=0.5)

    ax.set_xlabel("Decomposition base B", fontsize=12)
    ax.set_ylabel("log growth rate per fold", fontsize=12)
    ax.set_title(f"Growth rate vs B  ({q_labels[q]})", fontsize=13)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

fig.suptitle("Phase transition in LatticeFold norm growth", fontsize=14, fontweight="bold", y=1.02)
fig.tight_layout()
fig.savefig(FIGURES_DIR / "phase_growth_rate.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("Saved: figures/phase_growth_rate.png")

# ---------------------------------------------------------------------------
# Figure 2: Phase boundary B_c(n) for each q
# ---------------------------------------------------------------------------

fig, ax = plt.subplots(figsize=(7, 5))

markers = ["o", "s", "^", "D"]
for i, q in enumerate(qs):
    ns_with_data = [n for n in ns if (n, q) in b_c_table]
    b_cs = [b_c_table[(n, q)] for n in ns_with_data]

    ax.plot(
        ns_with_data,
        b_cs,
        markers[i % len(markers)] + "-",
        label=q_labels[q],
        linewidth=2,
        markersize=8,
    )

    # Fit B_c ~ a * log(n) + b (spin glass T_c scales logarithmically with system size)
    if len(ns_with_data) >= 3:
        log_ns = np.log(ns_with_data)
        try:
            coeffs = np.polyfit(log_ns, b_cs, 1)
            ns_fine = np.logspace(np.log2(ns_with_data[0]), np.log2(ns_with_data[-1]), 100, base=2)
            ax.plot(
                ns_fine,
                np.polyval(coeffs, np.log(ns_fine)),
                "--",
                color=ax.lines[-1].get_color(),
                linewidth=1,
                alpha=0.5,
            )
        except np.linalg.LinAlgError:
            pass

ax.set_xlabel("Ring dimension n", fontsize=12)
ax.set_ylabel("Critical base B_c", fontsize=12)
ax.set_title("Phase boundary B_c(n, q)\nLatticeFold ordered ↔ disordered transition", fontsize=13)
ax.set_xscale("log", base=2)
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)

fig.tight_layout()
fig.savefig(FIGURES_DIR / "phase_boundary.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("Saved: figures/phase_boundary.png")

# ---------------------------------------------------------------------------
# Figure 3: "Magnetisation" plot — digit_l2_p99 vs B, normalised by naive baseline
#   Analogous to M(T) in Ising: flat in ordered phase, collapses above T_c
# ---------------------------------------------------------------------------

df_naive = df[(df["base"] == NAIVE_BASE) & (df["num_folds"] == FOLDS_FOR_FIT)].set_index(["n", "q"])

fig, axes = plt.subplots(1, len(qs), figsize=(6 * len(qs), 5), sharey=True)
if len(qs) == 1:
    axes = [axes]

for ax, q in zip(axes, qs):
    for color, n in zip(colors, ns):
        subset = df_deep[(df_deep["n"] == n) & (df_deep["q"] == q)].sort_values("base")
        if subset.empty:
            continue

        try:
            naive_norm = df_naive.loc[(n, q), "digit_l2_p99"]
        except KeyError:
            naive_norm = subset["digit_l2_p99"].max()

        bases = subset["base"].to_numpy()
        # Normalised norm: 1 = same as naive (no benefit), 0 = perfect reduction
        norm_ratio = subset["digit_l2_p99"].to_numpy() / naive_norm

        ax.plot(bases, norm_ratio, "o-", color=color, label=f"n={n}", linewidth=1.8, markersize=5)

        b_c = b_c_table.get((n, q))
        if b_c:
            ax.axvline(b_c, color=color, linestyle="--", linewidth=0.8, alpha=0.5)

    ax.axhline(1.0, color="black", linestyle=":", linewidth=1, label="naive baseline")
    ax.set_xlabel("Decomposition base B", fontsize=12)
    ax.set_ylabel("Normalised digit L2 p99  (vs naive)", fontsize=12)
    ax.set_title(f"'Magnetisation' analogue  ({q_labels[q]})", fontsize=13)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

fig.suptitle(
    "Ordered phase: decompose-then-fold keeps norm far below naive baseline",
    fontsize=13,
    fontweight="bold",
    y=1.02,
)
fig.tight_layout()
fig.savefig(FIGURES_DIR / "phase_magnetisation.png", dpi=150, bbox_inches="tight")
plt.close(fig)
print("Saved: figures/phase_magnetisation.png")

# ---------------------------------------------------------------------------
# Print B_c table
# ---------------------------------------------------------------------------

print("\n=== Phase boundary B_c(n, q) ===")
print(f"{'n':>6}  {'q':>15}  {'B_c':>6}")
print("-" * 32)
for (n, q), b_c in sorted(b_c_table.items()):
    print(f"{n:>6}  {q:>15,}  {b_c:>6.2f}")
