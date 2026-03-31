use rand::Rng;

/// Prime field element trait.
pub trait Field: Copy + Clone + PartialEq + Eq + std::fmt::Debug + Sized {
    fn zero() -> Self;
    fn one() -> Self;
    fn from_u64(val: u64) -> Self;
    fn add(self, other: Self) -> Self;
    fn sub(self, other: Self) -> Self;
    fn mul(self, other: Self) -> Self;
    fn inv(self) -> Self;
    fn random() -> Self;
    fn to_bytes(self) -> [u8; 8];
}

/// Field element modulo the Mersenne prime p = 2^61 - 1.
#[derive(Copy, Clone, PartialEq, Eq, Debug)]
pub struct Fp61(u64);

const P: u64 = (1u64 << 61) - 1;

impl Fp61 {
    #[inline]
    fn reduce(x: u128) -> u64 {
        let mut r = (x as u64 & P) + ((x >> 61) as u64);
        if r >= P {
            r -= P;
        }
        r
    }
}

impl Field for Fp61 {
    #[inline]
    fn zero() -> Self {
        Fp61(0)
    }

    #[inline]
    fn one() -> Self {
        Fp61(1)
    }

    fn from_u64(val: u64) -> Self {
        Fp61(val % P)
    }

    #[inline]
    fn add(self, other: Self) -> Self {
        let mut r = self.0 + other.0;
        if r >= P {
            r -= P;
        }
        Fp61(r)
    }

    #[inline]
    fn sub(self, other: Self) -> Self {
        let r = if self.0 >= other.0 {
            self.0 - other.0
        } else {
            P - other.0 + self.0
        };
        Fp61(r)
    }

    #[inline]
    fn mul(self, other: Self) -> Self {
        let wide = self.0 as u128 * other.0 as u128;
        Fp61(Self::reduce(wide))
    }

    fn inv(self) -> Self {
        assert!(self.0 != 0, "cannot invert zero");
        // Fermat's little theorem: a^(p-2) mod p
        let mut result = Fp61::one();
        let mut base = self;
        let mut exp = P - 2;
        while exp > 0 {
            if exp & 1 == 1 {
                result = result.mul(base);
            }
            base = base.mul(base);
            exp >>= 1;
        }
        result
    }

    fn random() -> Self {
        let mut rng = rand::thread_rng();
        Fp61(rng.gen_range(0..P))
    }

    fn to_bytes(self) -> [u8; 8] {
        self.0.to_be_bytes()
    }
}

/// Create a vector of n zero field elements.
pub fn field_zeros<F: Field>(n: usize) -> Vec<F> {
    vec![F::zero(); n]
}

/// Create a vector of n random field elements.
pub fn random_field_vector<F: Field>(n: usize) -> Vec<F> {
    (0..n).map(|_| F::random()).collect()
}
