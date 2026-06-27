#!/usr/bin/env python3
"""Extract encrypted keylogger payloads from a PCAP/PCAPNG capture."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Iterable

try:
    from scapy.all import Raw, UDP, rdpcap
except ImportError as exc:  # pragma: no cover - dependency error surfaced to user
    raise SystemExit(
        "Missing dependency: scapy. Install it with 'pip install scapy'."
    ) from exc

try:
    from Crypto.Cipher import AES
except ImportError as exc:  # pragma: no cover - dependency error surfaced to user
    raise SystemExit(
        "Missing dependency: pycryptodome. Install it with 'pip install pycryptodome'."
    ) from exc


def iter_payloads(
    packets, port: int | None
) -> Iterable[tuple[int, bytes]]:
    """Yield (index, payload_bytes) for UDP packets hitting the keylogger port."""
    for idx, packet in enumerate(packets, start=1):
        if UDP not in packet or Raw not in packet:
            continue

        udp_layer = packet[UDP]
        if port is not None and udp_layer.dport != port and udp_layer.sport != port:
            continue

        payload = bytes(packet[Raw].load)
        if payload:
            yield idx, payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
        "Extract encrypted UDP payloads produced by the keylogger, decrypt them, "
        "and print the recovered keystrokes."
    )
    )
    parser.add_argument("pcap", help="Path to the PCAP/PCAPNG capture file")
    parser.add_argument(
        "--port",
        type=int,
        default=9000,
        help="UDP port used by the keylogger (default: 9000)",
    )
    parser.add_argument(
        "--key-hex",
        default="0100f6082d5b7de566d7b44fdf2c56b659884a582099ad4287bcc00b4a38ab3c",
        help="AES key in hexadecimal (default: key used in logger.py)",
    )
    parser.add_argument(
        "--nonce-hex",
        default="69a7ec080b0cdb04c214a9aa",
        help="AES-GCM nonce in hexadecimal (default: nonce used in logger.py)",
    )
    return parser.parse_args()


def decrypt_payload(payload: bytes, key: bytes, nonce: bytes) -> str:
    if len(payload) < 16:
        raise ValueError("ciphertext too short to contain GCM authentication tag")
    ciphertext, tag = payload[:-16], payload[-16:]
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    plaintext = cipher.decrypt_and_verify(ciphertext, tag)
    return plaintext.decode("utf-8", errors="replace")


def main() -> int:
    args = parse_args()

    try:
        packets = rdpcap(args.pcap)
    except OSError as err:
        print(f"Failed to read capture '{args.pcap}': {err}", file=sys.stderr)
        return 1

    try:
        key = bytes.fromhex(args.key_hex)
        nonce = bytes.fromhex(args.nonce_hex)
    except ValueError as err:
        print(f"Invalid key/nonce hex: {err}", file=sys.stderr)
        return 1

    if len(key) not in (16, 24, 32):
        print("AES key must be 16/24/32 bytes when decoded.", file=sys.stderr)
        return 1

    if len(nonce) != 12:
        print("AES-GCM nonce must decode to exactly 12 bytes.", file=sys.stderr)
        return 1

    printed = 0
    for pkt_idx, payload in iter_payloads(packets, args.port):
        try:
            plaintext = decrypt_payload(payload, key, nonce)
            clear = json.loads(plaintext)
            events = clear.get("events", [])
            keys = ", ".join(event.get("key", "?") for event in events)
            print(f"[pkt {pkt_idx} seq={clear.get('seq')}] {keys}")
            printed += 1
        except Exception as err:  # noqa: BLE001
            print(f"[pkt {pkt_idx}] failed to decrypt: {err}", file=sys.stderr)

    if printed == 0:
        print("No matching encrypted payloads found.", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
