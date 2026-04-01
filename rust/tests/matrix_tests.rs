use nano_nova::field::{Field, Fp61};
use nano_nova::matrix::{DenseMatrix, MatrixOps};

#[test]
fn test_identity_mul_vec() {
    let data = vec![
        Fp61::one(),
        Fp61::zero(),
        Fp61::zero(),
        Fp61::zero(),
        Fp61::one(),
        Fp61::zero(),
        Fp61::zero(),
        Fp61::zero(),
        Fp61::one(),
    ];
    let m = DenseMatrix::new(data, 3, 3);
    let v = vec![Fp61::from_u64(1), Fp61::from_u64(2), Fp61::from_u64(3)];
    let result = m.mul_vec(&v);
    assert_eq!(result, v);
}

#[test]
fn test_mul_vec_sums_row() {
    let data = vec![Fp61::one(), Fp61::one(), Fp61::one()];
    let m = DenseMatrix::new(data, 1, 3);
    let v = vec![Fp61::from_u64(2), Fp61::from_u64(3), Fp61::from_u64(4)];
    let result = m.mul_vec(&v);
    assert_eq!(result, vec![Fp61::from_u64(9)]);
}

#[test]
fn test_dimensions() {
    let data = vec![Fp61::zero(); 6];
    let m = DenseMatrix::new(data, 2, 3);
    assert_eq!(m.rows(), 2);
    assert_eq!(m.cols(), 3);
}

#[test]
fn test_zeros() {
    let m: DenseMatrix<Fp61> = DenseMatrix::zeros(3, 4);
    assert_eq!(m.rows(), 3);
    assert_eq!(m.cols(), 4);
    let v = vec![Fp61::from_u64(1); 4];
    let result = m.mul_vec(&v);
    assert_eq!(result, vec![Fp61::zero(); 3]);
}

#[test]
fn test_set_get() {
    let mut m: DenseMatrix<Fp61> = DenseMatrix::zeros(3, 3);
    m.set(1, 2, Fp61::from_u64(42));
    assert_eq!(m.get(1, 2), Fp61::from_u64(42));
    assert_eq!(m.get(0, 0), Fp61::zero());
}
