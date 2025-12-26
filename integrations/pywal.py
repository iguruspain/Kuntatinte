"""Integración con Pywal (API Python).

Este módulo usa la API de la librería `pywal` para generar paletas de colores
a partir de imágenes.

Función principal:
- `generate_palette(image_path)` -> lista de hex colores

Notas:
- Requiere `pywal` instalado. Si no está disponible, levanta una excepción.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List
# No post-processing here; return colors as pywal provides them


def _parse_colors_from_pywal_result(result) -> List[str]:
    """Normaliza distintos tipos de resultado a lista de hex strings.

    result puede ser:
    - dict con clave 'colors' (mapping color0..)
    - dict con clave 'palette' o 'colors16'
    - lista de hex strings
    - cadena (json)
    """
    if result is None:
        return []

    if isinstance(result, str):
        # intentar parsear JSON
        try:
            data = json.loads(result)
            return _parse_colors_from_pywal_result(data)
        except Exception:
            # if it's a hex string, return it as a list
            val = result.strip()
            return [val] if val else []

    if isinstance(result, dict):
        # classic format: {'colors': {'color0': '#xxxxxx', ...}}
        if 'colors' in result and isinstance(result['colors'], dict):
            colors = result['colors']
            out = []
            # maintain order color0..colorN
            for i in range(0, 32):
                k = f'color{i}'
                if k in colors:
                    out.append(colors[k])
            if out:
                return out

        # otras claves comunes
        for key in ('palette', 'colors16', 'colors_16'):
            if key in result and isinstance(result[key], (list, tuple)):
                return [c if str(c).startswith('#') else f"#{c}" for c in result[key]]

        # intentar extraer cualquier lista con valores hex
        for v in result.values():
            if isinstance(v, (list, tuple)):
                candidate = [c for c in v if isinstance(c, str) and c.startswith('#')]
                if candidate:
                    return candidate

    if isinstance(result, (list, tuple)):
        out = []
        for c in result:
            if isinstance(c, str):
                out.append(c if c.startswith('#') else f"#{c}")
            elif isinstance(c, (list, tuple)) and len(c) >= 3:
                r, g, b = c[0], c[1], c[2]
                out.append(f"#{int(r):02x}{int(g):02x}{int(b):02x}")
        return out

    return []


import subprocess
import json
import tempfile
import os
from pathlib import Path

def generate_palette(image_path: str, cols: int = 16) -> List[str]:
    """Genera una paleta usando pywal sin aplicar tema.

    Args:
        image_path: ruta a la imagen de entrada.
        cols: número de colores a extraer (por defecto 16).

    Returns:
        Lista de colores en formato '#rrggbb'.

    Raises:
        RuntimeError si pywal no está disponible o si hay un error.
    """
    img = str(Path(image_path))

    # Use pywal Python module
    try:
        import pywal  # type: ignore
    except Exception as e:
        raise RuntimeError("pywal is not installed in the virtual environment") from e

    # Use pywal.colors.get with quiet=True to suppress logs and avoid side effects
    try:
        result = pywal.colors.get(img, cols=cols, quiet=True)
        parsed = _parse_colors_from_pywal_result(result)
        if parsed:
            return parsed
    except Exception as e:
        raise RuntimeError(f"pywal failed: {e}")

    raise RuntimeError("pywal API no devolvió una paleta.")
