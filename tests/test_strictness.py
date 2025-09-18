#!/usr/bin/env python3
"""Test script for the new ParseStrictness functionality."""

from kicad_parserv2 import ParseStrictness
from kicad_parserv2.board_layout import KicadPcb


def test_strictness():
    test_sexpr = """
    (kicad_pcb
        (version 20230620)
        (generator kicad_pcb)

        (general
            (thickness 1.6)
        )

        (page "A4")

        (layers
            (0 "F.Cu" signal)
            (31 "B.Cu" signal)
        )

        (setup
            (stackup
                (layer "F.Cu"
                    (type "copper")
                    (thickness 0.035)
                )
            )
        )

        (net 0 "")
        (net 1 "GND")
    )
    """

    print("Testing ParseStrictness levels...")

    # Test STRICT (should fail)
    print("\n1. STRICT mode:")
    try:
        pcb = KicadPcb.from_sexpr(test_sexpr, ParseStrictness.STRICT)
        print("✅ STRICT: Parsed successfully (unexpected)")
    except ValueError as e:
        print(f"❌ STRICT: Failed as expected - {e}")

    # Test LENIENT (should work with warnings)
    print("\n2. LENIENT mode:")
    try:
        pcb = KicadPcb.from_sexpr(test_sexpr, ParseStrictness.LENIENT)
        print(f"✅ LENIENT: Parsed successfully - Version: {pcb.version}")
    except Exception as e:
        print(f"❌ LENIENT: Failed - {e}")

    # Test PERMISSIVE (should work silently)
    print("\n3. PERMISSIVE mode:")
    try:
        pcb = KicadPcb.from_sexpr(test_sexpr, ParseStrictness.PERMISSIVE)
        print(f"✅ PERMISSIVE: Parsed successfully - Version: {pcb.version}")
    except Exception as e:
        print(f"❌ PERMISSIVE: Failed - {e}")


if __name__ == "__main__":
    test_strictness()
