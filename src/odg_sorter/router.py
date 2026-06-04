from dataclasses import dataclass
from pathlib import Path

from odg_sorter.config.rules import RULES, RuleResult
from odg_sorter.identify import Signals


@dataclass(frozen=True)
class Route:
    rule: str
    destination: Path
    sidecar_template: str
    confidence: str


@dataclass(frozen=True)
class Park:
    rule: str
    destination: Path
    reason: str


def route(signals: Signals) -> Route | Park:
    for rule in RULES:
        result: RuleResult | None = rule["match"](signals)
        if result is None:
            continue
        if result.kind == "route":
            return Route(
                rule=rule["name"],
                destination=result.destination,
                sidecar_template=rule["sidecar_template"],
                confidence=rule["confidence"],
            )
        return Park(rule=rule["name"], destination=result.destination, reason=result.reason)
    raise RuntimeError("rules list has no fallback — fix config/rules.py")
