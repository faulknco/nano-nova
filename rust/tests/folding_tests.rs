use nano_nova::commitment::ToyCommitment;
use nano_nova::examples::{fibonacci_circuit, fibonacci_step, fibonacci_witness};
use nano_nova::field::{Field, Fp61};
use nano_nova::folding::fold;
use nano_nova::r1cs::{r1cs_to_relaxed, trivial_relaxed};

#[test]
fn test_fold_two_instances() {
    let shape = fibonacci_circuit::<Fp61>();

    let z1 = [Fp61::from_u64(1), Fp61::from_u64(1)];
    let z1_out = fibonacci_step(&z1);
    let x1: Vec<Fp61> = z1.iter().chain(z1_out.iter()).copied().collect();
    let w1 = fibonacci_witness(&z1);
    let (inst1, wit1) = r1cs_to_relaxed::<Fp61, _, ToyCommitment>(&shape, &x1, &w1);

    let z2 = [Fp61::from_u64(1), Fp61::from_u64(2)];
    let z2_out = fibonacci_step(&z2);
    let x2: Vec<Fp61> = z2.iter().chain(z2_out.iter()).copied().collect();
    let w2 = fibonacci_witness(&z2);
    let (inst2, wit2) = r1cs_to_relaxed::<Fp61, _, ToyCommitment>(&shape, &x2, &w2);

    let (folded_inst, folded_wit) =
        fold::<Fp61, _, ToyCommitment>(&shape, &inst1, &wit1, &inst2, &wit2);
    assert!(shape.is_relaxed_satisfied(&folded_inst, &folded_wit));
}

#[test]
fn test_fold_with_trivial() {
    let shape = fibonacci_circuit::<Fp61>();

    let (triv_inst, triv_wit) = trivial_relaxed::<Fp61, _, ToyCommitment>(&shape);

    let z = [Fp61::from_u64(5), Fp61::from_u64(8)];
    let z_out = fibonacci_step(&z);
    let x: Vec<Fp61> = z.iter().chain(z_out.iter()).copied().collect();
    let w = fibonacci_witness(&z);
    let (inst, wit) = r1cs_to_relaxed::<Fp61, _, ToyCommitment>(&shape, &x, &w);

    let (folded_inst, folded_wit) =
        fold::<Fp61, _, ToyCommitment>(&shape, &triv_inst, &triv_wit, &inst, &wit);
    assert!(shape.is_relaxed_satisfied(&folded_inst, &folded_wit));
}

#[test]
fn test_multiple_folds() {
    let shape = fibonacci_circuit::<Fp61>();
    let (mut acc_inst, mut acc_wit) = trivial_relaxed::<Fp61, _, ToyCommitment>(&shape);
    let mut z = vec![Fp61::from_u64(1), Fp61::from_u64(1)];

    for _ in 0..10 {
        let z_next = fibonacci_step(&z);
        let w = fibonacci_witness(&z);
        let x: Vec<Fp61> = z.iter().chain(z_next.iter()).copied().collect();
        let (fresh_inst, fresh_wit) =
            r1cs_to_relaxed::<Fp61, _, ToyCommitment>(&shape, &x, &w);
        let (new_inst, new_wit) =
            fold::<Fp61, _, ToyCommitment>(&shape, &acc_inst, &acc_wit, &fresh_inst, &fresh_wit);
        assert!(shape.is_relaxed_satisfied(&new_inst, &new_wit));
        acc_inst = new_inst;
        acc_wit = new_wit;
        z = z_next;
    }
}
