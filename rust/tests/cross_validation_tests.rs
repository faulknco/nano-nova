use nano_nova::commitment::ToyCommitment;
use nano_nova::examples::{fibonacci_circuit, fibonacci_step, fibonacci_witness};
use nano_nova::field::{Field, Fp61};
use nano_nova::folding::{compute_cross_term, fold};
use nano_nova::matrix::DenseMatrix;
use nano_nova::r1cs::{r1cs_to_relaxed, trivial_relaxed};

#[test]
fn test_cross_term_is_zero_for_trivial_fold() {
    // When folding a trivial accumulator (u=0, all zeros) with a fresh instance,
    // the cross-term T should be all zeros.
    // This is serialization-independent and matches the Python output: T = [0, 0, 0]
    let shape = fibonacci_circuit::<Fp61>();

    let z_in = vec![Fp61::from_u64(1), Fp61::from_u64(1)];
    let z_out = fibonacci_step(&z_in);
    let x: Vec<Fp61> = z_in.iter().chain(z_out.iter()).copied().collect();
    let w = fibonacci_witness(&z_in);

    let (triv_inst, triv_wit) = trivial_relaxed::<Fp61, _, ToyCommitment>(&shape);
    let (fresh_inst, fresh_wit) = r1cs_to_relaxed::<Fp61, _, ToyCommitment>(&shape, &x, &w);

    let t = compute_cross_term::<Fp61, _, ToyCommitment>(
        &shape,
        &triv_inst,
        &triv_wit,
        &fresh_inst,
        &fresh_wit,
    );

    // Cross-term is zero when one instance is trivial (u=0, z=0)
    // This matches Python: T = [0, 0, 0]
    assert_eq!(t, vec![Fp61::zero(), Fp61::zero(), Fp61::zero()]);
}

#[test]
fn test_first_fold_produces_valid_instance() {
    // NOTE: Fiat-Shamir challenge differs between Python and Rust because:
    // - Python serializes field elements via numpy.tobytes() (little-endian)
    // - Rust serializes via u64::to_be_bytes() (big-endian)
    // Both produce valid folded instances; the exact field values differ.
    let shape = fibonacci_circuit::<Fp61>();

    let z_in = vec![Fp61::from_u64(1), Fp61::from_u64(1)];
    let z_out = fibonacci_step(&z_in);
    let x: Vec<Fp61> = z_in.iter().chain(z_out.iter()).copied().collect();
    let w = fibonacci_witness(&z_in);

    let (triv_inst, triv_wit) = trivial_relaxed::<Fp61, _, ToyCommitment>(&shape);
    let (fresh_inst, fresh_wit) = r1cs_to_relaxed::<Fp61, _, ToyCommitment>(&shape, &x, &w);

    let (folded_inst, folded_wit) =
        fold::<Fp61, _, ToyCommitment>(&shape, &triv_inst, &triv_wit, &fresh_inst, &fresh_wit);

    // The folded instance must satisfy the relaxed R1CS relation
    assert!(shape.is_relaxed_satisfied(&folded_inst, &folded_wit));

    // Since T=0 and E1=0, E2=0: E_folded should also be zero
    assert_eq!(
        folded_wit.e,
        vec![Fp61::zero(), Fp61::zero(), Fp61::zero()]
    );

    // u_folded = 0 + r*1 = r (some nonzero challenge)
    assert_ne!(folded_inst.u, Fp61::zero());
}

#[test]
fn test_10_step_ivc_final_state_matches_python() {
    // The final Fibonacci state after 10 steps is deterministic
    // regardless of serialization — it only depends on field arithmetic.
    // Python: z_current = [89, 144]
    use nano_nova::ivc::{ivc_prove, ivc_verify};

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
}
