#!/usr/bin/env python3
"""Comprehensive round-trip test for all KiCad classes."""

import inspect
from dataclasses import fields
from typing import get_args, get_origin

import kicad_parserv2
from kicad_parserv2.base_element import KiCadObject, ParseStrictness


def get_all_kicad_classes():
    """Get all KiCadObject classes from kicad_parserv2."""
    classes = []

    # Get all exported classes from __all__
    for name in kicad_parserv2.__all__:
        obj = getattr(kicad_parserv2, name)

        # Check if it's a class and inherits from KiCadObject
        if (
            inspect.isclass(obj) and issubclass(obj, KiCadObject) and obj != KiCadObject
        ):  # Exclude base class
            classes.append(obj)

    return sorted(classes, key=lambda cls: cls.__name__)


def create_default_instance(cls):
    """Create a default instance of a KiCad class."""
    try:
        # Try to create with all defaults
        return cls()
    except Exception as e:
        print(f"  ❌ Could not create default instance: {e}")
        return None


def run_class_round_trip(cls):
    """Test round-trip for a single KiCad class."""
    print(f"\n--- Testing {cls.__name__} ---")

    # Create default instance
    original = create_default_instance(cls)
    if original is None:
        return False

    print(f"  ✅ Created instance: {original}")

    try:
        # Convert to S-expression
        sexpr = original.to_sexpr()
        print(f"  ✅ Serialized: {sexpr}")

        # Parse back from S-expression with COMPLETE mode to verify all parameters are consumed
        regenerated = cls.from_sexpr(sexpr, ParseStrictness.COMPLETE)
        print(f"  ✅ Parsed back: {regenerated}")

        # Test equality
        are_equal = original == regenerated

        if are_equal:
            print(f"  ✅ Round-trip successful for {cls.__name__}")
            return True
        else:
            print(f"  ❌ Round-trip failed for {cls.__name__}: objects not equal")

            # Debug differences
            print(f"    Original:    {original}")
            print(f"    Regenerated: {regenerated}")

            # Compare field by field
            field_infos = original._classify_fields()
            for field_info in field_infos:
                orig_val = getattr(original, field_info.name)
                regen_val = getattr(regenerated, field_info.name)
                if orig_val != regen_val:
                    print(f"    Diff in {field_info.name}: {orig_val} != {regen_val}")

            return False

    except Exception as e:
        print(f"  ❌ Round-trip failed for {cls.__name__}: {e}")
        return False


def test_all_classes():
    """Test round-trip for all KiCad classes."""
    print("=== COMPREHENSIVE ROUND-TRIP TEST FOR ALL KICAD CLASSES ===")

    # Get all classes
    classes = get_all_kicad_classes()
    print(f"Found {len(classes)} KiCad classes to test")

    # Track results
    passed = []
    failed = []
    skipped = []

    # Test each class
    for cls in classes:
        try:
            success = run_class_round_trip(cls)
            if success:
                passed.append(cls.__name__)
            else:
                failed.append(cls.__name__)
        except Exception as e:
            print(f"\n--- Testing {cls.__name__} ---")
            print(f"  ❌ Exception during test: {e}")
            skipped.append((cls.__name__, str(e)))

    # Print summary
    print("\n" + "=" * 60)
    print("ROUND-TRIP TEST SUMMARY")
    print("=" * 60)

    print(f"\n✅ PASSED ({len(passed)}):")
    for name in passed:
        print(f"  - {name}")

    if failed:
        print(f"\n❌ FAILED ({len(failed)}):")
        for name in failed:
            print(f"  - {name}")

    if skipped:
        print(f"\n⚠️  SKIPPED ({len(skipped)}):")
        for name, reason in skipped:
            print(f"  - {name}: {reason}")

    print(f"\nTotal: {len(classes)} classes")
    print(
        f"Success rate: {len(passed)}/{len(classes)} ({100*len(passed)/len(classes):.1f}%)"
    )

    # Overall result
    if len(failed) == 0 and len(skipped) == 0:
        print("\n🎉 ALL TESTS PASSED! 🎉")
    else:
        print(f"\n⚠️  {len(failed)} failures, {len(skipped)} skipped")
        assert (
            len(failed) == 0 and len(skipped) == 0
        ), f"{len(failed)} failures, {len(skipped)} skipped"


def test_specific_classes():
    """Test specific classes that are commonly used."""
    print("\n=== TESTING SPECIFIC IMPORTANT CLASSES ===")

    # Import specific classes for targeted testing
    from kicad_parserv2.base_types import At, Layer, Size, Xy
    from kicad_parserv2.pad_and_drill import Net
    from kicad_parserv2.text_and_documents import Generator, Version

    important_classes = [At, Layer, Size, Xy, Version, Generator, Net]

    for cls in important_classes:
        run_class_round_trip(cls)


if __name__ == "__main__":
    # First test important classes
    test_specific_classes()

    # Then test all classes
    success = test_all_classes()

    if success:
        exit(0)
    else:
        exit(1)
