from pwn import *
from Crypto.Cipher import AES
from Crypto.Util.strxor import strxor
from Crypto.Util.Padding import unpad

#r = process(['python3', '../src/chall.py'])
r = remote('localhost', 1337)
r.recvuntil(b'> ')
r.sendline(b'3')
ct = bytes.fromhex(r.recvline().strip().decode())
iv = ct[:16]
ct = ct[16:]

def padding_oracle(iv: bytes, ct: bytes):
    assert len(iv) == AES.block_size
    send_bytes = (iv.hex() + ct.hex()).encode()
    r.recvuntil(b'> ')
    r.sendline(b'2')
    r.sendline(send_bytes)
    response = r.recvline()
    return b'Oops mesin pemecah telur rusak' not in response

def _attack_block(padding_oracle, iv, c):
    r = bytes()
    for i in reversed(range(16)):
        s = bytes([16 - i] * (16 - i))
        for b in range(256):
            iv_ = bytes(i) + strxor(s, bytes([b]) + r)
            if padding_oracle(iv_, c):
                r = bytes([b]) + r
                break
        else:
            raise ValueError(f"Unable to find decryption for {s}, {iv}, and {c}")

    return strxor(iv, r)


def attack(padding_oracle, iv, c):
    """
    Recovers the plaintext using the padding oracle attack.
    :param padding_oracle: the padding oracle, returns True if the padding is correct, False otherwise
    :param iv: the initialization vector
    :param c: the ciphertext
    :return: the (padded) plaintext
    """
    p = _attack_block(padding_oracle, iv, c[0:16])
    for i in range(16, len(c), 16):
        p += _attack_block(padding_oracle, c[i - 16:i], c[i:i + 16])

    return p


pt = unpad(attack(padding_oracle, iv, ct), AES.block_size)
print(pt)
r.close()
