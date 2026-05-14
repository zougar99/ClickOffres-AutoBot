"""
Form analysis and auto-fill engine using Playwright.
Detects form fields on a webpage and fills them with user-provided data.
"""

import asyncio
import json
import re
from dataclasses import dataclass, field
from typing import Optional

from playwright.async_api import async_playwright, Page, Browser, BrowserContext


@dataclass(frozen=True)
class DeviceProfile:
    name: str
    viewport_width: int
    viewport_height: int
    user_agent: str
    locale: str = "fr-FR"


DEVICE_PROFILES: dict[str, DeviceProfile] = {
    "Windows": DeviceProfile(
        name="Windows",
        viewport_width=1366,
        viewport_height=768,
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
    ),
    "macOS": DeviceProfile(
        name="macOS",
        viewport_width=1440,
        viewport_height=900,
        user_agent=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6_3) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
    ),
    "Android": DeviceProfile(
        name="Android",
        viewport_width=412,
        viewport_height=915,
        user_agent=(
            "Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
        ),
    ),
    "iOS": DeviceProfile(
        name="iOS",
        viewport_width=390,
        viewport_height=844,
        user_agent=(
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 "
            "Mobile/15E148 Safari/604.1"
        ),
    ),
    "Linux": DeviceProfile(
        name="Linux",
        viewport_width=1366,
        viewport_height=768,
        user_agent=(
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
    ),
}


FIELD_PATTERNS = {
    "first_name": [
        r"first.?name", r"fname", r"prenom", r"prénom", r"given.?name",
        r"first", r"vorname", r"nombre"
    ],
    "last_name": [
        r"last.?name", r"lname", r"nom", r"family.?name", r"surname",
        r"last", r"nachname", r"apellido"
    ],
    "full_name": [
        r"full.?name", r"your.?name", r"^name$", r"nom.?complet",
        r"complete.?name", r"display.?name"
    ],
    "email": [
        r"e?.?mail", r"courriel", r"correo"
    ],
    "phone": [
        r"phone", r"tel", r"téléphone", r"telephone", r"mobile",
        r"cell", r"gsm", r"numero", r"numéro"
    ],
    "address": [
        r"address", r"adresse", r"street", r"rue", r"addr",
        r"address.?line.?1", r"street.?address"
    ],
    "city": [
        r"city", r"ville", r"town", r"ciudad", r"stadt"
    ],
    "zip_code": [
        r"zip", r"postal", r"code.?postal", r"postcode", r"plz"
    ],
    "country": [
        r"country", r"pays", r"land", r"país"
    ],
    "company": [
        r"company", r"entreprise", r"société", r"societe", r"organization",
        r"organisation", r"firma", r"employer"
    ],
    "job_title": [
        r"job.?title", r"title", r"poste", r"fonction", r"position",
        r"role", r"intitulé"
    ],
    "website": [
        r"website", r"site.?web", r"url", r"homepage", r"web"
    ],
    "message": [
        r"message", r"comment", r"note", r"description", r"remarks",
        r"commentaire", r"objet", r"subject", r"sujet", r"details"
    ],
    "password": [
        r"pass", r"pwd", r"mot.?de.?passe"
    ],
    "username": [
        r"user.?name", r"login", r"identifiant", r"pseudo"
    ],
    "date_of_birth": [
        r"birth", r"dob", r"date.?naissance", r"birthday", r"naissance"
    ],
    "gender": [
        r"gender", r"sexe", r"genre"
    ],
    "linkedin": [
        r"linkedin"
    ],
    "cv_upload": [
        r"cv", r"resume", r"curriculum", r"attachment", r"file", r"upload",
        r"piece.?jointe", r"document"
    ],
}


@dataclass
class DetectedField:
    selector: str
    field_type: str
    tag: str
    input_type: str
    label: str
    placeholder: str
    matched_category: Optional[str] = None
    confidence: float = 0.0


@dataclass
class AnalysisResult:
    url: str
    fields: list[DetectedField] = field(default_factory=list)
    page_title: str = ""
    forms_count: int = 0


@dataclass
class ProxyConfig:
    enabled: bool = False
    server: str = ""
    username: str = ""
    password: str = ""

    @property
    def is_valid(self) -> bool:
        return self.enabled and bool(self.server.strip())

    def to_playwright(self) -> Optional[dict]:
        if not self.is_valid:
            return None
        proxy = {"server": self.server.strip()}
        if self.username.strip():
            proxy["username"] = self.username.strip()
        if self.password.strip():
            proxy["password"] = self.password.strip()
        return proxy

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "server": self.server,
            "username": self.username,
            "password": self.password,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProxyConfig":
        return cls(
            enabled=data.get("enabled", False),
            server=data.get("server", ""),
            username=data.get("username", ""),
            password=data.get("password", ""),
        )


class FormEngine:
    def __init__(self):
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

    async def start_browser(self, headless: bool = False,
                            proxy: Optional[ProxyConfig] = None,
                            device_profile_name: str = "Windows",
                            storage_state_path: str | None = None):
        # Ensure stale sessions are closed before creating a new context.
        if self._browser or self._playwright:
            await self.close()

        self._playwright = await async_playwright().start()

        launch_args = {"headless": headless}
        if proxy and proxy.is_valid:
            launch_args["proxy"] = proxy.to_playwright()

        self._browser = await self._playwright.chromium.launch(**launch_args)
        profile = DEVICE_PROFILES.get(device_profile_name, DEVICE_PROFILES["Windows"])
        context_args = {
            "viewport": {"width": profile.viewport_width, "height": profile.viewport_height},
            "user_agent": profile.user_agent,
            "locale": profile.locale,
        }
        if storage_state_path:
            context_args["storage_state"] = storage_state_path
        self._context = await self._browser.new_context(**context_args)
        self._page = await self._context.new_page()

    async def has_live_page(self) -> bool:
        if not self._page:
            return False

    async def save_storage_state(self, path: str) -> None:
        if not self._context:
            raise RuntimeError("Browser context is not available.")
        await self._context.storage_state(path=path)

    async def get_cookies(self) -> list[dict]:
        if not self._context:
            raise RuntimeError("Browser context is not available.")
        return await self._context.cookies()

    async def add_cookies(self, cookies: list[dict]) -> None:
        if not self._context:
            raise RuntimeError("Browser context is not available.")
        if not cookies:
            return
        await self._context.add_cookies(cookies)
        try:
            return not self._page.is_closed()
        except Exception:
            return False

    async def close(self):
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._browser = None
        self._playwright = None
        self._page = None

    async def navigate(self, url: str) -> str:
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        last_error = None
        strategies = [
            ("domcontentloaded", 30000),
            ("load", 45000),
            ("commit", 60000),
        ]
        for wait_until, timeout in strategies:
            try:
                await self._page.goto(url, wait_until=wait_until, timeout=timeout)
                await self._page.wait_for_timeout(1500)
                return await self._page.title()
            except Exception as e:
                last_error = e
                # Try the next strategy before failing.
                continue
        raise RuntimeError(f"Navigation failed for {url}: {last_error}")

    def _match_category(self, name: str, id_attr: str, placeholder: str,
                        label: str, input_type: str, aria_label: str,
                        autocomplete: str) -> tuple[Optional[str], float]:
        text = f"{name} {id_attr} {placeholder} {label} {aria_label} {autocomplete}".lower().strip()
        tokens = set(re.findall(r"[a-z0-9_]+", text))

        if input_type == "email":
            return "email", 0.95
        if input_type == "tel":
            return "phone", 0.95
        if input_type == "url":
            return "website", 0.90
        if input_type == "password":
            return "password", 0.95
        if input_type == "file":
            return "cv_upload", 0.80

        autocomplete_map = {
            "given-name": "first_name",
            "family-name": "last_name",
            "name": "full_name",
            "email": "email",
            "tel": "phone",
            "address-line1": "address",
            "address-level2": "city",
            "postal-code": "zip_code",
            "country-name": "country",
            "organization": "company",
            "organization-title": "job_title",
            "url": "website",
            "username": "username",
            "new-password": "password",
            "current-password": "password",
            "bday": "date_of_birth",
            "sex": "gender",
        }
        auto_key = autocomplete.lower().strip()
        if auto_key in autocomplete_map:
            return autocomplete_map[auto_key], 0.99

        best_match = None
        best_score = 0.0

        for category, patterns in FIELD_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    score = len(pattern) / max(len(text), 1)
                    score = min(score * 2, 0.95)
                    pattern_token = pattern.replace(".?", "").replace("^", "").replace("$", "")
                    if pattern_token in tokens:
                        score = min(score + 0.2, 0.98)
                    if score > best_score:
                        best_score = score
                        best_match = category
        return best_match, best_score

    async def analyze(self, url: str) -> AnalysisResult:
        title = await self.navigate(url)

        fields_data = await self._page.evaluate("""
        () => {
            const results = [];
            const seen = new Set();

            function getLabelFor(el) {
                if (el.id) {
                    const label = document.querySelector(`label[for="${el.id}"]`);
                    if (label) return label.innerText.trim();
                }
                const parent = el.closest('label');
                if (parent) return parent.innerText.trim();
                const prev = el.previousElementSibling;
                if (prev && prev.tagName === 'LABEL') return prev.innerText.trim();
                return '';
            }

            function getSelector(el) {
                if (el.id) return '#' + CSS.escape(el.id);
                if (el.name) return `${el.tagName.toLowerCase()}[name="${CSS.escape(el.name)}"]`;
                const parent = el.parentElement;
                if (!parent) return el.tagName.toLowerCase();
                const idx = Array.from(parent.children).filter(c => c.tagName === el.tagName).indexOf(el);
                const parentSel = parent.id ? '#' + CSS.escape(parent.id) : parent.tagName.toLowerCase();
                return `${parentSel} > ${el.tagName.toLowerCase()}:nth-of-type(${idx + 1})`;
            }

            const inputs = document.querySelectorAll('input, textarea, select');
            inputs.forEach(el => {
                const type = (el.type || '').toLowerCase();
                if (['hidden', 'submit', 'button', 'reset', 'image'].includes(type)) return;
                if (el.style.display === 'none' || el.style.visibility === 'hidden') return;
                const rect = el.getBoundingClientRect();
                if (rect.width === 0 && rect.height === 0) return;

                const sel = getSelector(el);
                if (seen.has(sel)) return;
                seen.add(sel);

                results.push({
                    selector: sel,
                    tag: el.tagName.toLowerCase(),
                    type: type || 'text',
                    name: el.name || '',
                    id: el.id || '',
                    placeholder: el.placeholder || '',
                    label: getLabelFor(el),
                    ariaLabel: el.getAttribute('aria-label') || '',
                    autocomplete: (el.getAttribute('autocomplete') || '').toLowerCase(),
                    required: el.required,
                });
            });

            const formsCount = document.querySelectorAll('form').length;
            return { fields: results, formsCount };
        }
        """)

        result = AnalysisResult(url=url, page_title=title, forms_count=fields_data["formsCount"])

        for f in fields_data["fields"]:
            category, confidence = self._match_category(
                f["name"],
                f["id"],
                f["placeholder"],
                f["label"],
                f["type"],
                f.get("ariaLabel", ""),
                f.get("autocomplete", ""),
            )
            detected = DetectedField(
                selector=f["selector"],
                field_type=f["type"],
                tag=f["tag"],
                input_type=f["type"],
                label=f["label"] or f["placeholder"] or f["name"] or f["id"],
                placeholder=f["placeholder"],
                matched_category=category,
                confidence=confidence,
            )
            result.fields.append(detected)

        return result

    async def fill_fields(self, fields: list[DetectedField], user_data: dict,
                          on_progress=None) -> list[dict]:
        results = []
        for i, f in enumerate(fields):
            if not f.matched_category or f.matched_category not in user_data:
                results.append({"field": f.label, "status": "skipped", "reason": "no data"})
                continue

            value = user_data[f.matched_category]
            if not value:
                results.append({"field": f.label, "status": "skipped", "reason": "empty value"})
                continue

            try:
                el = self._page.locator(f.selector).first
                await el.wait_for(state="visible", timeout=5000)
                if f.tag == "select":
                    try:
                        await el.select_option(label=value, timeout=3000)
                    except Exception:
                        await el.select_option(value=value, timeout=3000)
                elif f.input_type == "file":
                    await el.set_input_files(value, timeout=5000)
                elif f.input_type == "checkbox":
                    if value.lower() in ("true", "1", "yes", "oui"):
                        await el.check(timeout=3000)
                elif f.input_type == "radio":
                    await el.check(timeout=3000)
                else:
                    success = False
                    for _attempt in range(2):
                        try:
                            await el.click(timeout=3000)
                            await el.fill("", timeout=2000)
                            await el.fill(value, timeout=3000)
                            success = True
                            break
                        except Exception:
                            await self._page.wait_for_timeout(250)
                    if not success:
                        await el.type(value, delay=20, timeout=4000)

                results.append({"field": f.label, "status": "filled", "value": value})
                if on_progress:
                    on_progress(i + 1, len(fields), f.label, "filled")
            except Exception as e:
                results.append({"field": f.label, "status": "error", "reason": str(e)[:100]})
                if on_progress:
                    on_progress(i + 1, len(fields), f.label, "error")

        return results

    async def submit_form(self):
        submit_selectors = [
            'button[type="submit"]',
            'input[type="submit"]',
            'button:has-text("Submit")',
            'button:has-text("Envoyer")',
            'button:has-text("Soumettre")',
            'button:has-text("Postuler")',
            'button:has-text("Apply")',
            'button:has-text("Send")',
            'button:has-text("Valider")',
        ]
        for sel in submit_selectors:
            try:
                btn = self._page.locator(sel).first
                if await btn.is_visible(timeout=1000):
                    await btn.click(timeout=5000)
                    return True
            except:
                continue
        return False

    async def click_helper_elements(self, max_clicks: int = 8) -> list[str]:
        """Try benign helper clicks (cookie/continue/next/required checkboxes)."""
        if not self._page:
            return []

        actions: list[str] = []
        click_candidates = [
            ('button:has-text("Accept")', "accept"),
            ('button:has-text("I Agree")', "agree"),
            ('button:has-text("Allow")', "allow"),
            ('button:has-text("Continue")', "continue"),
            ('button:has-text("Next")', "next"),
            ('button:has-text("Start")', "start"),
            ('button:has-text("Proceed")', "proceed"),
            ('button:has-text("OK")', "ok"),
            ('button:has-text("Close")', "close"),
            ('button:has-text("Fermer")', "close"),
            ('button:has-text("Accepter")', "accept"),
            ('button:has-text("Suivant")', "next"),
            ('[aria-label*="accept" i]', "accept"),
            ('[aria-label*="continue" i]', "continue"),
            ('[role="button"][aria-label*="close" i]', "close"),
        ]

        for selector, tag in click_candidates:
            if len(actions) >= max_clicks:
                break
            try:
                loc = self._page.locator(selector)
                count = await loc.count()
                for idx in range(min(count, 2)):
                    if len(actions) >= max_clicks:
                        break
                    el = loc.nth(idx)
                    try:
                        if await el.is_visible(timeout=800):
                            await el.click(timeout=2000)
                            actions.append(f"click:{tag}")
                            await self._page.wait_for_timeout(250)
                    except Exception:
                        continue
            except Exception:
                continue

        # Optional required checkboxes (terms/privacy) when present.
        checkbox_selectors = [
            'input[type="checkbox"][required]',
            'input[type="checkbox"][name*="terms" i]',
            'input[type="checkbox"][id*="terms" i]',
            'input[type="checkbox"][name*="privacy" i]',
            'input[type="checkbox"][id*="privacy" i]',
        ]
        for selector in checkbox_selectors:
            if len(actions) >= max_clicks:
                break
            try:
                loc = self._page.locator(selector)
                count = await loc.count()
                for idx in range(min(count, 2)):
                    if len(actions) >= max_clicks:
                        break
                    el = loc.nth(idx)
                    try:
                        if await el.is_visible(timeout=800):
                            await el.check(timeout=2000)
                            actions.append("check:required")
                            await self._page.wait_for_timeout(150)
                    except Exception:
                        continue
            except Exception:
                continue

        return actions

    @staticmethod
    async def probe_proxy(
        proxy: ProxyConfig,
        timeout_ms: int = 12000,
        test_url: str = "https://api.ipify.org?format=json",
        fast_mode: bool = False,
    ) -> dict:
        start = asyncio.get_running_loop().time()
        playwright = None
        request_ctx = None
        try:
            playwright = await async_playwright().start()
            # Lighter than launching full Chromium for every proxy probe.
            request_ctx = await playwright.request.new_context(
                proxy=proxy.to_playwright(),
                ignore_https_errors=True,
            )

            probe_urls = [test_url] if fast_mode else [
                test_url,
                "https://api.ipify.org",
                "https://ifconfig.me/ip",
                "https://httpbin.org/ip",
            ]
            body_text = ""
            ip_value = ""
            last_err = ""
            for url in probe_urls:
                try:
                    resp = await request_ctx.get(url, timeout=timeout_ms)
                    body_text = (await resp.text() or "").strip()
                    if not resp.ok:
                        last_err = f"{url} returned HTTP {resp.status}"
                        continue
                    if not body_text:
                        continue
                    if body_text.startswith("{"):
                        try:
                            parsed = json.loads(body_text)
                            ip_value = str(parsed.get("ip", "")).strip()
                        except Exception:
                            ip_value = ""
                    if not ip_value:
                        m = re.search(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", body_text)
                        ip_value = m.group(0) if m else ""
                    if body_text:
                        break
                except Exception as probe_err:
                    last_err = str(probe_err)
                    continue

            if not body_text:
                raise RuntimeError(last_err or "No response from probe endpoints")

            country_value = ""
            if ip_value:
                try:
                    geo = await request_ctx.get(
                        f"https://ipwho.is/{ip_value}",
                        timeout=min(timeout_ms, 6000),
                    )
                    if geo.ok:
                        geo_data = await geo.json()
                        if isinstance(geo_data, dict):
                            country_value = str(geo_data.get("country", "")).strip()
                except Exception:
                    country_value = ""
            elapsed_ms = int((asyncio.get_running_loop().time() - start) * 1000)
            return {
                "ok": True,
                "ip": ip_value,
                "country": country_value,
                "details": body_text[:120],
                "elapsed_ms": elapsed_ms,
            }
        except Exception as e:
            elapsed_ms = int((asyncio.get_running_loop().time() - start) * 1000)
            reason = str(e)
            low = reason.lower()
            if "timeout" in low or "timed out" in low:
                reason = "Timeout: proxy is too slow or unreachable"
            elif "407" in low or "proxy authentication required" in low:
                reason = "Proxy auth required (407): invalid username/password"
            elif "403" in low:
                reason = "Forbidden (403): target blocked this proxy"
            elif "connection refused" in low:
                reason = "Connection refused: proxy host/port not accepting traffic"
            return {
                "ok": False,
                "ip": "",
                "country": "",
                "details": reason[:180],
                "elapsed_ms": elapsed_ms,
            }
        finally:
            if request_ctx:
                try:
                    await request_ctx.dispose()
                except Exception:
                    pass
            if playwright:
                try:
                    await playwright.stop()
                except Exception:
                    pass
