use nano_nova::commitment::ToyCommitment;
use nano_nova::field::{Field, Fp61};
use nano_nova::matrix::DenseMatrix;
use nano_nova::r1cs::{r1cs_to_relaxed, trivial_relaxed, R1CSShape};

/// Build the Fibonacci step circuit.
fn fib_circuit() -> R1CSShape<Fp61, DenseMatrix<Fp61>> {
    let (m, n, l) = (3, 6, 4);
    let mut a = DenseMatrix::<Fp61>::zeros(m, n);
    let mut b = DenseMatrix::<Fp61>::zeros(m, n);
    let mut c = DenseMatrix::<Fp61>::zeros(m, n);

    // Constraint 1: 1 * (z_i[0] + z_i[1]) = w[0]
    a.set(0, 0, Fp61::one());
    b.set(0, 1, Fp61::one());
    b.set(0, 2, Fp61::one());
    c.set(0, 5, Fp61::one());

    // Constraint 2: 1 * z_i[1] = z_{i+1}[0]
    a.set(1, 0, Fp61::one());
    b.set(1, 2, Fp61::one());
    c.set(1, 3, Fp61::one());

    // Constraint 3: 1 * w[0] = z_{i+1}[1]
    a.set(2, 0, Fp61::one());
    b.set(2, 5, Fp61::one());
    c.set(2, 4, Fp61::one());

    R1CSShape::new(a, b, c, m, n, l)
}

#[test]
fn test_circuit_dimensions() {
    let shape = fib_circuit();
    assert_eq!(shape.m, 3);
    assert_eq!(shape.n, 6);
    assert_eq!(shape.l, 4);
}

#[test]
fn test_satisfied_instance() {
    let shape = fib_circuit();
    let x = vec![
        Fp61::from_u64(1),
        Fp61::from_u64(1),
        Fp61::from_u64(1),
        Fp61::from_u64(2),
    ];
    let w = vec![Fp61::from_u64(2)];
    assert!(shape.is_satisfied(&x, &w));
}

#[test]
fn test_wrong_witness_rejected() {
    let shape = fib_circuit();
    let x = vec![
        Fp61::from_u64(1),
        Fp61::from_u64(1),
        Fp61::from_u64(1),
        Fp61::from_u64(2),
    ];
    let w = vec![Fp61::from_u64(99)];
    assert!(!shape.is_satisfied(&x, &w));
}

#[test]
fn test_lifted_satisfies_relaxed() {
    let shape = fib_circuit();
    let z_in = [Fp61::from_u64(3), Fp61::from_u64(5)];
    let z_out = [z_in[1], z_in[0].add(z_in[1])];
    let x = vec![z_in[0], z_in[1], z_out[0], z_out[1]];
    let w = vec![z_in[0].add(z_in[1])];

    let (instance, witness) =
        r1cs_to_relaxed::<Fp61, DenseMatrix<Fp61>, ToyCommitment>(&shape, &x, &w);
    assert!(shape.is_relaxed_satisfied(&instance, &witness));
}

#[test]
fn test_trivial_instance() {
    let shape = fib_circuit();
    let (instance, witness) =
        trivial_relaxed::<Fp61, DenseMatrix<Fp61>, ToyCommitment>(&shape);
    assert!(shape.is_relaxed_satisfied(&instance, &witness));
}
