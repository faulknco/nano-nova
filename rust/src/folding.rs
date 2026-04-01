use crate::commitment::CommitmentScheme;
use crate::field::Field;
use crate::matrix::MatrixOps;
use crate::r1cs::{R1CSShape, RelaxedR1CSInstance, RelaxedR1CSWitness};
use sha2::{Digest, Sha256};

/// Compute cross-term T = Az1.Bz2 + Az2.Bz1 - u1*Cz2 - u2*Cz1.
pub fn compute_cross_term<F: Field, M: MatrixOps<F>, C: CommitmentScheme<F>>(
    shape: &R1CSShape<F, M>,
    inst1: &RelaxedR1CSInstance<F, C>,
    wit1: &RelaxedR1CSWitness<F>,
    inst2: &RelaxedR1CSInstance<F, C>,
    wit2: &RelaxedR1CSWitness<F>,
) -> Vec<F> {
    let z1 = shape.make_relaxed_z(inst1.u, &inst1.x, &wit1.w);
    let z2 = shape.make_relaxed_z(inst2.u, &inst2.x, &wit2.w);

    let az1 = shape.a.mul_vec(&z1);
    let bz1 = shape.b.mul_vec(&z1);
    let az2 = shape.a.mul_vec(&z2);
    let bz2 = shape.b.mul_vec(&z2);
    let cz1 = shape.c.mul_vec(&z1);
    let cz2 = shape.c.mul_vec(&z2);

    (0..shape.m)
        .map(|i| {
            az1[i]
                .mul(bz2[i])
                .add(az2[i].mul(bz1[i]))
                .sub(inst1.u.mul(cz2[i]))
                .sub(inst2.u.mul(cz1[i]))
        })
        .collect()
}

/// Derive Fiat-Shamir challenge from transcript.
///
/// Transcript: com_T || x1 || x2 || u1 (8 bytes BE) || u2 (8 bytes BE) || com_W1 || com_W2
pub fn fiat_shamir_challenge<F: Field, C: CommitmentScheme<F>>(
    com_t: &C,
    inst1: &RelaxedR1CSInstance<F, C>,
    inst2: &RelaxedR1CSInstance<F, C>,
) -> F {
    let mut hasher = Sha256::new();
    hasher.update(com_t.value());
    for elem in &inst1.x {
        hasher.update(elem.to_bytes());
    }
    for elem in &inst2.x {
        hasher.update(elem.to_bytes());
    }
    hasher.update(inst1.u.to_bytes());
    hasher.update(inst2.u.to_bytes());
    hasher.update(inst1.com_w.value());
    hasher.update(inst2.com_w.value());

    let hash = hasher.finalize();
    let r_bytes: [u8; 8] = hash[..8].try_into().unwrap();
    let r_int = u64::from_be_bytes(r_bytes);
    F::from_u64(r_int)
}

/// Fold two Relaxed R1CS instances into one.
pub fn fold<F: Field, M: MatrixOps<F>, C: CommitmentScheme<F>>(
    shape: &R1CSShape<F, M>,
    inst1: &RelaxedR1CSInstance<F, C>,
    wit1: &RelaxedR1CSWitness<F>,
    inst2: &RelaxedR1CSInstance<F, C>,
    wit2: &RelaxedR1CSWitness<F>,
) -> (RelaxedR1CSInstance<F, C>, RelaxedR1CSWitness<F>) {
    // Step 1: Cross-term
    let t = compute_cross_term(shape, inst1, wit1, inst2, wit2);

    // Step 2: Commit to T
    let com_t = C::commit(&t);

    // Step 3: Challenge
    let r = fiat_shamir_challenge(&com_t, inst1, inst2);
    let r_sq = r.mul(r);

    // Step 4: Fold
    // E' = E1 + r*T + r^2*E2
    let e_folded: Vec<F> = (0..shape.m)
        .map(|i| wit1.e[i].add(r.mul(t[i])).add(r_sq.mul(wit2.e[i])))
        .collect();

    // u' = u1 + r*u2
    let u_folded = inst1.u.add(r.mul(inst2.u));

    // x' = x1 + r*x2
    let x_folded: Vec<F> = inst1
        .x
        .iter()
        .zip(inst2.x.iter())
        .map(|(&a, &b)| a.add(r.mul(b)))
        .collect();

    // W' = W1 + r*W2
    let w_folded: Vec<F> = wit1
        .w
        .iter()
        .zip(wit2.w.iter())
        .map(|(&a, &b)| a.add(r.mul(b)))
        .collect();

    let com_e_folded = C::commit(&e_folded);
    let com_w_folded = C::commit(&w_folded);

    let folded_instance = RelaxedR1CSInstance {
        com_e: com_e_folded,
        u: u_folded,
        x: x_folded,
        com_w: com_w_folded,
    };
    let folded_witness = RelaxedR1CSWitness {
        e: e_folded,
        w: w_folded,
    };

    (folded_instance, folded_witness)
}
