"""
word_replacement_service.py
Ersetzt Wörter basierend auf dem persönlichen Vokabular aus config.json.
Unterstützt einfache Ersetzungen und Regex-Muster.
"""

import re
from typing import Optional
from .config_service import config


class WordReplacementService:
    """
    Wendet benutzerdefinierte Wortersetzungen und persönliches Vokabular an.
    Beispiel: "Mogan" → "Morgan" (Eigenname-Korrektur)
    """

    def __init__(self) -> None:
        self._replacements: list[tuple[re.Pattern, str]] = []
        self._vocabulary: list[str] = []
        self._reload()

    def _reload(self) -> None:
        """Liest Ersetzungen und Vokabular aus der Konfiguration."""
        self._replacements = []

        # Einfache Wort-Ersetzungen aus config
        raw_replacements: list = config.get_list("word_replacements")
        for item in raw_replacements:
            if isinstance(item, dict):
                source = item.get("from", "")
                target = item.get("to", "")
                if source and target:
                    try:
                        pattern = re.compile(
                            r"\b" + re.escape(source) + r"\b",
                            flags=re.IGNORECASE
                        )
                        self._replacements.append((pattern, target))
                    except re.error:
                        pass

        # Persönliches Vokabular (Eigennamen, Fachbegriffe)
        self._vocabulary = config.get_list("personal_vocabulary")
        print(f"[WordReplace] {len(self._replacements)} Ersetzungen, "
              f"{len(self._vocabulary)} Vokabular-Einträge geladen")

    def apply(self, text: str) -> str:
        """
        Wendet alle konfigurierten Ersetzungen auf den Text an.

        Args:
            text: Eingangstext

        Returns:
            Text mit angewandten Ersetzungen
        """
        if not text:
            return text

        # Wort-Ersetzungen anwenden
        for pattern, replacement in self._replacements:
            text = pattern.sub(replacement, text)

        # Persönliches Vokabular: Korrekte Schreibweise erzwingen
        text = self._apply_vocabulary(text)

        return text

    def _apply_vocabulary(self, text: str) -> str:
        """
        Ersetzt fehlerhafte Transkription von Eigennamen.
        Vergleicht phonetisch ähnliche Wörter mit dem Vokabular.
        """
        if not self._vocabulary:
            return text

        words = text.split()
        corrected = []

        for word in words:
            clean_word = re.sub(r"[^a-zA-ZäöüÄÖÜß]", "", word)
            # Prüfe ob ein Vokabular-Eintrag ähnlich ist
            match = self._find_best_match(clean_word)
            if match:
                # Originalformat beibehalten (Satzzeichen etc.)
                corrected.append(word.replace(clean_word, match))
            else:
                corrected.append(word)

        return " ".join(corrected)

    def _find_best_match(self, word: str) -> Optional[str]:
        """
        Einfacher phonetischer Vergleich für Eigenname-Korrektur.
        Verwendet Levenshtein-Distanz (vereinfacht).
        """
        if len(word) < 3:
            return None

        word_lower = word.lower()
        for vocab_word in self._vocabulary:
            vocab_lower = vocab_word.lower()
            # Exakte Übereinstimmung (case-insensitive)
            if word_lower == vocab_lower and word != vocab_word:
                return vocab_word
            # Ähnlichkeit prüfen (max. 2 Zeichen Unterschied)
            if abs(len(word_lower) - len(vocab_lower)) <= 1:
                dist = self._levenshtein(word_lower, vocab_lower)
                if dist == 1:  # Nur 1 Buchstabe Unterschied
                    return vocab_word

        return None

    @staticmethod
    def _levenshtein(s1: str, s2: str) -> int:
        """Berechnet die Levenshtein-Distanz zwischen zwei Strings."""
        if len(s1) < len(s2):
            return WordReplacementService._levenshtein(s2, s1)
        if len(s2) == 0:
            return len(s1)

        prev_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            curr_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = prev_row[j + 1] + 1
                deletions  = curr_row[j] + 1
                subs       = prev_row[j] + (c1 != c2)
                curr_row.append(min(insertions, deletions, subs))
            prev_row = curr_row

        return prev_row[-1]

    def reload(self) -> None:
        """Lädt die Konfiguration neu (nach Änderungen in den Einstellungen)."""
        self._reload()

    def add_replacement(self, source: str, target: str) -> None:
        """Fügt eine neue Ersetzung zur Konfiguration hinzu."""
        replacements = config.get_list("word_replacements")
        replacements.append({"from": source, "to": target})
        config.set("word_replacements", replacements)
        self._reload()

    def add_vocabulary(self, word: str) -> None:
        """Fügt einen Eintrag zum persönlichen Vokabular hinzu."""
        vocabulary = config.get_list("personal_vocabulary")
        if word not in vocabulary:
            vocabulary.append(word)
            config.set("personal_vocabulary", vocabulary)
            self._reload()
