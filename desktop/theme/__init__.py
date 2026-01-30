from .palette import apply_palette
from .stylesheet import apply_stylesheet

def apply_theme(window=None):
    apply_palette()
    apply_stylesheet(window)