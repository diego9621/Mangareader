def apply_stylesheet(window=None):
    css = """
    QMainWindow { background: #121212; }
    QWidget { color: #eaeaea; font-size: 12px; }
    QLabel { color: #eaeaea; }
    QSplitter::handle { background: #0f0f0f; width: 8px; }
    QScrollArea { border: 0; background: #0f0f0f; }
    QListWidget { background: #141414; border: 1px solid rgba(255,255,255,0.06); border-radius: 14px; padding: 8px; outline: 0; }
    QListWidget::item { border-radius: 12px; padding: 6px; }
    QListWidget::item:selected { background: rgba(59,130,246,0.18); border: 1px solid rgba(59,130,246,0.35); }
    QLineEdit { background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 12px; padding: 9px 12px; }
    QLineEdit:focus { border: 1px solid rgba(230, 73, 73, 0.7); }
    QPushButton { background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.10); border-radius: 12px; padding: 10px 12px; font-weight: 800; }
    QPushButton:hover { background: rgba(255,255,255,0.10); }
    QPushButton:pressed { background: rgba(255,255,255,0.05); }
    QToolButton { background: transparent; border: 1px solid transparent; border-radius: 12px; padding: 8px 12px; font-weight: 800; }
    QToolButton:hover { background: rgba(255,255,255,0.06); }
    QToolButton:checked { background: rgba(255,255,255,0.10); border: 1px solid rgba(255,255,255,0.10); }

    #PrimaryCTA { background: rgba(59,130,246,0.95); border: 1px solid rgba(59,130,246,0.95); color: white; }
    #PrimaryCTA:hover { background: rgba(59,130,246,0.85); }
    #SecondaryCTA { background: rgba(255,255,255,0.06); }

    #CardPrimary { background: rgba(227, 101, 109, 0.95); border: 1px solid rgba(59,130,246,0.95); color: white; border-radius: 12px; padding: 9px 10px; font-weight: 900; }
    #CardPrimary:hover { background: rgba(232, 86, 86, 0.85); }
    #CardSecondary { background: rgba(255,255,255,0.10); border: 1px solid rgba(255,255,255,0.12); border-radius: 12px; padding: 9px 10px; font-weight: 900; }

    QGroupBox { border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; margin-top: 10px; padding: 10px; }
    QGroupBox:title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #bdbdbd; font-weight: 800; }

    QSlider::groove:horizontal { height: 6px; background: rgba(255,255,255,0.10); border-radius: 3px; }
    QSlider::handle:horizontal { width: 16px; margin: -6px 0; border-radius: 8px; background: #3b82f6; }

    QProgressBar { border: 0; background: rgba(255,255,255,0.08); border-radius: 4px; height: 6px; }
    QProgressBar::chunk { background: rgba(59,130,246,0.85); border-radius: 4px; }

    #ChaptersPreview { background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 14px; padding: 6px; }
    #ProgBadge { background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.08); border-radius: 999px; }
    #ProgBadgeText { color: #d6d6d6; font-weight: 900; }
    #Chip { background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.10); border-radius: 999px; padding: 4px 10px; font-weight: 900; color: #d6d6d6; }
    """
    if window:
        window.setStyleSheet(css)