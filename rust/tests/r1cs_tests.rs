use nano_nova::commitment::ToyCommitment;
use nano_nova::examples::fibonacci_circuit;
use nano_nova::field::{Field, Fp61};
use nano_nova::matrix::DenseMatrix;
use nano_nova::r1cs::{r1cs_to_relaxed, trivial_relaxed};

#[test]
fn test_circuit_dimensions() {
    let shape = fibonacci_circuit::<Fp61>();
    assert_eq!(shape.m, 3);
    assert_eq!(shape.n, 6);
    assert_eq!(shape.l, 4);
}

#[test]
fn test_satisfied_instance() {
    let shape = fibonacci_circuit::<Fp61>();
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
    let shape = fibonacci_circuit::<Fp61>();
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
    let shape = fibonacci_circuit::<Fp61>();
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
    let shape = fibonacci_circuit::<Fp61>();
    let (instance, witness) =
        trivial_relaxed::<Fp61, DenseMatrix<Fp61>, ToyCommitment>(&shape);
    assert!(shape.is_relaxed_satisfied(&instance, &witness));
}
