use crate::commitment::CommitmentScheme;
use crate::field::Field;
use crate::folding::fold;
use crate::matrix::MatrixOps;
use crate::r1cs::{r1cs_to_relaxed, trivial_relaxed, R1CSShape, RelaxedR1CSInstance, RelaxedR1CSWitness};

/// The output of an IVC computation.
pub struct IVCProof<F: Field, C: CommitmentScheme<F>> {
    pub instance: RelaxedR1CSInstance<F, C>,
    pub witness: RelaxedR1CSWitness<F>,
    pub z_current: Vec<F>,
    pub num_steps: usize,
}

/// Run IVC for num_steps applications of step_fn.
pub fn ivc_prove<F: Field, M: MatrixOps<F>, C: CommitmentScheme<F>>(
    shape: &R1CSShape<F, M>,
    step_fn: fn(&[F]) -> Vec<F>,
    witness_fn: fn(&[F]) -> Vec<F>,
    z0: &[F],
    num_steps: usize,
) -> IVCProof<F, C> {
    let (mut acc_inst, mut acc_wit) = trivial_relaxed::<F, M, C>(shape);
    let mut z_current = z0.to_vec();

    for i in 0..num_steps {
        let z_next = step_fn(&z_current);
        let w_i = witness_fn(&z_current);

        let mut x_i = Vec::with_capacity(z_current.len() + z_next.len());
        x_i.extend_from_slice(&z_current);
        x_i.extend_from_slice(&z_next);

        debug_assert!(
            shape.is_satisfied(&x_i, &w_i),
            "Step {}: R1CS not satisfied!",
            i
        );

        let (fresh_inst, fresh_wit) = r1cs_to_relaxed::<F, M, C>(shape, &x_i, &w_i);
        let (new_inst, new_wit) =
            fold::<F, M, C>(shape, &acc_inst, &acc_wit, &fresh_inst, &fresh_wit);

        acc_inst = new_inst;
        acc_wit = new_wit;
        z_current = z_next;
    }

    IVCProof {
        instance: acc_inst,
        witness: acc_wit,
        z_current,
        num_steps,
    }
}

/// Verify an IVC proof by checking the accumulated Relaxed R1CS.
pub fn ivc_verify<F: Field, M: MatrixOps<F>, C: CommitmentScheme<F>>(
    shape: &R1CSShape<F, M>,
    proof: &IVCProof<F, C>,
) -> bool {
    shape.is_relaxed_satisfied(&proof.instance, &proof.witness)
}
