# LatticeFold Norm Growth Parameter Sweep — Design Spec

## Goal

Run large-scale Monte Carlo parameter sweeps of LatticeFold norm growth in Rust, outputting CSV for Python publication figures. Target: ZKProof 8 submission data.

## Parameter Ranges

- **Ring dimension (n):** [64, 128, 256, 512]
- **Modulus (q):** [2^16+1 (65537), 2^32, 2^64]
- **Decomposition base (B):** [0 (naive), 2, 4, 8, 16]
- **Fold counts:** [100, 500, 1000]
- **Trials per combo:** 1000
- **Total combos:** 4 × 3 × 5 × 3 = 180

Estimated runtime: ~12-18 hours on M4 MacBook Air (overnight).

## Architecture

New modules added to the existing `rust/` crate:

```
rust/src/
├── ring.rs          # Z_q[X]/(X^n+1) arithmetic + Karatsuba
├── decompose.rs     # Base-B digit decomposition/recomposition
├── norm_sim.rs      # Single-trial folding simulation with norm tracking
├── norm_sweep.rs    # Parameter sweep driver (Monte Carlo + CSV output)
└── bin/nano_nova.rs # + new `bench-norm` subcommand
```

## Module Details

### `ring.rs` — Polynomial Ring Z_q[X]/(X^n+1)

`RingElement` struct:
- `coeffs: Vec<u64>` — coefficients in [0, q)
- `n: usize` — ring dimension (power of 2)
- `q: u64` — modulus

Operations:
- `add(&self, other: &Self) -> Self` — coefficient-wise mod q
- `sub(&self, other: &Self) -> Self` — coefficient-wise mod q
- `mul(&self, other: &Self) -> Self` — negacyclic polynomial mul (X^n = -1)
  - Schoolbook O(n^2) for n ≤ 64
  - Karatsuba O(n^1.585) for n > 64
- `scalar_mul(&self, s: u64) -> Self` — multiply all coefficients by scalar mod q
- `neg(&self) -> Self` — negate all coefficients mod q
- `l2_norm(&self) -> f64` — sqrt(sum of centered_coeff^2), where centered = min(c, q-c)
- `linf_norm(&self) -> u64` — max of centered coefficients
- `random(n: usize, q: u64, bound: u64, rng: &mut impl Rng) -> Self` — coefficients in [0, bound)
- `random_ternary(n: usize, q: u64, rng: &mut impl Rng) -> Self` — coefficients in {0, 1, q-1}

Karatsuba for negacyclic multiplication:
- Split polynomial into two halves: f = f_lo + X^(n/2) * f_hi
- Three recursive multiplications instead of four
- Apply negacyclic reduction (X^n = -1) during recombination
- Base case at n ≤ 64: schoolbook
- Works for any modulus q (no root-of-unity requirement)

### `decompose.rs` — Base-B Digit Decomposition

Functions:
- `decompose(elem: &RingElement, base: u64) -> Vec<RingElement>` — split each coefficient into ceil(log_B(q)) digits, each in [0, B)
- `recompose(digits: &[RingElement], base: u64, q: u64) -> RingElement` — reconstruct: sum(digit_i * B^i) mod q
- `num_digits(q: u64, base: u64) -> usize` — ceil(log_B(q))

Matches Python `decompose.py` semantics exactly.

### `norm_sim.rs` — Single Trial Simulation

```rust
pub struct SimConfig {
    pub n: usize,
    pub q: u64,
    pub base: u64,       // 0 = naive (no decomposition)
    pub num_folds: usize,
    pub witness_length: usize,  // fixed at 4
    pub initial_bound: u64,     // fixed at 16
}

pub struct FoldStep {
    pub l2: f64,
    pub linf: u64,
    pub digit_l2: f64,   // intermediate digit norm (0 for naive)
    pub digit_linf: u64,
}

pub fn simulate_trial(config: &SimConfig, rng: &mut impl Rng) -> Vec<FoldStep>
```

Algorithm per trial:
1. Initialize `W_acc`: 4 random ring elements, coefficients in [0, 16)
2. If base > 0: decompose `W_acc` into digits
3. For each fold step:
   a. Sample fresh witness `W_fresh` (same distribution as initial)
   b. Sample ternary challenge `r`
   c. If naive (base=0): `W_acc[j] = W_acc[j] + r * W_fresh[j]` for each j
   d. If decomposed: fold digit-by-digit with challenge, recompose, record intermediate norms, re-decompose
   e. Record l2_norm, linf_norm of recomposed witness
4. Return per-step norm trajectory

### `norm_sweep.rs` — Monte Carlo Driver + CSV Output

```rust
pub struct SweepConfig {
    pub ring_dims: Vec<usize>,
    pub moduli: Vec<u64>,
    pub bases: Vec<u64>,
    pub fold_counts: Vec<usize>,
    pub num_trials: usize,
    pub seed: u64,
    pub outdir: PathBuf,
}
```

Sweep loop:
1. Create outdir and `trajectories/` subdirectory
2. Open `summary.csv`, write header row, flush
3. For each (n, q, base, num_folds) in cartesian product:
   a. Run `num_trials` trials with Xoshiro256PlusPlus seeded per-trial
   b. Aggregate statistics across trials: mean, std, median, p95, p99, max for l2 and linf
   c. Compute mean trajectory across trials
   d. Fit log-linear growth rate: log(l2[step]) = a*step + b, return slope `a`
   e. Append one row to `summary.csv`, flush immediately
   f. Write trajectory CSV to `trajectories/{n}_{q}_{base}_{folds}.csv`
   g. Print progress to stderr: `[42/180] n=256 q=65536 B=4 folds=500: 12.4s (est 3.2h remaining)`

### CLI Extension

New subcommand on the existing `nano-nova` binary:

```
nano-nova bench-norm \
  --ring-dims 64,128,256,512 \
  --moduli 65537,4294967296,18446744073709551616 \
  --bases 0,2,4,8,16 \
  --folds 100,500,1000 \
  --trials 1000 \
  --seed 42 \
  --outdir results/norm_growth/
```

All parameters have defaults matching the target sweep.

### CSV Output Format

**`summary.csv`** (appended incrementally, one row per combo):
```
n,q,base,num_folds,trials,l2_mean,l2_std,l2_median,l2_p95,l2_p99,l2_max,linf_mean,linf_std,linf_median,linf_p95,linf_p99,linf_max,log_growth_rate,elapsed_secs
64,65537,2,100,1000,12.3,1.4,12.1,14.8,16.2,18.1,8.1,1.2,7.9,10.0,11.3,13.0,0.023,4.2
```

**`trajectories/{n}_{q}_{base}_{folds}.csv`** (one file per combo, written on completion):
```
fold_step,l2_mean,l2_p99,linf_mean,linf_p99
0,1.2,1.5,1.0,1.0
1,2.1,3.4,1.8,2.9
```

### Streaming/Resumability

- Summary CSV is flushed after each combo — `tail -f` to monitor, no data loss on interrupt
- Trajectory CSVs written atomically per combo
- Progress printed to stderr with ETA
- No resume support (rerun from scratch if interrupted — combos are independent and fast enough)

### Dependencies

New in Cargo.toml:
```toml
rand_xoshiro = "0.6"
```

Updated release profile:
```toml
[profile.release]
opt-level = 3
lto = true
codegen-units = 1
```

### Testing

- Ring arithmetic: associativity, commutativity, negacyclic reduction (X^n = -1)
- Karatsuba vs schoolbook: verify identical results for all n
- Decompose/recompose roundtrip for various q, B
- Norm computation: cross-validate specific values against Python
- Single trial: run 1 trial, verify trajectory shape and final norms match Python

### Out of Scope

- GPU acceleration
- Rayon parallelism (single-threaded; add later if needed)
- Plotting (Python notebooks)
- NTT (Karatsuba is sufficient and works for all moduli)
- Phase transition analysis (interpretation, not code)
