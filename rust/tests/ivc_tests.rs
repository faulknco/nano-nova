use nano_nova::commitment::ToyCommitment;
use nano_nova::examples::{fibonacci_circuit, fibonacci_step, fibonacci_witness};
use nano_nova::field::{Field, Fp61};
use nano_nova::ivc::{ivc_prove, ivc_verify};
use nano_nova::matrix::DenseMatrix;

#[test]
fn test_ivc_fibonacci_10_steps() {
    let shape = fibonacci_circuit::<Fp61>();
    let z0 = vec![Fp61::from_u64(1), Fp61::from_u64(1)];

    let proof = ivc_prove::<Fp61, DenseMatrix<Fp61>, ToyCommitment>(
        &shape,
        fibonacci_step,
        fibonacci_witness,
        &z0,
        10,
    );

    assert!(ivc_verify(&shape, &proof));
    assert_eq!(proof.z_current[0], Fp61::from_u64(89));
    assert_eq!(proof.z_current[1], Fp61::from_u64(144));
    assert_eq!(proof.num_steps, 10);
}

#[test]
fn test_ivc_fibonacci_100_steps() {
    let shape = fibonacci_circuit::<Fp61>();
    let z0 = vec![Fp61::from_u64(1), Fp61::from_u64(1)];

    let proof = ivc_prove::<Fp61, DenseMatrix<Fp61>, ToyCommitment>(
        &shape,
        fibonacci_step,
        fibonacci_witness,
        &z0,
        100,
    );

    assert!(ivc_verify(&shape, &proof));
    assert_eq!(proof.num_steps, 100);
}
