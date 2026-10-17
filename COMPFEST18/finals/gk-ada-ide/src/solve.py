from pwn import *

# If running locally:
#p = process(['python3', 'chall.py'])
# If remote:
p = remote('34.1.203.129', 3321)

iv = b'whatisthisfor???'

def xor(a, b):
    return bytes(x ^ y for x, y in zip(a, b))

def get_enc():
    p.recvuntil(b'This is the encrypted block: ')
    enc_str = p.recvline().strip().decode()
    blocks_str = enc_str[1:-1].split(', ')
    blocks = [eval(block) for block in blocks_str]
    return blocks

def oracle(data):
    p.recvuntil(b'>> ')
    p.sendline(data.hex().encode())
    p.recvuntil(b'Here is the result: ')
    line = p.recvline().strip().decode()
    return eval(line)

def main():
    enc = get_enc()
    flag = b''
    prev = iv

    for c in enc:
        block = oracle(c)
        pt_block = xor(xor(block, iv), prev)
        flag += pt_block
        prev = c

    print(flag)

if __name__ == '__main__':
    main()