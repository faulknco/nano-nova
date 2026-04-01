use nano_nova::decompose::{decompose_element, num_digits, recompose_element};
use nano_nova::ring::RingElement;

#[test]
fn test_ring_mul_matches_python() {
    // Python: (1 + X) * (2 + 3X) in Z_17[X]/(X^4+1) = [2, 5, 3, 0]
    let a = RingElement::from_coeffs(&[1, 1, 0, 0], 4, 17);
    let b = RingElement::from_coeffs(&[2, 3, 0, 0], 4, 17);
    let c = a.mul(&b);
    assert_eq!(c.coeffs(), &[2, 5, 3, 0]);
}

#[test]
fn test_norms_match_python() {
    // Python: [3, 14, 0, 8] in Z_17 → centered [3, -3, 0, 8]
    // l2 = sqrt(9+9+0+64) = sqrt(82) ≈ 9.0553851381
    // linf = 8
    let e = RingElement::from_coeffs(&[3, 14, 0, 8], 4, 17);
    let l2 = e.l2_norm();
    assert!((l2 - 9.0553851381).abs() < 1e-6);
    assert_eq!(e.linf_norm(), 8);
}

#[test]
fn test_decompose_matches_python() {
    // Python: [13, 7, 16, 0] in Z_17, base=4, num_digits=3
    // digit[0] = [1, 3, 0, 0]
    // digit[1] = [3, 1, 0, 0]
    // digit[2] = [0, 0, 1, 0]
    let elem = RingElement::from_coeffs(&[13, 7, 16, 0], 4, 17);
    let nd = num_digits(17, 4);
    assert_eq!(nd, 3);

    let digits = decompose_element(&elem, 4, nd);
    assert_eq!(digits[0].coeffs(), &[1, 3, 0, 0]);
    assert_eq!(digits[1].coeffs(), &[3, 1, 0, 0]);
    assert_eq!(digits[2].coeffs(), &[0, 0, 1, 0]);

    let recomp = recompose_element(&digits, 4);
    assert_eq!(recomp.coeffs(), &[13, 7, 16, 0]);
}
