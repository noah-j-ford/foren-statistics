"""
Uses:
    Standardization.xlsx
"""

import difflib
import re
from functools import lru_cache

import pandas as pd

from config import YEAR, NAME_CORRECTIONS_PATH

# ======================================================================
# Name / school lookups (from Standardization.xlsx)
# ======================================================================

def _rules_to_dict(df, col1, col2):
    """Two columns -> dict, skipping blank rows and trimming stray whitespace."""
    df = df.dropna(subset=[col1, col2])
    return dict(zip(df[col1].str.strip(), df[col2].str.strip()))


@lru_cache(maxsize=1)
def load_name_corrections(path=NAME_CORRECTIONS_PATH):
    """Reads Name Corrections.xlsx once per process, no matter how many Standardizers are created."""
    sheets = pd.read_excel(path, sheet_name=None, dtype=str)
    return {
        'names': _rules_to_dict(sheets["Names"], "Raw Text", "Standardized"),
        'schools': _rules_to_dict(sheets["Schools"], "Raw Text", "Standardized"),
        'classes': _rules_to_dict(sheets["Schools"], "Standardized", f"Class {YEAR}"),
        'districts': _rules_to_dict(sheets["Schools"], "Standardized", f"District {YEAR}"),
        'dropped': sheets["Dropped"],
    }


# ======================================================================
# Event names: rules + fuzzy fallback
#   1. Normalize   lowercase, drop punctuation, collapse whitespace
#   2. Split       pull out the level (novice / varsity / A-2 / A-3); match only event words
#   3. Rules       keyword regexes; two different events matching = ambiguous
#   4. Fuzzy       typo-tolerant token match (difflib) against event keywords
#   5. Give up     raise EventMatchError (or return the raw name) and record it for review
# ======================================================================

class EventMatchError(ValueError):
    """Raised when an event name can't be matched to exactly one event."""

# (regex on the normalized, level-stripped string, event code)
# Every rule that matches is collected; more than one distinct code means "ambiguous".
_EVENT_RULES = [
    (re.compile(r"dramatic|serious|\bdi\b"), "DI"),
    (re.compile(r"\bhumo?u?r|\bhi\b"), "HI"),
    (re.compile(r"poetry|\bpoe\b"), "POE"),
    (re.compile(r"program|\bpoi\b"), "POI"),
    (re.compile(r"\bduo\b|duet"), "DUO"),
    (re.compile(r"\bdrama\b|\boid\b"), "OID"),
    (re.compile(r"orator|persuas|original|\boo\b"), "OO"),
    (re.compile(r"inform|\binf\b|\binfo\b"), "INF"),
    (re.compile(r"entertain|\bent\b"), "ENT"),
    (re.compile(r"extemp|\bext\b"), "EXT"),
    (re.compile(r"imprompt|\bimp\b"), "IMP"),
]

# Keywords for the typo-tolerant fallback (whole tokens, compared with difflib).
_EVENT_FUZZY_KEYWORDS = {
    "dramatic": "DI", "serious": "DI",
    "humorous": "HI", "humourous": "HI", "humor": "HI",
    "poetry": "POE",
    "program": "POI",
    "duo": "DUO", "duet": "DUO",
    "drama": "OID",
    "oratory": "OO", "persuasive": "OO", "original": "OO",
    "informative": "INF",
    "entertainment": "ENT",
    "extemporaneous": "EXT", "extemp": "EXT",
    "impromptu": "IMP",
}
_FUZZY_CUTOFF = 0.8
_MIN_FUZZY_LEN = 4  # short tokens ("of", "oral", "duo") are too easy to mis-match

_LEVEL_STRIP = re.compile(r"\b(novice|nov|varsity|jv)\b|\ba \d\b")
_NOVICE = re.compile(r"\bnovice\b|\bnov\b|^n (?=\S)")

_UNMATCHED_EVENTS = set()


def _normalize_event_text(name):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", name.lower())).strip()


def _event_codes(name):
    """Returns (set of matching event codes, whether the name is novice). Pure: records nothing."""
    if not isinstance(name, str):
        return set(), False

    text = _normalize_event_text(name)
    novice = bool(_NOVICE.search(text))
    text = _LEVEL_STRIP.sub(" ", re.sub(r"^n (?=\S)", "", text))
    text = re.sub(r"\s+", " ", text).strip()

    codes = {code for pattern, code in _EVENT_RULES if pattern.search(text)}
    if not codes:  # fuzzy fallback
        for token in text.split():
            if len(token) < _MIN_FUZZY_LEN:
                continue
            close = difflib.get_close_matches(token, _EVENT_FUZZY_KEYWORDS, n=1, cutoff=_FUZZY_CUTOFF)
            if close:
                codes.add(_EVENT_FUZZY_KEYWORDS[close[0]])
    return codes, novice


def _match_event(name, keep_novice, on_unmatched):
    if on_unmatched not in ("raise", "return"):
        raise ValueError("on_unmatched must be 'raise' or 'return'")

    codes, novice = _event_codes(name)

    if len(codes) == 1:
        code = next(iter(codes))
        return f"N-{code}" if (novice and keep_novice) else code

    _UNMATCHED_EVENTS.add(name if isinstance(name, str) else repr(name))
    if on_unmatched == "return":
        return name
    reason = "ambiguous (" + ", ".join(sorted(codes)) + ")" if codes else "no match"
    raise EventMatchError(f"Could not standardize event name {name!r}: {reason}")


# ======================================================================
# Standardizer
# ======================================================================

#Add in a rule of "If string starts with 'Mc', capitalize 3rd letter (McCormick, McKnight, etc.)
class Standardizer:
    def __init__(self):
        # Sensitive lookups come from the private Excel file
        corrections = load_name_corrections()
        self.names = corrections["names"]
        self.schools = corrections["schools"]
        self.classes = corrections["classes"]
        self.districts = corrections["districts"]
        self.dropped = corrections["dropped"]

    def standardize_name(self, name):
        """Standardizes the name of a competitor, judge, or OID"""
        return self.names.get(name, name)

    def standardize_school_name(self, name):
        """Standardizes a school name."""
        return self.schools.get(name, name)

    def standardize_event_name(self, name, keep_novice=True, on_unmatched="return"):
        """
        Standardizes an event name to DI, HI, POE, POI, DUO, OID, OO, INF, ENT, EXT, or IMP.
        keep_novice=True returns "N-<code>" for novice events.
        on_unmatched="raise" raises EventMatchError for unknown names; "return" passes the raw name through.
        """
        return _match_event(name, keep_novice, on_unmatched)

    def is_event_name(self, name):
        """
        True if the text looks like an event name (even an ambiguous one). Never raises and
        never records anything as unmatched, so it is safe to run over a whole column.
        """
        codes, _ = _event_codes(name)
        return len(codes) >= 1

    def unmatched_events(self):
        """Raw event names that couldn't be matched this run (for review / adding rules)."""
        return sorted(_UNMATCHED_EVENTS)