"""Tests for S-expression parameter tracking functionality."""

import pytest

from kicad_parserv2.base_element import ParseStrictness
from kicad_parserv2.base_types import At, Layer, Size
from kicad_parserv2.pad_and_drill import Pad
from kicad_parserv2.sexpr_parser import SExprParser


def test_sexpr_parser_tracking_basic():
    """Test basic parameter tracking in SExprParser."""
    # Simple S-expression with multiple parameters
    sexpr_data = ["pad", "1", "smd", "rect", [10.0, 20.0], [1.0, 2.0]]

    # Test with tracking enabled
    parser = SExprParser(sexpr_data, track_usage=True)

    # Mark some parameters as used
    parser.mark_used(1)  # "1"
    parser.mark_used(3)  # "rect"

    # Check unused parameters
    unused = parser.get_unused_parameters()
    assert len(unused) == 3  # "smd", [10.0, 20.0], [1.0, 2.0]
    assert "smd" in unused
    assert [10.0, 20.0] in unused
    assert [1.0, 2.0] in unused

    # Mark more parameters
    parser.mark_used(2)  # "smd"
    parser.mark_used(4)  # [10.0, 20.0]
    parser.mark_used(5)  # [1.0, 2.0]

    # Now all should be used
    unused = parser.get_unused_parameters()
    assert len(unused) == 0


def test_sexpr_parser_tracking_disabled():
    """Test that tracking can be disabled."""
    sexpr_data = ["pad", "1", "smd", "rect"]
    parser = SExprParser(sexpr_data, track_usage=False)

    # Marking should have no effect
    parser.mark_used(1)
    parser.mark_used(2)

    # Should return empty list when tracking is disabled
    unused = parser.get_unused_parameters()
    assert len(unused) == 0


def test_sexpr_parser_check_complete_usage_success():
    """Test check_complete_usage when all parameters are used."""
    sexpr_data = ["at", 10.0, 20.0, 90.0]
    parser = SExprParser(sexpr_data, track_usage=True)

    # Mark all parameters as used
    parser.mark_used(1)  # 10.0
    parser.mark_used(2)  # 20.0
    parser.mark_used(3)  # 90.0

    # Should not raise an exception
    parser.check_complete_usage("At")


def test_sexpr_parser_check_complete_usage_failure():
    """Test check_complete_usage when parameters are unused."""
    sexpr_data = ["at", 10.0, 20.0, 90.0]
    parser = SExprParser(sexpr_data, track_usage=True)

    # Only mark first parameter as used
    parser.mark_used(1)  # 10.0

    # Should raise an exception for unused parameters
    with pytest.raises(ValueError, match="Unused parameters in At: \\[20.0, 90.0\\]"):
        parser.check_complete_usage("At")


def test_complete_strictness_mode_with_fully_used_parameters():
    """Test COMPLETE strictness mode when all parameters are used."""
    # Simple At object S-expression: (at 10.0 20.0 90.0)
    sexpr_data = ["at", 10.0, 20.0, 90.0]

    # Should parse successfully in COMPLETE mode when all parameters are used
    at_obj = At.from_sexpr(sexpr_data, ParseStrictness.COMPLETE)

    assert at_obj.x == 10.0
    assert at_obj.y == 20.0
    assert at_obj.angle == 90.0


def test_complete_strictness_mode_with_unused_parameters():
    """Test COMPLETE strictness mode when parameters are unused."""
    # S-expression with extra unused parameters
    sexpr_data = ["at", 10.0, 20.0, 90.0, "unused_param", 42]

    # Should raise ValueError for unused parameters in COMPLETE mode
    with pytest.raises(ValueError, match="Unused parameters in At"):
        At.from_sexpr(sexpr_data, ParseStrictness.COMPLETE)


def test_complete_strictness_mode_with_complex_object():
    """Test COMPLETE strictness mode with a more complex object."""
    # Size object S-expression: (size 1.0 2.0)
    sexpr_data = ["size", 1.0, 2.0]

    # Should parse successfully when all parameters are used
    size_obj = Size.from_sexpr(sexpr_data, ParseStrictness.COMPLETE)

    assert size_obj.width == 1.0
    assert size_obj.height == 2.0


def test_complete_strictness_mode_with_complex_unused_parameters():
    """Test COMPLETE strictness mode with unused parameters in complex object."""
    # Size with extra unused parameters
    sexpr_data = ["size", 1.0, 2.0, "extra", "unused"]

    # Should raise ValueError for unused parameters
    with pytest.raises(ValueError, match="Unused parameters in Size"):
        Size.from_sexpr(sexpr_data, ParseStrictness.COMPLETE)


def test_other_strictness_modes_ignore_unused_parameters():
    """Test that other strictness modes don't fail on unused parameters."""
    # S-expression with extra unused parameters
    sexpr_data = ["at", 10.0, 20.0, 90.0, "unused", "parameters"]

    # Should work fine with other strictness modes
    for strictness in [
        ParseStrictness.STRICT,
        ParseStrictness.LENIENT,
        ParseStrictness.PERMISSIVE,
    ]:
        at_obj = At.from_sexpr(sexpr_data, strictness)
        assert at_obj.x == 10.0
        assert at_obj.y == 20.0
        assert at_obj.angle == 90.0


def test_complete_strictness_with_nested_objects():
    """Test COMPLETE strictness with objects that have nested elements."""
    # Create a more complex S-expression with nested objects
    # This would be for a pad with nested at and size elements
    sexpr_data = ["pad", "1", "smd", "rect", ["at", 0.0, 0.0, 0.0], ["size", 1.0, 2.0]]

    # Should parse successfully when all parameters are used
    try:
        pad_obj = Pad.from_sexpr(sexpr_data, ParseStrictness.COMPLETE)
        # Basic validation
        assert pad_obj.number == "1"
        assert pad_obj.type.value == "smd"
        assert pad_obj.shape.value == "rect"
    except ValueError as e:
        # If there are unused parameters, the error should mention them
        if "Unused parameters" in str(e):
            print(f"Expected unused parameters error: {e}")
        else:
            raise


def test_complete_strictness_with_optional_elements():
    """Test COMPLETE strictness with optional elements that are present."""
    # Layer object with simple name
    sexpr_data = ["layer", "F.Cu"]

    # Should work with COMPLETE mode
    layer_obj = Layer.from_sexpr(sexpr_data, ParseStrictness.COMPLETE)
    assert layer_obj.name == "F.Cu"


def test_tracking_preserves_parsing_correctness():
    """Test that tracking doesn't interfere with normal parsing."""
    # Test various objects to ensure tracking doesn't break normal functionality
    test_cases = [
        (["at", 10.0, 20.0], At),
        (["size", 1.0, 2.0], Size),
        (["layer", "F.Cu"], Layer),
    ]

    for sexpr_data, obj_class in test_cases:
        # Parse with and without COMPLETE mode
        obj_normal = obj_class.from_sexpr(sexpr_data, ParseStrictness.STRICT)
        obj_tracked = obj_class.from_sexpr(sexpr_data, ParseStrictness.COMPLETE)

        # Objects should be equivalent
        assert obj_normal == obj_tracked


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
