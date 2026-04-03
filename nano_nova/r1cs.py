"""
R1CS and Relaxed R1CS data structures.

An R1CS instance encodes a computation as:
    Az ∘ Bz = Cz
where z = (1, x, w), A/B/C are sparse matrices, and ∘ is Hadamard product.

A Relaxed R1CS generalizes this to:
    Az ∘ Bz = u·Cz + E
where u is a scalar and E is an error vector. For a "real" instance, u=1 and E=0.

Nova paper reference: Section 4 (Folding Scheme for R1CS)
"""

from dataclasses import dataclass

import numpy as np

from .field import GF, field_zeros


@dataclass
class R1CSShape:
    """The structure of an R1CS — matrices A, B, C and dimensions.

    Attributes:
        A, B, C: Constraint matrices over GF(p). Shape: (m, n) where
                  m = number of constraints, n = 1 + |x| + |w|.
        m: Number of constraints.
        n: Total witness length (1 + public inputs + private witness).
        l: Number of public inputs.
    """

    A: np.ndarray  # GF array, shape (m, n)
    B: np.ndarray  # GF array, shape (m, n)
    C: np.ndarray  # GF array, shape (m, n)
    m: int  # number of constraints
    n: int  # total variables (1 + l + witness_size)
    l: int  # number of public inputs

    def is_satisfied(self, x, w) -> bool:
        """Check if (x, w) satisfies Az ∘ Bz = Cz."""
        z = self._make_z(x, w)
        Az = self.A @ z
        Bz = self.B @ z
        Cz = self.C @ z
        return np.all(Az * Bz == Cz)

    def is_relaxed_satisfied(
        self, instance: "RelaxedR1CSInstance", witness: "RelaxedR1CSWitness"
    ) -> bool:
        """Check if a relaxed instance satisfies Az ∘ Bz = u·Cz + E.

        For relaxed R1CS, z = (u, x, W) — the first element is u, not 1.
        This is because folding combines z' = z₁ + r·z₂, making the first
        element u₁ + r·u₂ = u'. The matrices select u from position 0.
        """
        z = self._make_relaxed_z(instance.u, instance.x, witness.W)
        Az = self.A @ z
        Bz = self.B @ z
        Cz = self.C @ z
        lhs = Az * Bz
        rhs = instance.u * Cz + witness.E
        return np.all(lhs == rhs)

    def _make_z(self, x, w):
        """Construct z = (1, x, w) for standard R1CS."""
        one = GF(np.array([1]))
        return GF(np.concatenate([one, x, w]))

    def _make_relaxed_z(self, u, x, w):
        """Construct z = (u, x, w) for relaxed R1CS."""
        u_arr = GF(np.array([int(u)]))
        return GF(np.concatenate([u_arr, x, w]))


@dataclass
class RelaxedR1CSInstance:
    """Public part of a Relaxed R1CS instance.

    Nova paper: Definition 7 — a relaxed instance is (com_E, u, x, com_W).
    We store commitments as opaque values and keep u, x as field elements.

    Attributes:
        com_E: Commitment to the error vector E.
        u: Relaxation scalar. u=1 for "real" instances, u=0 for trivial.
        x: Public input/output vector.
        com_W: Commitment to the witness W.
    """

    com_E: object  # commitment (opaque)
    u: object  # field element
    x: np.ndarray  # GF array of public inputs
    com_W: object  # commitment (opaque)


@dataclass
class RelaxedR1CSWitness:
    """Private part of a Relaxed R1CS instance.

    Attributes:
        E: Error vector. E=0 for real instances.
        W: Witness vector.
    """

    E: np.ndarray  # GF array, length m
    W: np.ndarray  # GF array, length (n - 1 - l)


def r1cs_to_relaxed(
    shape: R1CSShape, x, w, commit_fn
) -> tuple[RelaxedR1CSInstance, RelaxedR1CSWitness]:
    """Lift a standard R1CS instance to a Relaxed R1CS instance.

    A satisfied R1CS instance (x, w) becomes a relaxed instance with u=1, E=0.

    Args:
        shape: The R1CS structure.
        x: Public inputs.
        w: Witness.
        commit_fn: Commitment function Com(vector) -> commitment.

    Returns:
        (instance, witness) pair for the relaxed system.
    """
    E = field_zeros(shape.m)
    u = GF(1)
    com_E = commit_fn(E)
    com_W = commit_fn(w)
    instance = RelaxedR1CSInstance(com_E=com_E, u=u, x=x, com_W=com_W)
    witness = RelaxedR1CSWitness(E=E, W=w)
    return instance, witness


def trivial_relaxed(shape: R1CSShape, commit_fn) -> tuple[RelaxedR1CSInstance, RelaxedR1CSWitness]:
    """Create a trivial relaxed instance (u=0, E=0, W=0, x=0).

    This is the starting accumulator for IVC. With u=0, W=0, x=0, E=0, the
    relaxed relation becomes Az∘Bz = 0·Cz + 0. Since z = (u, x, W) = (0, 0, 0),
    every matrix product Az, Bz, Cz is zero, so 0 = 0 holds trivially.

    Args:
        shape: The R1CS structure.
        commit_fn: Commitment function.

    Returns:
        Trivial (instance, witness) pair.
    """
    E = field_zeros(shape.m)
    W = field_zeros(shape.n - 1 - shape.l)
    x = field_zeros(shape.l)
    u = GF(0)
    com_E = commit_fn(E)
    com_W = commit_fn(W)
    instance = RelaxedR1CSInstance(com_E=com_E, u=u, x=x, com_W=com_W)
    witness = RelaxedR1CSWitness(E=E, W=W)
    return instance, witness
