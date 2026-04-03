# §1 Introduction

Zero-knowledge proof systems based on folding schemes [KST21] have emerged as one of the
most practically efficient approaches to Incrementally Verifiable Computation (IVC). Nova [KST21]
introduced the core idea: two Relaxed R1CS instances can be *folded* into one via a random
linear combination, with a cross-term commitment absorbing the quadratic interference. Repeating
this for N steps yields a proof of `F^N(z₀) = z_N` verifiable in O(1) time regardless of N.

LatticeFold [BC24] extends this paradigm to post-quantum security, replacing elliptic-curve
commitments with lattice-based ones. The key operation is *digit decomposition*: a witness
vector W ∈ Z_q^n is rewritten in base B as W = Σ B^k d_k, and the folded digit norm ||d||₂
is bounded to ensure the security proof goes through. The tightness of this bound directly
determines the efficiency of LatticeFold — looser bounds force larger parameters, higher
communication cost, and slower verification.

Current LatticeFold security proofs bound the folded digit norm in the worst case: a sequence
of maximally adversarial folding challenges. This is provably sound but empirically conservative.
In practice, Fiat-Shamir challenges are pseudorandom — they behave as independent draws from
Z_q, not as adversarially chosen worst-case sequences.

**The question we address:** how do digit norms actually grow under random challenges, and how
does this differ from the worst-case bound?

## 1.1 Our Contributions

We establish a formal correspondence between LatticeFold's norm growth dynamics and the
Edwards-Anderson (EA) spin glass model from condensed matter physics. The central result is:

> **Decompose-then-fold operates in two distinct phases. Below a critical decomposition base
> B_c(n, q), digit norms grow slowly and remain 32–383× smaller than the worst-case bound.
> Above B_c, norms grow explosively. The transition is the cryptographic analogue of the
> spin glass phase transition.**

Concretely, we contribute:

1. **A formal spin glass mapping** (§3). We show that carry terms in base-B digit arithmetic
   are structurally identical to spin-spin interactions in a disordered magnet, with Fiat-Shamir
   challenges playing the role of quenched random couplings. The Edwards-Anderson order parameter
   q_EA maps to the normalised log norm growth rate.

2. **An empirical phase boundary** (§4–5). Monte Carlo sweeps over ring dimensions n ∈ {64, 128,
   256, 512}, moduli q ∈ {65537, 2^32}, and bases B ∈ {2, 4, 8, 16} confirm the phase structure.
   The reduction ratio (typical vs worst-case norm) is 32–383× and is stable across fold depth
   (N = 100 to 1000). The critical base B_c(n) scales as a·log(n) + b, consistent with
   mean-field finite-size scaling.

3. **A tighter security parameter recommendation** (§6). Operating at B ≪ B_c places the system
   deep in the ordered phase, where typical-case norms are far below worst-case bounds. We give
   concrete parameter ranges where LatticeFold can be deployed more aggressively than current
   proofs suggest.

4. **An Ising IVC demonstration** (§2.3). The 1D Ising model transfer matrix is a natural Nova
   IVC circuit — each spin is one R1CS step, and the partition function becomes a cryptographic
   accumulator. We use this as a pedagogical bridge between the physics and the cryptography,
   and as a test case for the formal mapping (the 1D model is always in the ordered phase, as
   expected).

## 1.2 Connection to Prior Work

**Nova and folding schemes.** Since Nova [KST21], a number of folding-based IVC systems have
appeared: SuperNova [KS22] for non-uniform computation, HyperNova [KS23] using multilinear
extensions, ProtoGalaxy [EG23] with improved efficiency, and CycleFold [KS23b] for recursive
elliptic-curve arithmetic. All share the core structure: fold fresh instances into an accumulator
of fixed size. Our analysis applies to the folding step itself and is not specific to any one system.

**LatticeFold.** Boneh and Chen [BC24] introduced LatticeFold as the first post-quantum folding
scheme with concrete efficiency. Their security proof bounds the Euclidean norm of decomposed
witness digits using a worst-case analysis over all possible challenge sequences. Our work
characterises the gap between worst-case and typical-case behaviour.

**Statistical mechanics and cryptography.** Connections between statistical mechanics and
cryptography are not new: the hardness of lattice problems has been related to phase transitions
in random constraint satisfaction [MM09], and the random oracle model has a statistical mechanical
interpretation via the replica method [MPZ02]. The specific connection between spin glass order
parameters and lattice norm growth is, to our knowledge, new.

**Norm growth in lattice schemes.** Norm growth is a central concern in lattice-based protocols
more broadly — it appears in the analysis of NTRU [HPS98], in bootstrapping bounds for FHE [BGV12],
and in the security of lattice signatures [DDLL13]. The decompose-then-fold strategy is specific
to LatticeFold; the phase-transition perspective we develop here may apply more broadly to
iterative lattice operations.

## 1.3 Organisation

§2 reviews LatticeFold's norm decomposition and the Edwards-Anderson spin glass in the depth
needed for the mapping in §3. Readers familiar with either can skip the corresponding subsection.
§3 establishes the formal correspondence. §4 presents the empirical sweep results. §5 characterises
the phase boundary B_c(n, q). §6 discusses implications for parameter selection. §7 outlines
future work including the 2D Ising phase transition via IVC and the replica-method derivation
of B_c.

## References (cited in §1)

- [KST21] Kothapalli, Setty, Tzialla. Nova: Recursive Zero-Knowledge Arguments from Folding Schemes. CRYPTO 2022.
- [BC24] Boneh, Chen. LatticeFold. CRYPTO 2024.
- [KS22] Kothapalli, Setty. SuperNova. 2022.
- [KS23] Kothapalli, Setty. HyperNova. CRYPTO 2023.
- [EG23] Eagen, Gabizon. ProtoGalaxy. 2023.
- [KS23b] Kothapalli, Setty. CycleFold. 2023.
- [MM09] Mézard, Montanari. Information, Physics, and Computation. OUP 2009.
- [MPZ02] Mézard, Parisi, Zecchina. Analytic and Algorithmic Solution of Random Satisfiability Problems. Science 2002.
- [HPS98] Hoffstein, Pipher, Silverman. NTRU. 1998.
- [BGV12] Brakerski, Gentry, Vaikuntanathan. Fully Homomorphic Encryption. 2012.
- [DDLL13] Ducas, Durmus, Lepoint, Lyubashevsky. Lattice Signatures and Bimodal Gaussians. CRYPTO 2013.
