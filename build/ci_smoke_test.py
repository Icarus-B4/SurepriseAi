"""
ci_smoke_test.py
Schneller CI-Smoke-Test ohne GUI-Start oder Modell-Download.
"""

import compileall
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> None:
    if not compileall.compile_dir(str(ROOT / "src"), quiet=1):
        print("py_compile fehlgeschlagen")
        sys.exit(1)

    from src.version import __version__
    from src.services.config_service import config
    from src.services.media_url_service import is_media_url
    from src.services.dictation_context_service import merge_polish_context
    from src.services.history_export import _as_srt
    from src.services.update_service import parse_version, is_newer

    assert is_media_url("https://www.youtube.com/watch?v=abc")
    assert merge_polish_context("OCR", "Markierung")
    assert _as_srt({"polished": "Test.", "words": 1, "wpm": 60})
    assert parse_version("v0.1.1") > parse_version("0.1.0")
    assert is_newer("v0.2.0", "0.1.0")
    assert config.get_str("global_hotkey")

    print(f"Smoke OK v{__version__}")


if __name__ == "__main__":
    main()
