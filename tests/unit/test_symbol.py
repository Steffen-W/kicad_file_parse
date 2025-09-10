"""
Unit tests for kicad_symbol module

Progress:
✅ SymbolArc class (minimal + comprehensive)
✅ SymbolCircle class (minimal + comprehensive)
✅ SymbolBezier class (minimal + comprehensive)
✅ SymbolPolyline class (minimal + comprehensive)
✅ SymbolRectangle class (minimal + comprehensive)
✅ SymbolText class (minimal + comprehensive)
✅ SymbolPin class (minimal + comprehensive)
✅ KiCadSymbol class (minimal + comprehensive)
✅ KiCadSymbolLibrary class (minimal + comprehensive)
"""

import pytest

from kicad_parser import (
    KiCadSymbol,
    KiCadSymbolLibrary,
    PinElectricalType,
    PinGraphicStyle,
    Position,
    SymbolPin,
    SymbolProperty,
    create_basic_symbol,
)
from kicad_parser.kicad_common import (
    CoordinatePoint,
    CoordinatePointList,
    Fill,
    FillType,
    Font,
    Stroke,
    StrokeType,
    TextEffects,
)
from kicad_parser.kicad_symbol import (
    SymbolArc,
    SymbolBezier,
    SymbolCircle,
    SymbolPolyline,
    SymbolRectangle,
    SymbolText,
)
from kicad_parser.sexpdata import Symbol


class TestKiCadSymbol:
    """Test KiCadSymbol class"""

    def test_symbol_creation(self, sample_symbol):
        """Test creating a symbol"""
        assert sample_symbol.name == "TestSymbol"
        assert (
            len(sample_symbol.properties) >= 4
        )  # Reference, Value, Footprint, Datasheet

    def test_get_property(self, sample_symbol):
        """Test getting property by key"""
        ref_prop = sample_symbol.get_property("Reference")
        assert ref_prop is not None
        assert ref_prop.key == "Reference"
        assert ref_prop.value == "U"

    def test_set_property_existing(self, sample_symbol):
        """Test setting existing property"""
        sample_symbol.set_property("Reference", "IC")
        ref_prop = sample_symbol.get_property("Reference")
        assert ref_prop.value == "IC"

    def test_set_property_new(self, sample_symbol):
        """Test setting new property"""
        original_count = len(sample_symbol.properties)
        sample_symbol.set_property("Description", "Test component")

        desc_prop = sample_symbol.get_property("Description")
        assert desc_prop is not None
        assert desc_prop.value == "Test component"
        assert len(sample_symbol.properties) == original_count + 1

    def test_remove_property(self, sample_symbol):
        """Test removing property"""
        # Add a property to remove
        sample_symbol.set_property("TestProp", "TestValue")
        original_count = len(sample_symbol.properties)

        # Remove it
        result = sample_symbol.remove_property("TestProp")
        assert result is True
        assert len(sample_symbol.properties) == original_count - 1
        assert sample_symbol.get_property("TestProp") is None

    def test_remove_nonexistent_property(self, sample_symbol):
        """Test removing non-existent property"""
        original_count = len(sample_symbol.properties)
        result = sample_symbol.remove_property("NonExistent")
        assert result is False
        assert len(sample_symbol.properties) == original_count


class TestSymbolProperty:
    """Test SymbolProperty class"""

    def test_property_creation(self):
        """Test creating a symbol property"""
        prop = SymbolProperty(
            key="Reference", value="U1", id=0, position=Position(0, 2.54)
        )
        assert prop.key == "Reference"
        assert prop.value == "U1"
        assert prop.id == 0
        assert prop.position.x == 0
        assert prop.position.y == 2.54


class TestSymbolPin:
    """Test SymbolPin class"""

    def test_pin_creation(self):
        """Test creating a symbol pin"""
        pin = SymbolPin(
            electrical_type=PinElectricalType.INPUT,
            graphic_style=PinGraphicStyle.LINE,
            position=Position(-5.08, 0, 0),
            length=2.54,
            name="DATA",
            number="1",
        )
        assert pin.electrical_type == PinElectricalType.INPUT
        assert pin.graphic_style == PinGraphicStyle.LINE
        assert pin.position.x == -5.08
        assert pin.length == 2.54
        assert pin.name == "DATA"
        assert pin.number == "1"

    def test_pin_electrical_types(self):
        """Test pin electrical type enum values"""
        assert PinElectricalType.INPUT.value == "input"
        assert PinElectricalType.OUTPUT.value == "output"
        assert PinElectricalType.BIDIRECTIONAL.value == "bidirectional"
        assert PinElectricalType.PASSIVE.value == "passive"
        assert PinElectricalType.POWER_IN.value == "power_in"

    def test_pin_graphic_styles(self):
        """Test pin graphic style enum values"""
        assert PinGraphicStyle.LINE.value == "line"
        assert PinGraphicStyle.INVERTED.value == "inverted"
        assert PinGraphicStyle.CLOCK.value == "clock"


class TestKiCadSymbolLibrary:
    """Test KiCadSymbolLibrary class"""

    def test_library_creation(self, sample_library):
        """Test creating a symbol library"""
        assert sample_library.version == 20211014
        assert sample_library.generator == "pytest"
        assert len(sample_library.symbols) == 3

    def test_get_symbol(self, sample_library):
        """Test getting symbol by name"""
        symbol = sample_library.get_symbol("Symbol_0")
        assert symbol is not None
        assert symbol.name == "Symbol_0"

    def test_get_nonexistent_symbol(self, sample_library):
        """Test getting non-existent symbol"""
        symbol = sample_library.get_symbol("NonExistent")
        assert symbol is None

    def test_add_symbol(self, sample_library):
        """Test adding symbol to library"""
        new_symbol = create_basic_symbol("NewSymbol", "U", "New")
        original_count = len(sample_library.symbols)

        sample_library.add_symbol(new_symbol)
        assert len(sample_library.symbols) == original_count + 1

        retrieved = sample_library.get_symbol("NewSymbol")
        assert retrieved is not None
        assert retrieved.name == "NewSymbol"

    def test_add_duplicate_symbol(self, sample_library):
        """Test adding symbol with duplicate name (should replace)"""
        original_count = len(sample_library.symbols)

        # Add symbol with existing name
        duplicate = create_basic_symbol("Symbol_0", "IC", "Duplicate")
        sample_library.add_symbol(duplicate)

        # Count should be same (replaced, not added)
        assert len(sample_library.symbols) == original_count

        # But the symbol should be updated
        retrieved = sample_library.get_symbol("Symbol_0")
        assert retrieved.get_property("Reference").value == "IC"

    def test_remove_symbol(self, sample_library):
        """Test removing symbol from library"""
        original_count = len(sample_library.symbols)
        result = sample_library.remove_symbol("Symbol_1")

        assert result is True
        assert len(sample_library.symbols) == original_count - 1
        assert sample_library.get_symbol("Symbol_1") is None

    def test_remove_nonexistent_symbol(self, sample_library):
        """Test removing non-existent symbol"""
        original_count = len(sample_library.symbols)
        result = sample_library.remove_symbol("NonExistent")

        assert result is False
        assert len(sample_library.symbols) == original_count


class TestCreateBasicSymbol:
    """Test create_basic_symbol utility function"""

    def test_create_basic_symbol(self):
        """Test creating a basic symbol"""
        symbol = create_basic_symbol("TestIC", "U", "TestValue")

        assert symbol.name == "TestIC"
        assert len(symbol.properties) >= 4

        # Check required properties
        ref_prop = symbol.get_property("Reference")
        assert ref_prop.value == "U"

        val_prop = symbol.get_property("Value")
        assert val_prop.value == "TestValue"

        footprint_prop = symbol.get_property("Footprint")
        assert footprint_prop.value == ""

        datasheet_prop = symbol.get_property("Datasheet")
        assert datasheet_prop.value == ""

    def test_create_basic_symbol_defaults(self):
        """Test creating basic symbol with default value"""
        symbol = create_basic_symbol("TestIC", "U")

        val_prop = symbol.get_property("Value")
        assert val_prop.value == "TestIC"  # Should default to name


class TestSymbolArcComprehensive:
    """Comprehensive tests for SymbolArc class based on specification"""

    def test_symbol_arc_minimal(self):
        """Test minimal arc with start, mid, end points"""
        # Based on spec: (arc (start X Y) (mid X Y) (end X Y) STROKE_DEFINITION FILL_DEFINITION)
        sexpr = [
            Symbol("arc"),
            [Symbol("start"), 0, 0],
            [Symbol("mid"), 2.5, 2.5],
            [Symbol("end"), 5.0, 0],
            [Symbol("stroke"), [Symbol("width"), 0.254]],
        ]
        arc = SymbolArc.from_sexpr(sexpr)

        assert arc.start.x == 0
        assert arc.start.y == 0
        assert arc.mid.x == 2.5
        assert arc.mid.y == 2.5
        assert arc.end.x == 5.0
        assert arc.end.y == 0

        # Test round-trip serialization
        result_sexpr = arc.to_sexpr()
        assert result_sexpr[0] == Symbol("arc")

    def test_symbol_arc_comprehensive(self):
        """Test comprehensive arc with stroke and fill"""
        # Based on spec: (arc (start X Y) (mid X Y) (end X Y) STROKE_DEFINITION FILL_DEFINITION)
        sexpr = [
            Symbol("arc"),
            [Symbol("start"), -2.54, 1.27],
            [Symbol("mid"), 0, 3.81],
            [Symbol("end"), 2.54, 1.27],
            [
                Symbol("stroke"),
                [Symbol("width"), 0.508],
                [Symbol("type"), Symbol("dash")],
            ],
            [Symbol("fill"), [Symbol("type"), Symbol("background")]],
        ]
        arc = SymbolArc.from_sexpr(sexpr)

        assert arc.start.x == -2.54
        assert arc.start.y == 1.27
        assert arc.mid.x == 0
        assert arc.mid.y == 3.81
        assert arc.end.x == 2.54
        assert arc.end.y == 1.27
        assert arc.stroke.width == 0.508
        assert arc.stroke.type == StrokeType.DASH
        assert arc.fill.type == FillType.BACKGROUND


class TestSymbolCircleComprehensive:
    """Comprehensive tests for SymbolCircle class based on specification"""

    def test_symbol_circle_minimal(self):
        """Test minimal circle with center and radius"""
        # Based on spec: (circle (center X Y) (radius RADIUS) STROKE_DEFINITION FILL_DEFINITION)
        sexpr = [
            Symbol("circle"),
            [Symbol("center"), 0, 0],
            [Symbol("radius"), 1.27],
            [Symbol("stroke"), [Symbol("width"), 0.254]],
        ]
        circle = SymbolCircle.from_sexpr(sexpr)

        assert circle.center.x == 0
        assert circle.center.y == 0
        assert circle.radius == 1.27

        # Test round-trip serialization
        result_sexpr = circle.to_sexpr()
        assert result_sexpr[0] == Symbol("circle")

    def test_symbol_circle_comprehensive(self):
        """Test comprehensive circle with stroke and fill"""
        # Test with different stroke types and fill
        sexpr = [
            Symbol("circle"),
            [Symbol("center"), 5.08, -2.54],
            [Symbol("radius"), 3.175],
            [
                Symbol("stroke"),
                [Symbol("width"), 0.762],
                [Symbol("type"), Symbol("dot")],
            ],
            [Symbol("fill"), [Symbol("type"), Symbol("outline")]],
        ]
        circle = SymbolCircle.from_sexpr(sexpr)

        assert circle.center.x == 5.08
        assert circle.center.y == -2.54
        assert circle.radius == 3.175
        assert circle.stroke.width == 0.762
        assert circle.stroke.type == StrokeType.DOT
        assert circle.fill.type == FillType.OUTLINE


class TestSymbolBezierComprehensive:
    """Comprehensive tests for SymbolBezier class based on specification"""

    def test_symbol_bezier_minimal(self):
        """Test minimal bezier with control points"""
        # Based on spec: (bezier COORDINATE_POINT_LIST STROKE_DEFINITION FILL_DEFINITION)
        sexpr = [
            Symbol("bezier"),
            [
                Symbol("pts"),
                [Symbol("xy"), 0, 0],
                [Symbol("xy"), 1.27, 2.54],
                [Symbol("xy"), 3.81, 2.54],
                [Symbol("xy"), 5.08, 0],
            ],
            [Symbol("stroke"), [Symbol("width"), 0.254]],
        ]
        bezier = SymbolBezier.from_sexpr(sexpr)

        assert len(bezier.points.points) == 4
        assert bezier.points.points[0].x == 0
        assert bezier.points.points[0].y == 0
        assert bezier.points.points[3].x == 5.08
        assert bezier.points.points[3].y == 0

        # Test round-trip serialization
        result_sexpr = bezier.to_sexpr()
        assert result_sexpr[0] == Symbol("bezier")

    def test_symbol_bezier_comprehensive(self):
        """Test comprehensive bezier curve with complex stroke and fill"""
        sexpr = [
            Symbol("bezier"),
            [
                Symbol("pts"),
                [Symbol("xy"), -5.08, -2.54],
                [Symbol("xy"), -1.27, 5.08],
                [Symbol("xy"), 1.27, 5.08],
                [Symbol("xy"), 5.08, -2.54],
            ],
            [
                Symbol("stroke"),
                [Symbol("width"), 0.508],
                [Symbol("type"), Symbol("dash_dot")],
            ],
            [Symbol("fill"), [Symbol("type"), Symbol("background")]],
        ]
        bezier = SymbolBezier.from_sexpr(sexpr)

        assert len(bezier.points.points) == 4
        assert bezier.stroke.width == 0.508
        assert bezier.stroke.type == StrokeType.DASH_DOT
        assert bezier.fill.type == FillType.BACKGROUND


class TestSymbolPolylineComprehensive:
    """Comprehensive tests for SymbolPolyline class based on specification"""

    def test_symbol_polyline_minimal(self):
        """Test minimal polyline with points list"""
        # Based on spec: (polyline COORDINATE_POINT_LIST STROKE_DEFINITION FILL_DEFINITION)
        sexpr = [
            Symbol("polyline"),
            [
                Symbol("pts"),
                [Symbol("xy"), 0, 0],
                [Symbol("xy"), 2.54, 0],
                [Symbol("xy"), 2.54, 2.54],
            ],
            [Symbol("stroke"), [Symbol("width"), 0.254]],
        ]
        polyline = SymbolPolyline.from_sexpr(sexpr)

        assert len(polyline.points.points) == 3
        assert polyline.points.points[0].x == 0
        assert polyline.points.points[1].x == 2.54
        assert polyline.points.points[2].y == 2.54

        # Test round-trip serialization
        result_sexpr = polyline.to_sexpr()
        assert result_sexpr[0] == Symbol("polyline")

    def test_symbol_polyline_comprehensive(self):
        """Test comprehensive polyline with multiple points and styling"""
        sexpr = [
            Symbol("polyline"),
            [
                Symbol("pts"),
                [Symbol("xy"), -3.81, -1.27],
                [Symbol("xy"), 0, 3.81],
                [Symbol("xy"), 3.81, -1.27],
                [Symbol("xy"), 0, -3.81],
                [Symbol("xy"), -3.81, -1.27],
            ],  # Closed shape
            [
                Symbol("stroke"),
                [Symbol("width"), 0.762],
                [Symbol("type"), Symbol("solid")],
            ],
            [Symbol("fill"), [Symbol("type"), Symbol("outline")]],
        ]
        polyline = SymbolPolyline.from_sexpr(sexpr)

        assert len(polyline.points.points) == 5  # Including closing point
        assert polyline.stroke.width == 0.762
        assert polyline.stroke.type == StrokeType.SOLID
        assert polyline.fill.type == FillType.OUTLINE


class TestSymbolRectangleComprehensive:
    """Comprehensive tests for SymbolRectangle class based on specification"""

    def test_symbol_rectangle_minimal(self):
        """Test minimal rectangle with start/end points"""
        # Based on spec: (rectangle (start X Y) (end X Y) STROKE_DEFINITION FILL_DEFINITION)
        sexpr = [
            Symbol("rectangle"),
            [Symbol("start"), -1.27, -1.27],
            [Symbol("end"), 1.27, 1.27],
            [Symbol("stroke"), [Symbol("width"), 0.254]],
        ]
        rectangle = SymbolRectangle.from_sexpr(sexpr)

        assert rectangle.start.x == -1.27
        assert rectangle.start.y == -1.27
        assert rectangle.end.x == 1.27
        assert rectangle.end.y == 1.27

        # Test round-trip serialization
        result_sexpr = rectangle.to_sexpr()
        assert result_sexpr[0] == Symbol("rectangle")

    def test_symbol_rectangle_comprehensive(self):
        """Test comprehensive rectangle with fill background"""
        sexpr = [
            Symbol("rectangle"),
            [Symbol("start"), -6.35, -3.175],
            [Symbol("end"), 6.35, 3.175],
            [
                Symbol("stroke"),
                [Symbol("width"), 0.508],
                [Symbol("type"), Symbol("solid")],
            ],
            [Symbol("fill"), [Symbol("type"), Symbol("background")]],
        ]
        rectangle = SymbolRectangle.from_sexpr(sexpr)

        assert rectangle.start.x == -6.35
        assert rectangle.start.y == -3.175
        assert rectangle.end.x == 6.35
        assert rectangle.end.y == 3.175
        assert rectangle.stroke.width == 0.508
        assert rectangle.fill.type == FillType.BACKGROUND


class TestSymbolTextComprehensive:
    """Comprehensive tests for SymbolText class based on specification"""

    def test_symbol_text_minimal(self):
        """Test minimal text with text and position"""
        # Based on spec: (text "TEXT" POSITION_IDENTIFIER (effects TEXT_EFFECTS))
        sexpr = [
            Symbol("text"),
            "Label",
            [Symbol("at"), 0, 0, 0],
            [Symbol("effects"), [Symbol("font"), [Symbol("size"), 1.27, 1.27]]],
        ]
        text = SymbolText.from_sexpr(sexpr)

        assert text.text == "Label"
        assert text.position.x == 0
        assert text.position.y == 0
        assert text.position.angle == 0

        # Test round-trip serialization
        result_sexpr = text.to_sexpr()
        assert result_sexpr[0] == Symbol("text")
        assert result_sexpr[1] == "Label"

    def test_symbol_text_comprehensive(self):
        """Test comprehensive text with effects"""
        sexpr = [
            Symbol("text"),
            "IC1",
            [Symbol("at"), 2.54, -5.08, 90],
            [
                Symbol("effects"),
                [
                    Symbol("font"),
                    [Symbol("size"), 2.0, 1.5],
                    [Symbol("thickness"), 0.3],
                    Symbol("bold"),
                ],
                [Symbol("justify"), Symbol("left"), Symbol("bottom")],
                Symbol("hide"),
            ],
        ]
        text = SymbolText.from_sexpr(sexpr)

        assert text.text == "IC1"
        assert text.position.x == 2.54
        assert text.position.y == -5.08
        assert text.position.angle == 90
        assert text.effects.font.size_height == 2.0
        assert text.effects.font.size_width == 1.5
        assert text.effects.font.thickness == 0.3
        assert text.effects.font.bold is True
        assert text.effects.hide is True


class TestSymbolPinComprehensive:
    """Comprehensive tests for SymbolPin class based on specification"""

    def test_symbol_pin_minimal(self):
        """Test minimal pin with electrical type and position"""
        # Based on spec: (pin PIN_ELECTRICAL_TYPE PIN_GRAPHIC_STYLE POSITION_IDENTIFIER (length LENGTH) (name "NAME" TEXT_EFFECTS) (number "NUMBER" TEXT_EFFECTS))
        sexpr = [
            Symbol("pin"),
            Symbol("input"),
            Symbol("line"),
            [Symbol("at"), -7.62, 0, 0],
            [Symbol("length"), 2.54],
            [
                Symbol("name"),
                "IN",
                [Symbol("effects"), [Symbol("font"), [Symbol("size"), 1.27, 1.27]]],
            ],
            [
                Symbol("number"),
                "1",
                [Symbol("effects"), [Symbol("font"), [Symbol("size"), 1.27, 1.27]]],
            ],
        ]
        pin = SymbolPin.from_sexpr(sexpr)

        assert pin.electrical_type == PinElectricalType.INPUT
        assert pin.graphic_style == PinGraphicStyle.LINE
        assert pin.position.x == -7.62
        assert pin.position.y == 0
        assert pin.length == 2.54
        assert pin.name == "IN"
        assert pin.number == "1"

    def test_symbol_pin_comprehensive(self):
        """Test comprehensive pin with all attributes"""
        # Test all electrical types and graphic styles from specification
        electrical_types_test = [
            (Symbol("input"), PinElectricalType.INPUT),
            (Symbol("output"), PinElectricalType.OUTPUT),
            (Symbol("bidirectional"), PinElectricalType.BIDIRECTIONAL),
            (Symbol("tri_state"), PinElectricalType.TRI_STATE),
            (Symbol("passive"), PinElectricalType.PASSIVE),
            (Symbol("power_in"), PinElectricalType.POWER_IN),
            (Symbol("power_out"), PinElectricalType.POWER_OUT),
        ]

        for symbol_type, expected_type in electrical_types_test:
            sexpr = [
                Symbol("pin"),
                symbol_type,
                Symbol("inverted"),
                [Symbol("at"), 7.62, 2.54, 180],
                [Symbol("length"), 5.08],
                [
                    Symbol("name"),
                    "DATA",
                    [
                        Symbol("effects"),
                        [Symbol("font"), [Symbol("size"), 1.0, 1.0]],
                        Symbol("hide"),
                    ],
                ],
                [
                    Symbol("number"),
                    "A1",
                    [Symbol("effects"), [Symbol("font"), [Symbol("size"), 0.8, 0.8]]],
                ],
            ]
            pin = SymbolPin.from_sexpr(sexpr)

            assert pin.electrical_type == expected_type
            assert pin.graphic_style == PinGraphicStyle.INVERTED
            assert pin.position.angle == 180
            assert pin.length == 5.08
            assert pin.name == "DATA"
            assert pin.number == "A1"


class TestKiCadSymbolComprehensive:
    """Comprehensive tests for KiCadSymbol class based on specification"""

    def test_kicad_symbol_minimal(self):
        """Test minimal symbol with name only"""
        # Based on spec: (symbol "LIBRARY_ID" [(extends "LIBRARY_ID")] [(pin_numbers hide)] [(pin_names [(offset OFFSET)] hide)] (in_bom yes | no) (on_board yes | no) ...)
        symbol = KiCadSymbol(name="TestSymbol")

        assert symbol.name == "TestSymbol"
        assert symbol.in_bom is None  # Default - optional token
        assert symbol.on_board is None  # Default - optional token
        assert len(symbol.properties) >= 0

        # Test round-trip serialization
        result_sexpr = symbol.to_sexpr()
        assert result_sexpr[0] == Symbol("symbol")

    def test_kicad_symbol_comprehensive(self):
        """Test comprehensive symbol with all features"""
        symbol = KiCadSymbol(
            name="ComplexSymbol",
            extends="BaseSymbol",
            pin_numbers_hide=True,
            pin_names_hide=True,
            pin_names_offset=1.016,
            in_bom=True,
            on_board=True,
        )

        # Add comprehensive properties
        symbol.set_property("Reference", "U")
        symbol.set_property("Value", "ComplexIC")
        symbol.set_property("Footprint", "Package_QFP:LQFP-64")
        symbol.set_property("Datasheet", "https://example.com/datasheet.pdf")

        # Add graphics elements
        symbol.rectangles.append(
            SymbolRectangle(
                start=CoordinatePoint(-5, -3),
                end=CoordinatePoint(5, 3),
                stroke=Stroke(width=0.254),
                fill=Fill(type=FillType.BACKGROUND),
            )
        )

        # Add pins
        symbol.pins.append(
            SymbolPin(
                electrical_type=PinElectricalType.INPUT,
                graphic_style=PinGraphicStyle.LINE,
                position=Position(-7.62, 0),
                length=2.54,
                name="CLK",
                number="1",
            )
        )

        assert symbol.name == "ComplexSymbol"
        assert symbol.extends == "BaseSymbol"
        assert symbol.pin_numbers_hide is True
        assert symbol.pin_names_hide is True
        assert symbol.pin_names_offset == 1.016
        assert len(symbol.properties) == 4
        assert len(symbol.rectangles) == 1
        assert len(symbol.pins) == 1


class TestKiCadSymbolLibraryComprehensive:
    """Comprehensive tests for KiCadSymbolLibrary class based on specification"""

    def test_kicad_symbol_library_minimal(self):
        """Test minimal symbol library with version and generator"""
        # Based on spec: (kicad_symbol_lib (version VERSION) (generator GENERATOR) ...)
        library = KiCadSymbolLibrary(version=20211014, generator="pytest")

        assert library.version == 20211014
        assert library.generator == "pytest"
        assert len(library.symbols) == 0

        # Test round-trip serialization
        result_sexpr = library.to_sexpr()
        assert result_sexpr[0] == Symbol("kicad_symbol_lib")

    def test_kicad_symbol_library_comprehensive(self):
        """Test comprehensive symbol library with multiple symbols"""
        library = KiCadSymbolLibrary(version=20220914, generator="comprehensive_test")

        # Add multiple symbols with different features
        # Simple symbol
        simple_symbol = KiCadSymbol(name="Resistor")
        simple_symbol.set_property("Reference", "R")
        simple_symbol.set_property("Value", "1k")
        library.add_symbol(simple_symbol)

        # Complex symbol with graphics
        complex_symbol = KiCadSymbol(
            name="OpAmp", pin_names_offset=0.508, pin_numbers_hide=False
        )
        complex_symbol.set_property("Reference", "U")
        complex_symbol.set_property("Value", "LM358")

        # Add triangle graphics for op-amp
        complex_symbol.polylines.append(
            SymbolPolyline(
                points=CoordinatePointList(
                    [
                        CoordinatePoint(-5, -3),
                        CoordinatePoint(5, 0),
                        CoordinatePoint(-5, 3),
                        CoordinatePoint(-5, -3),
                    ]
                ),
                stroke=Stroke(width=0.254),
                fill=Fill(type=FillType.BACKGROUND),
            )
        )

        # Add pins
        complex_symbol.pins.extend(
            [
                SymbolPin(
                    PinElectricalType.INPUT,
                    PinGraphicStyle.LINE,
                    Position(-7.62, 2.54),
                    2.54,
                    "V+",
                    "1",
                ),
                SymbolPin(
                    PinElectricalType.INPUT,
                    PinGraphicStyle.LINE,
                    Position(-7.62, -2.54),
                    2.54,
                    "V-",
                    "2",
                ),
                SymbolPin(
                    PinElectricalType.OUTPUT,
                    PinGraphicStyle.LINE,
                    Position(7.62, 0),
                    2.54,
                    "OUT",
                    "3",
                ),
            ]
        )

        library.add_symbol(complex_symbol)

        # Capacitor with different graphics
        cap_symbol = KiCadSymbol(name="Capacitor")
        cap_symbol.set_property("Reference", "C")
        cap_symbol.set_property("Value", "100nF")

        # Add capacitor graphics (two parallel lines)
        cap_symbol.polylines.extend(
            [
                SymbolPolyline(
                    points=CoordinatePointList(
                        [CoordinatePoint(-1, -3), CoordinatePoint(-1, 3)]
                    ),
                    stroke=Stroke(width=0.508),
                ),
                SymbolPolyline(
                    points=CoordinatePointList(
                        [CoordinatePoint(1, -3), CoordinatePoint(1, 3)]
                    ),
                    stroke=Stroke(width=0.508),
                ),
            ]
        )

        cap_symbol.pins.extend(
            [
                SymbolPin(
                    PinElectricalType.PASSIVE,
                    PinGraphicStyle.LINE,
                    Position(-2.54, 0),
                    1.54,
                    "",
                    "1",
                ),
                SymbolPin(
                    PinElectricalType.PASSIVE,
                    PinGraphicStyle.LINE,
                    Position(2.54, 0),
                    1.54,
                    "",
                    "2",
                ),
            ]
        )

        library.add_symbol(cap_symbol)

        # Verify library contents
        assert library.version == 20220914
        assert library.generator == "comprehensive_test"
        assert len(library.symbols) == 3

        # Verify we can retrieve all symbols
        assert library.get_symbol("Resistor") is not None
        assert library.get_symbol("OpAmp") is not None
        assert library.get_symbol("Capacitor") is not None

        # Verify symbol properties
        opamp = library.get_symbol("OpAmp")
        assert len(opamp.pins) == 3
        assert len(opamp.polylines) == 1
        assert opamp.pin_names_offset == 0.508

        capacitor = library.get_symbol("Capacitor")
        assert len(capacitor.pins) == 2
        assert len(capacitor.polylines) == 2
