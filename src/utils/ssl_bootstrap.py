"""
ssl_bootstrap.py
Stellt SSL-Zertifikate für urllib in Dev- und PyInstaller-Bundles bereit.
"""

import os
import sys


def certifi_bundle_path() -> str | None:
    """Pfad zum CA-Bundle (certifi), inkl. PyInstaller _MEIPASS."""
    if getattr(sys, "frozen", False):
        bundled = os.path.join(sys._MEIPASS, "certifi", "cacert.pem")
        if os.path.isfile(bundled):
            return bundled
    try:
        import certifi

        return certifi.where()
    except ImportError:
        return None


def configure_ssl_environment() -> None:
    """Setzt Umgebungsvariablen für HTTPS vor allen API-Aufrufen."""
    bundle = certifi_bundle_path()
    if bundle:
        os.environ.setdefault("SSL_CERT_FILE", bundle)
        os.environ.setdefault("REQUESTS_CA_BUNDLE", bundle)
