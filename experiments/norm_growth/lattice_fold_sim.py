"""
LatticeFold folding simulation with norm tracking.

Simulates the witness norm evolution through multiple folding steps
under different strategies:
1. Naive folding: W' = W1 + r*W2 (no decomposition)
2. Decompose-then-fold: decompose, fold digits, re-decompose

KEY INSIGHT: The strategies produce the same algebraic witness (same polynomial).
The difference is in what the prover COMMITS TO and what norms the verifier checks:

- Naive: prover commits to W directly. The verifier checks ||W|| < bound.
  After n folds, ||W|| grows without bound → commitment breaks.

- Decompose-then-fold: prover commits to DIGIT VECTORS separately.
  After re-decomposition, each digit has coefficients in [0, B-1].
  The verifier checks ||digit_k|| < B * sqrt(n * len).
  These norms are BOUNDED regardless of fold count.

So the key metric is: what norm does the verifier need to accept?
- For naive: ||W_recomposed|| (unbounded growth)
- For decompose: max(||digit_k||) over all k (bounded by B * sqrt(n * len))

BETWEEN re-decomposition steps (after fold, before re-decompose), the digit
norms are larger. This intermediate growth is what determines whether parameters
are viable — if intermediate norms exceed q, information is lost.

LatticeFold paper: eprint 2024/257, Section 4
"""

from dataclasses import dataclass

import numpy as np

from .decompose import decompose_vector, num_digits_for_params, recompose_vector
from .ring_arithmetic import RingElement, RingParams, RingVector


@dataclass
class FoldingConfig:
    """Configuration for a folding simulation."""

    params: RingParams
    base: int  # 0 = naive folding
    witness_length: int = 4
    initial_bound: int = 16

    @property
    def uses_decomposition(self) -> bool:
        return self.base > 0

    @property
    def num_digits(self) -> int:
        if not self.uses_decomposition:
            return 1
        return num_digits_for_params(self.params, self.base)


@dataclass
class FoldStepResult:
    """Norm measurements after one fold step."""

    step: int

    # Norm of the recomposed (algebraic) witness — same for naive and decompose
    recomposed_l2: float
    recomposed_linf: int

    # For decompose strategy: norm of digit vectors AFTER folding but BEFORE re-decompose
    # This is the critical intermediate norm that must stay below q
    intermediate_digit_l2: float
    intermediate_digit_linf: int

    # For decompose strategy: norm of digit vectors AFTER re-decomposition
    # This should be bounded by B * sqrt(n * witness_length)
    final_digit_l2: float
    final_digit_linf: int

    challenge_linf: int


def sample_challenge(params: RingParams) -> RingElement:
    """Sample a challenge from C_small (ternary: coefficients in {-1, 0, 1})."""
    return RingElement.random_small(params, bound=1)


def naive_fold_step(w1: RingVector, w2: RingVector, r: RingElement) -> RingVector:
    """Naive folding: W' = W1 + r * W2."""
    return w1 + w2.scalar_mul(r)


def decompose_fold_step_detailed(
    w_acc_digits: list[RingVector],
    w_fresh: RingVector,
    r: RingElement,
    base: int,
    num_digits: int,
) -> tuple[list[RingVector], list[RingVector], RingVector]:
    """Decompose-then-fold with detailed norm tracking.

    Returns:
        (new_digits, intermediate_digits, recomposed_witness)
        - new_digits: after re-decomposition (bounded norms)
        - intermediate_digits: after fold, before re-decompose (may be large)
        - recomposed_witness: the algebraic witness value
    """
    fresh_digits = decompose_vector(w_fresh, base, num_digits)

    # Fold digit-by-digit
    intermediate_digits = []
    for d_acc, d_fresh in zip(w_acc_digits, fresh_digits):
        folded = d_acc + d_fresh.scalar_mul(r)
        intermediate_digits.append(folded)

    # Recompose to get actual witness
    w_folded = recompose_vector(intermediate_digits, base)

    # Re-decompose for next round
    new_digits = decompose_vector(w_folded, base, num_digits)

    return new_digits, intermediate_digits, w_folded


def _max_digit_l2(digits: list[RingVector]) -> float:
    """Max L2 norm across all digit vectors."""
    return max(dv.l2_norm() for dv in digits)


def _max_digit_linf(digits: list[RingVector]) -> int:
    """Max Linf norm across all digit vectors."""
    return max(dv.linf_norm() for dv in digits)


def simulate_folding(
    config: FoldingConfig, num_folds: int, seed: int | None = None
) -> list[FoldStepResult]:
    """Simulate multiple folding steps and track norm evolution.

    Tracks three sets of norms:
    1. Recomposed witness norm (same for both strategies — the algebraic value)
    2. Intermediate digit norms (after fold, before re-decompose — must stay < q)
    3. Final digit norms (after re-decompose — bounded by B*sqrt(n*len))

    For naive folding, intermediate and final digit norms are set to the
    recomposed witness norm (no decomposition to measure).
    """
    if seed is not None:
        np.random.seed(seed)

    params = config.params
    results = []

    w_acc = RingVector.random_short(config.witness_length, params, config.initial_bound)

    if config.uses_decomposition:
        acc_digits = decompose_vector(w_acc, config.base, config.num_digits)

    for step in range(num_folds):
        w_fresh = RingVector.random_short(config.witness_length, params, config.initial_bound)
        r = sample_challenge(params)

        if config.uses_decomposition:
            new_digits, inter_digits, w_recomp = decompose_fold_step_detailed(
                acc_digits, w_fresh, r, config.base, config.num_digits
            )
            acc_digits = new_digits
            w_acc = w_recomp

            results.append(
                FoldStepResult(
                    step=step + 1,
                    recomposed_l2=w_recomp.l2_norm(),
                    recomposed_linf=w_recomp.linf_norm(),
                    intermediate_digit_l2=_max_digit_l2(inter_digits),
                    intermediate_digit_linf=_max_digit_linf(inter_digits),
                    final_digit_l2=_max_digit_l2(new_digits),
                    final_digit_linf=_max_digit_linf(new_digits),
                    challenge_linf=r.linf_norm(),
                )
            )
        else:
            w_acc = naive_fold_step(w_acc, w_fresh, r)

            results.append(
                FoldStepResult(
                    step=step + 1,
                    recomposed_l2=w_acc.l2_norm(),
                    recomposed_linf=w_acc.linf_norm(),
                    intermediate_digit_l2=w_acc.l2_norm(),
                    intermediate_digit_linf=w_acc.linf_norm(),
                    final_digit_l2=w_acc.l2_norm(),
                    final_digit_linf=w_acc.linf_norm(),
                    challenge_linf=r.linf_norm(),
                )
            )

    return results
