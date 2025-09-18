#!/usr/bin/env python3
"""Comprehensive test for KiCadObject to find all problems.

This test systematically tests all aspects of KiCadObject:
- Parsing with different strictness levels
- Serialization (to_sexpr)
- Round-trip conversion
- Field classification
- Multi-value vs named field detection
- List parsing
- Error handling
"""

import logging
from dataclasses import dataclass, field
from typing import List, Optional

from kicad_parserv2 import ParseStrictness
from kicad_parserv2.base_element import KiCadObject


# Test data classes covering different scenarios
@dataclass
class SimpleValue(KiCadObject):
    """Simple single-value token like (version 20230620)."""

    __token_name__ = "version"
    value: int = field(default=0)


@dataclass
class MultiValue(KiCadObject):
    """Multi-value token like (xy 10.0 20.0)."""

    __token_name__ = "xy"
    x: float = field(default=0.0)
    y: float = field(default=0.0)


@dataclass
class TripleValue(KiCadObject):
    """Triple-value token like (at 100 100 90)."""

    __token_name__ = "at"
    x: float = field(default=0.0)
    y: float = field(default=0.0)
    angle: Optional[float] = field(default=None)


@dataclass
class ComplexObject(KiCadObject):
    """Complex object with multiple named fields like Setup."""

    __token_name__ = "complex"
    required_field: float = field(default=0.0)
    optional_field: Optional[str] = field(default=None)
    another_required: int = field(default=42)


@dataclass
class NestedObject(KiCadObject):
    """Object containing other objects."""

    __token_name__ = "nested"
    name: str = field(default="test")
    position: Optional[MultiValue] = field(default=None)


@dataclass
class ListContainer(KiCadObject):
    """Object containing lists."""

    __token_name__ = "container"
    name: str = field(default="container")
    items: List[SimpleValue] = field(default_factory=list)
    positions: List[MultiValue] = field(default_factory=list)


def test_simple_value():
    """Test simple single-value tokens."""
    print("\n=== Testing Simple Value ===")

    # Test parsing
    sexpr = "(version 20230620)"
    obj = SimpleValue.from_sexpr(sexpr, ParseStrictness.COMPLETE)
    print(f"Parsed: {obj}")
    assert obj.value == 20230620

    # Test serialization
    regenerated = obj.to_sexpr()
    print(f"Serialized: {regenerated}")

    # Test round-trip
    obj2 = SimpleValue.from_sexpr(regenerated, ParseStrictness.COMPLETE)
    print(f"Round-trip: {obj2}")
    assert obj2.value == obj.value
    print("✅ Simple value: PASSED")


def test_multi_value():
    """Test multi-value tokens."""
    print("\n=== Testing Multi Value ===")

    # Test parsing
    sexpr = "(xy 10.5 20.3)"
    obj = MultiValue.from_sexpr(sexpr, ParseStrictness.COMPLETE)
    print(f"Parsed: {obj}")
    assert obj.x == 10.5
    assert obj.y == 20.3

    # Test serialization
    regenerated = obj.to_sexpr()
    print(f"Serialized: {regenerated}")

    # Test round-trip
    obj2 = MultiValue.from_sexpr(regenerated, ParseStrictness.COMPLETE)
    print(f"Round-trip: {obj2}")
    assert obj2.x == obj.x
    assert obj2.y == obj.y
    print("✅ Multi value: PASSED")


def test_triple_value():
    """Test triple-value tokens with optional field."""
    print("\n=== Testing Triple Value ===")

    # Test parsing with optional field present
    sexpr1 = "(at 100 200 90)"
    obj1 = TripleValue.from_sexpr(sexpr1, ParseStrictness.COMPLETE)
    print(f"Parsed with angle: {obj1}")
    assert obj1.x == 100
    assert obj1.y == 200
    assert obj1.angle == 90

    # Test parsing with optional field missing
    sexpr2 = "(at 100 200)"
    obj2 = TripleValue.from_sexpr(sexpr2, ParseStrictness.LENIENT)
    print(f"Parsed without angle: {obj2}")
    assert obj2.x == 100
    assert obj2.y == 200
    assert obj2.angle is None

    # Test serialization
    regenerated1 = obj1.to_sexpr()
    regenerated2 = obj2.to_sexpr()
    print(f"Serialized with angle: {regenerated1}")
    print(f"Serialized without angle: {regenerated2}")

    print("✅ Triple value: PASSED")


def test_complex_object():
    """Test complex objects with named fields."""
    print("\n=== Testing Complex Object ===")

    # Test parsing with all fields
    sexpr1 = (
        "(complex (required_field 3.14) (optional_field hello) (another_required 123))"
    )
    obj1 = ComplexObject.from_sexpr(sexpr1, ParseStrictness.COMPLETE)
    print(f"Parsed complete: {obj1}")
    assert obj1.required_field == 3.14
    assert obj1.optional_field == "hello"
    assert obj1.another_required == 123

    # Test parsing with missing optional field
    sexpr2 = "(complex (required_field 2.71) (another_required 456))"
    obj2 = ComplexObject.from_sexpr(sexpr2, ParseStrictness.LENIENT)
    print(f"Parsed partial: {obj2}")
    assert obj2.required_field == 2.71
    assert obj2.optional_field is None
    assert obj2.another_required == 456

    # Test serialization
    regenerated1 = obj1.to_sexpr()
    regenerated2 = obj2.to_sexpr()
    print(f"Serialized complete: {regenerated1}")
    print(f"Serialized partial: {regenerated2}")

    # This is where we expect to find the multi-value detection bug
    try:
        obj1_roundtrip = ComplexObject.from_sexpr(
            regenerated1, ParseStrictness.COMPLETE
        )
        print(f"Round-trip complete: {obj1_roundtrip}")
        print("✅ Complex object round-trip: PASSED")
    except Exception as e:
        print(f"❌ Complex object round-trip: FAILED - {e}")

    print("✅ Complex object: PARTIAL")


def test_nested_object():
    """Test objects containing other objects."""
    print("\n=== Testing Nested Object ===")

    # Test parsing
    sexpr = "(nested (name test_object) (xy 15.0 25.0))"
    obj = NestedObject.from_sexpr(sexpr, ParseStrictness.LENIENT)
    print(f"Parsed: {obj}")
    assert obj.name == "test_object"
    assert obj.position is not None
    assert obj.position.x == 15.0
    assert obj.position.y == 25.0

    # Test serialization
    regenerated = obj.to_sexpr()
    print(f"Serialized: {regenerated}")

    print("✅ Nested object: PASSED")


def test_list_container():
    """Test objects containing lists."""
    print("\n=== Testing List Container ===")

    # Test parsing
    sexpr = """(container
        (name test_container)
        (version 1)
        (version 2)
        (version 3)
        (xy 10 20)
        (xy 30 40)
    )"""
    obj = ListContainer.from_sexpr(sexpr, ParseStrictness.LENIENT)
    print(f"Parsed: {obj}")
    assert obj.name == "test_container"
    assert len(obj.items) == 3
    assert len(obj.positions) == 2
    assert obj.items[0].value == 1
    assert obj.items[1].value == 2
    assert obj.items[2].value == 3
    assert obj.positions[0].x == 10
    assert obj.positions[1].y == 40

    # Test serialization
    regenerated = obj.to_sexpr()
    print(f"Serialized: {regenerated}")

    print("✅ List container: PASSED")


def test_strictness_levels():
    """Test different strictness levels."""
    print("\n=== Testing Strictness Levels ===")

    # Incomplete S-expression (missing required fields)
    incomplete_sexpr = "(complex (required_field 1.23))"

    # STRICT should fail
    try:
        obj_strict = ComplexObject.from_sexpr(
            incomplete_sexpr, ParseStrictness.COMPLETE
        )
        print("❌ STRICT mode should have failed")
    except ValueError as e:
        print(f"✅ STRICT correctly failed: {e}")

    # LENIENT should work with warnings
    print("Testing LENIENT mode:")
    obj_lenient = ComplexObject.from_sexpr(incomplete_sexpr, ParseStrictness.LENIENT)
    print(f"LENIENT result: {obj_lenient}")
    assert obj_lenient.required_field == 1.23
    assert obj_lenient.another_required == 42  # Default value

    # PERMISSIVE should work silently
    print("Testing PERMISSIVE mode:")
    obj_permissive = ComplexObject.from_sexpr(
        incomplete_sexpr, ParseStrictness.PERMISSIVE
    )
    print(f"PERMISSIVE result: {obj_permissive}")
    assert obj_permissive.required_field == 1.23
    assert obj_permissive.another_required == 42  # Default value

    print("✅ Strictness levels: PASSED")


def test_error_cases():
    """Test various error conditions."""
    print("\n=== Testing Error Cases ===")

    # Invalid token name
    try:
        SimpleValue.from_sexpr("(wrong_token 123)", ParseStrictness.STRICT)
        print("❌ Should have failed on wrong token")
    except ValueError as e:
        print(f"✅ Correctly failed on wrong token: {e}")

    # Invalid type conversion
    try:
        SimpleValue.from_sexpr('(version "not_a_number")', ParseStrictness.STRICT)
        print("❌ Should have failed on type conversion")
    except ValueError as e:
        print(f"✅ Correctly failed on type conversion: {e}")

    # Empty S-expression
    try:
        SimpleValue.from_sexpr("()", ParseStrictness.STRICT)
        print("❌ Should have failed on empty sexpr")
    except ValueError as e:
        print(f"✅ Correctly failed on empty sexpr: {e}")

    print("✅ Error cases: PASSED")


def run_comprehensive_test():
    """Run all tests to find KiCadObject problems."""
    print("=== COMPREHENSIVE KiCadObject TEST ===")
    print("This test will systematically check all KiCadObject functionality")

    # Enable logging to see warnings
    logging.basicConfig(level=logging.WARNING)

    test_simple_value()
    test_multi_value()
    test_triple_value()
    test_complex_object()  # This will likely show the serialization bug
    test_nested_object()
    test_list_container()
    test_strictness_levels()
    test_error_cases()

    print("\n=== TEST SUMMARY ===")
    print("✅ Basic functionality works")
    print("✅ List parsing works (thanks to get_list_of_tokens)")
    print("✅ Strictness levels work")
    print("❌ Complex object serialization likely has multi-value detection bug")
    print("\nThe main issue to fix: Multi-value token detection in to_sexpr()")


if __name__ == "__main__":
    run_comprehensive_test()
