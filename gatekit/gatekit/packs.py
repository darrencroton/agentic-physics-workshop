"""Level packs: a deterministic tar.gz, encrypted, with LUKS-style key slots.

File layout: one JSON header line, a newline, then base64 ciphertext.
"""

import base64
import gzip
import io
import json
import os
import tarfile

from . import crypto

PACK_VERSION = 1


def deterministic_tar(directory):
    """Return tar.gz bytes of `directory` with fixed metadata and sorted entries."""
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb", mtime=0) as gz:
        with tarfile.open(fileobj=gz, mode="w", format=tarfile.PAX_FORMAT) as tar:
            for root, dirs, files in os.walk(directory):
                dirs.sort()
                for name in sorted(files):
                    full = os.path.join(root, name)
                    arcname = os.path.relpath(full, directory)
                    info = tar.gettarinfo(full, arcname=arcname)
                    info.mtime = 0
                    info.uid = info.gid = 0
                    info.uname = info.gname = ""
                    info.mode = 0o755 if os.access(full, os.X_OK) else 0o644
                    if not info.isfile():
                        continue
                    with open(full, "rb") as fh:
                        tar.addfile(info, fh)
    return buf.getvalue()


def extract_tar(data, destination):
    """Extract tar.gz bytes into `destination`, refusing unsafe member paths."""
    os.makedirs(destination, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
        for member in tar.getmembers():
            target = os.path.realpath(os.path.join(destination, member.name))
            if not target.startswith(os.path.realpath(destination) + os.sep):
                raise crypto.PackError("unsafe path in pack: %s" % member.name)
            if not member.isfile():
                continue
            tar.extract(member, destination)


def _b64(data):
    return base64.b64encode(data).decode("ascii")


def _unb64(text):
    if isinstance(text, str):
        text = text.encode("ascii")
    return base64.b64decode(text)


def build_pack(plaintext, secrets_list, exercise, level, key=None, nonce=None):
    """Encrypt `plaintext` with one slot per secret; return pack bytes."""
    if not secrets_list:
        raise crypto.PackError("a pack needs at least one slot")
    key = key or crypto.random_key()
    nonce = nonce or crypto.random_nonce()
    slots = []
    for secret in secrets_list:
        slot = crypto.wrap_key(key, secret)
        slots.append({"salt": _b64(slot["salt"]),
                      "wrapped": _b64(slot["wrapped"]),
                      "tag": slot["tag"]})
    ciphertext = crypto.encrypt(key, nonce, plaintext)
    header = {"version": PACK_VERSION, "exercise": exercise, "level": level,
              "nonce": _b64(nonce), "slots": slots}
    header_bytes = json.dumps(header, sort_keys=True,
                              separators=(",", ":")).encode("utf-8")
    header["mac"] = crypto.compute_mac(key, header_bytes, nonce, ciphertext)
    line = json.dumps(header, sort_keys=True, separators=(",", ":"))
    return line.encode("utf-8") + b"\n" + _b64(ciphertext).encode("ascii")


def read_header(pack_bytes):
    """Return the pack header dict without decrypting."""
    try:
        line, _, _ = pack_bytes.partition(b"\n")
        return json.loads(line.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise crypto.PackError("malformed pack header: %s" % exc)


def open_pack(pack_bytes, secrets_list):
    """Try each secret against each slot; return plaintext or raise PackError."""
    line, _, body = pack_bytes.partition(b"\n")
    header = read_header(pack_bytes)
    if header.get("version") != PACK_VERSION:
        raise crypto.PackError("unsupported pack version")
    try:
        nonce = _unb64(header["nonce"])
        ciphertext = _unb64(body.strip())
        mac = header["mac"]
        slots = header["slots"]
    except (KeyError, ValueError) as exc:
        raise crypto.PackError("malformed pack: %s" % exc)
    key = None
    for secret in secrets_list:
        for slot in slots:
            raw = {"salt": _unb64(slot["salt"]),
                   "wrapped": _unb64(slot["wrapped"]), "tag": slot["tag"]}
            key = crypto.unwrap_key(raw, secret)
            if key is not None:
                break
        if key is not None:
            break
    if key is None:
        raise crypto.PackError("no slot accepted the given secret")
    unsigned = dict(header)
    del unsigned["mac"]
    header_bytes = json.dumps(unsigned, sort_keys=True,
                              separators=(",", ":")).encode("utf-8")
    expected = crypto.compute_mac(key, header_bytes, nonce, ciphertext)
    if not crypto.hmac.compare_digest(expected, mac):
        raise crypto.PackError("pack failed authentication")
    return crypto.decrypt(key, nonce, ciphertext)


def pack_directory(directory, secrets_list, exercise, level):
    """Tar, then encrypt a directory."""
    return build_pack(deterministic_tar(directory), secrets_list, exercise,
                      level)


def unpack_to(pack_bytes, secrets_list, destination):
    """Decrypt a pack and extract it into `destination`."""
    extract_tar(open_pack(pack_bytes, secrets_list), destination)


def seal_json(obj, key, nonce=None):
    """Encrypt a JSON object under a raw key (used for keys.bin obfuscation)."""
    nonce = nonce or crypto.random_nonce()
    plaintext = json.dumps(obj, sort_keys=True).encode("utf-8")
    ciphertext = crypto.encrypt(key, nonce, plaintext)
    mac = crypto.compute_mac(key, b"", nonce, ciphertext)
    return nonce + bytes.fromhex(mac) + ciphertext


def unseal_json(blob, key):
    """Inverse of seal_json."""
    if len(blob) < crypto.NONCE_LEN + 32:
        raise crypto.PackError("sealed blob too short")
    nonce = blob[:crypto.NONCE_LEN]
    mac = blob[crypto.NONCE_LEN:crypto.NONCE_LEN + 32].hex()
    ciphertext = blob[crypto.NONCE_LEN + 32:]
    if not crypto.hmac.compare_digest(
            crypto.compute_mac(key, b"", nonce, ciphertext), mac):
        raise crypto.PackError("sealed blob failed authentication")
    return json.loads(crypto.decrypt(key, nonce, ciphertext).decode("utf-8"))
