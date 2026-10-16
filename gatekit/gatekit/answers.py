"""Answer canonicalisation and slot-secret enumeration for gate questions.

Question kinds: keyword, choice, numeric, numeric-log, free.

A typed answer maps to a list of candidate canonical forms (`candidates`): one
per number for the numeric kinds (the last MAX_NUMBERS found), one for keyword
and choice questions, none for free text. An answer is accepted if any
candidate is an accepted form.
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

MAX_NUMBERS = 6
_NUMBER_RE = re.compile(
    r"([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)"
    r"(?:\s*(%)|\s*([kKM])(?![^\W\d_]))?")
_MULTIPLIERS = {"k": 1e3, "K": 1e3, "M": 1e6}


class AnswerError(ValueError):
    """Raised when an answer cannot be interpreted for its kind."""


def canon_keyword(text):
    """NFKC, Greek aliases, case-fold, strip whitespace and punctuation."""
    text = "".join(GREEK_ALIASES.get(ch, ch) for ch in text)
    text = unicodedata.normalize("NFKC", text).casefold()
    return "".join(ch for ch in text if ch.isalnum())


def canon_choice(text):
    """Option letter: a leading one ('c - I think the second'), else the only
    stand-alone one ('the answer is c'); 'i' is never an option."""
    tokens = re.findall(r"[^\W\d_]+", text.casefold())
    letters = [tok for tok in tokens if len(tok) == 1 and tok != "i"]
    if tokens and tokens[0] in letters:
        return tokens[0]
    if len(set(letters)) != 1:
        raise AnswerError("answer with one letter, e.g. a")
    return letters[0]


def numbers(text):
    """The last MAX_NUMBERS finite numbers in `text` (results usually come
    last); '%' divides by 100, k and M multiply (when not followed by a
    letter)."""
    text = text.replace(",", "").replace("×10^", "e").replace("x10^", "e")
    text = text.replace("−", "-")
    found = []
    for number, percent, multiplier in _NUMBER_RE.findall(text):
        value = float(number)
        if percent:
            value /= 100.0
        elif multiplier:
            value *= _MULTIPLIERS[multiplier]
        if math.isfinite(value):
            found.append(value)
    return found[-MAX_NUMBERS:]


def _numeric_candidates(text, decimals, log):
    """Canonical form of each number, de-duplicated, in order."""
    values = numbers(text)
    if not values:
        raise AnswerError("answer with a number, e.g. 0.0093 or 1.2e-3")
    if log:
        values = [math.log10(v) for v in values if v > 0]
        if not values:
            raise AnswerError("answer with a positive number")
    return list(dict.fromkeys(_fmt(v, decimals) for v in values))


def _fmt(value, decimals):
    rounded = round(value, decimals)
    if rounded == 0:
        rounded = 0.0
    return "%.*f" % (decimals, rounded)


def canon_keyword_contains(question, text):
    """Canonical keyword, or the first `contains` term found within it."""
    canon = canon_keyword(text)
    for term in question.get("contains", []):
        term_canon = canon_keyword(term)
        if term_canon in canon:
            return term_canon
    return canon


def candidates(question, text):
    """Canonical forms to try for `text`: none for free, else at least one."""
    kind = question.get("kind", "free")
    if kind == "keyword":
        return [canon_keyword_contains(question, text)]
    if kind == "choice":
        return [canon_choice(text)]
    if kind == "numeric":
        return _numeric_candidates(text, int(question.get("decimals", 2)), False)
    if kind == "numeric-log":
        return _numeric_candidates(text, int(question.get("decimals", 1)), True)
    if kind == "free":
        return []
    raise AnswerError("unknown question kind: %s" % kind)


def _grid(lo, hi, decimals):
    step = 10.0 ** (-decimals)
    lo = round(lo, decimals)
    n = int(round((round(hi, decimals) - lo) / step))
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
        forms = candidates(question, text)
    except AnswerError:
        return False
    if not forms:
        return True
    accepted = set(accepted_forms(question))
    return any(form in accepted for form in forms)
