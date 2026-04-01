use std::fs::{self, File};
use std::io::{BufWriter, Write};
use std::path::PathBuf;
use std::time::Instant;

use rand::SeedableRng;
use rand_xoshiro::Xoshiro256PlusPlus;

use crate::norm_sim::{FoldStep, SimConfig, simulate_trial};

pub struct SweepConfig {
    pub ring_dims: Vec<usize>,
    pub moduli: Vec<u64>,
    pub bases: Vec<u64>,
    pub fold_counts: Vec<usize>,
    pub num_trials: usize,
    pub seed: u64,
    pub outdir: PathBuf,
}

fn percentile(sorted: &[f64], p: f64) -> f64 {
    if sorted.is_empty() {
        return 0.0;
    }
    let idx = (p / 100.0 * (sorted.len() - 1) as f64).round() as usize;
    sorted[idx.min(sorted.len() - 1)]
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

fn aggregate_trials(all_results: &[Vec<FoldStep>], num_folds: usize) -> ComboStats {
    let num_trials = all_results.len();

    let mut final_l2s: Vec<f64> = all_results
        .iter()
        .map(|r| r.last().unwrap().l2)
        .collect();
    final_l2s.sort_by(|a, b| a.partial_cmp(b).unwrap());

    let l2_mean = final_l2s.iter().sum::<f64>() / num_trials as f64;
    let l2_variance =
        final_l2s.iter().map(|&x| (x - l2_mean).powi(2)).sum::<f64>() / num_trials as f64;

    let mut final_linfs: Vec<f64> = all_results
        .iter()
        .map(|r| r.last().unwrap().linf as f64)
        .collect();
    final_linfs.sort_by(|a, b| a.partial_cmp(b).unwrap());

    let linf_mean = final_linfs.iter().sum::<f64>() / num_trials as f64;
    let linf_variance =
        final_linfs.iter().map(|&x| (x - linf_mean).powi(2)).sum::<f64>() / num_trials as f64;

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
        l2_std: l2_variance.sqrt(),
        l2_median: percentile(&final_l2s, 50.0),
        l2_p95: percentile(&final_l2s, 95.0),
        l2_p99: percentile(&final_l2s, 99.0),
        l2_max: *final_l2s.last().unwrap_or(&0.0),
        linf_mean,
        linf_std: linf_variance.sqrt(),
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
    let traj_dir = config.outdir.join("trajectories");
    fs::create_dir_all(&traj_dir).expect("failed to create trajectories dir");

    let summary_path = config.outdir.join("summary.csv");
    let summary_file = File::create(&summary_path).expect("failed to create summary.csv");
    let mut summary = BufWriter::new(summary_file);
    writeln!(
        summary,
        "n,q,base,num_folds,trials,l2_mean,l2_std,l2_median,l2_p95,l2_p99,l2_max,\
         linf_mean,linf_std,linf_median,linf_p95,linf_p99,linf_max,log_growth_rate,elapsed_secs"
    )
    .unwrap();
    summary.flush().unwrap();

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

        let mut all_results: Vec<Vec<FoldStep>> = Vec::with_capacity(config.num_trials);
        for trial in 0..config.num_trials {
            let seed = config.seed.wrapping_add(trial as u64 * 1000);
            let mut rng = Xoshiro256PlusPlus::seed_from_u64(seed);
            let results = simulate_trial(&sim_config, &mut rng);
            all_results.push(results);
        }

        let stats = aggregate_trials(&all_results, num_folds);
        let elapsed = combo_start.elapsed().as_secs_f64();

        writeln!(
            summary,
            "{},{},{},{},{},{:.6},{:.6},{:.6},{:.6},{:.6},{:.6},\
             {:.6},{:.6},{:.6},{:.6},{:.6},{:.6},{:.8},{:.1}",
            n,
            q,
            base,
            num_folds,
            config.num_trials,
            stats.l2_mean,
            stats.l2_std,
            stats.l2_median,
            stats.l2_p95,
            stats.l2_p99,
            stats.l2_max,
            stats.linf_mean,
            stats.linf_std,
            stats.linf_median,
            stats.linf_p95,
            stats.linf_p99,
            stats.linf_max,
            stats.log_growth_rate,
            elapsed,
        )
        .unwrap();
        summary.flush().unwrap();

        let traj_path = traj_dir.join(format!("{}_{}_{}_{}.csv", n, q, base, num_folds));
        let mut traj_file = BufWriter::new(File::create(&traj_path).unwrap());
        writeln!(traj_file, "fold_step,l2_mean,l2_p99,linf_mean,linf_p99").unwrap();
        for step in 0..num_folds {
            writeln!(
                traj_file,
                "{},{:.6},{:.6},{:.6},{:.6}",
                step + 1,
                stats.mean_l2_trajectory[step],
                stats.p99_l2_trajectory[step],
                stats.mean_linf_trajectory[step],
                stats.p99_linf_trajectory[step],
            )
            .unwrap();
        }

        let elapsed_total = sweep_start.elapsed().as_secs_f64();
        let avg_per_combo = elapsed_total / (idx + 1) as f64;
        let remaining = avg_per_combo * (total - idx - 1) as f64;
        let remaining_h = remaining / 3600.0;
        let strategy = if base == 0 {
            "naive".to_string()
        } else {
            format!("B={}", base)
        };
        eprintln!(
            "[{}/{}] n={} q={} {} folds={}: {:.1}s (est {:.1}h remaining)",
            idx + 1,
            total,
            n,
            q,
            strategy,
            num_folds,
            elapsed,
            remaining_h,
        );
    }

    eprintln!("Done! Results in {}", config.outdir.display());
}
