use nano_nova::ring::RingElement;

#[test]
fn test_add() {
    let a = RingElement::from_coeffs(&[1, 2, 3, 0], 4, 17);
    let b = RingElement::from_coeffs(&[4, 5, 6, 0], 4, 17);
    let c = a.add(&b);
    assert_eq!(c.coeffs(), &[5, 7, 9, 0]);
}

#[test]
fn test_add_wraps_mod_q() {
    let a = RingElement::from_coeffs(&[15, 16], 2, 17);
    let b = RingElement::from_coeffs(&[3, 3], 2, 17);
    let c = a.add(&b);
    assert_eq!(c.coeffs(), &[1, 2]);
}

#[test]
fn test_sub() {
    let a = RingElement::from_coeffs(&[5, 10], 2, 17);
    let b = RingElement::from_coeffs(&[3, 12], 2, 17);
    let c = a.sub(&b);
    assert_eq!(c.coeffs(), &[2, 15]);
}

#[test]
fn test_scalar_mul() {
    let a = RingElement::from_coeffs(&[3, 5, 7, 0], 4, 17);
    let b = a.scalar_mul(3);
    assert_eq!(b.coeffs(), &[9, 15, 4, 0]);
}

#[test]
fn test_neg() {
    let a = RingElement::from_coeffs(&[0, 5, 10, 0], 4, 17);
    let b = a.neg();
    assert_eq!(b.coeffs(), &[0, 12, 7, 0]);
}

#[test]
fn test_l2_norm() {
    // coeffs [3, 12] with q=17: centered coeffs are 3 and 12-17=-5
    let a = RingElement::from_coeffs(&[3, 12], 2, 17);
    let norm = a.l2_norm();
    let expected = ((3.0f64 * 3.0) + (5.0 * 5.0)).sqrt();
    assert!((norm - expected).abs() < 1e-10);
}

#[test]
fn test_linf_norm() {
    // coeffs [3, 12] with q=17: centered coeffs are 3 and -5, |max| = 5
    let a = RingElement::from_coeffs(&[3, 12], 2, 17);
    assert_eq!(a.linf_norm(), 5);
}

#[test]
fn test_zero() {
    let z = RingElement::zero(4, 17);
    assert_eq!(z.coeffs(), &[0, 0, 0, 0]);
    assert_eq!(z.l2_norm(), 0.0);
}

#[test]
fn test_from_coeffs_reduces_mod_q() {
    let a = RingElement::from_coeffs(&[20, 34], 2, 17);
    assert_eq!(a.coeffs(), &[3, 0]);
}

#[test]
fn test_mul_schoolbook_trivial() {
    // [1, 0, 0, 0] * [1, 0, 0, 0] = [1, 0, 0, 0] (identity * identity)
    let a = RingElement::from_coeffs(&[1, 0, 0, 0], 4, 17);
    let b = RingElement::from_coeffs(&[1, 0, 0, 0], 4, 17);
    let c = a.mul_schoolbook(&b);
    assert_eq!(c.coeffs(), &[1, 0, 0, 0]);
}

#[test]
fn test_mul_schoolbook_negacyclic() {
    // [0, 1, 0, 0] * [0, 1, 0, 0] = x * x = x^2 = [0, 0, 1, 0]
    // [0, 0, 1, 0] * [0, 0, 1, 0] = x^2 * x^2 = x^4 = -1 = [16, 0, 0, 0] mod 17
    let a = RingElement::from_coeffs(&[0, 1, 0, 0], 4, 17);
    let b = a.mul_schoolbook(&a);
    assert_eq!(b.coeffs(), &[0, 0, 1, 0]);

    let c = b.mul_schoolbook(&b);
    // x^4 = -1 mod (x^4+1), so coefficient of x^0 = -1 = 16 mod 17
    assert_eq!(c.coeffs(), &[16, 0, 0, 0]);
}

#[test]
fn test_mul_karatsuba_delegates_to_schoolbook() {
    let a = RingElement::from_coeffs(&[1, 2, 3, 4], 4, 17);
    let b = RingElement::from_coeffs(&[5, 6, 7, 8], 4, 17);
    let school = a.mul_schoolbook(&b);
    let karat = a.mul_karatsuba(&b);
    assert_eq!(school.coeffs(), karat.coeffs());
}

#[test]
fn test_mul_dispatches() {
    let a = RingElement::from_coeffs(&[1, 2, 3, 4], 4, 17);
    let b = RingElement::from_coeffs(&[5, 6, 7, 8], 4, 17);
    let direct = a.mul_schoolbook(&b);
    let dispatched = a.mul(&b);
    assert_eq!(direct.coeffs(), dispatched.coeffs());
}

#[test]
fn test_getters() {
    let a = RingElement::from_coeffs(&[1, 2, 3, 4], 4, 17);
    assert_eq!(a.n(), 4);
    assert_eq!(a.q(), 17);
}

#[test]
fn test_centered_coeff() {
    let a = RingElement::zero(4, 17);
    // q=17, q/2=8: values <= 8 stay, values > 8 become negative
    assert_eq!(a.centered_coeff(0), 0);
    assert_eq!(a.centered_coeff(8), 8);
    assert_eq!(a.centered_coeff(9), -8);  // 9 - 17 = -8
    assert_eq!(a.centered_coeff(16), -1); // 16 - 17 = -1
}
