import os
import subprocess
import tempfile


nope = [">","<"," ","=" ,"/","\\",","] #why would you ever need this

print("Welcome to CSaaS!!")

print("Please input the following parameters value:")
print("n: ",end="")
n = input()
print("e: ",end="")
e = input()
print("c1: ",end="")
c1 = input()
print("c2: ",end="")
c2 = input()
print("function variable: ",end="")
var = input()
print("f: ",end="")
f = input()
print("g: ",end="")
g = input()

params = [n, e, c1, c2, var, f, g]
for param in params:
    if len(param) > 35:
        print("Too long!")
        exit()
    for _ in nope:
        if _ in param:
            print("Nope")
            exit()

n = int(n)
e = int(e)
c1 = int(c1)
c2 = int(c2)

code = f"""
n  = {n}
e  = {e}
c1 = {c1}
c2 = {c2}

R.<{var}> = Zmod(n)[]

f = R({f!r})
g = R({g!r})

h = gcd(f, g)
m = (-h[0])
print(m)
"""

with tempfile.NamedTemporaryFile(mode="w", suffix=".sage", delete=False) as temp_file:
    temp_file.write(code)
    temp_file_path = temp_file.name

try:
    result = subprocess.run(["sage", temp_file_path], capture_output=True, text=True)
    print("Output:")
    print(result.stdout)
    if result.stderr:
        print("Errors:")
        print(result.stderr)

except subprocess.TimeoutExpired:
    print("Timeout")

finally:
    os.unlink(temp_file_path)
