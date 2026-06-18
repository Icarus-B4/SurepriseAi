"""Tests für Correction Learning und Diff-Helfer."""

from src.services.correction_learning_service import CorrectionLearningService
from src.services.word_replacement_service import WordReplacementService
from src.utils.diff_helper import count_text_changes, texts_differ


class _FakeReplacer:
    def __init__(self):
        self.replacements = []
        self.vocabulary = []

    def add_replacement(self, source, target):
        self.replacements.append((source, target))

    def add_vocabulary(self, word):
        self.vocabulary.append(word)


def test_texts_differ():
    assert texts_differ("Hallo Welt", "Hallo schöne Welt")
    assert not texts_differ(" gleich ", "gleich")


def test_count_text_changes():
    assert count_text_changes("a b c", "a x c") >= 1
    assert count_text_changes("gleich", "gleich") == 0


def test_extract_word_replacement_candidate():
    replacer = _FakeReplacer()
    service = CorrectionLearningService(replacer)  # type: ignore[arg-type]
    candidates = service.extract_candidates(
        "Bitte schick mir die Web Stark Datei",
        "Bitte schick mir die Webstark Datei",
    )
    assert len(candidates) == 1
    assert candidates[0].source == "Web Stark"
    assert candidates[0].target == "Webstark"
    assert candidates[0].kind == "replacement"


def test_levenshtein_replacer_still_works():
    wr = WordReplacementService()
    assert wr._levenshtein("abc", "abd") == 1
