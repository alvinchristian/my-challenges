"""Compatibility XOR helper matching pwntools xor behavior for common inputs."""


def _flatten(value):
    if isinstance(value, (bytes, bytearray, memoryview)):
        return bytes(value)

    if isinstance(value, str):
        return value.encode()

    if isinstance(value, int):
        if -128 <= value <= 255:
            return bytes([value & 0xFF])
        if value >= 0:
            raise ValueError(f"pack(): number does not fit within word_size [0, {value}, 256]")
        raise ValueError("pack(): number does not fit within word_size")

    if isinstance(value, (list, tuple)):
        return b"".join(_flatten(v) for v in value)

    raise TypeError(f"flat(): cannot flatten object of type {type(value).__name__}")


def xor(*args, **kwargs):
    cut = kwargs.pop("cut", "max")
    if kwargs:
        bad_key = next(iter(kwargs))
        raise TypeError(f"xor() got an unexpected keyword argument '{bad_key}'")

    if not args:
        raise ValueError("Must have something to xor")

    parts = []
    for arg in args:
        data = _flatten(arg)
        if data:
            parts.append(bytearray(data))
    if not parts:
        return b""

    if isinstance(cut, int):
        out_len = cut
    elif cut == "left":
        out_len = len(parts[0])
    elif cut == "right":
        out_len = len(parts[-1])
    elif cut == "min":
        out_len = min(len(p) for p in parts)
    elif cut == "max":
        out_len = max(len(p) for p in parts)
    else:
        raise ValueError("Not a valid argument for 'cut'")

    out = bytearray()
    for i in range(out_len):
        b = 0
        for part in parts:
            b ^= part[i % len(part)]
        out.append(b)
    return bytes(out)
