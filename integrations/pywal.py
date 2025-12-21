# Copyright (C) 2025 Igu R. Spain
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Integración con Pywal (API Python).

Este módulo intenta usar la API de la librería `pywal` cuando está
disponible; si no puede detectar una API directa, hace un fallback
prudente al CLI (solo como último recurso).

Función principal:
- `generate_palette(image_path, mode='auto', cols=16)` -> lista de hex colores

Notas:
- La API de `pywal` ha cambiado entre versiones; por eso se intentan
  varios puntos de entrada. Si ninguna está disponible, se levanta
  una excepción clara para que el backend pueda manejarla.
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


def generate_palette(image_path: str, _mode: str = 'auto', cols: int = 16, _timeout: int = 30) -> List[str]:
    """Genera una paleta usando pywal.

    Args:
        image_path: ruta a la imagen de entrada.
        mode: 'auto', 'light' o 'dark' — intención para la generación.
        cols: número de colores solicitados (intención, depende de pywal).

    Returns:
        Lista de colores en formato '#rrggbb'.

    Raises:
        RuntimeError si pywal no está disponible o si hay un error.
    """
    img = str(Path(image_path))

    # Try to use the pywal API if it's installed
    try:
        import pywal  # type: ignore
    except Exception as e:
        raise RuntimeError("pywal is not installed in the virtual environment") from e

    # Different versions of pywal expose different entry points.
    # We will use only the `pywal` module API. No fallback to CLI.
    colors: List[str] = []
    # pywal.colors.get or pywal.colors.get_colors
    if hasattr(pywal, 'colors'):
        colors_mod = pywal.colors
        if hasattr(colors_mod, 'get'):
            try:
                res = colors_mod.get(img, colors=cols)
                parsed = _parse_colors_from_pywal_result(res)
                if parsed:
                    colors = parsed
            except TypeError:
                # different signature; try with minimal parameters
                res = colors_mod.get(img)
                parsed = _parse_colors_from_pywal_result(res)
                if parsed:
                    colors = parsed

        if hasattr(colors_mod, 'get_colors') and not colors:
            res = colors_mod.get_colors(img)
            parsed = _parse_colors_from_pywal_result(res)
            if parsed:
                colors = parsed

    # Check other entry points in the pywal module
    if not colors and hasattr(pywal, 'wal') and hasattr(pywal.wal, 'colors'):
        res = pywal.wal.colors(img)
        parsed = _parse_colors_from_pywal_result(res)
        if parsed:
            colors = parsed

    if not colors:
        raise RuntimeError("pywal API no devolvió una paleta. Asegúrate de tener instalado 'pywal' y que la versión exponga la API de colores.")

    # Devolver la paleta tal cual la proporciona la API de pywal
    return colors
