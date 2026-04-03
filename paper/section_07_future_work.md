# §7 Future Work

## 7.1 2D Ising Phase Transition via IVC Accumulator

The most immediate extension is the 2D Ising model on a strip of width L. The transfer matrix
is 2^L × 2^L — for L=3, a valid 8×8 Nova R1CS step. Unlike the 1D model, the 2D Ising has
a genuine phase transition at T_c = 2J/ln(1+√2) ≈ 2.27J (Onsager, 1944).

Near T_c, the spectral gap Δ = λ+ - λ- → 0, meaning the dominant and sub-dominant eigenvalues
become degenerate. In the IVC accumulator, this manifests as the folding challenge r amplifying
the sub-dominant component — the accumulator state near T_c carries information about the
phase transition.

**Research question:** can the critical temperature T_c be *detected* from the IVC accumulator
state, without explicitly computing the partition function? A positive answer would be the first
instance of a physical phase transition being certified by a zero-knowledge proof.

## 7.2 Replica Method Calculation of B_c(n, q)

Section 3.6 derives the carry probability and identifies the percolation condition for the
phase boundary, but stops short of computing B_c analytically. The replica method [Par79,
MPZ02] provides the tools to complete this calculation.

The replica calculation would proceed by:
1. Replicate the folded digit system m times with the same quenched challenges
2. Compute the replica partition function Z^m as a function of B, n, q
3. Take m → 0 (replica trick) to extract the free energy
4. Locate the replica symmetry breaking transition — this is B_c

An analytical B_c(n, q) formula would:
- Confirm or refute the empirical B_c ~ a·log(n) + b scaling
- Give a tighter security bound than worst-case proofs (replacing empirical Table 5.1)
- Potentially unify the LatticeFold and spin glass security analyses

## 7.3 Tensor Networks and Matrix Product States

Matrix Product States (MPS) in condensed matter physics are tensor networks contracted
left-to-right — structurally identical to Nova's sequential accumulation. The Density Matrix
Renormalisation Group (DMRG) algorithm, which optimises MPS to find ground states, is
essentially running IVC on a quantum many-body system.

The formal connection: an MPS of bond dimension χ on N sites has the same structure as a
Nova IVC chain of depth N with R1CS constraint size χ×χ. Proving an MPS contraction via
Nova would connect ZK proofs to quantum many-body physics at a mathematical level, not
merely by analogy.

A concrete near-term goal: implement the χ=2 (qubit) MPS contraction as a Nova R1CS step,
verify the ground state energy of the transverse-field Ising model via ivc_verify.

## 7.4 Rule 110 and Turing-Complete IVC

Rule 110 cellular automaton is Turing complete. One step of Rule 110 is a simple local R1CS
constraint: each cell's next state depends only on itself and its two neighbours. Proving N
steps of Rule 110 evolution via Nova IVC would be the most visceral demonstration that
"IVC = universal verifiable computation."

Practical interest: cellular automaton proofs have been proposed as benchmarks for IVC
performance [ref]. Rule 110 is also a natural test bed for the spin glass mapping — the
local coupling structure (each cell to its neighbours) corresponds to a short-range spin glass
rather than the SK all-to-all model, and the phase boundary analysis of §3 would need extension
to the short-range case.

## 7.5 Production Cryptography Upgrade

The current implementation uses a toy commitment scheme (a SHA-256 hash of the vector) that
is neither hiding nor binding in any cryptographic sense. A production-grade version would:

- Replace ToyCommitment with a Pedersen commitment over BN254 or Pasta curves
- Replace the toy field GF(2^61-1) with the BN254 scalar field
- Use sparse (CSR) matrices for R1CS, matching the Sonobe [ref] library conventions

The codebase is structured for this: `CommitmentScheme` and `Field` are trait bounds in Rust,
so swapping implementations requires only new trait implementors, not changes to the folding
or IVC logic. A direct comparison against Sonobe's Nova implementation would validate both
the educational code and the production upgrade path.

## 7.6 u128 Modulus and Phase Space Exploration

The current Rust implementation is limited to q < 2^63 due to u64 arithmetic with i64 centering.
Extending to u128 would allow:
- q = 2^64 (NTT-friendly, standard in lattice crypto)
- q = 2^128 (128-bit security level)
- Hunting for phase transitions as q crosses power-of-two boundaries

The q-independence observation (§6.3) predicts no phase transition as a function of q alone.
Testing this at q = 2^64 and 2^128 would either confirm the prediction or reveal new physics
at larger moduli.
