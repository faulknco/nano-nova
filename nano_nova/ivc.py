"""
Incrementally Verifiable Computation (IVC) via Nova folding.

IVC proves that a computation f^n(x₀) = xₙ was executed correctly,
where f is applied n times. The prover maintains a running "accumulator"
that folds in each new step, deferring the expensive proof to the end.

    Step 0: z₀ = x₀,       acc = trivial
    Step 1: z₁ = f(z₀),    acc = fold(acc, fresh₁)
    Step 2: z₂ = f(z₁),    acc = fold(acc, fresh₂)
    ...
    Step n: zₙ = f(zₙ₋₁),  acc = fold(acc, freshₙ)
    Final:  verify acc satisfies Relaxed R1CS

Nova paper reference: Section 5 (IVC from Folding Schemes)
"""

from dataclasses import dataclass

import numpy as np

from .commitment import commit
from .field import GF
from .folding import fold
from .r1cs import (
    R1CSShape,
    RelaxedR1CSInstance,
    RelaxedR1CSWitness,
    r1cs_to_relaxed,
    trivial_relaxed,
)


@dataclass
class IVCProof:
    """The output of an IVC computation.

    Attributes:
        instance: The accumulated Relaxed R1CS instance.
        witness: The accumulated witness.
        z_current: The current state z_n = f^n(z_0).
        num_steps: How many steps were folded.
    """

    instance: RelaxedR1CSInstance
    witness: RelaxedR1CSWitness
    z_current: np.ndarray
    num_steps: int


def ivc_prove(
    shape: R1CSShape,
    step_fn,
    witness_fn,
    z0: np.ndarray,
    num_steps: int,
    verbose: bool = False,
) -> IVCProof:
    """Run IVC for num_steps applications of step_fn.

    Args:
        shape: The R1CS structure encoding one step of f.
        step_fn: Function z_{i+1} = step_fn(z_i) computing the public transition.
        witness_fn: Function w_i = witness_fn(z_i) computing the R1CS witness
                    for one step. Must satisfy shape.is_satisfied(x_i, w_i)
                    where x_i encodes (z_i, z_{i+1}).
        z0: Initial state.
        num_steps: Number of steps to prove.
        verbose: Print progress.

    Returns:
        IVCProof with the accumulated instance and final state.
    """
    # Initialize with trivial accumulator
    acc_instance, acc_witness = trivial_relaxed(shape, commit)
    z_current = z0

    for i in range(num_steps):
        # Execute one step
        z_next = step_fn(z_current)

        # Build the R1CS witness for this step
        w_i = witness_fn(z_current)

        # Public input encodes (z_i, z_{i+1})
        x_i = GF(np.concatenate([z_current, z_next]))

        # Verify the fresh instance satisfies standard R1CS
        if not shape.is_satisfied(x_i, w_i):
            raise ValueError(f"Step {i}: R1CS not satisfied — check step_fn and witness_fn")

        # Lift to relaxed R1CS
        fresh_instance, fresh_witness = r1cs_to_relaxed(shape, x_i, w_i, commit)

        # Fold into accumulator
        acc_instance, acc_witness = fold(
            shape, acc_instance, acc_witness, fresh_instance, fresh_witness
        )

        if verbose and (i + 1) % 10 == 0:
            print(f"  Step {i + 1}/{num_steps} folded")

        z_current = z_next

    return IVCProof(
        instance=acc_instance,
        witness=acc_witness,
        z_current=z_current,
        num_steps=num_steps,
    )


def ivc_verify(shape: R1CSShape, proof: IVCProof) -> bool:
    """Verify an IVC proof by checking the accumulated Relaxed R1CS.

    In real Nova, this involves two checks: (1) a SNARK proof over the
    accumulated Relaxed R1CS instance, and (2) verifying that z_current
    matches the public input of the accumulator. Here we only do check (1)
    directly — sufficient for the educational demo but not production-complete.

    Args:
        shape: The R1CS structure.
        proof: The IVC proof to verify.

    Returns:
        True if the accumulated instance satisfies Relaxed R1CS.
    """
    return shape.is_relaxed_satisfied(proof.instance, proof.witness)
