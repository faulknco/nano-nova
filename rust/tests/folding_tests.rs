use nano_nova::commitment::ToyCommitment;
use nano_nova::field::{Field, Fp61};
use nano_nova::folding::fold;
use nano_nova::matrix::DenseMatrix;
use nano_nova::r1cs::{r1cs_to_relaxed, trivial_relaxed, R1CSShape};

fn fib_circuit() -> R1CSShape<Fp61, DenseMatrix<Fp61>> {
    let (m, n, l) = (3, 6, 4);
    let mut a = DenseMatrix::<Fp61>::zeros(m, n);
    let mut b = DenseMatrix::<Fp61>::zeros(m, n);
    let mut c = DenseMatrix::<Fp61>::zeros(m, n);

    a.set(0, 0, Fp61::one());
    b.set(0, 1, Fp61::one());
    b.set(0, 2, Fp61::one());
    c.set(0, 5, Fp61::one());

    a.set(1, 0, Fp61::one());
    b.set(1, 2, Fp61::one());
    c.set(1, 3, Fp61::one());

    a.set(2, 0, Fp61::one());
    b.set(2, 5, Fp61::one());
    c.set(2, 4, Fp61::one());

    R1CSShape::new(a, b, c, m, n, l)
}

fn fib_step(z: &[Fp61]) -> Vec<Fp61> {
    vec![z[1], z[0].add(z[1])]
}

fn fib_witness(z: &[Fp61]) -> Vec<Fp61> {
    vec![z[0].add(z[1])]
}

#[test]
fn test_fold_two_instances() {
    let shape = fib_circuit();

    let z1 = [Fp61::from_u64(1), Fp61::from_u64(1)];
    let z1_out = fib_step(&z1);
    let x1: Vec<Fp61> = z1.iter().chain(z1_out.iter()).copied().collect();
    let w1 = fib_witness(&z1);
    let (inst1, wit1) = r1cs_to_relaxed::<Fp61, _, ToyCommitment>(&shape, &x1, &w1);

    let z2 = [Fp61::from_u64(1), Fp61::from_u64(2)];
    let z2_out = fib_step(&z2);
    let x2: Vec<Fp61> = z2.iter().chain(z2_out.iter()).copied().collect();
    let w2 = fib_witness(&z2);
    let (inst2, wit2) = r1cs_to_relaxed::<Fp61, _, ToyCommitment>(&shape, &x2, &w2);

    let (folded_inst, folded_wit) =
        fold::<Fp61, _, ToyCommitment>(&shape, &inst1, &wit1, &inst2, &wit2);
    assert!(shape.is_relaxed_satisfied(&folded_inst, &folded_wit));
}

#[test]
fn test_fold_with_trivial() {
    let shape = fib_circuit();

    let (triv_inst, triv_wit) = trivial_relaxed::<Fp61, _, ToyCommitment>(&shape);

    let z = [Fp61::from_u64(5), Fp61::from_u64(8)];
    let z_out = fib_step(&z);
    let x: Vec<Fp61> = z.iter().chain(z_out.iter()).copied().collect();
    let w = fib_witness(&z);
    let (inst, wit) = r1cs_to_relaxed::<Fp61, _, ToyCommitment>(&shape, &x, &w);

    let (folded_inst, folded_wit) =
        fold::<Fp61, _, ToyCommitment>(&shape, &triv_inst, &triv_wit, &inst, &wit);
    assert!(shape.is_relaxed_satisfied(&folded_inst, &folded_wit));
}

#[test]
fn test_multiple_folds() {
    let shape = fib_circuit();
    let (mut acc_inst, mut acc_wit) = trivial_relaxed::<Fp61, _, ToyCommitment>(&shape);
    let mut z = vec![Fp61::from_u64(1), Fp61::from_u64(1)];

    for _ in 0..10 {
        let z_next = fib_step(&z);
        let w = fib_witness(&z);
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
