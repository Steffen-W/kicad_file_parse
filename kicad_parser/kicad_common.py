"""
KiCad S-Expression Common Types and Utilities

This module contains common data structures and utilities shared across
all KiCad file formats (symbol libraries, footprint libraries, schematics, boards).
"""

from __future__ import annotations

import re
import uuid as python_uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, cast

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
    def parse_stroke_or_width(
        sexpr: SExpr, default_width: float = 0.254
    ) -> "StrokeDefinition":
        """Parse stroke with legacy width fallback"""
        stroke_token = SExprParser.find_token(sexpr, "stroke")
        width_token = SExprParser.find_token(sexpr, "width")

        if stroke_token:
            return StrokeDefinition.from_sexpr(stroke_token)
        elif width_token:
            return StrokeDefinition(
                width=SExprParser.safe_float(
                    SExprParser.get_value(width_token, 1), default_width
                )
            )
        else:
            return StrokeDefinition(width=default_width)

    @staticmethod
    def validate_token_length(token: List, min_length: int) -> bool:
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
    def get_optional_bool_flag(sexpr: SExpr, symbol_name: str) -> Optional[bool]:
        """Get optional boolean flag from symbol presence.

        Returns:
            True if symbol exists in sexpr, None if it doesn't
        """
        return True if SExprParser.has_symbol(sexpr, symbol_name) else None

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
    def from_sexpr(cls, sexpr: Optional[SExpr]) -> "Position":
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


class CoordinatePointList(KiCadObject):
    """List of X/Y coordinate points token.

    The 'pts' token defines a list of X/Y coordinate points in the format:
    (pts
        (xy X Y)
        ...
        (xy X Y)
    )

    Where each xy token defines a single X and Y coordinate pair.
    The number of points is determined by the object type.
    """

    __token_name__ = "pts"

    def __init__(self, points: Optional[List["XYCoordinate"]] = None) -> None:
        super().__init__()
        self.points = points or []

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "CoordinatePointList":
        if not sexpr:
            return cls()

        points = []
        for item in sexpr[1:]:
            if isinstance(item, list) and len(item) > 0 and item[0] == Symbol("xy"):
                points.append(XYCoordinate.from_sexpr(item))

        return cls(points=points)

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol(self.__token_name__)]
        result.extend([point.to_sexpr() for point in self.points])
        return result


class StrokeType(Enum):
    """Valid stroke line styles"""

    DASH = "dash"
    DASH_DOT = "dash_dot"
    DASH_DOT_DOT = "dash_dot_dot"
    DOT = "dot"
    DEFAULT = "default"
    SOLID = "solid"


class JustifyHorizontal(Enum):
    LEFT = "left"
    RIGHT = "right"
    CENTER = "center"


class JustifyVertical(Enum):
    TOP = "top"
    BOTTOM = "bottom"
    CENTER = "center"


class FootprintTextType(Enum):
    """Footprint text types"""

    REFERENCE = "reference"
    VALUE = "value"
    USER = "user"


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
        type_str = SExprParser.get_required_str(sexpr, "type", default="none")
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
    effects: Optional["TextEffectsDefinition"] = None

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
        id_val = SExprParser.get_optional_int(sexpr, "id")

        at_token = SExprParser.find_token(sexpr, "at")
        position = Position.from_sexpr(at_token) if at_token else None

        effects_token = SExprParser.find_token(sexpr, "effects")
        effects = (
            TextEffectsDefinition.from_sexpr(effects_token) if effects_token else None
        )

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


# Abstract base classes


class KiCadObject(ABC):
    """Base class for all KiCad objects"""

    # Class variable to store the token name - override in subclasses
    __token_name__: Optional[str] = None

    def __init__(self) -> None:
        # Instance variable to track if token exists in parsed data
        self.__token_exists__: bool = False

    @classmethod
    def auto_parse(cls, sexpr: SExpr) -> Optional["KiCadObject"]:
        """Automatically find and parse token if it exists

        Returns:
            Optional[KiCadObject]: Parsed object if token found, None otherwise
        """
        if cls.__token_name__ is None:
            raise ValueError(f"Class {cls.__name__} must define __token_name__")

        # Find the token in the S-Expression
        token = SExprParser.find_token(sexpr, cls.__token_name__)
        if token is None:
            return None

        # Create instance and mark token as existing
        instance = cls.from_sexpr(token)
        instance.__token_exists__ = True
        return instance

    @classmethod
    def try_parse(cls, sexpr: SExpr) -> "KiCadObject":
        """Try to parse token, create empty instance if not found

        Returns:
            KiCadObject: Parsed object or default instance if token missing
        """
        result = cls.auto_parse(sexpr)
        if result is None:
            # Create default instance if token not found
            result = cls._create_default()
            result.__token_exists__ = False
        return result

    @classmethod
    def _create_default(cls) -> "KiCadObject":
        """Create default instance when token is not found

        Override in subclasses to provide meaningful defaults
        """
        # This will call the abstract from_sexpr with empty list
        # Subclasses should handle this case gracefully
        try:
            return cls.from_sexpr([])
        except:
            raise NotImplementedError(
                f"Class {cls.__name__} must implement _create_default() or handle empty S-Expression in from_sexpr()"
            )

    def token_exists(self) -> bool:
        """Check if the token was found during parsing"""
        return getattr(self, "__token_exists__", False)

    def to_sexpr_if_exists(self) -> Optional[SExpr]:
        """Convert to S-Expression only if token existed during parsing

        Returns:
            Optional[SExpr]: S-Expression if token existed, None otherwise
        """
        return self.to_sexpr() if self.token_exists() else None

    @classmethod
    @abstractmethod
    def from_sexpr(cls, sexpr: SExpr) -> "KiCadObject":
        """Parse object from S-Expression"""
        pass

    @abstractmethod
    def to_sexpr(self) -> SExpr:
        """Convert object to S-Expression"""
        pass


class PositionIdentifier(KiCadObject):
    """Position identifier token that defines positional coordinates and rotation of an object.

    The 'at' token defines the positional coordinates and rotation of an object in the format:
    (at X Y [ANGLE])

    Where:
        X: The horizontal position of the object
        Y: The vertical position of the object
        ANGLE: Optional rotational angle of the object (not all objects have rotational definitions)

    Note: Symbol text ANGLEs are stored in tenth's of a degree. All other ANGLEs are stored in degrees.
    """

    __token_name__ = "at"

    def __init__(self, x: float = 0.0, y: float = 0.0, angle: float = 0.0) -> None:
        super().__init__()
        self.x = x
        self.y = y
        self.angle = angle

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "PositionIdentifier":
        if not sexpr:
            return cls()

        x = SExprParser.safe_float(SExprParser.get_value(sexpr, 1), 0.0)
        y = SExprParser.safe_float(SExprParser.get_value(sexpr, 2), 0.0)
        angle = SExprParser.safe_float(SExprParser.get_value(sexpr, 3), 0.0)

        return cls(x=x, y=y, angle=angle)

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol(self.__token_name__), self.x, self.y]
        if self.angle != 0.0:
            result.append(self.angle)
        return result


class XYCoordinate(KiCadObject):
    """Single X/Y coordinate pair token.

    The 'xy' token defines a single X and Y coordinate pair in the format:
    (xy X Y)

    Where:
        X: The horizontal coordinate value
        Y: The vertical coordinate value
    """

    __token_name__ = "xy"

    def __init__(self, x: float = 0.0, y: float = 0.0) -> None:
        super().__init__()
        self.x = x
        self.y = y

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "XYCoordinate":
        if not sexpr:
            return cls()

        x = SExprParser.safe_float(SExprParser.get_value(sexpr, 1), 0.0)
        y = SExprParser.safe_float(SExprParser.get_value(sexpr, 2), 0.0)

        return cls(x=x, y=y)

    def to_sexpr(self) -> SExpr:
        return [Symbol(self.__token_name__), self.x, self.y]


class StrokeDefinition(KiCadObject):
    """Stroke definition that defines how outlines of graphical objects are drawn.

    The 'stroke' token defines how the outlines of graphical objects are drawn in the format:
    (stroke
        (width WIDTH)
        (type TYPE)
        (color R G B A)
    )

    Where:
        width: The line width of the graphic object
        type: The line style of the graphic object (dash, dash_dot, dash_dot_dot, dot, default, solid)
        color: The line red, green, blue, and alpha color settings (optional)
    """

    __token_name__ = "stroke"

    def __init__(
        self,
        width: float = 0.254,
        stroke_type: StrokeType = StrokeType.SOLID,
        color: Optional[Tuple[float, float, float, float]] = None,
    ) -> None:
        super().__init__()
        self.width = width
        self.stroke_type = stroke_type
        self.color = color

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "StrokeDefinition":
        if not sexpr:
            return cls()

        width = SExprParser.get_required_float(sexpr, "width", default=0.254)

        type_str = SExprParser.get_optional_str(sexpr, "type")
        stroke_type = StrokeType.SOLID
        if type_str:
            stroke_type = StrokeType(type_str)

        color = None
        color_token = SExprParser.find_token(sexpr, "color")
        if color_token and len(color_token) >= 5:
            color = (
                SExprParser.safe_float(color_token[1]),
                SExprParser.safe_float(color_token[2]),
                SExprParser.safe_float(color_token[3]),
                SExprParser.safe_float(color_token[4]),
            )

        return cls(width=width, stroke_type=stroke_type, color=color)

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol(self.__token_name__), [Symbol("width"), self.width]]
        if self.stroke_type != StrokeType.SOLID:
            result.append([Symbol("type"), Symbol(self.stroke_type.value)])
        if self.color:
            result.append([Symbol("color")] + list(self.color))
        return result


class FontDefinition(KiCadObject):
    """Font definition that defines how text is shown.

    The 'font' token defines how the text is shown in the format:
    (font
        [(face FACE_NAME)]
        (size HEIGHT WIDTH)
        [(thickness THICKNESS)]
        [bold]
        [italic]
        [(line_spacing LINE_SPACING)]
    )

    Where:
        face: Optional font family name (TrueType font family or "KiCad Font")
        size: Font height and width
        thickness: Line thickness of the font (optional)
        bold: Bold text flag (optional)
        italic: Italic text flag (optional)
        line_spacing: Spacing between lines as ratio of standard line-spacing (optional, not yet supported)
    """

    __token_name__ = "font"

    def __init__(
        self,
        size_height: float = 1.27,
        size_width: float = 1.27,
        face: Optional[str] = None,
        thickness: Optional[float] = None,
        bold: bool = False,
        italic: bool = False,
        line_spacing: Optional[float] = None,
    ) -> None:
        super().__init__()
        self.size_height = size_height
        self.size_width = size_width
        self.face = face
        self.thickness = thickness
        self.bold = bold
        self.italic = italic
        self.line_spacing = line_spacing

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "FontDefinition":
        if not sexpr:
            return cls()

        size_token = SExprParser.find_token(sexpr, "size")
        size_height = 1.27
        size_width = 1.27
        if size_token:
            size_height = SExprParser.safe_float(
                SExprParser.get_value(size_token, 1), 1.27
            )
            size_width = SExprParser.safe_float(
                SExprParser.get_value(size_token, 2), 1.27
            )

        return cls(
            size_height=size_height,
            size_width=size_width,
            face=SExprParser.get_optional_str(sexpr, "face"),
            thickness=SExprParser.get_optional_float(sexpr, "thickness"),
            bold=SExprParser.has_symbol(sexpr, "bold"),
            italic=SExprParser.has_symbol(sexpr, "italic"),
            line_spacing=SExprParser.get_optional_float(sexpr, "line_spacing"),
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol(self.__token_name__)]
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


class TextEffectsDefinition(KiCadObject):
    """Text effects definition that defines how text is displayed.

    The 'effects' token defines how text objects are displayed in the format:
    (effects
        (font ...)
        [(justify [left | right] [top | bottom] [mirror])]
        [hide]
    )

    Where:
        font: Font definition for the text
        justify: Text justification (horizontal: left/right, vertical: top/bottom, mirror flag)
        hide: Optional flag to hide the text

    Note: Mirror token is only supported in PCB Editor and Footprints.
    Default justification is center both horizontally and vertically without mirroring.
    """

    __token_name__ = "effects"

    def __init__(
        self,
        font: Optional[FontDefinition] = None,
        justify_horizontal: JustifyHorizontal = JustifyHorizontal.CENTER,
        justify_vertical: JustifyVertical = JustifyVertical.CENTER,
        mirror: bool = False,
        hide: bool = False,
    ) -> None:
        super().__init__()
        self.font = font or FontDefinition()
        self.justify_horizontal = justify_horizontal
        self.justify_vertical = justify_vertical
        self.mirror = mirror
        self.hide = hide

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "TextEffectsDefinition":
        if not sexpr:
            return cls()

        font_token = SExprParser.find_token(sexpr, "font")
        font = FontDefinition.from_sexpr(font_token) if font_token else FontDefinition()

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
            font=font,
            justify_horizontal=justify_h,
            justify_vertical=justify_v,
            mirror=mirror,
            hide=SExprParser.has_symbol(sexpr, "hide"),
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol(self.__token_name__)]
        result.append(self.font.to_sexpr())

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


class PageSettings(KiCadObject):
    """Page settings definition that defines the drawing page size and orientation.

    The 'paper' token defines the drawing page size and orientation in the format:
    (paper
        PAPER_SIZE | WIDTH HEIGHT
        [portrait]
    )

    Where:
        PAPER_SIZE: Valid page sizes are A0, A1, A2, A3, A4, A5, A, B, C, D, and E
        WIDTH HEIGHT: Custom user defined page sizes (alternative to PAPER_SIZE)
        portrait: Optional flag for portrait mode (landscape is default)
    """

    __token_name__ = "paper"

    def __init__(
        self,
        paper_size: Optional[PaperSize] = None,
        custom_width: Optional[float] = None,
        custom_height: Optional[float] = None,
        portrait: bool = False,
    ) -> None:
        super().__init__()
        self.paper_size = paper_size
        self.custom_width = custom_width
        self.custom_height = custom_height
        self.portrait = portrait

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
        if not sexpr:
            return cls()

        portrait = SExprParser.has_symbol(sexpr, "portrait")

        if len(sexpr) >= 2:
            size_str = str(sexpr[1])
            paper_size = None
            for ps in PaperSize:
                if ps.value == size_str:
                    paper_size = ps
                    break

            if paper_size:
                return cls(paper_size=paper_size, portrait=portrait)
            elif len(sexpr) >= 3:
                return cls(
                    custom_width=float(sexpr[1]),
                    custom_height=float(sexpr[2]),
                    portrait=portrait,
                )

        return cls(portrait=portrait)

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol(self.__token_name__)]

        if self.paper_size:
            result.append(self.paper_size.value)
        elif self.custom_width is not None and self.custom_height is not None:
            result.extend([self.custom_width, self.custom_height])

        if self.portrait:
            result.append(Symbol("portrait"))

        return result


class TitleBlock(KiCadObject):
    """Title block definition that defines the contents of the title block.

    The 'title_block' token defines the contents of the title block in the format:
    (title_block
        (title "TITLE")
        (date "DATE")
        (rev "REVISION")
        (company "COMPANY_NAME")
        (comment N "COMMENT")
    )

    Where:
        title: Quoted string that defines the document title
        date: Quoted string that defines the document date using YYYY-MM-DD format
        rev: Quoted string that defines the document revision
        company: Quoted string that defines the document company name
        comment: Document comments where N is a number from 1 to 9 and COMMENT is a quoted string
    """

    __token_name__ = "title_block"

    def __init__(
        self,
        title: str = "",
        date: str = "",
        revision: str = "",
        company: str = "",
        comments: Optional[Dict[int, str]] = None,
    ) -> None:
        super().__init__()
        self.title = title
        self.date = date
        self.revision = revision
        self.company = company
        self.comments = comments or {}

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "TitleBlock":
        if not sexpr:
            return cls()

        comments = {}
        comment_tokens = SExprParser.find_all_tokens(sexpr, "comment")
        for token in comment_tokens:
            if len(token) >= 3:
                comments[int(token[1])] = str(token[2])

        return cls(
            title=SExprParser.get_required_str(sexpr, "title", default=""),
            date=SExprParser.get_required_str(sexpr, "date", default=""),
            revision=SExprParser.get_required_str(sexpr, "rev", default=""),
            company=SExprParser.get_required_str(sexpr, "company", default=""),
            comments=comments,
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol(self.__token_name__)]

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


class UUID(KiCadObject):
    """Universally Unique Identifier definition.

    The 'uuid' token defines a universally unique identifier in the format:
    (uuid UUID)

    Where:
        UUID: A Version 4 (random) UUID that should be globally unique

    Note: KiCad UUIDs are generated using the mt19937 Mersenne Twister algorithm.
    Files converted from legacy versions of KiCad (prior to 6.0) have their locally-unique
    timestamps re-encoded in UUID format.
    """

    __token_name__ = "uuid"

    def __init__(self, uuid: str = "") -> None:
        super().__init__()
        self.uuid = uuid

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "UUID":
        if not sexpr:
            return cls()

        uuid_value = str(SExprParser.get_value(sexpr, 1, ""))
        return cls(uuid=uuid_value)

    def to_sexpr(self) -> SExpr:
        return [Symbol(self.__token_name__), self.uuid]


class Image(KiCadObject):
    """Embedded image definition.

    The 'image' token defines an embedded image in the format:
    (image
        POSITION_IDENTIFIER
        [(scale SCALAR)]
        [(layer LAYER_DEFINITIONS)]
        UNIQUE_IDENTIFIER
        (data IMAGE_DATA)
    )

    Where:
        POSITION_IDENTIFIER: X and Y coordinates of the image
        scale: Optional scale factor of the image
        layer: Associated board layer using canonical layer name (board and footprint images only)
        UNIQUE_IDENTIFIER: Universally unique identifier for the image
        data: Image data in PNG format encoded with MIME type base64

    Note: This section will not exist if no images are present.
    """

    __token_name__ = "image"

    def __init__(
        self,
        position: Optional[Position] = None,
        scale: Optional[float] = None,
        layer: Optional[str] = None,
        uuid: Optional[UUID] = None,
        data: Optional[str] = None,
    ) -> None:
        super().__init__()
        self.position = position or Position()
        self.scale = scale
        self.layer = layer
        self.uuid = uuid
        self.data = data

    @property
    def layers(self) -> List[str]:
        """Return layers as a list for compatibility"""
        return [self.layer] if self.layer else []

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "Image":
        if not sexpr:
            return cls()

        at_token = SExprParser.find_token(sexpr, "at")
        position = Position.from_sexpr(at_token) if at_token else Position()

        uuid_token = SExprParser.find_token(sexpr, "uuid")
        uuid_obj = UUID.from_sexpr(uuid_token) if uuid_token else None

        return cls(
            position=position,
            scale=SExprParser.get_optional_float(sexpr, "scale"),
            layer=SExprParser.get_optional_str(sexpr, "layer"),
            uuid=uuid_obj,
            data=SExprParser.get_optional_str(sexpr, "data"),
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol(self.__token_name__)]
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


class Layer(KiCadObject):
    """Layer definition for drawable board and footprint objects.

    The 'layer' token defines which layer drawable objects exist on in the format:
    (layer LAYER_DEFINITION)

    Where:
        LAYER_DEFINITION: Canonical layer name(s) or wildcard patterns

    Layer definitions can be specified as:
        - One or more canonical layer names
        - Wildcard '*' to represent all layers matching the pattern
        - Example: '*.Cu' represents all copper layers

    Layer Capacity:
        - 60 total layers
        - 32 copper layers
        - 8 paired technical layers (silk screen, solder mask, solder paste, adhesive)
        - 4 user pre-defined layers (drawings, ECO, comments)
        - 1 board outline layer
        - 1 board margins layer
        - 9 optional user definable layers

    Note: All layer names are canonical internally. User defined layer names are only
    used for display and output purposes.
    """

    __token_name__ = "layer"

    def __init__(self, layer_definition: str = "") -> None:
        super().__init__()
        self.layer_definition = layer_definition

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "Layer":
        if not sexpr:
            return cls()

        layer_def = str(SExprParser.get_value(sexpr, 1, ""))
        return cls(layer_definition=layer_def)

    def to_sexpr(self) -> SExpr:
        return [Symbol(self.__token_name__), self.layer_definition]


class FootprintText(KiCadObject):
    """Footprint text definition.

    The 'fp_text' token defines text in a footprint definition in the format:
    (fp_text
        TYPE
        "TEXT"
        POSITION_IDENTIFIER
        [unlocked]
        (layer LAYER_DEFINITION)
        [hide]
        (effects TEXT_EFFECTS)
        (uuid UUID)
    )

    Where:
        TYPE: Text type (reference, value, user)
        TEXT: Quoted string that defines the text
        POSITION_IDENTIFIER: X and Y position coordinates and optional orientation angle
        unlocked: Optional token indicating if text orientation can be non-upright
        layer: Canonical layer the text resides on
        hide: Optional token to hide the text
        effects: Text effects defining how text is displayed
        uuid: Unique identifier of the text object
    """

    __token_name__ = "fp_text"

    def __init__(
        self,
        text_type: FootprintTextType = FootprintTextType.USER,
        text: str = "",
        position: Optional[Position] = None,
        unlocked: bool = False,
        layer: Optional[str] = None,
        hide: bool = False,
        effects: Optional["TextEffectsDefinition"] = None,
        uuid: Optional[UUID] = None,
    ) -> None:
        super().__init__()
        self.text_type = text_type
        self.text = text
        self.position = position or Position()
        self.unlocked = unlocked
        self.layer = layer
        self.hide = hide
        self.effects = effects
        self.uuid = uuid

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "FootprintText":
        if not sexpr:
            return cls()

        text_type = FootprintTextType.USER
        if len(sexpr) > 1:
            type_str = str(sexpr[1])
            for ft in FootprintTextType:
                if ft.value == type_str:
                    text_type = ft
                    break

        text = str(SExprParser.get_value(sexpr, 2, ""))

        at_token = SExprParser.find_token(sexpr, "at")
        position = Position.from_sexpr(at_token) if at_token else Position()

        effects_token = SExprParser.find_token(sexpr, "effects")
        effects = (
            TextEffectsDefinition.from_sexpr(effects_token) if effects_token else None
        )

        uuid_token = SExprParser.find_token(sexpr, "uuid")
        uuid_obj = UUID.from_sexpr(uuid_token) if uuid_token else None

        return cls(
            text_type=text_type,
            text=text,
            position=position,
            unlocked=SExprParser.has_symbol(sexpr, "unlocked"),
            layer=SExprParser.get_optional_str(sexpr, "layer"),
            hide=SExprParser.has_symbol(sexpr, "hide"),
            effects=effects,
            uuid=uuid_obj,
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol(self.__token_name__), self.text_type.value, self.text]
        result.append(self.position.to_sexpr())

        if self.unlocked:
            result.append(Symbol("unlocked"))
        if self.layer:
            result.append([Symbol("layer"), self.layer])
        if self.hide:
            result.append(Symbol("hide"))
        if self.effects:
            result.append(self.effects.to_sexpr())
        if self.uuid:
            result.append(self.uuid.to_sexpr())

        return result


class FootprintTextBox(KiCadObject):
    """Footprint text box definition (from version 7).

    The 'fp_text_box' token defines a rectangle containing line-wrapped text in the format:
    (fp_text_box
        [locked]
        "TEXT"
        [(start X Y)]
        [(end X Y)]
        [(pts (xy X Y) (xy X Y) (xy X Y) (xy X Y))]
        [(angle ROTATION)]
        (layer LAYER_DEFINITION)
        (uuid UUID)
        TEXT_EFFECTS
        [STROKE_DEFINITION]
        [(render_cache RENDER_CACHE)]
    )

    Where:
        locked: Optional token specifying if text box can be moved
        TEXT: Content of the text box
        start: Top-left of cardinally oriented text box
        end: Bottom-right of cardinally oriented text box
        pts: Four corners of non-cardinally oriented text box
        angle: Optional rotation in degrees
        layer: Canonical layer the text box resides on
        uuid: Unique identifier of the text box
        TEXT_EFFECTS: Style of the text in the text box
        STROKE_DEFINITION: Style of optional border around text box
        render_cache: Cache for TrueType fonts

    Note: If angle is not given or is cardinal (0,90,180,270), must have start/end tokens.
    If angle is non-cardinal, must have pts token with 4 points.
    """

    __token_name__ = "fp_text_box"

    def __init__(
        self,
        text: str = "",
        locked: bool = False,
        start: Optional[Position] = None,
        end: Optional[Position] = None,
        points: Optional["CoordinatePointList"] = None,
        angle: Optional[float] = None,
        layer: Optional[str] = None,
        uuid: Optional[UUID] = None,
        effects: Optional["TextEffectsDefinition"] = None,
        stroke: Optional["StrokeDefinition"] = None,
        render_cache: Optional[str] = None,
    ) -> None:
        super().__init__()
        self.text = text
        self.locked = locked
        self.start = start
        self.end = end
        self.points = points
        self.angle = angle
        self.layer = layer
        self.uuid = uuid
        self.effects = effects
        self.stroke = stroke
        self.render_cache = render_cache

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "FootprintTextBox":
        if not sexpr:
            return cls()

        text = str(SExprParser.get_value(sexpr, 1, ""))

        start_token = SExprParser.find_token(sexpr, "start")
        start = (
            Position(
                SExprParser.safe_float(SExprParser.get_value(start_token, 1)),
                SExprParser.safe_float(SExprParser.get_value(start_token, 2)),
            )
            if start_token
            else None
        )

        end_token = SExprParser.find_token(sexpr, "end")
        end = (
            Position(
                SExprParser.safe_float(SExprParser.get_value(end_token, 1)),
                SExprParser.safe_float(SExprParser.get_value(end_token, 2)),
            )
            if end_token
            else None
        )

        pts_token = SExprParser.find_token(sexpr, "pts")
        points = CoordinatePointList.from_sexpr(pts_token) if pts_token else None

        effects_token = SExprParser.find_token(sexpr, "effects")
        effects = (
            TextEffectsDefinition.from_sexpr(effects_token) if effects_token else None
        )

        stroke_token = SExprParser.find_token(sexpr, "stroke")
        stroke = StrokeDefinition.from_sexpr(stroke_token) if stroke_token else None

        uuid_token = SExprParser.find_token(sexpr, "uuid")
        uuid_obj = UUID.from_sexpr(uuid_token) if uuid_token else None

        return cls(
            text=text,
            locked=SExprParser.has_symbol(sexpr, "locked"),
            start=start,
            end=end,
            points=points,
            angle=SExprParser.get_optional_float(sexpr, "angle"),
            layer=SExprParser.get_optional_str(sexpr, "layer"),
            uuid=uuid_obj,
            effects=effects,
            stroke=stroke,
            render_cache=SExprParser.get_optional_str(sexpr, "render_cache"),
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol(self.__token_name__)]

        if self.locked:
            result.append(Symbol("locked"))
        result.append(self.text)

        if self.start:
            result.append([Symbol("start"), self.start.x, self.start.y])
        if self.end:
            result.append([Symbol("end"), self.end.x, self.end.y])
        if self.points:
            result.append(self.points.to_sexpr())
        if self.angle is not None:
            result.append([Symbol("angle"), self.angle])
        if self.layer:
            result.append([Symbol("layer"), self.layer])
        if self.uuid:
            result.append(self.uuid.to_sexpr())
        if self.effects:
            result.append(self.effects.to_sexpr())
        if self.stroke:
            result.append(self.stroke.to_sexpr())
        if self.render_cache:
            result.append([Symbol("render_cache"), self.render_cache])

        return result


class FootprintLine(KiCadObject):
    """Footprint line definition.

    The 'fp_line' token defines a graphic line in a footprint definition in the format:
    (fp_line
        (start X Y)
        (end X Y)
        (layer LAYER_DEFINITION)
        (width WIDTH)
        STROKE_DEFINITION
        [(locked)]
        (uuid UUID)
    )

    Where:
        start: Coordinates of the beginning of the line
        end: Coordinates of the end of the line
        layer: Canonical layer the line resides on
        width: Line width (prior to version 7)
        STROKE_DEFINITION: Width and style of the line (from version 7)
        locked: Optional token defining if line cannot be edited
        uuid: Unique identifier of the line object
    """

    __token_name__ = "fp_line"

    def __init__(
        self,
        start: Optional[Position] = None,
        end: Optional[Position] = None,
        layer: Optional[str] = None,
        width: Optional[float] = None,
        stroke: Optional["StrokeDefinition"] = None,
        locked: bool = False,
        uuid: Optional[UUID] = None,
    ) -> None:
        super().__init__()
        self.start = start or Position()
        self.end = end or Position()
        self.layer = layer
        self.width = width
        self.stroke = stroke
        self.locked = locked
        self.uuid = uuid

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "FootprintLine":
        if not sexpr:
            return cls()

        start_token = SExprParser.find_token(sexpr, "start")
        start = (
            Position(
                SExprParser.safe_float(SExprParser.get_value(start_token, 1)),
                SExprParser.safe_float(SExprParser.get_value(start_token, 2)),
            )
            if start_token
            else Position()
        )

        end_token = SExprParser.find_token(sexpr, "end")
        end = (
            Position(
                SExprParser.safe_float(SExprParser.get_value(end_token, 1)),
                SExprParser.safe_float(SExprParser.get_value(end_token, 2)),
            )
            if end_token
            else Position()
        )

        stroke_token = SExprParser.find_token(sexpr, "stroke")
        stroke = StrokeDefinition.from_sexpr(stroke_token) if stroke_token else None

        uuid_token = SExprParser.find_token(sexpr, "uuid")
        uuid_obj = UUID.from_sexpr(uuid_token) if uuid_token else None

        return cls(
            start=start,
            end=end,
            layer=SExprParser.get_optional_str(sexpr, "layer"),
            width=SExprParser.get_optional_float(sexpr, "width"),
            stroke=stroke,
            locked=SExprParser.has_symbol(sexpr, "locked"),
            uuid=uuid_obj,
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol(self.__token_name__)]
        result.append([Symbol("start"), self.start.x, self.start.y])
        result.append([Symbol("end"), self.end.x, self.end.y])

        if self.layer:
            result.append([Symbol("layer"), self.layer])
        if self.width is not None:
            result.append([Symbol("width"), self.width])
        if self.stroke:
            result.append(self.stroke.to_sexpr())
        if self.locked:
            result.append(Symbol("locked"))
        if self.uuid:
            result.append(self.uuid.to_sexpr())

        return result


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


# Backward compatibility aliases for old class names
Stroke = StrokeDefinition
Font = FontDefinition
TextEffects = TextEffectsDefinition
