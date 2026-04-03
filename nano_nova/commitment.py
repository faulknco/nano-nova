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
        - Not hiding: the hash is deterministic and reveals structure

    In production, replace with Pedersen commitments over an elliptic curve,
    which are additively homomorphic: Com(v1 + r*v2) = Com(v1) + r*Com(v2).
    Here we simulate this by recomputing the commitment of the folded vector.
    """

    def __init__(self, value: bytes):
        self.value = value

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
    return ToyCommitment(value=h)
