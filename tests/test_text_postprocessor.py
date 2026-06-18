"""Tests für Developer-Syntax, Deutsch-Engine und Postprocessor."""

from src.services.developer_syntax import apply_developer_syntax
from src.services.german_text_engine import apply_german_native, resolve_german_register
from src.services.text_postprocessor import apply_postprocessing


def test_camel_case_prefix():
    text = "Implementiere camel case fetch user handler für die API."
    result = apply_developer_syntax(text)
    assert "fetchUserHandler" in result
    assert "camel case" not in result.lower()


def test_snake_case_suffix():
    text = "Die Variable user id in snake case speichern."
    result = apply_developer_syntax(text)
    assert "user_id" in result
    assert "snake case" not in result.lower()


def test_pascal_case():
    text = "Erstelle pascal case api response model."
    result = apply_developer_syntax(text)
    assert "ApiResponseModel" in result


def test_german_decimal_and_euro():
    text = "Der Preis beträgt 12 komma 5 euro."
    result = apply_german_native(text, "formal")
    assert "12,5" in result
    assert "€" in result


def test_german_sie_register():
    text = "Kannst du mir bitte das schicken?"
    result = apply_german_native(text, "formal")
    assert "Sie" in result or "Ihnen" in result


def test_resolve_register():
    assert resolve_german_register("formal") == "sie"
    assert resolve_german_register("casual") == "du"


def test_postprocessor_developer_disabled():
    text = "camel case foo bar"
    result = apply_postprocessing(text, developer=False)
    assert "camel case" in result.lower()


def test_postprocessor_developer_style_enabled():
    text = "camel case fetch user handler"
    result = apply_postprocessing(text, style="developer", developer=None)
    assert "fetchUserHandler" in result
    assert "camel case" not in result.lower()
