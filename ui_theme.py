"""Shared UI theme tokens for the modern dashboard."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    bg_main: str = "#f3f6fb"
    bg_sidebar: str = "#ffffff"
    bg_panel: str = "#eef2f8"
    bg_card: str = "#ffffff"
    border: str = "#d5deea"
    text_primary: str = "#0f172a"
    text_muted: str = "#64748b"
    accent: str = "#2563eb"
    accent_hover: str = "#1e4fb9"
    success: str = "#16a34a"
    warning: str = "#d97706"
    danger: str = "#dc2626"


THEME = Theme()
