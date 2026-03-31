"""
Monte Carlo experiment runner for norm growth analysis.

Runs multiple trials of LatticeFold folding simulations across a grid
of parameters and collects statistical summaries. This is the core
experimental engine for the norm growth analysis.

Design: each parameter combination runs N_trials independent simulations.
For each trial, we track L2 and Linf norms at every fold step, then
aggregate across trials to get distributional statistics.
"""

from dataclasses import dataclass, field
from itertools import product

import numpy as np

from .lattice_fold_sim import FoldingConfig, simulate_folding
from .ring_arithmetic import RingParams


@dataclass
class ExperimentConfig:
    """Full experiment specification.

    Attributes:
        ring_dims: List of ring dimensions n to test.
        moduli: List of moduli q to test.
        bases: List of decomposition bases B to test (0 = naive).
        num_folds_list: List of fold counts to test.
        num_trials: Number of Monte Carlo trials per parameter combination.
        witness_length: Number of ring elements in witness vector.
        initial_bound: Initial coefficient bound for witnesses.
    """

    ring_dims: list[int] = field(default_factory=lambda: [64, 128])
    moduli: list[int] = field(default_factory=lambda: [2**16, 2**32])
    bases: list[int] = field(default_factory=lambda: [0, 2, 4, 8])
    num_folds_list: list[int] = field(default_factory=lambda: [100, 500])
    num_trials: int = 100
    witness_length: int = 4
    initial_bound: int = 16


@dataclass
class TrialSummary:
    """Summary statistics from one trial."""

    final_l2: float
    final_linf: int
    max_l2: float
    max_linf: int
    l2_trajectory: list[float]  # norm at each step
    linf_trajectory: list[int]


@dataclass
class ParameterResult:
    """Aggregated results for one parameter combination."""

    ring_dim: int
    modulus: int
    base: int  # 0 = naive
    num_folds: int
    num_trials: int

    # Distributional statistics of final L2 norm
    l2_mean: float = 0.0
    l2_std: float = 0.0
    l2_median: float = 0.0
    l2_p95: float = 0.0
    l2_p99: float = 0.0
    l2_max: float = 0.0

    # Distributional statistics of final Linf norm
    linf_mean: float = 0.0
    linf_std: float = 0.0
    linf_median: float = 0.0
    linf_p95: float = 0.0
    linf_p99: float = 0.0
    linf_max: float = 0.0

    # Mean trajectory (averaged over trials)
    mean_l2_trajectory: list[float] = field(default_factory=list)
    mean_linf_trajectory: list[float] = field(default_factory=list)

    # Log growth rate: slope of log(||W_n||) vs n
    l2_log_growth_rate: float = 0.0


def run_single_config(
    config: FoldingConfig, num_folds: int, num_trials: int, verbose: bool = False
) -> ParameterResult:
    """Run Monte Carlo trials for a single parameter configuration.

    Args:
        config: Folding configuration.
        num_folds: Number of fold steps per trial.
        num_trials: Number of independent trials.
        verbose: Print progress.

    Returns:
        ParameterResult with aggregated statistics.
    """
    summaries: list[TrialSummary] = []

    for trial in range(num_trials):
        results = simulate_folding(config, num_folds, seed=trial * 1000 + 42)

        # For decompose strategy, track intermediate digit norms (the critical metric)
        # For naive, these equal the recomposed norms
        l2_traj = [r.intermediate_digit_l2 for r in results]
        linf_traj = [r.intermediate_digit_linf for r in results]

        summaries.append(
            TrialSummary(
                final_l2=l2_traj[-1],
                final_linf=linf_traj[-1],
                max_l2=max(l2_traj),
                max_linf=max(linf_traj),
                l2_trajectory=l2_traj,
                linf_trajectory=linf_traj,
            )
        )

    # Aggregate
    final_l2s = np.array([s.final_l2 for s in summaries])
    final_linfs = np.array([s.final_linf for s in summaries])

    # Mean trajectories
    all_l2_trajs = np.array([s.l2_trajectory for s in summaries])
    all_linf_trajs = np.array([s.linf_trajectory for s in summaries], dtype=float)
    mean_l2_traj = np.mean(all_l2_trajs, axis=0).tolist()
    mean_linf_traj = np.mean(all_linf_trajs, axis=0).tolist()

    # Log growth rate: fit log(||W_n||) = a*n + b
    mean_log_l2 = np.mean(np.log(all_l2_trajs + 1e-10), axis=0)
    steps = np.arange(1, num_folds + 1)
    if len(steps) > 1:
        coeffs = np.polyfit(steps, mean_log_l2, 1)
        log_growth_rate = float(coeffs[0])
    else:
        log_growth_rate = 0.0

    base_label = config.base if config.uses_decomposition else 0

    result = ParameterResult(
        ring_dim=config.params.n,
        modulus=config.params.q,
        base=base_label,
        num_folds=num_folds,
        num_trials=num_trials,
        l2_mean=float(np.mean(final_l2s)),
        l2_std=float(np.std(final_l2s)),
        l2_median=float(np.median(final_l2s)),
        l2_p95=float(np.percentile(final_l2s, 95)),
        l2_p99=float(np.percentile(final_l2s, 99)),
        l2_max=float(np.max(final_l2s)),
        linf_mean=float(np.mean(final_linfs)),
        linf_std=float(np.std(final_linfs)),
        linf_median=float(np.median(final_linfs)),
        linf_p95=float(np.percentile(final_linfs, 95)),
        linf_p99=float(np.percentile(final_linfs, 99)),
        linf_max=float(np.max(final_linfs)),
        mean_l2_trajectory=mean_l2_traj,
        mean_linf_trajectory=mean_linf_traj,
        l2_log_growth_rate=log_growth_rate,
    )

    if verbose:
        strategy = f"B={base_label}" if base_label > 0 else "naive"
        print(
            f"  n={config.params.n}, q=2^{int(np.log2(config.params.q))}, "
            f"{strategy}, {num_folds} folds: "
            f"L2 mean={result.l2_mean:.1f}, p99={result.l2_p99:.1f}, "
            f"growth_rate={result.l2_log_growth_rate:.4f}"
        )

    return result


def run_experiment(config: ExperimentConfig, verbose: bool = True) -> list[ParameterResult]:
    """Run the full parameter sweep experiment.

    Args:
        config: Experiment configuration with parameter grids.
        verbose: Print progress.

    Returns:
        List of ParameterResult, one per parameter combination.
    """
    results = []
    total = (
        len(config.ring_dims) * len(config.moduli) * len(config.bases) * len(config.num_folds_list)
    )

    if verbose:
        print(f"Running {total} parameter combinations x {config.num_trials} trials each\n")

    count = 0
    for n, q, base, num_folds in product(
        config.ring_dims, config.moduli, config.bases, config.num_folds_list
    ):
        count += 1
        if verbose:
            print(f"[{count}/{total}]", end="")

        params = RingParams(n=n, q=q)
        folding_config = FoldingConfig(
            params=params,
            base=base,
            witness_length=config.witness_length,
            initial_bound=config.initial_bound,
        )

        result = run_single_config(folding_config, num_folds, config.num_trials, verbose=verbose)
        results.append(result)

    if verbose:
        print(f"\nDone: {len(results)} parameter combinations completed.")

    return results
