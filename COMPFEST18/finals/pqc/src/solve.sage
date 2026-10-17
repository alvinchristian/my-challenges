from pwn import *
from Crypto.Util.number import long_to_bytes

def hnp(p, T, A, B, lattice_reduction=None, verbose=False):
    verbose = (lambda *a: print('[hnp]', *a)) if verbose else lambda *_: None

    if len(T) != len(A):
        raise ValueError(f'Expected number of t_i to equal number of a_i, but got {len(T)} and {len(A)}.')

    m = len(T)
    M = p * Matrix.identity(QQ, m)
    M = M.stack(vector(T))
    M = M.stack(vector(A))
    M = M.augment(vector([0] * m + [B / p] + [0]))
    M = M.augment(vector([0] * (m + 1) + [B]))
    M = M.dense_matrix()

    verbose('Lattice dimensions:', M.dimensions())
    lattice_reduction_timer = cputime()
    if lattice_reduction:
        M = lattice_reduction(M)
    else:
        M = M.LLL()
    verbose(f'Lattice reduction took {cputime(lattice_reduction_timer):.3f}s')

    for row in M:
        if row[-1] == -B:
            alpha = (row[-2] * p / B) % p
            if all((beta - t * alpha + a) % p == 0 for beta, t, a in zip(row[:m], T, A)):
                return alpha
        if row[-1] == B:
            alpha = (-row[-2] * p / B) % p
            if all((beta - t * alpha + a) % p == 0 for beta, t, a in zip(-row[:m], T, A)):
                return alpha

    return None

io = process(['python', 'chall.py'])
#io = remote('34.142.142.133', 9003)
io.recvuntil('p: ')
p = int(io.recvline().strip().decode())

A_list = []
b_list = []

for i in range(10):
    io.recvuntil('> ')
    io.sendline('0')
    io.recvuntil('A: ')
    A = int(io.recvline().strip().decode())
    io.recvuntil('b: ')
    b = int(io.recvline().strip().decode())
    A_list.append(A)
    b_list.append(b)

S = hnp(p, A_list, b_list, 2**128 + 2**256 )
print(long_to_bytes(S))