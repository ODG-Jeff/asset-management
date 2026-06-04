"""Watched directories and destination roots. Data-only — edit this file to change paths."""
from pathlib import Path

# The studio root. Everything under here.
STUDIO_ROOT = Path(r"C:\ODG")

# Inflow: what the watcher tails.
WATCHED_PATHS: tuple[Path, ...] = (
    STUDIO_ROOT / "_intake",
    # ComfyUI output directory. UPDATE when the actual ComfyUI install path is confirmed.
    STUDIO_ROOT / "generated" / "comfyui_output",
)

# Destination roots used by rules. Keep names stable — rule destinations reference these.
REPOS = STUDIO_ROOT / "repos"
VAULT = STUDIO_ROOT / "ODG_Vault"
QUARANTINE = STUDIO_ROOT / "_quarantine"
UNSORTED = STUDIO_ROOT / "_intake" / "unsorted"

# Vault PARA roots.
VAULT_PROJECTS = VAULT / "Opal Dragonfly Games" / "Projects"
VAULT_GALLERY = VAULT / "Opal Dragonfly Games" / "Resources" / "Asset Gallery"

# Per-project shorthand used by rules.
DHTW_REPO = REPOS / "dhtw"
DHTW_TABLETOP_REPO = REPOS / "dhtw-tabletop"
TLL_REPO = REPOS / "tll"
