#!/usr/bin/env python3

from __future__ import annotations
import uuid
import datetime
import sys
import argparse
from typing import Iterator


# ---------- helpers for exact 100ns handling ----------

EPOCH_1582 = datetime.datetime(1582, 10, 15, tzinfo=None)
# conversion constants (integers)
TICKS_PER_SECOND = 10_000_000          # 1e7 100ns ticks per second
TICKS_PER_MICROSECOND = 10             # 10 ticks per microsecond


def timestamp_to_datetime_exact(uuid_time: int) -> tuple[datetime.datetime, int]:
    """
    Convert an integer UUID timestamp (100ns ticks since 1582-10-15)
    to a (datetime, remainder_100ns) tuple where remainder_100ns is
    the leftover ticks smaller than 1 second (0..TICKS_PER_SECOND-1).
    The returned datetime has second precision (no fractional microseconds).
    """
    seconds = uuid_time // TICKS_PER_SECOND
    remainder_ticks = uuid_time % TICKS_PER_SECOND
    dt = EPOCH_1582 + datetime.timedelta(seconds=int(seconds))
    return dt, remainder_ticks


def datetime_to_timestamp_exact(dt: datetime.datetime) -> int:
    """
    Convert a naive (or tz-unaware) datetime into UUID v1 timestamp
    integer (100ns ticks since 1582-10-15) using only integer math.
    Note: dt must not be earlier than the UUID epoch.
    """
    if dt.tzinfo is not None:
        # convert to naive by dropping tz (caller should pass naive)
        dt = dt.astimezone(datetime.timezone.utc).replace(tzinfo=None)

    delta = dt - EPOCH_1582
    # total seconds (integer) and microseconds (int)
    total_seconds = int(delta.days) * 86400 + delta.seconds
    # delta.microseconds is already integer microseconds
    microseconds = delta.microseconds
    ticks = total_seconds * TICKS_PER_SECOND + microseconds * TICKS_PER_MICROSECOND
    return int(ticks)


# ---------- UUID construction (copied/compatible with Python stdlib) ----------

def uuid1_from_parts(node: int, clock_seq: int, timestamp: int) -> uuid.UUID:
    """
    Build a uuid.UUID object from node, clock_seq, and timestamp (100ns ticks).
    Mirrors Python's uuid._uuid_generate_time-based logic fields.
    """
    time_low = timestamp & 0xFFFFFFFF
    time_mid = (timestamp >> 32) & 0xFFFF
    time_hi_version = (timestamp >> 48) & 0x0FFF
    clock_seq_low = clock_seq & 0xFF
    clock_seq_hi_variant = (clock_seq >> 8) & 0x3F
    return uuid.UUID(fields=(time_low, time_mid, time_hi_version,
                             clock_seq_hi_variant, clock_seq_low, node), version=1)


# ---------- printing / parsing helpers ----------

def UUIDTime(u: uuid.UUID) -> tuple[datetime.datetime, int]:
    """Return (datetime base-second, remainder_100ns) for a uuid.UUID v1"""
    if u.version != 1:
        raise ValueError("UUID is not version 1")
    ts = u.time  # integer 100ns ticks
    return timestamp_to_datetime_exact(ts)


def UUIDMac(u: uuid.UUID) -> str:
    """Return MAC address from UUID node value as common hex colon form."""
    return ":".join(['{:02x}'.format((u.node >> ele) & 0xff) for ele in range(0, 8*6, 8)][::-1])


def printUUIDInfo(u_str: str) -> None:
    try:
        u = uuid.UUID(u_str)
    except Exception:
        print("Invalid UUID")
        sys.exit(2)

    print("UUID version: {}".format(u.version))

    if u.version == 1:
        dt, rem = UUIDTime(u)
        # rem is number of 100ns ticks into that second
        # Convert remainder to microseconds + leftover 100ns ticks for human display
        microsec = rem // TICKS_PER_MICROSECOND
        leftover_100ns = rem % TICKS_PER_MICROSECOND
        print("UUID time (base second): {}".format(dt))
        print("UUID remainder into second (100ns ticks): {}".format(rem))
        print("UUID time (with fractional microsecond): {} + {}×100ns".format(dt + datetime.timedelta(microseconds=microsec), leftover_100ns))
        print("UUID timestamp (100ns ticks): {}".format(u.time))
        print("UUID node: {}".format(u.node))
        print("UUID MAC address: {}".format(UUIDMac(u)))
        print("UUID clock sequence: {}".format(u.clock_seq))


# ---------- generation ----------

def genUUIDs(sample_uuid: str, precision: int, seconds: int, base_timestamp: int) -> Iterator[uuid.UUID]:
    """
    Generate UUIDs:
      - If seconds == 0: produce canonical uuid for base_timestamp once,
        then brute force the 4th group (clock-seq hex) by string combinatorics,
        but yield only UUIDs that are version 1 and RFC-4122 variant.
      - Else: iterate timestamps from base_timestamp - seconds .. + seconds
        with step 'precision' (precision in 100ns ticks).
    sample_uuid: a string UUID used to extract node and clock_seq defaults.
    base_timestamp: integer number of 100ns ticks since epoch.
    """
    u = uuid.UUID(sample_uuid)
    if u.version != 1:
        print("Only v1 GUIDs supported")
        sys.exit(2)

    node = u.node
    clock_seq = u.clock_seq

    # seconds==0: do canonical + brute force 4th group by text manipulation,
    # but only yield RFC-4122 compatible v1 UUIDs.
    if seconds == 0:
        canonical = uuid1_from_parts(node, clock_seq, base_timestamp)
        yield canonical

        s = str(canonical)  # standard UUID textual format
        parts = s.split('-')
        if len(parts) != 5:
            print("Unexpected UUID format", file=sys.stderr)
            sys.exit(2)

        prefix = "-".join(parts[0:3]) + "-"   # keep time_low-time_mid-time_hi_and_version-
        suffix = "-" + parts[4]               # keep -node

        # We brute-force the 16-bit clock-seq field (4 hex characters).
        # Only values where the high byte has RFC-4122 variant bits (0b10xxxxxx)
        # are valid. That means (high_byte & 0xC0) == 0x80.
        for i in range(0x0000, 0x10000):
            high_byte = (i >> 8) & 0xFF
            if (high_byte & 0xC0) != 0x80:
                # Skip values with non-RFC variant bits
                continue

            new_clock_group = f"{i:04x}"
            new_uuid_str = prefix + new_clock_group + suffix
            try:
                candidate = uuid.UUID(new_uuid_str)
            except Exception:
                # unlikely, but skip malformed strings
                continue

            # Double-check it's a v1 RFC-4122 UUID
            if candidate.version != 1:
                continue
            if candidate.variant != uuid.RFC_4122:
                continue

            yield candidate

        return

    # non-zero seconds: vary timestamp in integer ticks
    start = int(base_timestamp - (TICKS_PER_SECOND * seconds))
    end = int(base_timestamp + (TICKS_PER_SECOND * seconds)) + 1
    # guard: precision must be >= 1
    if precision <= 0:
        precision = 1
    for t in range(start, end, precision):
        yield uuid1_from_parts(node, clock_seq, int(t))


# ---------- main / CLI ----------

def main() -> None:
    parser = argparse.ArgumentParser(prog="uuid_time_tool.py")
    parser.add_argument("-i", "--info", help="Print UUID info and exit", action="store_true")
    parser.add_argument("-p", "--precision", type=int, default=10000,
                        help="Number of 100ns intervals between each UUID (default 10000)")
    parser.add_argument("-r", "--range", type=int, default=1,
                        help="Number of seconds each side of the timestamp to generate UUIDs for (default 1). Use 0 to brute force 4th group.")
    parser.add_argument("-t", "--base-time",
                        help="Either a UUID timestamp integer (100ns ticks) OR a datetime 'YYYY-MM-DD HH:MM:SS'",
                        type=str, required=True)
    parser.add_argument("uuid", help="A sample UUID v1 to match node/clock_seq")
    args = parser.parse_args()

    # Validate GUID
    try:
        _ = uuid.UUID(args.uuid)
    except ValueError:
        print("Invalid UUID")
        sys.exit(1)

    # If info requested, print and exit
    if args.info:
        printUUIDInfo(args.uuid)
        sys.exit(0)

    # parse base-time argument:
    base_time_arg = args.base_time
    base_timestamp: int
    try:
        if base_time_arg.isdigit():
            # numeric: assume it's the raw UUID timestamp (100ns ticks)
            base_timestamp = int(base_time_arg)
        else:
            # parse datetime string exactly "YYYY-MM-DD HH:MM:SS"
            dt = datetime.datetime.strptime(base_time_arg, "%Y-%m-%d %H:%M:%S")
            base_timestamp = datetime_to_timestamp_exact(dt)
    except Exception as e:
        print("Error parsing base time:", e)
        sys.exit(1)

    # Show brief diagnostic (exact values)
    dt_base, rem = timestamp_to_datetime_exact(base_timestamp)
    microsec = rem // TICKS_PER_MICROSECOND
    leftover_100ns = rem % TICKS_PER_MICROSECOND
    # Generate and print UUIDs
    try:
        for u in genUUIDs(args.uuid, args.precision, args.range, base_timestamp):
            print(u)
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
