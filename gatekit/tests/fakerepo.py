"""Build a minimal workshop repo layout in a temporary directory for tests."""

import json
import os
import shutil
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
GATEKIT_DIR = os.path.dirname(HERE)
TEMPLATES = os.path.join(GATEKIT_DIR, "templates")

MANIFEST = {
    "exercise": "fake", "title": "Fake Exercise",
    "models": {"default": "haiku", "allowed": ["haiku"]},
    "levels": [
        {"id": 0, "title": "Zero", "persona": "literal", "target_minutes": 5,
         "gate": {"type": "none"}},
        {"id": 1, "title": "One", "persona": "coach", "target_minutes": 5,
         "gate": {"type": "none"}},
    ],
}

GUARD0 = {"editable": ["src/**", "tests/**", "LOG.md"]}
GUARD_PHASES = {
    "editable": ["LOG.md"],
    "phases": {
        "none": {"editable": ["LOG.md"], "frozen": ["src", "tests"],
                 "message": "Start a cycle with ./tdd red first."},
        "red": {"editable": ["tests/**", "LOG.md"], "frozen": ["src"],
                "message": "src/ is frozen in RED."},
        "green": {"editable": ["src/**", "LOG.md"], "frozen": ["tests"],
                  "message": "Tests are frozen in GREEN. If a test is wrong, "
                             "the group must decide to return to RED."},
        "refactor": {"editable": ["src/**", "LOG.md"], "frozen": ["tests"],
                     "message": "Tests are frozen in REFACTOR."},
    },
}


def make(level=0, guard=None, manifest=None, allowed=None, phase=None):
    """Create the fake repo; return its root path."""
    root = tempfile.mkdtemp(prefix="fakerepo-")
    manifest = manifest or MANIFEST
    os.makedirs(os.path.join(root, ".gatekit"))
    os.symlink(os.path.join(GATEKIT_DIR, "gatekit"),
               os.path.join(root, ".gatekit", "gatekit"))
    with open(os.path.join(root, ".gatekit", "manifest.json"), "w") as fh:
        json.dump(manifest, fh)
    for lvl in range(len(manifest["levels"])):
        src = os.path.join(root, ".gatekit", "levels", str(lvl))
        os.makedirs(src)
        with open(os.path.join(src, "persona.txt"), "w") as fh:
            fh.write("persona: %s\n\nRules for level %d.\n"
                     % (manifest["levels"][lvl]["persona"], lvl))
        with open(os.path.join(src, "hints.json"), "w") as fh:
            json.dump({"tiers": [
                {"unlock_after_minutes": 0, "text": "Hint one for level %d" % lvl},
                {"unlock_after_minutes": 5, "text": "Hint two"},
                {"unlock_after_minutes": 10, "text": "Hint three"}]}, fh)
        with open(os.path.join(src, "guard.json"), "w") as fh:
            json.dump(guard or GUARD0, fh)
    shutil.copytree(os.path.join(TEMPLATES, ".claude"),
                    os.path.join(root, ".claude"))
    shutil.copy(os.path.join(TEMPLATES, "gate"), os.path.join(root, "gate"))
    os.chmod(os.path.join(root, "gate"), 0o755)
    for name in ("LOG.md", "README.md", "Makefile"):
        with open(os.path.join(root, name), "w") as fh:
            fh.write("# %s\n" % name)
    os.makedirs(os.path.join(root, "src"))
    os.makedirs(os.path.join(root, "tests"))
    os.makedirs(os.path.join(root, ".vault"))
    with open(os.path.join(root, ".vault", "level1.pack"), "wb") as fh:
        fh.write(b"{}\n")
    from gatekit import cli
    cli.reset_workshop(root, manifest)
    if level or allowed is not None:
        from gatekit import state as st
        state = st.load_state(root)
        while state["level"] < level:
            st.advance_level(state, manifest["levels"][state["level"] + 1]["persona"])
        if allowed is not None:
            state["allowed_models"] = allowed
        st.save_state(root, state)
    for lvl in range(1, level + 1):
        shutil.copytree(os.path.join(root, ".gatekit", "levels", str(lvl)),
                        os.path.join(root, ".workshop", "levels", str(lvl)))
    if phase is not None:
        os.makedirs(os.path.join(root, ".tdd"), exist_ok=True)
        with open(os.path.join(root, ".tdd", "phase"), "w") as fh:
            fh.write(phase + "\n")
    return root


def env_for(root):
    """Environment with CLAUDE_PROJECT_DIR set for hooks."""
    env = dict(os.environ)
    env["CLAUDE_PROJECT_DIR"] = root
    return env
