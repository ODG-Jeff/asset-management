from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

_TEMPLATES_DIR = files("odg_sorter.templates.sidecars")
_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=select_autoescape(disabled_extensions=("j2",), default=False),
    keep_trailing_newline=True,
)

_BODY_SEPARATOR = "<!-- Body is human-owned. Sorter never touches anything below the frontmatter+embed. -->"


@dataclass(frozen=True)
class SidecarContext:
    template: str
    sidecar_path: Path
    data: dict


def write_sidecar(ctx: SidecarContext) -> Path:
    rendered = _env.get_template(ctx.template).render(**ctx.data)
    existing_body = _extract_body_below_separator(ctx.sidecar_path) if ctx.sidecar_path.exists() else ""
    final = rendered + existing_body
    ctx.sidecar_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = ctx.sidecar_path.with_suffix(ctx.sidecar_path.suffix + ".tmp")
    tmp.write_text(final, encoding="utf-8")
    tmp.replace(ctx.sidecar_path)
    return ctx.sidecar_path


def _extract_body_below_separator(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if _BODY_SEPARATOR not in text:
        return ""
    _, after = text.split(_BODY_SEPARATOR, 1)
    return after
