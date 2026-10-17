from Crypto.Util.number import bytes_to_long,getPrime
from sage.all import QQ

from secret import gen_pubkey as pub

n = getPrime(512)
p = getPrime(256)

FLAG = b"COMPFEST18{defense_not_in_depth}"
S = bytes_to_long(FLAG)

def kuekue(x, y, z):
    return QQ(x**3 + y**3 + z**3) / QQ(x * y * z)
    
def main():
    print(f"p: {p}")
    for i in range(7):
        A = getPrime(256)
        e = getPrime(128)
        b = (A * S) % p + e
        R = getPrime(1024)
        a0,b0,c0 = pub(A,b,R)
        print(f"pub = ({a0}, {b0}, {c0})")
        assert(kuekue(a0,b0,c0) == kuekue(A,b,R))

if __name__ == '__main__':
    main()