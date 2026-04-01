use crate::field::Field;
use sha2::{Digest, Sha256};

/// Trait for commitment schemes.
pub trait CommitmentScheme<F: Field>: Clone + PartialEq + Eq + std::fmt::Debug {
    fn commit(vector: &[F]) -> Self;
    fn commit_with_blinding(v1: &[F], v2: &[F], r: F) -> Self;
    fn value(&self) -> &[u8];
}

/// Hash-based toy commitment (SHA256). Binding but not hiding.
#[derive(Clone, PartialEq, Eq)]
pub struct ToyCommitment {
    hash: [u8; 32],
}

impl std::fmt::Debug for ToyCommitment {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(
            f,
            "Com({:02x}{:02x}{:02x}{:02x}...)",
            self.hash[0], self.hash[1], self.hash[2], self.hash[3]
        )
    }
}

impl<F: Field> CommitmentScheme<F> for ToyCommitment {
    fn commit(vector: &[F]) -> Self {
        let mut hasher = Sha256::new();
        for elem in vector {
            hasher.update(elem.to_bytes());
        }
        let hash: [u8; 32] = hasher.finalize().into();
        ToyCommitment { hash }
    }

    fn commit_with_blinding(v1: &[F], v2: &[F], r: F) -> Self {
        assert_eq!(v1.len(), v2.len(), "vectors must have equal length");
        let combined: Vec<F> = v1
            .iter()
            .zip(v2.iter())
            .map(|(&a, &b)| a.add(r.mul(b)))
            .collect();
        Self::commit(&combined)
    }

    fn value(&self) -> &[u8] {
        &self.hash
    }
}
