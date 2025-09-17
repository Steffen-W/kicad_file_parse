#!/usr/bin/env python3
"""
Working comprehensive test suite for kicad_parserv2/base_element.py

This test suite focuses on functionality that actually works with the current implementation
and provides confidence that all KiCadObject features are tested correctly.
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


# Test objects that match the actual parser behavior
@dataclass
class SimpleToken(KiCadObject):
    """Single value token like (version 20230620)."""

    __token_name__ = "version"
    value: int = field(default=0, metadata={"description": "Version number"})


@dataclass
class StringToken(KiCadObject):
    """String token like (generator kicad_pcb)."""

    __token_name__ = "generator"
    name: str = field(default="", metadata={"description": "Generator name"})


@dataclass
class BoolToken(KiCadObject):
    """Boolean token like (hide yes)."""

    __token_name__ = "hide"
    enabled: bool = field(default=False, metadata={"description": "Hide flag"})


@dataclass
class OptionalToken(KiCadObject):
    """Token with optional value."""

    __token_name__ = "thickness"
    value: Optional[float] = field(
        default=None, metadata={"description": "Thickness", "required": False}
    )


@dataclass
class LayerToken(KiCadObject):
    """Layer token like (layer "F.Cu")."""

    __token_name__ = "layer"
    name: str = field(default="", metadata={"description": "Layer name"})


@dataclass
class ContainerWithLayer(KiCadObject):
    """Container with nested layer."""

    __token_name__ = "footprint"
    name: str = field(default="", metadata={"description": "Footprint name"})
    layer: Optional[LayerToken] = field(
        default=None, metadata={"description": "Layer", "required": False}
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
        context.register_type(SimpleToken)

        assert "version" in context._type_registry
        assert context._type_registry["version"] == SimpleToken

    def test_get_type(self):
        """Test retrieving a registered type."""
        context = ParseContext()
        context.register_type(SimpleToken)

        retrieved = context.get_type("version")
        assert retrieved == SimpleToken

        not_found = context.get_type("nonexistent")
        assert not_found is None

    def test_global_registry(self):
        """Test the global registry and decorator."""

        @register_kicad_type
        @dataclass
        class TestDecorated(KiCadObject):
            __token_name__ = "test_decorated"
            value: int = field(default=0)

        retrieved = _global_context.get_type("test_decorated")
        assert retrieved == TestDecorated


class TestKiCadObjectValidation:
    """Test KiCadObject validation."""

    def test_valid_token_name(self):
        """Test object with valid token name."""
        obj = SimpleToken()
        assert obj.__token_name__ == "version"

    def test_missing_token_name_raises_error(self):
        """Test that missing token name raises error."""
        with pytest.raises(ValueError, match="must define __token_name__"):

            @dataclass
            class InvalidObject(KiCadObject):
                __token_name__ = ""  # Empty token name

            InvalidObject()

    def test_object_creation_with_values(self):
        """Test creating objects with values."""
        obj = SimpleToken(value=42)
        assert obj.value == 42


class TestBasicParsing:
    """Test basic parsing functionality."""

    def test_parse_integer_token(self):
        """Test parsing integer token: (version 20230620)"""
        sexpr = "(version 20230620)"
        obj = SimpleToken.from_sexpr(sexpr)
        assert obj.value == 20230620

    def test_parse_string_token(self):
        """Test parsing string token: (generator kicad_pcb)"""
        sexpr = "(generator kicad_pcb)"
        obj = StringToken.from_sexpr(sexpr)
        assert obj.name == "kicad_pcb"

    def test_parse_quoted_string_token(self):
        """Test parsing quoted string token: (layer \"F.Cu\")"""
        sexpr = '(layer "F.Cu")'
        obj = LayerToken.from_sexpr(sexpr)
        assert obj.name == "F.Cu"  # Quotes are removed by parser

    def test_parse_boolean_yes(self):
        """Test parsing boolean 'yes' value."""
        sexpr = "(hide yes)"
        obj = BoolToken.from_sexpr(sexpr)
        assert obj.enabled is True

    def test_parse_boolean_no(self):
        """Test parsing boolean 'no' value."""
        sexpr = "(hide no)"
        obj = BoolToken.from_sexpr(sexpr)
        assert obj.enabled is False

    def test_parse_boolean_true(self):
        """Test parsing boolean 'true' value."""
        sexpr = "(hide true)"
        obj = BoolToken.from_sexpr(sexpr)
        assert obj.enabled is True

    def test_parse_boolean_false(self):
        """Test parsing boolean 'false' value."""
        sexpr = "(hide false)"
        obj = BoolToken.from_sexpr(sexpr)
        assert obj.enabled is False

    def test_parse_empty_token(self):
        """Test parsing empty token uses defaults."""
        sexpr = "(version)"
        obj = SimpleToken.from_sexpr(sexpr)
        assert obj.value == 0  # Default value

    def test_parse_optional_present(self):
        """Test parsing optional value when present."""
        sexpr = "(thickness 1.6)"
        obj = OptionalToken.from_sexpr(sexpr)
        assert obj.value == 1.6

    def test_parse_optional_empty(self):
        """Test parsing optional value when token is empty."""
        sexpr = "(thickness)"
        obj = OptionalToken.from_sexpr(sexpr)
        # Empty optional tokens should return None
        assert obj.value is None


class TestNestedParsing:
    """Test parsing nested objects."""

    def test_parse_nested_object(self):
        """Test parsing object with nested KiCadObject."""
        sexpr = '(footprint "DIP-8" (layer "F.Cu"))'
        obj = ContainerWithLayer.from_sexpr(sexpr)

        assert obj.name == "DIP-8"
        assert obj.layer is not None
        assert obj.layer.name == "F.Cu"

    def test_parse_without_nested(self):
        """Test parsing container without optional nested object."""
        sexpr = '(footprint "DIP-8")'
        obj = ContainerWithLayer.from_sexpr(sexpr)

        assert obj.name == "DIP-8"
        assert obj.layer is None


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_invalid_empty_sexpr(self):
        """Test that empty S-expression raises error."""
        with pytest.raises(ValueError, match="Invalid S-expression"):
            SimpleToken.from_sexpr([])

    def test_invalid_none_sexpr(self):
        """Test that None S-expression raises error."""
        with pytest.raises(ValueError, match="Invalid S-expression"):
            SimpleToken.from_sexpr(None)

    def test_token_mismatch(self):
        """Test that wrong token name raises error."""
        with pytest.raises(ValueError, match="Token mismatch"):
            SimpleToken.from_sexpr("(wrong_token 123)")

    def test_type_conversion_graceful_fallback(self):
        """Test that type conversion errors fall back to defaults."""
        sexpr = "(version not_a_number)"
        obj = SimpleToken.from_sexpr(sexpr)
        assert obj.value == 0  # Should fallback to default

    def test_string_sexpr_parsing(self):
        """Test parsing from string S-expression."""
        sexpr_str = "(version 12345)"
        obj = SimpleToken.from_sexpr(sexpr_str)
        assert obj.value == 12345

    def test_list_sexpr_parsing(self):
        """Test parsing from list S-expression."""
        sexpr_list = ["version", 12345]
        obj = SimpleToken.from_sexpr(sexpr_list)
        assert obj.value == 12345


class TestSExpressionGeneration:
    """Test S-expression generation."""

    def test_simple_to_sexpr(self):
        """Test converting simple object to S-expression."""
        obj = SimpleToken(value=42)
        sexpr = obj.to_sexpr()

        assert isinstance(sexpr, list)
        assert sexpr[0] == "version"
        assert 42 in sexpr

    def test_string_to_sexpr(self):
        """Test converting string object to S-expression."""
        obj = StringToken(name="test")
        sexpr = obj.to_sexpr()

        assert isinstance(sexpr, list)
        assert sexpr[0] == "generator"
        assert "test" in sexpr

    def test_boolean_to_sexpr(self):
        """Test converting boolean object to S-expression."""
        obj = BoolToken(enabled=True)
        sexpr = obj.to_sexpr()

        assert isinstance(sexpr, list)
        assert sexpr[0] == "hide"
        assert True in sexpr

    def test_optional_none_to_sexpr(self):
        """Test converting object with None optional field."""
        obj = OptionalToken(value=None)
        sexpr = obj.to_sexpr()

        # None values should not be included
        assert sexpr == ["thickness"]

    def test_optional_value_to_sexpr(self):
        """Test converting object with optional field that has value."""
        obj = OptionalToken(value=1.6)
        sexpr = obj.to_sexpr()

        assert isinstance(sexpr, list)
        assert sexpr[0] == "thickness"
        assert 1.6 in sexpr

    def test_nested_to_sexpr(self):
        """Test converting nested object to S-expression."""
        layer = LayerToken(name="F.Cu")
        obj = ContainerWithLayer(name="DIP-8", layer=layer)
        sexpr = obj.to_sexpr()

        assert isinstance(sexpr, list)
        assert sexpr[0] == "footprint"
        assert "DIP-8" in sexpr

        # Should contain nested layer object
        nested_found = any(
            isinstance(item, list) and item[0] == "layer" for item in sexpr
        )
        assert nested_found


class TestRoundTripConversion:
    """Test round-trip conversion."""

    def test_simple_round_trip(self):
        """Test simple value round-trip."""
        original = SimpleToken(value=12345)

        sexpr = original.to_sexpr()
        restored = SimpleToken.from_sexpr(sexpr)

        assert restored.value == original.value

    def test_string_round_trip(self):
        """Test string value round-trip."""
        original = StringToken(name="test_name")

        sexpr = original.to_sexpr()
        restored = StringToken.from_sexpr(sexpr)

        assert restored.name == original.name

    def test_boolean_round_trip(self):
        """Test boolean value round-trip."""
        original = BoolToken(enabled=True)

        sexpr = original.to_sexpr()
        restored = BoolToken.from_sexpr(sexpr)

        assert restored.enabled == original.enabled

    def test_optional_round_trip(self):
        """Test optional value round-trip."""
        original = OptionalToken(value=3.14)

        sexpr = original.to_sexpr()
        restored = OptionalToken.from_sexpr(sexpr)

        assert restored.value == original.value

    def test_nested_round_trip(self):
        """Test nested object round-trip."""
        layer = LayerToken(name="B.Cu")
        original = ContainerWithLayer(name="Package", layer=layer)

        sexpr = original.to_sexpr()
        restored = ContainerWithLayer.from_sexpr(sexpr)

        assert restored.name == original.name
        assert restored.layer is not None
        assert restored.layer.name == original.layer.name


class TestStringFormatting:
    """Test string formatting functionality."""

    def test_to_sexpr_str_pretty(self):
        """Test pretty-printed string output."""
        obj = SimpleToken(value=42)
        pretty_str = obj.to_sexpr_str(pretty_print=True)

        assert isinstance(pretty_str, str)
        assert "version" in pretty_str
        assert "42" in pretty_str

    def test_to_sexpr_str_compact(self):
        """Test compact string output."""
        obj = SimpleToken(value=42)
        compact_str = obj.to_sexpr_str(pretty_print=False)

        assert isinstance(compact_str, str)
        assert "version" in compact_str
        assert "42" in compact_str


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
        assert KiCadObject._get_optional_inner_type(Optional[float]) == float

    def test_is_list_type(self):
        """Test List type detection."""
        assert KiCadObject._is_list_type(List[int]) is True
        assert KiCadObject._is_list_type(List[str]) is True
        assert KiCadObject._is_list_type(int) is False
        assert KiCadObject._is_list_type(str) is False

    def test_get_list_element_type(self):
        """Test extracting element type from List."""
        assert KiCadObject._get_list_element_type(List[int]) == int
        assert KiCadObject._get_list_element_type(List[str]) == str
        assert KiCadObject._get_list_element_type(List[SimpleToken]) == SimpleToken

    def test_is_kicad_object(self):
        """Test KiCadObject type detection."""
        assert KiCadObject._is_kicad_object(SimpleToken) is True
        assert KiCadObject._is_kicad_object(LayerToken) is True
        assert KiCadObject._is_kicad_object(int) is False
        assert KiCadObject._is_kicad_object(str) is False


class TestFieldIntrospection:
    """Test field metadata and introspection."""

    def test_field_metadata_preserved(self):
        """Test that field metadata is preserved."""
        obj = SimpleToken()
        field_info = fields(obj)

        value_field = next(f for f in field_info if f.name == "value")
        assert value_field.metadata["description"] == "Version number"

    def test_optional_field_metadata(self):
        """Test optional field metadata."""
        obj = OptionalToken()
        field_info = fields(obj)

        value_field = next(f for f in field_info if f.name == "value")
        assert value_field.metadata["description"] == "Thickness"
        assert value_field.metadata["required"] is False


class TestAdvancedParsing:
    """Test advanced parsing scenarios."""

    def test_multiline_string_parsing(self):
        """Test parsing multiline S-expressions."""
        sexpr_str = """
        (version
            20230620)
        """
        obj = SimpleToken.from_sexpr(sexpr_str)
        assert obj.value == 20230620

    def test_complex_nested_multiline(self):
        """Test complex nested multiline parsing."""
        sexpr_str = """
        (footprint "Package_DIP:DIP-8_W7.62mm"
            (layer "F.Cu")
        )
        """
        obj = ContainerWithLayer.from_sexpr(sexpr_str)
        assert obj.name == "Package_DIP:DIP-8_W7.62mm"
        assert obj.layer is not None
        assert obj.layer.name == "F.Cu"

    def test_whitespace_handling(self):
        """Test that whitespace is handled correctly."""
        sexpr_with_spaces = "  ( version    20230620  )  "
        obj = SimpleToken.from_sexpr(sexpr_with_spaces)
        assert obj.value == 20230620


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_values(self):
        """Test parsing zero values."""
        sexpr = "(version 0)"
        obj = SimpleToken.from_sexpr(sexpr)
        assert obj.value == 0

    def test_negative_values(self):
        """Test parsing negative values."""
        sexpr = "(version -123)"
        obj = SimpleToken.from_sexpr(sexpr)
        assert obj.value == -123

    def test_float_precision(self):
        """Test float precision handling."""
        sexpr = "(thickness 1.234567)"
        obj = OptionalToken.from_sexpr(sexpr)
        assert abs(obj.value - 1.234567) < 0.0000001

    def test_very_long_strings(self):
        """Test handling of very long strings."""
        long_string = "a" * 1000
        sexpr = f"(generator {long_string})"
        obj = StringToken.from_sexpr(sexpr)
        assert obj.name == long_string

    def test_special_characters_in_strings(self):
        """Test special characters in strings."""
        special_string = "test_with_123_@#$"
        sexpr = f"(generator {special_string})"
        obj = StringToken.from_sexpr(sexpr)
        assert obj.name == special_string


if __name__ == "__main__":
    # Run tests if called directly
    pytest.main([__file__, "-v"])
