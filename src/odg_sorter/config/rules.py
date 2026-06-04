"""Routing rules. First-match-wins. Add new rules at the top of their project block.

Each rule is a dict:
    name: str                 — logged on every match
    match: Callable[[Signals], RuleResult | None]
                              — return None to skip; RuleResult to claim
    sidecar_template: str | None  — Jinja2 template basename; None for park
    confidence: str           — 'high' | 'low' | 'none'
"""
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from odg_sorter.config.paths import (
    DHTW_REPO,
    DHTW_TABLETOP_REPO,
    TLL_REPO,
    UNSORTED,
)
from odg_sorter.identify import Signals


@dataclass(frozen=True)
class RuleResult:
    kind: str  # "route" | "park"
    destination: Path
    reason: str = ""


# -------- Helpers --------

THEME_RE = re.compile(r"^[a-z]+_(?P<theme>[a-z]+)_v\d+_\d+\.png$", re.IGNORECASE)


def _detect_theme(filename: str) -> str | None:
    m = THEME_RE.match(filename)
    return m.group("theme").lower() if m else None


def _route(dest: Path) -> RuleResult:
    return RuleResult(kind="route", destination=dest)


def _park(reason: str) -> RuleResult:
    return RuleResult(kind="park", destination=UNSORTED / date.today().isoformat(), reason=reason)


# -------- Rules --------

def _match_dhtw_sled_themed_v7(s: Signals) -> RuleResult | None:
    if s.tool != "comfyui":
        return None
    if not any("dhtwsprite" in lora.lower() for lora in s.comfyui_loras):
        return None
    theme = _detect_theme(s.filename) or "uncategorized"
    return _route(DHTW_REPO / "assets" / "sleds" / "themes" / theme / s.filename)


def _match_dhtw_card_front(s: Signals) -> RuleResult | None:
    if not re.match(r"^card_\d{3}_.+\.png$", s.filename, re.IGNORECASE):
        return None
    return _route(DHTW_TABLETOP_REPO / "components" / "cards" / "fronts" / s.filename)


def _match_dhtw_arlo_voice(s: Signals) -> RuleResult | None:
    if not re.match(r"^taunt_\d+.*\.(wav|mp3|flac)$", s.filename, re.IGNORECASE):
        return None
    return _route(DHTW_REPO / "client" / "assets" / "audio" / "arlo" / s.filename)


def _match_tgc_component_svg(s: Signals) -> RuleResult | None:
    if s.extension != ".svg":
        return None
    m = re.match(r"^(card|chit|token|board|box)_.*\.svg$", s.filename, re.IGNORECASE)
    if not m:
        return None
    component_type = m.group(1).lower() + "s"
    return _route(DHTW_TABLETOP_REPO / "components" / component_type / s.filename)


def _match_tll_comfyui(s: Signals) -> RuleResult | None:
    if s.tool != "comfyui":
        return None
    wf = s.comfyui_workflow.lower()
    if not any(tag in wf for tag in ("tll", "probe", "the-last-light")):
        return None
    system = _system_hint(s.filename) or "uncategorized"
    return _route(TLL_REPO / "client" / "assets" / "generated" / system / s.filename)


def _match_tll_glb_export(s: Signals) -> RuleResult | None:
    if s.extension != ".glb":
        return None
    p = str(s.path).replace("\\", "/").lower()
    if "/generated/tll/" not in p and not re.match(r"^(probe|console|hub)_", s.filename, re.IGNORECASE):
        return None
    system = _system_hint(s.filename) or "uncategorized"
    return _route(TLL_REPO / "client" / "assets" / "3d" / system / s.filename)


def _match_dhtw_glb_export(s: Signals) -> RuleResult | None:
    if s.extension != ".glb":
        return None
    p = str(s.path).replace("\\", "/").lower()
    if "/generated/dhtw/" not in p and not re.match(r"^(sled|wall|arlo)_", s.filename, re.IGNORECASE):
        return None
    system = _system_hint(s.filename) or "uncategorized"
    return _route(DHTW_REPO / "client" / "assets" / "3d" / system / s.filename)


def _match_blender_source(s: Signals) -> RuleResult | None:
    if s.extension != ".blend":
        return None
    project = _project_hint(s.filename)
    if not project:
        return _park("blend-file-without-project-hint")
    return _route(_repo_for(project) / "blender" / s.filename)


def _match_fallback_park(_s: Signals) -> RuleResult:
    return _park("no-rule-matched")


def _system_hint(filename: str) -> str | None:
    m = re.match(r"^([a-z]+)_", filename, re.IGNORECASE)
    return m.group(1).lower() if m else None


def _project_hint(filename: str) -> str | None:
    n = filename.lower()
    if "dhtw" in n or "sled" in n or "arlo" in n or "wall" in n:
        return "dhtw"
    if "tll" in n or "probe" in n or "console" in n:
        return "tll"
    return None


def _repo_for(project: str) -> Path:
    return {"dhtw": DHTW_REPO, "tll": TLL_REPO, "dhtw-tabletop": DHTW_TABLETOP_REPO}[project]


RULES = [
    {"name": "dhtw-sled-themed-v7",  "match": _match_dhtw_sled_themed_v7,  "sidecar_template": "dhtw-sled.md.j2",       "confidence": "high"},
    {"name": "dhtw-card-front",      "match": _match_dhtw_card_front,      "sidecar_template": "dhtw-card.md.j2",       "confidence": "high"},
    {"name": "dhtw-arlo-voice",      "match": _match_dhtw_arlo_voice,      "sidecar_template": "dhtw-arlo-voice.md.j2", "confidence": "high"},
    {"name": "tgc-component-svg",    "match": _match_tgc_component_svg,    "sidecar_template": "tgc-component.md.j2",   "confidence": "high"},
    {"name": "tll-comfyui",          "match": _match_tll_comfyui,          "sidecar_template": "tll-comfyui.md.j2",     "confidence": "high"},
    {"name": "tll-glb-export",       "match": _match_tll_glb_export,       "sidecar_template": "tll-glb.md.j2",         "confidence": "high"},
    {"name": "dhtw-glb-export",      "match": _match_dhtw_glb_export,      "sidecar_template": "dhtw-glb.md.j2",        "confidence": "high"},
    {"name": "blender-source-file",  "match": _match_blender_source,       "sidecar_template": "blender-source.md.j2",  "confidence": "high"},
    {"name": "fallback-park",        "match": _match_fallback_park,        "sidecar_template": None,                    "confidence": "none"},
]
