"""Exercise manifest loading and validation.

Schema (documented in gatekit/README.md):

{
  "exercise": "tdd-ladder",
  "title": "The TDD Ladder",
  "tool": "tddtool",                      # optional module under .gatekit/
  "other_agents": true,                   # optional bool: ship OTHER-AGENTS.md
  "models": {"default": "haiku", "allowed": ["haiku"]},
  "levels": [
    {"id": 0, "title": "...", "persona": "literal", "target_minutes": 5,
     "files": {"BRIEF.md": "BRIEF.md"},   # pack path -> repo path on unlock
     "gate": {"type": "verified" | "crypto" | "none",
              "condition": "tool.function",            # verified
              "check": "checks/level0.py",             # crypto
              "questions": [{"id": "...", "prompt": "...",
                             "kind": "numeric", "decimals": 2,
                             "lo": 0, "hi": 1,         # crypto kinds
                             "accept": ["sun"],        # keyword/choice kinds
                             "contains": ["psi"],      # keyword: any answer
                                                       # containing a term
                             "validator": "tool.function",    # verified
                             "wrong_hint": "...",             # optional
                             "text_from": "tool.function"}],  # optional
              "talk": "..." | ["...", "..."],   # each ends in "?"; shown,
                                                # never asked
              "post_unlock": "tool.function",
              "note": "..."},                  # printed before the talk
     "start": "ask for step 1"}                # optional: "Next: ... then <start>."
  ]
}
"""

import json
import os

from .answers import canon_keyword

MANIFEST_FILE = "manifest.json"
GATE_TYPES = ("verified", "crypto", "none")
REMOVED_KEYS = {
    "reflection": "use 'talk' (a prompt ending in '?', shown but never asked)",
    "reflections": "use 'talk' (a list of prompts ending in '?')",
    "pre_reflection_note": "use 'note'",
}
PERSONAS = ("literal", "coach", "collaborator")
QUESTION_KINDS = ("keyword", "choice", "numeric", "numeric-log", "free")


class ManifestError(Exception):
    """Raised for a missing or invalid manifest."""


def load_manifest(path):
    """Load and validate a manifest file."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            manifest = json.load(fh)
    except FileNotFoundError:
        raise ManifestError("manifest not found: %s" % path)
    except ValueError as exc:
        raise ManifestError("manifest is not valid JSON: %s" % exc)
    validate(manifest)
    return manifest


def _check_prompt(index, text):
    """Raise ManifestError unless a prompt ends in '?', ':' or ')' (not '.)')."""
    if not isinstance(text, str):
        raise ManifestError("level %d: prompt must be a string: %r"
                            % (index, text))
    end = text.rstrip()
    if not end.endswith(("?", ":", ")")) or end.endswith(".)"):
        raise ManifestError(
            "level %d: prompt must end with '?', ':' or ')' (not '.)'): %r"
            % (index, text))


def _check_talk(index, text):
    """Raise ManifestError unless a talk prompt is a string ending in '?'."""
    if not isinstance(text, str) or not text.rstrip().endswith("?"):
        raise ManifestError("level %d: talk prompt must be a string ending "
                            "in '?': %r" % (index, text))


def _check_contains(index, question, kind):
    """Raise ManifestError unless `contains` is a list of non-empty terms."""
    if "contains" not in question:
        return
    terms = question["contains"]
    if (kind != "keyword" or not isinstance(terms, list)
            or not all(isinstance(t, str) for t in terms)):
        raise ManifestError(
            "level %d: question '%s': contains needs a list of strings on a "
            "keyword question" % (index, question["id"]))
    for term in terms:
        if not canon_keyword(term):
            raise ManifestError(
                "level %d: question '%s': contains term %r has no letters "
                "or digits" % (index, question["id"], term))


def validate(manifest):
    """Raise ManifestError on schema problems."""
    for key in ("exercise", "title", "levels"):
        if key not in manifest:
            raise ManifestError("manifest is missing '%s'" % key)
    levels = manifest["levels"]
    if not isinstance(levels, list) or not levels:
        raise ManifestError("manifest needs a non-empty 'levels' list")
    for index, level in enumerate(levels):
        if level.get("id") != index:
            raise ManifestError("level ids must be 0..n in order")
        if level.get("persona", "coach") not in PERSONAS:
            raise ManifestError("level %d: unknown persona" % index)
        gate = level.get("gate", {"type": "none"})
        if gate.get("type") == "crypto-reflection":
            raise ManifestError("level %d: gate type 'crypto-reflection' is "
                                "removed: use 'crypto'" % index)
        if gate.get("type", "none") not in GATE_TYPES:
            raise ManifestError("level %d: unknown gate type" % index)
        for question in gate.get("questions", []):
            if "id" not in question or "prompt" not in question:
                raise ManifestError("level %d: question needs id and prompt"
                                    % index)
            kind = question.get("kind", "free")
            if kind not in QUESTION_KINDS:
                raise ManifestError("level %d: question '%s': unknown kind '%s'"
                                    % (index, question["id"], kind))
            for key in ("wrong_hint", "text_from"):
                if key in question and not isinstance(question[key], str):
                    raise ManifestError(
                        "level %d: question '%s': %s must be a string"
                        % (index, question["id"], key))
            _check_prompt(index, question["prompt"])
            _check_contains(index, question, kind)
            name = question.get("text_from")
            if name is not None and (name.count(".") != 1
                                     or not all(name.split("."))):
                raise ManifestError(
                    "level %d: question '%s': text_from must look like "
                    "'tool.function'" % (index, question["id"]))
        for key, advice in REMOVED_KEYS.items():
            if key in gate:
                raise ManifestError("level %d: gate key '%s' is removed: %s"
                                    % (index, key, advice))
        talk = gate.get("talk", [])
        if isinstance(talk, str):
            talk = [talk]
        if not isinstance(talk, list):
            raise ManifestError("level %d: talk must be a string or a list of "
                                "strings" % index)
        for text in talk:
            _check_talk(index, text)
        for key, owner in (("note", gate), ("start", level)):
            if key in owner and not isinstance(owner[key], str):
                raise ManifestError("level %d: %s must be a string"
                                    % (index, key))
    if not isinstance(manifest.get("other_agents", False), bool):
        raise ManifestError("'other_agents' must be true or false")
    models = manifest.get("models", {})
    if "allowed" in models and not isinstance(models["allowed"], list):
        raise ManifestError("models.allowed must be a list")


def level_by_id(manifest, level_id):
    """Return the level dict with the given id, or None past the end."""
    levels = manifest["levels"]
    if 0 <= level_id < len(levels):
        return levels[level_id]
    return None


def is_last_level(manifest, level_id):
    """True if `level_id` is the final level."""
    return level_id == len(manifest["levels"]) - 1


def find_root(start=None):
    """Walk up from `start` to the directory holding .gatekit/manifest.json."""
    current = os.path.abspath(start or os.getcwd())
    while True:
        candidate = os.path.join(current, ".gatekit", MANIFEST_FILE)
        if os.path.isfile(candidate):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            raise ManifestError("not inside a workshop repo (no .gatekit/)")
        current = parent


def load_root_manifest(root):
    """Load the manifest of a built workshop repo."""
    return load_manifest(os.path.join(root, ".gatekit", MANIFEST_FILE))
