use crate::field::Field;
use crate::matrix::DenseMatrix;
use crate::r1cs::R1CSShape;

/// Fibonacci step circuit: (a, b) -> (b, a+b).
///
/// z = (1, z_i[0], z_i[1], z_{i+1}[0], z_{i+1}[1], w[0])
/// m=3 constraints, n=6 variables, l=4 public inputs.
pub fn fibonacci_circuit<F: Field>() -> R1CSShape<F, DenseMatrix<F>> {
    let (m, n, l) = (3, 6, 4);
    let mut a = DenseMatrix::<F>::zeros(m, n);
    let mut b = DenseMatrix::<F>::zeros(m, n);
    let mut c = DenseMatrix::<F>::zeros(m, n);

    // Constraint 1: 1 * (z_i[0] + z_i[1]) = w[0]
    a.set(0, 0, F::one());
    b.set(0, 1, F::one());
    b.set(0, 2, F::one());
    c.set(0, 5, F::one());

    // Constraint 2: 1 * z_i[1] = z_{i+1}[0]
    a.set(1, 0, F::one());
    b.set(1, 2, F::one());
    c.set(1, 3, F::one());

    // Constraint 3: 1 * w[0] = z_{i+1}[1]
    a.set(2, 0, F::one());
    b.set(2, 5, F::one());
    c.set(2, 4, F::one());

    R1CSShape::new(a, b, c, m, n, l)
}

/// Compute one Fibonacci step: (a, b) -> (b, a+b).
pub fn fibonacci_step<F: Field>(z: &[F]) -> Vec<F> {
    vec![z[1], z[0].add(z[1])]
}

/// Compute the witness for one Fibonacci step: w = [a + b].
pub fn fibonacci_witness<F: Field>(z: &[F]) -> Vec<F> {
    vec![z[0].add(z[1])]
}
