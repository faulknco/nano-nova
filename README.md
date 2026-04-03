# nanoNova

An educational implementation of [Nova's folding scheme](https://eprint.iacr.org/2021/370) for Incrementally Verifiable Computation (IVC), with a novel connection to statistical mechanics.

**This is not production cryptography.** It's a research tool that maps code directly to the Nova paper's equations — built to make the ideas accessible and experimentally explorable.

---

## The Core Idea

Nova folds two R1CS constraint instances into one via a random linear combination. Repeat this for N steps and you get IVC: a proof that a computation `F^N(z₀) = zₙ` was executed correctly, verified in constant time regardless of N.

This repo makes that concrete through three lenses:

1. **Python implementation** — R1CS, relaxed R1CS, folding, and IVC from scratch
2. **Manim animations** — 7 scenes explaining R1CS, the fold, and IVC visually
3. **Physics connection** — the 1D Ising transfer matrix is a natural IVC circuit; the partition function becomes a cryptographic accumulator

---

## The Ising IVC Connection

The 1D Ising model partition function is computed by iterating a 2×2 transfer matrix:

```
v_{k+1} = T · v_k,    Z_N = sum(v_N)
```

This is exactly the `F^N(z₀)` structure Nova was designed for. Each transfer matrix multiply is one R1CS constraint. After N spins, `ivc_verify` confirms the full chain in O(1) — the verifier doesn't care how many spins there were.

The analogy runs deeper:

| Statistical Mechanics | Nova IVC |
|---|---|
| Transfer matrix T | Step function F |
| Partition function Z = Tr(T^N) | Accumulated R1CS instance |
| RG coarse-graining | Recursive proof compression |
| Correlation length ξ ~ 1/ln(λ+/λ-) | LatticeFold norm growth rate |
| Thermodynamic limit | O(1) verifier cost |

The renormalization group integrates out short-wavelength modes to produce a smaller effective system. Nova folds fresh instances into an accumulator that stays the same size. Both are compression operations that preserve essential structure. This connection has not appeared in the literature.

---

## Repository Structure

```
nano_nova/            # Core Python library
├── field.py          # Finite field arithmetic (GF(2^61-1) via galois)
├── r1cs.py           # R1CS and Relaxed R1CS data structures
├── commitment.py     # Toy commitment scheme
├── folding.py        # Core Nova fold step
└── ivc.py            # IVC prover and verifier

notebooks/
├── 01–05_*.ipynb     # Step-by-step Nova walkthrough
├── 06_norm_growth_analysis.ipynb   # LatticeFold norm analysis
├── 07_publication_figures.py       # Figure generation from sweep data
└── 08_ising_ivc.py                 # 1D Ising as an IVC circuit

rust/                 # High-performance norm growth sweep
└── src/
    ├── norm_sweep.rs               # Monte Carlo digit norm measurement
    └── bin/nano_nova.rs            # CLI entry point

animations/           # Manim scenes (rendered at 1080p60)
├── scene_01_r1cs.py  # R1CSIntro, R1CSEquation, R1CSRelaxation
├── scene_02_folding.py  # FoldingSetup, TheFold
├── scene_03_ivc.py   # IVCAccumulation, IVCPunchline
└── common/           # Shared theme and components

results/
└── norm_growth_v2/   # Sweep results: n=64–512, B=2–16, 1000 folds
    ├── summary.csv
    ├── trajectories/
    └── figures/
```

---

## Quick Start

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/yourusername/nano-nova
cd nano-nova
uv sync

# Run the Ising IVC demo
uv run python notebooks/08_ising_ivc.py

# Step-by-step notebooks
uv run jupyter lab

# Render animations (requires LaTeX and ffmpeg)
uv sync --extra animations
cd animations
manim -pql scene_01_r1cs.py R1CSEquation
```

For the Rust norm sweep:

```bash
cd rust
cargo run --release --bin nano-nova -- bench-norm \
  --ring-dims 64,128,256 \
  --moduli 65537 \
  --bases 0,2,4,8,16 \
  --folds 100,500,1000 \
  --trials 1000 \
  --outdir ../results/norm_growth_v2
```

---

## LatticeFold Norm Growth

A parallel thread of this research measures how digit norms grow under repeated folding — relevant to LatticeFold's security proof, which bounds the norm of decomposed witness vectors.

Key finding: the decompose-then-fold strategy keeps digit L2 norms **100–400× smaller** than naive folding, across ring dimensions n=64–512 and decomposition bases B=2–16. The reduction ratio is stable regardless of fold depth.

Figures are in `results/norm_growth_v2/figures/`.

---

## References

- [Nova: Recursive Zero-Knowledge Arguments from Folding Schemes](https://eprint.iacr.org/2021/370) — Kothapalli, Setty, Tzialla (2021)
- [LatticeFold](https://eprint.iacr.org/2024/257) — Boneh, Chen (2024)
- [SuperNova](https://eprint.iacr.org/2022/1758) — Kothapalli, Setty (2022)
- [Arnaucube's Nova notes](https://raw.githubusercontent.com/arnaucube/math/master/notes_nova.pdf)

---

## License

MIT. Not for production use.
