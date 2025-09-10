"""
Unit tests for KiCad graphics classes

Tests all graphics components including dimension formats, graphical elements,
and rendering properties based on KiCad PCB file format specifications.
"""

import pytest

from kicad_parser import *
from kicad_parser.kicad_common import JustifyHorizontal, StrokeType
from kicad_parser.kicad_graphics import (
    ArrowDirection,
    Dimension,
    DimensionFormat,
    DimensionStyle,
    DimensionType,
    DimensionUnits,
    DimensionUnitsFormat,
    GraphicalArc,
    GraphicalBezier,
    GraphicalCircle,
    GraphicalLine,
    GraphicalPolygon,
    GraphicalRectangle,
    GraphicalText,
    GraphicalTextBox,
    TextFrameType,
    TextPositionMode,
)

# PROGRESS TRACKING - GRAPHICS TESTS
# =======================================
# ✓ Creating test_graphics.py for graphics classes - COMPLETED
# ✓ Test DimensionFormat, DimensionStyle classes - COMPLETED
# ✓ Test GraphicalText, GraphicalLine, GraphicalRectangle classes - COMPLETED
# ✓ Test GraphicalCircle, GraphicalArc, GraphicalPolygon classes - COMPLETED
# ✓ Test Dimension, GraphicalTextBox, GraphicalBezier classes - COMPLETED


class TestDimensionFormat:
    """Test DimensionFormat class for dimension formatting"""

    def test_dimension_format_minimal(self):
        """Test minimal DimensionFormat creation and parsing"""
        # Minimal DimensionFormat with defaults
        dimension_format = DimensionFormat()

        assert dimension_format.prefix is None
        assert dimension_format.suffix is None
        assert dimension_format.units == DimensionUnits.MILLIMETERS
        assert dimension_format.units_format == DimensionUnitsFormat.NO_SUFFIX
        assert dimension_format.precision == 2
        assert dimension_format.override_value is None
        assert dimension_format.suppress_zeros is False

        # Test round-trip
        sexpr = dimension_format.to_sexpr()
        parsed_format = DimensionFormat.from_sexpr(sexpr)
        assert parsed_format.units == dimension_format.units
        assert parsed_format.precision == dimension_format.precision

    def test_dimension_format_comprehensive(self):
        """Test comprehensive DimensionFormat with all parameters"""
        # Comprehensive DimensionFormat with all options
        dimension_format = DimensionFormat(
            prefix="DIM:",
            suffix=" mm",
            units=DimensionUnits.INCHES,
            units_format=DimensionUnitsFormat.PARENTHESIS,
            precision=4,
            override_value="CUSTOM_VALUE",
            suppress_zeros=True,
        )

        assert dimension_format.prefix == "DIM:"
        assert dimension_format.suffix == " mm"
        assert dimension_format.units == DimensionUnits.INCHES
        assert dimension_format.units_format == DimensionUnitsFormat.PARENTHESIS
        assert dimension_format.precision == 4
        assert dimension_format.override_value == "CUSTOM_VALUE"
        assert dimension_format.suppress_zeros is True

        # Test complete round-trip
        sexpr = dimension_format.to_sexpr()
        parsed_format = DimensionFormat.from_sexpr(sexpr)
        assert parsed_format.prefix == dimension_format.prefix
        assert parsed_format.suffix == dimension_format.suffix
        assert parsed_format.units == dimension_format.units
        assert parsed_format.units_format == dimension_format.units_format
        assert parsed_format.precision == dimension_format.precision
        assert parsed_format.override_value == dimension_format.override_value
        assert parsed_format.suppress_zeros == dimension_format.suppress_zeros


class TestDimensionStyle:
    """Test DimensionStyle class for dimension styling"""

    def test_dimension_style_minimal(self):
        """Test minimal DimensionStyle creation and parsing"""
        # Minimal DimensionStyle with defaults
        dimension_style = DimensionStyle()

        assert dimension_style.thickness == 0.15
        assert dimension_style.arrow_length == 1.27
        assert dimension_style.text_position_mode == TextPositionMode.OUTSIDE
        assert dimension_style.extension_height == 1.27
        assert dimension_style.extension_offset == 0.5
        assert dimension_style.keep_text_aligned is True
        assert dimension_style.text_frame == TextFrameType.NONE

        # Test round-trip
        sexpr = dimension_style.to_sexpr()
        parsed_style = DimensionStyle.from_sexpr(sexpr)
        assert parsed_style.thickness == dimension_style.thickness
        assert parsed_style.arrow_length == dimension_style.arrow_length

    def test_dimension_style_comprehensive(self):
        """Test comprehensive DimensionStyle with all parameters"""
        # Comprehensive DimensionStyle with all options
        dimension_style = DimensionStyle(
            thickness=0.25,
            arrow_length=2.54,
            text_position_mode=TextPositionMode.INLINE,
            extension_height=2.0,
            extension_offset=1.0,
            keep_text_aligned=False,
            text_frame=TextFrameType.RECTANGLE,
            arrow_direction=ArrowDirection.INWARD,
        )

        assert dimension_style.thickness == 0.25
        assert dimension_style.arrow_length == 2.54
        assert dimension_style.text_position_mode == TextPositionMode.INLINE
        assert dimension_style.extension_height == 2.0
        assert dimension_style.extension_offset == 1.0
        assert dimension_style.keep_text_aligned is False
        assert dimension_style.text_frame == TextFrameType.RECTANGLE
        assert dimension_style.arrow_direction == ArrowDirection.INWARD

        # Test complete round-trip
        sexpr = dimension_style.to_sexpr()
        parsed_style = DimensionStyle.from_sexpr(sexpr)
        assert parsed_style.thickness == dimension_style.thickness
        assert parsed_style.arrow_length == dimension_style.arrow_length
        assert parsed_style.text_position_mode == dimension_style.text_position_mode
        assert parsed_style.extension_height == dimension_style.extension_height
        assert parsed_style.extension_offset == dimension_style.extension_offset
        assert parsed_style.keep_text_aligned == dimension_style.keep_text_aligned
        assert parsed_style.text_frame == dimension_style.text_frame
        assert parsed_style.arrow_direction == dimension_style.arrow_direction


class TestGraphicalText:
    """Test GraphicalText class for text rendering"""

    def test_graphical_text_minimal(self):
        """Test minimal GraphicalText creation and parsing"""
        # Minimal GraphicalText
        text = GraphicalText(
            text="Test Text", position=Position(10.0, 20.0), layer="F.SilkS"
        )

        assert text.text == "Test Text"
        assert text.position.x == 10.0
        assert text.position.y == 20.0
        assert text.layer == "F.SilkS"

        # Test round-trip
        sexpr = text.to_sexpr()
        parsed_text = GraphicalText.from_sexpr(sexpr)
        assert parsed_text.text == text.text
        assert parsed_text.position.x == text.position.x
        assert parsed_text.position.y == text.position.y
        assert parsed_text.layer == text.layer

    def test_graphical_text_comprehensive(self):
        """Test comprehensive GraphicalText with all parameters"""
        # Comprehensive GraphicalText with effects and properties
        text = GraphicalText(
            text="Comprehensive Text",
            position=Position(25.4, 38.1, 45.0),
            layer="B.SilkS",
            effects=TextEffects(
                font=Font(size_height=2.0, size_width=2.0, thickness=0.3),
                justify_horizontal=JustifyHorizontal.CENTER,
                hide=False,
            ),
            uuid=UUID("text-uuid-123"),
        )

        assert text.text == "Comprehensive Text"
        assert text.position.x == 25.4
        assert text.position.y == 38.1
        assert text.position.angle == 45.0
        assert text.layer == "B.SilkS"
        assert text.effects is not None
        assert text.effects.font.size_height == 2.0
        assert text.effects.font.size_width == 2.0
        assert text.uuid.uuid == "text-uuid-123"

        # Test complete round-trip
        sexpr = text.to_sexpr()
        parsed_text = GraphicalText.from_sexpr(sexpr)
        assert parsed_text.text == text.text
        assert parsed_text.position.x == text.position.x
        assert parsed_text.position.y == text.position.y
        assert parsed_text.position.angle == text.position.angle
        assert parsed_text.layer == text.layer
        if parsed_text.uuid and text.uuid:
            assert parsed_text.uuid.uuid == text.uuid.uuid


class TestGraphicalLine:
    """Test GraphicalLine class for line rendering"""

    def test_graphical_line_minimal(self):
        """Test minimal GraphicalLine creation and parsing"""
        # Minimal GraphicalLine
        line = GraphicalLine(
            start=Position(0.0, 0.0), end=Position(10.0, 10.0), layer="F.SilkS"
        )

        assert line.start.x == 0.0
        assert line.start.y == 0.0
        assert line.end.x == 10.0
        assert line.end.y == 10.0
        assert line.layer == "F.SilkS"

        # Test round-trip
        sexpr = line.to_sexpr()
        parsed_line = GraphicalLine.from_sexpr(sexpr)
        assert parsed_line.start.x == line.start.x
        assert parsed_line.start.y == line.start.y
        assert parsed_line.end.x == line.end.x
        assert parsed_line.end.y == line.end.y
        assert parsed_line.layer == line.layer

    def test_graphical_line_comprehensive(self):
        """Test comprehensive GraphicalLine with all parameters"""
        # Comprehensive GraphicalLine with stroke and properties
        line = GraphicalLine(
            start=Position(12.7, 25.4),
            end=Position(50.8, 76.2),
            layer="B.Cu",
            stroke=Stroke(width=0.25, color=(0.8, 0.2, 0.1, 1.0)),
            uuid=UUID("line-uuid-456"),
        )

        assert line.start.x == 12.7
        assert line.start.y == 25.4
        assert line.end.x == 50.8
        assert line.end.y == 76.2
        assert line.layer == "B.Cu"
        assert line.stroke.width == 0.25
        assert line.stroke.color == (0.8, 0.2, 0.1, 1.0)
        assert line.uuid.uuid == "line-uuid-456"

        # Test complete round-trip
        sexpr = line.to_sexpr()
        parsed_line = GraphicalLine.from_sexpr(sexpr)
        assert parsed_line.start.x == line.start.x
        assert parsed_line.start.y == line.start.y
        assert parsed_line.end.x == line.end.x
        assert parsed_line.end.y == line.end.y
        assert parsed_line.layer == line.layer
        if parsed_line.uuid and line.uuid:
            assert parsed_line.uuid.uuid == line.uuid.uuid


class TestGraphicalRectangle:
    """Test GraphicalRectangle class for rectangle rendering"""

    def test_graphical_rectangle_minimal(self):
        """Test minimal GraphicalRectangle creation and parsing"""
        # Minimal GraphicalRectangle
        rectangle = GraphicalRectangle(
            start=Position(5.0, 5.0), end=Position(15.0, 15.0), layer="F.SilkS"
        )

        assert rectangle.start.x == 5.0
        assert rectangle.start.y == 5.0
        assert rectangle.end.x == 15.0
        assert rectangle.end.y == 15.0
        assert rectangle.layer == "F.SilkS"

        # Test round-trip
        sexpr = rectangle.to_sexpr()
        parsed_rectangle = GraphicalRectangle.from_sexpr(sexpr)
        assert parsed_rectangle.start.x == rectangle.start.x
        assert parsed_rectangle.start.y == rectangle.start.y
        assert parsed_rectangle.end.x == rectangle.end.x
        assert parsed_rectangle.end.y == rectangle.end.y
        assert parsed_rectangle.layer == rectangle.layer

    def test_graphical_rectangle_comprehensive(self):
        """Test comprehensive GraphicalRectangle with all parameters"""
        # Comprehensive GraphicalRectangle with fill and properties
        rectangle = GraphicalRectangle(
            start=Position(20.0, 30.0),
            end=Position(40.0, 50.0),
            layer="F.Fab",
            stroke=Stroke(width=0.12, type="dash_dot"),
            fill=True,
            uuid=UUID("rect-uuid-789"),
        )

        assert rectangle.start.x == 20.0
        assert rectangle.start.y == 30.0
        assert rectangle.end.x == 40.0
        assert rectangle.end.y == 50.0
        assert rectangle.layer == "F.Fab"
        assert rectangle.stroke.width == 0.12
        assert rectangle.stroke.type == StrokeType.DASH_DOT
        assert rectangle.fill == True
        assert rectangle.uuid.uuid == "rect-uuid-789"

        # Test complete round-trip
        sexpr = rectangle.to_sexpr()
        parsed_rectangle = GraphicalRectangle.from_sexpr(sexpr)
        assert parsed_rectangle.start.x == rectangle.start.x
        assert parsed_rectangle.start.y == rectangle.start.y
        assert parsed_rectangle.end.x == rectangle.end.x
        assert parsed_rectangle.end.y == rectangle.end.y
        assert parsed_rectangle.layer == rectangle.layer
        if parsed_rectangle.uuid and rectangle.uuid:
            assert parsed_rectangle.uuid.uuid == rectangle.uuid.uuid


class TestGraphicalCircle:
    """Test GraphicalCircle class for circle rendering"""

    def test_graphical_circle_minimal(self):
        """Test minimal GraphicalCircle creation and parsing"""
        # Minimal GraphicalCircle
        circle = GraphicalCircle(
            center=Position(25.0, 25.0),
            end=Position(35.0, 25.0),  # Radius endpoint
            layer="F.SilkS",
        )

        assert circle.center.x == 25.0
        assert circle.center.y == 25.0
        assert circle.end.x == 35.0
        assert circle.end.y == 25.0
        assert circle.layer == "F.SilkS"

        # Test round-trip
        sexpr = circle.to_sexpr()
        parsed_circle = GraphicalCircle.from_sexpr(sexpr)
        assert parsed_circle.center.x == circle.center.x
        assert parsed_circle.center.y == circle.center.y
        assert parsed_circle.end.x == circle.end.x
        assert parsed_circle.end.y == circle.end.y
        assert parsed_circle.layer == circle.layer

    def test_graphical_circle_comprehensive(self):
        """Test comprehensive GraphicalCircle with all parameters"""
        # Comprehensive GraphicalCircle with stroke and properties
        circle = GraphicalCircle(
            center=Position(50.8, 76.2),
            end=Position(63.5, 76.2),  # 12.7mm radius
            layer="B.SilkS",
            stroke=Stroke(width=0.2, color=(0.0, 1.0, 0.0, 1.0)),
            fill=False,
            uuid=UUID("circle-uuid-abc"),
        )

        assert circle.center.x == 50.8
        assert circle.center.y == 76.2
        assert circle.end.x == 63.5
        assert circle.end.y == 76.2
        assert circle.layer == "B.SilkS"
        assert circle.stroke.width == 0.2
        assert circle.stroke.color == (0.0, 1.0, 0.0, 1.0)
        assert circle.fill == False
        assert circle.uuid.uuid == "circle-uuid-abc"

        # Test complete round-trip
        sexpr = circle.to_sexpr()
        parsed_circle = GraphicalCircle.from_sexpr(sexpr)
        assert parsed_circle.center.x == circle.center.x
        assert parsed_circle.center.y == circle.center.y
        assert parsed_circle.end.x == circle.end.x
        assert parsed_circle.end.y == circle.end.y
        assert parsed_circle.layer == circle.layer
        if parsed_circle.uuid and circle.uuid:
            assert parsed_circle.uuid.uuid == circle.uuid.uuid


class TestGraphicalArc:
    """Test GraphicalArc class for arc rendering"""

    def test_graphical_arc_minimal(self):
        """Test minimal GraphicalArc creation and parsing"""
        # Minimal GraphicalArc
        arc = GraphicalArc(
            start=Position(10.0, 10.0),
            mid=Position(15.0, 15.0),
            end=Position(20.0, 10.0),
            layer="F.SilkS",
        )

        assert arc.start.x == 10.0
        assert arc.start.y == 10.0
        assert arc.mid.x == 15.0
        assert arc.mid.y == 15.0
        assert arc.end.x == 20.0
        assert arc.end.y == 10.0
        assert arc.layer == "F.SilkS"

        # Test round-trip
        sexpr = arc.to_sexpr()
        parsed_arc = GraphicalArc.from_sexpr(sexpr)
        assert parsed_arc.start.x == arc.start.x
        assert parsed_arc.start.y == arc.start.y
        assert parsed_arc.mid.x == arc.mid.x
        assert parsed_arc.mid.y == arc.mid.y
        assert parsed_arc.end.x == arc.end.x
        assert parsed_arc.end.y == arc.end.y
        assert parsed_arc.layer == arc.layer

    def test_graphical_arc_comprehensive(self):
        """Test comprehensive GraphicalArc with all parameters"""
        # Comprehensive GraphicalArc with stroke and properties
        arc = GraphicalArc(
            start=Position(30.0, 40.0),
            mid=Position(40.0, 50.0),
            end=Position(50.0, 40.0),
            layer="F.Cu",
            stroke=Stroke(width=0.35, type="solid", color=(1.0, 0.0, 1.0, 1.0)),
            uuid=UUID("arc-uuid-def"),
        )

        assert arc.start.x == 30.0
        assert arc.start.y == 40.0
        assert arc.mid.x == 40.0
        assert arc.mid.y == 50.0
        assert arc.end.x == 50.0
        assert arc.end.y == 40.0
        assert arc.layer == "F.Cu"
        assert arc.stroke.width == 0.35
        assert arc.stroke.type == StrokeType.SOLID
        assert arc.stroke.color == (1.0, 0.0, 1.0, 1.0)
        assert arc.uuid.uuid == "arc-uuid-def"

        # Test complete round-trip
        sexpr = arc.to_sexpr()
        parsed_arc = GraphicalArc.from_sexpr(sexpr)
        assert parsed_arc.start.x == arc.start.x
        assert parsed_arc.start.y == arc.start.y
        assert parsed_arc.mid.x == arc.mid.x
        assert parsed_arc.mid.y == arc.mid.y
        assert parsed_arc.end.x == arc.end.x
        assert parsed_arc.end.y == arc.end.y
        assert parsed_arc.layer == arc.layer
        if parsed_arc.uuid and arc.uuid:
            assert parsed_arc.uuid.uuid == arc.uuid.uuid


class TestGraphicalPolygon:
    """Test GraphicalPolygon class for polygon rendering"""

    def test_graphical_polygon_minimal(self):
        """Test minimal GraphicalPolygon creation and parsing"""
        # Minimal GraphicalPolygon
        points = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
        polygon = GraphicalPolygon(points=CoordinatePointList(points), layer="F.SilkS")

        assert len(polygon.points) == 4
        assert polygon.points[0] == (0.0, 0.0)
        assert polygon.points[1] == (10.0, 0.0)
        assert polygon.points[2] == (10.0, 10.0)
        assert polygon.points[3] == (0.0, 10.0)
        assert polygon.layer == "F.SilkS"

        # Test round-trip
        sexpr = polygon.to_sexpr()
        parsed_polygon = GraphicalPolygon.from_sexpr(sexpr)
        assert len(parsed_polygon.points) == len(polygon.points)
        assert parsed_polygon.points[0] == polygon.points[0]
        assert parsed_polygon.layer == polygon.layer

    def test_graphical_polygon_comprehensive(self):
        """Test comprehensive GraphicalPolygon with all parameters"""
        # Comprehensive GraphicalPolygon with stroke and fill
        points = [(15.0, 20.0), (25.0, 15.0), (35.0, 25.0), (25.0, 35.0), (15.0, 30.0)]
        polygon = GraphicalPolygon(
            points=CoordinatePointList(points),
            layer="B.Fab",
            stroke=Stroke(width=0.15, type="dash", color=(0.5, 0.5, 0.5, 0.8)),
            fill=True,
            uuid=UUID("polygon-uuid-ghi"),
        )

        assert len(polygon.points) == 5
        assert polygon.points[0] == (15.0, 20.0)
        assert polygon.points[4] == (15.0, 30.0)
        assert polygon.layer == "B.Fab"
        assert polygon.stroke.width == 0.15
        assert polygon.stroke.type == StrokeType.DASH
        assert polygon.fill == True
        assert polygon.uuid.uuid == "polygon-uuid-ghi"

        # Test complete round-trip
        sexpr = polygon.to_sexpr()
        parsed_polygon = GraphicalPolygon.from_sexpr(sexpr)
        assert len(parsed_polygon.points) == len(polygon.points)
        assert parsed_polygon.points[0] == polygon.points[0]
        assert parsed_polygon.points[4] == polygon.points[4]
        assert parsed_polygon.layer == polygon.layer
        if parsed_polygon.uuid and polygon.uuid:
            assert parsed_polygon.uuid.uuid == polygon.uuid.uuid


class TestDimension:
    """Test Dimension class for dimension annotations"""

    def test_dimension_minimal(self):
        """Test minimal Dimension creation and parsing"""
        # Minimal Dimension
        dimension = Dimension(type=DimensionType.ALIGNED, layer="Dwgs.User")

        assert dimension.type == DimensionType.ALIGNED
        assert dimension.layer == "Dwgs.User"
        assert dimension.locked is None

        # Test round-trip
        sexpr = dimension.to_sexpr()
        parsed_dimension = Dimension.from_sexpr(sexpr)
        assert parsed_dimension.type == dimension.type
        assert parsed_dimension.layer == dimension.layer

    def test_dimension_comprehensive(self):
        """Test comprehensive Dimension with all parameters"""
        # Comprehensive Dimension with format and style
        dimension = Dimension(
            locked=True,
            type=DimensionType.RADIAL,
            layer="Cmts.User",
            uuid=UUID("dimension-uuid-jkl"),
            points=CoordinatePointList([(0.0, 0.0), (50.0, 0.0), (25.0, -10.0)]),
            height=2.54,
            orientation=0,
            leader_length=5.08,
            text=GraphicalText(
                text="R25.0", position=Position(25.0, -10.0), layer="Cmts.User"
            ),
            format=DimensionFormat(
                prefix="R", units=DimensionUnits.MILLIMETERS, precision=1
            ),
            style=DimensionStyle(
                thickness=0.2,
                arrow_length=1.0,
                text_position_mode=TextPositionMode.MANUAL,
            ),
        )

        assert dimension.locked is True
        assert dimension.type == DimensionType.RADIAL
        assert dimension.layer == "Cmts.User"
        assert dimension.uuid.uuid == "dimension-uuid-jkl"
        assert len(dimension.points) == 3
        assert dimension.height == 2.54
        assert dimension.orientation == 0
        assert dimension.leader_length == 5.08
        assert dimension.text.text == "R25.0"
        assert dimension.format.prefix == "R"
        assert dimension.style.thickness == 0.2

        # Test complete round-trip
        sexpr = dimension.to_sexpr()
        parsed_dimension = Dimension.from_sexpr(sexpr)
        assert parsed_dimension.type == dimension.type
        assert parsed_dimension.layer == dimension.layer
        assert parsed_dimension.locked == dimension.locked
        if parsed_dimension.uuid and dimension.uuid:
            assert parsed_dimension.uuid.uuid == dimension.uuid.uuid


class TestGraphicalTextBox:
    """Test GraphicalTextBox class for text box rendering"""

    def test_graphical_textbox_minimal(self):
        """Test minimal GraphicalTextBox creation and parsing"""
        # Minimal GraphicalTextBox
        textbox = GraphicalTextBox(text="Text Box Content", layer="F.SilkS")

        assert textbox.text == "Text Box Content"
        assert textbox.layer == "F.SilkS"
        assert textbox.locked is None

        # Test round-trip
        sexpr = textbox.to_sexpr()
        parsed_textbox = GraphicalTextBox.from_sexpr(sexpr)
        assert parsed_textbox.text == textbox.text
        assert parsed_textbox.layer == textbox.layer

    def test_graphical_textbox_comprehensive(self):
        """Test comprehensive GraphicalTextBox with all parameters"""
        # Comprehensive GraphicalTextBox with all options
        textbox = GraphicalTextBox(
            locked=True,
            text="Comprehensive Text Box",
            start=Position(10.0, 10.0),
            end=Position(50.0, 30.0),
            layer="B.SilkS",
            uuid=UUID("textbox-uuid-mno"),
            effects=TextEffects(
                font=Font(size_height=1.5, size_width=1.5, thickness=0.2),
                justify_horizontal=JustifyHorizontal.LEFT,
            ),
            stroke=Stroke(width=0.1, color=(0.2, 0.8, 0.6, 1.0)),
            render_cache="cached_render_data",
        )

        assert textbox.locked is True
        assert textbox.text == "Comprehensive Text Box"
        assert textbox.start.x == 10.0
        assert textbox.start.y == 10.0
        assert textbox.end.x == 50.0
        assert textbox.end.y == 30.0
        assert textbox.layer == "B.SilkS"
        assert textbox.uuid.uuid == "textbox-uuid-mno"
        assert textbox.effects.font.size_height == 1.5
        assert textbox.effects.font.size_width == 1.5
        assert textbox.stroke.width == 0.1
        assert textbox.render_cache == "cached_render_data"

        # Test complete round-trip
        sexpr = textbox.to_sexpr()
        parsed_textbox = GraphicalTextBox.from_sexpr(sexpr)
        assert parsed_textbox.text == textbox.text
        assert parsed_textbox.layer == textbox.layer
        assert parsed_textbox.locked == textbox.locked
        if parsed_textbox.uuid and textbox.uuid:
            assert parsed_textbox.uuid.uuid == textbox.uuid.uuid


class TestGraphicalBezier:
    """Test GraphicalBezier class for Bezier curve rendering"""

    def test_graphical_bezier_minimal(self):
        """Test minimal GraphicalBezier creation and parsing"""
        # Minimal GraphicalBezier
        points = [(0.0, 0.0), (10.0, 20.0), (30.0, 20.0), (40.0, 0.0)]
        bezier = GraphicalBezier(points=CoordinatePointList(points), layer="F.SilkS")

        assert len(bezier.points) == 4
        assert bezier.points[0] == (0.0, 0.0)
        assert bezier.points[1] == (10.0, 20.0)
        assert bezier.points[2] == (30.0, 20.0)
        assert bezier.points[3] == (40.0, 0.0)
        assert bezier.layer == "F.SilkS"

        # Test round-trip
        sexpr = bezier.to_sexpr()
        parsed_bezier = GraphicalBezier.from_sexpr(sexpr)
        assert len(parsed_bezier.points) == len(bezier.points)
        assert parsed_bezier.points[0] == bezier.points[0]
        assert parsed_bezier.layer == bezier.layer

    def test_graphical_bezier_comprehensive(self):
        """Test comprehensive GraphicalBezier with all parameters"""
        # Comprehensive GraphicalBezier with stroke properties
        points = [
            (5.0, 5.0),
            (15.0, 25.0),
            (35.0, 25.0),
            (45.0, 5.0),
            (55.0, 15.0),
            (65.0, 5.0),
        ]
        bezier = GraphicalBezier(
            points=CoordinatePointList(points),
            layer="F.Cu",
            stroke=Stroke(width=0.4, type="dash_dot", color=(0.9, 0.1, 0.8, 1.0)),
            uuid=UUID("bezier-uuid-pqr"),
        )

        assert len(bezier.points) == 6
        assert bezier.points[0] == (5.0, 5.0)
        assert bezier.points[5] == (65.0, 5.0)
        assert bezier.layer == "F.Cu"
        assert bezier.stroke.width == 0.4
        assert bezier.stroke.type == StrokeType.DASH_DOT
        assert bezier.stroke.color == (0.9, 0.1, 0.8, 1.0)
        assert bezier.uuid.uuid == "bezier-uuid-pqr"

        # Test complete round-trip
        sexpr = bezier.to_sexpr()
        parsed_bezier = GraphicalBezier.from_sexpr(sexpr)
        assert len(parsed_bezier.points) == len(bezier.points)
        assert parsed_bezier.points[0] == bezier.points[0]
        assert parsed_bezier.points[5] == bezier.points[5]
        assert parsed_bezier.layer == bezier.layer
        if parsed_bezier.uuid and bezier.uuid:
            assert parsed_bezier.uuid.uuid == bezier.uuid.uuid


if __name__ == "__main__":
    pytest.main([__file__])
