from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    bg_main: str = "#0f1419"
    bg_sidebar: str = "#1a1f2e"
    bg_panel: str = "#151b28"
    bg_card: str = "#1e2738"
    border: str = "#2a3548"
    text_primary: str = "#e8edf5"
    text_muted: str = "#8892a8"
    accent: str = "#3b82f6"
    accent_hover: str = "#2563eb"
    accent_soft: str = "#1e3a5f"
    success: str = "#22c55e"
    warning: str = "#f59e0b"
    danger: str = "#ef4444"


THEME = Theme()
