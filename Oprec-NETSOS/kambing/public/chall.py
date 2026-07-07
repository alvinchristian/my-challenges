import os
from aes import *
from Crypto.Util.number import *
import secrets
from xor import xor


BITS = 50
key = os.urandom(16)
secret_xor = getPrime(128)

class LCG:
    def __init__(self, seed, m=1<<67, a=6364136223846793005, c=1442695040888963407):
        self.m = m
        self.a = a % m
        self.c = c % m
        self.state = seed & (m-1)

    def next(self):
        self.state = (self.a * self.state + self.c) & (self.m - 1)
        return self.state


def enc(plain):
    return [secrets.randbelow(plain)*plain + secrets.randbelow(2**BITS) for _ in range(5)]

seed = secrets.randbits(67)

lcg = LCG(seed)
leak = [lcg.next() >> 34 for _ in range(10)]


print("Enter the secret key to meet the goat!!")
print("Hint: ",leak)
secret = int(input())

if secret != seed:
    print("Wrong key, the gaot is disappointed :(")
    exit(0)

flag = open('flag.txt').read().strip().encode()
flag = xor(flag, long_to_bytes(secret_xor))
c = AES(key)

enc_flag = b"".join(c.encrypt_block(block) for block in split_blocks(pad(flag)))

print("wut is this??? ",enc(secret_xor))
print("Here is one of our goats: ", c.encrypt_block(b"tipsen my gaot!!").hex())
print("enc_flag:", enc_flag.hex())
