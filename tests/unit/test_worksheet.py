"""
Unit tests for kicad_worksheet module
"""

import pytest

from kicad_parser import (
    UUID,
    CornerType,
    KiCadWorksheet,
    Position,
    WorksheetBitmap,
    WorksheetLine,
    WorksheetPolygon,
    WorksheetRectangle,
    WorksheetSetup,
    WorksheetText,
    create_basic_worksheet,
    serialize_kicad_object,
)

# PROGRESS TRACKING - WORKSHEET TESTS
# =======================================
# ✓ Basic worksheet tests exist (TestKiCadWorksheet, TestWorksheetSetup, etc.)
# ✓ Enhanced with comprehensive minimal/comprehensive test patterns
# ✓ Test WorksheetText, WorksheetLine, WorksheetRectangle classes - COMPLETED
# ✓ Test WorksheetPolygon, WorksheetBitmap classes - COMPLETED
# ✓ Test WorksheetSetup, KiCadWorksheet classes - COMPLETED


class TestKiCadWorksheet:
    """Test KiCadWorksheet class"""

    def test_worksheet_creation(self):
        """Test creating a worksheet"""
        worksheet = KiCadWorksheet()
        assert worksheet.version == 20220228
        assert worksheet.generator == "kicad_parser"
        assert isinstance(worksheet.setup, WorksheetSetup)
        assert len(worksheet.lines) == 0
        assert len(worksheet.rectangles) == 0
        assert len(worksheet.polygons) == 0
        assert len(worksheet.texts) == 0
        assert len(worksheet.bitmaps) == 0

    def test_worksheet_with_content(self):
        """Test creating a worksheet with content"""
        worksheet = KiCadWorksheet()

        # Add a line
        line = WorksheetLine(
            start=Position(0, 0), end=Position(100, 100), linewidth=0.15
        )
        worksheet.add_line(line)

        # Add a rectangle
        rectangle = WorksheetRectangle(
            start=Position(10, 10), end=Position(50, 50), corner=CornerType.LEFT_TOP
        )
        worksheet.add_rectangle(rectangle)

        # Add text
        text = WorksheetText(text="Test Text", position=Position(25, 25))
        worksheet.add_text(text)

        assert len(worksheet.lines) == 1
        assert len(worksheet.rectangles) == 1
        assert len(worksheet.texts) == 1


class TestWorksheetSetup:
    """Test WorksheetSetup class"""

    def test_setup_defaults(self):
        """Test default setup values"""
        setup = WorksheetSetup()
        assert setup.textsize.x == 1.5
        assert setup.textsize.y == 1.5
        assert setup.linewidth == 0.15
        assert setup.textlinewidth == 0.15
        assert setup.left_margin == 10.0
        assert setup.right_margin == 10.0
        assert setup.top_margin == 10.0
        assert setup.bottom_margin == 10.0

    def test_setup_custom_values(self):
        """Test custom setup values"""
        setup = WorksheetSetup(
            textsize=Position(2.0, 2.0), linewidth=0.2, left_margin=15.0
        )
        assert setup.textsize.x == 2.0
        assert setup.textsize.y == 2.0
        assert setup.linewidth == 0.2
        assert setup.left_margin == 15.0


class TestWorksheetLine:
    """Test WorksheetLine class"""

    def test_line_basic(self):
        """Test basic line creation"""
        line = WorksheetLine(start=Position(0, 0), end=Position(10, 10))
        assert line.start.x == 0
        assert line.start.y == 0
        assert line.end.x == 10
        assert line.end.y == 10
        assert line.linewidth is None
        assert line.corner is None

    def test_line_with_attributes(self):
        """Test line with all attributes"""
        line = WorksheetLine(
            start=Position(5, 5),
            end=Position(15, 15),
            linewidth=0.25,
            repeat=3,
            incrx=10.0,
            incry=5.0,
            corner=CornerType.RIGHT_BOTTOM,
        )
        assert line.linewidth == 0.25
        assert line.repeat == 3
        assert line.incrx == 10.0
        assert line.incry == 5.0
        assert line.corner == CornerType.RIGHT_BOTTOM


class TestWorksheetRectangle:
    """Test WorksheetRectangle class"""

    def test_rectangle_basic(self):
        """Test basic rectangle creation"""
        rect = WorksheetRectangle(start=Position(10, 10), end=Position(50, 40))
        assert rect.start.x == 10
        assert rect.start.y == 10
        assert rect.end.x == 50
        assert rect.end.y == 40

    def test_rectangle_with_corner(self):
        """Test rectangle with corner positioning"""
        rect = WorksheetRectangle(
            start=Position(0, 0), end=Position(20, 20), corner=CornerType.LEFT_BOTTOM
        )
        assert rect.corner == CornerType.LEFT_BOTTOM


class TestWorksheetText:
    """Test WorksheetText class"""

    def test_text_basic(self):
        """Test basic text creation"""
        text = WorksheetText(text="Sample Text", position=Position(100, 50))
        assert text.text == "Sample Text"
        assert text.position.x == 100
        assert text.position.y == 50

    def test_text_with_limits(self):
        """Test text with length and height limits"""
        text = WorksheetText(
            text="Long Text", position=Position(0, 0), maxlen=20, maxheight=5.0
        )
        assert text.maxlen == 20
        assert text.maxheight == 5.0


class TestWorksheetPolygon:
    """Test WorksheetPolygon class"""

    def test_polygon_empty(self):
        """Test empty polygon creation"""
        polygon = WorksheetPolygon()
        assert len(polygon.points.points) == 0

    def test_polygon_with_repeat(self):
        """Test polygon with repeat attributes"""
        polygon = WorksheetPolygon(repeat=5, incrx=10.0, incry=15.0)
        assert polygon.repeat == 5
        assert polygon.incrx == 10.0
        assert polygon.incry == 15.0


class TestWorksheetBitmap:
    """Test WorksheetBitmap class"""

    def test_bitmap_basic(self):
        """Test basic bitmap creation"""
        bitmap = WorksheetBitmap(position=Position(50, 75))
        assert bitmap.position.x == 50
        assert bitmap.position.y == 75
        assert bitmap.image is None


class TestCornerType:
    """Test CornerType enum"""

    def test_corner_values(self):
        """Test corner type values"""
        assert CornerType.LEFT_TOP.value == "ltcorner"
        assert CornerType.LEFT_BOTTOM.value == "lbcorner"
        assert CornerType.RIGHT_BOTTOM.value == "rbcorner"
        assert CornerType.RIGHT_TOP.value == "rtcorner"


class TestWorksheetHelpers:
    """Test worksheet helper functions"""

    def test_create_basic_worksheet(self):
        """Test creating basic worksheet"""
        worksheet = create_basic_worksheet("Test Title", "Test Company")

        assert worksheet.version == 20220228
        assert worksheet.generator == "kicad_parser"
        assert len(worksheet.rectangles) == 1
        assert len(worksheet.texts) == 2

        # Check title text
        title_text = next((t for t in worksheet.texts if t.text == "Test Title"), None)
        assert title_text is not None
        assert title_text.corner == CornerType.RIGHT_BOTTOM

        # Check company text
        company_text = next(
            (t for t in worksheet.texts if t.text == "Test Company"), None
        )
        assert company_text is not None
        assert company_text.corner == CornerType.RIGHT_BOTTOM

    def test_worksheet_serialization(self):
        """Test worksheet serialization to S-expression"""
        worksheet = create_basic_worksheet("Test", "Company")
        sexpr_output = serialize_kicad_object(worksheet)

        # Basic checks that it serializes without error
        assert isinstance(sexpr_output, str)
        assert "kicad_wks" in sexpr_output
        assert "setup" in sexpr_output
        assert "Test" in sexpr_output
        assert "Company" in sexpr_output

    def test_worksheet_roundtrip(self):
        """Test worksheet round-trip (create -> serialize -> parse)"""
        # Create original worksheet
        original = create_basic_worksheet("Original Title", "Original Company")

        # Serialize to S-expression
        sexpr_str = serialize_kicad_object(original)

        # Parse back
        from kicad_parser.sexpdata import loads

        sexpr = loads(sexpr_str)
        parsed = KiCadWorksheet.from_sexpr(sexpr)

        # Verify structure is maintained
        assert parsed.version == original.version
        assert parsed.generator == original.generator
        assert len(parsed.rectangles) == len(original.rectangles)
        assert len(parsed.texts) == len(original.texts)

        # Check text content is preserved
        original_texts = [t.text for t in original.texts]
        parsed_texts = [t.text for t in parsed.texts]
        assert sorted(original_texts) == sorted(parsed_texts)


# =====================================================
# COMPREHENSIVE WORKSHEET TESTS (MINIMAL + COMPREHENSIVE PATTERN)
# =====================================================


class TestWorksheetSetupComprehensive:
    """Test WorksheetSetup class with comprehensive patterns"""

    def test_worksheet_setup_minimal(self):
        """Test minimal WorksheetSetup creation and parsing"""
        # Minimal WorksheetSetup with defaults
        setup = WorksheetSetup()

        assert setup.textsize.x == 1.5
        assert setup.textsize.y == 1.5
        assert setup.linewidth == 0.15
        assert setup.textlinewidth == 0.15
        assert setup.left_margin == 10.0
        assert setup.right_margin == 10.0
        assert setup.top_margin == 10.0
        assert setup.bottom_margin == 10.0

        # Test round-trip
        sexpr = setup.to_sexpr()
        parsed_setup = WorksheetSetup.from_sexpr(sexpr)
        assert parsed_setup.textsize.x == setup.textsize.x
        assert parsed_setup.linewidth == setup.linewidth
        assert parsed_setup.left_margin == setup.left_margin

    def test_worksheet_setup_comprehensive(self):
        """Test comprehensive WorksheetSetup with all parameters"""
        # Comprehensive WorksheetSetup with custom values
        setup = WorksheetSetup(
            textsize=Position(2.5, 3.0),
            linewidth=0.3,
            textlinewidth=0.25,
            left_margin=15.0,
            right_margin=12.0,
            top_margin=8.0,
            bottom_margin=20.0,
        )

        assert setup.textsize.x == 2.5
        assert setup.textsize.y == 3.0
        assert setup.linewidth == 0.3
        assert setup.textlinewidth == 0.25
        assert setup.left_margin == 15.0
        assert setup.right_margin == 12.0
        assert setup.top_margin == 8.0
        assert setup.bottom_margin == 20.0

        # Test complete round-trip
        sexpr = setup.to_sexpr()
        parsed_setup = WorksheetSetup.from_sexpr(sexpr)
        assert parsed_setup.textsize.x == setup.textsize.x
        assert parsed_setup.textsize.y == setup.textsize.y
        assert parsed_setup.linewidth == setup.linewidth
        assert parsed_setup.textlinewidth == setup.textlinewidth
        assert parsed_setup.left_margin == setup.left_margin
        assert parsed_setup.right_margin == setup.right_margin
        assert parsed_setup.top_margin == setup.top_margin
        assert parsed_setup.bottom_margin == setup.bottom_margin


class TestWorksheetLineComprehensive:
    """Test WorksheetLine class with comprehensive patterns"""

    def test_worksheet_line_minimal(self):
        """Test minimal WorksheetLine creation and parsing"""
        # Minimal WorksheetLine
        line = WorksheetLine(start=Position(0.0, 0.0), end=Position(50.0, 25.0))

        assert line.start.x == 0.0
        assert line.start.y == 0.0
        assert line.end.x == 50.0
        assert line.end.y == 25.0
        assert line.linewidth is None
        assert line.corner is None
        assert line.repeat is None
        assert line.incrx is None
        assert line.incry is None

        # Test round-trip
        sexpr = line.to_sexpr()
        parsed_line = WorksheetLine.from_sexpr(sexpr)
        assert parsed_line.start.x == line.start.x
        assert parsed_line.start.y == line.start.y
        assert parsed_line.end.x == line.end.x
        assert parsed_line.end.y == line.end.y

    def test_worksheet_line_comprehensive(self):
        """Test comprehensive WorksheetLine with all parameters"""
        # Comprehensive WorksheetLine with all attributes
        line = WorksheetLine(
            start=Position(12.7, 38.1),
            end=Position(76.2, 101.6),
            linewidth=0.35,
            repeat=5,
            incrx=25.4,
            incry=15.0,
            corner=CornerType.RIGHT_TOP,
        )

        assert line.start.x == 12.7
        assert line.start.y == 38.1
        assert line.end.x == 76.2
        assert line.end.y == 101.6
        assert line.linewidth == 0.35
        assert line.repeat == 5
        assert line.incrx == 25.4
        assert line.incry == 15.0
        assert line.corner == CornerType.RIGHT_TOP

        # Test complete round-trip
        sexpr = line.to_sexpr()
        parsed_line = WorksheetLine.from_sexpr(sexpr)
        assert parsed_line.start.x == line.start.x
        assert parsed_line.start.y == line.start.y
        assert parsed_line.end.x == line.end.x
        assert parsed_line.end.y == line.end.y
        assert (
            parsed_line.width == line.linewidth
        )  # After round-trip, legacy linewidth becomes stroke
        assert parsed_line.repeat == line.repeat
        assert parsed_line.incrx == line.incrx
        assert parsed_line.incry == line.incry
        assert parsed_line.corner == line.corner


class TestWorksheetRectangleComprehensive:
    """Test WorksheetRectangle class with comprehensive patterns"""

    def test_worksheet_rectangle_minimal(self):
        """Test minimal WorksheetRectangle creation and parsing"""
        # Minimal WorksheetRectangle
        rectangle = WorksheetRectangle(
            start=Position(10.0, 15.0), end=Position(40.0, 35.0)
        )

        assert rectangle.start.x == 10.0
        assert rectangle.start.y == 15.0
        assert rectangle.end.x == 40.0
        assert rectangle.end.y == 35.0
        assert rectangle.corner is None
        assert rectangle.linewidth is None
        assert rectangle.repeat is None
        assert rectangle.incrx is None
        assert rectangle.incry is None

        # Test round-trip
        sexpr = rectangle.to_sexpr()
        parsed_rectangle = WorksheetRectangle.from_sexpr(sexpr)
        assert parsed_rectangle.start.x == rectangle.start.x
        assert parsed_rectangle.start.y == rectangle.start.y
        assert parsed_rectangle.end.x == rectangle.end.x
        assert parsed_rectangle.end.y == rectangle.end.y

    def test_worksheet_rectangle_comprehensive(self):
        """Test comprehensive WorksheetRectangle with all parameters"""
        # Comprehensive WorksheetRectangle with all attributes
        rectangle = WorksheetRectangle(
            start=Position(20.0, 30.0),
            end=Position(80.0, 60.0),
            corner=CornerType.LEFT_BOTTOM,
            linewidth=0.2,
            repeat=3,
            incrx=50.0,
            incry=40.0,
        )

        assert rectangle.start.x == 20.0
        assert rectangle.start.y == 30.0
        assert rectangle.end.x == 80.0
        assert rectangle.end.y == 60.0
        assert rectangle.corner == CornerType.LEFT_BOTTOM
        assert rectangle.linewidth == 0.2
        assert rectangle.repeat == 3
        assert rectangle.incrx == 50.0
        assert rectangle.incry == 40.0

        # Test complete round-trip
        sexpr = rectangle.to_sexpr()
        parsed_rectangle = WorksheetRectangle.from_sexpr(sexpr)
        assert parsed_rectangle.start.x == rectangle.start.x
        assert parsed_rectangle.start.y == rectangle.start.y
        assert parsed_rectangle.end.x == rectangle.end.x
        assert parsed_rectangle.end.y == rectangle.end.y
        assert parsed_rectangle.corner == rectangle.corner
        assert (
            parsed_rectangle.width == rectangle.linewidth
        )  # After round-trip, legacy linewidth becomes stroke
        assert parsed_rectangle.repeat == rectangle.repeat
        assert parsed_rectangle.incrx == rectangle.incrx
        assert parsed_rectangle.incry == rectangle.incry


class TestWorksheetTextComprehensive:
    """Test WorksheetText class with comprehensive patterns"""

    def test_worksheet_text_minimal(self):
        """Test minimal WorksheetText creation and parsing"""
        # Minimal WorksheetText
        text = WorksheetText(text="Minimal Text", position=Position(25.0, 50.0))

        assert text.text == "Minimal Text"
        assert text.position.x == 25.0
        assert text.position.y == 50.0
        assert text.font is None
        assert text.justify is None
        assert text.corner is None
        assert text.maxlen is None
        assert text.maxheight is None
        assert text.repeat is None

        # Test round-trip
        sexpr = text.to_sexpr()
        parsed_text = WorksheetText.from_sexpr(sexpr)
        assert parsed_text.text == text.text
        assert parsed_text.position.x == text.position.x
        assert parsed_text.position.y == text.position.y

    def test_worksheet_text_comprehensive(self):
        """Test comprehensive WorksheetText with all parameters"""
        # Comprehensive WorksheetText with all attributes
        text = WorksheetText(
            text="Comprehensive Text Content",
            position=Position(50.0, 75.0),
            justify="center",
            corner=CornerType.RIGHT_BOTTOM,
            maxlen=25,
            maxheight=10.0,
            repeat=2,
            incrx=30.0,
            incry=20.0,
            incrlabel=1,
        )

        assert text.text == "Comprehensive Text Content"
        assert text.position.x == 50.0
        assert text.position.y == 75.0
        assert text.font is None
        assert text.justify == "center"
        assert text.corner == CornerType.RIGHT_BOTTOM
        assert text.maxlen == 25
        assert text.maxheight == 10.0
        assert text.repeat == 2
        assert text.incrx == 30.0
        assert text.incry == 20.0
        assert text.incrlabel == 1

        # Test complete round-trip
        sexpr = text.to_sexpr()
        parsed_text = WorksheetText.from_sexpr(sexpr)
        assert parsed_text.text == text.text
        assert parsed_text.position.x == text.position.x
        assert parsed_text.position.y == text.position.y
        assert parsed_text.font == text.font
        assert parsed_text.justify == text.justify
        assert parsed_text.corner == text.corner
        assert parsed_text.maxlen == text.maxlen
        assert parsed_text.maxheight == text.maxheight
        assert parsed_text.repeat == text.repeat
        assert parsed_text.incrx == text.incrx
        assert parsed_text.incry == text.incry
        assert parsed_text.incrlabel == text.incrlabel


class TestWorksheetPolygonComprehensive:
    """Test WorksheetPolygon class with comprehensive patterns"""

    def test_worksheet_polygon_minimal(self):
        """Test minimal WorksheetPolygon creation and parsing"""
        # Minimal WorksheetPolygon
        polygon = WorksheetPolygon()

        assert len(polygon.points.points) == 0
        assert polygon.linewidth is None
        assert polygon.repeat is None
        assert polygon.incrx is None
        assert polygon.incry is None

        # Test round-trip
        sexpr = polygon.to_sexpr()
        parsed_polygon = WorksheetPolygon.from_sexpr(sexpr)
        assert len(parsed_polygon.points.points) == len(polygon.points.points)

    def test_worksheet_polygon_comprehensive(self):
        """Test comprehensive WorksheetPolygon with all parameters"""
        from kicad_parser.kicad_common import CoordinatePoint, CoordinatePointList

        # Comprehensive WorksheetPolygon with points and attributes
        coord_points = [
            CoordinatePoint(10.0, 20.0),
            CoordinatePoint(30.0, 15.0),
            CoordinatePoint(40.0, 35.0),
            CoordinatePoint(20.0, 40.0),
            CoordinatePoint(5.0, 30.0),
        ]
        polygon = WorksheetPolygon(
            points=CoordinatePointList(coord_points),
            linewidth=0.25,
            repeat=4,
            incrx=60.0,
            incry=45.0,
        )

        assert len(polygon.points.points) == 5
        assert polygon.points.points[0].x == 10.0
        assert polygon.points.points[0].y == 20.0
        assert polygon.points.points[4].x == 5.0
        assert polygon.points.points[4].y == 30.0
        assert polygon.linewidth == 0.25
        assert polygon.repeat == 4
        assert polygon.incrx == 60.0
        assert polygon.incry == 45.0

        # Test complete round-trip
        sexpr = polygon.to_sexpr()
        parsed_polygon = WorksheetPolygon.from_sexpr(sexpr)
        assert len(parsed_polygon.points.points) == len(polygon.points.points)
        assert parsed_polygon.points.points[0].x == polygon.points.points[0].x
        assert parsed_polygon.points.points[0].y == polygon.points.points[0].y
        assert parsed_polygon.points.points[4].x == polygon.points.points[4].x
        assert parsed_polygon.points.points[4].y == polygon.points.points[4].y
        assert (
            parsed_polygon.width == polygon.linewidth
        )  # After round-trip, legacy linewidth becomes stroke
        assert parsed_polygon.repeat == polygon.repeat
        assert parsed_polygon.incrx == polygon.incrx
        assert parsed_polygon.incry == polygon.incry


class TestWorksheetBitmapComprehensive:
    """Test WorksheetBitmap class with comprehensive patterns"""

    def test_worksheet_bitmap_minimal(self):
        """Test minimal WorksheetBitmap creation and parsing"""
        # Minimal WorksheetBitmap
        bitmap = WorksheetBitmap(position=Position(100.0, 150.0))

        assert bitmap.position.x == 100.0
        assert bitmap.position.y == 150.0
        assert bitmap.image is None
        assert bitmap.scale is None
        assert bitmap.repeat is None
        assert bitmap.incrx is None
        assert bitmap.incry is None

        # Test round-trip
        sexpr = bitmap.to_sexpr()
        parsed_bitmap = WorksheetBitmap.from_sexpr(sexpr)
        assert parsed_bitmap.position.x == bitmap.position.x
        assert parsed_bitmap.position.y == bitmap.position.y

    def test_worksheet_bitmap_comprehensive(self):
        """Test comprehensive WorksheetBitmap with all parameters"""
        # Comprehensive WorksheetBitmap with image data
        bitmap = WorksheetBitmap(
            position=Position(200.0, 250.0),
            scale=2.0,
            repeat=3,
            incrx=75.0,
            incry=50.0,
            image="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
        )

        assert bitmap.position.x == 200.0
        assert bitmap.position.y == 250.0
        assert bitmap.scale == 2.0
        assert bitmap.repeat == 3
        assert bitmap.incrx == 75.0
        assert bitmap.incry == 50.0
        assert bitmap.image is not None
        assert "iVBORw0KGgoAAAANSUhEUgAAAAE" in bitmap.image

        # Test complete round-trip
        sexpr = bitmap.to_sexpr()
        parsed_bitmap = WorksheetBitmap.from_sexpr(sexpr)
        assert parsed_bitmap.position.x == bitmap.position.x
        assert parsed_bitmap.position.y == bitmap.position.y
        assert parsed_bitmap.scale == bitmap.scale
        assert parsed_bitmap.repeat == bitmap.repeat
        assert parsed_bitmap.incrx == bitmap.incrx
        assert parsed_bitmap.incry == bitmap.incry
        assert parsed_bitmap.image == bitmap.image


class TestKiCadWorksheetComprehensive:
    """Test KiCadWorksheet class with comprehensive patterns"""

    def test_kicad_worksheet_minimal(self):
        """Test minimal KiCadWorksheet creation and parsing"""
        # Minimal KiCadWorksheet
        worksheet = KiCadWorksheet()

        assert worksheet.version == 20220228
        assert worksheet.generator == "kicad_parser"
        assert isinstance(worksheet.setup, WorksheetSetup)
        assert len(worksheet.lines) == 0
        assert len(worksheet.rectangles) == 0
        assert len(worksheet.polygons) == 0
        assert len(worksheet.texts) == 0
        assert len(worksheet.bitmaps) == 0

        # Test round-trip
        sexpr = worksheet.to_sexpr()
        parsed_worksheet = KiCadWorksheet.from_sexpr(sexpr)
        assert parsed_worksheet.version == worksheet.version
        assert parsed_worksheet.generator == worksheet.generator
        assert len(parsed_worksheet.lines) == len(worksheet.lines)

    def test_kicad_worksheet_comprehensive(self):
        """Test comprehensive KiCadWorksheet with all elements"""
        from kicad_parser.kicad_common import CoordinatePointList

        # Comprehensive KiCadWorksheet with all element types
        worksheet = KiCadWorksheet(version=20230228, generator="comprehensive_test")

        # Add comprehensive setup
        worksheet.setup = WorksheetSetup(
            textsize=Position(2.0, 2.0), linewidth=0.2, left_margin=12.0
        )

        # Add line
        worksheet.add_line(
            WorksheetLine(
                start=Position(10.0, 20.0),
                end=Position(50.0, 60.0),
                linewidth=0.3,
                corner=CornerType.LEFT_TOP,
            )
        )

        # Add rectangle
        worksheet.add_rectangle(
            WorksheetRectangle(
                start=Position(100.0, 200.0),
                end=Position(150.0, 250.0),
                corner=CornerType.RIGHT_BOTTOM,
            )
        )

        # Add text
        worksheet.add_text(
            WorksheetText(
                text="Comprehensive Test Text",
                position=Position(75.0, 125.0),
                corner=CornerType.LEFT_BOTTOM,
            )
        )

        # Add polygon
        from kicad_parser.kicad_common import CoordinatePoint

        coord_points = [
            CoordinatePoint(200.0, 300.0),
            CoordinatePoint(220.0, 280.0),
            CoordinatePoint(240.0, 320.0),
        ]
        worksheet.add_polygon(
            WorksheetPolygon(points=CoordinatePointList(coord_points), linewidth=0.15)
        )

        # Add bitmap
        worksheet.add_bitmap(
            WorksheetBitmap(position=Position(300.0, 400.0), scale=1.5)
        )

        # Verify all elements
        assert worksheet.version == 20230228
        assert worksheet.generator == "comprehensive_test"
        assert worksheet.setup.textsize.x == 2.0
        assert worksheet.setup.linewidth == 0.2
        assert len(worksheet.lines) == 1
        assert len(worksheet.rectangles) == 1
        assert len(worksheet.texts) == 1
        assert len(worksheet.polygons) == 1
        assert len(worksheet.bitmaps) == 1

        # Check specific elements
        assert worksheet.lines[0].linewidth == 0.3
        assert worksheet.rectangles[0].corner == CornerType.RIGHT_BOTTOM
        assert worksheet.texts[0].text == "Comprehensive Test Text"
        assert len(worksheet.polygons[0].points.points) == 3
        assert worksheet.bitmaps[0].scale == 1.5

        # Test complete round-trip
        sexpr = worksheet.to_sexpr()
        parsed_worksheet = KiCadWorksheet.from_sexpr(sexpr)
        assert parsed_worksheet.version == worksheet.version
        assert parsed_worksheet.generator == worksheet.generator
        assert len(parsed_worksheet.lines) == len(worksheet.lines)
        assert len(parsed_worksheet.rectangles) == len(worksheet.rectangles)
        assert len(parsed_worksheet.texts) == len(worksheet.texts)
        assert len(parsed_worksheet.polygons) == len(worksheet.polygons)
        assert len(parsed_worksheet.bitmaps) == len(worksheet.bitmaps)

        # Verify element content preservation
        assert (
            parsed_worksheet.lines[0].width == worksheet.lines[0].linewidth
        )  # After round-trip, legacy linewidth becomes stroke
        assert parsed_worksheet.texts[0].text == worksheet.texts[0].text
        assert parsed_worksheet.rectangles[0].corner == worksheet.rectangles[0].corner
