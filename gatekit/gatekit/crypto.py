"""Pedagogical-grade pack encryption built from the Python standard library.

Content key K (32 random bytes) encrypts the payload with a SHAKE-256
keystream and is authenticated with HMAC-SHA256.  K is wrapped once per
accepted secret in a LUKS-style key slot derived with PBKDF2.
"""

import hashlib
import hmac
import os
import secrets

PBKDF2_ITERATIONS = 100_000
KEY_LEN = 32
NONCE_LEN = 16
SALT_LEN = 16


class PackError(Exception):
    """Raised when a pack cannot be decoded, authenticated or unlocked."""


def random_key():
    """Return a fresh 32-byte content key."""
    return secrets.token_bytes(KEY_LEN)


def random_nonce():
    """Return a fresh 16-byte nonce."""
    return secrets.token_bytes(NONCE_LEN)


def keystream(key, nonce, length):
    """Return `length` keystream bytes for (key, nonce)."""
    return hashlib.shake_256(key + nonce).digest(length)


def xor_bytes(data, stream):
    """XOR two equal-length byte strings."""
    if len(data) != len(stream):
        raise PackError("keystream length mismatch")
    return bytes(a ^ b for a, b in zip(data, stream))


def encrypt(key, nonce, plaintext):
    """Encrypt plaintext with the SHAKE-256 keystream."""
    return xor_bytes(plaintext, keystream(key, nonce, len(plaintext)))


def decrypt(key, nonce, ciphertext):
    """Decrypt ciphertext with the SHAKE-256 keystream."""
    return encrypt(key, nonce, ciphertext)


def mac_key(key):
    """Derive the MAC key from the content key."""
    return hashlib.sha256(b"mac" + key).digest()


def compute_mac(key, header_bytes, nonce, ciphertext):
    """Return the hex HMAC-SHA256 over header, nonce and ciphertext."""
    return hmac.new(mac_key(key), header_bytes + nonce + ciphertext,
                    hashlib.sha256).hexdigest()


def slot_derive(secret, salt):
    """PBKDF2 key material for one slot: 32 bytes wrap key + 32 bytes tag key."""
    if not isinstance(secret, bytes):
        raise PackError("slot secret must be bytes")
    return hashlib.pbkdf2_hmac("sha256", secret, salt, PBKDF2_ITERATIONS,
                               dklen=64)


def wrap_key(key, secret, salt=None):
    """Wrap the content key under `secret`; returns a slot dict."""
    salt = salt if salt is not None else secrets.token_bytes(SALT_LEN)
    d = slot_derive(secret, salt)
    wrapped = xor_bytes(key, d[:32])
    tag = hmac.new(d[32:], key, hashlib.sha256).hexdigest()
    return {"salt": salt, "wrapped": wrapped, "tag": tag}


def unwrap_key(slot, secret):
    """Return the content key if `secret` opens `slot`, else None."""
    d = slot_derive(secret, slot["salt"])
    key = xor_bytes(slot["wrapped"], d[:32])
    tag = hmac.new(d[32:], key, hashlib.sha256).hexdigest()
    if hmac.compare_digest(tag, slot["tag"]):
        return key
    return None


def obfuscation_key(*parts):
    """Deterministic key from string parts (obfuscation only, not secrecy)."""
    h = hashlib.sha256()
    for part in parts:
        h.update(part.encode("utf-8") + b"\x00")
    return h.digest()


def verify_token(token):
    """SHA-256("verify" || T) so a check can say PASS/FAIL without answers."""
    return hashlib.sha256(b"verify" + token).hexdigest()


def canonical_token(canonical_output):
    """T = SHA-256 of a check's canonical output (bytes or str)."""
    if isinstance(canonical_output, str):
        canonical_output = canonical_output.encode("utf-8")
    return hashlib.sha256(canonical_output).digest()


def crypto_slot_secret(token, canonical_answer):
    """Slot secret for a crypto gate: T || 0x00 || canon(A)."""
    return token + b"\x00" + canonical_answer.encode("utf-8")


def master_secret(passphrase):
    """Slot secret for the master passphrase."""
    return passphrase.strip().encode("utf-8")


def ensure_secure_file(path):
    """Raise if `path` is missing or readable by group or others."""
    if not os.path.isfile(path):
        raise PackError("passphrase file not found: %s" % path)
    mode = os.stat(path).st_mode & 0o777
    if mode & 0o077:
        raise PackError("passphrase file %s is readable by others; "
                        "chmod 600 it" % path)
