import json
import os
import shutil
import tempfile
import unittest

from gatekit import crypto, packs


class CryptoTests(unittest.TestCase):
    def test_keystream_roundtrip(self):
        key, nonce = crypto.random_key(), crypto.random_nonce()
        data = os.urandom(1000)
        self.assertEqual(crypto.decrypt(key, nonce, crypto.encrypt(key, nonce, data)), data)

    def test_slot_wrap_unwrap(self):
        key = crypto.random_key()
        slot = crypto.wrap_key(key, b"secret")
        self.assertEqual(crypto.unwrap_key(slot, b"secret"), key)
        self.assertIsNone(crypto.unwrap_key(slot, b"wrong"))

    def test_verify_token(self):
        token = crypto.canonical_token('{"h0": 70.0}')
        self.assertEqual(len(token), 32)
        self.assertNotEqual(crypto.verify_token(token), token.hex())


class PackTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.src = os.path.join(self.tmp, "level")
        os.makedirs(os.path.join(self.src, "sub"))
        with open(os.path.join(self.src, "BRIEF.md"), "w") as fh:
            fh.write("# Brief\n")
        with open(os.path.join(self.src, "sub", "data.txt"), "w") as fh:
            fh.write("1 2 3\n")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_deterministic_tar(self):
        a = packs.deterministic_tar(self.src)
        os.utime(os.path.join(self.src, "BRIEF.md"), (0, 0))
        b = packs.deterministic_tar(self.src)
        self.assertEqual(a, b)

    def test_roundtrip_and_master(self):
        pack = packs.pack_directory(self.src, [b"answer-secret", crypto.master_secret("pass\n")], "ex", 1)
        self.assertEqual(packs.read_header(pack)["level"], 1)
        for secret in (b"answer-secret", crypto.master_secret("pass")):
            out = os.path.join(self.tmp, "out-%d" % len(secret))
            packs.unpack_to(pack, [secret], out)
            with open(os.path.join(out, "sub", "data.txt")) as fh:
                self.assertEqual(fh.read(), "1 2 3\n")
        with self.assertRaises(crypto.PackError):
            packs.open_pack(pack, [b"nope"])

    def test_tamper_fails_mac(self):
        pack = packs.pack_directory(self.src, [b"s"], "ex", 1)
        header, _, body = pack.partition(b"\n")
        flipped = bytearray(packs._unb64(body))
        flipped[5] ^= 0x01
        tampered = header + b"\n" + packs._b64(bytes(flipped)).encode()
        with self.assertRaises(crypto.PackError):
            packs.open_pack(tampered, [b"s"])
        bad_header = header.replace(b'"level":1', b'"level":2') + b"\n" + body
        with self.assertRaises(crypto.PackError):
            packs.open_pack(bad_header, [b"s"])

    def test_malformed_slot_raises_pack_error(self):
        pack = packs.pack_directory(self.src, [b"s"], "ex", 1)
        header, _, body = pack.partition(b"\n")
        data = json.loads(header)
        for broken in ({}, {"salt": "!!", "wrapped": "", "tag": ""},
                       {"salt": "", "wrapped": "", "tag": None}):
            data["slots"] = [broken]
            with self.assertRaises(crypto.PackError):
                packs.open_pack(json.dumps(data).encode() + b"\n" + body, [b"s"])

    def test_seal_json(self):
        key = crypto.obfuscation_key("a", "b")
        blob = packs.seal_json({"k": [1, 2]}, key)
        self.assertEqual(packs.unseal_json(blob, key), {"k": [1, 2]})
        with self.assertRaises(crypto.PackError):
            packs.unseal_json(blob, crypto.obfuscation_key("x"))

    def test_unsafe_member_rejected(self):
        import io
        import tarfile
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:gz") as tar:
            info = tarfile.TarInfo("../escape.txt")
            info.size = 1
            tar.addfile(info, io.BytesIO(b"x"))
        with self.assertRaises(crypto.PackError):
            packs.extract_tar(buf.getvalue(), os.path.join(self.tmp, "x"))


if __name__ == "__main__":
    unittest.main()
