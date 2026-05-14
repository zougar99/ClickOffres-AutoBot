"""Proxy list parsing, ranking and reporting helpers."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

from form_engine import ProxyConfig


@dataclass
class ProxyCheckResult:
    index: int
    raw_input: str
    server: str
    ok: bool
    elapsed_ms: int
    ip: str
    country: str
    details: str


def parse_proxy_line(line: str) -> ProxyConfig | None:
    raw = line.strip()
    if not raw:
        return None

    if "://" in raw:
        parsed = urlparse(raw)
        if not parsed.hostname or not parsed.port:
            return None
        scheme = (parsed.scheme or "").lower()
        if scheme not in {"http", "https", "socks5"}:
            # Chromium proxy support is reliable with http/https/socks5.
            return None
        server = f"{scheme}://{parsed.hostname}:{parsed.port}"
        return ProxyConfig(
            enabled=True,
            server=server,
            username=parsed.username or "",
            password=parsed.password or "",
        )

    parts = raw.split(":")
    if len(parts) == 2:
        host, port = parts
        if not host or not port:
            return None
        return ProxyConfig(enabled=True, server=f"http://{host}:{port}")

    if len(parts) == 4:
        host, port, username, password = parts
        if not host or not port:
            return None
        return ProxyConfig(
            enabled=True,
            server=f"http://{host}:{port}",
            username=username,
            password=password,
        )

    return None


def normalize_proxy_entries(raw_text: str) -> list[str]:
    seen: set[str] = set()
    entries: list[str] = []
    for line in raw_text.splitlines():
        item = line.strip()
        if not item or item in seen:
            continue
        entries.append(item)
        seen.add(item)
    return entries


def pick_best_proxy(results: Iterable[ProxyCheckResult]) -> ProxyCheckResult | None:
    ok_results = [r for r in results if r.ok]
    if not ok_results:
        return None
    return min(ok_results, key=lambda x: x.elapsed_ms)


def export_proxy_results_csv(results: Iterable[ProxyCheckResult], path: Path) -> None:
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["index", "raw_input", "server", "ok", "elapsed_ms", "ip", "country", "details"],
        )
        writer.writeheader()
        for item in results:
            writer.writerow(
                {
                    "index": item.index,
                    "raw_input": item.raw_input,
                    "server": item.server,
                    "ok": item.ok,
                    "elapsed_ms": item.elapsed_ms,
                    "ip": item.ip,
                    "country": item.country,
                    "details": item.details,
                }
            )
