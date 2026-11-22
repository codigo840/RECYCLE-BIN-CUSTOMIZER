"""Conversión y almacenamiento persistente de iconos."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Literal

from PIL import Image

IconState = Literal["empty", "full"]


def icons_directory() -> Path:
    """Devuelve la carpeta persistente de iconos del usuario."""
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        base = Path(local_app_data)
    else:
        base = Path.home() / ".local" / "share"
    return base / "RecycleBinCustomizer" / "icons"


def _safe_stem(state: IconState) -> str:
    return "papelera_vacia" if state == "empty" else "papelera_llena"


def convert_to_ico(source: str | Path, state: IconState, destination: Path | None = None) -> Path:
    """Convierte una imagen a ICO multirresolución y devuelve su ruta."""
    source_path = Path(source)
    if not source_path.is_file():
        raise FileNotFoundError(f"No existe la imagen: {source_path}")
    if source_path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".ico"}:
        raise ValueError("El archivo debe ser PNG, JPG, JPEG o ICO.")

    target_dir = destination or icons_directory()
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{_safe_stem(state)}.ico"

    with Image.open(source_path) as image:
        rgba = image.convert("RGBA")
        # Un lienzo cuadrado evita que un origen rectangular produzca marcos
        # deformados o menores que el tamaño máximo solicitado.
        edge = max(rgba.size)
        canvas = Image.new("RGBA", (edge, edge), (0, 0, 0, 0))
        offset = ((edge - rgba.width) // 2, (edge - rgba.height) // 2)
        canvas.paste(rgba, offset, rgba)
        canvas.thumbnail((256, 256), Image.Resampling.LANCZOS)
        canvas.save(target, format="ICO", sizes=[(16, 16), (32, 32), (48, 48),
                                                  (64, 64), (128, 128), (256, 256)])
    return target


def preview_image(source: str | Path, size: tuple[int, int] = (120, 120)) -> Image.Image:
    """Carga una imagen redimensionada para la vista previa, preservando alfa."""
    path = Path(source)
    if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".ico"}:
        raise ValueError("El archivo debe ser PNG, JPG, JPEG o ICO.")
    if not path.is_file():
        raise FileNotFoundError(f"No existe la imagen: {path}")
    with Image.open(path) as image:
        preview = image.convert("RGBA")
        preview.thumbnail(size, Image.Resampling.LANCZOS)
        return preview.copy()

