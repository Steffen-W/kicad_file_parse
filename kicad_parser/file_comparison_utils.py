#!/usr/bin/env python3
"""
KiCad File Comparison Utilities

Standalone implementation of missing functions for file comparison functionality.
This module provides minimal dependencies implementation for detecting KiCad file types
and loading basic file objects.
"""

from __future__ import annotations

import re
from enum import Enum
from pathlib import Path
from typing import Any, List, Optional

from .sexpdata import loads


class KiCadFileType(Enum):
    """Enumeration of KiCad file types"""

    SCHEMATIC = "schematic"
    PCB = "board"
    FOOTPRINT = "footprint"
    SYMBOL_LIBRARY = "symbol_library"
    SYMBOL = "symbol"
    WORKSHEET = "worksheet"
    DESIGN_RULES = "design_rules"
    UNKNOWN = "unknown"


def detect_kicad_file_type(file_path: str) -> KiCadFileType:
    """
    Detect KiCad file type from file path.

    Args:
        file_path: Path to the KiCad file

    Returns:
        KiCadFileType enum value indicating the detected file type
    """
    return _detect_file_type_from_extension(file_path)


def _detect_file_type_from_extension(file_path: str) -> KiCadFileType:
    """Detect file type from file extension"""
    path = Path(file_path)
    suffix = path.suffix.lower()

    extension_map = {
        ".kicad_sch": KiCadFileType.SCHEMATIC,
        ".kicad_pcb": KiCadFileType.PCB,
        ".kicad_mod": KiCadFileType.FOOTPRINT,
        ".kicad_sym": KiCadFileType.SYMBOL_LIBRARY,
        ".kicad_wks": KiCadFileType.WORKSHEET,
        ".kicad_dru": KiCadFileType.DESIGN_RULES,
    }

    return extension_map.get(suffix, KiCadFileType.UNKNOWN)


class ComparisonResult:
    """Result of a file comparison operation"""

    def __init__(
        self,
        are_equal: bool,
        differences: Optional[List[str]] = None,
        similarity_score: Optional[float] = None,
    ):
        self.are_equal = are_equal
        self.differences = differences or []
        self.similarity_score = similarity_score

    def __str__(self) -> str:
        result = f"Files are {'EQUAL' if self.are_equal else 'DIFFERENT'}"
        if self.similarity_score is not None:
            result += f" (Similarity: {self.similarity_score:.2%})"
        if self.differences:
            result += f"\nDifferences found: {len(self.differences)}"
            for i, diff in enumerate(self.differences[:5]):  # Show first 5 differences
                result += f"\n  {i + 1}. {diff}"
            if len(self.differences) > 5:
                result += f"\n  ... and {len(self.differences) - 5} more differences"
        return result


def load_file_as_sexpr(file_path: str) -> Any:
    """Load a file and parse it as S-expression"""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    return loads(content)


def normalize_sexpr_for_comparison(sexpr: Any) -> Any:
    """Normalize S-expression for structural comparison (sort lists, etc.)"""
    if isinstance(sexpr, list):
        if len(sexpr) == 0:
            return []

        # Recursively normalize all elements first
        normalized_items = [normalize_sexpr_for_comparison(item) for item in sexpr]

        # For the root level or container elements, sort child elements by their type/name
        if (
            len(normalized_items) > 1
            and isinstance(normalized_items[0], str)
            and normalized_items[0]
            in ["kicad_sch", "kicad_pcb", "footprint", "kicad_symbol_lib"]
        ):

            # Keep the first element (main type) and sort the rest
            result: List[Any] = [normalized_items[0]]
            remaining = normalized_items[1:]

            # Sort elements by their type if they are lists with string identifiers
            sortable = []
            non_sortable = []

            for item in remaining:
                if (
                    isinstance(item, list)
                    and len(item) > 0
                    and isinstance(item[0], str)
                ):
                    sortable.append((item[0], item))
                else:
                    non_sortable.append(item)

            # Sort by the type/command name
            sortable.sort(key=lambda x: x[0])
            result.extend(item[1] for item in sortable)
            result.extend(non_sortable)

            return result
        else:
            return normalized_items
    else:
        return sexpr


def find_structural_differences(sexpr1: Any, sexpr2: Any, path: str = "") -> List[str]:
    """Find differences between two normalized S-expressions"""
    differences = []

    if not isinstance(sexpr1, type(sexpr2)) and not isinstance(sexpr2, type(sexpr1)):
        differences.append(
            f"Type mismatch at {path}: {type(sexpr1).__name__} vs {type(sexpr2).__name__}"
        )
        return differences

    if isinstance(sexpr1, list):
        if len(sexpr1) != len(sexpr2):
            differences.append(
                f"Length mismatch at {path}: {len(sexpr1)} vs {len(sexpr2)}"
            )
            return differences

        for i, (item1, item2) in enumerate(zip(sexpr1, sexpr2)):
            current_path = f"{path}[{i}]" if path else f"[{i}]"
            differences.extend(find_structural_differences(item1, item2, current_path))

    elif sexpr1 != sexpr2:
        differences.append(f"Value mismatch at {path}: '{sexpr1}' vs '{sexpr2}'")

    return differences


def calculate_structural_similarity(sexpr1: Any, sexpr2: Any) -> float:
    """Calculate similarity score between two S-expressions (0.0 to 1.0)"""

    def count_elements(sexpr: Any) -> int:
        if isinstance(sexpr, list):
            return 1 + sum(count_elements(item) for item in sexpr)
        else:
            return 1

    def count_common_elements(s1: Any, s2: Any) -> int:
        if not isinstance(s1, type(s2)) and not isinstance(s2, type(s1)):
            return 0

        if isinstance(s1, list):
            if len(s1) != len(s2):
                return 0
            return sum(
                count_common_elements(item1, item2) for item1, item2 in zip(s1, s2)
            )
        else:
            return 1 if s1 == s2 else 0

    total1 = count_elements(sexpr1)
    total2 = count_elements(sexpr2)
    common = count_common_elements(sexpr1, sexpr2)

    total_max = max(total1, total2)
    return common / total_max if total_max > 0 else 0.0


def calculate_text_similarity(text1: str, text2: str) -> float:
    """Calculate text similarity using character-based approach"""
    if not text1 and not text2:
        return 1.0
    if not text1 or not text2:
        return 0.0

    # Simple character-based similarity
    common_chars = sum(1 for c1, c2 in zip(text1, text2) if c1 == c2)
    max_length = max(len(text1), len(text2))

    return common_chars / max_length


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace in text: remove empty lines, normalize spaces"""
    lines = text.splitlines()

    # Remove empty lines and normalize whitespace within lines
    normalized_lines = []
    for line in lines:
        # Normalize internal whitespace (multiple spaces/tabs to single space)
        normalized_line = re.sub(r"\s+", " ", line.strip())
        if normalized_line:  # Only keep non-empty lines
            normalized_lines.append(normalized_line)

    return "\n".join(normalized_lines)
