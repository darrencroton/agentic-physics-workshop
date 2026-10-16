import os
import shutil
import tempfile
import unittest

from gatekit import answers, crypto, manifest as mf, packs, state as st


class AnswerTests(unittest.TestCase):
    def test_keyword_synonyms_and_greek(self):
        q = {"kind": "keyword", "accept": ["Ωm", "omega_m", "om"]}
        forms = answers.accepted_forms(q)
        self.assertIn("omegam", forms)
        self.assertIn("om", forms)
        for text in ("Omega_m", " OM ", "Ω m", "omega-m"):
            self.assertTrue(answers.matches(q, text), text)
        self.assertFalse(answers.matches(q, "H0"))

    def test_keyword_contains(self):
        q = {"kind": "keyword", "accept": ["sun", "the J/psi meson"],
             "contains": ["meson", "psi", "charmonium"]}
        for text in ("The J/ψ(1S) meson", "J/psi particle", "charmonium", "Sun"):
            self.assertTrue(answers.matches(q, text), text)
        self.assertFalse(answers.matches(q, "pion"))
        self.assertEqual(answers.accepted_forms(q),
                         ["charmonium", "meson", "psi", "sun"])

    def test_choice(self):
        q = {"kind": "choice", "accept": ["b"]}
        self.assertTrue(answers.matches(q, "B)"))
        self.assertFalse(answers.matches(q, "a"))
        self.assertFalse(answers.matches(q, "ab"))

    def test_numeric_grid(self):
        q = {"kind": "numeric", "lo": 0.0090, "hi": 0.0096, "decimals": 4}
        self.assertEqual(answers.accepted_forms(q),
                         ["0.0090", "0.0091", "0.0092", "0.0093", "0.0094", "0.0095", "0.0096"])
        for text in ("0.0093", "9.3e-3", "0.00934", "≈0.0093 (binomial)", "0.0096"):
            self.assertTrue(answers.matches(q, text), text)
        for text in ("0.0097", "0.008", "none", "0.00895"):
            self.assertFalse(answers.matches(q, text), text)

    def test_numeric_with_units(self):
        q = {"kind": "numeric", "lo": 1.1, "hi": 1.3, "decimals": 1}
        self.assertTrue(answers.matches(q, "1.2 km/s/Mpc"))
        self.assertTrue(answers.matches(q, "-1.2 km/s") is False)

    def test_numeric_log(self):
        q = {"kind": "numeric-log", "lo": 1e3, "hi": 1e5, "decimals": 1}
        self.assertTrue(answers.matches(q, "2e4"))
        self.assertFalse(answers.matches(q, "1e6"))
        self.assertFalse(answers.matches(q, "-5"))

    def test_free(self):
        self.assertTrue(answers.matches({"kind": "free"}, "anything"))
        self.assertEqual(answers.accepted_forms({"kind": "free"}), [])

    def test_crypto_slots_from_answers(self):
        token = crypto.canonical_token("output")
        q = {"kind": "numeric", "lo": 0.1, "hi": 0.3, "decimals": 1}
        secrets_list = [crypto.crypto_slot_secret(token, a) for a in answers.accepted_forms(q)]
        pack = packs.build_pack(b"payload", secrets_list, "ex", 1)
        good = crypto.crypto_slot_secret(token, answers.canonicalise(q, "0.21"))
        self.assertEqual(packs.open_pack(pack, [good]), b"payload")
        bad = crypto.crypto_slot_secret(token, answers.canonicalise(q, "0.4"))
        with self.assertRaises(crypto.PackError):
            packs.open_pack(pack, [bad])
        wrong_token = crypto.crypto_slot_secret(crypto.canonical_token("other"), "0.2")
        with self.assertRaises(crypto.PackError):
            packs.open_pack(pack, [wrong_token])


class ManifestRuleTests(unittest.TestCase):
    @staticmethod
    def manifest(**question):
        question = dict({"id": "q", "prompt": "Which?", "kind": "keyword",
                         "accept": ["a"]}, **question)
        return {"exercise": "x", "title": "X", "levels": [
            {"id": 0, "gate": {"type": "crypto", "questions": [question]}}]}

    def test_contains_rules(self):
        mf.validate(self.manifest(contains=["psi"]))
        for bad in ([""], ["-"], "psi", [1]):
            with self.assertRaises(mf.ManifestError, msg=repr(bad)):
                mf.validate(self.manifest(contains=bad))
        with self.assertRaises(mf.ManifestError):
            mf.validate(self.manifest(kind="choice", contains=["a"]))

    def test_prompt_endings(self):
        for good in ("Which?", "Answer:  ", "Pick one (a-d)"):
            mf.validate(self.manifest(prompt=good))
        for bad in ("Which.", "Pick one (a-d.)", "Pick one (e.g. a.)"):
            with self.assertRaises(mf.ManifestError, msg=bad):
                mf.validate(self.manifest(prompt=bad))
        bad = self.manifest()
        bad["levels"][0]["gate"]["reflection"] = "Why."
        with self.assertRaises(mf.ManifestError):
            mf.validate(bad)


class StateTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.manifest = {"exercise": "ex", "title": "Ex",
                         "models": {"allowed": ["haiku"]},
                         "levels": [{"id": 0, "title": "A", "persona": "literal"},
                                    {"id": 1, "title": "B", "persona": "coach"}]}

    def tearDown(self):
        shutil.rmtree(self.root)

    def test_roundtrip_and_advance(self):
        state = st.initial_state(self.manifest)
        st.save_state(self.root, state)
        loaded = st.load_state(self.root)
        self.assertEqual(loaded["level"], 0)
        self.assertEqual(loaded["persona"], "literal")
        self.assertLess(st.minutes_on_level(loaded), 1)
        st.advance_level(loaded, "coach")
        st.log_failed_attempt(loaded, "check")
        st.save_state(self.root, loaded)
        again = st.load_state(self.root)
        self.assertEqual(again["level"], 1)
        self.assertIsNotNone(again["levels"]["0"]["unlocked"])
        self.assertEqual(again["levels"]["1"]["failed_attempts"], 1)
        self.assertEqual(len(os.listdir(os.path.join(self.root, ".workshop"))), 1)

    def test_corrupt_state(self):
        os.makedirs(os.path.join(self.root, ".workshop"))
        with open(st.state_path(self.root), "w") as fh:
            fh.write("{not json")
        with self.assertRaises(st.StateError):
            st.load_state(self.root)
        with self.assertRaises(st.StateError):
            st.load_state(tempfile.mkdtemp())


if __name__ == "__main__":
    unittest.main()
