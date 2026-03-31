"""
Toy commitment scheme for nanoNova.

In real Nova, this would be a Pedersen commitment over an elliptic curve:
    Com(v; r) = <v, G> + r·H
where G is a vector of generators and H is a blinding generator.

For educational purposes, we use a hash-based commitment that is binding
(collision-resistant) but not hiding. This is sufficient to demonstrate
the folding mechanics without elliptic curve arithmetic.

Nova paper reference: Section 3.1 (Commitment Scheme)
"""

import hashlib

import numpy as np


class ToyCommitment:
    """A hash-based commitment for educational use.

    Properties:
        - Binding: hard to find two different vectors with the same commitment
        - Additively homomorphic (simulated): we track the underlying vector
          so we can verify homomorphic properties in tests

    In production, replace with Pedersen commitments over an elliptic curve.
    """

    def __init__(self, value: bytes, vector: np.ndarray | None = None):
        self.value = value
        self._vector = vector  # stored for homomorphic simulation

    def __eq__(self, other):
        return isinstance(other, ToyCommitment) and self.value == other.value

    def __repr__(self):
        return f"Com({self.value[:8].hex()}...)"


def commit(vector: np.ndarray) -> ToyCommitment:
    """Commit to a vector by hashing its contents.

    Args:
        vector: A GF(p) array to commit to.

    Returns:
        A ToyCommitment wrapping the hash.
    """
    data = vector.tobytes() if hasattr(vector, "tobytes") else bytes(vector)
    h = hashlib.sha256(data).digest()
    return ToyCommitment(value=h, vector=vector)


def commit_with_homomorphism(v1: np.ndarray, v2: np.ndarray, r) -> ToyCommitment:
    """Simulate homomorphic commitment: Com(v1 + r*v2) = Com(v1) + r*Com(v2).

    In real Pedersen commitments, this holds by group linearity.
    Here we just compute the commitment of the combined vector.

    Args:
        v1: First vector.
        v2: Second vector.
        r: Scalar multiplier.

    Returns:
        Commitment to v1 + r*v2.
    """
    combined = v1 + r * v2
    return commit(combined)
