# §2 Background

## 2.1 LatticeFold: Decompose-Then-Fold

### R1CS and Relaxed R1CS

A Rank-1 Constraint System (R1CS) over Z_q consists of matrices A, B, C ∈ Z_q^{m×n} and a
satisfying witness z ∈ Z_q^n such that:

```
(A·z) ∘ (B·z) = C·z
```

where ∘ denotes entry-wise (Hadamard) product. The *Relaxed R1CS* [KST21] generalises this:

```
(A·z) ∘ (B·z) = u·(C·z) + E
```

where u ∈ Z_q is a scalar *slack* and E ∈ Z_q^m is an *error vector*. The fresh instance
(before any folding) has u=1, E=0.

### The Nova Fold

Given two Relaxed R1CS instances (u₁, x₁, W₁, E₁) and (u₂, x₂, W₂, E₂) satisfying the same
shape (A, B, C), the Nova fold produces a single instance:

```
u'  = u₁ + r·u₂
x'  = x₁ + r·x₂
W'  = W₁ + r·W₂
E'  = E₁ + r·T + r²·E₂
```

where r ∈ Z_q is a random challenge and T is the cross-term:

```
T = A·z₁ ∘ B·z₂ + A·z₂ ∘ B·z₁ - u₁·C·z₂ - u₂·C·z₁
```

The folded instance satisfies Relaxed R1CS if both inputs did. IVC is achieved by treating
instance 2 as a fresh step and instance 1 as the running accumulator.

### LatticeFold's Decomposition Step

LatticeFold replaces the elliptic-curve commitments in Nova with lattice-based ones (Module-SIS).
The critical change is that the witness W ∈ Z_q^n must remain *short* for the lattice commitment
to be binding. After folding, W' = W₁ + r·W₂ can be as large as 2q — far outside the short
range.

The solution is *base-B decomposition*: write W in base B before folding:

```
W = Σ_{k=0}^{K-1} B^k · d_k,    K = ⌈log_B q⌉
```

where each digit vector d_k ∈ Z^n has entries in the balanced range [-(B-1)/2, (B-1)/2]. The
commitment is applied to (d_0, d_1, ..., d_{K-1}) rather than W directly. After folding, the
folded digit vectors d_k' must remain short enough for the security proof.

**The security condition.** LatticeFold's soundness requires:

```
||d_k'||₂ ≤ β    for all k
```

for some norm bound β. Current proofs set β using worst-case analysis: they bound the maximum
norm achievable by any sequence of challenges r_1, ..., r_N ∈ Z_q.

### Why Decompose-Then-Fold Helps

Without decomposition, folding multiplies witness norms by a factor of up to q per step — the
norm grows as q^N, making IVC useless beyond a handful of steps. With decomposition, each
digit d_k has norm at most (B-1)/2 before folding. The ideal case (no carry propagation between
digit levels) gives:

```
||d_k'||₂ ≤ (1 + |r|) · (B-1)/2 · √n
```

which grows at most linearly in N (via the |r| factor). However, digit levels are coupled through
carry terms — the actual growth is determined by the carry structure, which is the subject of §3.

---

## 2.2 The Edwards-Anderson Spin Glass

### Ising Spins and Disorder

The Ising model assigns a binary spin s_i ∈ {-1, +1} to each site i = 1, ..., N. In a
*ferromagnet*, all couplings J_ij = J > 0 favour alignment (s_i = s_j). In a *spin glass*,
couplings are random: some favour alignment, some anti-alignment. Frustration — the inability
of all couplings to be simultaneously satisfied — leads to complex, glassy behaviour.

The Sherrington-Kirkpatrick (SK) model [SK75] is the infinite-range spin glass:

```
H = -Σ_{i<j} J_ij · s_i · s_j,    J_ij ~ N(0, J²/N)
```

The 1/N normalisation makes the thermodynamics well-defined as N → ∞. The couplings J_ij
are *quenched*: drawn once and then fixed, with no thermal fluctuation.

### Order Parameter and Phase Transition

The Edwards-Anderson order parameter [EA75]:

```
q_EA = (1/N) Σ_i [<s_i>²]_J
```

measures the degree of spin freezing. Here <·> is the thermal (Boltzmann) average and [·]_J
is the average over the quenched disorder.

- **Ordered phase** (T < T_c): q_EA > 0. Spins are frozen in a disordered but stable
  configuration. The system has a well-defined local magnetisation at each site.
- **Paramagnetic phase** (T > T_c): q_EA = 0. Spins fluctuate freely; time-averaged
  magnetisation is zero.

In the SK model, the critical temperature is T_c = J — independent of system size (mean-field).
Below T_c, the free energy landscape has exponentially many metastable states (replica symmetry
breaking [Par79]).

### Finite-Size Scaling

In finite systems, the sharp phase transition is replaced by a crossover. The relevant
finite-size scaling form near T_c is:

```
q_EA(N, T) ≈ N^{-β/ν} · f((T - T_c) · N^{1/ν})
```

for critical exponents β, ν. For the SK model (mean-field), the crossover width scales as
N^{-1/4} — anomalously slow compared to short-range models. This means the transition
appears sharp even in moderately sized systems (N ~ 100), which is consistent with our
observation that the norm growth transition is sharp across n = 64–256.

### Why the SK Model Is the Right Analogy

The SK model is appropriate here (rather than, say, the 1D or 2D Ising model) for two reasons:

1. **All-to-all interactions.** In base-B decomposition, the carry at position i at level k
   depends on d_k^(1)[i] and d_k^(2)[i] — a local (position-by-position) interaction. But
   across the n ring positions, the ring multiplication (in Z_q[X]/(X^n+1)) creates all-to-all
   coupling when challenges r include polynomial multiplication. This is effectively a
   fully-connected interaction graph.

2. **Quenched Gaussian disorder.** Fiat-Shamir challenges, under the random oracle model, are
   uniform on Z_q. In the large-q limit, their centering makes them approximately Gaussian —
   matching the SK coupling distribution.

---

## 2.3 The Ising IVC Connection (Pedagogical Bridge)

The 1D Ising model partition function on a chain of N spins is:

```
Z_N = Σ_{s_1,...,s_N} exp(-β · Σ_i J·s_i·s_{i+1}) = Tr(T^N)
```

where T is the 2×2 transfer matrix:

```
T = [[e^{βJ}, e^{-βJ}],
     [e^{-βJ}, e^{βJ}]]
```

This is exactly the `F^N(z₀)` structure Nova IVC was designed for: each spin contributes one
step of a repeated computation, and `ivc_verify` confirms the full chain in O(1) regardless
of N.

In our implementation (`notebooks/08_ising_ivc.py`), we use integer couplings A=3, B=1
(i.e., T = [[3,1],[1,3]]) to avoid fixed-point arithmetic in the finite field. The dominant
eigenvalue is λ+ = A+B = 4, giving Z_N ≈ 2·4^N for large N.

**Why the 1D model is always ordered.** The 1D Ising model has no finite-temperature phase
transition: T_c = 0 (correlation length ξ = 1/ln(λ+/λ-) is finite for all T > 0). In the
language of §3.5, the integer transfer matrix is always in the ordered phase — digit norms
stay exactly at their initial values, and ivc_verify always passes. This is a useful sanity
check for the mapping.

**The 2D extension.** The 2D Ising model on an L×M strip has a transfer matrix of dimension
2^L × 2^L. For L=3, this is an 8×8 matrix — a valid Nova R1CS step. Crucially, the 2D model
has a phase transition at T_c = 2J/ln(1+√2) ≈ 2.27J (Onsager 1944). At T_c, the spectral
gap of the transfer matrix closes: λ+ → λ-. In the IVC accumulator, this would manifest as
the folding challenge r inducing a norm explosion at the critical step. This is the subject
of future work (§7.1).
