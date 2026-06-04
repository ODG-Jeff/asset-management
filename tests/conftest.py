from pathlib import Path

import pytest

from odg_sorter.config import paths as config_paths


@pytest.fixture
def tmp_studio(tmp_path, monkeypatch):
    """Redirect every config path into tmp_path. Returns dict of the redirected roots."""
    intake = tmp_path / "_intake"; intake.mkdir()
    unsorted = intake / "unsorted"; unsorted.mkdir()
    repos = tmp_path / "repos"; repos.mkdir()
    vault = tmp_path / "vault"; vault.mkdir()
    quarantine = tmp_path / "_quarantine"; quarantine.mkdir()
    comfyui_out = tmp_path / "comfyui_output"; comfyui_out.mkdir()

    monkeypatch.setattr(config_paths, "STUDIO_ROOT", tmp_path)
    monkeypatch.setattr(config_paths, "WATCHED_PATHS", (intake, comfyui_out))
    monkeypatch.setattr(config_paths, "REPOS", repos)
    monkeypatch.setattr(config_paths, "VAULT", vault)
    monkeypatch.setattr(config_paths, "QUARANTINE", quarantine)
    monkeypatch.setattr(config_paths, "UNSORTED", unsorted)
    monkeypatch.setattr(config_paths, "VAULT_PROJECTS", vault / "Opal Dragonfly Games" / "Projects")
    monkeypatch.setattr(config_paths, "VAULT_GALLERY", vault / "Opal Dragonfly Games" / "Resources" / "Asset Gallery")
    monkeypatch.setattr(config_paths, "DHTW_REPO", repos / "dhtw")
    monkeypatch.setattr(config_paths, "DHTW_TABLETOP_REPO", repos / "dhtw-tabletop")
    monkeypatch.setattr(config_paths, "TLL_REPO", repos / "tll")

    # config/rules.py imported the path constants at import time. Reload it
    # so the rules pick up the monkeypatched paths.
    import importlib

    from odg_sorter.config import rules as _rules
    importlib.reload(_rules)

    # Patch router.RULES (and router.RuleResult) to the reloaded versions so
    # the shared route() function uses tmp paths. We do NOT reload router itself
    # because that would replace the Route/Park dataclass definitions and break
    # isinstance checks in test_router.py (which holds the original classes).
    from odg_sorter import router as _router
    monkeypatch.setattr(_router, "RULES", _rules.RULES)
    monkeypatch.setattr(_router, "RuleResult", _rules.RuleResult)

    # main.py has module-level imports: QUARANTINE, REPOS, VAULT_PROJECTS, etc.
    # Reload it so those names resolve to the patched tmp paths.
    from odg_sorter import main as _main
    importlib.reload(_main)

    yield {
        "intake": intake,
        "unsorted": unsorted,
        "repos": repos,
        "vault": vault,
        "quarantine": quarantine,
        "comfyui_out": comfyui_out,
    }

    # Teardown: restore rules module and main to production paths. monkeypatch
    # already restores router.RULES/RuleResult and config_paths attributes;
    # reload rules so its module-level names are back to production values, and
    # reload main so its module-level path names are restored too.
    importlib.reload(_rules)
    importlib.reload(_main)
