# §6 Discussion: Parameter Recommendations

## 6.1 What the Phase Boundary Means for Practitioners

The core message of §3–5 is that LatticeFold's decompose-then-fold strategy has two operating
regimes, and the choice of decomposition base B determines which one you are in:

- **B ≪ B_c (deep ordered phase):** digit norms grow 32–383× slower than worst-case bounds.
  Security proofs are valid but overly conservative. Parameters can be tightened.
- **B ~ B_c (near the transition):** norm growth accelerates sharply. Small changes in B can
  shift the system into the disordered regime. Avoid.
- **B > B_c (disordered phase):** worst-case bounds become tight. Use the LatticeFold paper's
  original parameter recommendations.

For most practical deployments, B ∈ {2, 4} is well inside the ordered phase across all
(n, q) combinations tested. This is the safe operating range.

## 6.2 Recommended Parameters

Based on the empirical phase boundary (§5, Table 5.1), we recommend:

| Use case | n | q | B | Expected norm reduction | Notes |
|---|---|---|---|---|---|
| Lightweight IVC (IoT, mobile) | 64–128 | 65537 | 2 | ~370× | B=2 is deepest ordered; slowest per-fold |
| Standard IVC | 128–256 | 65537 | 4 | ~145× | Good tradeoff: 145× reduction, faster than B=2 |
| High-throughput IVC | 256–512 | 2^32 | 4 | ~145× | Larger n doesn't hurt reduction ratio |
| Avoid | any | any | ≥16 | 32× or less | Approaching B_c for n≤256 |

**Rationale for B=4 as the default.** B=4 gives 145× reduction at negligible cost over B=2
(one extra digit level). It is stable across all tested n and q values, and sits well below B_c
even for n=64. B=2 gives slightly more reduction (371×) but requires more digit levels K = ⌈log₂q⌉
vs K = ⌈log₄q⌉ — at q=65537, this is 17 vs 9 levels, roughly doubling the commitment size.

## 6.3 The q-Independence Observation

A perhaps surprising finding is that reduction ratios are numerically identical for q=65537
and q=4,294,967,296 (Table 4.1). This means:

1. The ordered/disordered phase structure is determined by B and n alone.
2. q only affects the *absolute* norm scale (more digit levels → higher absolute norms), not
   the *relative* benefit of decomposition.
3. Practitioners can freely choose q for other reasons (FFT-friendliness, security level) without
   worrying that it will push the system out of the ordered phase.

This is consistent with the spin glass picture: the phase boundary T_c = J in the SK model does
not depend on the number of spin states (the analogue of q). What matters is the coupling
strength (the analogue of B) and system size (n).

## 6.4 Limitations

**This analysis does not apply to adversarial provers.** The ordered-phase behaviour relies on
Fiat-Shamir challenges being pseudorandom. An adversarial prover with the ability to bias
challenges could in principle push the system toward the disordered phase. Standard LatticeFold
security proofs (which assume worst-case challenges) remain the correct basis for soundness.

**N=1000 is the limit of our sweep.** The stability of the reduction ratio across N=100–1000
is encouraging, but we have not tested arbitrarily deep IVC chains. Extrapolating to N=10^6
(a realistic production depth) requires either the theoretical bound from §3 or longer sweeps.

**B_c is empirically determined.** The phase boundary values in Table 5.1 are fitted from
Monte Carlo data, not analytically derived. The error bars (§5) reflect statistical uncertainty,
not the approximation error in the piecewise linear fit. The replica-method calculation of §7.2
would provide an analytical B_c.

## 6.5 Comparison to Existing LatticeFold Parameters

The LatticeFold paper [BC24] recommends parameters based on the Module-SIS security level
required. Their norm bounds are worst-case and implicitly assume the disordered phase. Our
results suggest that for any deployment using B ≤ 8, the effective security margin is
significantly higher than the proof requires — or equivalently, smaller ring dimensions n
could achieve the same security level.

A concrete example: if the LatticeFold proof requires n=256 with B=4 to keep norms below β
at worst-case growth, our results suggest n=128 with B=4 achieves the *same typical-case norm*
(since the reduction ratio is ~145× for both). This is a 2× reduction in communication cost.
