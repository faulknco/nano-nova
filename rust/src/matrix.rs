use crate::field::Field;

/// Trait for matrix-vector multiplication.
///
/// Abstracts over dense and (future) sparse matrix representations.
pub trait MatrixOps<F: Field> {
    fn mul_vec(&self, v: &[F]) -> Vec<F>;
    fn rows(&self) -> usize;
    fn cols(&self) -> usize;
}

/// Row-major dense matrix over a field F.
pub struct DenseMatrix<F: Field> {
    data: Vec<F>,
    nrows: usize,
    ncols: usize,
}

impl<F: Field> DenseMatrix<F> {
    pub fn new(data: Vec<F>, nrows: usize, ncols: usize) -> Self {
        assert_eq!(
            data.len(),
            nrows * ncols,
            "data length must equal nrows * ncols"
        );
        DenseMatrix { data, nrows, ncols }
    }

    pub fn zeros(nrows: usize, ncols: usize) -> Self {
        DenseMatrix {
            data: vec![F::zero(); nrows * ncols],
            nrows,
            ncols,
        }
    }

    #[inline]
    pub fn get(&self, row: usize, col: usize) -> F {
        self.data[row * self.ncols + col]
    }

    #[inline]
    pub fn set(&mut self, row: usize, col: usize, val: F) {
        self.data[row * self.ncols + col] = val;
    }
}

impl<F: Field> MatrixOps<F> for DenseMatrix<F> {
    fn mul_vec(&self, v: &[F]) -> Vec<F> {
        assert_eq!(
            v.len(),
            self.ncols,
            "vector length must match matrix columns"
        );
        (0..self.nrows)
            .map(|i| {
                let row_start = i * self.ncols;
                let mut sum = F::zero();
                for (j, &vj) in v.iter().enumerate() {
                    sum = sum.add(self.data[row_start + j].mul(vj));
                }
                sum
            })
            .collect()
    }

    fn rows(&self) -> usize {
        self.nrows
    }

    fn cols(&self) -> usize {
        self.ncols
    }
}
