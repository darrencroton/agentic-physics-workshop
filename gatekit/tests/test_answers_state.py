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

    def test_any_number_percent_and_multipliers(self):
        q = {"kind": "numeric", "lo": 0.0090, "hi": 0.0096, "decimals": 4}
        for text in ("sqrt(0.683*0.317/2500) = 0.0093", "0.93%", "0.0093 (not 2500)"):
            self.assertTrue(answers.matches(q, text), text)
        self.assertFalse(answers.matches(q, "0.0093 1 2 3 4 5 6"))
        self.assertEqual(answers.candidates(q, "1, 2, 2, 3"), ["1.0000", "2.0000", "3.0000"])
        self.assertEqual(len(answers.candidates(q, "1 2 3 4 5 6 7 8")), 6)
        with self.assertRaises(answers.AnswerError):
            answers.candidates(q, "none")
        self.assertEqual(answers.candidates({"kind": "free"}, "x"), [])
        log = {"kind": "numeric-log", "decimals": 4, "lo": 499500, "hi": 500000}
        for text in ("N(N-1)/2 = 499,500", "1000*999/2 = 499500", "500k", "0.5M", "499.5k"):
            self.assertTrue(answers.matches(log, text), text)
        for text in ("500,500", "999000", "1000000", "500 kB"):
            self.assertFalse(answers.matches(log, text), text)

    def test_choice_letter_among_words(self):
        q = {"kind": "choice", "accept": ["c"]}
        for text in ("c", "(c)", "C.", "c - the second only", "c, second only",
                     "c - I think the second is a pass", "I think c"):
            self.assertTrue(answers.matches(q, text), text)
        for text in ("a b", "ab", "the second only", "42"):
            self.assertFalse(answers.matches(q, text), text)

    def test_grid_starts_at_rounded_lo(self):
        q = {"kind": "numeric-log", "decimals": 4, "lo": 499500, "hi": 500000}
        self.assertEqual(answers.accepted_forms(q),
                         ["5.6985", "5.6986", "5.6987", "5.6988", "5.6989", "5.6990"])

    def test_free(self):
        self.assertTrue(answers.matches({"kind": "free"}, "anything"))
        self.assertEqual(answers.accepted_forms({"kind": "free"}), [])

    def test_crypto_slots_from_answers(self):
        token = crypto.canonical_token("output")
        q = {"kind": "numeric", "lo": 0.1, "hi": 0.3, "decimals": 1}
        secrets_list = [crypto.crypto_slot_secret(token, a) for a in answers.accepted_forms(q)]
        pack = packs.build_pack(b"payload", secrets_list, "ex", 1)
        good = crypto.crypto_slot_secret(token, answers.candidates(q, "0.21")[0])
        self.assertEqual(packs.open_pack(pack, [good]), b"payload")
        bad = crypto.crypto_slot_secret(token, answers.candidates(q, "0.4")[0])
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

    def test_talk_prompts_end_in_question_mark(self):
        for good in ("Why?", ["Why?", "How?"]):
            ok = self.manifest()
            ok["levels"][0]["gate"]["talk"] = good
            mf.validate(ok)
        for bad in ("Why.", ["Why?", "How"], 3):
            broken = self.manifest()
            broken["levels"][0]["gate"]["talk"] = bad
            with self.assertRaises(mf.ManifestError, msg=repr(bad)):
                mf.validate(broken)

    def test_old_reflection_keys_are_rejected_with_the_new_names(self):
        for old, new in (("reflection", "talk"), ("reflections", "talk"),
                         ("pre_reflection_note", "note")):
            bad = self.manifest()
            bad["levels"][0]["gate"][old] = "Why?"
            with self.assertRaisesRegex(mf.ManifestError, "'%s' is removed.*'%s'"
                                        % (old, new)):
                mf.validate(bad)
        bad = self.manifest()
        bad["levels"][0]["gate"]["type"] = "crypto-reflection"
        with self.assertRaisesRegex(mf.ManifestError, "crypto-reflection.*'crypto'"):
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
