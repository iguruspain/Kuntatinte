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

"""
File Utilities.

Helper functions for file and directory operations.
"""

import os
from pathlib import Path
from typing import Union

PathLike = Union[str, Path]


def read_file_as_text(path: PathLike) -> str:
    """Read entire file content as text.
    
    Args:
        path: Path to the file
    
    Returns:
        File contents as string
    """
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def write_text_to_file(path: PathLike, text: str) -> None:
    """Write text content to a file, creating directories if needed.
    
    Args:
        path: Path to the file
        text: Content to write
    """
    dirname = os.path.dirname(path)
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)


def file_exists(path: PathLike) -> bool:
    """Check if a file or directory exists.
    
    Args:
        path: Path to check
    
    Returns:
        True if path exists, False otherwise
    """
    return os.path.exists(path)


def ensure_directory_exists(path: PathLike) -> None:
    """Create directory if it doesn't exist.
    
    Args:
        path: Directory path to create
    """
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
