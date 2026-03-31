# nanoNova Rust Port — Design Spec

## Goal

Port nanoNova's educational Nova folding scheme from Python to Rust for speed (parameter sweeps at N_TRIALS=1000, n=256/512) while keeping it readable and educational. Trait-based architecture allows swapping in real crypto primitives later for Phase 4 (Sonobe benchmarks).

## Location

`~/Projects/nano-nova/rust/` — inside the existing repo alongside Python code.

## Architecture

```
rust/
├── Cargo.toml
├── src/
│   ├── lib.rs          # re-exports
│   ├── field.rs        # Fp61 (2^61-1) with Field trait
│   ├── matrix.rs       # Matrix trait + DenseMatrix impl
│   ├── commitment.rs   # Commitment trait + ToyCommitment (SHA256)
│   ├── r1cs.rs         # R1CSShape, RelaxedR1CSInstance/Witness
│   ├── folding.rs      # NIFS: cross-term, Fiat-Shamir, fold
│   ├── ivc.rs          # IVCProof, ivc_prove, ivc_verify
│   └── examples.rs     # Fibonacci circuit
├── src/bin/
│   └── nano_nova.rs    # CLI: prove/verify/bench commands
└── tests/
    └── nova_tests.rs   # Port of Python test suite
```

## Core Traits

### `Field`

Arithmetic over a prime field. Methods: `add`, `sub`, `mul`, `inv`, `zero`, `one`, `random`, `from_u64`, `to_bytes`.

Initial impl: `Fp61` — the Mersenne prime 2^61 - 1. All arithmetic in u64 with Mersenne reduction (shift + add). Matches the Python `galois.GF(2**61 - 1)` exactly.

Future impl: arkworks `Fp256<BN254Fr>` for production benchmarks.

### `MatrixOps<F: Field>`

Matrix-vector products. Methods: `mul_vec(&self, v: &[F]) -> Vec<F>`, `rows(&self) -> usize`, `cols(&self) -> usize`.

Initial impl: `DenseMatrix<F>` — row-major `Vec<F>`, dimensions stored explicitly. Matches Python numpy dense arrays.

Future impl: `CsrMatrix<F>` for circuits with >1000 constraints.

### `CommitmentScheme<F: Field>`

Binding commitments. Methods: `commit(&self, v: &[F]) -> Self::Output`, `commit_with_blinding(&self, v1: &[F], v2: &[F], r: F) -> Self::Output`.

Initial impl: `ToyCommitment` — SHA256 hash of serialized vector bytes. Matches Python implementation.

Future impl: Pedersen commitments over arkworks curves.

## Data Structures

All generic over `F: Field`:

### `R1CSShape<F, M: MatrixOps<F>>`

- `a: M, b: M, c: M` — constraint matrices
- `m: usize` — number of constraints
- `n: usize` — total variables (1 + |x| + |w|)
- `l: usize` — number of public inputs

Methods:
- `is_satisfied(&self, x: &[F], w: &[F]) -> bool` — check Az . Bz = Cz
- `is_relaxed_satisfied(&self, instance, witness) -> bool` — check Az . Bz = u*Cz + E
- `make_z(&self, x: &[F], w: &[F]) -> Vec<F>` — build z = (1, x, w)
- `make_relaxed_z(&self, u: F, x: &[F], w: &[F]) -> Vec<F>` — build z = (u, x, w)

### `RelaxedR1CSInstance<F, C>`

- `com_e: C` — commitment to error vector
- `u: F` — relaxation scalar
- `x: Vec<F>` — public inputs
- `com_w: C` — commitment to witness

### `RelaxedR1CSWitness<F>`

- `e: Vec<F>` — error vector
- `w: Vec<F>` — witness vector

### `IVCProof<F, C>`

- `instance: RelaxedR1CSInstance<F, C>`
- `witness: RelaxedR1CSWitness<F>`
- `z_current: Vec<F>` — current state
- `num_steps: usize`

## Algorithms

No algorithmic changes from Python. Identical math, identical Fiat-Shamir transcript construction.

### Folding (`folding.rs`)

1. `compute_cross_term(shape, inst1, wit1, inst2, wit2) -> Vec<F>` — T = Az1.Bz2 + Az2.Bz1 - u1*Cz2 - u2*Cz1
2. `fiat_shamir_challenge(com_t, inst1, inst2) -> F` — SHA256 transcript, first 8 bytes as u64, mod p
3. `fold(shape, inst1, wit1, inst2, wit2) -> (RelaxedR1CSInstance, RelaxedR1CSWitness)` — compute T, challenge r, fold E/u/x/W

### IVC (`ivc.rs`)

1. `ivc_prove(shape, step_fn, witness_fn, z0, num_steps) -> IVCProof` — accumulate via repeated folding
2. `ivc_verify(shape, proof) -> bool` — check relaxed R1CS on accumulated instance

### Fibonacci Circuit (`examples.rs`)

- `fibonacci_circuit() -> R1CSShape` — 3 constraints, 6 variables, 4 public inputs
- `fibonacci_step(z: &[F]) -> Vec<F>` — (a,b) -> (b, a+b)
- `fibonacci_witness(z: &[F]) -> Vec<F>` — [a+b]

Variable layout: z = (1, z1_in, z2_in, z1_out, z2_out, w0) — identical to Python.

## CLI (`src/bin/nano_nova.rs`)

Uses `clap` for argument parsing.

### Commands

```
nano-nova prove --circuit fibonacci --steps 1000
    Prove IVC, print timing and verification result.

nano-nova bench --circuit fibonacci --steps 10,100,1000 --trials 100 --output results.csv
    Run parameter sweep, output CSV.
```

### CSV Output Format

```
circuit,steps,trial,prove_time_us,verify_time_us,proof_size_bytes
fibonacci,1000,1,4523,12,192
```

Python notebooks read this with pandas for publication figures.

## Testing

### Ported from Python (10 tests)

1. `test_circuit_dimensions` — m=3, n=6, l=4
2. `test_satisfied_instance` — (1,1) -> (1,2) with w=[2]
3. `test_wrong_witness_rejected` — invalid witness fails
4. `test_lifted_instance_satisfies_relaxed` — r1cs_to_relaxed preserves satisfaction
5. `test_trivial_instance` — u=0, E=0, W=0 satisfies trivially
6. `test_fold_two_instances` — fold(valid, valid) -> valid
7. `test_fold_with_trivial` — fold(trivial, valid) -> valid
8. `test_multiple_folds` — 10 sequential folds maintain validity
9. `test_ivc_fibonacci_10_steps` — z_current = [89, 144]
10. `test_ivc_fibonacci_100_steps` — verifies after 100 steps

### New Rust-specific tests

- Field property tests: associativity, commutativity, multiplicative inverse, additive identity
- Cross-validation: hardcoded intermediate values from Python (specific z vectors, T values, challenges) to verify identical computation
- CLI integration: run binary, verify CSV output parses correctly

## Dependencies

```toml
[dependencies]
sha2 = "0.10"
rand = "0.8"
clap = { version = "4", features = ["derive"] }

[dev-dependencies]
# none beyond std test framework
```

Minimal dependency footprint. No arkworks yet.

## Out of Scope

- PyO3 bindings
- Sparse matrix implementation
- Real cryptographic commitments (Pedersen/KZG)
- Parallelism (rayon)
- no_std support
- Norm growth / LatticeFold experiments (separate future work)

## Future Extension Points

The trait boundaries are the extension points:

1. **Field** — swap `Fp61` for arkworks `BN254Fr` when adding Sonobe benchmarks
2. **MatrixOps** — add `CsrMatrix` when circuits exceed ~1000 constraints
3. **CommitmentScheme** — add Pedersen when integrating with real proof systems
4. **CLI** — add `--parallel` flag with rayon when single-threaded isn't fast enough
