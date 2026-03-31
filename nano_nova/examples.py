"""
Example circuits for nanoNova.

Provides simple R1CS circuits to demonstrate folding and IVC.
"""

import numpy as np

from .field import GF
from .r1cs import R1CSShape


def fibonacci_step_circuit() -> R1CSShape:
    """R1CS circuit for one Fibonacci step: (a, b) -> (b, a+b).

    Public inputs (l=4): x = [z_i[0], z_i[1], z_{i+1}[0], z_{i+1}[1]]
    Witness (1 element): w = [a + b] (the intermediate sum)

    z = (1, z_i[0], z_i[1], z_{i+1}[0], z_{i+1}[1], w[0])
    indices:  0      1        2          3            4       5

    Constraints (m=3):
    1. z_i[0] + z_i[1] = w[0]          (compute sum)
       Encoded as: (1) * (z_i[0] + z_i[1]) = w[0]
       A[0] = [0, 0, 0, 0, 0, 0], B[0] = [1, 0, 0, 0, 0, 0] — wait, R1CS is multiplicative.

    Actually, for R1CS we need (a·z)(b·z) = c·z. To encode addition:
       (1) * (z_i[0] + z_i[1]) = w[0]
       A = [1, 0, 0, 0, 0, 0]  (selects constant 1)
       B = [0, 1, 1, 0, 0, 0]  (selects z_i[0] + z_i[1])
       C = [0, 0, 0, 0, 0, 1]  (selects w[0])

    2. z_{i+1}[0] = z_i[1]             (first output = second input)
       (1) * (z_i[1]) = z_{i+1}[0]
       A = [1, 0, 0, 0, 0, 0]
       B = [0, 0, 1, 0, 0, 0]
       C = [0, 0, 0, 1, 0, 0]

    3. z_{i+1}[1] = w[0]               (second output = sum)
       (1) * (w[0]) = z_{i+1}[1]
       A = [1, 0, 0, 0, 0, 0]
       B = [0, 0, 0, 0, 0, 1]
       C = [0, 0, 0, 0, 1, 0]

    Returns:
        R1CSShape for the Fibonacci step circuit.
    """
    m = 3  # constraints
    n = 6  # variables: (1, x0_in, x1_in, x0_out, x1_out, w0)
    l = 4  # public inputs: x0_in, x1_in, x0_out, x1_out

    A = GF(np.zeros((m, n), dtype=int))
    B = GF(np.zeros((m, n), dtype=int))
    C = GF(np.zeros((m, n), dtype=int))

    # Constraint 1: 1 * (z_i[0] + z_i[1]) = w[0]
    A[0, 0] = GF(1)  # constant 1
    B[0, 1] = GF(1)  # z_i[0]
    B[0, 2] = GF(1)  # z_i[1]
    C[0, 5] = GF(1)  # w[0]

    # Constraint 2: 1 * z_i[1] = z_{i+1}[0]
    A[1, 0] = GF(1)
    B[1, 2] = GF(1)
    C[1, 3] = GF(1)

    # Constraint 3: 1 * w[0] = z_{i+1}[1]
    A[2, 0] = GF(1)
    B[2, 5] = GF(1)
    C[2, 4] = GF(1)

    return R1CSShape(A=A, B=B, C=C, m=m, n=n, l=l)


def fibonacci_step_fn(z: np.ndarray) -> np.ndarray:
    """Compute one Fibonacci step: (a, b) -> (b, a+b)."""
    return GF(np.array([z[1], z[0] + z[1]]))


def fibonacci_witness_fn(z: np.ndarray) -> np.ndarray:
    """Compute the witness for one Fibonacci step: w = [a + b]."""
    return GF(np.array([z[0] + z[1]]))
