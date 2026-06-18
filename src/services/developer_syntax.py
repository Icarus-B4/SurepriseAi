"""
developer_syntax.py
Sprachgesteuerte Code-Identifikatoren: camelCase, PascalCase, snake_case, kebab-case.
"""

from __future__ import annotations

import re
from typing import Callable

_WORD = r"[a-zA-Z][a-zA-Z0-9]*"
_WORDS = rf"{_WORD}(?:\s+{_WORD}){{0,7}}"

_PREFIX_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(rf"\bcamel\s*case\s+({_WORDS})", re.I), "camel"),
    (re.compile(rf"\bkamel\s*case\s+({_WORDS})", re.I), "camel"),
    (re.compile(rf"\bpascal\s*case\s+({_WORDS})", re.I), "pascal"),
    (re.compile(rf"\bsnake\s*case\s+({_WORDS})", re.I), "snake"),
    (re.compile(rf"\bkebab\s*case\s+({_WORDS})", re.I), "kebab"),
    (re.compile(rf"\bscreaming\s*snake\s*case\s+({_WORDS})", re.I), "screaming_snake"),
    (re.compile(rf"\bupper\s*snake\s*case\s+({_WORDS})", re.I), "screaming_snake"),
]

_SUFFIX_SPECS: list[tuple[str, str, str]] = [
    (" in ", "camel case", "camel"),
    (" in ", "pascal case", "pascal"),
    (" in ", "snake case", "snake"),
    (" in ", "kebab case", "kebab"),
    (" als ", "camel case", "camel"),
    (" als ", "snake case", "snake"),
]

_CONVERTERS: dict[str, Callable[[list[str]], str]] = {
    "camel": lambda w: _join_camel(w, pascal=False),
    "pascal": lambda w: _join_camel(w, pascal=True),
    "snake": lambda w: "_".join(x.lower() for x in w),
    "kebab": lambda w: "-".join(x.lower() for x in w),
    "screaming_snake": lambda w: "_".join(x.upper() for x in w),
}

_MAX_WORDS = 8


def apply_developer_syntax(text: str) -> str:
    """Wandelt gesprochene Case-Befehle in Code-Identifikatoren um."""
    if not text or not text.strip():
        return text

    result = _apply_suffix_rules(text)
    for pattern, mode in _PREFIX_RULES:
        result = pattern.sub(lambda m, mode=mode: _replace_match(m, mode), result)
    return result


def _apply_suffix_rules(text: str) -> str:
    result = text
    for joiner, case_name, mode in _SUFFIX_SPECS:
        token = f"{joiner}{case_name}"
        token_lower = token.lower()
        out: list[str] = []
        pos = 0
        lower = result.lower()
        while pos < len(result):
            idx = lower.find(token_lower, pos)
            if idx < 0:
                out.append(result[pos:])
                break
            before = result[:idx]
            words = _extract_suffix_identifiers(before)
            converter = _CONVERTERS.get(mode)
            if words and converter:
                _, tail = _split_trailing_words(before, len(words))
                word_start = idx - len(tail)
                out.append(result[pos:word_start])
                out.append(converter(words))
                pos = idx + len(token)
            else:
                out.append(result[pos : idx + len(token)])
                pos = idx + len(token)
            lower = result.lower()
        result = "".join(out)
    return result


def _split_trailing_words(text: str, count: int) -> tuple[str, str]:
    stripped = text.rstrip()
    parts = stripped.split()
    if len(parts) < count:
        return text, ""
    head = " ".join(parts[:-count])
    if head:
        head += " "
    tail = " ".join(parts[-count:])
    return head, tail


def _extract_suffix_identifiers(before: str) -> list[str]:
    """Identifikator-Wörter unmittelbar vor „… in snake case“."""
    text = before.rstrip()
    if not text:
        return []
    raw_words = text.split()
    collected: list[str] = []
    for word in reversed(raw_words):
        clean = re.sub(r"[^a-zA-Z0-9]", "", word)
        if not clean:
            break
        if collected and word[0].isupper() and any(w[0].islower() for w in collected):
            break
        collected.append(clean)
        if len(collected) >= _MAX_WORDS:
            break
    collected.reverse()
    return collected


def _replace_match(match: re.Match[str], mode: str) -> str:
    words = _trim_words(match.group(1))
    if not words:
        return match.group(0)
    converter = _CONVERTERS.get(mode)
    if not converter:
        return match.group(0)
    return converter(words)


def _trim_words(chunk: str) -> list[str]:
    words = chunk.strip().split()
    trimmed: list[str] = []
    for word in words[:_MAX_WORDS]:
        clean = re.sub(r"[^a-zA-Z0-9]", "", word)
        if not clean:
            break
        trimmed.append(clean)
    return trimmed


def _join_camel(words: list[str], *, pascal: bool) -> str:
    if not words:
        return ""
    if pascal:
        return "".join(w[:1].upper() + w[1:].lower() for w in words)
    return words[0].lower() + "".join(w[:1].upper() + w[1:].lower() for w in words[1:])
