use std::time::Instant;

use clap::{Parser, Subcommand};
use nano_nova::commitment::ToyCommitment;
use nano_nova::examples::{fibonacci_circuit, fibonacci_step, fibonacci_witness};
use nano_nova::field::{Field, Fp61};
use nano_nova::ivc::{ivc_prove, ivc_verify, IVCProof};
use nano_nova::matrix::DenseMatrix;
use nano_nova::r1cs::R1CSShape;

#[derive(Parser)]
#[command(name = "nano-nova", about = "Educational Nova folding scheme")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Prove IVC and print timing
    Prove {
        #[arg(long, default_value = "fibonacci")]
        circuit: String,
        #[arg(long, default_value_t = 100)]
        steps: usize,
    },
    /// Run LatticeFold norm growth parameter sweep
    BenchNorm {
        #[arg(long, default_value = "64,128,256,512")]
        ring_dims: String,
        #[arg(long, default_value = "65537,4294967296")]
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
    /// Run benchmark sweep and output CSV
    Bench {
        #[arg(long, default_value = "fibonacci")]
        circuit: String,
        /// Comma-separated step counts
        #[arg(long, default_value = "10,100,1000")]
        steps: String,
        #[arg(long, default_value_t = 10)]
        trials: usize,
        #[arg(long, default_value = "results.csv")]
        output: String,
    },
}

/// Run IVC prove + verify, returning the proof and timing in microseconds.
fn run_prove_verify(
    shape: &R1CSShape<Fp61, DenseMatrix<Fp61>>,
    z0: &[Fp61],
    steps: usize,
) -> (IVCProof<Fp61, ToyCommitment>, u128, u128) {
    let prove_start = Instant::now();
    let proof = ivc_prove::<Fp61, DenseMatrix<Fp61>, ToyCommitment>(
        shape,
        fibonacci_step,
        fibonacci_witness,
        z0,
        steps,
    );
    let prove_us = prove_start.elapsed().as_micros();

    let verify_start = Instant::now();
    let _valid = ivc_verify(shape, &proof);
    let verify_us = verify_start.elapsed().as_micros();

    (proof, prove_us, verify_us)
}

fn main() {
    let cli = Cli::parse();

    match cli.command {
        Commands::Prove { circuit, steps } => {
            assert_eq!(circuit, "fibonacci", "only fibonacci circuit supported");

            let shape = fibonacci_circuit::<Fp61>();
            let z0 = vec![Fp61::from_u64(1), Fp61::from_u64(1)];

            let (_proof, prove_us, verify_us) = run_prove_verify(&shape, &z0, steps);

            println!("Circuit:     {}", circuit);
            println!("Steps:       {}", steps);
            println!("Prove time:  {} us", prove_us);
            println!("Verify time: {} us", verify_us);
            println!("Valid:       true");
        }
        Commands::BenchNorm {
            ring_dims,
            moduli,
            bases,
            folds,
            trials,
            seed,
            outdir,
        } => {
            let ring_dims: Vec<usize> = ring_dims
                .split(',')
                .map(|s| s.trim().parse().expect("invalid ring dim"))
                .collect();
            let moduli: Vec<u64> = moduli
                .split(',')
                .map(|s| s.trim().parse().expect("invalid modulus"))
                .collect();
            let bases: Vec<u64> = bases
                .split(',')
                .map(|s| s.trim().parse().expect("invalid base"))
                .collect();
            let fold_counts: Vec<usize> = folds
                .split(',')
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
        Commands::Bench {
            circuit,
            steps,
            trials,
            output,
        } => {
            assert_eq!(circuit, "fibonacci", "only fibonacci circuit supported");

            let step_counts: Vec<usize> = steps
                .split(',')
                .map(|s| s.trim().parse().expect("invalid step count"))
                .collect();

            let shape = fibonacci_circuit::<Fp61>();
            let z0 = vec![Fp61::from_u64(1), Fp61::from_u64(1)];

            let mut csv = String::from("circuit,steps,trial,prove_time_us,verify_time_us\n");

            for &step_count in &step_counts {
                for trial in 1..=trials {
                    let (_proof, prove_us, verify_us) =
                        run_prove_verify(&shape, &z0, step_count);

                    csv.push_str(&format!(
                        "{},{},{},{},{}\n",
                        circuit, step_count, trial, prove_us, verify_us
                    ));

                    if trial == 1 {
                        eprintln!(
                            "{} steps, trial 1/{}: {} us prove",
                            step_count, trials, prove_us
                        );
                    }
                }
            }

            std::fs::write(&output, &csv).expect("failed to write CSV");
            eprintln!("Results written to {}", output);
        }
    }
}
