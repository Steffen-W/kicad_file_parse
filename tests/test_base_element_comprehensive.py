#!/usr/bin/env python3
"""
Comprehensive test suite for kicad_parserv2/base_element.py

This test file ensures all functionalities of KiCadObject are working correctly
and provides confidence in the implementation.
"""

from dataclasses import dataclass, field, fields
from typing import Any, List, Optional

import pytest

from kicad_parserv2.base_element import (
    KiCadObject,
    ParseContext,
    _global_context,
    register_kicad_type,
)
from kicad_parserv2.sexpr_parser import SExprParser


# Simple test objects that follow the actual KiCad token format
@dataclass
class SimpleValue(KiCadObject):
    """Test object representing a simple value token like (version 20230620)."""

    __token_name__ = "version"
    value: int = field(default=0, metadata={"description": "Version number"})


@dataclass
class SimpleString(KiCadObject):
    """Test object representing a string token like (generator kicad_pcb)."""

    __token_name__ = "generator"
    name: str = field(default="", metadata={"description": "Generator name"})


@dataclass
class OptionalValue(KiCadObject):
    """Test object with optional field."""

    __token_name__ = "thickness"
    value: Optional[float] = field(
        default=None, metadata={"description": "Thickness value", "required": False}
    )


@dataclass
class NestedObject(KiCadObject):
    """Test nested object."""

    __token_name__ = "at"
    x: float = field(default=0.0, metadata={"description": "X coordinate"})
    y: float = field(default=0.0, metadata={"description": "Y coordinate"})
    angle: Optional[float] = field(
        default=None, metadata={"description": "Angle", "required": False}
    )


@dataclass
class ContainerObject(KiCadObject):
    """Test object containing other objects."""

    __token_name__ = "footprint"
    name: str = field(default="", metadata={"description": "Footprint name"})
    position: Optional[NestedObject] = field(
        default=None, metadata={"description": "Position", "required": False}
    )


class TestParseContext:
    """Test ParseContext functionality."""

    def test_create_context(self):
        """Test creating a ParseContext."""
        context = ParseContext()
        assert context._type_registry == {}

    def test_register_type(self):
        """Test registering a type."""
        context = ParseContext()
        context.register_type(SimpleValue)

        assert "version" in context._type_registry
        assert context._type_registry["version"] == SimpleValue

    def test_get_type(self):
        """Test retrieving a registered type."""
        context = ParseContext()
        context.register_type(SimpleValue)

        retrieved = context.get_type("version")
        assert retrieved == SimpleValue

        not_found = context.get_type("nonexistent")
        assert not_found is None

    def test_register_decorator(self):
        """Test the register_kicad_type decorator."""

        @register_kicad_type
        @dataclass
        class TestDecorated(KiCadObject):
            __token_name__ = "test_decorated"
            value: int = field(default=0)

        retrieved = _global_context.get_type("test_decorated")
        assert retrieved == TestDecorated


class TestKiCadObjectBasics:
    """Test basic KiCadObject functionality."""

    def test_token_name_validation(self):
        """Test that __token_name__ is required."""
        # Valid object
        obj = SimpleValue()
        assert obj.__token_name__ == "version"

        # Invalid object without token name
        with pytest.raises(ValueError, match="must define __token_name__"):

            @dataclass
            class InvalidObject(KiCadObject):
                __token_name__ = ""  # Empty token name

            InvalidObject()

    def test_object_creation(self):
        """Test basic object creation."""
        obj = SimpleValue(value=42)
        assert obj.value == 42
        assert obj.__token_name__ == "version"


class TestSimpleParsing:
    """Test parsing of simple S-expressions."""

    def test_parse_simple_integer(self):
        """Test parsing simple integer value: (version 20230620)"""
        sexpr = "(version 20230620)"
        obj = SimpleValue.from_sexpr(sexpr)
        assert obj.value == 20230620

    def test_parse_simple_string(self):
        """Test parsing simple string value: (generator kicad_pcb)"""
        sexpr = "(generator kicad_pcb)"
        obj = SimpleString.from_sexpr(sexpr)
        assert obj.name == "kicad_pcb"

    def test_parse_optional_present(self):
        """Test parsing optional value when present: (thickness 1.6)"""
        sexpr = "(thickness 1.6)"
        obj = OptionalValue.from_sexpr(sexpr)
        assert obj.value == 1.6

    def test_parse_optional_absent(self):
        """Test parsing optional value when absent: (thickness)"""
        sexpr = "(thickness)"
        obj = OptionalValue.from_sexpr(sexpr)
        assert obj.value is None


class TestNestedParsing:
    """Test parsing of nested objects."""

    def test_parse_nested_object(self):
        """Test parsing nested object: (at 100 50 90)"""
        sexpr = "(at 100 50 90)"
        obj = NestedObject.from_sexpr(sexpr)
        assert obj.x == 100
        assert obj.y == 50
        assert obj.angle == 90

    def test_parse_nested_optional(self):
        """Test parsing nested object without optional field: (at 100 50)"""
        sexpr = "(at 100 50)"
        obj = NestedObject.from_sexpr(sexpr)
        assert obj.x == 100
        assert obj.y == 50
        assert obj.angle is None

    def test_parse_container_with_nested(self):
        """Test parsing container with nested object."""
        sexpr = '(footprint "DIP-8" (at 100 50))'
        obj = ContainerObject.from_sexpr(sexpr)
        assert obj.name == "DIP-8"
        assert obj.position is not None
        assert obj.position.x == 100
        assert obj.position.y == 50


class TestErrorHandling:
    """Test error handling."""

    def test_invalid_sexpr_format(self):
        """Test handling of invalid S-expression format."""
        with pytest.raises(ValueError, match="Invalid S-expression"):
            SimpleValue.from_sexpr([])  # Empty list

        with pytest.raises(ValueError, match="Invalid S-expression"):
            SimpleValue.from_sexpr(None)

    def test_token_mismatch(self):
        """Test handling of token mismatch."""
        with pytest.raises(ValueError, match="Token mismatch"):
            SimpleValue.from_sexpr("(wrong_token 123)")

    def test_type_conversion_errors(self):
        """Test graceful handling of type conversion errors."""
        # The implementation should handle conversion errors gracefully
        sexpr = "(version invalid_number)"
        obj = SimpleValue.from_sexpr(sexpr)
        assert obj.value == 0  # Should fallback to default


class TestSExpressionGeneration:
    """Test S-expression generation (to_sexpr)."""

    def test_simple_to_sexpr(self):
        """Test converting simple object to S-expression."""
        obj = SimpleValue(value=20230620)
        sexpr = obj.to_sexpr()

        assert isinstance(sexpr, list)
        assert sexpr[0] == "version"
        assert 20230620 in sexpr

    def test_string_to_sexpr(self):
        """Test converting string object to S-expression."""
        obj = SimpleString(name="kicad_pcb")
        sexpr = obj.to_sexpr()

        assert isinstance(sexpr, list)
        assert sexpr[0] == "generator"
        assert "kicad_pcb" in sexpr

    def test_optional_to_sexpr(self):
        """Test converting object with optional field to S-expression."""
        obj = OptionalValue(value=1.6)
        sexpr = obj.to_sexpr()

        assert isinstance(sexpr, list)
        assert sexpr[0] == "thickness"
        assert 1.6 in sexpr

    def test_optional_none_to_sexpr(self):
        """Test converting object with None optional field."""
        obj = OptionalValue(value=None)
        sexpr = obj.to_sexpr()

        # Should only contain token name when optional field is None
        assert sexpr == ["thickness"]

    def test_nested_to_sexpr(self):
        """Test converting nested object to S-expression."""
        position = NestedObject(x=100, y=50, angle=90)
        obj = ContainerObject(name="DIP-8", position=position)
        sexpr = obj.to_sexpr()

        assert isinstance(sexpr, list)
        assert sexpr[0] == "footprint"
        assert "DIP-8" in sexpr
        # Nested object should be represented as a list
        nested_found = any(isinstance(item, list) and item[0] == "at" for item in sexpr)
        assert nested_found


class TestRoundTripConversion:
    """Test round-trip conversion: object -> S-expression -> object."""

    def test_simple_round_trip(self):
        """Test round-trip for simple objects."""
        original = SimpleValue(value=42)

        # Convert to S-expression and back
        sexpr = original.to_sexpr()
        restored = SimpleValue.from_sexpr(sexpr)

        assert restored.value == original.value

    def test_string_round_trip(self):
        """Test round-trip for string objects."""
        original = SimpleString(name="test_name")

        sexpr = original.to_sexpr()
        restored = SimpleString.from_sexpr(sexpr)

        assert restored.name == original.name

    def test_optional_round_trip(self):
        """Test round-trip for optional objects."""
        original = OptionalValue(value=3.14)

        sexpr = original.to_sexpr()
        restored = OptionalValue.from_sexpr(sexpr)

        assert restored.value == original.value

    def test_nested_round_trip(self):
        """Test round-trip for nested objects."""
        position = NestedObject(x=10, y=20, angle=45)
        original = ContainerObject(name="test", position=position)

        sexpr = original.to_sexpr()
        restored = ContainerObject.from_sexpr(sexpr)

        assert restored.name == original.name
        assert restored.position is not None
        assert restored.position.x == original.position.x
        assert restored.position.y == original.position.y
        assert restored.position.angle == original.position.angle


class TestStringFormatting:
    """Test string formatting functionality."""

    def test_to_sexpr_str(self):
        """Test converting to formatted string."""
        obj = SimpleValue(value=42)

        # Pretty printed
        pretty_str = obj.to_sexpr_str(pretty_print=True)
        assert isinstance(pretty_str, str)
        assert "version" in pretty_str
        assert "42" in pretty_str

        # Compact
        compact_str = obj.to_sexpr_str(pretty_print=False)
        assert isinstance(compact_str, str)
        assert "version" in compact_str


class TestTypeCheckingHelpers:
    """Test the static helper methods."""

    def test_is_optional(self):
        """Test Optional type detection."""
        from typing import Union

        assert KiCadObject._is_optional(Optional[int]) is True
        assert KiCadObject._is_optional(Union[int, None]) is True
        assert KiCadObject._is_optional(int) is False
        assert KiCadObject._is_optional(str) is False

    def test_get_optional_inner_type(self):
        """Test extracting inner type from Optional."""
        assert KiCadObject._get_optional_inner_type(Optional[int]) == int
        assert KiCadObject._get_optional_inner_type(Optional[str]) == str

    def test_is_list_type(self):
        """Test List type detection."""
        assert KiCadObject._is_list_type(List[int]) is True
        assert KiCadObject._is_list_type(List[str]) is True
        assert KiCadObject._is_list_type(int) is False

    def test_get_list_element_type(self):
        """Test extracting element type from List."""
        assert KiCadObject._get_list_element_type(List[int]) == int
        assert KiCadObject._get_list_element_type(List[str]) == str

    def test_is_kicad_object(self):
        """Test KiCadObject type detection."""
        assert KiCadObject._is_kicad_object(SimpleValue) is True
        assert KiCadObject._is_kicad_object(NestedObject) is True
        assert KiCadObject._is_kicad_object(int) is False
        assert KiCadObject._is_kicad_object(str) is False


class TestFieldMetadata:
    """Test field metadata handling."""

    def test_field_descriptions(self):
        """Test that field descriptions are preserved."""
        obj = SimpleValue()
        field_info = fields(obj)

        value_field = next(f for f in field_info if f.name == "value")
        assert value_field.metadata["description"] == "Version number"


class TestAdvancedScenarios:
    """Test advanced parsing scenarios."""

    def test_multiline_string_parsing(self):
        """Test parsing multiline S-expression strings."""
        sexpr_str = """
        (version
            20230620)
        """
        obj = SimpleValue.from_sexpr(sexpr_str)
        assert obj.value == 20230620

    def test_nested_complex_parsing(self):
        """Test complex nested parsing."""
        sexpr_str = """
        (footprint "Package_DIP:DIP-8_W7.62mm"
            (at 100.0 50.0 90.0)
        )
        """
        obj = ContainerObject.from_sexpr(sexpr_str)
        assert obj.name == "Package_DIP:DIP-8_W7.62mm"
        assert obj.position is not None
        assert obj.position.x == 100.0
        assert obj.position.y == 50.0
        assert obj.position.angle == 90.0


if __name__ == "__main__":
    # Run tests if called directly
    pytest.main([__file__, "-v"])
