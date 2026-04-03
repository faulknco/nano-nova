# §3 The Spin Glass ↔ LatticeFold Mapping

## 3.1 Overview

We establish a formal correspondence between the Edwards-Anderson (EA) spin glass model and
the norm growth dynamics of LatticeFold's decompose-then-fold strategy. The core claim is:

> **Carry propagation in base-B digit decomposition is structurally identical to spin-spin
> interaction in a disordered magnetic system. The norm explosion threshold B_c is the
> cryptographic analogue of the spin glass critical temperature T_c.**

The correspondence is not merely analogical — it arises from the same mathematical object:
a disordered interaction Hamiltonian with quenched randomness.

---

## 3.2 Notation

| Symbol | Meaning |
|---|---|
| n | Ring dimension (Z_q[X]/(X^n + 1)) |
| q | Modulus |
| B | Decomposition base |
| K = ⌈log_B q⌉ | Number of digit levels |
| W ∈ Z_q^n | Witness vector |
| d_k ∈ Z^n | k-th digit vector, balanced: d_k[i] ∈ [-(B-1)/2, (B-1)/2] |
| r ∈ Z_q | Fiat-Shamir folding challenge |
| N | Total fold depth |
| J_ij | EA coupling between spins i and j |
| s_i ∈ {±1} | Ising spin |
| q_EA | Edwards-Anderson order parameter |

---

## 3.3 The Edwards-Anderson Spin Glass

The Sherrington-Kirkpatrick (SK) mean-field spin glass has Hamiltonian:

```
H = -Σ_{i<j} J_ij s_i s_j
```

where J_ij ~ N(0, J²/N) are *quenched* (frozen) random couplings. The key feature is that
disorder is frozen at the start and fixed throughout — there is no thermal average over couplings,
only over spins.

The Edwards-Anderson order parameter:

```
q_EA = (1/N) Σ_i [<s_i>²]_J
```

where <·> is the thermal average and [·]_J is the disorder average. In the ordered (spin glass)
phase: q_EA > 0 (spins are frozen in some configuration). In the disordered (paramagnetic)
phase: q_EA = 0 (spins fluctuate freely).

The phase boundary in the SK model is at T_c = J — below this temperature, the system
enters the spin glass phase.

---

## 3.4 Carry Propagation as Spin-Spin Interaction

**Setup.** Given W ∈ Z_q^n, its balanced base-B decomposition is:

```
W = Σ_{k=0}^{K-1} B^k d_k,   d_k ∈ Z^n,   d_k[i] ∈ [-(B-1)/2, (B-1)/2]
```

After one fold with challenge r, the folded witness is:

```
W' = W_1 + r · W_2
```

The naive expectation is that the digits fold as d_k' = d_k^(1) + r · d_k^(2). This fails
because the sum may exceed the digit range, generating a *carry*:

```
d_k^(1)[i] + r · d_k^(2)[i] = d_k'[i] + B · c_{k+1}[i]
```

where c_{k+1}[i] ∈ {-1, 0, 1} is the carry propagated from level k to level k+1. The actual
folded digit vector at level k is:

```
d_k'[i] = d_k^(1)[i] + r · d_k^(2)[i] + c_k[i] - B · c_{k+1}[i]
```

**Carry = interaction.** Each carry c_{k+1}[i] couples digit level k to level k+1 at position i.
It is generated when the intermediate sum exceeds the balanced range — an event that depends on
the values of *both* d_k^(1)[i] and d_k^(2)[i], mediated by the random challenge r.

This is structurally identical to a spin interaction: c_{k+1}[i] ≡ J_{k,i} · s_k^(1)[i] · s_k^(2)[i],
where r plays the role of the coupling constant and the carry event plays the role of a spin flip.

**Quenched disorder.** In the full IVC protocol over N folds, the challenges r_1, ..., r_N are
determined by the Fiat-Shamir hash of the transcript. From the perspective of any given fold,
these are fixed — they are *quenched* disorder, exactly as J_ij is quenched in the EA model.

---

## 3.5 Formal Identification Table

| EA Spin Glass | LatticeFold (decompose-then-fold) |
|---|---|
| Spin s_i ∈ {±1} | Digit component d_k[i] ∈ Z (bounded) |
| Quenched coupling J_ij ~ N(0, J²/N) | Quenched Fiat-Shamir challenge r_t |
| Thermal fluctuation (T) | Decomposition base B (sets digit range) |
| Spin-spin interaction J_ij s_i s_j | Carry term c_k[i] from digit overflow |
| Edwards-Anderson order parameter q_EA | Normalised log norm growth rate r/N |
| Ordered phase (T < T_c, q_EA > 0) | B < B_c: norms stay bounded |
| Paramagnetic phase (T > T_c, q_EA = 0) | B > B_c: norms grow explosively |
| Critical temperature T_c | Critical base B_c |
| Replica symmetry breaking (RSB) | Carry cascade: high-level digits blow up first |
| Free energy F(β) | Folded norm ||d_N||₂ as function of (N, B, q) |

---

## 3.6 The Carry Probability and the Phase Boundary

**Single carry probability.** For digit components drawn uniformly from the balanced range
d[i] ~ Uniform{-(B-1)/2, ..., (B-1)/2}, the sum d^(1)[i] + r · d^(2)[i] for r ~ Uniform(Z_q)
has variance:

```
σ² ≈ (1 + r²) · (B² - 1) / 12
```

For large n, by the central limit theorem across digit positions, the carry probability at
level k is:

```
p_carry(B, r) = 2 · Φ(-(B-1) / (2σ))
              ≈ 2 · Φ(-√(3(B-1)² / ((1+r²)(B²-1))))
              → 2 · Φ(-√(3/(1+r²)))   as B → ∞
```

where Φ is the standard normal CDF.

**Phase boundary condition.** The system is in the ordered phase when carry propagation
*does not percolate* through the K-level digit hierarchy. The critical condition is:

```
p_carry(B_c, r) = p_percolation
```

where p_percolation is the percolation threshold of the carry cascade process. For the
one-dimensional carry chain (level k feeds level k+1), the threshold is p_c = 1 (carries
always propagate). For the n-dimensional case, carries at different positions can cancel
each other — the effective threshold depends on n.

This cancellation is why B_c shifts with n: larger n provides more opportunities for carry
cancellation across ring positions (similar to the way connectivity affects percolation in
finite graphs). The empirical fit B_c ~ a · log(n) (§5) is consistent with this picture —
logarithmic finite-size scaling is the hallmark of mean-field critical points, which the SK
spin glass (and this system) exhibits.

**Remark.** A complete analytical derivation of B_c(n, q) via the replica method is left for
future work (§7). The empirical evidence in §4 strongly supports the existence of a sharp
phase boundary and its n-dependence.

---

## 3.7 Security Implications

The spin glass correspondence reframes LatticeFold's security argument:

**Current proofs** bound the norm of folded digits in the *worst case*: a sequence of maximally
unfavourable challenges. This is the high-T (paramagnetic) regime — the system is assumed to
always be disordered.

**Our claim** is that the *typical* LatticeFold execution operates in the ordered phase. Honest
prover challenges (from Fiat-Shamir) are not adversarially chosen. Under the random oracle
model, they are i.i.d. — exactly the quenched Gaussian disorder of the SK model. In the
ordered phase, digit norms are O(√n · √B) rather than the worst-case O(B^K · √n).

Concretely:

- Current security proofs assume norm growth at the worst-case rate (paramagnetic phase)
- Empirical results show growth at the ordered-phase rate, 32–383× smaller
- The gap between worst-case and typical-case grows with fold depth N

This suggests that LatticeFold's soundness parameters can be tightened significantly for
honest executions. The tightest parameters correspond to operating well inside the ordered
phase (B ≪ B_c), where the spin glass analogy predicts the smallest norm growth.

**Caveat.** This analysis assumes the Fiat-Shamir challenges behave as random, independent
draws — standard under the random oracle model. A malicious prover who can bias the challenges
could in principle push the system toward the disordered phase. Resistance to such attacks
falls back on the standard LWE/RLWE hardness assumptions.

---

## 3.8 Connection to the Ising IVC Demo

The 1D Ising model in this repo (§2, `notebooks/08_ising_ivc.py`) is not merely pedagogical —
it is the simplest exactly-solvable instance of the correspondence described here.

The transfer matrix T = [[A, B], [B, A]] with integer couplings A=3, B=1 is the R1CS step
function. Each Nova fold absorbs one transfer matrix multiplication. The IVC accumulator after
N steps encodes the partition function Z_N = Tr(T^N).

In the language of §3.5: the transfer matrix eigenvalues play the role of spin couplings, and
the spectral gap (λ+ - λ-) = 2(A-B) = 4 is the analogue of J (the coupling strength). The
system is always in the ordered phase for this integer toy, which is why the IVC chain is
perfectly stable and the proof is trivially valid at every step.

The 2D Ising model, by contrast, has a genuine phase transition at T_c = 2/ln(1+√2). Extending
the IVC demo to a 2D strip transfer matrix would allow observing — for the first time — how a
phase transition manifests in a cryptographic accumulator. This is the subject of future work (§7).
