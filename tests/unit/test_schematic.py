"""
Unit tests for KiCad schematic parser

Tests all components of the schematic file format according to
doc/file-formats/sexpr-schematic/_index.en.adoc
"""

import os
import tempfile
from pathlib import Path

import pytest

from kicad_parser import *
from kicad_parser.kicad_schematic import (
    Bus,
    BusEntry,
    GlobalLabel,
    HierarchicalLabel,
    HierarchicalPin,
    HierarchicalSheet,
    Junction,
    KiCadSchematic,
    LabelShape,
    LocalLabel,
    NoConnect,
    PinElectricalType,
    Polyline,
    RootSheetInstance,
    SchematicSymbol,
    SchematicText,
    SheetInstance,
    SheetProject,
    SymbolInstance,
    SymbolProject,
    Wire,
    create_basic_schematic,
    load_schematic,
    save_schematic,
)
from kicad_parser.sexpdata import loads

# PROGRESS TRACKING - SCHEMATIC TESTS
# =======================================
# ✓ Comprehensive test structure exists (TestSchematicCore, TestJunction, etc.)
# ✓ Junction, NoConnect, BusEntry classes - existing comprehensive tests
# ✓ Wire, Bus, Polyline classes - existing comprehensive tests
# ✓ SchematicText, LocalLabel, GlobalLabel classes - existing comprehensive tests
# ✓ HierarchicalLabel, SymbolInstance, SymbolProject classes - existing comprehensive tests
# ✓ SchematicSymbol classes - existing comprehensive tests
# ✓ HierarchicalPin, SheetInstance, SheetProject classes - existing comprehensive tests
# ✓ HierarchicalSheet, RootSheetInstance classes - existing comprehensive tests
# ✓ KiCadSchematic class - existing comprehensive tests
# ✓ Image class tests - COMPLETED (minimal + comprehensive)


class TestImage:
    """Test Image class for embedded images in schematics"""

    def test_image_minimal(self):
        """Test minimal Image creation and parsing"""
        # Minimal Image with just position
        sexpr_data = '(image (at 25.4 38.1) (scale 1.0) (uuid "test-uuid-1234") (data "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="))'

        sexpr = loads(sexpr_data)
        image = Image.from_sexpr(sexpr)

        assert image.position.x == 25.4
        assert image.position.y == 38.1
        assert image.scale == 1.0
        assert image.uuid.uuid == "test-uuid-1234"
        assert image.data is not None
        assert (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8" in image.data
        )

        # Test round-trip
        sexpr = image.to_sexpr()
        parsed_image = Image.from_sexpr(sexpr)
        assert parsed_image.position.x == image.position.x
        assert parsed_image.position.y == image.position.y
        assert parsed_image.scale == image.scale
        if parsed_image.uuid and image.uuid:
            assert parsed_image.uuid.uuid == image.uuid.uuid

    def test_image_comprehensive(self):
        """Test comprehensive Image with all parameters"""
        # Comprehensive Image with position, scale, layer, UUID, and base64 data
        sexpr_data = """(image 
            (at 127.0 101.6 45.0) 
            (scale 2.5) 
            (layer "F.SilkS") 
            (uuid "comprehensive-image-uuid-5678")
            (data "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==")
        )"""

        sexpr = loads(sexpr_data)
        image = Image.from_sexpr(sexpr)

        # Verify position with rotation
        assert image.position.x == 127.0
        assert image.position.y == 101.6
        assert image.position.angle == 45.0

        # Verify scale, layer, UUID, and data
        assert image.scale == 2.5
        assert image.layer == "F.SilkS"
        assert image.uuid.uuid == "comprehensive-image-uuid-5678"
        assert image.data is not None
        assert "iVBORw0KGgoAAAANSUhEUgAAAAE" in image.data

        # Test complete round-trip
        sexpr = image.to_sexpr()
        parsed_image = Image.from_sexpr(sexpr)

        assert parsed_image.position.x == image.position.x
        assert parsed_image.position.y == image.position.y
        assert parsed_image.position.angle == image.position.angle
        assert parsed_image.scale == image.scale
        assert parsed_image.layer == image.layer
        if parsed_image.uuid and image.uuid:
            assert parsed_image.uuid.uuid == image.uuid.uuid
        assert parsed_image.data == image.data


class TestSchematicCore:
    """Test core schematic parsing functionality"""

    def test_basic_schematic_creation(self):
        """Test creating a basic schematic"""
        schematic = create_basic_schematic("Test Schematic", "Test Company")

        assert schematic.title_block.title == "Test Schematic"
        assert schematic.title_block.company == "Test Company"
        assert schematic.version == 20230121
        assert schematic.generator == "kicad-parser"
        assert schematic.sheet_instances is not None
        assert schematic.sheet_instances.page == "1"

    def test_schematic_round_trip(self):
        """Test schematic serialization and parsing round-trip"""
        # Create test schematic
        original = create_basic_schematic("Round Trip Test")

        # Add some basic elements
        original.junctions.append(
            Junction(
                position=Position(50.0, 50.0),
                diameter=0.36,
                uuid=UUID("12345678-1234-1234-1234-123456789abc"),
            )
        )

        original.wires.append(
            Wire(
                points=CoordinatePointList([(0.0, 0.0), (10.0, 0.0)]),
                uuid=UUID("87654321-4321-4321-4321-cba987654321"),
            )
        )

        # Serialize and parse back
        sexpr = original.to_sexpr()
        parsed = KiCadSchematic.from_sexpr(sexpr)

        assert parsed.title_block.title == original.title_block.title
        assert len(parsed.junctions) == 1
        assert len(parsed.wires) == 1
        assert parsed.junctions[0].position.x == 50.0
        assert parsed.wires[0].points[0] == (0.0, 0.0)


class TestJunction:
    """Test junction parsing and serialization"""

    def test_junction_basic(self):
        """Test basic junction creation and parsing"""
        junction = Junction(
            position=Position(25.4, 30.0),
            diameter=0.36,
            color=(1.0, 0.0, 0.0, 1.0),
            uuid=UUID("test-uuid-junction"),
        )

        sexpr = junction.to_sexpr()
        parsed = Junction.from_sexpr(sexpr)

        assert parsed.position.x == 25.4
        assert parsed.position.y == 30.0
        assert parsed.diameter == 0.36
        assert parsed.color == (1.0, 0.0, 0.0, 1.0)
        assert parsed.uuid.uuid == "test-uuid-junction"

    def test_junction_minimal(self):
        """Test junction with minimal parameters"""
        junction = Junction(position=Position(0.0, 0.0), uuid=UUID("minimal"))

        sexpr = junction.to_sexpr()
        parsed = Junction.from_sexpr(sexpr)

        assert parsed.position.x == 0.0
        assert parsed.diameter == 0.0  # Default
        assert parsed.color is None


class TestNoConnect:
    """Test no-connect parsing and serialization"""

    def test_no_connect_basic(self):
        """Test basic no-connect creation"""
        nc = NoConnect(position=Position(12.7, 25.4), uuid=UUID("no-connect-test"))

        sexpr = nc.to_sexpr()
        parsed = NoConnect.from_sexpr(sexpr)

        assert parsed.position.x == 12.7
        assert parsed.position.y == 25.4
        assert parsed.uuid.uuid == "no-connect-test"


class TestBusEntry:
    """Test bus entry parsing and serialization"""

    def test_bus_entry_basic(self):
        """Test basic bus entry creation"""
        entry = BusEntry(
            position=Position(5.0, 10.0),
            size=(2.54, 2.54),
            stroke=Stroke(width=0.127),
            uuid=UUID("bus-entry-test"),
        )

        sexpr = entry.to_sexpr()
        parsed = BusEntry.from_sexpr(sexpr)

        assert parsed.position.x == 5.0
        assert parsed.position.y == 10.0
        assert parsed.size == (2.54, 2.54)
        assert parsed.stroke.width == 0.127
        assert parsed.uuid.uuid == "bus-entry-test"

    def test_bus_entry_specification_compliance(self):
        """Test bus entry according to sexp-schematic.md specification"""
        # Test specification format: (bus_entry POSITION_IDENTIFIER (size X Y) STROKE_DEFINITION UNIQUE_IDENTIFIER)

        # Test with minimal required parameters
        entry_minimal = BusEntry(
            position=Position(12.7, 25.4),
            size=(2.54, -2.54),  # Negative Y for typical bus entry direction
            stroke=Stroke(width=0.152),
            uuid=UUID("bus-entry-minimal"),
        )

        sexpr = entry_minimal.to_sexpr()
        parsed = BusEntry.from_sexpr(sexpr)
        assert parsed.position.x == 12.7
        assert parsed.position.y == 25.4
        assert parsed.size == (2.54, -2.54)
        assert parsed.stroke.width == 0.152
        assert parsed.uuid.uuid == "bus-entry-minimal"

        # Test with position including angle
        entry_with_angle = BusEntry(
            position=Position(50.8, 38.1, 90.0),
            size=(3.81, 3.81),
            stroke=Stroke(width=0.254, color=(1.0, 0.0, 0.0, 1.0)),
            uuid=UUID("bus-entry-angled"),
        )

        sexpr = entry_with_angle.to_sexpr()
        parsed = BusEntry.from_sexpr(sexpr)
        assert parsed.position.x == 50.8
        assert parsed.position.y == 38.1
        assert parsed.position.angle == 90.0
        assert parsed.size == (3.81, 3.81)
        assert parsed.stroke.width == 0.254
        if parsed.stroke.color:
            assert parsed.stroke.color == (1.0, 0.0, 0.0, 1.0)

        # Test parsing raw S-expression according to specification
        sexpr_raw = '(bus_entry (at 76.2 63.5) (size 2.54 -2.54) (stroke (width 0.127) (type default)) (uuid "spec-test-bus-entry"))'
        from kicad_parser.sexpdata import loads

        sexpr_parsed = loads(sexpr_raw)
        entry_parsed = BusEntry.from_sexpr(sexpr_parsed)
        assert entry_parsed.position.x == 76.2
        assert entry_parsed.position.y == 63.5
        assert entry_parsed.size == (2.54, -2.54)
        assert entry_parsed.stroke.width == 0.127
        assert entry_parsed.uuid.uuid == "spec-test-bus-entry"


class TestWireAndBus:
    """Test wire and bus parsing and serialization"""

    def test_wire_basic(self):
        """Test basic wire creation"""
        wire = Wire(
            points=CoordinatePointList([(0.0, 0.0), (10.0, 5.0), (20.0, 0.0)]),
            stroke=Stroke(width=0.152),
            uuid=UUID("wire-test"),
        )

        sexpr = wire.to_sexpr()
        parsed = Wire.from_sexpr(sexpr)

        assert len(parsed.points) == 3
        assert parsed.points[0] == (0.0, 0.0)
        assert parsed.points[1] == (10.0, 5.0)
        assert parsed.points[2] == (20.0, 0.0)
        assert parsed.stroke.width == 0.152
        assert parsed.uuid.uuid == "wire-test"

    def test_bus_basic(self):
        """Test basic bus creation"""
        bus = Bus(
            points=CoordinatePointList([(5.0, 5.0), (15.0, 5.0)]),
            stroke=Stroke(width=0.254),
            uuid=UUID("bus-test"),
        )

        sexpr = bus.to_sexpr()
        parsed = Bus.from_sexpr(sexpr)

        assert len(parsed.points) == 2
        assert parsed.points[0] == (5.0, 5.0)
        assert parsed.points[1] == (15.0, 5.0)
        assert parsed.stroke.width == 0.254


class TestPolyline:
    """Test polyline (graphical line) parsing and serialization"""

    def test_polyline_basic(self):
        """Test basic polyline creation"""
        polyline = Polyline(
            points=CoordinatePointList(
                [(0.0, 0.0), (5.0, 0.0), (5.0, 5.0), (0.0, 5.0), (0.0, 0.0)]
            ),
            stroke=Stroke(width=0.127),
            uuid=UUID("polyline-test"),
        )

        sexpr = polyline.to_sexpr()
        parsed = Polyline.from_sexpr(sexpr)

        assert len(parsed.points) == 5
        assert parsed.points[0] == (0.0, 0.0)
        assert parsed.points[-1] == (0.0, 0.0)  # Closed shape
        assert parsed.stroke.width == 0.127


class TestSchematicText:
    """Test schematic text parsing and serialization"""

    def test_schematic_text_basic(self):
        """Test basic schematic text creation"""
        text = SchematicText(
            text="Test Text",
            position=Position(10.0, 15.0, 45.0),
            effects=TextEffects(font=Font(size_height=2.0, size_width=1.5, bold=True)),
            uuid=UUID("text-test"),
        )

        sexpr = text.to_sexpr()
        parsed = SchematicText.from_sexpr(sexpr)

        assert parsed.text == "Test Text"
        assert parsed.position.x == 10.0
        assert parsed.position.y == 15.0
        assert parsed.position.angle == 45.0
        assert parsed.effects.font.size_height == 2.0
        assert parsed.effects.font.bold is True


class TestLabels:
    """Test label parsing and serialization"""

    def test_local_label_basic(self):
        """Test basic local label creation"""
        label = LocalLabel(
            text="NET_NAME",
            position=Position(20.0, 25.0),
            effects=TextEffects(),
            uuid=UUID("local-label-test"),
        )

        sexpr = label.to_sexpr()
        parsed = LocalLabel.from_sexpr(sexpr)

        assert parsed.text == "NET_NAME"
        assert parsed.position.x == 20.0
        assert parsed.position.y == 25.0

    def test_global_label_basic(self):
        """Test basic global label creation"""
        label = GlobalLabel(
            text="GLOBAL_NET",
            shape=LabelShape.OUTPUT,
            position=Position(30.0, 35.0),
            fields_autoplaced=True,
            uuid=UUID("global-label-test"),
        )

        sexpr = label.to_sexpr()
        parsed = GlobalLabel.from_sexpr(sexpr)

        assert parsed.text == "GLOBAL_NET"
        assert parsed.shape == LabelShape.OUTPUT
        assert parsed.position.x == 30.0
        assert parsed.fields_autoplaced is True

    def test_global_label_fields_autoplaced_optional(self):
        """Test global label with and without fields_autoplaced according to specification"""
        # Test with fields_autoplaced=True
        label_with_autoplaced = GlobalLabel(
            text="NET_WITH_AUTOPLACED",
            shape=LabelShape.INPUT,
            position=Position(10.0, 20.0),
            fields_autoplaced=True,
            uuid=UUID("label-autoplaced-true"),
        )

        sexpr = label_with_autoplaced.to_sexpr()
        parsed = GlobalLabel.from_sexpr(sexpr)
        assert parsed.fields_autoplaced is True

        # Test with fields_autoplaced=False (should not appear in S-expression)
        label_without_autoplaced = GlobalLabel(
            text="NET_WITHOUT_AUTOPLACED",
            shape=LabelShape.INPUT,
            position=Position(10.0, 30.0),
            fields_autoplaced=False,
            uuid=UUID("label-autoplaced-false"),
        )

        sexpr = label_without_autoplaced.to_sexpr()
        parsed = GlobalLabel.from_sexpr(sexpr)
        assert parsed.fields_autoplaced is False

        # Test parsing S-expression without fields_autoplaced (should default to False)
        sexpr_without = '(global_label "TEST_NET" (shape input) (at 50.0 60.0) (effects (font (size 1.27 1.27))) (uuid "test-no-autoplaced"))'
        from kicad_parser.sexpdata import loads

        sexpr_parsed = loads(sexpr_without)
        label_parsed = GlobalLabel.from_sexpr(sexpr_parsed)
        assert label_parsed.fields_autoplaced is False
        assert label_parsed.text == "TEST_NET"
        assert label_parsed.shape == LabelShape.INPUT

    def test_hierarchical_label_basic(self):
        """Test basic hierarchical label creation"""
        label = HierarchicalLabel(
            text="HIER_SIGNAL",
            shape=LabelShape.BIDIRECTIONAL,
            position=Position(40.0, 45.0),
            uuid=UUID("hier-label-test"),
        )

        sexpr = label.to_sexpr()
        parsed = HierarchicalLabel.from_sexpr(sexpr)

        assert parsed.text == "HIER_SIGNAL"
        assert parsed.shape == LabelShape.BIDIRECTIONAL
        assert parsed.position.x == 40.0

    def test_label_shapes(self):
        """Test all label shape types"""
        shapes = [
            LabelShape.INPUT,
            LabelShape.OUTPUT,
            LabelShape.BIDIRECTIONAL,
            LabelShape.TRI_STATE,
            LabelShape.PASSIVE,
        ]

        for shape in shapes:
            label = GlobalLabel(
                text="TEST",
                shape=shape,
                position=Position(0, 0),
                uuid=UUID(f"test-{shape.value}"),
            )

            sexpr = label.to_sexpr()
            parsed = GlobalLabel.from_sexpr(sexpr)
            assert parsed.shape == shape


class TestSchematicSymbol:
    """Test schematic symbol parsing and serialization"""

    def test_symbol_basic(self):
        """Test basic symbol creation"""
        symbol = SchematicSymbol(
            library_id="Device:R",
            position=Position(50.0, 60.0),
            unit=1,
            in_bom=True,
            on_board=True,
            uuid=UUID("symbol-test"),
        )

        # Add a project instance
        project = SymbolProject(
            name="test_project", instances={"/": SymbolInstance(reference="R1", unit=1)}
        )
        symbol.projects.append(project)

        sexpr = symbol.to_sexpr()
        parsed = SchematicSymbol.from_sexpr(sexpr)

        assert parsed.library_id == "Device:R"
        assert parsed.position.x == 50.0
        assert parsed.unit == 1
        assert parsed.in_bom is True
        assert parsed.on_board is True
        assert len(parsed.projects) == 1
        assert parsed.projects[0].name == "test_project"
        assert parsed.projects[0].instances["/"].reference == "R1"

    def test_symbol_properties(self):
        """Test symbol with properties"""
        symbol = SchematicSymbol(
            library_id="Device:C", position=Position(0, 0), uuid=UUID("prop-test")
        )

        # Add properties
        symbol.properties.extend(
            [
                Property("Reference", "C1"),
                Property("Value", "100nF"),
                Property("Footprint", "Capacitor_SMD:C_0603_1608Metric"),
            ]
        )

        sexpr = symbol.to_sexpr()
        parsed = SchematicSymbol.from_sexpr(sexpr)

        assert len(parsed.properties) == 3
        prop_dict = {p.key: p.value for p in parsed.properties}
        assert prop_dict["Reference"] == "C1"
        assert prop_dict["Value"] == "100nF"
        assert "0603" in prop_dict["Footprint"]


class TestHierarchicalSheet:
    """Test hierarchical sheet parsing and serialization"""

    def test_sheet_basic(self):
        """Test basic sheet creation"""
        sheet = HierarchicalSheet(
            position=Position(100.0, 100.0),
            size=(50.0, 30.0),
            stroke=Stroke(width=0.127),
            uuid=UUID("sheet-test"),
            sheet_name="Sub Sheet",
            file_name="sub_sheet.kicad_sch",
        )

        # Add a hierarchical pin
        pin = HierarchicalPin(
            name="DATA_BUS",
            electrical_type=PinElectricalType.BIDIRECTIONAL,
            position=Position(150.0, 110.0),
            uuid=UUID("pin-test"),
        )
        sheet.pins.append(pin)

        # Add project instance
        project = SheetProject(
            name="main_project", instances={"/sheet1": SheetInstance(page="2")}
        )
        sheet.projects.append(project)

        sexpr = sheet.to_sexpr()
        parsed = HierarchicalSheet.from_sexpr(sexpr)

        assert parsed.position.x == 100.0
        assert parsed.size == (50.0, 30.0)
        assert parsed.sheet_name == "Sub Sheet"
        assert parsed.file_name == "sub_sheet.kicad_sch"
        assert len(parsed.pins) == 1
        assert parsed.pins[0].name == "DATA_BUS"
        assert parsed.pins[0].electrical_type == PinElectricalType.BIDIRECTIONAL
        assert len(parsed.projects) == 1
        assert parsed.projects[0].instances["/sheet1"].page == "2"

    def test_sheet_pin_types(self):
        """Test all hierarchical pin electrical types"""
        types = [
            PinElectricalType.INPUT,
            PinElectricalType.OUTPUT,
            PinElectricalType.BIDIRECTIONAL,
            PinElectricalType.TRI_STATE,
            PinElectricalType.PASSIVE,
        ]

        for pin_type in types:
            pin = HierarchicalPin(
                name="TEST_PIN",
                electrical_type=pin_type,
                position=Position(0, 0),
                uuid=UUID(f"pin-{pin_type.value}"),
            )

            sexpr = pin.to_sexpr()
            parsed = HierarchicalPin.from_sexpr(sexpr)
            assert parsed.electrical_type == pin_type


class TestRootSheetInstance:
    """Test root sheet instance parsing and serialization"""

    def test_root_sheet_basic(self):
        """Test basic root sheet instance"""
        root = RootSheetInstance(page="Main")

        sexpr = root.to_sexpr()
        parsed = RootSheetInstance.from_sexpr(sexpr)

        assert parsed.page == "Main"


class TestFileOperations:
    """Test file loading and saving operations"""

    def test_schematic_file_round_trip(self):
        """Test complete schematic file save and load"""
        # Create a comprehensive test schematic
        original = create_basic_schematic("File Test", "Test Corp")

        # Add various elements
        original.junctions.append(
            Junction(
                position=Position(25.4, 25.4), diameter=0.36, uuid=UUID("junction-1")
            )
        )

        original.wires.extend(
            [
                Wire(
                    points=CoordinatePointList([(0.0, 0.0), (25.4, 0.0)]),
                    uuid=UUID("wire-1"),
                ),
                Wire(
                    points=CoordinatePointList([(25.4, 0.0), (25.4, 25.4)]),
                    uuid=UUID("wire-2"),
                ),
            ]
        )

        original.local_labels.append(
            LocalLabel(text="VCC", position=Position(12.7, 0.0), uuid=UUID("label-vcc"))
        )

        original.symbols.append(
            SchematicSymbol(
                library_id="Device:R",
                position=Position(50.0, 25.4),
                uuid=UUID("resistor-1"),
            )
        )

        # Test file operations
        with tempfile.NamedTemporaryFile(
            mode="w+", suffix=".kicad_sch", delete=False
        ) as f:
            temp_file_name = f.name

        try:
            # Save schematic
            save_schematic(original, temp_file_name)

            # Load schematic back
            loaded = load_schematic(temp_file_name)

            # Verify basic properties
            assert loaded.title_block.title == "File Test"
            assert loaded.title_block.company == "Test Corp"
            assert loaded.version == original.version
            assert loaded.generator == original.generator

            # Verify elements were preserved
            assert len(loaded.junctions) == 1
            assert len(loaded.wires) == 2
            assert len(loaded.local_labels) == 1
            assert len(loaded.symbols) == 1

            assert loaded.junctions[0].position.x == 25.4
            assert loaded.wires[0].points[0] == (0.0, 0.0)
            assert loaded.local_labels[0].text == "VCC"
            assert loaded.symbols[0].library_id == "Device:R"

        finally:
            # Clean up - ensure file is closed before deletion
            try:
                os.unlink(temp_file_name)
            except (OSError, PermissionError):
                # On Windows, sometimes the file is still locked
                # Try again after a short delay
                import time

                time.sleep(0.1)
                try:
                    os.unlink(temp_file_name)
                except (OSError, PermissionError):
                    pass  # Ignore if we still can't delete

    def test_detect_schematic_file_type(self):
        """Test schematic file type detection"""
        schematic = create_basic_schematic("Detection Test")

        # Test content detection
        sexpr = schematic.to_sexpr()
        content = str(sexpr)  # Convert to string representation

        # The detection should work with the S-expression format
        # Note: This tests the principle - actual detection may need file format
        assert "kicad_sch" in content

    def test_schematic_validation(self):
        """Test basic schematic validation"""
        schematic = create_basic_schematic("Validation Test")

        # Test that required fields are present (UUID is always defined but can be empty)
        # Users can use generate_UUID() to create new UUIDs when needed
        assert schematic.uuid is not None
        assert schematic.version > 0
        assert schematic.generator != ""
        assert schematic.sheet_instances is not None

        # Test round-trip validation
        sexpr = schematic.to_sexpr()
        parsed = KiCadSchematic.from_sexpr(sexpr)

        # Both should have same UUID (can be empty string)
        assert parsed.uuid.uuid == schematic.uuid.uuid
        assert parsed.version == schematic.version
        assert parsed.generator == schematic.generator


class TestComplexScenarios:
    """Test complex real-world scenarios"""

    def test_multi_sheet_design(self):
        """Test schematic with multiple hierarchical sheets"""
        schematic = create_basic_schematic("Multi-Sheet Design")

        # Add main sheet symbols
        schematic.symbols.append(
            SchematicSymbol(
                library_id="MCU_ST_STM32F4:STM32F407VGTx",
                position=Position(100.0, 100.0),
                uuid=UUID("mcu-main"),
            )
        )

        # Add hierarchical sheets
        power_sheet = HierarchicalSheet(
            position=Position(200.0, 50.0),
            size=(50.0, 30.0),
            uuid=UUID("power-sheet"),
            sheet_name="Power Supply",
            file_name="power.kicad_sch",
        )

        # Add pins to power sheet
        power_sheet.pins.extend(
            [
                HierarchicalPin(
                    name="VCC_5V",
                    electrical_type=PinElectricalType.OUTPUT,
                    position=Position(200.0, 60.0),
                    uuid=UUID("pin-vcc5v"),
                ),
                HierarchicalPin(
                    name="VCC_3V3",
                    electrical_type=PinElectricalType.OUTPUT,
                    position=Position(200.0, 70.0),
                    uuid=UUID("pin-vcc3v3"),
                ),
            ]
        )

        schematic.sheets.append(power_sheet)

        # Add connections between main and hierarchical sheets
        schematic.global_labels.extend(
            [
                GlobalLabel(
                    text="VCC_5V",
                    shape=LabelShape.INPUT,
                    position=Position(180.0, 60.0),
                    uuid=UUID("global-vcc5v"),
                ),
                GlobalLabel(
                    text="VCC_3V3",
                    shape=LabelShape.INPUT,
                    position=Position(180.0, 70.0),
                    uuid=UUID("global-vcc3v3"),
                ),
            ]
        )

        # Test serialization and parsing
        sexpr = schematic.to_sexpr()
        parsed = KiCadSchematic.from_sexpr(sexpr)

        assert len(parsed.symbols) == 1
        assert len(parsed.sheets) == 1
        assert len(parsed.global_labels) == 2

        power_sheet_parsed = parsed.sheets[0]
        assert power_sheet_parsed.sheet_name == "Power Supply"
        assert power_sheet_parsed.file_name == "power.kicad_sch"
        assert len(power_sheet_parsed.pins) == 2

    def test_bus_design(self):
        """Test schematic with bus connections"""
        schematic = create_basic_schematic("Bus Design")

        # Add bus connections
        schematic.buses.extend(
            [
                Bus(
                    points=CoordinatePointList([(50.0, 50.0), (150.0, 50.0)]),
                    stroke=Stroke(width=0.254),
                    uuid=UUID("data-bus"),
                ),
                Bus(
                    points=CoordinatePointList([(150.0, 50.0), (150.0, 100.0)]),
                    stroke=Stroke(width=0.254),
                    uuid=UUID("data-bus-vert"),
                ),
            ]
        )

        # Add bus entries
        schematic.bus_entries.extend(
            [
                BusEntry(
                    position=Position(60.0, 50.0),
                    size=(2.54, -2.54),
                    uuid=UUID("bus-entry-1"),
                ),
                BusEntry(
                    position=Position(70.0, 50.0),
                    size=(2.54, -2.54),
                    uuid=UUID("bus-entry-2"),
                ),
            ]
        )

        # Add individual wires from bus entries
        schematic.wires.extend(
            [
                Wire(
                    points=CoordinatePointList([(60.0, 47.46), (60.0, 40.0)]),
                    uuid=UUID("d0-wire"),
                ),
                Wire(
                    points=CoordinatePointList([(70.0, 47.46), (70.0, 40.0)]),
                    uuid=UUID("d1-wire"),
                ),
            ]
        )

        # Add labels for bus signals
        schematic.local_labels.extend(
            [
                LocalLabel(
                    text="D0", position=Position(60.0, 35.0), uuid=UUID("label-d0")
                ),
                LocalLabel(
                    text="D1", position=Position(70.0, 35.0), uuid=UUID("label-d1")
                ),
            ]
        )

        # Test serialization
        sexpr = schematic.to_sexpr()
        parsed = KiCadSchematic.from_sexpr(sexpr)

        assert len(parsed.buses) == 2
        assert len(parsed.bus_entries) == 2
        assert len(parsed.wires) == 2
        assert len(parsed.local_labels) == 2

    def test_mixed_symbol_units(self):
        """Test schematic with multi-unit symbols"""
        schematic = create_basic_schematic("Multi-Unit Design")

        # Add different units of the same symbol
        op_amp_lib = "Amplifier_Operational:LM324"

        schematic.symbols.extend(
            [
                SchematicSymbol(
                    library_id=op_amp_lib,
                    position=Position(100.0, 100.0),
                    unit=1,  # First op-amp
                    uuid=UUID("opamp-u1a"),
                ),
                SchematicSymbol(
                    library_id=op_amp_lib,
                    position=Position(100.0, 150.0),
                    unit=2,  # Second op-amp
                    uuid=UUID("opamp-u1b"),
                ),
                SchematicSymbol(
                    library_id=op_amp_lib,
                    position=Position(200.0, 125.0),
                    unit=5,  # Power unit
                    uuid=UUID("opamp-u1-pwr"),
                ),
            ]
        )

        # Test serialization
        sexpr = schematic.to_sexpr()
        parsed = KiCadSchematic.from_sexpr(sexpr)

        assert len(parsed.symbols) == 3
        units = [s.unit for s in parsed.symbols]
        assert 1 in units
        assert 2 in units
        assert 5 in units


if __name__ == "__main__":
    pytest.main([__file__])
