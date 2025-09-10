"""
Integration tests for KiCad file format round-trip processing

Tests that objects can be serialized to S-expressions and parsed back
to equivalent objects without loss of information. This validates the
complete parse → serialize → parse cycle for all major KiCad file formats.
"""

import os
import tempfile

import pytest

from kicad_parser import *
from kicad_parser.kicad_board import FootprintPad, FootprintText, KiCadFootprint
from kicad_parser.kicad_board_elements import ZoneFillSettings
from kicad_parser.kicad_common import CoordinatePoint, CoordinatePointList
from kicad_parser.kicad_graphics import GraphicalCircle, GraphicalLine, GraphicalText
from kicad_parser.kicad_pcb import KiCadPCB, TrackSegment, Zone
from kicad_parser.kicad_schematic import (
    Bus,
    GlobalLabel,
    HierarchicalSheet,
    Junction,
    KiCadSchematic,
    LabelShape,
    LocalLabel,
    SchematicSymbol,
    Wire,
)
from kicad_parser.kicad_symbol import KiCadSymbol, KiCadSymbolLibrary, SymbolPin
from kicad_parser.kicad_worksheet import KiCadWorksheet, WorksheetLine, WorksheetText

# PROGRESS TRACKING - ROUND-TRIP INTEGRATION TESTS
# =======================================
# ✅ Creating round-trip tests for all main formats
# ✅ Test common classes round-trip (Position, Stroke, TextEffects, etc.)
# ✅ Test schematic format round-trip (KiCadSchematic with elements)
# ✅ Test PCB format round-trip (KiCadPCB with footprints and tracks)
# ✅ Test symbol format round-trip (KiCadSymbolLibrary with symbols)
# ✅ Test worksheet format round-trip (KiCadWorksheet with elements)
# ✅ Test complex integration scenarios


class TestCommonClassesRoundTrip:
    """Test round-trip functionality for common KiCad classes"""

    def test_position_round_trip(self):
        """Test Position round-trip with various angles"""
        positions = [
            Position(0.0, 0.0),
            Position(25.4, 38.1),
            Position(100.0, 200.0, 90.0),
            Position(-50.0, -75.0, 180.0),
            Position(12.7, 19.05, 45.5),
        ]

        for original in positions:
            sexpr = original.to_sexpr()
            parsed = Position.from_sexpr(sexpr)

            assert parsed.x == original.x
            assert parsed.y == original.y
            assert parsed.angle == original.angle

    def test_stroke_round_trip(self):
        """Test Stroke round-trip with different properties"""
        from kicad_parser.kicad_common import StrokeType

        strokes = [
            Stroke(width=0.15),
            Stroke(width=0.25, type=StrokeType.DASH, color=(1.0, 0.0, 0.0, 1.0)),
            Stroke(width=0.1, type=StrokeType.DOT, color=(0.0, 1.0, 0.0, 0.8)),
        ]

        for original in strokes:
            sexpr = original.to_sexpr()
            parsed = Stroke.from_sexpr(sexpr)

            assert parsed.width == original.width
            assert parsed.type == original.type
            assert parsed.color == original.color

    def test_text_effects_round_trip(self):
        """Test TextEffects round-trip with fonts"""
        from kicad_parser.kicad_common import JustifyHorizontal, JustifyVertical

        effects = [
            TextEffects(),
            TextEffects(
                font=Font(size_height=2.0, size_width=2.0, thickness=0.3, bold=True),
                justify_horizontal=JustifyHorizontal.LEFT,
                justify_vertical=JustifyVertical.BOTTOM,
                hide=True,
            ),
        ]

        for original in effects:
            sexpr = original.to_sexpr()
            parsed = TextEffects.from_sexpr(sexpr)

            assert parsed.font.size_height == original.font.size_height
            assert parsed.font.size_width == original.font.size_width
            assert parsed.justify_horizontal == original.justify_horizontal
            assert parsed.hide == original.hide

    def test_coordinate_point_list_round_trip(self):
        """Test CoordinatePointList round-trip"""
        points = [
            CoordinatePoint(10.0, 20.0),
            CoordinatePoint(30.0, 40.0),
            CoordinatePoint(50.0, 60.0),
        ]
        original = CoordinatePointList(points)

        sexpr = original.to_sexpr()
        parsed = CoordinatePointList.from_sexpr(sexpr)

        assert len(parsed.points) == len(original.points)
        for i, point in enumerate(parsed.points):
            assert point.x == original.points[i].x
            assert point.y == original.points[i].y


class TestSchematicRoundTrip:
    """Test round-trip functionality for schematic files"""

    def test_basic_schematic_round_trip(self):
        """Test basic schematic with common elements"""
        from kicad_parser.kicad_schematic import create_basic_schematic

        # Create schematic with various elements
        original = create_basic_schematic("Round-Trip Test", "Test Company")

        # Add junction
        original.junctions.append(
            Junction(
                position=Position(50.0, 75.0),
                diameter=0.36,
                uuid=UUID("junction-test-123"),
            )
        )

        # Add wire
        original.wires.append(
            Wire(
                points=CoordinatePointList([(25.0, 50.0), (75.0, 50.0)]),
                uuid=UUID("wire-test-456"),
            )
        )

        # Add global label
        original.global_labels.append(
            GlobalLabel(
                text="TEST_SIGNAL",
                position=Position(100.0, 50.0),
                shape=LabelShape.INPUT,
                uuid=UUID("label-test-789"),
            )
        )

        # Perform round-trip
        sexpr = original.to_sexpr()
        parsed = KiCadSchematic.from_sexpr(sexpr)

        # Verify structure preservation
        assert parsed.version == original.version
        assert parsed.title_block.title == original.title_block.title
        assert len(parsed.junctions) == len(original.junctions)
        assert len(parsed.wires) == len(original.wires)
        assert len(parsed.global_labels) == len(original.global_labels)

        # Verify element details
        assert parsed.junctions[0].position.x == original.junctions[0].position.x
        assert parsed.junctions[0].diameter == original.junctions[0].diameter
        assert len(parsed.wires[0].points) == len(original.wires[0].points)
        assert parsed.global_labels[0].text == original.global_labels[0].text
        assert parsed.global_labels[0].shape == original.global_labels[0].shape

    def test_complex_schematic_round_trip(self):
        """Test complex schematic with hierarchical sheets"""
        original = KiCadSchematic(
            version=20230121,
            generator="round_trip_test",
            title_block=TitleBlock(
                title="Complex Test", date="2023-01-01", revision="1.0"
            ),
        )

        # Add hierarchical sheet
        from kicad_parser.kicad_schematic import PinElectricalType

        sheet_pins = [
            HierarchicalPin(
                name="VCC",
                electrical_type=PinElectricalType.INPUT,
                position=Position(200.0, 100.0),
                uuid=UUID("pin-vcc-123"),
            ),
            HierarchicalPin(
                name="GND",
                electrical_type=PinElectricalType.OUTPUT,
                position=Position(200.0, 150.0),
                uuid=UUID("pin-gnd-456"),
            ),
        ]

        original.sheets.append(
            HierarchicalSheet(
                position=Position(150.0, 75.0),
                size=(100.0, 100.0),
                uuid=UUID("sheet-test-789"),
                sheet_name="Power Supply",
                file_name="power.kicad_sch",
                pins=sheet_pins,
            )
        )

        # Round-trip test
        sexpr = original.to_sexpr()
        parsed = KiCadSchematic.from_sexpr(sexpr)

        assert len(parsed.sheets) == 1
        assert parsed.sheets[0].sheet_name == "Power Supply"
        assert parsed.sheets[0].file_name == "power.kicad_sch"
        assert len(parsed.sheets[0].pins) == 2
        assert parsed.sheets[0].pins[0].name == "VCC"
        assert parsed.sheets[0].pins[1].name == "GND"


class TestPCBRoundTrip:
    """Test round-trip functionality for PCB files"""

    def test_basic_pcb_round_trip(self):
        """Test basic PCB with footprints and tracks"""
        from kicad_parser.kicad_pcb import create_basic_pcb

        # Create basic PCB
        original = create_basic_pcb("Round-Trip PCB Test")

        # Add a track segment
        original.track_segments.append(
            TrackSegment(
                start=(100.0, 100.0),
                end=(150.0, 100.0),
                width=0.25,
                layer="F.Cu",
                net=1,
                uuid=UUID("track-test-123"),
            )
        )

        # Add a footprint
        footprint = KiCadFootprint(
            library_link="Resistor_SMD:R_0805_2012Metric",
            position=Position(125.0, 125.0),
            uuid=UUID("footprint-test-456"),
        )

        # Add pad to footprint
        from kicad_parser.kicad_board import PadShape, PadType

        footprint.pads.append(
            FootprintPad(
                number="1",
                type=PadType.SMD,
                shape=PadShape.ROUNDRECT,
                position=Position(0.0, 0.0),
                size=(1.0, 1.3),
                layers=["F.Cu", "F.Paste", "F.Mask"],
                uuid=UUID("pad-test-789"),
            )
        )

        original.footprints.append(footprint)

        # Round-trip test
        sexpr = original.to_sexpr()
        parsed = KiCadPCB.from_sexpr(sexpr)

        # Verify structure
        assert len(parsed.track_segments) == len(original.track_segments)
        assert len(parsed.footprints) == len(original.footprints)

        # Verify track details
        assert parsed.track_segments[0].start[0] == original.track_segments[0].start[0]
        assert parsed.track_segments[0].width == original.track_segments[0].width
        assert parsed.track_segments[0].layer == original.track_segments[0].layer

        # Verify footprint details
        assert parsed.footprints[0].library_link == original.footprints[0].library_link
        assert len(parsed.footprints[0].pads) == len(original.footprints[0].pads)
        assert (
            parsed.footprints[0].pads[0].number == original.footprints[0].pads[0].number
        )

    def test_pcb_with_zones_round_trip(self):
        """Test PCB with copper zones"""
        original = KiCadPCB(version=20230121, generator="zone_test")

        # Create zone with polygon
        zone_points = CoordinatePointList(
            [(50.0, 50.0), (150.0, 50.0), (150.0, 150.0), (50.0, 150.0)]
        )

        original.zones.append(
            Zone(
                net=1,
                net_name="GND",
                layers=["F.Cu"],
                uuid=UUID("zone-test-123"),
                polygon_points=zone_points,
                fill_settings=ZoneFillSettings(
                    thermal_gap=0.508, thermal_bridge_width=0.508
                ),
            )
        )

        # Round-trip test
        sexpr = original.to_sexpr()
        parsed = KiCadPCB.from_sexpr(sexpr)

        assert len(parsed.zones) == 1
        assert parsed.zones[0].net == 1
        assert parsed.zones[0].net_name == "GND"
        assert len(parsed.zones[0].polygon_points) == 4


class TestSymbolLibraryRoundTrip:
    """Test round-trip functionality for symbol libraries"""

    def test_symbol_library_round_trip(self):
        """Test symbol library with multiple symbols"""
        original = KiCadSymbolLibrary(version=20230121, generator="round_trip_test")

        # Create symbol with pins
        symbol = KiCadSymbol(
            name="Device:R",
            pin_numbers_hide=False,
            pin_names_offset=0.508,
            in_bom=True,
            on_board=True,
        )

        # Add pins
        from kicad_parser.kicad_symbol import PinElectricalType, PinGraphicStyle

        symbol.pins.append(
            SymbolPin(
                number="1",
                name="~",
                electrical_type=PinElectricalType.PASSIVE,
                graphic_style=PinGraphicStyle.LINE,
                position=Position(-2.54, 0.0),
                length=2.54,
            )
        )

        symbol.pins.append(
            SymbolPin(
                number="2",
                name="~",
                electrical_type=PinElectricalType.PASSIVE,
                graphic_style=PinGraphicStyle.LINE,
                position=Position(2.54, 0.0),
                length=2.54,
            )
        )

        original.symbols.append(symbol)

        # Round-trip test
        sexpr = original.to_sexpr()
        parsed = KiCadSymbolLibrary.from_sexpr(sexpr)

        assert len(parsed.symbols) == 1
        assert parsed.symbols[0].name == original.symbols[0].name
        assert len(parsed.symbols[0].pins) == 2
        assert parsed.symbols[0].pins[0].number == "1"
        assert parsed.symbols[0].pins[1].number == "2"


class TestWorksheetRoundTrip:
    """Test round-trip functionality for worksheet files"""

    def test_worksheet_round_trip(self):
        """Test worksheet with various elements"""

        original = KiCadWorksheet(version=20230121, generator="round_trip_test")

        # Add additional elements
        original.lines.append(
            WorksheetLine(
                start=Position(50.0, 50.0),
                end=Position(150.0, 50.0),
                linewidth=0.25,
                repeat=3,
                incrx=25.0,
            )
        )

        original.texts.append(
            WorksheetText(text="Test Text", position=Position(100.0, 100.0), maxlen=20)
        )

        # Round-trip test
        sexpr = original.to_sexpr()
        parsed = KiCadWorksheet.from_sexpr(sexpr)

        assert parsed.version == original.version
        assert len(parsed.lines) == len(original.lines)
        assert len(parsed.texts) == len(original.texts)

        # Check added elements (use width property which handles both stroke and linewidth)
        added_line = next((line for line in parsed.lines if line.width == 0.25), None)
        assert added_line is not None
        assert added_line.repeat == 3
        assert added_line.incrx == 25.0

        added_text = next(
            (text for text in parsed.texts if text.text == "Test Text"), None
        )
        assert added_text is not None
        assert added_text.position.x == 100.0


class TestFileFormatIntegration:
    """Test complete file format integration scenarios"""

    def test_temporary_file_round_trip(self):
        """Test saving and loading from temporary files"""
        from kicad_parser.kicad_schematic import load_schematic, save_schematic

        # Create original schematic
        original = KiCadSchematic(
            version=20230121,
            generator="file_test",
            title_block=TitleBlock(title="File Test", company="Test Co"),
        )

        original.junctions.append(
            Junction(
                position=Position(25.4, 38.1),
                diameter=0.36,
                uuid=UUID("file-junction-123"),
            )
        )

        # Save to temporary file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".kicad_sch", delete=False
        ) as f:
            temp_path = f.name

        try:
            save_schematic(original, temp_path)

            # Load from file
            parsed = load_schematic(temp_path)

            # Verify content
            assert parsed.version == original.version
            assert parsed.title_block.title == original.title_block.title
            assert len(parsed.junctions) == len(original.junctions)
            assert parsed.junctions[0].position.x == original.junctions[0].position.x

        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_complex_multi_element_integration(self):
        """Test complex scenario with multiple interconnected elements"""
        original = KiCadSchematic(version=20230121, generator="integration_test")

        # Create interconnected elements that reference each other
        junction_uuid = UUID("junction-main-123")
        wire_uuid = UUID("wire-main-456")
        label_uuid = UUID("label-main-789")

        # Junction at connection point
        original.junctions.append(
            Junction(position=Position(100.0, 100.0), uuid=junction_uuid)
        )

        # Wire connecting to junction
        original.wires.append(
            Wire(
                points=CoordinatePointList(
                    [(50.0, 100.0), (100.0, 100.0)]
                ),  # Connects to junction
                uuid=wire_uuid,
            )
        )

        # Label at junction
        original.global_labels.append(
            GlobalLabel(
                text="SIGNAL_NET",
                position=Position(100.0, 100.0),  # Same position as junction
                shape=LabelShape.BIDIRECTIONAL,
                uuid=label_uuid,
            )
        )

        # Round-trip and verify relationships preserved
        sexpr = original.to_sexpr()
        parsed = KiCadSchematic.from_sexpr(sexpr)

        # All elements should be present
        assert len(parsed.junctions) == 1
        assert len(parsed.wires) == 1
        assert len(parsed.global_labels) == 1

        # Positions should match (indicating preserved connections)
        junction_pos = parsed.junctions[0].position
        label_pos = parsed.global_labels[0].position
        wire_end = parsed.wires[0].points[-1]  # Last point of wire

        assert junction_pos.x == label_pos.x == wire_end[0] == 100.0
        assert junction_pos.y == label_pos.y == wire_end[1] == 100.0


if __name__ == "__main__":
    pytest.main([__file__])
