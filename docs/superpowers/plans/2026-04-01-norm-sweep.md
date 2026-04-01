# LatticeFold Norm Growth Parameter Sweep Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rust Monte Carlo parameter sweep for LatticeFold norm growth analysis, with streaming CSV output for Python publication figures.

**Architecture:** 4 new Rust modules (ring.rs, decompose.rs, norm_sim.rs, norm_sweep.rs) added to the existing nano-nova crate, plus a new `bench-norm` CLI subcommand. Ring arithmetic uses schoolbook for n≤64 and Karatsuba for n>64 over arbitrary moduli. Monte Carlo driver streams results to CSV incrementally.

**Tech Stack:** Rust, rand_xoshiro (seeded RNG), clap (CLI), existing nano-nova crate

**Spec:** `docs/superpowers/specs/2026-04-01-norm-sweep-design.md`

**Python reference:** `experiments/norm_growth/` (ring_arithmetic.py, decompose.py, lattice_fold_sim.py, monte_carlo.py)

---

### Task 1: Dependencies and Module Stubs

**Files:**
- Modify: `rust/Cargo.toml`
- Modify: `rust/src/lib.rs`
- Create: `rust/src/ring.rs`
- Create: `rust/src/decompose.rs`
- Create: `rust/src/norm_sim.rs`
- Create: `rust/src/norm_sweep.rs`

- [ ] **Step 1: Update Cargo.toml**

Add `rand_xoshiro` dependency and release profile tuning:

```toml
[dependencies]
sha2 = "0.10"
rand = "0.8"
rand_xoshiro = "0.6"
clap = { version = "4", features = ["derive"] }

[profile.release]
opt-level = 3
lto = true
codegen-units = 1
```

- [ ] **Step 2: Update lib.rs**

```rust
pub mod field;
pub mod matrix;
pub mod commitment;
pub mod r1cs;
pub mod folding;
pub mod ivc;
pub mod examples;
pub mod ring;
pub mod decompose;
pub mod norm_sim;
pub mod norm_sweep;
```

- [ ] **Step 3: Create empty stub files**

Create `rust/src/ring.rs`, `rust/src/decompose.rs`, `rust/src/norm_sim.rs`, `rust/src/norm_sweep.rs` — all empty.

- [ ] **Step 4: Verify compilation**

Run: `cd ~/Projects/nano-nova/rust && cargo build`
Expected: Compiles (warnings about empty modules OK)

- [ ] **Step 5: Commit**

```bash
cd ~/Projects/nano-nova && git add rust/Cargo.toml rust/src/lib.rs rust/src/ring.rs rust/src/decompose.rs rust/src/norm_sim.rs rust/src/norm_sweep.rs && git commit -m "feat(rust): add module stubs and deps for norm growth sweep"
```

---

### Task 2: Ring Arithmetic — RingElement Basics

**Files:**
- Create: `rust/src/ring.rs`
- Create: `rust/tests/ring_tests.rs`

Implements `RingElement` with add, sub, scalar_mul, norms, and constructors. Polynomial multiplication is deferred to Task 3.

- [ ] **Step 1: Write basic ring element tests**

```rust
// rust/tests/ring_tests.rs
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
    assert_eq!(c.coeffs(), &[1, 2]); // (15+3)%17=1, (16+3)%17=2
}

#[test]
fn test_sub() {
    let a = RingElement::from_coeffs(&[5, 10], 2, 17);
    let b = RingElement::from_coeffs(&[3, 12], 2, 17);
    let c = a.sub(&b);
    assert_eq!(c.coeffs(), &[2, 15]); // 5-3=2, (10-12)%17=15
}

#[test]
fn test_scalar_mul() {
    let a = RingElement::from_coeffs(&[3, 5, 7, 0], 4, 17);
    let b = a.scalar_mul(3);
    assert_eq!(b.coeffs(), &[9, 15, 4, 0]); // 7*3=21%17=4
}

#[test]
fn test_neg() {
    let a = RingElement::from_coeffs(&[0, 5, 10], 3, 17);
    let b = a.neg();
    assert_eq!(b.coeffs(), &[0, 12, 7]); // 17-5=12, 17-10=7
}

#[test]
fn test_l2_norm() {
    // Centered: [3, -5] for coeffs [3, 12] with q=17
    let a = RingElement::from_coeffs(&[3, 12], 2, 17);
    let norm = a.l2_norm();
    let expected = ((3.0f64 * 3.0) + (5.0 * 5.0)).sqrt(); // sqrt(34)
    assert!((norm - expected).abs() < 1e-10);
}

#[test]
fn test_linf_norm() {
    let a = RingElement::from_coeffs(&[3, 12], 2, 17);
    assert_eq!(a.linf_norm(), 5); // max(|3|, |12-17|) = max(3, 5)
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
    assert_eq!(a.coeffs(), &[3, 0]); // 20%17=3, 34%17=0
}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/Projects/nano-nova/rust && cargo test --test ring_tests`
Expected: FAIL — `RingElement` not defined

- [ ] **Step 3: Implement RingElement basics**

```rust
// rust/src/ring.rs
use rand::Rng;

/// An element of Z_q[X]/(X^n+1).
///
/// Coefficients stored in [0, q-1]. The polynomial X^n = -1 in this ring.
#[derive(Clone, Debug)]
pub struct RingElement {
    coeffs_data: Vec<u64>,
    n: usize,
    q: u64,
}

impl RingElement {
    pub fn from_coeffs(coeffs: &[u64], n: usize, q: u64) -> Self {
        assert!(n > 0 && (n & (n - 1)) == 0, "n must be a power of 2");
        assert!(q > 1, "q must be > 1");
        let mut data: Vec<u64> = coeffs.iter().map(|&c| c % q).collect();
        data.resize(n, 0);
        RingElement { coeffs_data: data, n, q }
    }

    pub fn zero(n: usize, q: u64) -> Self {
        RingElement { coeffs_data: vec![0; n], n, q }
    }

    pub fn coeffs(&self) -> &[u64] {
        &self.coeffs_data
    }

    pub fn n(&self) -> usize {
        self.n
    }

    pub fn q(&self) -> u64 {
        self.q
    }

    /// Random element with coefficients in [0, bound).
    pub fn random_short(n: usize, q: u64, bound: u64, rng: &mut impl Rng) -> Self {
        let coeffs: Vec<u64> = (0..n).map(|_| rng.gen_range(0..bound)).collect();
        RingElement { coeffs_data: coeffs, n, q }
    }

    /// Random ternary element: coefficients in {0, 1, q-1} (representing {0, 1, -1}).
    pub fn random_ternary(n: usize, q: u64, rng: &mut impl Rng) -> Self {
        let coeffs: Vec<u64> = (0..n)
            .map(|_| {
                match rng.gen_range(0u8..3) {
                    0 => 0,
                    1 => 1,
                    _ => q - 1, // represents -1 mod q
                }
            })
            .collect();
        RingElement { coeffs_data: coeffs, n, q }
    }

    pub fn add(&self, other: &Self) -> Self {
        assert_eq!(self.n, other.n);
        assert_eq!(self.q, other.q);
        let coeffs: Vec<u64> = self.coeffs_data.iter().zip(other.coeffs_data.iter())
            .map(|(&a, &b)| (a + b) % self.q)
            .collect();
        RingElement { coeffs_data: coeffs, n: self.n, q: self.q }
    }

    pub fn sub(&self, other: &Self) -> Self {
        assert_eq!(self.n, other.n);
        assert_eq!(self.q, other.q);
        let coeffs: Vec<u64> = self.coeffs_data.iter().zip(other.coeffs_data.iter())
            .map(|(&a, &b)| (a + self.q - b) % self.q)
            .collect();
        RingElement { coeffs_data: coeffs, n: self.n, q: self.q }
    }

    pub fn scalar_mul(&self, s: u64) -> Self {
        let coeffs: Vec<u64> = self.coeffs_data.iter()
            .map(|&c| ((c as u128 * s as u128) % self.q as u128) as u64)
            .collect();
        RingElement { coeffs_data: coeffs, n: self.n, q: self.q }
    }

    pub fn neg(&self) -> Self {
        let coeffs: Vec<u64> = self.coeffs_data.iter()
            .map(|&c| if c == 0 { 0 } else { self.q - c })
            .collect();
        RingElement { coeffs_data: coeffs, n: self.n, q: self.q }
    }

    /// Centered coefficient: c if c <= q/2, else c - q (as i64).
    fn centered_coeff(&self, c: u64) -> i64 {
        if c <= self.q / 2 {
            c as i64
        } else {
            c as i64 - self.q as i64
        }
    }

    pub fn l2_norm(&self) -> f64 {
        let sum_sq: f64 = self.coeffs_data.iter()
            .map(|&c| {
                let centered = self.centered_coeff(c) as f64;
                centered * centered
            })
            .sum();
        sum_sq.sqrt()
    }

    pub fn linf_norm(&self) -> u64 {
        self.coeffs_data.iter()
            .map(|&c| self.centered_coeff(c).unsigned_abs())
            .max()
            .unwrap_or(0)
    }

    /// Negacyclic polynomial multiplication: schoolbook O(n^2).
    pub fn mul_schoolbook(&self, other: &Self) -> Self {
        assert_eq!(self.n, other.n);
        assert_eq!(self.q, other.q);
        let n = self.n;
        let q = self.q as u128;
        let mut result = vec![0u128; n];

        for i in 0..n {
            for j in 0..n {
                let prod = self.coeffs_data[i] as u128 * other.coeffs_data[j] as u128;
                let idx = i + j;
                if idx < n {
                    result[idx] = (result[idx] + prod) % q;
                } else {
                    // X^n = -1, so X^(n+k) = -X^k
                    result[idx - n] = (result[idx - n] + q - prod % q) % q;
                }
            }
        }

        let coeffs: Vec<u64> = result.iter().map(|&c| c as u64).collect();
        RingElement { coeffs_data: coeffs, n: self.n, q: self.q }
    }

    /// Polynomial multiplication — dispatches to schoolbook or Karatsuba.
    pub fn mul(&self, other: &Self) -> Self {
        if self.n <= 64 {
            self.mul_schoolbook(other)
        } else {
            self.mul_karatsuba(other)
        }
    }

    /// Karatsuba negacyclic multiplication O(n^1.585).
    /// Placeholder — implemented in Task 3.
    pub fn mul_karatsuba(&self, other: &Self) -> Self {
        // Temporary: delegate to schoolbook. Task 3 replaces this.
        self.mul_schoolbook(other)
    }
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/Projects/nano-nova/rust && cargo test --test ring_tests`
Expected: All 9 tests pass

- [ ] **Step 5: Commit**

```bash
cd ~/Projects/nano-nova && git add rust/src/ring.rs rust/tests/ring_tests.rs && git commit -m "feat(rust): RingElement with add, sub, scalar_mul, norms, schoolbook mul"
```

---

### Task 3: Karatsuba Negacyclic Multiplication

**Files:**
- Modify: `rust/src/ring.rs`
- Modify: `rust/tests/ring_tests.rs`

- [ ] **Step 1: Write Karatsuba tests**

Add to `rust/tests/ring_tests.rs`:

```rust
#[test]
fn test_schoolbook_mul_basic() {
    // (1 + X) * (1 + X) = 1 + 2X + X^2 in Z_17[X]/(X^4+1)
    let a = RingElement::from_coeffs(&[1, 1, 0, 0], 4, 17);
    let b = a.mul_schoolbook(&a);
    assert_eq!(b.coeffs(), &[1, 2, 1, 0]);
}

#[test]
fn test_schoolbook_mul_negacyclic() {
    // X^3 * X = X^4 = -1 mod (X^4+1), so result = [q-1, 0, 0, 0]
    let a = RingElement::from_coeffs(&[0, 0, 0, 1], 4, 17); // X^3
    let b = RingElement::from_coeffs(&[0, 1, 0, 0], 4, 17); // X
    let c = a.mul_schoolbook(&b);
    assert_eq!(c.coeffs(), &[16, 0, 0, 0]); // -1 mod 17 = 16
}

#[test]
fn test_karatsuba_matches_schoolbook_n128() {
    use rand::SeedableRng;
    use rand_xoshiro::Xoshiro256PlusPlus;

    let mut rng = Xoshiro256PlusPlus::seed_from_u64(42);
    let n = 128;
    let q = 65537u64;
    let a = RingElement::random_short(n, q, q, &mut rng);
    let b = RingElement::random_short(n, q, q, &mut rng);

    let school = a.mul_schoolbook(&b);
    let karat = a.mul_karatsuba(&b);
    assert_eq!(school.coeffs(), karat.coeffs());
}

#[test]
fn test_karatsuba_matches_schoolbook_n256() {
    use rand::SeedableRng;
    use rand_xoshiro::Xoshiro256PlusPlus;

    let mut rng = Xoshiro256PlusPlus::seed_from_u64(99);
    let n = 256;
    let q: u64 = 4294967296; // 2^32
    let a = RingElement::random_short(n, q, 1000, &mut rng);
    let b = RingElement::random_short(n, q, 1000, &mut rng);

    let school = a.mul_schoolbook(&b);
    let karat = a.mul_karatsuba(&b);
    assert_eq!(school.coeffs(), karat.coeffs());
}

#[test]
fn test_mul_dispatches_karatsuba_for_large_n() {
    use rand::SeedableRng;
    use rand_xoshiro::Xoshiro256PlusPlus;

    let mut rng = Xoshiro256PlusPlus::seed_from_u64(77);
    let n = 128;
    let q = 65537u64;
    let a = RingElement::random_short(n, q, q, &mut rng);
    let b = RingElement::random_short(n, q, q, &mut rng);

    // mul() should give the same result as schoolbook
    let via_mul = a.mul(&b);
    let via_school = a.mul_schoolbook(&b);
    assert_eq!(via_mul.coeffs(), via_school.coeffs());
}
```

- [ ] **Step 2: Run tests to verify they pass (Karatsuba still delegates to schoolbook)**

Run: `cd ~/Projects/nano-nova/rust && cargo test --test ring_tests`
Expected: All 14 tests pass (Karatsuba delegates to schoolbook for now)

- [ ] **Step 3: Implement Karatsuba**

Replace `mul_karatsuba` in `rust/src/ring.rs`:

```rust
    /// Karatsuba negacyclic multiplication O(n^1.585).
    ///
    /// For negacyclic ring Z_q[X]/(X^n+1), splits polynomials into halves
    /// and uses 3 multiplications instead of 4. Base case at n <= 64
    /// falls back to schoolbook.
    pub fn mul_karatsuba(&self, other: &Self) -> Self {
        assert_eq!(self.n, other.n);
        assert_eq!(self.q, other.q);

        if self.n <= 64 {
            return self.mul_schoolbook(other);
        }

        let n = self.n;
        let q = self.q;
        let half = n / 2;

        // Split: f = f_lo + X^(n/2) * f_hi
        let f_lo = RingElement::from_coeffs(&self.coeffs_data[..half], half, q);
        let f_hi = RingElement::from_coeffs(&self.coeffs_data[half..], half, q);
        let g_lo = RingElement::from_coeffs(&other.coeffs_data[..half], half, q);
        let g_hi = RingElement::from_coeffs(&other.coeffs_data[half..], half, q);

        // Three recursive multiplications (in the sub-ring Z_q[X]/(X^(n/2)+1)):
        // But wait — the sub-ring is X^(n/2)+1 only if we handle the negacyclic
        // structure correctly. For Karatsuba on negacyclic polynomials:
        //
        // f*g mod (X^n+1) where f = f_lo + X^h * f_hi, g = g_lo + X^h * g_hi:
        //   = f_lo*g_lo + X^h*(f_lo*g_hi + f_hi*g_lo) + X^n*(f_hi*g_hi)
        //   = f_lo*g_lo + X^h*(f_lo*g_hi + f_hi*g_lo) - f_hi*g_hi  (since X^n = -1)
        //
        // Using Karatsuba trick:
        //   z0 = f_lo * g_lo       (in Z_q[X] mod X^h, NOT negacyclic)
        //   z2 = f_hi * g_hi       (in Z_q[X] mod X^h, NOT negacyclic)
        //   z1 = (f_lo + f_hi)*(g_lo + g_hi) - z0 - z2
        //
        // Result = (z0 - z2) + X^h * z1, reduced mod (X^n + 1)
        //
        // BUT: z0, z1, z2 are degree-(n-2) polynomials (2*half - 2 coefficients),
        // not reduced mod X^(n/2)+1. We need to handle the wrap-around into
        // the full n-coefficient result, then apply X^n = -1.
        //
        // Simpler approach: do standard Karatsuba producing a 2n-1 length result,
        // then reduce mod (X^n + 1).

        // Standard polynomial Karatsuba (no negacyclic reduction in sub-calls)
        let mut result_long = vec![0i128; 2 * n];
        Self::karatsuba_plain(
            &self.coeffs_data, &other.coeffs_data, &mut result_long, q,
        );

        // Negacyclic reduction: X^n = -1, so coeff[i+n] subtracts from coeff[i]
        let mut result = vec![0u64; n];
        for i in 0..n {
            let val = result_long[i] - result_long[i + n];
            result[i] = val.rem_euclid(q as i128) as u64;
        }

        RingElement { coeffs_data: result, n, q }
    }

    /// Standard Karatsuba polynomial multiplication (no modular reduction).
    /// Writes a + b coefficients into `out` (length must be >= 2*max(a.len(), b.len())).
    fn karatsuba_plain(a: &[u64], b: &[u64], out: &mut [i128], q: u64) {
        let n = a.len();
        assert_eq!(n, b.len());

        if n <= 64 {
            // Base case: schoolbook into out
            for v in out.iter_mut().take(2 * n) {
                *v = 0;
            }
            for i in 0..n {
                for j in 0..n {
                    out[i + j] += a[i] as i128 * b[j] as i128;
                }
            }
            // Reduce intermediate values to prevent overflow on very large n
            for v in out.iter_mut().take(2 * n) {
                *v = v.rem_euclid(q as i128);
            }
            return;
        }

        let half = n / 2;

        let a_lo = &a[..half];
        let a_hi = &a[half..];
        let b_lo = &b[..half];
        let b_hi = &b[half..];

        // z0 = a_lo * b_lo
        let mut z0 = vec![0i128; 2 * half];
        Self::karatsuba_plain(a_lo, b_lo, &mut z0, q);

        // z2 = a_hi * b_hi
        let mut z2 = vec![0i128; 2 * half];
        Self::karatsuba_plain(a_hi, b_hi, &mut z2, q);

        // z1 = (a_lo + a_hi) * (b_lo + b_hi) - z0 - z2
        let a_sum: Vec<u64> = a_lo.iter().zip(a_hi.iter())
            .map(|(&x, &y)| (x + y) % q)
            .collect();
        let b_sum: Vec<u64> = b_lo.iter().zip(b_hi.iter())
            .map(|(&x, &y)| (x + y) % q)
            .collect();
        let mut z1_full = vec![0i128; 2 * half];
        Self::karatsuba_plain(&a_sum, &b_sum, &mut z1_full, q);

        // z1 = z1_full - z0 - z2
        for i in 0..(2 * half) {
            z1_full[i] = (z1_full[i] - z0[i] - z2[i]).rem_euclid(q as i128);
        }

        // Combine into out: result[0..2n-1]
        for v in out.iter_mut().take(2 * n) {
            *v = 0;
        }
        for i in 0..(2 * half) {
            out[i] = (out[i] + z0[i]) % q as i128;
            out[i + half] = (out[i + half] + z1_full[i]) % q as i128;
            out[i + n] = (out[i + n] + z2[i]) % q as i128;
        }
    }
```

- [ ] **Step 4: Run tests to verify Karatsuba matches schoolbook**

Run: `cd ~/Projects/nano-nova/rust && cargo test --test ring_tests`
Expected: All 14 tests pass, including karatsuba-vs-schoolbook cross-checks

- [ ] **Step 5: Commit**

```bash
cd ~/Projects/nano-nova && git add rust/src/ring.rs rust/tests/ring_tests.rs && git commit -m "feat(rust): Karatsuba negacyclic polynomial multiplication"
```

---

### Task 4: Base-B Decomposition

**Files:**
- Create: `rust/src/decompose.rs`
- Create: `rust/tests/decompose_tests.rs`

- [ ] **Step 1: Write decomposition tests**

```rust
// rust/tests/decompose_tests.rs
use nano_nova::ring::RingElement;
use nano_nova::decompose::{decompose_element, recompose_element, num_digits};

#[test]
fn test_num_digits() {
    assert_eq!(num_digits(65536, 2), 16);   // ceil(log2(65536)) = 16
    assert_eq!(num_digits(65537, 2), 17);   // ceil(log2(65537)) = 17
    assert_eq!(num_digits(65536, 16), 4);   // ceil(log16(65536)) = 4
    assert_eq!(num_digits(256, 4), 4);      // ceil(log4(256)) = 4
}

#[test]
fn test_decompose_recompose_roundtrip() {
    let elem = RingElement::from_coeffs(&[42, 100, 255, 0], 4, 256);
    let base = 4u64;
    let nd = num_digits(256, base);
    let digits = decompose_element(&elem, base, nd);

    // Each digit should have coefficients in [0, base-1]
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
    // 13 in base 2 = [1, 0, 1, 1] (LSB first)
    let elem = RingElement::from_coeffs(&[13], 1, 16);
    let digits = decompose_element(&elem, 2, 4);
    assert_eq!(digits[0].coeffs(), &[1]); // 2^0 digit
    assert_eq!(digits[1].coeffs(), &[0]); // 2^1 digit
    assert_eq!(digits[2].coeffs(), &[1]); // 2^2 digit
    assert_eq!(digits[3].coeffs(), &[1]); // 2^3 digit
}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/Projects/nano-nova/rust && cargo test --test decompose_tests`
Expected: FAIL

- [ ] **Step 3: Implement decomposition**

```rust
// rust/src/decompose.rs
use crate::ring::RingElement;

/// Number of base-B digits needed to represent values in [0, q-1].
pub fn num_digits(q: u64, base: u64) -> usize {
    assert!(base >= 2, "base must be >= 2");
    let mut digits = 0;
    let mut val = q - 1; // max value we need to represent
    while val > 0 {
        val /= base;
        digits += 1;
    }
    digits
}

/// Decompose a ring element into base-B digits (LSB first).
///
/// Each output RingElement has coefficients in [0, base-1].
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
///
/// elem = digits[0] + base*digits[1] + base^2*digits[2] + ...
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
///
/// Input: vec of k RingElements.
/// Output: vec of num_digits RingElement-vectors, where output[d][i] is
/// the d-th digit of the i-th input element.
pub fn decompose_vector(
    elems: &[RingElement], base: u64, nd: usize,
) -> Vec<Vec<RingElement>> {
    let all_digits: Vec<Vec<RingElement>> = elems.iter()
        .map(|e| decompose_element(e, base, nd))
        .collect();

    // Transpose: group by digit position
    (0..nd)
        .map(|d| all_digits.iter().map(|digits| digits[d].clone()).collect())
        .collect()
}

/// Recompose a vector of ring elements from digit vectors.
pub fn recompose_vector(digit_vecs: &[Vec<RingElement>], base: u64) -> Vec<RingElement> {
    let num_elems = digit_vecs[0].len();
    (0..num_elems)
        .map(|i| {
            let digits: Vec<RingElement> = digit_vecs.iter()
                .map(|dv| dv[i].clone())
                .collect();
            recompose_element(&digits, base)
        })
        .collect()
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/Projects/nano-nova/rust && cargo test --test decompose_tests`
Expected: All 4 tests pass

- [ ] **Step 5: Commit**

```bash
cd ~/Projects/nano-nova && git add rust/src/decompose.rs rust/tests/decompose_tests.rs && git commit -m "feat(rust): base-B digit decomposition and recomposition"
```

---

### Task 5: Folding Simulation (Single Trial)

**Files:**
- Create: `rust/src/norm_sim.rs`
- Create: `rust/tests/norm_sim_tests.rs`

- [ ] **Step 1: Write simulation tests**

```rust
// rust/tests/norm_sim_tests.rs
use nano_nova::norm_sim::{SimConfig, simulate_trial};
use rand::SeedableRng;
use rand_xoshiro::Xoshiro256PlusPlus;

#[test]
fn test_naive_fold_norms_grow() {
    let config = SimConfig {
        n: 64,
        q: 65537,
        base: 0, // naive
        num_folds: 100,
        witness_length: 4,
        initial_bound: 16,
    };
    let mut rng = Xoshiro256PlusPlus::seed_from_u64(42);
    let results = simulate_trial(&config, &mut rng);

    assert_eq!(results.len(), 100);
    // Naive folding: norms should grow over time
    assert!(results.last().unwrap().l2 > results.first().unwrap().l2);
}

#[test]
fn test_decompose_fold_digit_norms_bounded() {
    let config = SimConfig {
        n: 64,
        q: 65537,
        base: 4,
        num_folds: 100,
        witness_length: 4,
        initial_bound: 16,
    };
    let mut rng = Xoshiro256PlusPlus::seed_from_u64(42);
    let results = simulate_trial(&config, &mut rng);

    assert_eq!(results.len(), 100);
    // After re-decomposition, digit norms should be bounded
    // Final digit linf should be < base (4) for all steps
    for step in &results {
        assert!(step.digit_linf < config.q,
            "digit linf {} exceeded q at step", step.digit_linf);
    }
}

#[test]
fn test_deterministic_with_same_seed() {
    let config = SimConfig {
        n: 64,
        q: 65537,
        base: 2,
        num_folds: 10,
        witness_length: 4,
        initial_bound: 16,
    };

    let mut rng1 = Xoshiro256PlusPlus::seed_from_u64(42);
    let r1 = simulate_trial(&config, &mut rng1);

    let mut rng2 = Xoshiro256PlusPlus::seed_from_u64(42);
    let r2 = simulate_trial(&config, &mut rng2);

    for (a, b) in r1.iter().zip(r2.iter()) {
        assert_eq!(a.l2, b.l2);
        assert_eq!(a.linf, b.linf);
    }
}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/Projects/nano-nova/rust && cargo test --test norm_sim_tests`
Expected: FAIL

- [ ] **Step 3: Implement norm_sim.rs**

```rust
// rust/src/norm_sim.rs
use rand::Rng;
use crate::ring::RingElement;
use crate::decompose::{decompose_element, decompose_vector, recompose_element, recompose_vector, num_digits};

pub struct SimConfig {
    pub n: usize,
    pub q: u64,
    pub base: u64,       // 0 = naive (no decomposition)
    pub num_folds: usize,
    pub witness_length: usize,
    pub initial_bound: u64,
}

pub struct FoldStep {
    pub l2: f64,
    pub linf: u64,
    pub digit_l2: f64,
    pub digit_linf: u64,
}

/// Compute L2 norm across a vector of ring elements.
fn vec_l2(elems: &[RingElement]) -> f64 {
    let sum_sq: f64 = elems.iter()
        .map(|e| {
            let n = e.l2_norm();
            n * n
        })
        .sum();
    sum_sq.sqrt()
}

/// Compute Linf norm across a vector of ring elements.
fn vec_linf(elems: &[RingElement]) -> u64 {
    elems.iter().map(|e| e.linf_norm()).max().unwrap_or(0)
}

/// Max L2 norm across digit vectors.
fn max_digit_l2(digit_vecs: &[Vec<RingElement>]) -> f64 {
    digit_vecs.iter().map(|dv| vec_l2(dv)).fold(0.0f64, f64::max)
}

/// Max Linf norm across digit vectors.
fn max_digit_linf(digit_vecs: &[Vec<RingElement>]) -> u64 {
    digit_vecs.iter().map(|dv| vec_linf(dv)).max().unwrap_or(0)
}

/// Random witness vector: `witness_length` ring elements with coefficients in [0, bound).
fn random_witness(n: usize, q: u64, length: usize, bound: u64, rng: &mut impl Rng) -> Vec<RingElement> {
    (0..length).map(|_| RingElement::random_short(n, q, bound, rng)).collect()
}

pub fn simulate_trial(config: &SimConfig, rng: &mut impl Rng) -> Vec<FoldStep> {
    let n = config.n;
    let q = config.q;
    let uses_decomp = config.base > 0;
    let nd = if uses_decomp { num_digits(q, config.base) } else { 1 };

    let mut w_acc = random_witness(n, q, config.witness_length, config.initial_bound, rng);

    let mut acc_digits = if uses_decomp {
        decompose_vector(&w_acc, config.base, nd)
    } else {
        vec![]
    };

    let mut results = Vec::with_capacity(config.num_folds);

    for _ in 0..config.num_folds {
        let w_fresh = random_witness(n, q, config.witness_length, config.initial_bound, rng);
        let r = RingElement::random_ternary(n, q, rng);

        if uses_decomp {
            let fresh_digits = decompose_vector(&w_fresh, config.base, nd);

            // Fold digit-by-digit: d_acc[k][j] + r * d_fresh[k][j]
            let inter_digits: Vec<Vec<RingElement>> = acc_digits.iter()
                .zip(fresh_digits.iter())
                .map(|(d_acc, d_fresh)| {
                    d_acc.iter().zip(d_fresh.iter())
                        .map(|(a, f)| a.add(&r.mul(f)))
                        .collect()
                })
                .collect();

            // Recompose
            let w_folded = recompose_vector(&inter_digits, config.base);

            // Record intermediate digit norms
            let digit_l2 = max_digit_l2(&inter_digits);
            let digit_linf = max_digit_linf(&inter_digits);

            // Re-decompose for next round
            acc_digits = decompose_vector(&w_folded, config.base, nd);
            w_acc = w_folded;

            results.push(FoldStep {
                l2: vec_l2(&w_acc),
                linf: vec_linf(&w_acc),
                digit_l2,
                digit_linf,
            });
        } else {
            // Naive: W' = W_acc + r * W_fresh
            w_acc = w_acc.iter().zip(w_fresh.iter())
                .map(|(a, f)| a.add(&r.mul(f)))
                .collect();

            let l2 = vec_l2(&w_acc);
            let linf = vec_linf(&w_acc);
            results.push(FoldStep {
                l2,
                linf,
                digit_l2: l2,
                digit_linf: linf,
            });
        }
    }

    results
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/Projects/nano-nova/rust && cargo test --test norm_sim_tests`
Expected: All 3 tests pass

- [ ] **Step 5: Commit**

```bash
cd ~/Projects/nano-nova && git add rust/src/norm_sim.rs rust/tests/norm_sim_tests.rs && git commit -m "feat(rust): single-trial LatticeFold folding simulation with norm tracking"
```

---

### Task 6: Monte Carlo Sweep with Streaming CSV

**Files:**
- Create: `rust/src/norm_sweep.rs`

- [ ] **Step 1: Implement norm_sweep.rs**

```rust
// rust/src/norm_sweep.rs
use std::fs::{self, File};
use std::io::{BufWriter, Write};
use std::path::PathBuf;
use std::time::Instant;

use rand::SeedableRng;
use rand_xoshiro::Xoshiro256PlusPlus;

use crate::norm_sim::{SimConfig, FoldStep, simulate_trial};

pub struct SweepConfig {
    pub ring_dims: Vec<usize>,
    pub moduli: Vec<u64>,
    pub bases: Vec<u64>,
    pub fold_counts: Vec<usize>,
    pub num_trials: usize,
    pub seed: u64,
    pub outdir: PathBuf,
}

struct ComboStats {
    l2_mean: f64,
    l2_std: f64,
    l2_median: f64,
    l2_p95: f64,
    l2_p99: f64,
    l2_max: f64,
    linf_mean: f64,
    linf_std: f64,
    linf_median: f64,
    linf_p95: f64,
    linf_p99: f64,
    linf_max: f64,
    log_growth_rate: f64,
    mean_l2_trajectory: Vec<f64>,
    mean_linf_trajectory: Vec<f64>,
    p99_l2_trajectory: Vec<f64>,
    p99_linf_trajectory: Vec<f64>,
}

fn percentile(sorted: &[f64], p: f64) -> f64 {
    if sorted.is_empty() { return 0.0; }
    let idx = (p / 100.0 * (sorted.len() - 1) as f64).round() as usize;
    sorted[idx.min(sorted.len() - 1)]
}

fn aggregate_trials(all_results: &[Vec<FoldStep>], num_folds: usize) -> ComboStats {
    let num_trials = all_results.len();

    // Final L2 norms
    let mut final_l2s: Vec<f64> = all_results.iter()
        .map(|r| r.last().unwrap().l2)
        .collect();
    final_l2s.sort_by(|a, b| a.partial_cmp(b).unwrap());

    let l2_mean = final_l2s.iter().sum::<f64>() / num_trials as f64;
    let l2_variance = final_l2s.iter().map(|&x| (x - l2_mean).powi(2)).sum::<f64>() / num_trials as f64;
    let l2_std = l2_variance.sqrt();

    // Final Linf norms
    let mut final_linfs: Vec<f64> = all_results.iter()
        .map(|r| r.last().unwrap().linf as f64)
        .collect();
    final_linfs.sort_by(|a, b| a.partial_cmp(b).unwrap());

    let linf_mean = final_linfs.iter().sum::<f64>() / num_trials as f64;
    let linf_variance = final_linfs.iter().map(|&x| (x - linf_mean).powi(2)).sum::<f64>() / num_trials as f64;
    let linf_std = linf_variance.sqrt();

    // Mean and p99 trajectories
    let mut mean_l2_traj = vec![0.0f64; num_folds];
    let mut mean_linf_traj = vec![0.0f64; num_folds];
    let mut p99_l2_traj = vec![0.0f64; num_folds];
    let mut p99_linf_traj = vec![0.0f64; num_folds];

    for step in 0..num_folds {
        let mut step_l2s: Vec<f64> = all_results.iter().map(|r| r[step].l2).collect();
        let mut step_linfs: Vec<f64> = all_results.iter().map(|r| r[step].linf as f64).collect();
        step_l2s.sort_by(|a, b| a.partial_cmp(b).unwrap());
        step_linfs.sort_by(|a, b| a.partial_cmp(b).unwrap());

        mean_l2_traj[step] = step_l2s.iter().sum::<f64>() / num_trials as f64;
        mean_linf_traj[step] = step_linfs.iter().sum::<f64>() / num_trials as f64;
        p99_l2_traj[step] = percentile(&step_l2s, 99.0);
        p99_linf_traj[step] = percentile(&step_linfs, 99.0);
    }

    // Log growth rate: fit log(l2[step]) = a*step + b via least squares
    let log_growth_rate = if num_folds > 1 {
        let n = num_folds as f64;
        let mut sum_x = 0.0f64;
        let mut sum_y = 0.0f64;
        let mut sum_xy = 0.0f64;
        let mut sum_xx = 0.0f64;
        for (i, &y_val) in mean_l2_traj.iter().enumerate() {
            let x = (i + 1) as f64;
            let y = (y_val + 1e-10).ln();
            sum_x += x;
            sum_y += y;
            sum_xy += x * y;
            sum_xx += x * x;
        }
        (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x)
    } else {
        0.0
    };

    ComboStats {
        l2_mean,
        l2_std,
        l2_median: percentile(&final_l2s, 50.0),
        l2_p95: percentile(&final_l2s, 95.0),
        l2_p99: percentile(&final_l2s, 99.0),
        l2_max: *final_l2s.last().unwrap_or(&0.0),
        linf_mean,
        linf_std,
        linf_median: percentile(&final_linfs, 50.0),
        linf_p95: percentile(&final_linfs, 95.0),
        linf_p99: percentile(&final_linfs, 99.0),
        linf_max: *final_linfs.last().unwrap_or(&0.0),
        log_growth_rate,
        mean_l2_trajectory: mean_l2_traj,
        mean_linf_trajectory: mean_linf_traj,
        p99_l2_trajectory: p99_l2_traj,
        p99_linf_trajectory: p99_linf_traj,
    }
}

pub fn run_sweep(config: &SweepConfig) {
    // Create output directories
    let traj_dir = config.outdir.join("trajectories");
    fs::create_dir_all(&traj_dir).expect("failed to create trajectories dir");

    // Open summary CSV with immediate flushing
    let summary_path = config.outdir.join("summary.csv");
    let summary_file = File::create(&summary_path).expect("failed to create summary.csv");
    let mut summary = BufWriter::new(summary_file);
    writeln!(summary,
        "n,q,base,num_folds,trials,l2_mean,l2_std,l2_median,l2_p95,l2_p99,l2_max,\
         linf_mean,linf_std,linf_median,linf_p95,linf_p99,linf_max,log_growth_rate,elapsed_secs"
    ).unwrap();
    summary.flush().unwrap();

    // Build parameter grid
    let mut combos: Vec<(usize, u64, u64, usize)> = Vec::new();
    for &n in &config.ring_dims {
        for &q in &config.moduli {
            for &base in &config.bases {
                for &folds in &config.fold_counts {
                    combos.push((n, q, base, folds));
                }
            }
        }
    }

    let total = combos.len();
    let sweep_start = Instant::now();

    for (idx, &(n, q, base, num_folds)) in combos.iter().enumerate() {
        let combo_start = Instant::now();

        let sim_config = SimConfig {
            n,
            q,
            base,
            num_folds,
            witness_length: 4,
            initial_bound: 16,
        };

        // Run all trials
        let mut all_results: Vec<Vec<FoldStep>> = Vec::with_capacity(config.num_trials);
        for trial in 0..config.num_trials {
            let seed = config.seed.wrapping_add(trial as u64 * 1000);
            let mut rng = Xoshiro256PlusPlus::seed_from_u64(seed);
            let results = simulate_trial(&sim_config, &mut rng);
            all_results.push(results);
        }

        // Aggregate statistics
        let stats = aggregate_trials(&all_results, num_folds);
        let elapsed = combo_start.elapsed().as_secs_f64();

        // Append to summary CSV (flush immediately)
        writeln!(summary,
            "{},{},{},{},{},{:.6},{:.6},{:.6},{:.6},{:.6},{:.6},\
             {:.6},{:.6},{:.6},{:.6},{:.6},{:.6},{:.8},{:.1}",
            n, q, base, num_folds, config.num_trials,
            stats.l2_mean, stats.l2_std, stats.l2_median,
            stats.l2_p95, stats.l2_p99, stats.l2_max,
            stats.linf_mean, stats.linf_std, stats.linf_median,
            stats.linf_p95, stats.linf_p99, stats.linf_max,
            stats.log_growth_rate, elapsed,
        ).unwrap();
        summary.flush().unwrap();

        // Write trajectory CSV
        let traj_path = traj_dir.join(format!("{}_{}_{}_{}.csv", n, q, base, num_folds));
        let mut traj_file = BufWriter::new(File::create(&traj_path).unwrap());
        writeln!(traj_file, "fold_step,l2_mean,l2_p99,linf_mean,linf_p99").unwrap();
        for step in 0..num_folds {
            writeln!(traj_file, "{},{:.6},{:.6},{:.6},{:.6}",
                step + 1,
                stats.mean_l2_trajectory[step],
                stats.p99_l2_trajectory[step],
                stats.mean_linf_trajectory[step],
                stats.p99_linf_trajectory[step],
            ).unwrap();
        }

        // Progress to stderr with ETA
        let elapsed_total = sweep_start.elapsed().as_secs_f64();
        let avg_per_combo = elapsed_total / (idx + 1) as f64;
        let remaining = avg_per_combo * (total - idx - 1) as f64;
        let remaining_h = remaining / 3600.0;
        let strategy = if base == 0 { "naive".to_string() } else { format!("B={}", base) };
        eprintln!(
            "[{}/{}] n={} q={} {} folds={}: {:.1}s (est {:.1}h remaining)",
            idx + 1, total, n, q, strategy, num_folds, elapsed, remaining_h,
        );
    }

    eprintln!("Done! Results in {}", config.outdir.display());
}
```

- [ ] **Step 2: Verify it compiles**

Run: `cd ~/Projects/nano-nova/rust && cargo build`
Expected: Compiles

- [ ] **Step 3: Commit**

```bash
cd ~/Projects/nano-nova && git add rust/src/norm_sweep.rs && git commit -m "feat(rust): Monte Carlo sweep driver with streaming CSV output"
```

---

### Task 7: CLI bench-norm Subcommand

**Files:**
- Modify: `rust/src/bin/nano_nova.rs`

- [ ] **Step 1: Add bench-norm subcommand**

Add to the `Commands` enum in `rust/src/bin/nano_nova.rs`:

```rust
    /// Run LatticeFold norm growth parameter sweep
    BenchNorm {
        #[arg(long, default_value = "64,128,256,512")]
        ring_dims: String,
        #[arg(long, default_value = "65537,4294967296,18446744073709551616")]
        moduli: String,
        #[arg(long, default_value = "0,2,4,8,16")]
        bases: String,
        #[arg(long, default_value = "100,500,1000")]
        folds: String,
        #[arg(long, default_value_t = 1000)]
        trials: usize,
        #[arg(long, default_value_t = 42)]
        seed: u64,
        #[arg(long, default_value = "results/norm_growth")]
        outdir: String,
    },
```

Add the match arm in `main()`:

```rust
        Commands::BenchNorm {
            ring_dims,
            moduli,
            bases,
            folds,
            trials,
            seed,
            outdir,
        } => {
            let ring_dims: Vec<usize> = ring_dims.split(',')
                .map(|s| s.trim().parse().expect("invalid ring dim"))
                .collect();
            let moduli: Vec<u64> = moduli.split(',')
                .map(|s| s.trim().parse().expect("invalid modulus"))
                .collect();
            let bases: Vec<u64> = bases.split(',')
                .map(|s| s.trim().parse().expect("invalid base"))
                .collect();
            let fold_counts: Vec<usize> = folds.split(',')
                .map(|s| s.trim().parse().expect("invalid fold count"))
                .collect();

            let config = nano_nova::norm_sweep::SweepConfig {
                ring_dims,
                moduli,
                bases,
                fold_counts,
                num_trials: trials,
                seed,
                outdir: std::path::PathBuf::from(outdir),
            };

            nano_nova::norm_sweep::run_sweep(&config);
        }
```

Add the necessary import at the top of the file (no new `use` needed — accessed via `nano_nova::norm_sweep`).

- [ ] **Step 2: Test with a small sweep**

Run: `cd ~/Projects/nano-nova/rust && cargo run --release -- bench-norm --ring-dims 64 --moduli 65537 --bases 0,2 --folds 10 --trials 5 --outdir /tmp/test_norm`
Expected: Runs in a few seconds, creates `/tmp/test_norm/summary.csv` and `/tmp/test_norm/trajectories/` with CSV files. Progress printed to stderr.

- [ ] **Step 3: Verify CSV output**

Run: `cat /tmp/test_norm/summary.csv`
Expected: Header row + 2 data rows (2 bases × 1 ring_dim × 1 modulus × 1 fold_count). All numeric values present.

Run: `ls /tmp/test_norm/trajectories/`
Expected: `64_65537_0_10.csv` and `64_65537_2_10.csv`

Run: `head -5 /tmp/test_norm/trajectories/64_65537_2_10.csv`
Expected: Header + 4 data rows with fold_step, l2_mean, l2_p99, linf_mean, linf_p99

- [ ] **Step 4: Commit**

```bash
cd ~/Projects/nano-nova && git add rust/src/bin/nano_nova.rs && git commit -m "feat(rust): bench-norm CLI subcommand for parameter sweeps"
```

---

### Task 8: Cross-Validation with Python

**Files:**
- Create: `rust/tests/norm_cross_validation.rs`

- [ ] **Step 1: Generate Python reference values**

Run:

```bash
cd ~/Projects/nano-nova && uv run python -c "
import numpy as np
np.random.seed(42)
from experiments.norm_growth.ring_arithmetic import RingParams, RingElement, RingVector
from experiments.norm_growth.decompose import decompose_element, recompose_element, num_digits_for_params

params = RingParams(n=4, q=17)

# Test ring mul: (1 + X) * (2 + 3X) mod (X^4+1) mod 17
a = RingElement(np.array([1, 1, 0, 0], dtype=np.int64), params)
b = RingElement(np.array([2, 3, 0, 0], dtype=np.int64), params)
c = a * b
print(f'ring_mul: {list(c.coeffs)}')

# Test decompose/recompose: 13 in base 4 with q=17, n=4
elem = RingElement(np.array([13, 7, 16, 0], dtype=np.int64), params)
nd = num_digits_for_params(params, 4)
digits = decompose_element(elem, 4, nd)
print(f'num_digits(17, 4) = {nd}')
for i, d in enumerate(digits):
    print(f'  digit[{i}] = {list(d.coeffs)}')
recomp = recompose_element(digits, 4)
print(f'recomposed: {list(recomp.coeffs)}')

# Test norms
e = RingElement(np.array([3, 14, 0, 8], dtype=np.int64), params)
print(f'l2_norm = {e.l2_norm():.10f}')
print(f'linf_norm = {e.linf_norm()}')
print(f'centered = {list(e.centered_coeffs())}')
"
```

Record the output and write assertions.

- [ ] **Step 2: Write cross-validation test**

```rust
// rust/tests/norm_cross_validation.rs
use nano_nova::ring::RingElement;
use nano_nova::decompose::{decompose_element, recompose_element, num_digits};

#[test]
fn test_ring_mul_matches_python() {
    // (1 + X) * (2 + 3X) in Z_17[X]/(X^4+1)
    let a = RingElement::from_coeffs(&[1, 1, 0, 0], 4, 17);
    let b = RingElement::from_coeffs(&[2, 3, 0, 0], 4, 17);
    let c = a.mul(&b);
    // FILL IN from Python output
    // Expected: [2, 5, 3, 0] — (1*2=2, 1*3+1*2=5, 1*3=3, 0)
    // Verify against Python output and update if different
    let py_result = c.coeffs(); // compare with Python output
    assert_eq!(py_result.len(), 4);
    // The implementer MUST run the Python script and fill in exact values
}

#[test]
fn test_decompose_matches_python() {
    let elem = RingElement::from_coeffs(&[13, 7, 16, 0], 4, 17);
    let nd = num_digits(17, 4);
    let digits = decompose_element(&elem, 4, nd);
    let recomp = recompose_element(&digits, 4);
    assert_eq!(recomp.coeffs(), elem.coeffs());
    // FILL IN digit values from Python output
}

#[test]
fn test_norms_match_python() {
    let e = RingElement::from_coeffs(&[3, 14, 0, 8], 4, 17);
    // centered: [3, -3, 0, 8] (14 > 17/2=8, so 14-17=-3; 8 <= 8 so 8)
    // Wait: 8 <= 8 (q/2 = 8), so 8 stays as 8. But |8| in centered rep...
    // Actually for q=17, q/2=8. If c <= 8, centered = c. If c > 8, centered = c-17.
    // So: 3->3, 14->14-17=-3, 0->0, 8->8
    // l2 = sqrt(9+9+0+64) = sqrt(82)
    // linf = max(3, 3, 0, 8) = 8
    let l2 = e.l2_norm();
    let linf = e.linf_norm();
    // FILL IN exact value from Python output
    assert!((l2 - 82.0f64.sqrt()).abs() < 1e-6);
    assert_eq!(linf, 8);
}
```

**Important:** The implementer MUST run the Python script first and fill in the exact values. The comments show expected values but Python output is authoritative.

- [ ] **Step 3: Run test**

Run: `cd ~/Projects/nano-nova/rust && cargo test --test norm_cross_validation`
Expected: All tests pass

- [ ] **Step 4: Commit**

```bash
cd ~/Projects/nano-nova && git add rust/tests/norm_cross_validation.rs && git commit -m "test(rust): cross-validation of ring arithmetic against Python"
```

---

### Task 9: Final Verification and Release Build

**Files:**
- None new

- [ ] **Step 1: Run full test suite**

Run: `cd ~/Projects/nano-nova/rust && cargo test`
Expected: All tests pass (33 existing + ~20 new ≈ 53 tests)

- [ ] **Step 2: Run clippy**

Run: `cd ~/Projects/nano-nova/rust && cargo clippy -- -D warnings`
Expected: Clean

- [ ] **Step 3: Fix any clippy warnings**

Apply fixes as needed.

- [ ] **Step 4: Test release build with a medium sweep**

Run: `cd ~/Projects/nano-nova/rust && cargo run --release -- bench-norm --ring-dims 64,128 --moduli 65537 --bases 0,2,4 --folds 100 --trials 100 --outdir ~/Projects/nano-nova/results/norm_growth_test`
Expected: Completes in under a minute, produces summary.csv with 6 rows and trajectory CSVs.

- [ ] **Step 5: Verify CSV is well-formed**

Run: `cd ~/Projects/nano-nova && head -3 results/norm_growth_test/summary.csv`
Expected: Header + 2 data rows, all columns numeric

- [ ] **Step 6: Commit everything**

```bash
cd ~/Projects/nano-nova && git add rust/ results/ && git commit -m "feat(rust): complete LatticeFold norm growth parameter sweep"
```

---

### Task Summary

| Task | Module | Tests | Description |
|------|--------|-------|-------------|
| 1 | stubs | 0 | Dependencies, module stubs |
| 2 | ring.rs | 9 | RingElement basics + schoolbook mul |
| 3 | ring.rs | 5 | Karatsuba negacyclic multiplication |
| 4 | decompose.rs | 4 | Base-B decomposition/recomposition |
| 5 | norm_sim.rs | 3 | Single-trial folding simulation |
| 6 | norm_sweep.rs | 0 | Monte Carlo sweep + streaming CSV |
| 7 | CLI | manual | bench-norm subcommand |
| 8 | cross-validation | 3 | Python reference value comparison |
| 9 | cleanup | 0 | Clippy, release build, verification |
