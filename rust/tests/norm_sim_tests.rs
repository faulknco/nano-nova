use nano_nova::norm_sim::{SimConfig, simulate_trial};
use rand::SeedableRng;
use rand_xoshiro::Xoshiro256PlusPlus;

#[test]
fn test_naive_fold_norms_grow() {
    let config = SimConfig {
        n: 64,
        q: 65537,
        base: 0,
        num_folds: 100,
        witness_length: 4,
        initial_bound: 16,
    };
    let mut rng = Xoshiro256PlusPlus::seed_from_u64(42);
    let results = simulate_trial(&config, &mut rng);
    assert_eq!(results.len(), 100);
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
