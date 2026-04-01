use crate::ring::RingElement;

/// Number of base-B digits needed to represent values in [0, q-1].
pub fn num_digits(q: u64, base: u64) -> usize {
    assert!(base >= 2, "base must be >= 2");
    let mut digits = 0;
    let mut val = q - 1;
    while val > 0 {
        val /= base;
        digits += 1;
    }
    digits
}

/// Decompose a ring element into base-B digits (LSB first).
pub fn decompose_element(elem: &RingElement, base: u64, nd: usize) -> Vec<RingElement> {
    let n = elem.n();
    let q = elem.q();
    let mut remaining: Vec<u64> = elem.coeffs().to_vec();
    let mut digits = Vec::with_capacity(nd);
    for _ in 0..nd {
        let digit_coeffs: Vec<u64> = remaining.iter().map(|&c| c % base).collect();
        digits.push(RingElement::from_coeffs(&digit_coeffs, n, q));
        remaining = remaining.iter().map(|&c| c / base).collect();
    }
    digits
}

/// Recompose a ring element from its base-B digits.
pub fn recompose_element(digits: &[RingElement], base: u64) -> RingElement {
    assert!(!digits.is_empty());
    let n = digits[0].n();
    let q = digits[0].q();
    let mut result = RingElement::zero(n, q);
    let mut power = 1u64;
    for digit in digits {
        result = result.add(&digit.scalar_mul(power));
        power = ((power as u128 * base as u128) % q as u128) as u64;
    }
    result
}

/// Decompose a vector of ring elements, returning digit vectors.
/// Output[d][i] is the d-th digit of the i-th input element.
pub fn decompose_vector(elems: &[RingElement], base: u64, nd: usize) -> Vec<Vec<RingElement>> {
    let all_digits: Vec<Vec<RingElement>> = elems.iter()
        .map(|e| decompose_element(e, base, nd))
        .collect();
    (0..nd)
        .map(|d| all_digits.iter().map(|digits| digits[d].clone()).collect())
        .collect()
}

/// Recompose a vector of ring elements from digit vectors.
pub fn recompose_vector(digit_vecs: &[Vec<RingElement>], base: u64) -> Vec<RingElement> {
    let num_elems = digit_vecs[0].len();
    (0..num_elems)
        .map(|i| {
            let digits: Vec<RingElement> = digit_vecs.iter().map(|dv| dv[i].clone()).collect();
            recompose_element(&digits, base)
        })
        .collect()
}
