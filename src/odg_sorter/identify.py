import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image

_TOOL_BY_EXT = {
    ".png": "comfyui",      # default; refined by metadata below
    ".jpg": "comfyui",
    ".jpeg": "comfyui",
    ".webp": "comfyui",
    ".svg": "inkscape",
    ".glb": "blender",
    ".gltf": "blender",
    ".fbx": "blender",
    ".obj": "blender",
    ".blend": "blender",
    ".wav": "audio",
    ".mp3": "audio",
    ".flac": "audio",
}


@dataclass(frozen=True)
class Signals:
    path: Path
    filename: str
    extension: str
    size_bytes: int
    hash_sha256: str
    tool: str
    comfyui_workflow: str = ""
    comfyui_loras: tuple[str, ...] = ()
    comfyui_model: str = ""
    comfyui_seed: str = ""
    comfyui_prompt: str = ""
    extras: dict[str, str] = field(default_factory=dict)


def identify(path: Path) -> Signals:
    path = Path(path)
    ext = path.suffix.lower()
    size = path.stat().st_size
    hash_ = _sha256_of(path)

    tool = _TOOL_BY_EXT.get(ext, "unknown")
    workflow = loras = model = seed = prompt = ""
    if ext in (".png", ".jpg", ".jpeg", ".webp"):
        text = _extract_png_text(path)
        if text:
            tool = "comfyui"
            workflow = text.get("workflow", "")
            loras = _extract_field(workflow, "loras")
            model = _extract_field(workflow, "model")
            seed = _extract_field(workflow, "seed")
            prompt = _extract_field(workflow, "prompt")
        else:
            tool = "image"  # PNG with no metadata isn't necessarily ComfyUI

    return Signals(
        path=path,
        filename=path.name,
        extension=ext,
        size_bytes=size,
        hash_sha256=hash_,
        tool=tool,
        comfyui_workflow=workflow,
        comfyui_loras=tuple(loras) if isinstance(loras, list) else (),
        comfyui_model=model if isinstance(model, str) else "",
        comfyui_seed=str(seed) if seed else "",
        comfyui_prompt=prompt if isinstance(prompt, str) else "",
    )


def _sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _extract_png_text(path: Path) -> dict[str, str]:
    try:
        with Image.open(path) as img:
            text = dict(getattr(img, "text", {}) or {})
            text.update(getattr(img, "info", {}) or {})
            return {k: v for k, v in text.items() if isinstance(v, str)}
    except Exception:
        return {}


def _extract_field(workflow_json_str: str, key: str):
    import json
    try:
        data = json.loads(workflow_json_str)
        return data.get(key, "")
    except Exception:
        return ""
