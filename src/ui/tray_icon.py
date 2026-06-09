"""
tray_icon.py
System-Tray-Icon (QSystemTrayIcon) für SurepriseAi in PyQt6.
Ermöglicht Steuerung im Hintergrund und bietet Schnellzugriff auf Stile, Einstellungen und Beenden.
"""

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtCore import Qt, pyqtSignal
from src.services.config_service import config
from src.ui.design_tokens import Colors


class SurepriseTrayIcon(QSystemTrayIcon):
    # Signale für App-Controller
    toggle_island = pyqtSignal()
    open_settings = pyqtSignal()
    quit_app = pyqtSignal()
    style_selected = pyqtSignal(str)
    toggle_recording = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setToolTip("SurepriseAi")
        
        # Icon zeichnen
        self.setIcon(self._create_tray_icon())
        
        # Klick-Handler
        self.activated.connect(self._on_activated)
        self._init_menu()

    def _create_tray_icon(self) -> QIcon:
        """Zeichnet ein minimalistisches System-Tray-Icon (Dynamic-Island-Form)."""
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Dunkler Hintergrund (Kreis)
        painter.setBrush(QColor("#0D0D0F"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, 16, 16)
        
        # Kleine Kapsel in der Mitte (Indigo Akzentfarbe)
        painter.setBrush(QColor("#6366F1"))
        painter.drawRoundedRect(3, 6, 10, 4, 2, 2)
        
        painter.end()
        return QIcon(pixmap)

    def _init_menu(self):
        """Initialisiert das QSS-gestylte Kontextmenü."""
        self.menu = QMenu()
        self.menu.setStyleSheet(f"""
            QMenu {{
                background-color: {Colors.SURFACE_HEX};
                border: 1px solid {Colors.BORDER_HEX};
                border-radius: 6px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 6px 24px 6px 24px;
                color: {Colors.TEXT_PRIMARY_HEX};
                font-family: "Segoe UI";
                font-size: 12px;
            }}
            QMenu::item:selected {{
                background-color: {Colors.SURFACE_ELEVATED};
                border-radius: 4px;
            }}
        """)
        
        # Diktat-Aktion
        self.record_action = self.menu.addAction("🎙 Diktat starten")
        self.record_action.triggered.connect(self.toggle_recording.emit)
        
        self.menu.addSeparator()
        
        # Stil-Submenü
        self.style_menu = self.menu.addMenu("🎨 Polishing-Stil")
        self.style_menu.setStyleSheet(self.menu.styleSheet())
        
        self.style_actions = {}
        styles = [
            ("casual", "Bereinigen"),
            ("business", "Business"),
            ("bullet_points", "Stichpunkte"),
            ("concise", "Kompakt"),
            ("formal", "Formell"),
        ]
        
        for key, label in styles:
            action = self.style_menu.addAction(label)
            action.setCheckable(True)
            action.triggered.connect(lambda checked, k=key: self.style_selected.emit(k))
            self.style_actions[key] = action
            
        self.update_menu_states()
        
        self.menu.addSeparator()
        
        # Einstellungen
        settings_action = self.menu.addAction("⚙ Einstellungen")
        settings_action.triggered.connect(self.open_settings.emit)
        
        # Beenden
        quit_action = self.menu.addAction("❌ Beenden")
        quit_action.triggered.connect(self.quit_app.emit)
        
        self.setContextMenu(self.menu)

    def update_menu_states(self):
        """Synchronisiert die Checkmarks im Submenü mit der aktuellen Konfiguration."""
        active_style = config.selected_style
        for key, action in self.style_actions.items():
            action.setChecked(key == active_style)

    def set_recording_state(self, is_recording: bool):
        """Aktualisiert die Beschriftung der Aufnahme-Aktion."""
        if is_recording:
            self.record_action.setText("⏹ Aufnahme stoppen")
        else:
            self.record_action.setText("🎙 Diktat starten")

    def _on_activated(self, reason):
        """Ein- und Ausblenden der Dynamic Island bei Doppelklick."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.toggle_island.emit()
