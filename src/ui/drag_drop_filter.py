"""
drag_drop_filter.py
Drag & Drop Event Filter für die Dynamic Island.
Abfängt DragEnter- und Drop-Events für Audiodateien oder Links
und leitet diese an die Callback-Funktionen des Fensters weiter.
"""

from PyQt6.QtCore import QObject, QEvent
from src.services.media_url_service import is_media_url


class DragDropFilter(QObject):
    """Event-Filter zur Kapselung der Drag & Drop-Logik."""

    def __init__(self, window):
        super().__init__(window)
        self.window = window

    def eventFilter(self, watched, event) -> bool:
        """Verarbeitet Drag- und Drop-Ereignisse."""
        if event.type() == QEvent.Type.DragEnter:
            if event.mimeData().hasUrls():
                for url in event.mimeData().urls():
                    if url.isLocalFile():
                        path = url.toLocalFile().lower()
                        if path.endswith(('.mp3', '.wav', '.m4a', '.mp4', '.avi', '.mov', '.ogg', '.flac')):
                            event.acceptProposedAction()
                            return True
                    elif is_media_url(url.toString()):
                        event.acceptProposedAction()
                        return True
            return False

        elif event.type() == QEvent.Type.Drop:
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    path_lower = file_path.lower()
                    if path_lower.endswith(('.mp3', '.wav', '.m4a', '.mp4', '.avi', '.mov', '.ogg', '.flac')):
                        if hasattr(self.window, "file_dropped_callback") and self.window.file_dropped_callback:
                            self.window.file_dropped_callback(file_path)
                        break
                else:
                    remote = url.toString()
                    if is_media_url(remote):
                        if hasattr(self.window, "url_dropped_callback") and self.window.url_dropped_callback:
                            self.window.url_dropped_callback(remote)
                        break
            event.acceptProposedAction()
            return True

        return super().eventFilter(watched, event)
