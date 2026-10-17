from sage.all import QQ, EllipticCurve_from_cubic, lcm, ZZ

def magic(x, y, z):
    return QQ(x**3 + y**3 + z**3) / QQ(x * y * z)

def gen_pubkey(x,y,z):
    t = magic(x, y, z)
    P = QQ["X, Y, Z"]
    X, Y, Z = P.gens()
    cubic = X**3 + Y**3 + Z**3 - t * X * Y * Z
    f = EllipticCurve_from_cubic(cubic, [1, -1, 0])
    fi = f.inverse()
    H = f([x, y, z])
    G = 2 * H
    a, b, c = fi(G)
    l = lcm(lcm(a.denominator(), b.denominator()), c.denominator())
    a, b, c = ZZ(a * l), ZZ(b * l), ZZ(c * l)
    return int(a), int(b), int(c)