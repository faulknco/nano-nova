use nano_nova::commitment::{CommitmentScheme, ToyCommitment};
use nano_nova::field::{Field, Fp61};

#[test]
fn test_same_input_same_commitment() {
    let v = vec![Fp61::from_u64(1), Fp61::from_u64(2), Fp61::from_u64(3)];
    let c1 = ToyCommitment::commit(&v);
    let c2 = ToyCommitment::commit(&v);
    assert_eq!(c1, c2);
}

#[test]
fn test_different_input_different_commitment() {
    let v1 = vec![Fp61::from_u64(1), Fp61::from_u64(2)];
    let v2 = vec![Fp61::from_u64(3), Fp61::from_u64(4)];
    let c1 = ToyCommitment::commit(&v1);
    let c2 = ToyCommitment::commit(&v2);
    assert_ne!(c1, c2);
}

#[test]
fn test_commit_with_blinding() {
    let v1 = vec![Fp61::from_u64(10), Fp61::from_u64(20)];
    let v2 = vec![Fp61::from_u64(3), Fp61::from_u64(4)];
    let r = Fp61::from_u64(5);
    let blinded = ToyCommitment::commit_with_blinding(&v1, &v2, r);

    let combined: Vec<Fp61> = v1
        .iter()
        .zip(v2.iter())
        .map(|(&a, &b)| a.add(r.mul(b)))
        .collect();
    let expected = ToyCommitment::commit(&combined);
    assert_eq!(blinded, expected);
}

#[test]
fn test_value_is_32_bytes() {
    let v = vec![Fp61::from_u64(42)];
    let c = <ToyCommitment as CommitmentScheme<Fp61>>::commit(&v);
    assert_eq!(<ToyCommitment as CommitmentScheme<Fp61>>::value(&c).len(), 32);
}
