"""Optimized S-expression parser for KiCad objects with field classification."""

from __future__ import annotations

import logging
from abc import ABC
from dataclasses import MISSING, dataclass, fields
from enum import Enum
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


@dataclass
class ParseContext:
    """Context for tracking hierarchical parsing path."""

    path: List[str]

    def __init__(self, initial_path: Optional[List[str]] = None):
        """Initialize parsing context with optional initial path."""
        self.path = initial_path or []

    def enter(self, name: str) -> "ParseContext":
        """Create new context for entering a nested level."""
        return ParseContext(self.path + [name])

    def get_path_string(self) -> str:
        """Get the current path as a formatted string."""
        return " > ".join(self.path) if self.path else ""

    def format_message(self, message: str) -> str:
        """Format a message with the current path context."""
        path_str = self.get_path_string()
        if path_str:
            return f"{path_str}: {message}"
        return message


class ParseStrictness(Enum):
    """Parser strictness levels for error handling."""

    STRICT = "strict"  # Raise exceptions for all parsing errors
    LENIENT = "lenient"  # Log warnings and use defaults for missing fields
    PERMISSIVE = "permissive"  # Silently use defaults for missing fields
    COMPLETE = "complete"  # Track all parameters and raise error if any are unused


class FieldType(Enum):
    """Classification of field types for optimized parsing."""

    PRIMITIVE = "primitive"
    OPTIONAL_PRIMITIVE = "optional_primitive"
    LIST_PRIMITIVE = "list_primitive"
    KICAD_OBJECT = "kicad_object"
    OPTIONAL_KICAD_OBJECT = "optional_kicad_object"
    LIST_KICAD_OBJECT = "list_kicad_object"
    OPTIONAL_FLAG = "optional_flag"


@dataclass
class FieldInfo:
    """Complete field information for optimized parsing."""

    name: str
    field_type: FieldType
    inner_type: Type[Any]
    position_index: int
    token_name: Optional[str] = None


@dataclass
class KiCadObject(ABC):
    """Base class for KiCad S-expression objects with optimized parsing."""

    __token_name__: ClassVar[str] = ""

    def __post_init__(self) -> None:
        """Validate token name is defined."""
        if not self.__token_name__:
            raise ValueError(
                f"Class {self.__class__.__name__} must define __token_name__"
            )

    @classmethod
    def from_sexpr(
        cls: Type[T],
        sexpr: Union[str, SExpr],
        strictness: ParseStrictness = ParseStrictness.STRICT,
        context: Optional[ParseContext] = None,
    ) -> T:
        """Parse from string or S-expression with configurable strictness and path tracking."""
        if isinstance(sexpr, str):
            parser = SExprParser.from_string(sexpr)
            sexpr = parser.sexpr

        # Create context if not provided
        if context is None:
            context = ParseContext([cls.__name__])

        return cls._parse_sexpr(sexpr, strictness, context)

    @classmethod
    def _parse_sexpr(
        cls: Type[T],
        sexpr: SExpr,
        strictness: ParseStrictness = ParseStrictness.STRICT,
        context: Optional[ParseContext] = None,
    ) -> T:
        """Core optimized parser using field classification."""
        if not isinstance(sexpr, list) or not sexpr:
            raise ValueError(f"Invalid S-expression for {cls.__name__}: {sexpr}")

        if str(sexpr[0]) != cls.__token_name__:
            raise ValueError(
                f"Token mismatch: expected '{cls.__token_name__}', got '{sexpr[0]}'"
            )

        # Create context if not provided
        if context is None:
            context = ParseContext([cls.__name__])

        field_infos = cls._classify_fields()
        field_defaults = {
            f.name: f.default for f in fields(cls) if f.default != MISSING
        }
        parsed_values = {}
        sexpr_data = sexpr[1:]

        # Create parser with tracking for COMPLETE mode
        track_usage = strictness == ParseStrictness.COMPLETE
        parser = SExprParser(sexpr, track_usage=track_usage)

        for field_info in field_infos:
            # Create field-specific context
            field_context = context.enter(field_info.name)
            value = cls._parse_field(
                field_info, sexpr_data, strictness, field_defaults, parser, field_context
            )
            if value is not None:
                parsed_values[field_info.name] = value
            elif field_info.name in field_defaults:
                parsed_values[field_info.name] = field_defaults[field_info.name]

        # Check for unused parameters in COMPLETE mode
        if strictness == ParseStrictness.COMPLETE:
            parser.check_complete_usage(cls.__name__)

        return cls(**parsed_values)

    @classmethod
    def _classify_fields(cls) -> List[FieldInfo]:
        """Pre-classify all fields for optimized parsing."""
        field_types = get_type_hints(cls)
        field_infos = []
        position_index = 0

        for field in fields(cls):
            if field.name.startswith("_"):
                continue

            field_type = field_types[field.name]
            field_info = cls._classify_field(field.name, field_type, position_index)
            field_infos.append(field_info)
            position_index += 1

        return field_infos

    @classmethod
    def _classify_field(
        cls, name: str, field_type: Type[Any], position: int
    ) -> FieldInfo:
        """Classify a single field and extract all parsing information."""
        is_optional = get_origin(field_type) is Union and type(None) in get_args(
            field_type
        )
        is_list = get_origin(field_type) in (list, List)

        # Unwrap Optional[...] and List[...] to get inner type
        inner_type = field_type
        if is_optional:
            inner_type = next(
                arg for arg in get_args(field_type) if arg is not type(None)
            )

        # Re-check if we have a list after unwrapping Optional
        is_list = get_origin(inner_type) in (list, List)
        if is_list:
            inner_type = get_args(inner_type)[0] if get_args(inner_type) else str
        is_kicad_object = False
        is_optional_flag = False
        try:
            is_kicad_object = isinstance(inner_type, type) and issubclass(
                inner_type, KiCadObject
            )
        except TypeError as e:
            logging.warning(
                f"Type checking failed for field '{name}' with type {inner_type}: {e}"
            )
            is_kicad_object = False

        # Check if it's an OptionalFlag type
        try:
            is_optional_flag = isinstance(inner_type, type) and issubclass(
                inner_type, OptionalFlag
            )
        except TypeError:
            is_optional_flag = False

        token_name = (
            getattr(inner_type, "__token_name__", None) if is_kicad_object else None
        )
        if is_list and is_kicad_object:
            field_type_enum = FieldType.LIST_KICAD_OBJECT
        elif is_list:
            field_type_enum = FieldType.LIST_PRIMITIVE
        elif is_optional and is_optional_flag:
            field_type_enum = FieldType.OPTIONAL_FLAG
        elif is_optional and is_kicad_object:
            field_type_enum = FieldType.OPTIONAL_KICAD_OBJECT
        elif is_optional:
            field_type_enum = FieldType.OPTIONAL_PRIMITIVE
        elif is_kicad_object:
            field_type_enum = FieldType.KICAD_OBJECT
        else:
            field_type_enum = FieldType.PRIMITIVE

        return FieldInfo(
            name=name,
            field_type=field_type_enum,
            inner_type=inner_type,
            position_index=position,
            token_name=token_name,
        )

    @classmethod
    def _parse_field(
        cls,
        field_info: FieldInfo,
        sexpr_data: List[SExprValue],
        strictness: ParseStrictness,
        field_defaults: Dict[str, Any],
        parser: Optional[SExprParser] = None,
        context: Optional[ParseContext] = None,
    ) -> Any:
        """Parse field using optimized classification with strictness handling."""
        if field_info.field_type == FieldType.PRIMITIVE:
            return cls._parse_primitive(
                field_info, sexpr_data, strictness, field_defaults, parser, context
            )

        elif field_info.field_type == FieldType.OPTIONAL_PRIMITIVE:
            try:
                return cls._parse_primitive(
                    field_info, sexpr_data, strictness, field_defaults, parser, context
                )
            except ValueError as e:
                # Only re-raise conversion errors in STRICT mode, not missing value errors
                if (
                    strictness == ParseStrictness.STRICT
                    and "No value found" not in str(e)
                ):
                    raise
                elif strictness == ParseStrictness.LENIENT:
                    message = f"Optional field '{field_info.name}' in {cls.__name__} failed to parse: {e}"
                    if context:
                        message = context.format_message(message)
                    logging.warning(message)
                return None

        elif field_info.field_type == FieldType.KICAD_OBJECT:
            return cls._parse_object(field_info, sexpr_data, strictness, parser, context)

        elif field_info.field_type == FieldType.OPTIONAL_KICAD_OBJECT:
            return cls._parse_object(field_info, sexpr_data, strictness, parser, context)

        elif field_info.field_type in (
            FieldType.LIST_PRIMITIVE,
            FieldType.LIST_KICAD_OBJECT,
        ):
            return cls._parse_list(field_info, sexpr_data, strictness, parser, context)

        elif field_info.field_type == FieldType.OPTIONAL_FLAG:
            return cls._parse_optional_flag(field_info, sexpr_data, strictness, parser)

        return None

    @classmethod
    def _parse_primitive(
        cls,
        field_info: FieldInfo,
        sexpr_data: List[SExprValue],
        strictness: ParseStrictness,
        field_defaults: Dict[str, Any],
        parser: Optional[SExprParser] = None,
        context: Optional[ParseContext] = None,
    ) -> Any:
        """Parse primitive value using field name or position with strictness handling."""
        # Try named field first: (field_name value)
        for i, item in enumerate(sexpr_data):
            if (
                isinstance(item, list)
                and len(item) >= 2
                and str(item[0]) == field_info.name
            ):
                # Mark as used for tracking (i+1 because index 0 is token name)
                if parser:
                    parser.mark_used(i + 1)
                try:
                    return cls._convert_value(item[1], field_info.inner_type)
                except ValueError as e:
                    if strictness == ParseStrictness.STRICT:
                        raise
                    elif strictness == ParseStrictness.LENIENT:
                        message = f"Conversion failed for field '{field_info.name}' in {cls.__name__}: {e}"
                        if context:
                            message = context.format_message(message)
                        logging.warning(message)

        # Try positional access for multi-value tokens
        if field_info.position_index < len(sexpr_data):
            value = sexpr_data[field_info.position_index]
            if not isinstance(value, list):
                # Mark as used for tracking (position_index+1 because index 0 is token name)
                if parser:
                    parser.mark_used(field_info.position_index + 1)
                try:
                    return cls._convert_value(value, field_info.inner_type)
                except ValueError as e:
                    if strictness == ParseStrictness.STRICT:
                        raise
                    elif strictness == ParseStrictness.LENIENT:
                        message = f"Positional conversion failed for field '{field_info.name}' in {cls.__name__}: {e}"
                        if context:
                            message = context.format_message(message)
                        logging.warning(message)

        if strictness == ParseStrictness.STRICT:
            raise ValueError(f"No value found for field '{field_info.name}'")

        # Check if field is optional (should not generate warnings when missing)
        is_optional_field = field_info.field_type in (
            FieldType.OPTIONAL_PRIMITIVE,
            FieldType.OPTIONAL_KICAD_OBJECT,
            FieldType.OPTIONAL_FLAG,
        )

        default_value = field_defaults.get(field_info.name)
        if default_value is not None:
            # Only log warnings for non-optional fields
            if strictness == ParseStrictness.LENIENT and not is_optional_field:
                message = f"Missing field '{field_info.name}' (default: {default_value})"
                if context:
                    message = context.format_message(message)
                logging.warning(message)
            return default_value

        # Only warn for required fields
        if strictness == ParseStrictness.LENIENT and not is_optional_field:
            message = f"Missing field '{field_info.name}' in {cls.__name__} with no default, returning None"
            if context:
                message = context.format_message(message)
            logging.warning(message)

        return None

    @classmethod
    def _parse_object(
        cls,
        field_info: FieldInfo,
        sexpr_data: List[SExprValue],
        strictness: ParseStrictness,
        parser: Optional[SExprParser] = None,
        context: Optional[ParseContext] = None,
    ) -> Optional[KiCadObject]:
        """Parse KiCadObject using token name."""
        if not field_info.token_name:
            return None

        for i, item in enumerate(sexpr_data):
            if (
                isinstance(item, list)
                and item
                and str(item[0]) == field_info.token_name
            ):
                # Mark as used for tracking (i+1 because index 0 is token name)
                if parser:
                    parser.mark_used(i + 1)
                return field_info.inner_type._parse_sexpr(item, strictness, context)  # type: ignore[no-any-return]

        return None

    @classmethod
    def _parse_list(
        cls,
        field_info: FieldInfo,
        sexpr_data: List[SExprValue],
        strictness: ParseStrictness,
        parser: Optional[SExprParser] = None,
        context: Optional[ParseContext] = None,
    ) -> List[Any]:
        """Parse list of values by collecting individual objects using SExprParser."""
        result = []

        if field_info.token_name:  # List of KiCadObjects
            local_parser = SExprParser(sexpr_data)
            matching_tokens = local_parser.get_list_of_tokens(field_info.token_name)

            # Track each matching token in the original parser
            if parser:
                for i, item in enumerate(sexpr_data):
                    if (
                        isinstance(item, list)
                        and item
                        and str(item[0]) == field_info.token_name
                    ):
                        parser.mark_used(i + 1)

            for i, token_sexpr in enumerate(matching_tokens):
                # Create index-specific context for list items
                item_context = context.enter(f"[{i}]") if context else None
                result.append(
                    field_info.inner_type._parse_sexpr(token_sexpr, strictness, item_context)
                )
        else:  # List of primitives
            for i, item in enumerate(sexpr_data):
                if (
                    isinstance(item, list)
                    and len(item) > 1
                    and str(item[0]) == field_info.name
                ):
                    # Mark as used for tracking (i+1 because index 0 is token name)
                    if parser:
                        parser.mark_used(i + 1)
                    for value in item[1:]:
                        result.append(cls._convert_value(value, field_info.inner_type))
                    break

        return result

    @classmethod
    def _parse_optional_flag(
        cls,
        field_info: FieldInfo,
        sexpr_data: List[SExprValue],
        strictness: ParseStrictness,
        parser: Optional[SExprParser] = None,
    ) -> Optional[OptionalFlag]:
        """Parse OptionalFlag by directly searching sexpr_data."""
        flag_found = False
        for i, item in enumerate(sexpr_data):
            if str(item) == field_info.name:
                flag_found = True
                # Mark as used for tracking (i+1 because index 0 is token name)
                if parser:
                    parser.mark_used(i + 1)
                break

        result = OptionalFlag(field_info.name)
        result.found = flag_found
        return result

    @classmethod
    def _convert_value(cls, value: Any, target_type: Type[Any]) -> Any:
        """Convert value to target type with error handling."""
        if value is None:
            raise ValueError(f"Cannot convert None to {target_type.__name__}")

        try:
            if target_type == int:
                return int(value)
            elif target_type == str:
                return str(value)
            elif target_type == float:
                return float(value)
            elif target_type == bool:
                return str(value).lower() in ("yes", "true", "1")
            elif isinstance(target_type, type) and issubclass(target_type, Enum):
                # Handle enum conversion - try by value first, then by name
                if isinstance(value, target_type):
                    return value
                try:
                    return target_type(value)
                except ValueError:
                    # Try by name if value lookup failed
                    return target_type[str(value).upper()]
            else:
                raise ValueError(f"Unsupported type: {target_type}")
        except (ValueError, TypeError) as e:
            raise ValueError(f"Cannot convert '{value}' to {target_type.__name__}: {e}")

    def to_sexpr(self) -> SExpr:
        """Convert to S-expression using simple field iteration with named fields."""
        result: SExpr = [self.__token_name__]
        field_infos = self._classify_fields()
        field_defaults = {
            f.name: f.default for f in fields(self) if f.default != MISSING
        }

        for field_info in field_infos:
            value = getattr(self, field_info.name)

            if value is None:
                is_optional_field = field_info.field_type in (
                    FieldType.OPTIONAL_PRIMITIVE,
                    FieldType.OPTIONAL_KICAD_OBJECT,
                    FieldType.OPTIONAL_FLAG,
                )
                has_default = field_info.name in field_defaults

                if is_optional_field or has_default:
                    continue
                else:
                    raise ValueError(
                        f"Required field '{field_info.name}' is None in {self.__class__.__name__}. "
                        f"Field type: {field_info.field_type}"
                    )
            if isinstance(value, list):
                # Unroll list items as individual S-expressions
                for item in value:
                    if isinstance(item, KiCadObject):
                        result.append(item.to_sexpr())
                    elif isinstance(item, Enum):
                        result.append(item.value)
                    else:
                        result.append(item)
            elif isinstance(value, KiCadObject):
                result.append(value.to_sexpr())
            elif isinstance(value, OptionalFlag):
                # Only add the flag to the result if it was found
                if value.found:
                    result.append(value.expected_value)
            else:
                # Primitives as named fields: (field_name value)
                # Convert enum to its value for serialization
                if isinstance(value, Enum):
                    result.append([field_info.name, value.value])
                else:
                    result.append([field_info.name, value])

        return result

    def __eq__(self, other: object) -> bool:
        """Fast and robust equality comparison for KiCadObjects."""
        if not isinstance(other, KiCadObject):
            return False

        if self.__class__ != other.__class__:
            return False
        field_infos = self._classify_fields()

        for field_info in field_infos:
            self_value = getattr(self, field_info.name)
            other_value = getattr(other, field_info.name)

            if (self_value is None) != (other_value is None):
                return False

            if self_value is None and other_value is None:
                continue
            if not isinstance(other_value, type(self_value)):
                return False

            if isinstance(self_value, list):
                if len(self_value) != len(other_value):
                    return False

                for self_item, other_item in zip(self_value, other_value):
                    if isinstance(self_item, KiCadObject):
                        if not self_item.__eq__(other_item):  # Recursive comparison
                            return False
                    else:
                        if self_item != other_item:
                            return False

            elif isinstance(self_value, KiCadObject):
                if not self_value.__eq__(other_value):  # Recursive comparison
                    return False

            else:
                if self_value != other_value:
                    return False

        return True

    def __hash__(self) -> int:
        """Hash implementation - required when implementing __eq__."""
        return hash((self.__class__.__name__, self.__token_name__))

    def to_sexpr_str(self, pretty_print: bool = True) -> str:
        """Convert to formatted S-expression string."""
        return sexpr_to_str(self.to_sexpr(), pretty_print=pretty_print)

    def __str__(self) -> str:
        """String representation showing only non-None values (except for required fields)."""
        field_infos = self._classify_fields()
        field_defaults = {
            f.name: f.default for f in fields(self) if f.default != MISSING
        }

        non_none_fields = []

        for field_info in field_infos:
            value = getattr(self, field_info.name)

            # Check if field is optional
            is_optional_field = field_info.field_type in (
                FieldType.OPTIONAL_PRIMITIVE,
                FieldType.OPTIONAL_KICAD_OBJECT,
                FieldType.OPTIONAL_FLAG,
            )
            has_default = field_info.name in field_defaults

            # Show field if:
            # 1. Value is not None (for any field), OR
            # 2. Field is required (not optional and no default) even if None
            # Skip optional fields that are None
            if is_optional_field and value is None:
                continue
            elif value is not None or (not is_optional_field and not has_default):
                # Format value for display
                if isinstance(value, list) and len(value) == 0:
                    # Skip empty lists for optional fields
                    if is_optional_field or has_default:
                        continue
                    display_value = "[]"
                elif isinstance(value, OptionalFlag):
                    # Only show OptionalFlag if it was found
                    if value.found:
                        display_value = f"OptionalFlag({value.expected_value}=True)"
                    else:
                        continue
                elif isinstance(value, KiCadObject):
                    # Use the custom __str__ for nested KiCadObjects
                    display_value = str(value)
                elif isinstance(value, list):
                    # Handle lists of KiCadObjects recursively
                    if value and isinstance(value[0], KiCadObject):
                        formatted_items = [str(item) for item in value]
                        display_value = f"[{', '.join(formatted_items)}]"
                    else:
                        display_value = repr(value)
                else:
                    display_value = repr(value)

                non_none_fields.append(f"{field_info.name}={display_value}")

        return f"{self.__class__.__name__}({', '.join(non_none_fields)})"


@dataclass
class OptionalFlag:
    """Simple flag container for optional string tokens in S-expressions.

    This is not a KiCadObject but a helper class that tells the parser
    to look for a specific string token in the S-expression data.

    Examples:
    - OptionalFlag("italic") looks for "italic" in (font (size 1.27 1.27) italic)
    - OptionalFlag("unlocked") looks for "unlocked" in (fp_text reference "U1" (at 0 0) unlocked)
    - OptionalFlag("mirror") looks for "mirror" in (justify left top mirror)

    Args:
        expected_value: The string token to search for
        found: Whether the token was found during parsing
    """

    expected_value: str
    found: bool = False

    def __init__(self, expected_value: str):
        self.expected_value = expected_value
        self.found = False
