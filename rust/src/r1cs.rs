use crate::commitment::CommitmentScheme;
use crate::field::{field_zeros, Field};
use crate::matrix::MatrixOps;

/// R1CS constraint system: Az . Bz = Cz.
pub struct R1CSShape<F: Field, M: MatrixOps<F>> {
    pub a: M,
    pub b: M,
    pub c: M,
    pub m: usize,
    pub n: usize,
    pub l: usize,
    _phantom: std::marker::PhantomData<F>,
}

impl<F: Field, M: MatrixOps<F>> R1CSShape<F, M> {
    pub fn new(a: M, b: M, c: M, m: usize, n: usize, l: usize) -> Self {
        R1CSShape {
            a,
            b,
            c,
            m,
            n,
            l,
            _phantom: std::marker::PhantomData,
        }
    }

    /// Check Az . Bz = Cz where z = (1, x, w).
    pub fn is_satisfied(&self, x: &[F], w: &[F]) -> bool {
        let z = self.make_z(x, w);
        let az = self.a.mul_vec(&z);
        let bz = self.b.mul_vec(&z);
        let cz = self.c.mul_vec(&z);
        az.iter()
            .zip(bz.iter())
            .zip(cz.iter())
            .all(|((&a, &b), &c)| a.mul(b) == c)
    }

    /// Check Az . Bz = u*Cz + E where z = (u, x, W).
    pub fn is_relaxed_satisfied<C: CommitmentScheme<F>>(
        &self,
        instance: &RelaxedR1CSInstance<F, C>,
        witness: &RelaxedR1CSWitness<F>,
    ) -> bool {
        let z = self.make_relaxed_z(instance.u, &instance.x, &witness.w);
        let az = self.a.mul_vec(&z);
        let bz = self.b.mul_vec(&z);
        let cz = self.c.mul_vec(&z);
        az.iter()
            .zip(bz.iter())
            .zip(cz.iter())
            .zip(witness.e.iter())
            .all(|(((&a, &b), &c), &e)| a.mul(b) == instance.u.mul(c).add(e))
    }

    /// Build z = (1, x, w).
    pub fn make_z(&self, x: &[F], w: &[F]) -> Vec<F> {
        let mut z = Vec::with_capacity(self.n);
        z.push(F::one());
        z.extend_from_slice(x);
        z.extend_from_slice(w);
        z
    }

    /// Build z = (u, x, w).
    pub fn make_relaxed_z(&self, u: F, x: &[F], w: &[F]) -> Vec<F> {
        let mut z = Vec::with_capacity(self.n);
        z.push(u);
        z.extend_from_slice(x);
        z.extend_from_slice(w);
        z
    }
}

/// Public part of a Relaxed R1CS instance.
pub struct RelaxedR1CSInstance<F: Field, C: CommitmentScheme<F>> {
    pub com_e: C,
    pub u: F,
    pub x: Vec<F>,
    pub com_w: C,
}

/// Private part of a Relaxed R1CS instance.
pub struct RelaxedR1CSWitness<F: Field> {
    pub e: Vec<F>,
    pub w: Vec<F>,
}

/// Lift a standard R1CS instance (x, w) to Relaxed R1CS with u=1, E=0.
pub fn r1cs_to_relaxed<F: Field, M: MatrixOps<F>, C: CommitmentScheme<F>>(
    shape: &R1CSShape<F, M>,
    x: &[F],
    w: &[F],
) -> (RelaxedR1CSInstance<F, C>, RelaxedR1CSWitness<F>) {
    let e = field_zeros::<F>(shape.m);
    let com_e = C::commit(&e);
    let com_w = C::commit(w);
    let instance = RelaxedR1CSInstance {
        com_e,
        u: F::one(),
        x: x.to_vec(),
        com_w,
    };
    let witness = RelaxedR1CSWitness {
        e,
        w: w.to_vec(),
    };
    (instance, witness)
}

/// Create a trivial relaxed instance (u=0, E=0, W=0, x=0).
pub fn trivial_relaxed<F: Field, M: MatrixOps<F>, C: CommitmentScheme<F>>(
    shape: &R1CSShape<F, M>,
) -> (RelaxedR1CSInstance<F, C>, RelaxedR1CSWitness<F>) {
    let e = field_zeros::<F>(shape.m);
    let w = field_zeros::<F>(shape.n - 1 - shape.l);
    let x = field_zeros::<F>(shape.l);
    let com_e = C::commit(&e);
    let com_w = C::commit(&w);
    let instance = RelaxedR1CSInstance {
        com_e,
        u: F::zero(),
        x,
        com_w,
    };
    let witness = RelaxedR1CSWitness { e, w };
    (instance, witness)
}
