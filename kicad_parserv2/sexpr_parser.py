"""S-Expression Parser for KiCad files

This module provides a comfortable and simplified approach to parsing
S-expressions compared to the original kicad_parser implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional, Tuple, Type, TypeVar, cast, overload

from .sexpdata import Symbol, dumps, loads

# Type definitions
SExprValue = Any  # Can be Symbol, str, int, float, or nested list
SExpr = List[SExprValue]
T = TypeVar("T")


def str_to_sexpr(content: str) -> SExpr:
    """Convert string content to S-expression.

    Args:
        content: String content containing S-expression data

    Returns:
        Parsed S-expression as nested lists/atoms

    Raises:
        ValueError: If content cannot be parsed as valid S-expression
    """
    try:
        return cast(SExpr, loads(content))
    except Exception as e:
        raise ValueError(f"Failed to parse S-expression: {e}") from e


def sexpr_to_str(sexpr: SExpr, pretty_print: bool = True) -> str:
    """Convert S-expression to string representation.

    Args:
        sexpr: S-expression to serialize
        pretty_print: Whether to format output for readability

    Returns:
        String representation of the S-expression

    Raises:
        ValueError: If sexpr cannot be serialized
    """
    try:
        return dumps(sexpr, pretty_print=pretty_print)
    except Exception as e:
        raise ValueError(f"Failed to serialize S-expression: {e}") from e


@dataclass
class ParseResult:
    """Result of a parsing operation."""

    value: Any
    found: bool
    token: Optional[SExpr] = None


class SExprParser:
    """S-Expression parser with type-safe methods and convenient API."""

    def __init__(self, sexpr: SExpr) -> None:
        """Initialize parser with an S-expression.

        Args:
            sexpr: Parsed S-expression as nested lists/atoms
        """
        self.sexpr = sexpr

    @classmethod
    def from_string(cls, sexpr_string: str) -> "SExprParser":
        """Create parser from S-expression string.

        Args:
            sexpr_string: String containing S-expression data

        Returns:
            New parser instance
        """
        return cls(str_to_sexpr(sexpr_string))

    @classmethod
    def from_file(cls, filepath: str) -> "SExprParser":
        """Create parser from S-expression file.

        Args:
            filepath: Path to file containing S-expression data

        Returns:
            New parser instance
        """
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return cls.from_string(content)

    def find_token(self, token_name: str) -> Optional["SExprParser"]:
        """Find a token and return a new parser for it.

        Args:
            token_name: Name of the token to find

        Returns:
            New parser instance for the found token, or None if not found
        """
        for item in self.sexpr:
            if (
                isinstance(item, list)
                and len(item) > 0
                and (item[0] == Symbol(token_name) or str(item[0]) == token_name)
            ):
                return SExprParser(item)
        return None

    def find_all_tokens(self, token_name: str) -> List["SExprParser"]:
        """Find all tokens with the given name.

        Args:
            token_name: Name of the tokens to find

        Returns:
            List of parser instances for found tokens
        """
        results = []
        for item in self.sexpr:
            if (
                isinstance(item, list)
                and len(item) > 0
                and (item[0] == Symbol(token_name) or str(item[0]) == token_name)
            ):
                results.append(SExprParser(item))
        return results

    def has_token(self, token_name: str) -> bool:
        """Check if a token exists."""
        return self.find_token(token_name) is not None

    def get_value(self, index: int) -> ParseResult:
        """Get value at specific index.

        Args:
            index: Index to retrieve

        Returns:
            ParseResult with the value and whether it was found
        """
        if len(self.sexpr) > index:
            return ParseResult(value=self.sexpr[index], found=True)
        return ParseResult(value=None, found=False)

    @overload
    def parse_token(
        self, token_name: str, types: None = None, required: bool = False
    ) -> Tuple[Optional[str], ...]:
        """Parse token returning tuple of string values."""
        ...

    @overload
    def parse_token(
        self, token_name: str, types: Tuple[Type[T], ...], required: bool = False
    ) -> Tuple[Optional[T], ...]:
        """Parse token returning tuple of typed values."""
        ...

    def parse_token(
        self,
        token_name: str,
        types: Optional[Tuple[Type[Any], ...]] = None,
        required: bool = False,
    ) -> Tuple[Any, ...]:
        """Parse a token with automatic type conversion.

        Args:
            token_name: Name of the token to parse
            types: Tuple of types to convert values to (e.g., (str, float, bool))
            required: Whether the token is required (raises if missing)

        Returns:
            Tuple of converted values, with None for missing optional values
        """
        token_parser = self.find_token(token_name)

        if token_parser is None:
            if required:
                raise ValueError(f"Required token '{token_name}' not found")
            return tuple(None for _ in types) if types else (None,)

        if types is None:
            return tuple(
                str(token_parser.sexpr[i]) if i < len(token_parser.sexpr) else None
                for i in range(1, len(token_parser.sexpr))
            )

        results = []
        for i, target_type in enumerate(types, start=1):
            if i < len(token_parser.sexpr):
                value = token_parser.sexpr[i]
                converted = self._convert_value(value, target_type)
                results.append(converted)
            else:
                results.append(None)

        return tuple(results)

    def _convert_value(self, value: Any, target_type: Type[T]) -> Optional[T]:
        """Convert a value to the target type safely."""
        if value is None:
            return None

        try:
            if target_type == str:
                return cast(T, str(value))
            elif target_type == float:
                return cast(T, float(value))
            elif target_type == int:
                return cast(T, int(value))
            elif target_type == bool:
                if isinstance(value, str):
                    return cast(T, value.lower() in ("true", "yes", "1"))
                return cast(T, bool(value))
            else:
                if target_type is object or not callable(target_type):
                    return cast(T, value)
                try:
                    return target_type(value)  # type: ignore[call-arg]
                except (TypeError, ValueError):
                    return cast(T, value)
        except (ValueError, TypeError):
            return None

    def parse_optional(
        self, token_name: str, target_type: Type[T], default: Optional[T] = None
    ) -> Optional[T]:
        """Parse an optional single-value token.

        Args:
            token_name: Name of the token
            target_type: Type to convert to
            default: Default value if token not found

        Returns:
            Converted value, default, or None
        """
        token_parser = self.find_token(token_name)
        if token_parser is None:
            return default

        if len(token_parser.sexpr) > 1:
            return self._convert_value(token_parser.sexpr[1], target_type)
        return default

    def parse_required(self, token_name: str, target_type: Type[T]) -> T:
        """Parse a required single-value token.

        Args:
            token_name: Name of the token
            target_type: Type to convert to

        Returns:
            Converted value

        Raises:
            ValueError: If token not found or conversion fails
        """
        token_parser = self.find_token(token_name)
        if token_parser is None:
            raise ValueError(f"Required token '{token_name}' not found")

        if len(token_parser.sexpr) <= 1:
            raise ValueError(f"Token '{token_name}' has no value")

        result = self._convert_value(token_parser.sexpr[1], target_type)
        if result is None:
            raise ValueError(
                f"Failed to convert value in token '{token_name}' to {target_type.__name__}"
            )

        return result

    def parse_list(self, token_name: str, target_type: Type[T]) -> List[T]:
        """Parse a token that contains a list of values.

        Args:
            token_name: Name of the token
            target_type: Type to convert each value to

        Returns:
            List of converted values
        """
        token_parser = self.find_token(token_name)
        if token_parser is None:
            return []

        results = []
        for i in range(1, len(token_parser.sexpr)):
            converted = self._convert_value(token_parser.sexpr[i], target_type)
            if converted is not None:
                results.append(converted)

        return results

    def get_main_token(self) -> Optional[str]:
        """Get the main token name (first element) of this S-expression."""
        if len(self.sexpr) > 0:
            return str(self.sexpr[0])
        return None

    def is_token_type(self, token_name: str) -> bool:
        """Check if this S-expression represents a specific token type."""
        main_token = self.get_main_token()
        return main_token == token_name if main_token else False

    def to_string(self, pretty_print: bool = True) -> str:
        """Convert the S-expression to string representation.

        Args:
            pretty_print: Whether to format output for readability

        Returns:
            String representation of the S-expression
        """
        return sexpr_to_str(self.sexpr, pretty_print=pretty_print)

    def to_file(self, filepath: str, pretty_print: bool = True) -> None:
        """Save the S-expression to a file.

        Args:
            filepath: Path where to save the file
            pretty_print: Whether to format output for readability
        """
        content = self.to_string(pretty_print=pretty_print)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

    @property
    def raw_data(self) -> SExpr:
        """Get the raw S-expression data."""
        return self.sexpr

    def __repr__(self) -> str:
        return f"SExprParser({self.sexpr})"

    def __str__(self) -> str:
        """String representation of the parser (pretty-printed S-expression)."""
        return self.to_string(pretty_print=True)


def parse_sexpr(sexpr: SExpr) -> SExprParser:
    """Create a SExprParser from an S-expression.

    Args:
        sexpr: Parsed S-expression as nested lists/atoms

    Returns:
        New parser instance
    """
    return SExprParser(sexpr)


if __name__ == "__main__":
    # Example: Parse a nested KiCad footprint S-expression
    content = """(footprint "R_0805"
        (at 10.0 20.0 90)
        (layer "F.Cu")
        (properties
            (name "R1")
            (value "1k")
            (footprint "R_0805"))
        (pad "1" smd rect (at -0.9 0) (size 0.8 1.0))
        (pad "2" smd rect (at 0.9 0) (size 0.8 1.0)))"""

    # Create parser from string
    parser = SExprParser.from_string(content)

    # Basic token operations
    print(f"Main token: {parser.get_main_token()}")
    print(f"Has layer token: {parser.has_token('layer')}")
    print(f"Is footprint type: {parser.is_token_type('footprint')}")

    # Parse position values
    x, y, angle = parser.parse_token("at", (float, float, float))
    print(f"Position: x={x}, y={y}, angle={angle}")

    # Parse single values
    layer = parser.parse_optional("layer", str)
    print(f"Layer: {layer}")

    # Navigate nested structures
    props = parser.find_token("properties")
    if props:
        name = props.parse_optional("name", str)
        value = props.parse_optional("value", str)
        print(f"Properties: name={name}, value={value}")
    else:
        print("No properties found")

    # Parse multiple tokens
    pads = parser.find_all_tokens("pad")
    print(f"Found {len(pads)} pads:")
    for pad in pads:
        pad_num = pad.get_value(1).value
        pad_type = pad.get_value(2).value
        print(f"  Pad {pad_num}: {pad_type}")

    # Export back to string
    print(f"\nRound-trip test:\n{parser.to_string()}")
