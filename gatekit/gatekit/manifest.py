"""Exercise manifest loading and validation.

Schema (documented in gatekit/README.md):

{
  "exercise": "tdd-ladder",
  "title": "The TDD Ladder",
  "tool": "tddtool",                      # optional module under .gatekit/
  "models": {"default": "haiku", "allowed": ["haiku"]},
  "levels": [
    {"id": 0, "title": "...", "persona": "literal", "target_minutes": 5,
     "files": {"BRIEF.md": "BRIEF.md"},   # pack path -> repo path on unlock
     "gate": {"type": "verified" | "crypto" | "crypto-reflection" | "none",
              "condition": "tool.function",            # verified
              "check": "checks/level0.py",             # crypto
              "questions": [{"id": "...", "prompt": "...",
                             "kind": "numeric", "decimals": 2,
                             "lo": 0, "hi": 1,         # crypto kinds
                             "validator": "tool.function",    # verified
                             "wrong_hint": "...",             # optional
                             "text_from": "tool.function"}],  # optional
              "reflection": "..." | "reflections": ["...", "..."],
              "post_unlock": "tool.function",
              "pre_reflection_note": "..."}}
  ]
}
"""

import json
import os

MANIFEST_FILE = "manifest.json"
GATE_TYPES = ("verified", "crypto", "crypto-reflection", "none")
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
            name = question.get("text_from")
            if name is not None and (name.count(".") != 1
                                     or not all(name.split("."))):
                raise ManifestError(
                    "level %d: question '%s': text_from must look like "
                    "'tool.function'" % (index, question["id"]))
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
