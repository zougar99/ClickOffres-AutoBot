"""Persistence helpers for profiles and templates."""

from __future__ import annotations

import json
from pathlib import Path

from form_engine import ProxyConfig


class ProfileStudioStore:
    def __init__(
        self,
        profiles_file: Path,
        templates_file: Path,
        default_data: dict,
        default_settings: dict,
        default_templates: dict,
    ):
        self.profiles_file = profiles_file
        self.templates_file = templates_file
        self.default_data = default_data
        self.default_settings = default_settings
        self.default_templates = default_templates

    def load_profiles(self, seed_user_data: dict, seed_proxy: ProxyConfig) -> dict:
        if self.profiles_file.exists():
            try:
                with open(self.profiles_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict) and data:
                    return data
            except Exception:
                pass
        return {
            "default": {
                "user_data": dict(seed_user_data),
                "proxy": seed_proxy.to_dict(),
                "settings": dict(self.default_settings),
            }
        }

    def save_profiles(self, profiles: dict) -> None:
        with open(self.profiles_file, "w", encoding="utf-8") as f:
            json.dump(profiles, f, ensure_ascii=False, indent=2)

    def load_templates(self) -> dict:
        if self.templates_file.exists():
            try:
                with open(self.templates_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                if isinstance(loaded, dict):
                    return {**self.default_templates, **loaded}
            except Exception:
                pass
        return dict(self.default_templates)

    def save_templates(self, templates: dict) -> None:
        with open(self.templates_file, "w", encoding="utf-8") as f:
            json.dump(templates, f, ensure_ascii=False, indent=2)
