"""
Nova's NIFS (Non-Interactive Folding Scheme) for Relaxed R1CS.

This is the heart of Nova. Given two Relaxed R1CS instances, we fold them
into a single instance of the same size. The cross-term T absorbs the
"interference" from combining two quadratic constraints.

The physics analogy: T is a renormalization counter-term that absorbs
perturbative corrections when combining two constraint systems.

Nova paper reference: Section 4, Construction 4 (NIFS for Relaxed R1CS)
"""

import hashlib

import numpy as np

from .commitment import ToyCommitment, commit
from .field import GF
from .r1cs import R1CSShape, RelaxedR1CSInstance, RelaxedR1CSWitness


def compute_cross_term(
    shape: R1CSShape,
    instance1: RelaxedR1CSInstance,
    witness1: RelaxedR1CSWitness,
    instance2: RelaxedR1CSInstance,
    witness2: RelaxedR1CSWitness,
) -> np.ndarray:
    """Compute the cross-term T for folding two relaxed instances.

    T = Az₁ ∘ Bz₂ + Az₂ ∘ Bz₁ - u₁·Cz₂ - u₂·Cz₁

    This is the "interference" term that arises from the quadratic nature
    of R1CS when combining two instances via random linear combination.

    Nova paper: Equation in Construction 4, step 1.

    Args:
        shape: R1CS structure (A, B, C matrices).
        instance1, witness1: First relaxed instance.
        instance2, witness2: Second relaxed instance.

    Returns:
        Cross-term vector T of length m (number of constraints).
    """
    z1 = shape._make_relaxed_z(instance1.u, instance1.x, witness1.W)
    z2 = shape._make_relaxed_z(instance2.u, instance2.x, witness2.W)

    Az1 = shape.A @ z1
    Bz1 = shape.B @ z1
    Az2 = shape.A @ z2
    Bz2 = shape.B @ z2
    Cz1 = shape.C @ z1
    Cz2 = shape.C @ z2

    # T = Az₁ ∘ Bz₂ + Az₂ ∘ Bz₁ - u₁·Cz₂ - u₂·Cz₁
    T = Az1 * Bz2 + Az2 * Bz1 - instance1.u * Cz2 - instance2.u * Cz1
    return T


def fiat_shamir_challenge(
    com_T: ToyCommitment,
    instance1: RelaxedR1CSInstance,
    instance2: RelaxedR1CSInstance,
) -> np.ndarray:
    """Derive a challenge r via Fiat-Shamir (hash of transcript).

    In the interactive protocol, the verifier sends random r after seeing com_T.
    Fiat-Shamir makes this non-interactive by hashing the transcript.

    Note: the full Nova transcript (Construction 4) also includes com_E1 and
    com_E2. We omit them here for simplicity — this is sufficient for the
    educational IVC demo but not for production security.

    Nova paper: Section 4, making NIFS non-interactive.

    Args:
        com_T: Commitment to the cross-term.
        instance1: First public instance.
        instance2: Second public instance.

    Returns:
        Challenge r as a GF(p) field element.
    """
    # 9 bytes covers the full 61-bit field prime (2^61 - 1 < 2^72 = 9 bytes)
    transcript = b""
    transcript += com_T.value
    transcript += instance1.x.tobytes()
    transcript += instance2.x.tobytes()
    transcript += int(instance1.u).to_bytes(9, "big")
    transcript += int(instance2.u).to_bytes(9, "big")
    transcript += instance1.com_W.value
    transcript += instance2.com_W.value

    h = hashlib.sha256(transcript).digest()
    r_int = int.from_bytes(h[:8], "big") % int(GF.order)
    return GF(r_int)


def fold(
    shape: R1CSShape,
    instance1: RelaxedR1CSInstance,
    witness1: RelaxedR1CSWitness,
    instance2: RelaxedR1CSInstance,
    witness2: RelaxedR1CSWitness,
) -> tuple[RelaxedR1CSInstance, RelaxedR1CSWitness]:
    """Fold two Relaxed R1CS instances into one.

    This is the core Nova operation. Given (inst₁, w₁) and (inst₂, w₂):
    1. Compute cross-term T
    2. Commit to T
    3. Derive challenge r (Fiat-Shamir)
    4. Fold: E' = E₁ + r·T + r²·E₂
             u' = u₁ + r·u₂
             x' = x₁ + r·x₂
             W' = W₁ + r·W₂

    The folded instance satisfies Relaxed R1CS if both inputs did.

    Nova paper: Construction 4 (NIFS.P and NIFS.V).

    Args:
        shape: R1CS structure.
        instance1, witness1: First relaxed instance (typically the running accumulator).
        instance2, witness2: Second relaxed instance (typically a fresh step).

    Returns:
        (folded_instance, folded_witness) — a new valid Relaxed R1CS pair.
    """
    # Step 1: Compute cross-term
    T = compute_cross_term(shape, instance1, witness1, instance2, witness2)

    # Step 2: Commit to T
    com_T = commit(T)

    # Step 3: Fiat-Shamir challenge
    r = fiat_shamir_challenge(com_T, instance1, instance2)

    # Step 4: Fold everything
    # E' = E₁ + r·T + r²·E₂
    r_sq = r * r
    E_folded = witness1.E + r * T + r_sq * witness2.E

    # u' = u₁ + r·u₂
    u_folded = instance1.u + r * instance2.u

    # x' = x₁ + r·x₂
    x_folded = instance1.x + r * instance2.x

    # W' = W₁ + r·W₂
    W_folded = witness1.W + r * witness2.W

    # Commitments fold homomorphically (simulated here)
    com_E_folded = commit(E_folded)
    com_W_folded = commit(W_folded)

    folded_instance = RelaxedR1CSInstance(
        com_E=com_E_folded,
        u=u_folded,
        x=x_folded,
        com_W=com_W_folded,
    )
    folded_witness = RelaxedR1CSWitness(E=E_folded, W=W_folded)

    return folded_instance, folded_witness
