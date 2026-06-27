from sage.all import *
from aes import *
from pwn import *
from Crypto.Util.number import *
import ast
from xor import xor

def bytes2mat(b):
    a = []
    for i in b:
        tmp = bin(i)[2:].zfill(8)
        for j in tmp:
            a.append(int(j))
    return Matrix(GF(2), a)

def mat2bytes(m):
    a = ""
    for i in range(128):
        a += str(m[0, i])
    a = [a[i:i+8] for i in range(0, 128, 8)]
    a = [int(i, 2) for i in a]
    return bytes(a)

I = identity_matrix(GF(2), 8)
X = Matrix(GF(2), 8, 8)
for i in range(7):
    X[i, i+1] = 1
X[3, 0] = 1
X[4, 0] = 1
X[6, 0] = 1
X[7, 0] = 1

C = block_matrix([
    [X, X+I, I, I],
    [I, X, X+I, I],
    [I, I, X, X+I],
    [X+I, I, I, X]
])

zeros = Matrix(GF(2), 8, 8)
zeros2 = Matrix(GF(2), 32, 32)
o0 = block_matrix([
    [I, zeros, zeros, zeros],
    [zeros, zeros, zeros, zeros],
    [zeros, zeros, zeros, zeros],
    [zeros, zeros, zeros, zeros]
])

o1 = block_matrix([
    [zeros, zeros, zeros, zeros],
    [zeros, I, zeros, zeros],
    [zeros, zeros, zeros, zeros],
    [zeros, zeros, zeros, zeros]
])

o2 = block_matrix([
    [zeros, zeros, zeros, zeros],
    [zeros, zeros, zeros, zeros],
    [zeros, zeros, I, zeros],
    [zeros, zeros, zeros, zeros]
])

o3 = block_matrix([
    [zeros, zeros, zeros, zeros],
    [zeros, zeros, zeros, zeros],
    [zeros, zeros, zeros, zeros],
    [zeros, zeros, zeros, I]
])

S = block_matrix([
    [o0, o1, o2, o3],
    [o3, o0, o1, o2],
    [o2, o3, o0, o1],
    [o1, o2, o3, o0]
])

M = block_matrix([
    [C, zeros2, zeros2, zeros2],
    [zeros2, C, zeros2, zeros2],
    [zeros2, zeros2, C, zeros2],
    [zeros2, zeros2, zeros2, C]
])

R = M*S
A = S*(R**9) # sorry for the inconsistency in the variable name, this is supposed to be SA^9 that I talked about

from sage.all import QQ
from sage.all import ZZ
from sage.all import matrix
from sage.all import vector


def attack(y, k, s, m, a, c):
    """
    Recovers the states associated with the outputs from a truncated linear congruential generator.
    More information: Frieze, A. et al., "Reconstructing Truncated Integer Variables Satisfying Linear Congruences"
    :param y: the sequential output values obtained from the truncated LCG (the states truncated to s most significant bits)
    :param k: the bit length of the states
    :param s: the bit length of the outputs
    :param m: the modulus of the LCG
    :param a: the multiplier of the LCG
    :param c: the increment of the LCG
    :return: a list containing the states associated with the provided outputs
    """
    diff_bit_length = k - s

    # Preparing for the lattice reduction.
    delta = c % m
    y = vector(ZZ, y)
    for i in range(len(y)):
        # Shift output value to the MSBs and remove the increment.
        y[i] = (y[i] << diff_bit_length) - delta
        delta = (a * delta + c) % m

    # This lattice only works for increment = 0.
    B = matrix(ZZ, len(y), len(y))
    B[0, 0] = m
    for i in range(1, len(y)):
        B[i, 0] = a ** i
        B[i, i] = -1

    B = B.LLL()

    # Finding the target value to solve the equation for the states.
    b = B * y
    for i in range(len(b)):
        b[i] = round(QQ(b[i]) / m) * m - b[i]

    # Recovering the states
    delta = c % m
    x = list(B.solve_right(b))
    for i, state in enumerate(x):
        # Adding the MSBs and the increment back again.
        x[i] = int(y[i] + state + delta)
        delta = (a * delta + c) % m

    return x


def recover_seed(leak, k, s, m, a, c):
    states = [state % m for state in attack(leak, k, s, m, a, c)]
    a_inv = pow(a, -1, m)
    seed = (a_inv * ((states[0] - c) % m)) % m
    return seed, states



def recv_line_containing(io, token):
    while True:
        line = io.recvline(timeout=10)
        if not line:
            raise EOFError(f"EOF while waiting for: {token!r}")
        if token in line:
            return line


def matrix_lll(matrix: list[list[int]], transform: bool = False):
    """
    Compute LLL reduction on the given matrix.

    Args:
        matrix (list[list[int]]): the row-major two-dimensional integer matrix
        transform (bool): return transformation matrix if True

    Returns:
        LLL-reduced matrix and optionally the transformation matrix
    """
    try:
        from flint import fmpz_mat

        B = fmpz_mat(matrix)
        return B.lll(transform=transform)
    except ImportError:
        from sage.all import Matrix

        B = Matrix(matrix)
        return B.LLL(transformation=transform)


def sda(x: list[int], rho: int) -> int | None:
    """
    Solve ACD problem using Simultaneous Diophantine Approximation from
    [Algorithms for the Approximate Common Divisor Problem](https://eprint.iacr.org/2016/215.pdf)

    Args:
        x (list[int]): an array of known x_i = pq_i + r_i
        rho (int): the log2 bound of r_i, i.e. |r_i| < 2 ** rho

    Returns:
        the recovered p, or None for failure
    """

    # Simultaneous Diophantine approximation approach (SDA)

    # step 1:
    # create matrix
    # 2^{rho+1},  x_2,  x_3, ...,  x_t
    #         0, -x_1, ...
    #         0,    0, -x_1, ...
    #         ...
    #         0,    0,       ..., -x_1
    t = len(x)
    matrix = [[0] * t for _ in range(t)]
    matrix[0][0] = 2 ** (rho + 1)
    for i in range(t - 1):
        matrix[0][i + 1] = x[i + 1]
        matrix[i + 1][i + 1] = -x[0]

    # step 2:
    # use lll reduction
    # reduced vector: (q_12^{rho+1}, q_1x_2-q_2x_1, ..., q_1x_t-q_tx_1)
    reduced = matrix_lll(matrix)

    scale = 2 ** (rho + 1)
    bound = 2 ** rho
    candidates = []
    seen = set()

    # Try all short vectors from the reduced basis, not just the first one.
    for row_idx in range(t):
        q_1 = abs(int(reduced[row_idx, 0])) // scale
        if q_1 == 0:
            continue
        r_1 = x[0] % q_1
        p = abs((x[0] - r_1) // q_1)
        if p <= 1 or p in seen:
            continue
        seen.add(p)

        # Validate candidate by checking that all residues are within the noise bound.
        if all((xi % p) < bound for xi in x):
            candidates.append(p)

    if not candidates:
        return None

    # Prefer the largest valid p.
    return max(candidates)


def main():
    io = remote("localhost", 7101)

    io.recvuntil(b"Hint: ")
    leak = ast.literal_eval(io.recvline().decode().strip())

    k = 67
    s = 33
    m = 1 << 67
    a = 6364136223846793005
    c = 1442695040888963407

    seed, _states = recover_seed(leak, k, s, m, a, c)
    log.info(f"Recovered seed: {seed}")
    io.sendline(str(seed).encode())

    first = io.recvline(timeout=10)
    if not first:
        raise EOFError("Service closed after sending seed")
    if b"Wrong key" in first:
        raise RuntimeError(
            "Service rejected recovered seed. src/chall.py currently compares str input to int seed in Python 3."
        )

    if b"wut is this???" in first:
        wut_line = first
    else:
        wut_line = recv_line_containing(io, b"wut is this???")

    x = ast.literal_eval(wut_line.split(b"wut is this???", 1)[1].strip().decode())
    goat_line = recv_line_containing(io, b"Here is one of our goats:")
    enc_line = recv_line_containing(io, b"enc_flag:")
    io.close()

    ct2_hex = goat_line.split(b":", 1)[1].strip().decode()
    ct_hex = enc_line.split(b":", 1)[1].strip().decode()

    ct = bytes.fromhex(ct_hex)
    p2 = b"tipsen my gaot!!"
    ct2 = bytes.fromhex(ct2_hex)

    p2 = bytes2mat(p2).transpose()
    ct2 = bytes2mat(ct2).transpose()

    K = ct2 - A * p2
    A_inv = A.inverse()

    # Decrypt each 16-byte block separately
    recovered = b""
    for i in range(0, len(ct), 16):
        block = ct[i:i + 16]
        recovered += mat2bytes((A_inv * (bytes2mat(block).transpose() - K)).transpose())
    print(recovered.hex())

    # Collect robust ACD candidates across nearby rho values.
    candidates = []
    rho = 50
    res = sda(x, rho) 

    print("Got result:", bool(res))
    log.info(f"Recovered xor key: {res}")
    print(xor(long_to_bytes(res), recovered))


if __name__ == "__main__":
    main()
