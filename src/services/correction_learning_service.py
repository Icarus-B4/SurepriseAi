"""
correction_learning_service.py
Lernt aus manuellen Korrekturen nach Auto-Inject (Wort-Ersetzungen / Vokabular).
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass
from typing import Callable, Optional

from src.services.config_service import config
from src.services.word_replacement_service import WordReplacementService


@dataclass(frozen=True)
class LearningCandidate:
    source: str
    target: str
    kind: str  # "replacement" | "vocabulary"


class CorrectionLearningService:
    """Extrahiert Lernkandidaten aus Text-Diffs und persistiert sie lokal."""

    _MIN_WORD_LEN = 3
    _MAX_LEVENSHTEIN = 2

    def __init__(self, replacer: WordReplacementService) -> None:
        self._replacer = replacer

    def enabled(self) -> bool:
        return config.get_bool("enable_correction_learning", True)

    def extract_candidates(self, injected: str, edited: str) -> list[LearningCandidate]:
        """Findet Ein-Wort-Ersetzungen zwischen injiziertem und bearbeitetem Text."""
        injected = (injected or "").strip()
        edited = (edited or "").strip()
        if not injected or not edited or injected == edited:
            return []

        inj_words = injected.split()
        edit_words = edited.split()
        matcher = difflib.SequenceMatcher(None, inj_words, edit_words)
        candidates: list[LearningCandidate] = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag != "replace":
                continue
            src_chunk = " ".join(inj_words[i1:i2])
            tgt_chunk = " ".join(edit_words[j1:j2])
            src_parts = src_chunk.split()
            tgt_parts = tgt_chunk.split()
            if not src_parts or not tgt_parts:
                continue
            if len(src_parts) > 3 or len(tgt_parts) > 2:
                continue
            src_clean = re.sub(r"[^a-zA-ZäöüÄÖÜß0-9_-]", "", src_chunk.replace(" ", ""))
            tgt_clean = re.sub(r"[^a-zA-ZäöüÄÖÜß0-9_-]", "", tgt_chunk.replace(" ", ""))
            if not src_clean or not tgt_clean:
                continue
            if len(src_clean) < self._MIN_WORD_LEN or len(tgt_clean) < self._MIN_WORD_LEN:
                continue
            dist = WordReplacementService._levenshtein(
                src_clean.lower(), tgt_clean.lower()
            )
            if src_clean.lower() == tgt_clean.lower():
                if src_chunk != tgt_chunk:
                    kind = "replacement" if " " in src_chunk or " " in tgt_chunk else "vocabulary"
                    candidates.append(
                        LearningCandidate(
                            source=src_chunk, target=tgt_chunk, kind=kind
                        )
                    )
                continue
            if dist > max(self._MAX_LEVENSHTEIN, len(src_clean) // 3):
                continue
            candidates.append(
                LearningCandidate(source=src_chunk, target=tgt_chunk, kind="replacement")
            )

        return self._dedupe(candidates)

    def apply_candidates(
        self, candidates: list[LearningCandidate]
    ) -> list[LearningCandidate]:
        """Persistiert neue Kandidaten und lädt den Replacer neu."""
        applied: list[LearningCandidate] = []
        for cand in candidates:
            if self._already_known(cand):
                continue
            if cand.kind == "vocabulary":
                self._replacer.add_vocabulary(cand.target)
            else:
                self._replacer.add_replacement(cand.source, cand.target)
            applied.append(cand)
        return applied

    def learn_from_edit(
        self,
        injected: str,
        edited: str,
        on_learned: Optional[Callable[[list[LearningCandidate]], None]] = None,
    ) -> list[LearningCandidate]:
        """Extrahiert und speichert Lernkandidaten aus einer manuellen Korrektur."""
        if not self.enabled():
            return []
        candidates = self.extract_candidates(injected, edited)
        applied = self.apply_candidates(candidates)
        if applied and on_learned:
            on_learned(applied)
        return applied

    def _already_known(self, cand: LearningCandidate) -> bool:
        replacements = config.get_list("word_replacements")
        for item in replacements:
            if isinstance(item, dict):
                if (
                    str(item.get("from", "")).lower() == cand.source.lower()
                    and str(item.get("to", "")).lower() == cand.target.lower()
                ):
                    return True
        vocabulary = [str(v).lower() for v in config.get_list("personal_vocabulary")]
        if cand.target.lower() in vocabulary:
            return True
        return False

    @staticmethod
    def _dedupe(candidates: list[LearningCandidate]) -> list[LearningCandidate]:
        seen: set[tuple[str, str]] = set()
        unique: list[LearningCandidate] = []
        for cand in candidates:
            key = (cand.source.lower(), cand.target.lower())
            if key in seen:
                continue
            seen.add(key)
            unique.append(cand)
        return unique
