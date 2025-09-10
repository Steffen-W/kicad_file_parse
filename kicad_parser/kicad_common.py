"""
KiCad S-Expression Common Types and Utilities

This module contains common data structures and utilities shared across
all KiCad file formats (symbol libraries, footprint libraries, schematics, boards).
"""

from __future__ import annotations

import re
import uuid as python_uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union, cast

from . import sexpdata
from .sexpdata import Symbol

# Type definitions for S-Expressions
SExprValue = Any  # Can be Symbol, str, int, float, or nested list
SExpr = List[SExprValue]


# Centralized S-Expression conversion utilities
def str_to_sexpr(content: str) -> SExpr:
    """
    Convert string content to S-expression.

    This is the centralized function for parsing S-expressions from strings,
    wrapping sexpdata.loads() to provide consistent parsing throughout the codebase.

    Args:
        content: String content containing S-expression data

    Returns:
        Parsed S-expression as nested lists/atoms

    Raises:
        ValueError: If content cannot be parsed as valid S-expression
    """
    try:
        return cast(SExpr, sexpdata.loads(content))
    except Exception as e:
        raise ValueError(f"Failed to parse S-expression: {e}") from e


def sexpr_to_str(sexpr: SExpr, pretty_print: bool = True) -> str:
    """
    Convert S-expression to string representation.

    This is the centralized function for serializing S-expressions to strings,
    wrapping sexpdata.dumps() to provide consistent formatting throughout the codebase.

    Args:
        sexpr: S-expression to serialize
        pretty_print: Whether to format output for readability

    Returns:
        String representation of the S-expression

    Raises:
        ValueError: If sexpr cannot be serialized
    """
    try:
        return sexpdata.dumps(sexpr, pretty_print=pretty_print)  # type: ignore
    except Exception as e:
        raise ValueError(f"Failed to serialize S-expression: {e}") from e


# Utility classes for S-Expression parsing


class SExprParser:
    """Helper class for parsing S-Expressions with common patterns"""

    @staticmethod
    def find_token(sexpr: SExpr, token_name: str) -> Optional[SExpr]:
        """Find first occurrence of token in S-Expression

        Returns:
            Optional[List]: The matching token list or None if not found
        """
        for item in sexpr:
            if (
                isinstance(item, list)
                and len(item) > 0
                and item[0] == Symbol(token_name)
            ):
                return item
        return None

    @staticmethod
    def find_all_tokens(sexpr: SExpr, token_name: str) -> List[SExpr]:
        """Find all occurrences of token in S-Expression

        Returns:
            List[List]: All matching token lists
        """
        results = []
        for item in sexpr:
            if (
                isinstance(item, list)
                and len(item) > 0
                and item[0] == Symbol(token_name)
            ):
                results.append(item)
        return results

    @staticmethod
    def get_value(sexpr: SExpr, index: int, default: Any = None) -> Any:
        """Safely get value at index with default

        Returns:
            Any: Value at index or default if index out of bounds
        """
        return sexpr[index] if len(sexpr) > index else default

    @staticmethod
    def has_symbol(sexpr: SExpr, symbol_name: str) -> bool:
        """Check if symbol exists in S-Expression

        Returns:
            bool: True if symbol exists, False otherwise
        """
        return Symbol(symbol_name) in sexpr

    @staticmethod
    def get_symbol_value(sexpr: SExpr, symbol_name: str, default: Any = None) -> Any:
        """Get value following a symbol

        Returns:
            Any: Value following the symbol or default if not found
        """
        for i, item in enumerate(sexpr):
            if item == Symbol(symbol_name) and i + 1 < len(sexpr):
                return sexpr[i + 1]
        return default

    @staticmethod
    def safe_float(value: Any, default: float = 0.0) -> float:
        """Safely convert value to float with default"""
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def safe_int(value: Any, default: int = 0) -> int:
        """Safely convert value to int with default"""
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def safe_str(value: Any, default: Optional[str] = "") -> Optional[str]:
        """Safely convert value to string with default (can be None)"""
        if value is None:
            return default
        return str(value)

    @staticmethod
    def normalize_text_content(text: str) -> str:
        """Normalize text content to handle various KiCad format variations.

        Accepts both old and new format variations when parsing:
        - Empty strings: accepts both "~" and ""
        - Overbar syntax: accepts both ~TEXT~ and ~{TEXT}

        Returns:
            str: Normalized text content
        """
        if not text:
            return ""

        # Handle empty string marker (old format used "~")
        if text == "~":
            return ""

        # Convert old overbar syntax ~TEXT~ to new syntax ~{TEXT}
        # Use regex to find ~...~ patterns that are not already ~{...}
        # Match ~(text)~ but not ~{text}
        pattern = r"~([^~{}]+)~"
        if re.search(pattern, text):
            text = re.sub(pattern, r"~{\1}", text)

        return text

    @staticmethod
    def format_text_for_output(text: str) -> str:
        """Format text for output using newest format conventions.

        Always outputs in newest format:
        - Empty strings as ""
        - Preserves overbar syntax as-is (parser handles both variants)

        Returns:
            str: Formatted text for output
        """
        if not text:
            return ""
        return text

    @staticmethod
    def normalize_pin_electrical_type(pin_type: str) -> str:
        """Normalize pin electrical type for compatibility.

        Accepts both old and new pin type names when parsing.

        Returns:
            str: Normalized pin type (using new names)
        """
        # Map old pin type names to new ones
        type_mapping = {"unconnected": "no_connect"}

        return type_mapping.get(pin_type, pin_type)

    @staticmethod
    def parse_enum(value: Any, enum_class: Any, default: Any) -> Any:
        """Safely parse enum value with default

        Returns:
            Enum: Parsed enum value or default if parsing fails
        """
        try:
            return enum_class(str(value))
        except (ValueError, TypeError):
            return default

    @staticmethod
    def parse_stroke_or_width(sexpr: SExpr, default_width: float = 0.254) -> Stroke:
        """Parse stroke with legacy width fallback"""
        stroke_token = SExprParser.find_token(sexpr, "stroke")
        width_token = SExprParser.find_token(sexpr, "width")

        if stroke_token:
            return Stroke.from_sexpr(stroke_token)
        elif width_token:
            return Stroke(
                width=SExprParser.safe_float(
                    SExprParser.get_value(width_token, 1), default_width
                )
            )
        else:
            return Stroke(width=default_width)

    @staticmethod
    def validate_token_length(
        token: List, min_length: int, token_name: str = ""
    ) -> bool:
        """Validate that a token has minimum required length"""
        if not token or len(token) < min_length:
            return False
        return True

    @staticmethod
    def safe_get_position(sexpr: List, start_index: int = 1) -> "Position":
        """Safely parse position with bounds checking"""
        if not sexpr or len(sexpr) < start_index + 2:
            return Position(0.0, 0.0)

        x = SExprParser.safe_float(SExprParser.get_value(sexpr, start_index), 0.0)
        y = SExprParser.safe_float(SExprParser.get_value(sexpr, start_index + 1), 0.0)
        angle = SExprParser.safe_float(
            SExprParser.get_value(sexpr, start_index + 2), 0.0
        )

        return Position(x, y, angle)

    # Utility functions for common token parsing patterns
    @staticmethod
    def get_optional_str(
        sexpr: SExpr, token_name: str, index: int = 1
    ) -> Optional[str]:
        """Get optional string value from token"""
        token = SExprParser.find_token(sexpr, token_name)
        if token is None:
            return None
        raw = SExprParser.get_value(token, index)
        return str(raw) if raw is not None else None

    @staticmethod
    def get_optional_float(
        sexpr: SExpr, token_name: str, index: int = 1
    ) -> Optional[float]:
        """Get optional float value from token"""
        token = SExprParser.find_token(sexpr, token_name)
        if token is None:
            return None
        raw = SExprParser.get_value(token, index)
        return SExprParser.safe_float(raw) if raw is not None else None

    @staticmethod
    def get_optional_int(
        sexpr: SExpr, token_name: str, index: int = 1
    ) -> Optional[int]:
        """Get optional int value from token"""
        token = SExprParser.find_token(sexpr, token_name)
        if token is None:
            return None
        raw = SExprParser.get_value(token, index)
        return SExprParser.safe_int(raw) if raw is not None else None

    @staticmethod
    def get_required_str(
        sexpr: SExpr, token_name: str, index: int = 1, default: Optional[str] = None
    ) -> str:
        """Get required string value, raise if missing (unless default provided)"""
        token = SExprParser.find_token(sexpr, token_name)
        if token is None:
            if default is not None:
                return default  # Robustness: return default if provided
            raise ValueError(f"Required token '{token_name}' not found")
        raw = SExprParser.get_value(token, index)
        return str(raw) if raw is not None else (default or "")

    @staticmethod
    def get_required_float(
        sexpr: SExpr, token_name: str, index: int = 1, default: Optional[float] = None
    ) -> float:
        """Get required float value, raise if missing (unless default provided)"""
        token = SExprParser.find_token(sexpr, token_name)
        if token is None:
            if default is not None:
                return default  # Robustness: return default if provided
            raise ValueError(f"Required token '{token_name}' not found")
        raw = SExprParser.get_value(token, index)
        return SExprParser.safe_float(raw, default if default is not None else 0.0)

    @staticmethod
    def get_required_int(
        sexpr: SExpr, token_name: str, index: int = 1, default: Optional[int] = None
    ) -> int:
        """Get required int value, raise if missing (unless default provided)"""
        token = SExprParser.find_token(sexpr, token_name)
        if token is None:
            if default is not None:
                return default  # Robustness: return default if provided
            raise ValueError(f"Required token '{token_name}' not found")
        raw = SExprParser.get_value(token, index)
        return SExprParser.safe_int(raw, default if default is not None else 0)

    @staticmethod
    def get_optional_position(sexpr: SExpr, token_name: str) -> Optional["Position"]:
        """Get optional Position from token (X Y values)"""
        token = SExprParser.find_token(sexpr, token_name)
        if token is None:
            return None
        x = SExprParser.safe_float(SExprParser.get_value(token, 1), 0.0)
        y = SExprParser.safe_float(SExprParser.get_value(token, 2), 0.0)
        return Position(x, y)

    @staticmethod
    def get_required_position(
        sexpr: SExpr, token_name: str, default: Optional["Position"] = None
    ) -> "Position":
        """Get required Position from token, raise if missing (unless default provided)"""
        token = SExprParser.find_token(sexpr, token_name)
        if token is None:
            if default is not None:
                return default  # Robustness: return default if provided
            raise ValueError(f"Required token '{token_name}' not found")
        x = SExprParser.safe_float(SExprParser.get_value(token, 1), 0.0)
        y = SExprParser.safe_float(SExprParser.get_value(token, 2), 0.0)
        return Position(x, y)

    @staticmethod
    def get_position_with_default(
        sexpr: SExpr, token_name: str, default_x: float = 0.0, default_y: float = 0.0
    ) -> "Position":
        """Get Position from token with default values"""
        token = SExprParser.find_token(sexpr, token_name)
        if token is None:
            return Position(default_x, default_y)
        x = SExprParser.safe_float(SExprParser.get_value(token, 1), default_x)
        y = SExprParser.safe_float(SExprParser.get_value(token, 2), default_y)
        return Position(x, y)

    # Position-based safe getters for direct S-expression parsing
    @staticmethod
    def safe_get_str(sexpr: SExpr, index: int, default: str = "") -> str:
        """Get string value by index with safe fallback"""
        raw = SExprParser.get_value(sexpr, index)
        return str(raw) if raw is not None else default

    @staticmethod
    def safe_get_int(sexpr: SExpr, index: int, default: int = 0) -> int:
        """Get int value by index with safe fallback"""
        raw = SExprParser.get_value(sexpr, index)
        return SExprParser.safe_int(raw, default)

    @staticmethod
    def safe_get_float(sexpr: SExpr, index: int, default: float = 0.0) -> float:
        """Get float value by index with safe fallback"""
        raw = SExprParser.get_value(sexpr, index)
        return SExprParser.safe_float(raw, default)


# Common data structures


@dataclass
class Position:
    """Position identifier (at X Y [ANGLE]) or (xyz X Y Z)"""

    x: float = 0.0
    y: float = 0.0
    angle: float = 0.0
    z: Optional[float] = None  # For 3D coordinates (xyz format)

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "Position":
        # Handle different formats: (at X Y [ANGLE]) and (xyz X Y Z)
        if not sexpr or len(sexpr) < 2:
            return cls()

        # Check if this is an xyz token with nested xyz format
        if len(sexpr) >= 2 and isinstance(sexpr[1], list) and len(sexpr[1]) >= 1:
            if str(sexpr[1][0]) == "xyz":
                # Format: (offset (xyz X Y Z)) - get xyz sublist
                xyz_list = sexpr[1]
                return cls(
                    x=SExprParser.safe_float(SExprParser.get_value(xyz_list, 1), 0.0),
                    y=SExprParser.safe_float(SExprParser.get_value(xyz_list, 2), 0.0),
                    z=SExprParser.safe_float(SExprParser.get_value(xyz_list, 3), 0.0),
                    angle=0.0,
                )

        # Standard format: (at X Y [ANGLE])
        return cls(
            x=SExprParser.safe_float(SExprParser.get_value(sexpr, 1), 0.0),
            y=SExprParser.safe_float(SExprParser.get_value(sexpr, 2), 0.0),
            angle=SExprParser.safe_float(SExprParser.get_value(sexpr, 3), 0.0),
        )

    def to_sexpr(self, token: str = "at") -> SExpr:
        if self.z is not None:
            # 3D format: (token (xyz X Y Z))
            return [Symbol(token), [Symbol("xyz"), self.x, self.y, self.z]]
        else:
            # 2D format: (token X Y [ANGLE])
            result: SExpr = [Symbol(token), self.x, self.y]
            if self.angle != 0.0:
                result.append(self.angle)
            return result


@dataclass
class CoordinatePoint:
    """Single X/Y coordinate point"""

    x: float
    y: float

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "CoordinatePoint":
        """Parse from (xy X Y) format"""
        return cls(
            x=SExprParser.get_value(sexpr, 1, 0.0),
            y=SExprParser.get_value(sexpr, 2, 0.0),
        )

    def to_sexpr(self) -> SExpr:
        return [Symbol("xy"), self.x, self.y]


@dataclass
class CoordinatePointList:
    """List of coordinate points (pts ...)"""

    points: List[CoordinatePoint] = field(default_factory=list)

    def __init__(
        self,
        points: Optional[Sequence[Union[CoordinatePoint, Tuple[float, float]]]] = None,
    ) -> None:
        if points is None:
            self.points = []
        elif isinstance(points, list):
            self.points = []
            for point in points:
                if isinstance(point, tuple):
                    # Convert tuple (x, y) to CoordinatePoint
                    self.points.append(CoordinatePoint(x=point[0], y=point[1]))
                elif isinstance(point, CoordinatePoint):
                    self.points.append(point)
                else:
                    raise ValueError(f"Invalid point type: {type(point)}")
        else:
            raise ValueError(f"Invalid points type: {type(points)}")

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "CoordinatePointList":
        points = []
        for item in sexpr[1:]:
            if isinstance(item, list) and len(item) > 0 and item[0] == Symbol("xy"):
                points.append(CoordinatePoint.from_sexpr(item))
        return cls(points=points)

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("pts")]
        result.extend([point.to_sexpr() for point in self.points])
        return result

    def __len__(self) -> int:
        return len(self.points)

    def __getitem__(self, index: int) -> tuple:
        point = self.points[index]
        return (point.x, point.y)


class StrokeType(Enum):
    """Valid stroke line styles"""

    DASH = "dash"
    DASH_DOT = "dash_dot"
    DASH_DOT_DOT = "dash_dot_dot"
    DOT = "dot"
    DEFAULT = "default"
    SOLID = "solid"


@dataclass
class Stroke:
    """Stroke definition for graphical objects"""

    width: float = 0.254
    type: StrokeType = StrokeType.SOLID
    color: Optional[Tuple[float, float, float, float]] = None  # R, G, B, A

    def __post_init__(self) -> None:
        # Convert string type to StrokeType enum if needed
        if isinstance(self.type, str):
            try:
                self.type = StrokeType(self.type)
            except ValueError:
                # If the string doesn't match any enum value, default to SOLID
                self.type = StrokeType.SOLID

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "Stroke":
        return cls(
            width=SExprParser.get_optional_float(sexpr, "width") or 0.254,
            type=SExprParser.parse_enum(
                SExprParser.get_optional_str(sexpr, "type"),
                StrokeType,
                StrokeType.SOLID,
            ),
            color=(
                tuple(color_token[1:5])
                if (color_token := SExprParser.find_token(sexpr, "color"))
                and len(color_token) >= 5
                else None
            ),
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("stroke"), [Symbol("width"), self.width]]
        if self.type != StrokeType.SOLID:
            result.append([Symbol("type"), Symbol(self.type.value)])
        if self.color:
            result.append([Symbol("color")] + list(self.color))
        return result


@dataclass
class Font:
    """Font definition within text effects"""

    size_height: float = 1.27
    size_width: float = 1.27
    thickness: Optional[float] = None
    bold: bool = False
    italic: bool = False
    face: Optional[str] = None
    line_spacing: Optional[float] = None

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "Font":
        size_token = SExprParser.find_token(sexpr, "size")

        return cls(
            size_height=(
                SExprParser.get_value(size_token, 1, 1.27) if size_token else 1.27
            ),
            size_width=(
                SExprParser.get_value(size_token, 2, 1.27) if size_token else 1.27
            ),
            thickness=SExprParser.get_optional_float(sexpr, "thickness"),
            bold=SExprParser.has_symbol(sexpr, "bold"),
            italic=SExprParser.has_symbol(sexpr, "italic"),
            face=SExprParser.get_optional_str(sexpr, "face"),
            line_spacing=SExprParser.get_optional_float(sexpr, "line_spacing"),
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("font")]
        if self.face:
            result.append([Symbol("face"), self.face])
        result.append([Symbol("size"), self.size_height, self.size_width])
        if self.thickness:
            result.append([Symbol("thickness"), self.thickness])
        if self.bold:
            result.append(Symbol("bold"))
        if self.italic:
            result.append(Symbol("italic"))
        if self.line_spacing:
            result.append([Symbol("line_spacing"), self.line_spacing])
        return result


class JustifyHorizontal(Enum):
    LEFT = "left"
    RIGHT = "right"
    CENTER = "center"


class JustifyVertical(Enum):
    TOP = "top"
    BOTTOM = "bottom"
    CENTER = "center"


@dataclass
class TextEffects:
    """Text effects definition"""

    font: Font = field(default_factory=Font)
    justify_horizontal: JustifyHorizontal = JustifyHorizontal.CENTER
    justify_vertical: JustifyVertical = JustifyVertical.CENTER
    mirror: bool = False
    hide: bool = False

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "TextEffects":
        font_token = SExprParser.find_token(sexpr, "font")
        justify_token = SExprParser.find_token(sexpr, "justify")

        justify_h = JustifyHorizontal.CENTER
        justify_v = JustifyVertical.CENTER
        mirror = False

        if justify_token:
            for item in justify_token[1:]:
                if item == Symbol("left"):
                    justify_h = JustifyHorizontal.LEFT
                elif item == Symbol("right"):
                    justify_h = JustifyHorizontal.RIGHT
                elif item == Symbol("top"):
                    justify_v = JustifyVertical.TOP
                elif item == Symbol("bottom"):
                    justify_v = JustifyVertical.BOTTOM
                elif item == Symbol("mirror"):
                    mirror = True

        return cls(
            font=Font.from_sexpr(font_token) if font_token else Font(),
            justify_horizontal=justify_h,
            justify_vertical=justify_v,
            mirror=mirror,
            hide=SExprParser.has_symbol(sexpr, "hide"),
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("effects")]
        result.append(self.font.to_sexpr())

        # Add justify if not center
        justify_parts = []
        if self.justify_horizontal != JustifyHorizontal.CENTER:
            justify_parts.append(Symbol(self.justify_horizontal.value))
        if self.justify_vertical != JustifyVertical.CENTER:
            justify_parts.append(Symbol(self.justify_vertical.value))
        if self.mirror:
            justify_parts.append(Symbol("mirror"))

        if justify_parts:
            result.append([Symbol("justify")] + justify_parts)

        if self.hide:
            result.append(Symbol("hide"))

        return result


class FillType(Enum):
    """Fill types for graphical objects"""

    NONE = "none"
    OUTLINE = "outline"
    BACKGROUND = "background"


@dataclass
class Fill:
    """Fill definition for graphical objects"""

    type: FillType = FillType.NONE

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "Fill":
        type_str = SExprParser.get_optional_str(sexpr, "type") or "none"
        try:
            fill_type = FillType(type_str)
        except ValueError:
            fill_type = FillType.NONE
        return cls(type=fill_type)

    def to_sexpr(self) -> SExpr:
        return [Symbol("fill"), [Symbol("type"), Symbol(self.type.value)]]


@dataclass
class Property:
    """Generic property (key-value pair)"""

    key: str
    value: str
    id: Optional[int] = None
    position: Optional[Position] = None
    effects: Optional[TextEffects] = None

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "Property":
        # Parse key and value (always at indices 1 and 2)
        key = SExprParser.normalize_text_content(
            str(SExprParser.get_value(sexpr, 1, ""))
        )
        value = SExprParser.normalize_text_content(
            str(SExprParser.get_value(sexpr, 2, ""))
        )

        # Parse optional attributes
        id_token = SExprParser.find_token(sexpr, "id")
        id_val = None
        if id_token:
            try:
                id_val = int(SExprParser.get_value(id_token, 1))
            except (ValueError, TypeError):
                pass

        at_token = SExprParser.find_token(sexpr, "at")
        position = Position.from_sexpr(at_token) if at_token else None

        effects_token = SExprParser.find_token(sexpr, "effects")
        effects = TextEffects.from_sexpr(effects_token) if effects_token else None

        return cls(
            key=key,
            value=value,
            id=id_val,
            position=position,
            effects=effects,
        )

    def to_sexpr(self) -> SExpr:
        result = [Symbol("property"), self.key, self.value]
        if self.id is not None:
            result.append([Symbol("id"), self.id])
        if self.position is not None:
            result.append(self.position.to_sexpr())
        if self.effects is not None:
            result.append(self.effects.to_sexpr())
        return result


@dataclass
class UUID:
    """Universally Unique Identifier"""

    uuid: str

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "UUID":
        return cls(uuid=str(SExprParser.get_value(sexpr, 1, "")))

    def to_sexpr(self) -> SExpr:
        return [Symbol("uuid"), self.uuid]


class PaperSize(Enum):
    """Standard paper sizes"""

    A0 = "A0"
    A1 = "A1"
    A2 = "A2"
    A3 = "A3"
    A4 = "A4"
    A5 = "A5"
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"


@dataclass
class PageSettings:
    """Page settings definition"""

    paper_size: Optional[PaperSize] = None
    custom_width: Optional[float] = None
    custom_height: Optional[float] = None
    portrait: bool = False

    @property
    def width(self) -> float:
        """Get page width based on paper size or custom dimensions"""
        if self.custom_width is not None:
            return self.custom_width
        elif self.paper_size == PaperSize.A4:
            return 297.0 if not self.portrait else 210.0
        elif self.paper_size == PaperSize.A3:
            return 420.0 if not self.portrait else 297.0
        elif self.paper_size == PaperSize.A2:
            return 594.0 if not self.portrait else 420.0
        elif self.paper_size == PaperSize.A1:
            return 841.0 if not self.portrait else 594.0
        elif self.paper_size == PaperSize.A0:
            return 1189.0 if not self.portrait else 841.0
        elif self.paper_size == PaperSize.A:
            return 279.4 if not self.portrait else 215.9
        elif self.paper_size == PaperSize.B:
            return 431.8 if not self.portrait else 279.4
        elif self.paper_size == PaperSize.C:
            return 558.8 if not self.portrait else 431.8
        elif self.paper_size == PaperSize.D:
            return 863.6 if not self.portrait else 558.8
        elif self.paper_size == PaperSize.E:
            return 1117.6 if not self.portrait else 863.6
        return 297.0  # Default A4 width

    @property
    def height(self) -> float:
        """Get page height based on paper size or custom dimensions"""
        if self.custom_height is not None:
            return self.custom_height
        elif self.paper_size == PaperSize.A4:
            return 210.0 if not self.portrait else 297.0
        elif self.paper_size == PaperSize.A3:
            return 297.0 if not self.portrait else 420.0
        elif self.paper_size == PaperSize.A2:
            return 420.0 if not self.portrait else 594.0
        elif self.paper_size == PaperSize.A1:
            return 594.0 if not self.portrait else 841.0
        elif self.paper_size == PaperSize.A0:
            return 841.0 if not self.portrait else 1189.0
        elif self.paper_size == PaperSize.A:
            return 215.9 if not self.portrait else 279.4
        elif self.paper_size == PaperSize.B:
            return 279.4 if not self.portrait else 431.8
        elif self.paper_size == PaperSize.C:
            return 431.8 if not self.portrait else 558.8
        elif self.paper_size == PaperSize.D:
            return 558.8 if not self.portrait else 863.6
        elif self.paper_size == PaperSize.E:
            return 863.6 if not self.portrait else 1117.6
        return 210.0  # Default A4 height

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "PageSettings":
        portrait = SExprParser.has_symbol(sexpr, "portrait")

        # Check if it's a standard size or custom dimensions
        if len(sexpr) >= 2:
            size_str = str(sexpr[1])
            try:
                paper_size = PaperSize(size_str)
                return cls(paper_size=paper_size, portrait=portrait)
            except ValueError:
                # Must be custom dimensions
                if len(sexpr) >= 3:
                    return cls(
                        custom_width=float(sexpr[1]),
                        custom_height=float(sexpr[2]),
                        portrait=portrait,
                    )

        return cls(portrait=portrait)

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("paper")]

        if self.paper_size:
            result.append(self.paper_size.value)
        elif self.custom_width is not None and self.custom_height is not None:
            result.extend([self.custom_width, self.custom_height])

        if self.portrait:
            result.append(Symbol("portrait"))

        return result


@dataclass
class TitleBlock:
    """Title block definition"""

    title: str = ""
    date: str = ""
    revision: str = ""
    company: str = ""
    comments: Dict[int, str] = field(default_factory=dict)

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "TitleBlock":
        title_token = SExprParser.find_token(sexpr, "title")
        date_token = SExprParser.find_token(sexpr, "date")
        rev_token = SExprParser.find_token(sexpr, "rev")
        company_token = SExprParser.find_token(sexpr, "company")

        comments = {}
        comment_tokens = SExprParser.find_all_tokens(sexpr, "comment")
        for token in comment_tokens:
            if len(token) >= 3:
                comments[int(token[1])] = str(token[2])

        return cls(
            title=str(SExprParser.get_value(title_token, 1)) if title_token else "",
            date=str(SExprParser.get_value(date_token, 1)) if date_token else "",
            revision=str(SExprParser.get_value(rev_token, 1)) if rev_token else "",
            company=(
                str(SExprParser.get_value(company_token, 1)) if company_token else ""
            ),
            comments=comments,
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("title_block")]

        if self.title:
            result.append([Symbol("title"), self.title])
        if self.date:
            result.append([Symbol("date"), self.date])
        if self.revision:
            result.append([Symbol("rev"), self.revision])
        if self.company:
            result.append([Symbol("company"), self.company])

        for num, comment in self.comments.items():
            result.append([Symbol("comment"), num, comment])

        return result


@dataclass
class Image:
    """Embedded image definition"""

    position: Position
    scale: Optional[float] = None
    layer: Optional[str] = None
    uuid: Optional[UUID] = None
    data: Optional[str] = None

    @property
    def layers(self) -> List[str]:
        """Return layers as a list for compatibility"""
        return [self.layer] if self.layer else []

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "Image":
        # Find position (at token)
        at_token = SExprParser.find_token(sexpr, "at")
        scale_token = SExprParser.find_token(sexpr, "scale")
        layer_token = SExprParser.find_token(sexpr, "layer")
        uuid_token = SExprParser.find_token(sexpr, "uuid")
        data_token = SExprParser.find_token(sexpr, "data")

        return cls(
            position=Position.from_sexpr(at_token) if at_token else Position(0, 0),
            scale=SExprParser.get_value(scale_token, 1) if scale_token else None,
            layer=SExprParser.get_value(layer_token, 1) if layer_token else None,
            uuid=UUID.from_sexpr(uuid_token) if uuid_token else None,
            data=SExprParser.get_value(data_token, 1) if data_token else None,
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("image")]
        result.append(self.position.to_sexpr())

        if self.scale:
            result.append([Symbol("scale"), self.scale])
        if self.layer:
            result.append([Symbol("layer"), self.layer])
        if self.uuid:
            result.append(self.uuid.to_sexpr())
        if self.data:
            result.append([Symbol("data"), self.data])

        return result


# Abstract base classes


class KiCadObject(ABC):
    """Base class for all KiCad objects"""

    @classmethod
    @abstractmethod
    def from_sexpr(cls, sexpr: SExpr) -> "KiCadObject":
        """Parse object from S-Expression"""
        pass

    @abstractmethod
    def to_sexpr(self) -> SExpr:
        """Convert object to S-Expression"""
        pass


# UUID generation utility


def generate_UUID() -> "UUID":
    """Generate a new UUID for KiCad objects

    Returns:
        UUID: A new randomly generated UUID
    """
    return UUID(str(python_uuid.uuid4()))


# High-level parsing utilities


def parse_kicad_file(content: str, root_parser_class: Any) -> KiCadObject:
    """Generic KiCad file parser

    Args:
        content: S-expression file content string
        root_parser_class: Parser class with from_sexpr method

    Returns:
        KiCadObject: Parsed KiCad object

    Raises:
        ValueError: If content cannot be parsed as S-expression
        AttributeError: If parser_class lacks from_sexpr method
    """
    sexpr = str_to_sexpr(content)
    return cast(KiCadObject, root_parser_class.from_sexpr(sexpr))


def write_kicad_file(obj: KiCadObject) -> str:
    """Generic KiCad file writer"""
    return sexpr_to_str(obj.to_sexpr(), pretty_print=True)
