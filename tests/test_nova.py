"""Tests for nanoNova folding scheme."""

import numpy as np

from nano_nova.commitment import commit
from nano_nova.examples import (
    fibonacci_step_circuit,
    fibonacci_step_fn,
    fibonacci_witness_fn,
)
from nano_nova.field import GF
from nano_nova.folding import fold
from nano_nova.ivc import ivc_prove, ivc_verify
from nano_nova.r1cs import r1cs_to_relaxed, trivial_relaxed


class TestFibonacciCircuit:
    """Test the Fibonacci step R1CS circuit."""

    def setup_method(self):
        self.shape = fibonacci_step_circuit()

    def test_circuit_dimensions(self):
        assert self.shape.m == 3  # constraints
        assert self.shape.n == 6  # variables
        assert self.shape.l == 4  # public inputs

    def test_satisfied_instance(self):
        """A correct Fibonacci step should satisfy R1CS."""
        z_in = GF(np.array([1, 1]))  # fib(1), fib(2)
        z_out = fibonacci_step_fn(z_in)  # should be (1, 2)
        w = fibonacci_witness_fn(z_in)  # should be [2]
        x = GF(np.concatenate([z_in, z_out]))

        assert np.all(z_out == GF(np.array([1, 2])))
        assert self.shape.is_satisfied(x, w)

    def test_wrong_witness_rejected(self):
        """An incorrect witness should fail R1CS check."""
        z_in = GF(np.array([1, 1]))
        z_out = fibonacci_step_fn(z_in)
        w = GF(np.array([99]))  # wrong witness
        x = GF(np.concatenate([z_in, z_out]))

        assert not self.shape.is_satisfied(x, w)


class TestRelaxedR1CS:
    """Test Relaxed R1CS lifting and trivial instances."""

    def setup_method(self):
        self.shape = fibonacci_step_circuit()

    def test_lifted_instance_satisfies_relaxed(self):
        """An R1CS instance lifted to relaxed should satisfy relaxed relation."""
        z_in = GF(np.array([3, 5]))
        z_out = fibonacci_step_fn(z_in)
        w = fibonacci_witness_fn(z_in)
        x = GF(np.concatenate([z_in, z_out]))

        instance, witness = r1cs_to_relaxed(self.shape, x, w, commit)
        assert self.shape.is_relaxed_satisfied(instance, witness)

    def test_trivial_instance(self):
        """A trivial relaxed instance (u=0, E=0, W=0) should satisfy."""
        instance, witness = trivial_relaxed(self.shape, commit)
        assert self.shape.is_relaxed_satisfied(instance, witness)


class TestFolding:
    """Test the core folding operation."""

    def setup_method(self):
        self.shape = fibonacci_step_circuit()

    def test_fold_two_instances(self):
        """Folding two valid relaxed instances should produce a valid instance."""
        # First instance: (1, 1) -> (1, 2)
        z1 = GF(np.array([1, 1]))
        z1_out = fibonacci_step_fn(z1)
        w1 = fibonacci_witness_fn(z1)
        x1 = GF(np.concatenate([z1, z1_out]))
        inst1, wit1 = r1cs_to_relaxed(self.shape, x1, w1, commit)

        # Second instance: (1, 2) -> (2, 3)
        z2 = GF(np.array([1, 2]))
        z2_out = fibonacci_step_fn(z2)
        w2 = fibonacci_witness_fn(z2)
        x2 = GF(np.concatenate([z2, z2_out]))
        inst2, wit2 = r1cs_to_relaxed(self.shape, x2, w2, commit)

        # Fold
        folded_inst, folded_wit = fold(self.shape, inst1, wit1, inst2, wit2)

        # The folded instance should satisfy relaxed R1CS
        assert self.shape.is_relaxed_satisfied(folded_inst, folded_wit)

    def test_fold_with_trivial(self):
        """Folding a valid instance with a trivial one should produce a valid instance."""
        trivial_inst, trivial_wit = trivial_relaxed(self.shape, commit)

        z = GF(np.array([5, 8]))
        z_out = fibonacci_step_fn(z)
        w = fibonacci_witness_fn(z)
        x = GF(np.concatenate([z, z_out]))
        inst, wit = r1cs_to_relaxed(self.shape, x, w, commit)

        folded_inst, folded_wit = fold(self.shape, trivial_inst, trivial_wit, inst, wit)
        assert self.shape.is_relaxed_satisfied(folded_inst, folded_wit)

    def test_multiple_folds(self):
        """Multiple sequential folds should all produce valid instances."""
        acc_inst, acc_wit = trivial_relaxed(self.shape, commit)
        z = GF(np.array([1, 1]))

        for _ in range(10):
            z_next = fibonacci_step_fn(z)
            w = fibonacci_witness_fn(z)
            x = GF(np.concatenate([z, z_next]))
            fresh_inst, fresh_wit = r1cs_to_relaxed(self.shape, x, w, commit)

            acc_inst, acc_wit = fold(self.shape, acc_inst, acc_wit, fresh_inst, fresh_wit)
            assert self.shape.is_relaxed_satisfied(acc_inst, acc_wit)

            z = z_next


class TestIVC:
    """Test the full IVC pipeline."""

    def setup_method(self):
        self.shape = fibonacci_step_circuit()

    def test_ivc_fibonacci_10_steps(self):
        """IVC should correctly prove 10 Fibonacci steps."""
        z0 = GF(np.array([1, 1]))
        proof = ivc_prove(
            self.shape,
            step_fn=fibonacci_step_fn,
            witness_fn=fibonacci_witness_fn,
            z0=z0,
            num_steps=10,
        )

        # Verify the proof
        assert ivc_verify(self.shape, proof)

        # Check the final state is correct
        # Step fn: (a,b) -> (b, a+b). From (1,1):
        # (1,2), (2,3), (3,5), (5,8), (8,13), (13,21), (21,34), (34,55), (55,89), (89,144)
        assert int(proof.z_current[0]) == 89
        assert int(proof.z_current[1]) == 144
        assert proof.num_steps == 10

    def test_ivc_fibonacci_100_steps(self):
        """IVC should handle 100 Fibonacci steps."""
        z0 = GF(np.array([1, 1]))
        proof = ivc_prove(
            self.shape,
            step_fn=fibonacci_step_fn,
            witness_fn=fibonacci_witness_fn,
            z0=z0,
            num_steps=100,
        )

        assert ivc_verify(self.shape, proof)
        assert proof.num_steps == 100
