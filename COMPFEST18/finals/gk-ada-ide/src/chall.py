from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import os

key = os.urandom(16)
block_size = 16
iv = 'whatisthisfor???'
with open("flag.txt", "r") as f:
    FLAG = f.read().strip()

assert len(FLAG) % 16 == 0
assert len(iv) == block_size

def xor(a, b):
    return bytes([a[i] ^ b[i] for i in range(len(a))])


def encrypt(data):
    cipher = AES.new(key, AES.MODE_CBC, iv=iv.encode())
    return cipher.encrypt(data)

def decrypt(ct):
    pt = b''
    prev = iv.encode() 
    for i in range(0, len(ct), AES.block_size):
        block = ct[i:i+AES.block_size]
        cipher = AES.new(key, AES.MODE_ECB)
        p = xor(cipher.decrypt(block), prev)
        pt += p
        prev = xor(block, p)
    return pt

def main():
    enc_data = encrypt(FLAG.encode())
    print(f"This is the encrypted block: {[enc_data[i:i+block_size] for i in range(0, len(enc_data), block_size)]}")
    
    while True:
        print("Only send hex!")
        inp = input(">> ")
        print(f"Here is the result: {decrypt(bytes.fromhex(inp))}\n")
        
if __name__ == "__main__":
    main()