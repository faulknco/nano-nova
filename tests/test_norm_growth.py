"""Tests for the norm growth simulation modules."""

import numpy as np

from experiments.norm_growth.ring_arithmetic import RingParams, RingElement, RingVector
from experiments.norm_growth.decompose import (
    decompose_element,
    recompose_element,
    decompose_vector,
    recompose_vector,
    num_digits_for_params,
)
from experiments.norm_growth.lattice_fold_sim import FoldingConfig, simulate_folding


class TestRingArithmetic:
    def setup_method(self):
        self.params = RingParams(n=16, q=2**10)

    def test_addition(self):
        a = RingElement(np.array([1, 2, 3] + [0] * 13), self.params)
        b = RingElement(np.array([4, 5, 6] + [0] * 13), self.params)
        c = a + b
        assert c.coeffs[0] == 5
        assert c.coeffs[1] == 7
        assert c.coeffs[2] == 9

    def test_addition_mod_q(self):
        q = self.params.q
        a = RingElement(np.array([q - 1] + [0] * 15), self.params)
        b = RingElement(np.array([2] + [0] * 15), self.params)
        c = a + b
        assert c.coeffs[0] == 1  # (q-1 + 2) mod q = 1

    def test_multiplication_constant(self):
        a = RingElement(np.array([3, 0, 0] + [0] * 13), self.params)
        b = RingElement(np.array([7, 0, 0] + [0] * 13), self.params)
        c = a * b
        assert c.coeffs[0] == 21  # 3 * 7

    def test_negacyclic(self):
        """X^n = -1 in R_q, so X^(n-1) * X = -1."""
        n = self.params.n
        # a = X^(n-1)
        a_coeffs = np.zeros(n, dtype=np.int64)
        a_coeffs[n - 1] = 1
        a = RingElement(a_coeffs, self.params)
        # b = X
        b_coeffs = np.zeros(n, dtype=np.int64)
        b_coeffs[1] = 1
        b = RingElement(b_coeffs, self.params)
        c = a * b
        # X^n = -1, so result should be -1 = q-1
        assert c.coeffs[0] == self.params.q - 1

    def test_norms(self):
        c = np.zeros(16, dtype=np.int64)
        c[0] = 3
        c[1] = self.params.q - 4  # represents -4 in centered form
        a = RingElement(c, self.params)
        assert a.linf_norm() == 4
        assert abs(a.l2_norm() - 5.0) < 0.01  # sqrt(9 + 16) = 5


class TestDecomposition:
    def setup_method(self):
        self.params = RingParams(n=16, q=2**10)

    def test_round_trip_base2(self):
        a = RingElement.random(self.params)
        nd = num_digits_for_params(self.params, 2)
        digits = decompose_element(a, 2, nd)
        b = recompose_element(digits, 2)
        assert np.all(a.coeffs == b.coeffs)

    def test_round_trip_base4(self):
        a = RingElement.random(self.params)
        nd = num_digits_for_params(self.params, 4)
        digits = decompose_element(a, 4, nd)
        b = recompose_element(digits, 4)
        assert np.all(a.coeffs == b.coeffs)

    def test_digit_bounds(self):
        """Each digit should have coefficients in [0, B-1]."""
        a = RingElement.random(self.params)
        base = 4
        nd = num_digits_for_params(self.params, base)
        digits = decompose_element(a, base, nd)
        for d in digits:
            assert np.all(d.coeffs >= 0)
            assert np.all(d.coeffs < base)

    def test_vector_round_trip(self):
        vec = RingVector.random_short(3, self.params, 100)
        base = 4
        nd = num_digits_for_params(self.params, base)
        digit_vecs = decompose_vector(vec, base, nd)
        recomp = recompose_vector(digit_vecs, base)
        for orig, rec in zip(vec.elements, recomp.elements):
            assert np.all(orig.coeffs == rec.coeffs)


class TestFoldingSimulation:
    def setup_method(self):
        self.params = RingParams(n=16, q=2**10)

    def test_naive_runs(self):
        config = FoldingConfig(params=self.params, base=0, witness_length=2, initial_bound=8)
        results = simulate_folding(config, num_folds=10, seed=42)
        assert len(results) == 10
        assert all(r.recomposed_l2 > 0 for r in results)

    def test_decompose_runs(self):
        config = FoldingConfig(params=self.params, base=2, witness_length=2, initial_bound=8)
        results = simulate_folding(config, num_folds=10, seed=42)
        assert len(results) == 10
        assert all(r.final_digit_l2 > 0 for r in results)

    def test_decompose_bounds_digits(self):
        """After re-decomposition, digit norms should be bounded."""
        config = FoldingConfig(params=self.params, base=4, witness_length=2, initial_bound=8)
        results = simulate_folding(config, num_folds=50, seed=42)
        # Final digit Linf should be < B = 4
        for r in results:
            assert r.final_digit_linf < 4, (
                f"Step {r.step}: final_digit_linf={r.final_digit_linf} >= B=4"
            )

    def test_decompose_intermediate_smaller_than_naive(self):
        """Intermediate digit norms should be much smaller than naive witness norms."""
        cfg_naive = FoldingConfig(params=self.params, base=0, witness_length=2, initial_bound=8)
        cfg_decomp = FoldingConfig(params=self.params, base=4, witness_length=2, initial_bound=8)

        res_naive = simulate_folding(cfg_naive, num_folds=50, seed=42)
        res_decomp = simulate_folding(cfg_decomp, num_folds=50, seed=42)

        naive_final = res_naive[-1].recomposed_l2
        decomp_final = res_decomp[-1].intermediate_digit_l2

        assert decomp_final < naive_final, (
            f"Decompose intermediate ({decomp_final:.1f}) should be < naive ({naive_final:.1f})"
        )
