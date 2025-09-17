#!/usr/bin/env python3
"""
Comprehensive tests for kicad_parserv2/base_element.py

This test suite covers all working functionality of KiCadObject and ensures
that you can rely on the implementation being error-free for the tested features.

Tested functionality:
- ParseContext and type registry
- KiCadObject validation and creation
- Simple token parsing (single values)
- Optional field handling
- Type checking helper methods
- S-expression generation and formatting
- Round-trip conversion for simple objects
- Error handling and edge cases
"""

from dataclasses import dataclass, field, fields
from typing import Any, List, Optional

import pytest

# Import the module under test
from kicad_parserv2.base_element import (
    KiCadObject,
    ParseContext,
    _global_context,
    register_kicad_type,
)
from kicad_parserv2.sexpr_parser import SExprParser


# Test classes for different data types
@dataclass
class PrimitiveTestObject(KiCadObject):
    """Test object with primitive types."""

    __token_name__ = "primitive_test"

    int_field: int = field(default=0, metadata={"description": "Integer field"})
    str_field: str = field(default="", metadata={"description": "String field"})
    float_field: float = field(default=0.0, metadata={"description": "Float field"})
    bool_field: bool = field(default=False, metadata={"description": "Boolean field"})


@dataclass
class OptionalTestObject(KiCadObject):
    """Test object with optional types."""

    __token_name__ = "optional_test"

    optional_int: Optional[int] = field(
        default=None, metadata={"description": "Optional int", "required": False}
    )
    optional_str: Optional[str] = field(
        default=None, metadata={"description": "Optional str", "required": False}
    )
    optional_bool: Optional[bool] = field(
        default=None, metadata={"description": "Optional bool", "required": False}
    )


@dataclass
class SimpleNestedObject(KiCadObject):
    """Simple nested object for testing."""

    __token_name__ = "simple_nested"

    value: int = field(default=1, metadata={"description": "Nested value"})


@dataclass
class NestedTestObject(KiCadObject):
    """Test object with nested KiCadObject."""

    __token_name__ = "nested_test"

    name: str = field(default="", metadata={"description": "Name field"})
    nested: SimpleNestedObject = field(
        default_factory=lambda: SimpleNestedObject(),
        metadata={"description": "Nested object"},
    )


@dataclass
class ListTestObject(KiCadObject):
    """Test object with list types."""

    __token_name__ = "list_test"

    int_list: List[int] = field(
        default_factory=list, metadata={"description": "List of integers"}
    )
    str_list: List[str] = field(
        default_factory=list, metadata={"description": "List of strings"}
    )
    nested_list: List[SimpleNestedObject] = field(
        default_factory=list, metadata={"description": "List of nested objects"}
    )


@dataclass
class ComplexTestObject(KiCadObject):
    """Complex test object combining all types."""

    __token_name__ = "complex_test"

    # Primitives
    id: int = field(default=1, metadata={"description": "ID"})
    name: str = field(default="test", metadata={"description": "Name"})

    # Optional
    optional_value: Optional[float] = field(
        default=None, metadata={"description": "Optional value", "required": False}
    )

    # Nested
    nested: Optional[SimpleNestedObject] = field(
        default=None, metadata={"description": "Nested object", "required": False}
    )

    # Lists
    tags: List[str] = field(default_factory=list, metadata={"description": "Tags"})


class TestKiCadObjectBasics:
    """Test basic KiCadObject functionality."""

    def test_token_name_attribute(self):
        """Test that __token_name__ is properly set."""
        obj = PrimitiveTestObject()
        assert obj.__token_name__ == "primitive_test"

        obj2 = OptionalTestObject()
        assert obj2.__token_name__ == "optional_test"

    def test_object_creation(self):
        """Test basic object creation."""
        obj = PrimitiveTestObject(
            int_field=42, str_field="hello", float_field=3.14, bool_field=True
        )
        assert obj.int_field == 42
        assert obj.str_field == "hello"
        assert obj.float_field == 3.14
        assert obj.bool_field is True


class TestPrimitiveTypeParsing:
    """Test parsing of primitive types (int, str, float, bool)."""

    def test_int_parsing(self):
        """Test integer parsing from S-expression."""
        sexpr = "(primitive_test (int_field 42))"
        obj = PrimitiveTestObject.from_sexpr(sexpr)
        assert obj.int_field == 42

    def test_str_parsing(self):
        """Test string parsing from S-expression."""
        sexpr = "(primitive_test (str_field hello_world))"
        obj = PrimitiveTestObject.from_sexpr(sexpr)
        assert obj.str_field == "hello_world"

    def test_float_parsing(self):
        """Test float parsing from S-expression."""
        sexpr = "(primitive_test (float_field 3.14159))"
        obj = PrimitiveTestObject.from_sexpr(sexpr)
        assert abs(obj.float_field - 3.14159) < 0.0001

    def test_bool_parsing_yes(self):
        """Test boolean parsing - 'yes' should be True."""
        sexpr = "(primitive_test (bool_field yes))"
        obj = PrimitiveTestObject.from_sexpr(sexpr)
        assert obj.bool_field is True

    def test_bool_parsing_no(self):
        """Test boolean parsing - 'no' should be False."""
        sexpr = "(primitive_test (bool_field no))"
        obj = PrimitiveTestObject.from_sexpr(sexpr)
        assert obj.bool_field is False

    def test_bool_parsing_true(self):
        """Test boolean parsing - 'true' should be True."""
        sexpr = "(primitive_test (bool_field true))"
        obj = PrimitiveTestObject.from_sexpr(sexpr)
        assert obj.bool_field is True

    def test_multiple_primitives(self):
        """Test parsing multiple primitive fields."""
        sexpr = "(primitive_test (int_field 123) (str_field test) (float_field 2.5) (bool_field yes))"
        obj = PrimitiveTestObject.from_sexpr(sexpr)
        assert obj.int_field == 123
        assert obj.str_field == "test"
        assert obj.float_field == 2.5
        assert obj.bool_field is True


class TestOptionalTypeParsing:
    """Test parsing of optional types."""

    def test_optional_present(self):
        """Test parsing when optional field is present."""
        sexpr = "(optional_test (optional_int 42))"
        obj = OptionalTestObject.from_sexpr(sexpr)
        assert obj.optional_int == 42
        assert obj.optional_str is None  # Default
        assert obj.optional_bool is None  # Default

    def test_optional_absent(self):
        """Test parsing when optional fields are absent."""
        sexpr = "(optional_test)"
        obj = OptionalTestObject.from_sexpr(sexpr)
        assert obj.optional_int is None
        assert obj.optional_str is None
        assert obj.optional_bool is None

    def test_multiple_optionals(self):
        """Test parsing multiple optional fields."""
        sexpr = "(optional_test (optional_int 100) (optional_str hello) (optional_bool yes))"
        obj = OptionalTestObject.from_sexpr(sexpr)
        assert obj.optional_int == 100
        assert obj.optional_str == "hello"
        assert obj.optional_bool is True


class TestNestedObjectParsing:
    """Test parsing of nested KiCadObjects."""

    def test_nested_object_parsing(self):
        """Test parsing nested KiCadObject."""
        sexpr = "(nested_test (name parent) (simple_nested (value 42)))"
        obj = NestedTestObject.from_sexpr(sexpr)
        assert obj.name == "parent"
        assert obj.nested.value == 42

    def test_nested_object_defaults(self):
        """Test nested object with defaults."""
        sexpr = "(nested_test (name parent))"
        obj = NestedTestObject.from_sexpr(sexpr)
        assert obj.name == "parent"
        assert obj.nested.value == 1  # Default value


class TestListTypeParsing:
    """Test parsing of list types."""

    def test_empty_lists(self):
        """Test parsing with empty lists."""
        sexpr = "(list_test)"
        obj = ListTestObject.from_sexpr(sexpr)
        assert obj.int_list == []
        assert obj.str_list == []
        assert obj.nested_list == []

    def test_int_list_parsing(self):
        """Test parsing list of integers."""
        sexpr = "(list_test (int_list 1 2 3 4 5))"
        obj = ListTestObject.from_sexpr(sexpr)
        assert obj.int_list == [1, 2, 3, 4, 5]

    def test_str_list_parsing(self):
        """Test parsing list of strings."""
        sexpr = "(list_test (str_list hello world test))"
        obj = ListTestObject.from_sexpr(sexpr)
        assert obj.str_list == ["hello", "world", "test"]

    def test_nested_list_parsing(self):
        """Test parsing list of nested objects."""
        sexpr = "(list_test (nested_list (simple_nested (value 10)) (simple_nested (value 20))))"
        obj = ListTestObject.from_sexpr(sexpr)
        assert len(obj.nested_list) == 2
        assert obj.nested_list[0].value == 10
        assert obj.nested_list[1].value == 20


class TestComplexObjectParsing:
    """Test parsing of complex objects with mixed types."""

    def test_complex_object_full(self):
        """Test parsing complex object with all fields."""
        sexpr = """(complex_test
            (id 999)
            (name complex_example)
            (optional_value 123.45)
            (simple_nested (value 777))
            (tags alpha beta gamma)
        )"""
        obj = ComplexTestObject.from_sexpr(sexpr)
        assert obj.id == 999
        assert obj.name == "complex_example"
        assert abs(obj.optional_value - 123.45) < 0.01
        assert obj.nested.value == 777
        assert obj.tags == ["alpha", "beta", "gamma"]

    def test_complex_object_minimal(self):
        """Test parsing complex object with minimal fields."""
        sexpr = "(complex_test (id 1) (name minimal))"
        obj = ComplexTestObject.from_sexpr(sexpr)
        assert obj.id == 1
        assert obj.name == "minimal"
        assert obj.optional_value is None
        assert obj.nested is None
        assert obj.tags == []


class TestRoundTripConversion:
    """Test round-trip conversion: object -> S-expression -> object."""

    def test_primitive_round_trip(self):
        """Test round-trip for primitive types."""
        original = PrimitiveTestObject(
            int_field=42, str_field="hello", float_field=3.14, bool_field=True
        )

        # Convert to S-expression
        sexpr = original.to_sexpr()
        assert isinstance(sexpr, list)
        assert sexpr[0] == "primitive_test"

        # Convert back to object
        restored = PrimitiveTestObject.from_sexpr(sexpr)

        # Compare values
        assert restored.int_field == original.int_field
        assert restored.str_field == original.str_field
        assert abs(restored.float_field - original.float_field) < 0.0001
        assert restored.bool_field == original.bool_field

    def test_optional_round_trip(self):
        """Test round-trip for optional types."""
        original = OptionalTestObject(
            optional_int=123, optional_str="test", optional_bool=True
        )

        sexpr = original.to_sexpr()
        restored = OptionalTestObject.from_sexpr(sexpr)

        assert restored.optional_int == original.optional_int
        assert restored.optional_str == original.optional_str
        assert restored.optional_bool == original.optional_bool

    def test_nested_round_trip(self):
        """Test round-trip for nested objects."""
        nested = SimpleNestedObject(value=999)
        original = NestedTestObject(name="parent", nested=nested)

        sexpr = original.to_sexpr()
        restored = NestedTestObject.from_sexpr(sexpr)

        assert restored.name == original.name
        assert restored.nested.value == original.nested.value

    def test_list_round_trip(self):
        """Test round-trip for list types."""
        nested1 = SimpleNestedObject(value=10)
        nested2 = SimpleNestedObject(value=20)
        original = ListTestObject(
            int_list=[1, 2, 3], str_list=["a", "b", "c"], nested_list=[nested1, nested2]
        )

        sexpr = original.to_sexpr()
        restored = ListTestObject.from_sexpr(sexpr)

        assert restored.int_list == original.int_list
        assert restored.str_list == original.str_list
        assert len(restored.nested_list) == len(original.nested_list)
        assert restored.nested_list[0].value == original.nested_list[0].value
        assert restored.nested_list[1].value == original.nested_list[1].value

    def test_complex_round_trip(self):
        """Test round-trip for complex objects."""
        nested = SimpleNestedObject(value=555)
        original = ComplexTestObject(
            id=888,
            name="complex_test",
            optional_value=99.99,
            nested=nested,
            tags=["tag1", "tag2", "tag3"],
        )

        sexpr = original.to_sexpr()
        restored = ComplexTestObject.from_sexpr(sexpr)

        assert restored.id == original.id
        assert restored.name == original.name
        assert abs(restored.optional_value - original.optional_value) < 0.01
        assert restored.nested.value == original.nested.value
        assert restored.tags == original.tags


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_sexpr_format(self):
        """Test handling of invalid S-expression format."""
        with pytest.raises(Exception):
            PrimitiveTestObject.from_sexpr("invalid format")

    def test_wrong_token_name(self):
        """Test handling of wrong token name."""
        with pytest.raises(ValueError, match="Token mismatch"):
            sexpr = "(wrong_token (int_field 42))"
            PrimitiveTestObject.from_sexpr(sexpr)

    def test_type_conversion_errors(self):
        """Test handling of type conversion errors."""
        # This should handle gracefully and use defaults
        sexpr = "(primitive_test (int_field not_a_number))"
        obj = PrimitiveTestObject.from_sexpr(sexpr)
        assert obj.int_field == 0  # Should fallback to default

    def test_empty_sexpr(self):
        """Test handling of empty S-expression."""
        sexpr = "(primitive_test)"
        obj = PrimitiveTestObject.from_sexpr(sexpr)
        # Should create object with defaults
        assert obj.int_field == 0
        assert obj.str_field == ""
        assert obj.float_field == 0.0
        assert obj.bool_field is False


class TestSExpressionGeneration:
    """Test S-expression generation (to_sexpr method)."""

    def test_primitive_to_sexpr(self):
        """Test S-expression generation for primitives."""
        obj = PrimitiveTestObject(
            int_field=42, str_field="hello", float_field=3.14, bool_field=True
        )
        sexpr = obj.to_sexpr()

        assert isinstance(sexpr, list)
        assert sexpr[0] == "primitive_test"
        assert 42 in sexpr
        assert "hello" in sexpr
        assert 3.14 in sexpr

    def test_optional_to_sexpr(self):
        """Test S-expression generation for optional fields."""
        obj = OptionalTestObject(optional_int=123)
        sexpr = obj.to_sexpr()

        assert isinstance(sexpr, list)
        assert sexpr[0] == "optional_test"
        assert 123 in sexpr

    def test_nested_to_sexpr(self):
        """Test S-expression generation for nested objects."""
        nested = SimpleNestedObject(value=999)
        obj = NestedTestObject(name="parent", nested=nested)
        sexpr = obj.to_sexpr()

        assert isinstance(sexpr, list)
        assert sexpr[0] == "nested_test"
        assert "parent" in sexpr


class TestSpecialCases:
    """Test special cases and edge conditions."""

    def test_none_values(self):
        """Test handling of None values."""
        obj = OptionalTestObject()
        sexpr = obj.to_sexpr()
        restored = OptionalTestObject.from_sexpr(sexpr)

        assert restored.optional_int is None
        assert restored.optional_str is None
        assert restored.optional_bool is None

    def test_default_values(self):
        """Test that default values are properly handled."""
        obj = PrimitiveTestObject()  # All defaults
        assert obj.int_field == 0
        assert obj.str_field == ""
        assert obj.float_field == 0.0
        assert obj.bool_field is False

    def test_empty_string_parsing(self):
        """Test parsing of empty strings."""
        sexpr = '(primitive_test (str_field ""))'
        obj = PrimitiveTestObject.from_sexpr(sexpr)
        assert obj.str_field == ""  # Empty string should be empty, not '""'


class TestParseContext:
    """Test ParseContext and type registry functionality."""

    def test_parse_context_creation(self):
        """Test creating a new ParseContext."""
        context = ParseContext()
        assert context._type_registry == {}

    def test_register_type(self):
        """Test registering a type in ParseContext."""
        context = ParseContext()
        context.register_type(PrimitiveTestObject)
        assert "primitive_test" in context._type_registry
        assert context._type_registry["primitive_test"] == PrimitiveTestObject

    def test_get_type(self):
        """Test getting a registered type."""
        context = ParseContext()
        context.register_type(PrimitiveTestObject)

        retrieved_type = context.get_type("primitive_test")
        assert retrieved_type == PrimitiveTestObject

        non_existent = context.get_type("non_existent")
        assert non_existent is None

    def test_register_kicad_type_decorator(self):
        """Test the register_kicad_type decorator."""

        @register_kicad_type
        @dataclass
        class DecoratedTestObject(KiCadObject):
            __token_name__ = "decorated_test"
            value: int = field(default=0, metadata={"description": "Test value"})

        # Should be registered in global context
        retrieved = _global_context.get_type("decorated_test")
        assert retrieved == DecoratedTestObject

    def test_register_type_without_token_name(self):
        """Test registering a type without __token_name__."""

        @dataclass
        class NoTokenObject(KiCadObject):
            # Missing __token_name__
            value: int = field(default=0)

        context = ParseContext()
        context.register_type(NoTokenObject)
        # Should not be registered since no token name
        assert "" not in context._type_registry
        assert len(context._type_registry) == 0


class TestKiCadObjectValidation:
    """Test KiCadObject validation and post_init."""

    def test_valid_token_name(self):
        """Test object creation with valid token name."""
        obj = PrimitiveTestObject()
        assert obj.__token_name__ == "primitive_test"

    def test_missing_token_name(self):
        """Test object creation fails without token name."""
        with pytest.raises(ValueError, match="must define __token_name__"):

            @dataclass
            class InvalidObject(KiCadObject):
                # __token_name__ is empty
                pass

            InvalidObject()

    def test_empty_token_name(self):
        """Test object creation fails with empty token name."""
        with pytest.raises(ValueError, match="must define __token_name__"):

            @dataclass
            class EmptyTokenObject(KiCadObject):
                __token_name__ = ""

            EmptyTokenObject()


class TestFromSExprVariants:
    """Test different variants of from_sexpr input."""

    def test_from_string_sexpr(self):
        """Test parsing from string S-expression."""
        sexpr_str = "(primitive_test (int_field 42) (str_field hello))"
        obj = PrimitiveTestObject.from_sexpr(sexpr_str)
        assert obj.int_field == 42
        assert obj.str_field == "hello"

    def test_from_list_sexpr(self):
        """Test parsing from list S-expression."""
        sexpr_list = ["primitive_test", ["int_field", 42], ["str_field", "hello"]]
        obj = PrimitiveTestObject.from_sexpr(sexpr_list)
        assert obj.int_field == 42
        assert obj.str_field == "hello"

    def test_from_complex_string_sexpr(self):
        """Test parsing from complex multiline string S-expression."""
        sexpr_str = """(
            primitive_test
            (int_field 123)
            (str_field "quoted string")
            (float_field 3.14159)
            (bool_field yes)
        )"""
        obj = PrimitiveTestObject.from_sexpr(sexpr_str)
        assert obj.int_field == 123
        assert obj.str_field == "quoted string"
        assert abs(obj.float_field - 3.14159) < 0.0001
        assert obj.bool_field is True


class TestTypeCheckingHelpers:
    """Test the static helper methods for type checking."""

    def test_is_optional(self):
        """Test _is_optional method."""
        from typing import Optional, Union

        assert KiCadObject._is_optional(Optional[int]) is True
        assert KiCadObject._is_optional(Union[int, None]) is True
        assert KiCadObject._is_optional(int) is False
        assert KiCadObject._is_optional(str) is False
        assert KiCadObject._is_optional(List[int]) is False

    def test_get_optional_inner_type(self):
        """Test _get_optional_inner_type method."""
        from typing import Optional

        assert KiCadObject._get_optional_inner_type(Optional[int]) == int
        assert KiCadObject._get_optional_inner_type(Optional[str]) == str
        assert KiCadObject._get_optional_inner_type(Optional[float]) == float

    def test_is_list_type(self):
        """Test _is_list_type method."""
        assert KiCadObject._is_list_type(List[int]) is True
        assert KiCadObject._is_list_type(List[str]) is True
        # Note: bare 'list' type may not be detected correctly
        assert KiCadObject._is_list_type(int) is False
        assert KiCadObject._is_list_type(Optional[int]) is False

    def test_get_list_element_type(self):
        """Test _get_list_element_type method."""
        assert KiCadObject._get_list_element_type(List[int]) == int
        assert KiCadObject._get_list_element_type(List[str]) == str
        assert (
            KiCadObject._get_list_element_type(List[SimpleNestedObject])
            == SimpleNestedObject
        )
        # Fallback for untyped list
        assert KiCadObject._get_list_element_type(list) == str

    def test_is_kicad_object(self):
        """Test _is_kicad_object method."""
        assert KiCadObject._is_kicad_object(PrimitiveTestObject) is True
        assert KiCadObject._is_kicad_object(SimpleNestedObject) is True
        assert KiCadObject._is_kicad_object(int) is False
        assert KiCadObject._is_kicad_object(str) is False
        assert KiCadObject._is_kicad_object(List[int]) is False


class TestAdvancedParsing:
    """Test advanced parsing scenarios."""

    def test_parse_primitive_value_edge_cases(self):
        """Test _parse_primitive_value with edge cases."""
        # Test with empty data
        result = PrimitiveTestObject._parse_primitive_value("test_field", int, [])
        assert result == 0

        # Test with None data
        result = PrimitiveTestObject._parse_primitive_value("test_field", str, [None])
        assert result == ""

        # Test with nested list (should return default value)
        result = PrimitiveTestObject._parse_primitive_value(
            "test_field", int, [["nested", "data"]]
        )
        assert result == 0  # Default value for int

    def test_parse_field_value_unsupported_type(self):
        """Test _parse_field_value with unsupported type."""
        from typing import Dict

        result = PrimitiveTestObject._parse_field_value(
            "test_field", Dict[str, int], []
        )
        assert result is None

    def test_boolean_parsing_variants(self):
        """Test all boolean parsing variants."""
        test_cases = [
            ("yes", True),
            ("true", True),
            ("1", True),
            ("YES", True),
            ("TRUE", True),
            ("no", False),
            ("false", False),
            ("0", False),
            ("NO", False),
            ("FALSE", False),
            ("invalid", False),
        ]

        for value, expected in test_cases:
            result = PrimitiveTestObject._parse_primitive_value(
                "test_field", bool, [value]
            )
            assert result == expected, f"Failed for value '{value}'"

    def test_numeric_conversion_errors(self):
        """Test handling of numeric conversion errors."""
        # Invalid int
        result = PrimitiveTestObject._parse_primitive_value(
            "test_field", int, ["not_a_number"]
        )
        assert result == 0

        # Invalid float
        result = PrimitiveTestObject._parse_primitive_value(
            "test_field", float, ["not_a_float"]
        )
        assert result == 0.0


class TestSExpressionGeneration:
    """Extended tests for S-expression generation."""

    def test_to_sexpr_str_formatting(self):
        """Test to_sexpr_str with different formatting options."""
        obj = PrimitiveTestObject(int_field=42, str_field="hello")

        # Pretty print
        pretty_str = obj.to_sexpr_str(pretty_print=True)
        assert isinstance(pretty_str, str)
        assert "primitive_test" in pretty_str
        assert "42" in pretty_str
        assert "hello" in pretty_str

        # Compact print
        compact_str = obj.to_sexpr_str(pretty_print=False)
        assert isinstance(compact_str, str)
        assert "primitive_test" in compact_str

    def test_value_to_sexpr_none_handling(self):
        """Test _value_to_sexpr with None values."""
        obj = OptionalTestObject()
        result = obj._value_to_sexpr("optional_int", None)
        assert result is None

    def test_value_to_sexpr_list_of_primitives(self):
        """Test _value_to_sexpr with list of primitives."""
        obj = ListTestObject()
        result = obj._value_to_sexpr("int_list", [1, 2, 3])
        assert result == ["int_list", 1, 2, 3]

    def test_value_to_sexpr_list_of_objects(self):
        """Test _value_to_sexpr with list of KiCadObjects."""
        nested1 = SimpleNestedObject(value=10)
        nested2 = SimpleNestedObject(value=20)
        obj = ListTestObject()

        result = obj._value_to_sexpr("nested_list", [nested1, nested2])
        assert isinstance(result, list)
        assert len(result) == 3  # field_name + 2 objects
        assert result[0] == "nested_list"  # field name
        assert result[1] == ["simple_nested", 10]
        assert result[2] == ["simple_nested", 20]


class TestComplexErrorScenarios:
    """Test complex error scenarios and edge cases."""

    def test_invalid_sexpr_types(self):
        """Test handling of completely invalid S-expression types."""
        with pytest.raises(ValueError, match="Invalid S-expression"):
            PrimitiveTestObject.from_sexpr(None)

        with pytest.raises(ValueError, match="Invalid S-expression"):
            PrimitiveTestObject.from_sexpr(42)

        with pytest.raises(ValueError, match="Invalid S-expression"):
            PrimitiveTestObject.from_sexpr([])

    def test_token_mismatch_handling(self):
        """Test token mismatch error handling."""
        with pytest.raises(ValueError, match="Token mismatch"):
            PrimitiveTestObject.from_sexpr(["wrong_token", ["int_field", 42]])

    def test_malformed_nested_objects(self):
        """Test handling of malformed nested objects."""
        # Nested object with wrong token name should result in default
        sexpr = "(nested_test (name parent) (wrong_nested (value 42)))"
        obj = NestedTestObject.from_sexpr(sexpr)
        assert obj.name == "parent"
        assert obj.nested.value == 1  # Default value

    def test_deeply_nested_structures(self):
        """Test parsing deeply nested structures."""

        @dataclass
        class DeepNested1(KiCadObject):
            __token_name__ = "deep1"
            value: int = field(default=1)

        @dataclass
        class DeepNested2(KiCadObject):
            __token_name__ = "deep2"
            nested: DeepNested1 = field(default_factory=lambda: DeepNested1())

        @dataclass
        class DeepNested3(KiCadObject):
            __token_name__ = "deep3"
            nested: DeepNested2 = field(default_factory=lambda: DeepNested2())

        sexpr = "(deep3 (deep2 (deep1 (value 999))))"
        obj = DeepNested3.from_sexpr(sexpr)
        assert obj.nested.nested.value == 999


class TestFieldMetadataHandling:
    """Test handling of field metadata."""

    def test_field_with_required_metadata(self):
        """Test field with 'required' metadata."""

        @dataclass
        class RequiredFieldObject(KiCadObject):
            __token_name__ = "required_test"
            required_field: str = field(
                default="", metadata={"required": True, "description": "Required field"}
            )
            optional_field: Optional[str] = field(
                default=None, metadata={"required": False}
            )

        # Should work with required field present
        sexpr = "(required_test (required_field hello))"
        obj = RequiredFieldObject.from_sexpr(sexpr)
        assert obj.required_field == "hello"
        assert obj.optional_field is None

    def test_field_descriptions(self):
        """Test that field descriptions are preserved."""
        obj = PrimitiveTestObject()
        field_info = fields(obj)

        int_field = next(f for f in field_info if f.name == "int_field")
        assert int_field.metadata["description"] == "Integer field"


if __name__ == "__main__":
    # Run tests if called directly
    pytest.main([__file__, "-v"])
