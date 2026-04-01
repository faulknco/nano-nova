use rand::Rng;

/// A polynomial ring element in Z_q[X]/(X^n + 1).
///
/// Coefficients are stored in canonical form: values in [0, q-1].
/// The ring dimension `n` must be a power of 2 for the negacyclic
/// reduction X^n = -1 to be well-defined.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RingElement {
    coeffs_data: Vec<u64>,
    n: usize,
    q: u64,
}

impl RingElement {
    /// Construct from a slice of coefficients, reducing each mod q.
    /// Pads with zeros up to length n if the slice is shorter.
    /// Panics if the slice is longer than n.
    pub fn from_coeffs(coeffs: &[u64], n: usize, q: u64) -> Self {
        assert!(
            coeffs.len() <= n,
            "from_coeffs: coeffs.len() ({}) > n ({})",
            coeffs.len(),
            n
        );
        let mut data = Vec::with_capacity(n);
        for &c in coeffs {
            data.push(c % q);
        }
        while data.len() < n {
            data.push(0);
        }
        RingElement { coeffs_data: data, n, q }
    }

    /// Zero polynomial in R_q with dimension n.
    pub fn zero(n: usize, q: u64) -> Self {
        RingElement {
            coeffs_data: vec![0u64; n],
            n,
            q,
        }
    }

    /// Sample a polynomial with coefficients drawn uniformly from [0, bound).
    pub fn random_short<R: Rng>(n: usize, q: u64, bound: u64, rng: &mut R) -> Self {
        let coeffs_data = (0..n).map(|_| rng.gen_range(0..bound)).collect();
        RingElement { coeffs_data, n, q }
    }

    /// Sample a ternary polynomial with coefficients in {0, 1, q-1}.
    pub fn random_ternary<R: Rng>(n: usize, q: u64, rng: &mut R) -> Self {
        let coeffs_data = (0..n)
            .map(|_| match rng.gen_range(0u8..3) {
                0 => 0u64,
                1 => 1u64,
                _ => q - 1,
            })
            .collect();
        RingElement { coeffs_data, n, q }
    }

    // ── Accessors ─────────────────────────────────────────────────────────────

    pub fn coeffs(&self) -> &[u64] {
        &self.coeffs_data
    }

    pub fn n(&self) -> usize {
        self.n
    }

    pub fn q(&self) -> u64 {
        self.q
    }

    // ── Arithmetic ────────────────────────────────────────────────────────────

    /// Coefficient-wise addition mod q.
    pub fn add(&self, other: &Self) -> Self {
        debug_assert_eq!(self.n, other.n);
        debug_assert_eq!(self.q, other.q);
        let data = self
            .coeffs_data
            .iter()
            .zip(other.coeffs_data.iter())
            .map(|(&a, &b)| (a + b) % self.q)
            .collect();
        RingElement { coeffs_data: data, n: self.n, q: self.q }
    }

    /// Coefficient-wise subtraction mod q.
    pub fn sub(&self, other: &Self) -> Self {
        debug_assert_eq!(self.n, other.n);
        debug_assert_eq!(self.q, other.q);
        let data = self
            .coeffs_data
            .iter()
            .zip(other.coeffs_data.iter())
            .map(|(&a, &b)| (a + self.q - b) % self.q)
            .collect();
        RingElement { coeffs_data: data, n: self.n, q: self.q }
    }

    /// Scalar multiplication mod q. Uses u128 intermediates to prevent overflow.
    pub fn scalar_mul(&self, s: u64) -> Self {
        let data = self
            .coeffs_data
            .iter()
            .map(|&c| ((c as u128 * s as u128) % self.q as u128) as u64)
            .collect();
        RingElement { coeffs_data: data, n: self.n, q: self.q }
    }

    /// Negation: (q - c) % q per coefficient.
    pub fn neg(&self) -> Self {
        let data = self
            .coeffs_data
            .iter()
            .map(|&c| (self.q - c) % self.q)
            .collect();
        RingElement { coeffs_data: data, n: self.n, q: self.q }
    }

    // ── Centered representation ───────────────────────────────────────────────

    /// Map a canonical coefficient c in [0, q-1] to the centered range
    /// (-q/2, q/2]. Values <= q/2 are returned as-is; larger values have q
    /// subtracted.
    pub fn centered_coeff(&self, c: u64) -> i64 {
        if c <= self.q / 2 {
            c as i64
        } else {
            c as i64 - self.q as i64
        }
    }

    // ── Norms ─────────────────────────────────────────────────────────────────

    /// L2 norm of the centered coefficient vector.
    pub fn l2_norm(&self) -> f64 {
        let sum_sq: f64 = self
            .coeffs_data
            .iter()
            .map(|&c| {
                let cc = self.centered_coeff(c) as f64;
                cc * cc
            })
            .sum();
        sum_sq.sqrt()
    }

    /// L-infinity norm: max absolute value of centered coefficients.
    pub fn linf_norm(&self) -> u64 {
        self.coeffs_data
            .iter()
            .map(|&c| self.centered_coeff(c).unsigned_abs())
            .max()
            .unwrap_or(0)
    }

    // ── Polynomial multiplication ─────────────────────────────────────────────

    /// Schoolbook negacyclic multiplication in Z_q[X]/(X^n + 1).
    ///
    /// O(n^2). Uses i128 intermediates to avoid overflow when accumulating
    /// products before the final mod reduction.
    pub fn mul_schoolbook(&self, other: &Self) -> Self {
        debug_assert_eq!(self.n, other.n);
        debug_assert_eq!(self.q, other.q);

        let n = self.n;
        let q = self.q as i128;
        // Work in signed i128 to handle the subtractions from negacyclic wrap.
        let mut result = vec![0i128; n];

        for i in 0..n {
            for j in 0..n {
                let idx = i + j;
                let prod = self.coeffs_data[i] as i128 * other.coeffs_data[j] as i128;
                if idx < n {
                    result[idx] += prod;
                } else {
                    // X^n = -1, so coefficient wraps with negation
                    result[idx - n] -= prod;
                }
            }
        }

        // Reduce each coefficient mod q into [0, q-1]
        let data = result
            .into_iter()
            .map(|v| {
                let r = v % q;
                // Bring into [0, q-1]
                if r < 0 { (r + q) as u64 } else { r as u64 }
            })
            .collect();

        RingElement { coeffs_data: data, n, q: self.q }
    }

    /// Karatsuba negacyclic multiplication in Z_q[X]/(X^n + 1).
    ///
    /// Performs standard (non-negacyclic) Karatsuba to produce a 2n-1 length
    /// intermediate, then applies the negacyclic reduction X^n = -1.
    /// Falls back to schoolbook for n <= 64.
    pub fn mul_karatsuba(&self, other: &Self) -> Self {
        debug_assert_eq!(self.n, other.n);
        debug_assert_eq!(self.q, other.q);

        let n = self.n;
        let q = self.q;

        // Produce the 2n-1 unreduced product via recursive Karatsuba.
        let raw = karatsuba_raw(&self.coeffs_data, &other.coeffs_data);

        // Apply negacyclic reduction: for each i in [n, 2n-2], subtract from i-n.
        let mut result = vec![0i128; n];
        for (i, &v) in raw.iter().enumerate() {
            if i < n {
                result[i] += v;
            } else {
                result[i - n] -= v;
            }
        }

        let data = result
            .into_iter()
            .map(|v| v.rem_euclid(q as i128) as u64)
            .collect();

        RingElement { coeffs_data: data, n, q }
    }

    /// Dispatching multiply: uses Karatsuba for n > 64, schoolbook otherwise.
    pub fn mul(&self, other: &Self) -> Self {
        if self.n > 64 {
            self.mul_karatsuba(other)
        } else {
            self.mul_schoolbook(other)
        }
    }
}

// ── Karatsuba helper ──────────────────────────────────────────────────────────

/// Standard (non-negacyclic) polynomial multiplication via Karatsuba.
///
/// Returns a vector of length `2*n - 1` holding the unreduced product
/// coefficients as i128 values. The caller applies the negacyclic reduction.
///
/// Base case: n <= 64 uses schoolbook O(n^2).
fn karatsuba_raw(a: &[u64], b: &[u64]) -> Vec<i128> {
    let n = a.len();
    debug_assert_eq!(n, b.len());

    if n <= 64 {
        // Schoolbook base case — no negacyclic wrapping here.
        let out_len = if n == 0 { 0 } else { 2 * n - 1 };
        let mut result = vec![0i128; out_len];
        for i in 0..n {
            for j in 0..n {
                result[i + j] += a[i] as i128 * b[j] as i128;
            }
        }
        return result;
    }

    let half = n / 2;
    let (a_lo, a_hi) = a.split_at(half);
    let (b_lo, b_hi) = b.split_at(half);

    // z0 = a_lo * b_lo   (length 2*half - 1)
    let z0 = karatsuba_raw(a_lo, b_lo);
    // z2 = a_hi * b_hi   (length 2*(n-half) - 1)
    let z2 = karatsuba_raw(a_hi, b_hi);

    // mid_a = a_lo + a_hi,  mid_b = b_lo + b_hi  (may be length n-half)
    let mid_len = half.max(n - half);
    let mut mid_a = vec![0i128; mid_len];
    let mut mid_b = vec![0i128; mid_len];
    for i in 0..half {
        mid_a[i] += a_lo[i] as i128;
        mid_b[i] += b_lo[i] as i128;
    }
    for i in 0..(n - half) {
        mid_a[i] += a_hi[i] as i128;
        mid_b[i] += b_hi[i] as i128;
    }

    // z1_raw = mid_a * mid_b  (may have negative coefficients due to i128 sums)
    let z1_raw = karatsuba_raw_i128(&mid_a, &mid_b);

    // z1 = z1_raw - z0 - z2
    // We need a working buffer of length 2*mid_len - 1
    let z1_len = 2 * mid_len - 1;
    let mut z1 = z1_raw;
    z1.resize(z1_len, 0i128);
    for (i, &v) in z0.iter().enumerate() {
        z1[i] -= v;
    }
    for (i, &v) in z2.iter().enumerate() {
        z1[i] -= v;
    }

    // Accumulate into result of length 2*n - 1
    let out_len = 2 * n - 1;
    let mut result = vec![0i128; out_len];
    for (i, &v) in z0.iter().enumerate() {
        result[i] += v;
    }
    for (i, &v) in z1.iter().enumerate() {
        result[i + half] += v;
    }
    for (i, &v) in z2.iter().enumerate() {
        result[i + n] += v;
    }
    result
}

/// Same as `karatsuba_raw` but accepts i128 inputs (used for the middle term).
fn karatsuba_raw_i128(a: &[i128], b: &[i128]) -> Vec<i128> {
    let n = a.len();
    debug_assert_eq!(n, b.len());

    if n <= 64 {
        let out_len = if n == 0 { 0 } else { 2 * n - 1 };
        let mut result = vec![0i128; out_len];
        for i in 0..n {
            for j in 0..n {
                result[i + j] += a[i] * b[j];
            }
        }
        return result;
    }

    let half = n / 2;
    let (a_lo, a_hi) = a.split_at(half);
    let (b_lo, b_hi) = b.split_at(half);

    let z0 = karatsuba_raw_i128(a_lo, b_lo);
    let z2 = karatsuba_raw_i128(a_hi, b_hi);

    let mid_len = half.max(n - half);
    let mut mid_a = vec![0i128; mid_len];
    let mut mid_b = vec![0i128; mid_len];
    for i in 0..half {
        mid_a[i] += a_lo[i];
        mid_b[i] += b_lo[i];
    }
    for i in 0..(n - half) {
        mid_a[i] += a_hi[i];
        mid_b[i] += b_hi[i];
    }

    let z1_len = 2 * mid_len - 1;
    let mut z1 = karatsuba_raw_i128(&mid_a, &mid_b);
    z1.resize(z1_len, 0i128);
    for (i, &v) in z0.iter().enumerate() {
        z1[i] -= v;
    }
    for (i, &v) in z2.iter().enumerate() {
        z1[i] -= v;
    }

    let out_len = 2 * n - 1;
    let mut result = vec![0i128; out_len];
    for (i, &v) in z0.iter().enumerate() {
        result[i] += v;
    }
    for (i, &v) in z1.iter().enumerate() {
        result[i + half] += v;
    }
    for (i, &v) in z2.iter().enumerate() {
        result[i + n] += v;
    }
    result
}
