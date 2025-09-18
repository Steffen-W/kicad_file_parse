"""Tests for parameter tracking when parsing from strings."""

import pytest

from kicad_parserv2.base_element import ParseStrictness
from kicad_parserv2.base_types import At, Layer, Size
from kicad_parserv2.sexpr_parser import str_to_sexpr


def test_string_parsing_with_complete_mode_success():
    """Test parsing from string with COMPLETE mode when all parameters are used."""

    # Test cases with different S-expression strings
    test_cases = [
        {
            "string": "(at 10.0 20.0 90.0)",
            "class": At,
            "expected_values": {"x": 10.0, "y": 20.0, "angle": 90.0},
        },
        {
            "string": "(size 1.5 2.5)",
            "class": Size,
            "expected_values": {"width": 1.5, "height": 2.5},
        },
        {
            "string": '(layer "F.Cu")',
            "class": Layer,
            "expected_values": {"name": "F.Cu"},
        },
    ]

    for test_case in test_cases:
        print(f"\nTesting: {test_case['string']}")

        # Parse string to S-expression
        sexpr_data = str_to_sexpr(test_case["string"])

        # Should parse successfully in COMPLETE mode
        obj = test_case["class"]._parse_sexpr(sexpr_data, ParseStrictness.COMPLETE)

        # Verify values
        for attr, expected_value in test_case["expected_values"].items():
            actual_value = getattr(obj, attr)
            assert (
                actual_value == expected_value
            ), f"Expected {attr}={expected_value}, got {actual_value}"


def test_string_parsing_with_complete_mode_unused_parameters():
    """Test parsing from string with COMPLETE mode when parameters are unused."""

    test_cases = [
        {
            "string": "(at 10.0 20.0 90.0 unused_param extra_value)",
            "class": At,
            "expected_unused": ["unused_param", "extra_value"],
        },
        {
            "string": '(size 1.0 2.0 "extra" "parameters")',
            "class": Size,
            "expected_unused": ["extra", "parameters"],
        },
    ]

    for test_case in test_cases:
        print(f"\nTesting: {test_case['string']}")

        # Parse string to S-expression
        sexpr_data = str_to_sexpr(test_case["string"])

        # Should raise ValueError for unused parameters in COMPLETE mode
        with pytest.raises(ValueError, match="Unused parameters"):
            test_case["class"]._parse_sexpr(sexpr_data, ParseStrictness.COMPLETE)


def test_string_parsing_other_strictness_modes():
    """Test that other strictness modes work with string parsing regardless of unused parameters."""

    # String with extra parameters
    test_string = '(at 5.0 15.0 45.0 "ignored" "parameters")'
    sexpr_data = str_to_sexpr(test_string)

    # Should work with all other strictness modes
    for strictness in [
        ParseStrictness.STRICT,
        ParseStrictness.LENIENT,
        ParseStrictness.PERMISSIVE,
    ]:
        at_obj = At._parse_sexpr(sexpr_data, strictness)
        assert at_obj.x == 5.0
        assert at_obj.y == 15.0
        assert at_obj.angle == 45.0


def test_complex_string_parsing_with_nested_structures():
    """Test string parsing with more complex nested S-expressions."""

    # Test with nested structures (this would be handled by higher-level parsing)
    simple_string = "(at 0.0 0.0)"
    sexpr_data = str_to_sexpr(simple_string)

    print(f"\nParsed S-expression from '{simple_string}': {sexpr_data}")

    # Should parse successfully
    at_obj = At._parse_sexpr(sexpr_data, ParseStrictness.COMPLETE)
    assert at_obj.x == 0.0
    assert at_obj.y == 0.0
    # angle is optional and will be None when not provided
    assert at_obj.angle is None


def test_string_parsing_error_handling():
    """Test error handling when parsing invalid strings."""

    # Test with malformed S-expression
    invalid_strings = [
        "(at 10.0",  # Missing closing parenthesis
        "at 10.0 20.0)",  # Missing opening parenthesis
        "(at non_numeric_value 20.0)",  # Invalid numeric value
    ]

    for invalid_string in invalid_strings:
        print(f"\nTesting invalid string: {invalid_string}")

        try:
            sexpr_data = str_to_sexpr(invalid_string)
            # If parsing succeeds, test that the object parsing handles it gracefully
            try:
                At._parse_sexpr(sexpr_data, ParseStrictness.COMPLETE)
            except (ValueError, TypeError) as e:
                print(f"   Expected error in object parsing: {e}")
        except ValueError as e:
            print(f"   Expected error in string parsing: {e}")


def test_real_world_string_parsing_scenario():
    """Test a real-world scenario parsing multiple strings from a hypothetical KiCad file."""

    # Simulate reading S-expressions from a file as strings
    kicad_expressions = [
        "(at 0.0 0.0 0.0)",
        "(size 1.0 1.0)",
        '(layer "F.Cu")',
        # These have extra parameters that would be detected as gaps
        "(at 5.0 10.0 45.0 snap_to_grid true)",
        "(size 2.0 3.0 units mm tolerance 0.1)",
    ]

    print("\n=== Real-world String Parsing Scenario ===")
    print("Analyzing S-expression strings for parser completeness...")

    gaps_found = 0
    total_analyzed = 0

    for i, expr_string in enumerate(kicad_expressions):
        print(f"\nExpression {i+1}: {expr_string}")

        try:
            # Parse string to S-expression
            sexpr_data = str_to_sexpr(expr_string)

            # Determine class based on token name (handle Symbol objects)
            token_name = str(sexpr_data[0])
            if token_name == "at":
                obj_class = At
            elif token_name == "size":
                obj_class = Size
            elif token_name == "layer":
                obj_class = Layer
            else:
                print(f"   Skipping unknown token: {token_name}")
                continue

            total_analyzed += 1

            try:
                obj = obj_class._parse_sexpr(sexpr_data, ParseStrictness.COMPLETE)
                print(f"   ✓ Complete: All parameters consumed")
            except ValueError as e:
                gaps_found += 1
                print(f"   ! Gap detected: {e}")

        except Exception as e:
            print(f"   ✗ Parsing error: {e}")

    print(f"\n=== Summary ===")
    print(f"Total analyzed: {total_analyzed}")
    print(f"Gaps found: {gaps_found}")
    if total_analyzed > 0:
        print(
            f"Completeness: {((total_analyzed - gaps_found) / total_analyzed * 100):.1f}%"
        )
    else:
        print("Completeness: No expressions were analyzed")


def test_direct_class_parsing_from_string():
    """Test direct parsing of KiCad objects from strings with parameter tracking."""

    print("\n=== Direct Class Parsing from String ===")

    test_cases = [
        {
            "description": "At object from string - complete",
            "string": "(at 1.0 2.0 45.0)",
            "class": At,
            "should_succeed": True,
        },
        {
            "description": "At object from string - with unused parameters",
            "string": "(at 1.0 2.0 45.0 locked reference_id 123)",
            "class": At,
            "should_succeed": False,
        },
        {
            "description": "Size object from string - complete",
            "string": "(size 3.0 4.0)",
            "class": Size,
            "should_succeed": True,
        },
        {
            "description": "Size object from string - with unused parameters",
            "string": "(size 3.0 4.0 auto_scale maintain_ratio)",
            "class": Size,
            "should_succeed": False,
        },
    ]

    for test_case in test_cases:
        print(f"\nTesting: {test_case['description']}")
        print(f"String: {test_case['string']}")

        # Step 1: Parse string to S-expression
        sexpr_data = str_to_sexpr(test_case["string"])
        print(f"Parsed S-expr: {sexpr_data}")

        # Step 2: Parse S-expression to KiCad object with COMPLETE tracking
        try:
            obj = test_case["class"]._parse_sexpr(sexpr_data, ParseStrictness.COMPLETE)
            if test_case["should_succeed"]:
                print(f"✓ SUCCESS: Object parsed correctly")
                print(f"   Result: {obj}")
            else:
                print(f"✗ UNEXPECTED SUCCESS: Should have detected unused parameters")

        except ValueError as e:
            if not test_case["should_succeed"]:
                print(f"✓ EXPECTED FAILURE: {e}")
            else:
                print(f"✗ UNEXPECTED FAILURE: {e}")

        # Step 3: Show that other modes work regardless
        try:
            obj_lenient = test_case["class"]._parse_sexpr(
                sexpr_data, ParseStrictness.LENIENT
            )
            print(f"   LENIENT mode: ✓ Always succeeds - {obj_lenient}")
        except Exception as e:
            print(f"   LENIENT mode: ✗ Failed - {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
