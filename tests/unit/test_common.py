"""
Unit tests for kicad_common module

Progress:
✅ Position class (minimal + comprehensive)
✅ CoordinatePoint class (minimal + comprehensive)
✅ CoordinatePointList class (minimal + comprehensive)
✅ Stroke class (minimal + comprehensive)
✅ Font class (minimal + comprehensive)
✅ TextEffects class (minimal + comprehensive)
✅ PageSettings class (minimal + comprehensive)
✅ TitleBlock class (minimal + comprehensive)
✅ Property class (minimal + comprehensive)
✅ Image class (minimal + comprehensive)
✅ UUID class (minimal + comprehensive)
"""

import pytest

from kicad_parser import UUID, Fill, Font, Position, Property, Stroke, TextEffects
from kicad_parser.kicad_common import (
    CoordinatePoint,
    CoordinatePointList,
    FillType,
    Image,
    JustifyHorizontal,
    JustifyVertical,
    PageSettings,
    SExprParser,
    StrokeType,
    TitleBlock,
)
from kicad_parser.sexpdata import Symbol


class TestPosition:
    """Test Position class"""

    def test_position_creation(self):
        """Test creating a position"""
        pos = Position(1.0, 2.0, 90.0)
        assert pos.x == 1.0
        assert pos.y == 2.0
        assert pos.angle == 90.0

    def test_position_defaults(self):
        """Test position with default values"""
        pos = Position(1.0, 2.0)
        assert pos.x == 1.0
        assert pos.y == 2.0
        assert pos.angle == 0.0

    def test_position_from_sexpr(self):
        """Test parsing position from S-expression"""
        sexpr = [Symbol("at"), 1.5, 2.5, 45.0]
        pos = Position.from_sexpr(sexpr)
        assert pos.x == 1.5
        assert pos.y == 2.5
        assert pos.angle == 45.0

    def test_position_to_sexpr(self):
        """Test converting position to S-expression"""
        pos = Position(1.0, 2.0, 90.0)
        sexpr = pos.to_sexpr()
        assert sexpr == [Symbol("at"), 1.0, 2.0, 90.0]

    def test_position_to_sexpr_no_angle(self):
        """Test converting position without angle to S-expression"""
        pos = Position(1.0, 2.0, 0.0)
        sexpr = pos.to_sexpr()
        assert sexpr == [Symbol("at"), 1.0, 2.0]

    def test_position_comprehensive_parsing(self):
        """Test comprehensive position with distinctive non-default values"""
        # Based on spec: (at X Y [ANGLE])
        sexpr = [Symbol("at"), 10.5, -20.3, 45.0]
        pos = Position.from_sexpr(sexpr)

        assert pos.x == 10.5
        assert pos.y == -20.3
        assert pos.angle == 45.0

        # Test round-trip serialization
        result_sexpr = pos.to_sexpr()
        assert result_sexpr == [Symbol("at"), 10.5, -20.3, 45.0]

    def test_position_minimal_parsing(self):
        """Test minimal position with only coordinates"""
        # Based on spec: (at X Y) - angle is optional
        sexpr = [Symbol("at"), 0, 0]
        pos = Position.from_sexpr(sexpr)

        assert pos.x == 0
        assert pos.y == 0
        assert pos.angle == 0.0  # Default value

        # Test round-trip serialization omits default angle
        result_sexpr = pos.to_sexpr()
        assert result_sexpr == [Symbol("at"), 0, 0]


class TestStroke:
    """Test Stroke class"""

    def test_stroke_defaults(self):
        """Test stroke with default values"""
        stroke = Stroke()
        assert stroke.width == 0.254
        assert stroke.type == StrokeType.SOLID
        assert stroke.color is None

    def test_stroke_with_values(self):
        """Test stroke with custom values"""
        stroke = Stroke(width=0.5, type=StrokeType.DASH)
        assert stroke.width == 0.5
        assert stroke.type == StrokeType.DASH

    def test_stroke_from_sexpr(self):
        """Test parsing stroke from S-expression"""
        sexpr = [
            Symbol("stroke"),
            [Symbol("width"), 0.3],
            [Symbol("type"), Symbol("dash")],
        ]
        stroke = Stroke.from_sexpr(sexpr)
        assert stroke.width == 0.3
        assert stroke.type == StrokeType.DASH

    def test_stroke_to_sexpr(self):
        """Test converting stroke to S-expression"""
        stroke = Stroke(width=0.3, type=StrokeType.DASH)
        sexpr = stroke.to_sexpr()
        expected = [
            Symbol("stroke"),
            [Symbol("width"), 0.3],
            [Symbol("type"), Symbol("dash")],
        ]
        assert sexpr == expected

    def test_stroke_comprehensive_parsing(self):
        """Test comprehensive stroke with all attributes"""
        # Based on spec: (stroke (width WIDTH) (type TYPE) (color R G B A))
        sexpr = [
            Symbol("stroke"),
            [Symbol("width"), 0.5],
            [Symbol("type"), Symbol("dash")],
            [Symbol("color"), 255, 128, 0, 200],
        ]
        stroke = Stroke.from_sexpr(sexpr)

        assert stroke.width == 0.5
        assert stroke.type == StrokeType.DASH
        assert stroke.color == (255, 128, 0, 200)

        # Test round-trip includes all elements
        result_sexpr = stroke.to_sexpr()
        assert [Symbol("width"), 0.5] in result_sexpr
        assert [Symbol("type"), Symbol("dash")] in result_sexpr
        assert [Symbol("color"), 255, 128, 0, 200] in result_sexpr

    def test_stroke_minimal_parsing(self):
        """Test minimal stroke with only width"""
        # Minimal case: only width specified
        sexpr = [Symbol("stroke"), [Symbol("width"), 0.1]]
        stroke = Stroke.from_sexpr(sexpr)

        assert stroke.width == 0.1
        assert stroke.type == StrokeType.SOLID  # Default value
        assert stroke.color is None  # Default value

        # Test round-trip serialization with minimal data
        result_sexpr = stroke.to_sexpr()
        assert [Symbol("width"), 0.1] in result_sexpr


class TestCoordinatePoint:
    """Test CoordinatePoint class based on spec: (xy X Y)"""

    def test_coordinate_point_minimal(self):
        """Test minimal coordinate point at origin"""
        # Based on spec: (xy X Y)
        sexpr = [Symbol("xy"), 0, 0]
        point = CoordinatePoint.from_sexpr(sexpr)

        assert point.x == 0
        assert point.y == 0

        # Test round-trip serialization
        result_sexpr = point.to_sexpr()
        assert result_sexpr == [Symbol("xy"), 0, 0]

    def test_coordinate_point_comprehensive(self):
        """Test comprehensive coordinate point with distinctive values"""
        # Test distinctive non-zero coordinates
        sexpr = [Symbol("xy"), 15.24, -25.4]
        point = CoordinatePoint.from_sexpr(sexpr)

        assert point.x == 15.24
        assert point.y == -25.4

        # Test round-trip serialization
        result_sexpr = point.to_sexpr()
        assert result_sexpr == [Symbol("xy"), 15.24, -25.4]


class TestCoordinatePointList:
    """Test CoordinatePointList class based on spec: (pts (xy X Y) ...)"""

    def test_coordinate_point_list_minimal(self):
        """Test minimal point list - empty"""
        # Based on spec: (pts)
        sexpr = [Symbol("pts")]
        point_list = CoordinatePointList.from_sexpr(sexpr)

        assert len(point_list.points) == 0

        # Test round-trip serialization
        result_sexpr = point_list.to_sexpr()
        assert result_sexpr == [Symbol("pts")]

    def test_coordinate_point_list_comprehensive(self):
        """Test comprehensive point list with multiple distinctive points"""
        # Based on spec: (pts (xy X Y) (xy X Y) (xy X Y))
        sexpr = [
            Symbol("pts"),
            [Symbol("xy"), 1.27, 2.54],
            [Symbol("xy"), -3.81, 7.62],
            [Symbol("xy"), 0, -10.16],
        ]
        point_list = CoordinatePointList.from_sexpr(sexpr)

        assert len(point_list.points) == 3
        assert point_list.points[0].x == 1.27
        assert point_list.points[0].y == 2.54
        assert point_list.points[1].x == -3.81
        assert point_list.points[1].y == 7.62
        assert point_list.points[2].x == 0
        assert point_list.points[2].y == -10.16

        # Test round-trip serialization
        result_sexpr = point_list.to_sexpr()
        assert len(result_sexpr) == 4  # pts + 3 xy points
        assert result_sexpr[0] == Symbol("pts")


class TestFill:
    """Test Fill class"""

    def test_fill_defaults(self):
        """Test fill with default values"""
        fill = Fill()
        assert fill.type == FillType.NONE

    def test_fill_from_sexpr(self):
        """Test parsing fill from S-expression"""
        sexpr = [Symbol("fill"), [Symbol("type"), Symbol("background")]]
        fill = Fill.from_sexpr(sexpr)
        assert fill.type == FillType.BACKGROUND

    def test_fill_to_sexpr(self):
        """Test converting fill to S-expression"""
        fill = Fill(type=FillType.BACKGROUND)
        sexpr = fill.to_sexpr()
        expected = [Symbol("fill"), [Symbol("type"), Symbol("background")]]
        assert sexpr == expected


class TestFont:
    """Test Font class"""

    def test_font_defaults(self):
        """Test font with default values"""
        font = Font()
        assert font.size_height == 1.27
        assert font.size_width == 1.27
        assert font.thickness is None
        assert font.bold is False
        assert font.italic is False

    def test_font_from_sexpr(self):
        """Test parsing font from S-expression"""
        sexpr = [
            Symbol("font"),
            [Symbol("size"), 1.5, 1.2],
            [Symbol("thickness"), 0.3],
            Symbol("bold"),
        ]
        font = Font.from_sexpr(sexpr)
        assert font.size_height == 1.5
        assert font.size_width == 1.2
        assert font.thickness == 0.3
        assert font.bold is True
        assert font.italic is False

    def test_font_to_sexpr(self):
        """Test converting font to S-expression"""
        font = Font(size_height=1.5, size_width=1.2, thickness=0.3, bold=True)
        sexpr = font.to_sexpr()
        expected = [
            Symbol("font"),
            [Symbol("size"), 1.5, 1.2],
            [Symbol("thickness"), 0.3],
            Symbol("bold"),
        ]
        assert sexpr == expected

    def test_font_comprehensive_parsing(self):
        """Test comprehensive font with all attributes"""
        # Based on spec: (font (size HEIGHT WIDTH) [thickness] [bold] [italic])
        sexpr = [
            Symbol("font"),
            [Symbol("size"), 2.54, 1.27],
            [Symbol("thickness"), 0.15],
            Symbol("bold"),
            Symbol("italic"),
        ]
        font = Font.from_sexpr(sexpr)

        assert font.size_height == 2.54
        assert font.size_width == 1.27
        assert font.thickness == 0.15
        assert font.bold is True
        assert font.italic is True

        # Test round-trip includes all elements
        result_sexpr = font.to_sexpr()
        assert Symbol("bold") in result_sexpr
        assert Symbol("italic") in result_sexpr
        assert [Symbol("thickness"), 0.15] in result_sexpr

    def test_font_minimal_parsing(self):
        """Test minimal font with only size"""
        # Minimal case: only size specified
        sexpr = [Symbol("font"), [Symbol("size"), 1.27, 1.27]]
        font = Font.from_sexpr(sexpr)

        assert font.size_height == 1.27
        assert font.size_width == 1.27
        assert font.thickness is None  # Default
        assert font.bold is False  # Default
        assert font.italic is False  # Default


class TestTextEffectsComprehensive:
    """Test TextEffects class based on spec: (effects (font ...) [justify] [hide])"""

    def test_text_effects_minimal(self):
        """Test minimal text effects with defaults"""
        effects = TextEffects()

        assert effects.font is not None
        assert effects.justify_horizontal == JustifyHorizontal.CENTER  # Default
        assert effects.justify_vertical == JustifyVertical.CENTER  # Default
        assert effects.hide is False

        # Test round-trip serialization
        result_sexpr = effects.to_sexpr()
        assert Symbol("effects") == result_sexpr[0]

    def test_text_effects_comprehensive(self):
        """Test comprehensive text effects with custom font, justify, hide"""
        # Based on spec: (effects (font ...) (justify ...) hide)
        sexpr = [
            Symbol("effects"),
            [Symbol("font"), [Symbol("size"), 3.0, 2.0], Symbol("bold")],
            [Symbol("justify"), Symbol("left"), Symbol("top")],
            Symbol("hide"),
        ]
        effects = TextEffects.from_sexpr(sexpr)

        assert effects.font.size_height == 3.0
        assert effects.font.size_width == 2.0
        assert effects.font.bold is True
        assert effects.justify_horizontal == JustifyHorizontal.LEFT
        assert effects.justify_vertical == JustifyVertical.TOP
        assert effects.hide is True

        # Test round-trip includes all elements
        result_sexpr = effects.to_sexpr()
        assert Symbol("hide") in result_sexpr


class TestPageSettingsComprehensive:
    """Test PageSettings class based on spec: (paper PAPER_SIZE|WIDTH HEIGHT [portrait])"""

    def test_page_settings_minimal(self):
        """Test minimal page settings with A4"""
        # Based on spec: (paper "A4")
        sexpr = [Symbol("paper"), "A4"]
        page = PageSettings.from_sexpr(sexpr)

        assert page.paper_size.value == "A4"
        assert page.portrait is False  # Default landscape

        # Test round-trip serialization
        result_sexpr = page.to_sexpr()
        assert result_sexpr == [Symbol("paper"), "A4"]

    def test_page_settings_comprehensive(self):
        """Test comprehensive page settings with custom size and portrait"""
        # Based on spec: (paper WIDTH HEIGHT portrait)
        sexpr = [Symbol("paper"), 297.0, 210.0, Symbol("portrait")]
        page = PageSettings.from_sexpr(sexpr)

        assert page.width == 297.0
        assert page.height == 210.0
        assert page.portrait is True

        # Test round-trip serialization
        result_sexpr = page.to_sexpr()
        assert 297.0 in result_sexpr
        assert 210.0 in result_sexpr
        assert Symbol("portrait") in result_sexpr


class TestTitleBlockComprehensive:
    """Test TitleBlock class based on spec: (title_block ...)"""

    def test_title_block_minimal(self):
        """Test minimal title block with empty fields"""
        title_block = TitleBlock()

        assert title_block.title == ""
        assert title_block.date == ""
        assert title_block.revision == ""
        assert title_block.company == ""
        assert len(title_block.comments) == 0

        # Test round-trip serialization
        result_sexpr = title_block.to_sexpr()
        assert Symbol("title_block") == result_sexpr[0]

    def test_title_block_comprehensive(self):
        """Test comprehensive title block with all fields"""
        # Based on spec: (title_block (title TITLE) (date DATE) (rev REV) (company COMPANY) (comment N COMMENT))
        sexpr = [
            Symbol("title_block"),
            [Symbol("title"), "Test Project"],
            [Symbol("date"), "2024-01-15"],
            [Symbol("rev"), "1.2"],
            [Symbol("company"), "ACME Corp"],
            [Symbol("comment"), 1, "First comment"],
            [Symbol("comment"), 2, "Second comment"],
        ]
        title_block = TitleBlock.from_sexpr(sexpr)

        assert title_block.title == "Test Project"
        assert title_block.date == "2024-01-15"
        assert title_block.revision == "1.2"
        assert title_block.company == "ACME Corp"
        assert len(title_block.comments) == 2
        assert title_block.comments[1] == "First comment"
        assert title_block.comments[2] == "Second comment"

        # Test round-trip includes all data
        result_sexpr = title_block.to_sexpr()
        assert [Symbol("title"), "Test Project"] in result_sexpr
        assert [Symbol("company"), "ACME Corp"] in result_sexpr


class TestUUID:
    """Test UUID class"""

    def test_uuid_creation(self):
        """Test creating UUID"""
        uuid_str = "12345678-1234-5678-9abc-123456789abc"
        uuid = UUID(uuid_str)
        assert uuid.uuid == uuid_str

    def test_uuid_from_sexpr(self):
        """Test parsing UUID from S-expression"""
        uuid_str = "12345678-1234-5678-9abc-123456789abc"
        sexpr = [Symbol("uuid"), uuid_str]
        uuid = UUID.from_sexpr(sexpr)
        assert uuid.uuid == uuid_str

    def test_uuid_to_sexpr(self):
        """Test converting UUID to S-expression"""
        uuid_str = "12345678-1234-5678-9abc-123456789abc"
        uuid = UUID(uuid_str)
        sexpr = uuid.to_sexpr()
        assert sexpr == [Symbol("uuid"), uuid_str]


class TestProperty:
    """Test Property class"""

    def test_property_creation(self):
        """Test creating property"""
        prop = Property("Reference", "U1")
        assert prop.key == "Reference"
        assert prop.value == "U1"

    def test_property_from_sexpr(self):
        """Test parsing property from S-expression"""
        sexpr = [Symbol("property"), "Reference", "U1"]
        prop = Property.from_sexpr(sexpr)
        assert prop.key == "Reference"
        assert prop.value == "U1"

    def test_property_to_sexpr(self):
        """Test converting property to S-expression"""
        prop = Property("Reference", "U1")
        sexpr = prop.to_sexpr()
        assert sexpr == [Symbol("property"), "Reference", "U1"]

    def test_property_comprehensive_parsing(self):
        """Test comprehensive property with all attributes"""
        # Based on spec: (property "KEY" "VALUE" (id N) POSITION_IDENTIFIER TEXT_EFFECTS)
        sexpr = [
            Symbol("property"),
            "Footprint",
            "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
            [Symbol("id"), 2],
            [Symbol("at"), 12.7, 25.4, 90],
            [
                Symbol("effects"),
                [Symbol("font"), [Symbol("size"), 1.0, 1.0]],
                Symbol("hide"),
            ],
        ]
        prop = Property.from_sexpr(sexpr)

        assert prop.key == "Footprint"
        assert prop.value == "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm"
        assert prop.id == 2
        assert prop.position is not None
        assert prop.position.x == 12.7
        assert prop.position.y == 25.4
        assert prop.position.angle == 90
        assert prop.effects is not None
        assert prop.effects.hide is True

    def test_property_minimal_parsing(self):
        """Test minimal property with key and value only"""
        # Based on spec: (property "KEY" "VALUE")
        sexpr = [Symbol("property"), "Reference", "U1"]
        prop = Property.from_sexpr(sexpr)

        assert prop.key == "Reference"
        assert prop.value == "U1"
        assert prop.id is None  # Default
        assert prop.position is None  # Default
        assert prop.effects is None  # Default

        # Test round-trip serialization
        result_sexpr = prop.to_sexpr()
        assert result_sexpr == [Symbol("property"), "Reference", "U1"]


class TestImageComprehensive:
    """Test Image class based on spec: (image POSITION [scale] [layer] UUID (data ...))"""

    def test_image_minimal(self):
        """Test minimal image with position and basic data"""
        # Based on spec: (image POSITION UUID (data ...))
        sexpr = [
            Symbol("image"),
            [Symbol("at"), 10, 20],
            [Symbol("uuid"), "550e8400-e29b-41d4-a716-446655440000"],
            [
                Symbol("data"),
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
            ],
        ]
        image = Image.from_sexpr(sexpr)

        assert image.position is not None
        assert image.position.x == 10
        assert image.position.y == 20
        assert image.scale is None  # Default
        assert image.uuid.uuid == "550e8400-e29b-41d4-a716-446655440000"
        assert len(image.data) > 0

    def test_image_comprehensive(self):
        """Test comprehensive image with all attributes"""
        # Based on spec: (image POSITION (scale SCALAR) (layer LAYER) UUID (data ...))
        sexpr = [
            Symbol("image"),
            [Symbol("at"), 15.24, 30.48],
            [Symbol("scale"), 2.5],
            [Symbol("layer"), "F.SilkS"],
            [Symbol("uuid"), "123e4567-e89b-12d3-a456-426614174000"],
            [
                Symbol("data"),
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
            ],
        ]
        image = Image.from_sexpr(sexpr)

        assert image.position.x == 15.24
        assert image.position.y == 30.48
        assert image.scale == 2.5
        assert "F.SilkS" in image.layers  # Layer handling varies by context
        assert image.uuid.uuid == "123e4567-e89b-12d3-a456-426614174000"
        assert len(image.data) > 0

        # Test round-trip includes scale
        result_sexpr = image.to_sexpr()
        assert [Symbol("scale"), 2.5] in result_sexpr


class TestUUIDComprehensive:
    """Test UUID class based on spec: (uuid UUID)"""

    def test_uuid_minimal(self):
        """Test minimal UUID with empty string"""
        uuid = UUID("")

        assert uuid.uuid == ""

        # Test round-trip serialization
        result_sexpr = uuid.to_sexpr()
        assert result_sexpr == [Symbol("uuid"), ""]

    def test_uuid_comprehensive(self):
        """Test comprehensive UUID with valid UUID string"""
        # Based on spec: (uuid UUID)
        sexpr = [Symbol("uuid"), "550e8400-e29b-41d4-a716-446655440000"]
        uuid = UUID.from_sexpr(sexpr)

        assert uuid.uuid == "550e8400-e29b-41d4-a716-446655440000"

        # Test round-trip serialization
        result_sexpr = uuid.to_sexpr()
        assert result_sexpr == [Symbol("uuid"), "550e8400-e29b-41d4-a716-446655440000"]


class TestSExprParser:
    """Test SExprParser utility class"""

    def test_find_token(self):
        """Test finding token in S-expression"""
        sexpr = [
            Symbol("symbol"),
            [Symbol("property"), "key", "value"],
            [Symbol("at"), 1, 2],
        ]
        token = SExprParser.find_token(sexpr, "property")
        assert token == [Symbol("property"), "key", "value"]

    def test_find_token_not_found(self):
        """Test finding non-existent token"""
        sexpr = [Symbol("symbol"), [Symbol("property"), "key", "value"]]
        token = SExprParser.find_token(sexpr, "missing")
        assert token is None

    def test_find_all_tokens(self):
        """Test finding all tokens of a type"""
        sexpr = [
            Symbol("symbol"),
            [Symbol("property"), "key1", "value1"],
            [Symbol("property"), "key2", "value2"],
        ]
        tokens = SExprParser.find_all_tokens(sexpr, "property")
        assert len(tokens) == 2
        assert tokens[0] == [Symbol("property"), "key1", "value1"]
        assert tokens[1] == [Symbol("property"), "key2", "value2"]

    def test_get_value(self):
        """Test getting value at index"""
        sexpr = ["a", "b", "c"]
        assert SExprParser.get_value(sexpr, 0) == "a"
        assert SExprParser.get_value(sexpr, 1) == "b"
        assert SExprParser.get_value(sexpr, 5, "default") == "default"

    def test_has_symbol(self):
        """Test checking for symbol presence"""
        sexpr = [
            Symbol("symbol"),
            Symbol("locked"),
            [Symbol("property"), "key", "value"],
        ]
        assert SExprParser.has_symbol(sexpr, "locked") is True
        assert SExprParser.has_symbol(sexpr, "missing") is False

    def test_safe_float(self):
        """Test safe float conversion"""
        assert SExprParser.safe_float(1.5) == 1.5
        assert SExprParser.safe_float("2.5") == 2.5
        assert SExprParser.safe_float("invalid", 0.0) == 0.0
        assert SExprParser.safe_float(None, 1.0) == 1.0

    def test_safe_int(self):
        """Test safe int conversion"""
        assert SExprParser.safe_int(5) == 5
        assert SExprParser.safe_int("10") == 10
        assert SExprParser.safe_int("invalid", 0) == 0
        assert SExprParser.safe_int(None, 5) == 5

    def test_safe_str(self):
        """Test safe string conversion"""
        assert SExprParser.safe_str("hello") == "hello"
        assert SExprParser.safe_str(123) == "123"
        assert SExprParser.safe_str(None, "default") == "default"
