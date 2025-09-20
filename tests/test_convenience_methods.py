"""Test convenience methods from_str and from_file for KiCadObject classes."""

import os
import tempfile
from pathlib import Path

from kicad_parserv2.base_element import ParseStrictness
from kicad_parserv2.base_types import Layer
from kicad_parserv2.board_layout import KicadPcb


def test_from_str_convenience_method():
    """Test from_str convenience method."""

    # Test simple Layer object with proper format
    layer_str = '(layer "F.Cu")'
    layer = Layer.from_str(layer_str)

    assert layer.name == "F.Cu"

    # Verify it's identical to from_sexpr
    layer_sexpr = Layer.from_sexpr(layer_str)
    assert layer.name == layer_sexpr.name


def test_from_file_with_strictness():
    """Test from_file with different strictness modes."""

    # Create a simple PCB file that might have missing fields
    pcb_content = """
    (kicad_pcb
        (version 20230620)
        (generator kicad_pcb)
        (general
            (thickness 1.6)
        )
        (page "A4")
        (layers
            (0 "F.Cu" signal)
        )
        (net 0 "")
    )
    """

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".kicad_pcb", delete=False, encoding="utf-8"
    ) as tmp_file:
        tmp_file.write(pcb_content)
        tmp_file_path = tmp_file.name

    try:
        # Test with LENIENT mode
        pcb = KicadPcb.from_file(tmp_file_path, ParseStrictness.LENIENT)

        assert pcb.version.version == 20230620
        assert pcb.generator.name == "kicad_pcb"
        assert len(pcb.nets) == 1

        # Test with explicit encoding
        pcb2 = KicadPcb.from_file(
            tmp_file_path, ParseStrictness.LENIENT, encoding="utf-8"
        )
        assert pcb2.version.version == pcb.version.version

    finally:
        # Clean up temporary file
        os.unlink(tmp_file_path)


def test_from_str_error_handling():
    """Test error handling in from_str method."""

    try:
        # Invalid S-expression should raise ValueError
        Layer.from_str("invalid s-expression")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Failed to parse S-expression" in str(e)


def test_convenience_methods_integration():
    """Test that convenience methods integrate properly with existing functionality."""

    # Create complex PCB content
    pcb_content = """
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
        (net 0 "")
        (net 1 "GND")
        (footprint "Package_DIP:DIP-8_W7.62mm"
            (at 100 100)
            (layer "F.Cu")
            (property "Reference" "U1")
            (property "Value" "ATtiny85")
        )
    )
    """

    # Test from_str
    pcb_from_str = KicadPcb.from_str(pcb_content, ParseStrictness.LENIENT)

    # Test from_file
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".kicad_pcb", delete=False, encoding="utf-8"
    ) as tmp_file:
        tmp_file.write(pcb_content)
        tmp_file_path = tmp_file.name

    try:
        pcb_from_file = KicadPcb.from_file(tmp_file_path, ParseStrictness.LENIENT)

        # Both should produce identical results
        assert pcb_from_str.version.version == pcb_from_file.version.version
        assert pcb_from_str.generator.name == pcb_from_file.generator.name
        assert len(pcb_from_str.nets) == len(pcb_from_file.nets)
        assert len(pcb_from_str.footprints) == len(pcb_from_file.footprints)

        # Test round-trip serialization
        serialized_list = pcb_from_file.to_sexpr()
        from kicad_parserv2.sexpr_parser import sexpr_to_str

        serialized_str = sexpr_to_str(serialized_list)
        pcb_round_trip = KicadPcb.from_str(serialized_str, ParseStrictness.STRICT)

        assert pcb_round_trip.version.version == pcb_from_file.version.version
        assert len(pcb_round_trip.nets) == len(pcb_from_file.nets)

    finally:
        os.unlink(tmp_file_path)


if __name__ == "__main__":
    test_from_str_convenience_method()
    test_from_file_with_strictness()
    test_from_str_error_handling()
    test_convenience_methods_integration()
    print("🎯 All convenience method tests passed!")
