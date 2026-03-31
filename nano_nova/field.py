"""
Finite field setup for nanoNova.

We use the galois library for GF(p) arithmetic. The prime is chosen small enough
for educational clarity but large enough to avoid trivial collisions.

Nova paper reference: Section 3 (Preliminaries)
"""

import galois
import numpy as np

# A 61-bit Mersenne prime — large enough for security demos, small enough for readability.
# In production Nova, this would be the scalar field of an elliptic curve (e.g., BN254).
DEFAULT_PRIME = 2**61 - 1

# Create the Galois field. All arithmetic in nanoNova happens here.
GF = galois.GF(DEFAULT_PRIME)


def random_field_element():
    """Sample a uniformly random field element."""
    return GF(np.random.randint(0, DEFAULT_PRIME))


def random_field_vector(n: int):
    """Sample a uniformly random vector of n field elements."""
    return GF(np.random.randint(0, DEFAULT_PRIME, size=n))


def field_zeros(n: int):
    """Zero vector of length n in GF(p)."""
    return GF(np.zeros(n, dtype=int))


def field_ones(n: int):
    """Ones vector of length n in GF(p)."""
    return GF(np.ones(n, dtype=int))
