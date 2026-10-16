"""Answer canonicalisation and slot-secret enumeration for gate questions.

Question kinds: keyword, choice, numeric, numeric-log, free.
"""

import math
import re
import unicodedata

GREEK_ALIASES = {
    "α": "alpha", "β": "beta", "γ": "gamma", "δ": "delta", "ε": "epsilon",
    "θ": "theta", "λ": "lambda", "μ": "mu", "ν": "nu", "π": "pi",
    "ρ": "rho", "σ": "sigma", "τ": "tau", "φ": "phi", "χ": "chi",
    "ψ": "psi", "ω": "omega", "Ω": "omega", "Λ": "lambda", "Σ": "sigma",
    "Δ": "delta", "Γ": "gamma", "Θ": "theta", "Φ": "phi", "Ψ": "psi",
    "₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4",
}

_NUMBER_RE = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")


class AnswerError(ValueError):
    """Raised when an answer cannot be interpreted for its kind."""


def canon_keyword(text):
    """NFKC, Greek aliases, case-fold, strip whitespace and punctuation."""
    text = "".join(GREEK_ALIASES.get(ch, ch) for ch in text)
    text = unicodedata.normalize("NFKC", text).casefold()
    return "".join(ch for ch in text if ch.isalnum())


def canon_choice(text):
    """Single lower-case letter, e.g. 'B)' -> 'b'."""
    letters = [ch for ch in text.casefold() if ch.isalpha()]
    if len(letters) != 1:
        raise AnswerError("answer with one letter, e.g. a")
    return letters[0]


def parse_number(text):
    """Parse a float from text, ignoring units and other suffixes."""
    text = text.replace(",", "").replace("×10^", "e").replace("x10^", "e")
    text = text.replace("−", "-")
    match = _NUMBER_RE.search(text)
    if not match:
        raise AnswerError("answer with a number, e.g. 0.0093 or 1.2e-3")
    try:
        return float(match.group(0))
    except ValueError:
        raise AnswerError("answer with a number")


def _fmt(value, decimals):
    rounded = round(value, decimals)
    if rounded == 0:
        rounded = 0.0
    return "%.*f" % (decimals, rounded)


def canon_numeric(text, decimals):
    """Round the parsed number to `decimals` places."""
    return _fmt(parse_number(text), decimals)


def canon_numeric_log(text, decimals):
    """Round log10 of the parsed number to `decimals` places."""
    value = parse_number(text)
    if value <= 0:
        raise AnswerError("answer with a positive number")
    return _fmt(math.log10(value), decimals)


def canon_keyword_contains(question, text):
    """Canonical keyword, or the first `contains` term found within it."""
    canon = canon_keyword(text)
    for term in question.get("contains", []):
        term_canon = canon_keyword(term)
        if term_canon in canon:
            return term_canon
    return canon


def canonicalise(question, text):
    """Canonical form of `text` for the question dict, or None for free text."""
    kind = question.get("kind", "free")
    if kind == "keyword":
        return canon_keyword_contains(question, text)
    if kind == "choice":
        return canon_choice(text)
    if kind == "numeric":
        return canon_numeric(text, int(question.get("decimals", 2)))
    if kind == "numeric-log":
        return canon_numeric_log(text, int(question.get("decimals", 1)))
    if kind == "free":
        return None
    raise AnswerError("unknown question kind: %s" % kind)


def _grid(lo, hi, decimals):
    step = 10.0 ** (-decimals)
    n = int(round((hi - lo) / step))
    if n < 0 or n > 100_000:
        raise AnswerError("numeric range too wide for the given decimals")
    return [_fmt(lo + i * step, decimals) for i in range(n + 1)]


def accepted_forms(question):
    """All canonical answer strings a question accepts (empty for free)."""
    kind = question.get("kind", "free")
    if kind == "keyword":
        forms = {canon_keyword_contains(question, s)
                 for s in question.get("accept", [])}
        forms.update(canon_keyword_contains(question, s)
                     for s in question.get("contains", []))
        return sorted(forms)
    if kind == "choice":
        return sorted({canon_choice(s) for s in question["accept"]})
    if kind == "numeric":
        decimals = int(question.get("decimals", 2))
        return _grid(float(question["lo"]), float(question["hi"]), decimals)
    if kind == "numeric-log":
        decimals = int(question.get("decimals", 1))
        return _grid(math.log10(float(question["lo"])),
                     math.log10(float(question["hi"])), decimals)
    if kind == "free":
        return []
    raise AnswerError("unknown question kind: %s" % kind)


def matches(question, text):
    """True if `text` is an accepted answer (local check, no crypto)."""
    try:
        canon = canonicalise(question, text)
    except AnswerError:
        return False
    if canon is None:
        return True
    return canon in accepted_forms(question)
