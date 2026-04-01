use nano_nova::field::{Field, Fp61};

#[test]
fn test_add_commutative() {
    let a = Fp61::from_u64(42);
    let b = Fp61::from_u64(1337);
    assert_eq!(a.add(b), b.add(a));
}

#[test]
fn test_mul_commutative() {
    let a = Fp61::from_u64(42);
    let b = Fp61::from_u64(1337);
    assert_eq!(a.mul(b), b.mul(a));
}

#[test]
fn test_additive_identity() {
    let a = Fp61::from_u64(12345);
    assert_eq!(a.add(Fp61::zero()), a);
}

#[test]
fn test_multiplicative_identity() {
    let a = Fp61::from_u64(12345);
    assert_eq!(a.mul(Fp61::one()), a);
}

#[test]
fn test_multiplicative_inverse() {
    let a = Fp61::from_u64(42);
    let a_inv = a.inv();
    assert_eq!(a.mul(a_inv), Fp61::one());
}

#[test]
fn test_sub_is_add_neg() {
    let a = Fp61::from_u64(100);
    let b = Fp61::from_u64(42);
    let result = a.sub(b);
    assert_eq!(result.add(b), a);
}

#[test]
fn test_from_u64_reduces_mod_p() {
    let p = (1u64 << 61) - 1;
    assert_eq!(Fp61::from_u64(p), Fp61::zero());
}

#[test]
fn test_to_bytes_deterministic() {
    let a = Fp61::from_u64(42);
    assert_eq!(a.to_bytes(), a.to_bytes());
    assert_eq!(a.to_bytes().len(), 8);
}

#[test]
fn test_add_wraps_around_modulus() {
    let p = (1u64 << 61) - 1;
    let a = Fp61::from_u64(p - 1);
    let b = Fp61::from_u64(2);
    assert_eq!(a.add(b), Fp61::one());
}

#[test]
fn test_mul_large_values() {
    let p = (1u64 << 61) - 1;
    let a = Fp61::from_u64(p - 1); // -1 mod p
    let b = Fp61::from_u64(p - 1); // -1 mod p
    assert_eq!(a.mul(b), Fp61::one()); // (-1)*(-1) = 1
}

#[test]
#[should_panic(expected = "cannot invert zero")]
fn test_inv_zero_panics() {
    Fp61::zero().inv();
}
