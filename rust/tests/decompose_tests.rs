use nano_nova::ring::RingElement;
use nano_nova::decompose::{decompose_element, recompose_element, num_digits};

#[test]
fn test_num_digits() {
    assert_eq!(num_digits(65536, 2), 16);
    assert_eq!(num_digits(65537, 2), 17);
    assert_eq!(num_digits(65536, 16), 4);
    assert_eq!(num_digits(256, 4), 4);
}

#[test]
fn test_decompose_recompose_roundtrip() {
    let elem = RingElement::from_coeffs(&[42, 100, 255, 0], 4, 256);
    let base = 4u64;
    let nd = num_digits(256, base);
    let digits = decompose_element(&elem, base, nd);
    for digit in &digits {
        for &c in digit.coeffs() {
            assert!(c < base, "digit coefficient {} >= base {}", c, base);
        }
    }
    let recomposed = recompose_element(&digits, base);
    assert_eq!(recomposed.coeffs(), elem.coeffs());
}

#[test]
fn test_decompose_recompose_large_q() {
    use rand::SeedableRng;
    use rand_xoshiro::Xoshiro256PlusPlus;
    let mut rng = Xoshiro256PlusPlus::seed_from_u64(42);
    let n = 64;
    let q: u64 = 65537;
    let base = 8u64;
    let elem = RingElement::random_short(n, q, q, &mut rng);
    let nd = num_digits(q, base);
    let digits = decompose_element(&elem, base, nd);
    let recomposed = recompose_element(&digits, base);
    assert_eq!(recomposed.coeffs(), elem.coeffs());
}

#[test]
fn test_decompose_base2() {
    // n must be power of 2, so use n=1 (which is 2^0)... actually n=1 is tricky.
    // Use n=2 and check first coefficient only
    let elem = RingElement::from_coeffs(&[13, 0], 2, 16);
    let digits = decompose_element(&elem, 2, 4);
    assert_eq!(digits[0].coeffs(), &[1, 0]); // 2^0 digit of 13 = 1
    assert_eq!(digits[1].coeffs(), &[0, 0]); // 2^1 digit of 13 = 0
    assert_eq!(digits[2].coeffs(), &[1, 0]); // 2^2 digit of 13 = 1
    assert_eq!(digits[3].coeffs(), &[1, 0]); // 2^3 digit of 13 = 1
}
