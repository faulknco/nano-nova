"""
Base-B decomposition for LatticeFold norm management.

The fundamental problem: in lattice-based folding, each fold step
W' = W1 + r*W2 grows the witness norm by a factor of ~||r||.
After n folds, ||Wn|| ~ ||r||^n * ||W0|| — exponential growth.

LatticeFold's solution: decompose the witness into base-B digits
before folding. Each digit vector has entries in {0, ..., B-1},
so the norm is bounded. After folding the digit vectors, norm growth
per fold is bounded by B rather than ||r||.

LatticeFold paper: Section 4.2 (eprint 2024/257)
"""


from .ring_arithmetic import RingElement, RingParams, RingVector


def decompose_element(elem: RingElement, base: int, num_digits: int) -> list[RingElement]:
    """Decompose a ring element into base-B digits.

    Given a ∈ R_q, write each coefficient in base B:
        a_i = a_i^(0) + B*a_i^(1) + B^2*a_i^(2) + ...

    Each digit a_i^(k) is in {0, 1, ..., B-1}.

    Args:
        elem: Ring element to decompose.
        base: Decomposition base B.
        num_digits: Number of digits k (should be ceil(log_B(q))).

    Returns:
        List of k RingElements, each with coefficients in [0, B-1].
    """
    digits = []
    remaining = elem.coeffs.copy()  # work with unsigned [0, q-1] representation

    for _ in range(num_digits):
        digit_coeffs = remaining % base
        digits.append(RingElement(digit_coeffs, elem.params))
        remaining = remaining // base

    return digits


def recompose_element(digits: list[RingElement], base: int) -> RingElement:
    """Recompose a ring element from its base-B digits.

    a = d[0] + B*d[1] + B^2*d[2] + ...

    Args:
        digits: List of digit RingElements.
        base: Decomposition base B.

    Returns:
        Recomposed RingElement.
    """
    params = digits[0].params
    result = RingElement.zero(params)
    power = 1

    for digit in digits:
        result = result + digit * power
        power *= base

    return result


def decompose_vector(vec: RingVector, base: int, num_digits: int) -> list[RingVector]:
    """Decompose each element of a RingVector into base-B digits.

    Returns a list of k RingVectors, where the i-th vector contains
    the i-th digit of each element.

    Args:
        vec: RingVector to decompose.
        base: Decomposition base B.
        num_digits: Number of digits.

    Returns:
        List of k RingVectors (digit vectors).
    """
    # Decompose each element
    all_digits = [decompose_element(elem, base, num_digits) for elem in vec.elements]

    # Transpose: group by digit position
    digit_vectors = []
    for k in range(num_digits):
        elements_at_k = [all_digits[i][k] for i in range(len(vec))]
        digit_vectors.append(RingVector(elements_at_k, vec.params))

    return digit_vectors


def recompose_vector(digit_vectors: list[RingVector], base: int) -> RingVector:
    """Recompose a RingVector from its digit vectors."""
    params = digit_vectors[0].params
    length = len(digit_vectors[0])

    elements = []
    for i in range(length):
        digits = [dv.elements[i] for dv in digit_vectors]
        elements.append(recompose_element(digits, base))

    return RingVector(elements, params)


def num_digits_for_params(params: RingParams, base: int) -> int:
    """Compute the number of digits needed: ceil(log_B(q))."""
    import math

    return math.ceil(math.log(params.q) / math.log(base))
