"""Recursive S-expression parser for KiCad objects."""

from __future__ import annotations

from abc import ABC
from dataclasses import MISSING, dataclass, fields
from typing import (
    Any,
    ClassVar,
    Dict,
    List,
    Optional,
    Type,
    TypeVar,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

from .sexpr_parser import SExpr, SExprParser, SExprValue, sexpr_to_str

T = TypeVar("T", bound="KiCadObject")


class ParseContext:
    """Context for parsing operations with type registry."""

    def __init__(self) -> None:
        self._type_registry: Dict[str, Type[KiCadObject]] = {}

    def register_type(self, cls: Type[KiCadObject]) -> None:
        """Register a KiCadObject type by its token name."""
        if hasattr(cls, "__token_name__") and cls.__token_name__:
            self._type_registry[cls.__token_name__] = cls

    def get_type(self, token_name: str) -> Optional[Type[KiCadObject]]:
        """Get registered type by token name."""
        return self._type_registry.get(token_name)


# Global type registry
_global_context = ParseContext()


def register_kicad_type(cls: Type[KiCadObject]) -> Type[KiCadObject]:
    """Decorator to register KiCadObject types."""
    _global_context.register_type(cls)
    return cls


@dataclass
class KiCadObject(ABC):
    """Base class for KiCad S-expression objects with recursive parsing."""

    __token_name__: ClassVar[str] = ""

    def __post_init__(self) -> None:
        """Validate token name is defined."""
        if not self.__token_name__:
            raise ValueError(
                f"Class {self.__class__.__name__} must define __token_name__"
            )

    @classmethod
    def from_sexpr(cls: Type[T], sexpr: Union[str, SExpr]) -> T:
        """Parse from string or S-expression.

        Provides bidirectional symmetry with to_sexpr().
        """
        if isinstance(sexpr, str):
            parser = SExprParser.from_string(sexpr)
            sexpr = parser.sexpr

        return cls._parse_sexpr(sexpr)

    @classmethod
    def _parse_sexpr(cls: Type[T], sexpr: SExpr) -> T:
        """Core recursive parser."""
        if not isinstance(sexpr, list) or not sexpr:
            raise ValueError(f"Invalid S-expression for {cls.__name__}: {sexpr}")

        # Validate token name
        token_name = str(sexpr[0])
        if token_name != cls.__token_name__:
            raise ValueError(
                f"Token mismatch: expected '{cls.__token_name__}', got '{token_name}'"
            )

        # Get field types and defaults
        field_types = get_type_hints(cls)
        field_defaults = {
            f.name: f.default for f in fields(cls) if f.default != MISSING
        }

        # Parse fields recursively
        parsed_values = {}
        sexpr_data = sexpr[1:]  # Skip token name

        for field in fields(cls):
            if field.name.startswith("_"):  # Skip private fields
                continue

            field_type = field_types[field.name]
            value = cls._parse_field_value(field.name, field_type, sexpr_data)

            if value is not None:
                parsed_values[field.name] = value
            elif field.name in field_defaults:
                parsed_values[field.name] = field_defaults[field.name]

        return cls(**parsed_values)

    @classmethod
    def _parse_field_value(
        cls, field_name: str, field_type: Type[Any], sexpr_data: List[SExprValue]
    ) -> Any:
        """Recursively parse a single field value."""
        # Handle Optional[T] -> Union[T, None]
        if cls._is_optional(field_type):
            inner_type = cls._get_optional_inner_type(field_type)
            result = cls._parse_field_value(field_name, inner_type, sexpr_data)
            # For optional fields, if we get default values and no matching field was found, return None
            if result == cls._get_default_value(
                inner_type
            ) and not cls._field_exists_in_sexpr(field_name, sexpr_data):
                return None
            return result

        # Handle List[T]
        if cls._is_list_type(field_type):
            element_type = cls._get_list_element_type(field_type)
            return cls._parse_list_values(field_name, element_type, sexpr_data)

        # Handle KiCadObject subtypes (including all token types)
        if cls._is_kicad_object(field_type):
            return cls._parse_kicad_object(field_type, sexpr_data)

        # Handle primitive types (int, str, float, bool)
        if field_type in (int, str, float, bool):
            return cls._parse_primitive_value(field_name, field_type, sexpr_data)

        # If we reach here, the field type is not supported
        return None

    @classmethod
    def _parse_list_values(
        cls, field_name: str, element_type: Type[Any], sexpr_data: List[SExprValue]
    ) -> List[Any]:
        """Parse list of values recursively."""
        result = []

        if cls._is_kicad_object(element_type):
            token_name = getattr(element_type, "__token_name__", None)
            if token_name:
                # First check if there's a named list containing the objects
                for item in sexpr_data:
                    if (
                        isinstance(item, list)
                        and len(item) > 1
                        and str(item[0]) == field_name
                    ):
                        # Found named list like (nested_list (simple_nested ...) (simple_nested ...))
                        for nested_item in item[1:]:
                            if (
                                isinstance(nested_item, list)
                                and nested_item
                                and str(nested_item[0]) == token_name
                            ):
                                result.append(element_type._parse_sexpr(nested_item))
                        break

                # If no named list found, search directly in sexpr_data (backward compatibility)
                if not result:
                    for item in sexpr_data:
                        if (
                            isinstance(item, list)
                            and item
                            and str(item[0]) == token_name
                        ):
                            result.append(element_type._parse_sexpr(item))
        else:
            # Handle list of primitives - look for named list tokens matching field_name
            for item in sexpr_data:
                if (
                    isinstance(item, list)
                    and len(item) > 1
                    and str(item[0]) == field_name
                ):
                    # Found named list like (int_list 1 2 3)
                    # Convert values to the appropriate type
                    for value in item[1:]:
                        converted_value = cls._convert_to_type(value, element_type)
                        result.append(converted_value)
                    break  # Only process the first matching list

        return result

    @classmethod
    def _parse_kicad_object(
        cls, object_type: Type[KiCadObject], sexpr_data: List[SExprValue]
    ) -> Optional[KiCadObject]:
        """Parse nested KiCadObject recursively."""
        token_name = getattr(object_type, "__token_name__", None)
        if not token_name:
            return None

        # Find matching token in sexpr_data
        for item in sexpr_data:
            if isinstance(item, list) and item and str(item[0]) == token_name:
                return object_type._parse_sexpr(item)

        return None

    @classmethod
    def _parse_primitive_value(
        cls, field_name: str, primitive_type: Type[Any], sexpr_data: List[SExprValue]
    ) -> Any:
        """Parse primitive value (int, str, float, bool) from S-expression data."""
        # First, try to find a named field like (field_name value)
        for item in sexpr_data:
            if isinstance(item, list) and len(item) >= 2 and str(item[0]) == field_name:
                value = item[1]  # Take the first value after field name
                return cls._convert_to_type(value, primitive_type)

        # For simple single-field objects, use the first non-list value
        if len(sexpr_data) == 1 and not isinstance(sexpr_data[0], list):
            return cls._convert_to_type(sexpr_data[0], primitive_type)

        # If it's a multi-value token like (at 100 50 90), handle positional parsing
        # Map field names to positions for common patterns
        position_map = cls._get_field_position_map()
        if field_name in position_map:
            position = position_map[field_name]
            if position < len(sexpr_data) and not isinstance(
                sexpr_data[position], list
            ):
                return cls._convert_to_type(sexpr_data[position], primitive_type)
            # If position is out of bounds, signal that field was not found
            elif position >= len(sexpr_data):
                return None  # Will be handled by _parse_field_value for optional fields

        # Fallback: use the old behavior for backward compatibility
        if sexpr_data and len(sexpr_data) > 0:
            value = sexpr_data[0]
            if not isinstance(value, list):
                return cls._convert_to_type(value, primitive_type)

        # Return default value if no suitable data found
        return cls._get_default_value(primitive_type)

    @classmethod
    def _convert_to_type(cls, value: Any, target_type: Type[Any]) -> Any:
        """Convert a value to the target type with proper error handling."""
        if value is None:
            return cls._get_default_value(target_type)

        try:
            if target_type == int:
                return int(value)
            elif target_type == str:
                return str(value)
            elif target_type == float:
                return float(value)
            elif target_type == bool:
                # Convert to string first to handle Symbol objects
                str_value = str(value).lower()
                return str_value in ("yes", "true", "1")
        except (ValueError, TypeError):
            # If conversion fails, return default
            pass

        return cls._get_default_value(target_type)

    @classmethod
    def _get_default_value(cls, primitive_type: Type[Any]) -> Any:
        """Get the default value for a primitive type."""
        if primitive_type == int:
            return 0
        elif primitive_type == str:
            return ""
        elif primitive_type == float:
            return 0.0
        elif primitive_type == bool:
            return False
        return None

    @classmethod
    def _field_exists_in_sexpr(
        cls, field_name: str, sexpr_data: List[SExprValue]
    ) -> bool:
        """Check if a field exists in the S-expression data."""
        for item in sexpr_data:
            if isinstance(item, list) and len(item) >= 1 and str(item[0]) == field_name:
                return True
        return False

    @classmethod
    def _get_field_position_map(cls) -> Dict[str, int]:
        """Get field name to position mapping for multi-value tokens.

        This enables proper parsing of tokens like (at x y angle) where:
        - x is at position 0
        - y is at position 1
        - angle is at position 2

        Subclasses can override this to define custom field mappings.
        """
        # Get all field names from the dataclass
        field_names = [f.name for f in fields(cls)]

        # Create default positional mapping
        position_map = {}
        for i, field_name in enumerate(field_names):
            position_map[field_name] = i

        return position_map

    def to_sexpr(self) -> SExpr:
        """Convert to S-expression."""
        result: SExpr = [self.__token_name__]

        # Check if this is a multi-value token (all primitive fields)
        all_fields = fields(self)
        if self._is_multi_value_token():
            # For multi-value tokens like (at x y angle), output values positionally
            for field in all_fields:
                value = getattr(self, field.name)
                if value is not None:
                    result.append(value)
        else:
            # For complex tokens, use named fields
            for field in all_fields:
                value = getattr(self, field.name)
                if value is None:
                    continue

                sexpr_value = self._value_to_sexpr(field.name, value)
                if sexpr_value is not None:
                    # Always append as single item - don't flatten KiCadObject lists
                    result.append(sexpr_value)

        return result

    def _is_multi_value_token(self) -> bool:
        """Check if this is a multi-value token with only primitive fields."""
        all_fields = fields(self)

        # Must have at least 2 fields
        if len(all_fields) < 2:
            return False

        # All fields must be primitive types (not Optional, List, or KiCadObject)
        for field in all_fields:
            field_type = field.type
            # Cast to Type[Any] to satisfy mypy
            if isinstance(field_type, type):
                if (
                    self._is_optional(field_type)
                    or self._is_list_type(field_type)
                    or self._is_kicad_object(field_type)
                ):
                    return False
                if field_type not in (int, str, float, bool):
                    return False
            else:
                # If field_type is not a type, it's not a primitive type
                return False

        return True

    def _value_to_sexpr(self, field_name: str, value: Any) -> Optional[SExprValue]:
        """Convert field value to S-expression recursively."""
        if value is None:
            return None

        # KiCadObject
        if isinstance(value, KiCadObject):
            return value.to_sexpr()

        # List
        if isinstance(value, list):
            if value and isinstance(value[0], KiCadObject):
                # List of KiCadObjects - wrap in named token
                return [field_name] + [item.to_sexpr() for item in value]
            else:
                # List of primitives - wrap in named token
                return [field_name] + list(value)

        # Primitive - return value directly for simple single-field tokens
        return value

    def to_sexpr_str(self, pretty_print: bool = True) -> str:
        """Convert to formatted S-expression string."""
        return sexpr_to_str(self.to_sexpr(), pretty_print=pretty_print)

    # Simplified type checking helpers
    @staticmethod
    def _is_optional(field_type: Type[Any]) -> bool:
        """Check if type is Optional[T]."""
        return get_origin(field_type) is Union and type(None) in get_args(field_type)

    @staticmethod
    def _get_optional_inner_type(field_type: Type[Any]) -> Type[Any]:
        """Extract T from Optional[T]."""
        for arg in get_args(field_type):
            if arg is not type(None):
                return arg  # type: ignore[no-any-return]
        return str  # Fallback to str type

    @staticmethod
    def _is_list_type(field_type: Type[Any]) -> bool:
        """Check if type is List[T]."""
        return get_origin(field_type) in (list, List)

    @staticmethod
    def _get_list_element_type(field_type: Type[Any]) -> Type[Any]:
        """Extract T from List[T]."""
        args = get_args(field_type)
        return args[0] if args else str

    @staticmethod
    def _is_kicad_object(field_type: Type[Any]) -> bool:
        """Check if type is a KiCadObject subclass."""
        try:
            return isinstance(field_type, type) and issubclass(field_type, KiCadObject)
        except TypeError:
            return False
