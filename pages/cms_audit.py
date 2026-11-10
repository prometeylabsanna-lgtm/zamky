"""G8 hardcode / manifest audit (fail-closed на blockers)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from django.conf import settings

from pages.content_manifest import ALLOWLIST_HARDCODE
from pages.models_cms import SiteBlock
from pages.seed_parity import collect_parity
from pages.site_content_registry import CONTENT_SECTIONS, all_registry_block_keys

_CYR_PROSE = re.compile(r"[А-Яа-яІіЇїЄєҐґ]{3,}")
_T_TAG = re.compile(r"\{\%\s*t\s+'([^']+)'\s*\%\}")
_STATIC_CONTENT = re.compile(
    r"""\{\%\s*static\s+['\"]img/(?!icons/|vendor/)([^'\"]+)['\"]"""
)
_ARIA_ALLOW = re.compile(
    r"(aria-label|placeholder|alt)=|Breadcrumbs|role="
)

# UI-chrome, не маркетинговий контент сторінки (warn, не blocker)
_UI_CHROME_KEYS = frozenset(
    {
        "Меню",
        "Пошук",
        "Обране",
        "Кошик",
        "Назад",
        "Далі",
        "Головна",
        "Закрити",
        "Темна тема",
        "Світла тема",
        "Не обрано",
        "Основна навігація",
        "Слайди банера",
        "Слайд",
        "Сайт зроблено в",
    }
)


@dataclass(frozen=True)
class AuditFinding:
    severity: str  # blocker | warn
    file: str
    line: int
    message: str
    suggestion: str = ""


@dataclass(frozen=True)
class AuditReport:
    findings: tuple[AuditFinding, ...]
    parity_ok: bool
    blockers: int
    warns: int

    @property
    def ok(self) -> bool:
        return self.blockers == 0 and self.parity_ok


def _templates_root() -> Path:
    return Path(settings.BASE_DIR) / "templates"


def _scan_templates() -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    root = _templates_root()
    if not root.exists():
        return findings

    for path in sorted(root.rglob("*.html")):
        # admin templates — не вітрина
        if "admin" in path.parts:
            continue
        rel = str(path.relative_to(settings.BASE_DIR))
        text = path.read_text(encoding="utf-8")
        for i, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("{#"):
                continue

            for m in _STATIC_CONTENT.finditer(line):
                # hero/static fallbacks допустимі лише якщо CMS_ALLOW_STATIC_FALLBACK
                if settings.CMS_ALLOW_STATIC_FALLBACK and "v2/" in m.group(0):
                    findings.append(
                        AuditFinding(
                            "warn",
                            rel,
                            i,
                            f"static content image: {m.group(0)[:80]}",
                            "перевести в MediaItem / HeroSlide.media",
                        )
                    )
                elif not settings.CMS_ALLOW_STATIC_FALLBACK and "img/v2/" in m.group(0):
                    findings.append(
                        AuditFinding(
                            "blocker",
                            rel,
                            i,
                            f"static content image при CMS_ALLOW_STATIC_FALLBACK=False: {m.group(0)[:80]}",
                            "MediaItem / upload",
                        )
                    )

            for m in _T_TAG.finditer(line):
                phrase = m.group(1)
                if phrase in _UI_CHROME_KEYS:
                    continue
                if any(a in phrase for a in ALLOWLIST_HARDCODE):
                    continue
                # aria / технічні короткі
                if _ARIA_ALLOW.search(line) and len(phrase) <= 24:
                    continue
                sev = "warn"
                # Маркетингові довгі рядки на home/footer — warn (борг до повного kill)
                if path.name in {"home.html", "footer.html", "header.html"} and len(phrase) > 40:
                    sev = "warn"
                findings.append(
                    AuditFinding(
                        sev,
                        rel,
                        i,
                        f"{{% t '{phrase[:60]}' %}}",
                        "SiteBlock / SiteSettings",
                    )
                )
    return findings


def _scan_manifest_db() -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    parity = collect_parity()
    if not parity.ok:
        findings.append(
            AuditFinding(
                "blocker",
                "DB",
                0,
                f"seed parity fail: blocks={parity.site_blocks}/{parity.expected_blocks} "
                f"heroes={parity.hero_slides}/{parity.expected_heroes}",
                "python manage.py seed_content",
            )
        )
    for page, key in parity.missing_block_keys:
        findings.append(
            AuditFinding(
                "blocker",
                "DB",
                0,
                f"missing required slot {page}.{key}",
                "seed_content",
            )
        )

    # required text slots non-empty after seed (visibility keys may be 0/1)
    for page, key in all_registry_block_keys():
        if key.endswith("_visible"):
            continue
        block = SiteBlock.objects.filter(page=page, key=key).first()
        if block is None:
            continue
        if block.content_type == "text" and not (block.text_html or "").strip():
            # info body can be empty until editor fills — warn
            findings.append(
                AuditFinding(
                    "warn",
                    "DB",
                    0,
                    f"empty text slot {page}.{key}",
                    "заповнити в адмінці або defaults",
                )
            )

    # registry sections have admin_model_name
    names = [s.admin_model_name for s in CONTENT_SECTIONS]
    if len(names) != len(set(names)):
        findings.append(
            AuditFinding(
                "blocker",
                "registry",
                0,
                "duplicate admin_model_name у CONTENT_SECTIONS",
                "унікальні proxy names",
            )
        )
    return findings


def run_audit() -> AuditReport:
    findings = _scan_manifest_db() + _scan_templates()
    blockers = sum(1 for f in findings if f.severity == "blocker")
    warns = sum(1 for f in findings if f.severity == "warn")
    return AuditReport(
        findings=tuple(findings),
        parity_ok=collect_parity().ok,
        blockers=blockers,
        warns=warns,
    )
