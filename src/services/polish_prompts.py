"""
polish_prompts.py
Ollama-Prompts inkl. optionalem Bildschirmkontext.
"""

from typing import Optional

STYLE_PROMPTS = {
    "business": "Schreibe den Text in einem klaren, sachlichen Business-Stil um. Antworte NUR mit dem Text.",
    "casual": "Bereinige den Text, behalte den lockeren Ton bei. Antworte NUR mit dem Text.",
    "bullet_points": "Wandle den Text in prägnante Stichpunkte um (mit '•'). Antworte NUR mit dem Text.",
    "key_points": "Extrahiere die 3–5 wichtigsten Kernpunkte als kurze Stichpunkte (mit '•'). Antworte NUR mit dem Text.",
    "concise": "Fasse den Text auf das Wesentliche zusammen. Antworte NUR mit dem Text.",
    "long": "Formuliere den Text ausführlicher und flüssiger, ohne neue Fakten zu erfinden. Antworte NUR mit dem Text.",
    "formal": "Formuliere den Text in einem formellen, höflichen Stil um. Antworte NUR mit dem Text.",
}

_CONTEXT_HEADER = (
    "Kontext (nur zur Korrektur von Eigennamen, Fachbegriffen und "
    "Rechtschreibung – nicht zitieren, keine neuen Fakten erfinden):\n"
)


def build_ollama_prompt(
    text: str,
    style: str,
    screen_context: Optional[str] = None,
) -> str:
    """Baut den vollständigen Ollama-Prompt."""
    style_line = STYLE_PROMPTS.get(style, STYLE_PROMPTS["casual"])
    parts = [style_line]
    if screen_context and screen_context.strip():
        parts.append("")
        parts.append(_CONTEXT_HEADER + screen_context.strip())
    parts.append("")
    parts.append(f"Text:\n{text}")
    return "\n".join(parts)
