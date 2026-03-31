"""
Polynomial ring arithmetic over R_q = Z_q[X] / (X^n + 1).

This is the algebraic structure underlying lattice-based commitments.
Elements are polynomials of degree < n with coefficients in Z_q.
Multiplication is polynomial multiplication modulo (X^n + 1).

The ring R_q is used in Module-SIS/Module-LWE based cryptography
(e.g., Kyber, Dilithium, LatticeFold).

Key properties:
- Addition: coefficient-wise mod q
- Multiplication: polynomial multiplication mod (X^n + 1) mod q
- The polynomial X^n + 1 is the n-th cyclotomic polynomial when n is a power of 2
- Elements of small norm (short vectors) are cryptographically useful
"""

from dataclasses import dataclass

import numpy as np


@dataclass
class RingParams:
    """Parameters for the polynomial ring R_q = Z_q[X]/(X^n+1).

    Attributes:
        n: Ring dimension (degree of the cyclotomic polynomial). Must be power of 2.
        q: Modulus. Coefficients are in Z_q = {0, 1, ..., q-1}.
    """

    n: int
    q: int

    def __post_init__(self):
        assert self.n > 0 and (self.n & (self.n - 1)) == 0, "n must be a power of 2"
        assert self.q > 1, "q must be > 1"


class RingElement:
    """An element of R_q = Z_q[X]/(X^n+1).

    Stored as a numpy int64 array of n coefficients in [0, q-1].
    The element a[0] + a[1]*X + a[2]*X^2 + ... + a[n-1]*X^(n-1).
    """

    __slots__ = ("coeffs", "params")

    def __init__(self, coeffs: np.ndarray, params: RingParams):
        self.params = params
        # Ensure coefficients are in [0, q-1]
        self.coeffs = np.asarray(coeffs, dtype=np.int64) % params.q

    @classmethod
    def zero(cls, params: RingParams) -> "RingElement":
        return cls(np.zeros(params.n, dtype=np.int64), params)

    @classmethod
    def one(cls, params: RingParams) -> "RingElement":
        c = np.zeros(params.n, dtype=np.int64)
        c[0] = 1
        return cls(c, params)

    @classmethod
    def random(cls, params: RingParams) -> "RingElement":
        """Uniformly random element of R_q."""
        return cls(np.random.randint(0, params.q, size=params.n, dtype=np.int64), params)

    @classmethod
    def random_small(cls, params: RingParams, bound: int = 1) -> "RingElement":
        """Random element with small coefficients in [-bound, bound].

        Used for challenge vectors in C_small (ternary when bound=1).
        """
        c = np.random.randint(-bound, bound + 1, size=params.n, dtype=np.int64)
        return cls(c, params)

    @classmethod
    def random_short(cls, params: RingParams, bound: int) -> "RingElement":
        """Random element with coefficients in [0, bound-1].

        Used to create initial witnesses with bounded norm.
        """
        c = np.random.randint(0, bound, size=params.n, dtype=np.int64)
        return cls(c, params)

    def __add__(self, other: "RingElement") -> "RingElement":
        assert self.params == other.params
        return RingElement((self.coeffs + other.coeffs) % self.params.q, self.params)

    def __sub__(self, other: "RingElement") -> "RingElement":
        assert self.params == other.params
        return RingElement((self.coeffs - other.coeffs) % self.params.q, self.params)

    def __mul__(self, other) -> "RingElement":
        if isinstance(other, RingElement):
            return self._ring_mul(other)
        elif isinstance(other, (int, np.integer)):
            return RingElement((self.coeffs * int(other)) % self.params.q, self.params)
        return NotImplemented

    def __rmul__(self, other) -> "RingElement":
        if isinstance(other, (int, np.integer)):
            return self.__mul__(other)
        return NotImplemented

    def _ring_mul(self, other: "RingElement") -> "RingElement":
        """Polynomial multiplication mod (X^n + 1) mod q.

        Uses negacyclic convolution: X^n = -1 in R_q.
        Schoolbook O(n^2) — sufficient for our simulation sizes.
        """
        n = self.params.n
        q = self.params.q
        result = np.zeros(n, dtype=np.int64)

        for i in range(n):
            for j in range(n):
                idx = i + j
                if idx < n:
                    result[idx] = (result[idx] + self.coeffs[i] * other.coeffs[j]) % q
                else:
                    # X^n = -1, so X^(n+k) = -X^k
                    result[idx - n] = (result[idx - n] - self.coeffs[i] * other.coeffs[j]) % q

        return RingElement(result, self.params)

    def centered_coeffs(self) -> np.ndarray:
        """Coefficients in centered representation: [-(q-1)/2, (q-1)/2].

        For norm computation, we need signed representation.
        A coefficient c in [0, q-1] maps to c if c < q/2, else c - q.
        """
        c = self.coeffs.copy()
        half_q = self.params.q // 2
        c = np.where(c > half_q, c - self.params.q, c)
        return c

    def l2_norm(self) -> float:
        """L2 norm of the centered coefficient vector."""
        return float(np.sqrt(np.sum(self.centered_coeffs() ** 2)))

    def linf_norm(self) -> int:
        """L-infinity norm (max absolute centered coefficient)."""
        return int(np.max(np.abs(self.centered_coeffs())))

    def __repr__(self) -> str:
        c = self.centered_coeffs()
        nonzero = [(i, c[i]) for i in range(len(c)) if c[i] != 0]
        if not nonzero:
            return "0"
        terms = []
        for i, coeff in nonzero[:5]:  # show first 5 nonzero terms
            if i == 0:
                terms.append(f"{coeff}")
            else:
                terms.append(f"{coeff}·X^{i}")
        s = " + ".join(terms)
        if len(nonzero) > 5:
            s += f" + ... ({len(nonzero)} terms)"
        return s


class RingVector:
    """A vector of RingElements — represents a module element over R_q.

    Witnesses in LatticeFold are vectors of ring elements.
    """

    __slots__ = ("elements", "params")

    def __init__(self, elements: list[RingElement], params: RingParams):
        self.elements = elements
        self.params = params

    @classmethod
    def random_short(cls, length: int, params: RingParams, bound: int) -> "RingVector":
        """Random vector with each element having coefficients in [0, bound-1]."""
        return cls([RingElement.random_short(params, bound) for _ in range(length)], params)

    @classmethod
    def zero(cls, length: int, params: RingParams) -> "RingVector":
        return cls([RingElement.zero(params) for _ in range(length)], params)

    def __add__(self, other: "RingVector") -> "RingVector":
        assert len(self.elements) == len(other.elements)
        return RingVector([a + b for a, b in zip(self.elements, other.elements)], self.params)

    def scalar_mul(self, r: RingElement) -> "RingVector":
        """Multiply each component by a ring element r."""
        return RingVector([r * e for e in self.elements], self.params)

    def l2_norm(self) -> float:
        """L2 norm: sqrt(sum of squared centered coefficients across all elements)."""
        total = 0.0
        for elem in self.elements:
            c = elem.centered_coeffs()
            total += float(np.sum(c**2))
        return float(np.sqrt(total))

    def linf_norm(self) -> int:
        """L-infinity norm: max absolute centered coefficient across all elements."""
        return max(elem.linf_norm() for elem in self.elements)

    def __len__(self) -> int:
        return len(self.elements)
