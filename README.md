# nanoNova

An educational Python implementation of [Nova's folding scheme](https://eprint.iacr.org/2021/370) for Incrementally Verifiable Computation (IVC).

**This is not production cryptography.** It's a learning tool that maps code directly to the Nova paper's equations, with step-by-step Jupyter notebooks.

## What is Nova?

Nova is a folding scheme that enables efficient Incrementally Verifiable Computation (IVC). Instead of proving each step of a repeated computation independently, Nova *folds* two constraint system instances into one — deferring the expensive proof to the very end.

The key insight: by introducing a "relaxed" version of R1CS with an error vector E and scalar u, the cross-terms from combining two instances can be absorbed into the error, producing a valid folded instance with just one commitment per step.

## Structure

```
nano_nova/
├── field.py          # Finite field arithmetic (via galois)
├── r1cs.py           # R1CS and Relaxed R1CS data structures
├── commitment.py     # Toy Pedersen commitment
├── folding.py        # Core folding step
└── ivc.py            # IVC loop

notebooks/
├── 01_field_arithmetic.ipynb
├── 02_r1cs_basics.ipynb
├── 03_relaxed_r1cs.ipynb
├── 04_folding_step.ipynb
└── 05_ivc_demo.ipynb

experiments/
└── norm_growth/      # LatticeFold norm growth Monte Carlo

animations/           # Manim visualizations
```

## Quick Start

```bash
uv sync
uv run jupyter lab
```

## References

- [Nova paper (eprint 2021/370)](https://eprint.iacr.org/2021/370)
- [Arnaucube's Nova notes](https://raw.githubusercontent.com/arnaucube/math/master/notes_nova.pdf)
- [Veridise Nova tutorial](https://veridise.com/blog/learn-blockchain/intro-to-nova-zk-folding-schemes-folding-and-nova/)
