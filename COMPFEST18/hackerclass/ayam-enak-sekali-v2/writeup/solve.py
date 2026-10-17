from pwn import *
from binascii import unhexlify, hexlify

context.log_level = 'info'
r = remote('localhost', 7103)

r.sendlineafter(b'> ', b'3')

encrypted_flag_hex = r.recvline().strip()
log.success(f"Encrypted Flag (HEX): {encrypted_flag_hex.decode()}")
encrypted_flag = unhexlify(encrypted_flag_hex)

AES_BLOCK_SIZE = 16
iv_original = encrypted_flag[:AES_BLOCK_SIZE]
ciphertext_asli = encrypted_flag[AES_BLOCK_SIZE:]

iv_modified_list = list(iv_original)
iv_modified_list[0] ^= 1  # Melakukan bit-flipping
iv_modified = bytes(iv_modified_list)

modified_ciphertext = iv_modified + ciphertext_asli
modified_ciphertext_hex = hexlify(modified_ciphertext)


r.sendlineafter(b'> ', b'2')
r.sendlineafter(b'> ', modified_ciphertext_hex)

mangled_flag_raw = r.recvline().strip()
mangled_flag = eval(mangled_flag_raw)

# Perbaiki byte pertama untuk mendapatkan flag asli
flag_list = list(mangled_flag)
flag_list[0] ^= 1 # Balikkan proses bit-flipping
flag = bytes(flag_list)

log.success(f"Flag: {flag.decode()}")

r.close()