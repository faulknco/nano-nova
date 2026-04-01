use rand::Rng;
use crate::ring::RingElement;
use crate::decompose::{decompose_vector, recompose_vector, num_digits};

/// Configuration for a single folding simulation trial.
pub struct SimConfig {
    /// Ring dimension (must be a power of 2).
    pub n: usize,
    /// Modulus.
    pub q: u64,
    /// Decomposition base. 0 means naive folding (no decomposition).
    pub base: u64,
    /// Number of fold steps to simulate.
    pub num_folds: usize,
    /// Number of ring elements in the witness vector.
    pub witness_length: usize,
    /// Initial witness coefficients are drawn from [0, initial_bound).
    pub initial_bound: u64,
}

/// Norms recorded at a single fold step.
pub struct FoldStep {
    /// L2 norm of the accumulated witness vector (after recomposition if decomposed).
    pub l2: f64,
    /// L-infinity norm of the accumulated witness vector.
    pub linf: u64,
    /// Max L2 norm across digit vectors (same as l2 for naive mode).
    pub digit_l2: f64,
    /// Max L-infinity norm across digit vectors (same as linf for naive mode).
    pub digit_linf: u64,
}

// ── Helper functions ──────────────────────────────────────────────────────────

/// L2 norm of a vector of ring elements: sqrt(sum of l2^2).
fn vec_l2(elems: &[RingElement]) -> f64 {
    let sum_sq: f64 = elems.iter().map(|e| { let l = e.l2_norm(); l * l }).sum();
    sum_sq.sqrt()
}

/// L-infinity norm of a vector of ring elements: max individual linf.
fn vec_linf(elems: &[RingElement]) -> u64 {
    elems.iter().map(|e| e.linf_norm()).max().unwrap_or(0)
}

/// Max L2 norm across a slice of digit vectors.
fn max_digit_l2(digit_vecs: &[Vec<RingElement>]) -> f64 {
    digit_vecs.iter().map(|dv| vec_l2(dv)).fold(0.0f64, f64::max)
}

/// Max L-infinity norm across a slice of digit vectors.
fn max_digit_linf(digit_vecs: &[Vec<RingElement>]) -> u64 {
    digit_vecs.iter().map(|dv| vec_linf(dv)).max().unwrap_or(0)
}

/// Sample a random witness: `length` RingElements with coefficients in [0, bound).
fn random_witness<R: Rng>(n: usize, q: u64, length: usize, bound: u64, rng: &mut R) -> Vec<RingElement> {
    (0..length)
        .map(|_| RingElement::random_short(n, q, bound, rng))
        .collect()
}

// ── Main simulation ───────────────────────────────────────────────────────────

/// Run a single simulation trial, returning one `FoldStep` per fold.
///
/// - If `config.base == 0`: naive folding — accumulate the witness directly.
/// - If `config.base > 0`: decompose-then-fold — fold digit vectors, then
///   recompose to measure algebraic norms and re-decompose for the next step.
pub fn simulate_trial<R: Rng>(config: &SimConfig, rng: &mut R) -> Vec<FoldStep> {
    let n = config.n;
    let q = config.q;
    let base = config.base;
    let length = config.witness_length;
    let bound = config.initial_bound;

    let mut steps = Vec::with_capacity(config.num_folds);

    if base == 0 {
        // ── Naive folding ─────────────────────────────────────────────────────
        let mut w_acc = random_witness(n, q, length, bound, rng);

        for _ in 0..config.num_folds {
            let w_fresh = random_witness(n, q, length, bound, rng);
            let r = RingElement::random_ternary(n, q, rng);

            // w_acc[j] = w_acc[j] + r * w_fresh[j]
            w_acc = w_acc
                .iter()
                .zip(w_fresh.iter())
                .map(|(acc, fresh)| acc.add(&r.mul(fresh)))
                .collect();

            let l2 = vec_l2(&w_acc);
            let linf = vec_linf(&w_acc);
            steps.push(FoldStep {
                l2,
                linf,
                digit_l2: l2,
                digit_linf: linf,
            });
        }
    } else {
        // ── Decompose-then-fold ───────────────────────────────────────────────
        let nd = num_digits(q, base);
        let w_acc_init = random_witness(n, q, length, bound, rng);
        let mut d_acc = decompose_vector(&w_acc_init, base, nd);

        for _ in 0..config.num_folds {
            let w_fresh = random_witness(n, q, length, bound, rng);
            let d_fresh = decompose_vector(&w_fresh, base, nd);
            let r = RingElement::random_ternary(n, q, rng);

            // Fold digit-by-digit: d_acc[k][j] = d_acc[k][j] + r * d_fresh[k][j]
            d_acc = d_acc
                .iter()
                .zip(d_fresh.iter())
                .map(|(acc_vec, fresh_vec)| {
                    acc_vec
                        .iter()
                        .zip(fresh_vec.iter())
                        .map(|(acc, fresh)| acc.add(&r.mul(fresh)))
                        .collect::<Vec<_>>()
                })
                .collect();

            // Record digit-level norms before recomposition
            let d_l2 = max_digit_l2(&d_acc);
            let d_linf = max_digit_linf(&d_acc);

            // Recompose to get the algebraic witness, measure its norms
            let w_recomposed = recompose_vector(&d_acc, base);
            let l2 = vec_l2(&w_recomposed);
            let linf = vec_linf(&w_recomposed);

            // Re-decompose the recomposed witness for the next step
            d_acc = decompose_vector(&w_recomposed, base, nd);

            steps.push(FoldStep {
                l2,
                linf,
                digit_l2: d_l2,
                digit_linf: d_linf,
            });
        }
    }

    steps
}
