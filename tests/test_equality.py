#!/usr/bin/env python3
"""Test the new __eq__ method for KiCadObjects."""

from kicad_parserv2 import ParseStrictness
from kicad_parserv2.board_layout import KicadPcb


def test_round_trip_equality():
    """Test round-trip equality using the new __eq__ method."""
    print("=== Testing Round-Trip Equality ===")

    test_sexpr = """
    (kicad_pcb
        (version 20230620)
        (generator kicad_pcb)
        (general (thickness 1.6))
        (page "A4")
        (layers (0 "F.Cu" signal) (31 "B.Cu" signal))
        (setup
            (stackup
                (layer "F.Cu" (type "copper") (thickness 0.035))
            )
        )
        (net 0 "")
        (net 1 "GND")
        (net 2 "VCC")
    )
    """

    # Parse original
    print("1. Parsing original...")
    pcb1 = KicadPcb.from_sexpr(test_sexpr, ParseStrictness.LENIENT)

    # Round-trip: to_sexpr -> from_sexpr
    print("2. Round-trip conversion...")
    regenerated_sexpr = pcb1.to_sexpr()
    pcb2 = KicadPcb.from_sexpr(regenerated_sexpr, ParseStrictness.LENIENT)

    # Test equality
    print("3. Testing equality...")
    are_equal = pcb1 == pcb2
    print(f"PCBs are equal: {are_equal}")

    if are_equal:
        print("✅ Round-trip equality test PASSED!")
    else:
        print("❌ Round-trip equality test FAILED!")

        # Debug differences
        print("\nDebugging differences...")
        print(f"PCB1 version: {pcb1.version}")
        print(f"PCB2 version: {pcb2}")
        print(f"Setup equal: {pcb1.setup == pcb2.setup}")
        print(f"Nets equal: {pcb1.nets == pcb2.nets}")
        print(f"PCB1 nets count: {len(pcb1.nets)}")
        print(f"PCB2 nets count: {len(pcb2.nets)}")


def test_equality_edge_cases():
    """Test equality edge cases."""
    print("\n=== Testing Equality Edge Cases ===")

    # Same object
    pcb1 = KicadPcb.from_sexpr(
        "(kicad_pcb (version 1) (generator test))", ParseStrictness.LENIENT
    )
    print(f"Same object equality: {pcb1 == pcb1}")  # Should be True

    # Different classes
    print(f"Different class equality: {pcb1 == 'not a pcb'}")  # Should be False

    # Same data, different instances
    pcb2 = KicadPcb.from_sexpr(
        "(kicad_pcb (version 1) (generator test))", ParseStrictness.LENIENT
    )
    print(f"Same data equality: {pcb1 == pcb2}")  # Should be True

    # Different data
    pcb3 = KicadPcb.from_sexpr(
        "(kicad_pcb (version 2) (generator test))", ParseStrictness.LENIENT
    )
    print(f"Different data equality: {pcb1 == pcb3}")  # Should be False


def test_equality_performance():
    """Test equality performance on larger objects."""
    print("\n=== Testing Equality Performance ===")

    complex_sexpr = """
    (kicad_pcb
        (version 20230620)
        (generator kicad_pcb)
        (general (thickness 1.6))
        (page "A4")
        (layers (0 "F.Cu" signal) (31 "B.Cu" signal))
        (setup (stackup (layer "F.Cu" (type "copper") (thickness 0.035))))
        (net 0 "")
        (net 1 "GND")
        (net 2 "VCC")
        (net 3 "5V")
        (net 4 "3V3")
    )
    """

    import time

    pcb1 = KicadPcb.from_sexpr(complex_sexpr, ParseStrictness.LENIENT)
    pcb2 = KicadPcb.from_sexpr(complex_sexpr, ParseStrictness.LENIENT)

    start_time = time.time()
    are_equal = pcb1 == pcb2
    elapsed = time.time() - start_time

    print(f"Complex equality check: {are_equal}")
    print(f"Time taken: {elapsed:.4f} seconds")


if __name__ == "__main__":
    test_round_trip_equality()
    test_equality_edge_cases()
    test_equality_performance()
