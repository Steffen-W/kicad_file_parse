"""
KiCad File I/O Module

This module provides unified file I/O operations for KiCad files without exposing
the internal sexpdata dependency. All file operations should go through this module.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, TypeVar, Union, cast

from .kicad_board import KiCadFootprint
from .kicad_common import KiCadObject, str_to_sexpr
from .kicad_design_rules import (
    KiCadDesignRules,
    parse_kicad_design_rules_file,
    write_kicad_design_rules_file,
)
from .kicad_pcb import KiCadPCB
from .kicad_schematic import KiCadSchematic
from .kicad_symbol import KiCadSymbolLibrary
from .kicad_worksheet import KiCadWorksheet
from .sexpdata import Delimiters, Symbol, tosexp

T = TypeVar("T", bound=KiCadObject)


# Custom formatting for KiCad files
@tosexp.register(float)
def format_float(obj: float, **kwds: Any) -> str:
    """Format float values in KiCad style

    Returns:
        str: Formatted float as string
    """
    return str(float(obj))


@tosexp.register(list)
@tosexp.register(Delimiters)
def format_sexp(obj: Delimiters, **kwds: Any) -> str:
    """Format S-expressions with KiCad-style indentation

    Applies custom formatting rules for KiCad S-expressions:
    - Single line for primitives-only expressions
    - Multi-line with indentation for nested structures
    - Special formatting for symbol library root elements

    Returns:
        str: Formatted S-expression string with proper indentation
    """
    items = obj if isinstance(obj, list) else obj.I
    if not items:
        return "()"

    # Track symbol context
    first = items[0]
    if isinstance(first, Symbol):
        kwds.setdefault("car_stack", []).append(str(first))

    try:
        # Check if we have any nested structures
        has_nested = any(isinstance(item, (list, Delimiters)) for item in items[1:])

        if not has_nested:
            # All primitives - single line
            formatted_items = [tosexp(item, **kwds) for item in items]
            result = "(" + " ".join(formatted_items) + ")"
        else:
            # Has nested structures - collect primitives and nested separately
            primitives = [tosexp(items[0], **kwds)]  # Always include first element
            nested_items = []

            # Process all items after the first
            for item in items[1:]:
                if isinstance(item, (list, Delimiters)):
                    nested_items.append(item)
                else:
                    primitives.append(tosexp(item, **kwds))

            # Build result
            parts = []

            # Add primitives on first line (if any beyond the first)
            if len(primitives) > 1:
                parts.append(" ".join(primitives))
            else:
                parts.append(primitives[0])

            # Add nested items on new lines
            for item in nested_items:
                formatted = tosexp(item, **kwds)
                # Indent each line
                indented_lines = []
                for line in formatted.split("\n"):
                    indented_lines.append("\t" + line if line.strip() else line)
                parts.append("\n" + "\n".join(indented_lines))

            result = "(" + "".join(parts) + "\n)"

        # Special case: top-level gets extra newline
        if isinstance(first, Symbol) and str(first) == "kicad_symbol_lib":
            result += "\n"

        return result

    finally:
        # Cleanup
        if isinstance(first, Symbol) and kwds.get("car_stack"):
            kwds["car_stack"].pop()


# File type detection
def detect_file_type(content: str) -> str:
    """Detect KiCad file type from S-expression content

    Analyzes the root token of S-expression content to determine file type.
    Supports symbol libraries, boards, schematics, footprints, worksheets, and design rules.
    """
    try:
        # Handle design rules which may have multiple S-expressions with comments
        if content.strip().startswith("#") or (
            "version" in content[:100] and "rule" in content
        ):
            # Check if content looks like design rules
            lines = content.split("\n")
            for line in lines:
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    if (
                        "version" in stripped and "(" in stripped
                    ) or "rule" in stripped:
                        return "design_rules"
                    break

        sexpr = str_to_sexpr(content)
        if len(sexpr) > 0:
            root_token = str(sexpr[0])
            if root_token == "kicad_symbol_lib":
                return "symbol_library"
            elif root_token == "kicad_pcb":
                return "board"
            elif root_token == "kicad_sch":
                return "schematic"
            elif root_token == "footprint":
                return "footprint"
            elif root_token == "module":  # Legacy footprint
                return "footprint"
            elif root_token == "kicad_wks":
                return "worksheet"
            elif root_token == "version":
                return "design_rules"
        return "unknown"
    except Exception:
        return "unknown"


def detect_file_type_from_path(filepath: Union[str, Path]) -> str:
    """Detect KiCad file type from file extension"""
    filepath = Path(filepath)
    suffix = filepath.suffix.lower()

    if suffix == ".kicad_sym":
        return "symbol_library"
    elif suffix == ".kicad_pcb":
        return "board"
    elif suffix == ".kicad_sch":
        return "schematic"
    elif suffix == ".kicad_mod":
        return "footprint"
    elif suffix == ".kicad_wks":
        return "worksheet"
    elif suffix == ".kicad_dru":
        return "design_rules"
    else:
        return "unknown"


# Core parsing functions
def parse_kicad_file(content: str, parser_class: Any) -> KiCadObject:
    """Parse KiCad file content using specified parser class"""
    try:
        sexpr = str_to_sexpr(content)
        return cast(KiCadObject, parser_class.from_sexpr(sexpr))
    except Exception as e:
        raise ValueError(f"Failed to parse KiCad file: {e}")


def serialize_kicad_object(obj: KiCadObject) -> str:
    """Serialize KiCad object to formatted string"""
    try:
        # Handle design rules specially
        if isinstance(obj, KiCadDesignRules):
            return write_kicad_design_rules_file(obj)

        sexpr = obj.to_sexpr()
        return cast(str, tosexp(sexpr))
    except Exception as e:
        raise ValueError(f"Failed to serialize KiCad object: {e}")


# File I/O functions
def load_kicad_file(
    filepath: Union[str, Path], parser_class: Any = None
) -> KiCadObject:
    """Load KiCad file from disk with automatic type detection

    Automatically detects file type and uses appropriate parser.
    Supports .kicad_sym (symbol libraries), .kicad_mod (footprints), .kicad_wks (worksheets),
    .kicad_sch (schematics), .kicad_pcb (boards), and .kicad_dru (design rules).
    """
    filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    # Read file content
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Auto-detect parser if not provided
    if parser_class is None:
        file_type = detect_file_type(content)
        if file_type == "symbol_library":
            parser_class = KiCadSymbolLibrary
        elif file_type == "footprint":
            parser_class = KiCadFootprint
        elif file_type == "worksheet":
            parser_class = KiCadWorksheet
        elif file_type == "schematic":
            parser_class = KiCadSchematic
        elif file_type == "board":
            parser_class = KiCadPCB
        elif file_type == "design_rules":
            # Handle design rules specially since they have a different parsing approach
            return parse_kicad_design_rules_file(content)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    return parse_kicad_file(content, parser_class)


def save_kicad_file(obj: KiCadObject, filepath: Union[str, Path]) -> None:
    """Save KiCad object to disk with proper formatting

    Returns:
        None
    """
    filepath = Path(filepath)

    # Ensure parent directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Serialize and save
    content = serialize_kicad_object(obj)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


# Convenience functions for specific file types
def load_symbol_library(filepath: Union[str, Path]) -> KiCadSymbolLibrary:
    """Load KiCad symbol library file

    Returns:
        KiCadSymbolLibrary: Loaded symbol library
    """
    return cast(KiCadSymbolLibrary, load_kicad_file(filepath, KiCadSymbolLibrary))


def save_symbol_library(library: Any, filepath: Union[str, Path]) -> None:
    """Save KiCad symbol library file

    Returns:
        None
    """
    save_kicad_file(library, filepath)


def load_footprint(filepath: Union[str, Path]) -> KiCadFootprint:
    """Load KiCad footprint file

    Returns:
        KiCadFootprint: Loaded footprint
    """
    return cast(KiCadFootprint, load_kicad_file(filepath, KiCadFootprint))


def save_footprint(footprint: Any, filepath: Union[str, Path]) -> None:
    """Save KiCad footprint file

    Returns:
        None
    """
    save_kicad_file(footprint, filepath)


def load_worksheet(filepath: Union[str, Path]) -> KiCadWorksheet:
    """Load KiCad worksheet file

    Returns:
        KiCadWorksheet: Loaded worksheet
    """
    return cast(KiCadWorksheet, load_kicad_file(filepath, KiCadWorksheet))


def save_worksheet(worksheet: Any, filepath: Union[str, Path]) -> None:
    """Save KiCad worksheet file

    Returns:
        None
    """
    save_kicad_file(worksheet, filepath)


def load_schematic(filepath: Union[str, Path]) -> KiCadSchematic:
    """Load KiCad schematic file

    Returns:
        KiCadSchematic: Loaded schematic
    """
    return cast(KiCadSchematic, load_kicad_file(filepath, KiCadSchematic))


def save_schematic(schematic: Any, filepath: Union[str, Path]) -> None:
    """Save KiCad schematic file

    Returns:
        None
    """
    save_kicad_file(schematic, filepath)


def load_pcb(filepath: Union[str, Path]) -> KiCadPCB:
    """Load KiCad PCB file

    Returns:
        KiCadPCB: Loaded PCB
    """
    return cast(KiCadPCB, load_kicad_file(filepath, KiCadPCB))


def save_pcb(pcb: Any, filepath: Union[str, Path]) -> None:
    """Save KiCad PCB file

    Returns:
        None
    """
    save_kicad_file(pcb, filepath)


# High-level API functions
def convert_file(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    modifier_func: Any = None,
) -> None:
    """Convert/modify KiCad file with optional transformation

    Returns:
        None
    """
    # Load file
    kicad_obj = load_kicad_file(input_path)

    # Apply modifier if provided
    if modifier_func:
        kicad_obj = modifier_func(kicad_obj)

    # Save result
    save_kicad_file(kicad_obj, output_path)


def validate_kicad_file(filepath: Union[str, Path]) -> Dict[str, Any]:
    """Validate KiCad file and return validation results"""
    try:
        obj = load_kicad_file(filepath)
        return {
            "valid": True,
            "file_type": detect_file_type_from_path(filepath),
            "object_type": type(obj).__name__,
            "error": None,
        }
    except Exception as e:
        return {
            "valid": False,
            "file_type": detect_file_type_from_path(filepath),
            "object_type": None,
            "error": str(e),
        }
