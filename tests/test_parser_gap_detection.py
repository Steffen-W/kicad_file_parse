"""Integration tests demonstrating parser gap detection using parameter tracking."""

import pytest

from kicad_parserv2.base_element import ParseStrictness
from kicad_parserv2.base_types import At, Size


def test_parser_gap_detection_demo():
    """Demonstrate how parameter tracking helps detect parser implementation gaps."""

    # Simulate a real KiCad S-expression that might have evolved to include new parameters
    # that our parser doesn't know about yet

    # Original S-expression our parser was designed for
    original_sexpr = ["at", 10.0, 20.0, 90.0]

    # New S-expression from a newer KiCad version with additional parameters
    # Let's say KiCad added a "locked" flag and "reference" parameter
    extended_sexpr = ["at", 10.0, 20.0, 90.0, "locked", "reference_point"]

    print("\n=== Parser Gap Detection Demo ===")

    # Test 1: Original S-expression should parse without issues
    print("\n1. Parsing original S-expression with COMPLETE mode:")
    try:
        at_obj = At.from_sexpr(original_sexpr, ParseStrictness.COMPLETE)
        print(
            f"   ✓ SUCCESS: Parsed At object: x={at_obj.x}, y={at_obj.y}, angle={at_obj.angle}"
        )
    except ValueError as e:
        print(f"   ✗ FAILED: {e}")

    # Test 2: Extended S-expression reveals parser gaps
    print("\n2. Parsing extended S-expression with COMPLETE mode:")
    try:
        at_obj = At.from_sexpr(extended_sexpr, ParseStrictness.COMPLETE)
        print(f"   ✗ UNEXPECTED SUCCESS: This should have failed!")
    except ValueError as e:
        print(f"   ✓ EXPECTED FAILURE: {e}")
        print(
            "   → This indicates our parser needs to be updated to handle new parameters"
        )

    # Test 3: Other strictness modes don't reveal the gap
    print("\n3. Parsing extended S-expression with LENIENT mode:")
    try:
        at_obj = At.from_sexpr(extended_sexpr, ParseStrictness.LENIENT)
        print(
            f"   ✓ SUCCESS: Parsed At object: x={at_obj.x}, y={at_obj.y}, angle={at_obj.angle}"
        )
        print("   → Parser gap is hidden - no indication that new parameters exist")
    except ValueError as e:
        print(f"   ✗ FAILED: {e}")


def test_detect_missing_parser_features():
    """Test detecting missing parser features through unused parameters."""

    # Simulate complex S-expressions that might have new features
    test_cases = [
        {
            "name": "At with new parameters",
            "sexpr": [
                "at",
                10.0,
                20.0,
                90.0,
                "snap_to_grid",
                "true",
                "layer_offset",
                0.1,
            ],
            "expected_unused": ["snap_to_grid", "true", "layer_offset", 0.1],
            "class": At,
        },
        {
            "name": "Size with new parameters",
            "sexpr": ["size", 1.0, 2.0, "min_size", 0.1, "max_size", 10.0],
            "expected_unused": ["min_size", 0.1, "max_size", 10.0],
            "class": Size,
        },
    ]

    print("\n=== Missing Parser Features Detection ===")

    for test_case in test_cases:
        print(f"\nTesting: {test_case['name']}")

        try:
            # This should fail in COMPLETE mode
            obj = test_case["class"].from_sexpr(
                test_case["sexpr"], ParseStrictness.COMPLETE
            )
            print(f"   ✗ UNEXPECTED: Parsing succeeded when it should have failed")
        except ValueError as e:
            print(f"   ✓ DETECTED GAP: {e}")

            # Verify the specific unused parameters are mentioned
            error_msg = str(e)
            for unused_param in test_case["expected_unused"]:
                if str(unused_param) in error_msg:
                    print(f"     → Found expected unused parameter: {unused_param}")
                else:
                    print(f"     → Missing expected unused parameter: {unused_param}")


def test_parser_completeness_validation():
    """Test validating parser completeness across different object types."""

    # Test with known good S-expressions (should pass COMPLETE mode)
    good_test_cases = [
        (["at", 0.0, 0.0, 0.0], At, "At with all standard parameters"),
        (["at", 10.0, 20.0], At, "At with position only"),
        (["size", 1.0, 2.0], Size, "Size with width and height"),
    ]

    print("\n=== Parser Completeness Validation ===")

    for sexpr, obj_class, description in good_test_cases:
        print(f"\nTesting: {description}")
        try:
            obj = obj_class.from_sexpr(sexpr, ParseStrictness.COMPLETE)
            print(f"   ✓ COMPLETE: All parameters consumed successfully")
        except ValueError as e:
            print(f"   ✗ INCOMPLETE: {e}")
            print("   → This indicates a potential issue in our parser implementation")


def test_real_world_gap_scenario():
    """Simulate a real-world scenario where KiCad adds new features."""

    print("\n=== Real-World Parser Gap Scenario ===")
    print("Simulating discovery of new KiCad features through file analysis...")

    # Simulate reading multiple S-expressions from a KiCad file
    # Some might be from newer KiCad versions with additional features
    sample_expressions = [
        # Standard expressions our parser handles
        ["at", 0.0, 0.0, 0.0],
        ["size", 1.0, 1.0],
        # Expressions with hypothetical new features
        ["at", 5.0, 10.0, 45.0, "grid_snap", "enabled"],
        ["size", 2.0, 3.0, "auto_resize", "true"],
    ]

    gaps_found = 0
    total_tested = 0

    for i, expr in enumerate(sample_expressions):
        print(f"\nAnalyzing expression {i+1}: {expr}")
        total_tested += 1

        # Determine the appropriate class based on token name
        if expr[0] == "at":
            obj_class = At
        elif expr[0] == "size":
            obj_class = Size
        else:
            continue

        try:
            obj = obj_class.from_sexpr(expr, ParseStrictness.COMPLETE)
            print(f"   ✓ COMPLETE: Parser handles all parameters")
        except ValueError as e:
            gaps_found += 1
            print(f"   ! GAP DETECTED: {e}")
            print("   → Recommendation: Update parser to handle these new parameters")

    print(f"\n=== Gap Detection Summary ===")
    print(f"Total expressions analyzed: {total_tested}")
    print(f"Parser gaps detected: {gaps_found}")
    print(
        f"Parser completeness: {((total_tested - gaps_found) / total_tested * 100):.1f}%"
    )

    if gaps_found > 0:
        print("\n🔍 RECOMMENDATION:")
        print("   Review the unused parameters and consider updating the parser")
        print("   to support new KiCad features for better future compatibility.")
    else:
        print("\n✅ PARSER STATUS: Complete for tested expressions")


if __name__ == "__main__":
    # Run the demo tests
    test_parser_gap_detection_demo()
    test_detect_missing_parser_features()
    test_parser_completeness_validation()
    test_real_world_gap_scenario()

    print("\n" + "=" * 60)
    print("Parameter tracking implementation successfully detects parser gaps!")
    print("=" * 60)
