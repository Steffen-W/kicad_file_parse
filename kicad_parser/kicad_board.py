"""
KiCad Board and Footprint S-Expression Classes

This module contains classes for board and footprint file formats,
including footprints, pads, zones, nets, and other board-specific items.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Sequence, Tuple, cast

from .kicad_board_elements import PadConnection, Zone, parse_zone_connect
from .kicad_common import (
    UUID,
    KiCadObject,
    Position,
    Property,
    SExpr,
    SExprParser,
    StrokeDefinition,
    Symbol,
    TextEffectsDefinition,
    parse_kicad_file,
    write_kicad_file,
)
from .kicad_graphics import (
    GraphicalArc,
    GraphicalCircle,
    GraphicalLine,
    GraphicalPolygon,
    GraphicalRectangle,
    GraphicalText,
)

# Layer definitions
CANONICAL_LAYER_NAMES = [
    "F.Cu",
    "In1.Cu",
    "In2.Cu",
    "In3.Cu",
    "In4.Cu",
    "In5.Cu",
    "In6.Cu",
    "In7.Cu",
    "In8.Cu",
    "In9.Cu",
    "In10.Cu",
    "In11.Cu",
    "In12.Cu",
    "In13.Cu",
    "In14.Cu",
    "In15.Cu",
    "In16.Cu",
    "In17.Cu",
    "In18.Cu",
    "In19.Cu",
    "In20.Cu",
    "In21.Cu",
    "In22.Cu",
    "In23.Cu",
    "In24.Cu",
    "In25.Cu",
    "In26.Cu",
    "In27.Cu",
    "In28.Cu",
    "In29.Cu",
    "In30.Cu",
    "B.Cu",
    "B.Adhes",
    "F.Adhes",
    "B.Paste",
    "F.Paste",
    "B.SilkS",
    "F.SilkS",
    "B.Mask",
    "F.Mask",
    "Dwgs.User",
    "Cmts.User",
    "Eco1.User",
    "Eco2.User",
    "Edge.Cuts",
    "F.CrtYd",
    "B.CrtYd",
    "F.Fab",
    "B.Fab",
    "User.1",
    "User.2",
    "User.3",
    "User.4",
    "User.5",
    "User.6",
    "User.7",
    "User.8",
    "User.9",
]


# Footprint types and enums
class FootprintType(Enum):
    """Footprint types"""

    SMD = "smd"
    THROUGH_HOLE = "through_hole"


class PadType(Enum):
    """Pad types"""

    THRU_HOLE = "thru_hole"
    SMD = "smd"
    CONNECT = "connect"
    NP_THRU_HOLE = "np_thru_hole"


class PadShape(Enum):
    """Pad shapes"""

    CIRCLE = "circle"
    RECT = "rect"
    OVAL = "oval"
    TRAPEZOID = "trapezoid"
    ROUNDRECT = "roundrect"
    CUSTOM = "custom"


class PadProperty(Enum):
    """Pad properties"""

    BGA = "pad_prop_bga"
    FIDUCIAL_GLOB = "pad_prop_fiducial_glob"
    FIDUCIAL_LOC = "pad_prop_fiducial_loc"
    TESTPOINT = "pad_prop_testpoint"
    HEATSINK = "pad_prop_heatsink"
    CASTELLATED = "pad_prop_castellated"


class CustomPadClearanceType(Enum):
    """Custom pad clearance types"""

    OUTLINE = "outline"
    CONVEXHULL = "convexhull"


class CustomPadAnchorShape(Enum):
    """Custom pad anchor shapes"""

    RECT = "rect"
    CIRCLE = "circle"


@dataclass
class FootprintOptions(KiCadObject):
    """Footprint options definition"""

    clearance: Optional[str] = None
    anchor: Optional[str] = None

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "FootprintOptions":
        return cls(
            clearance=SExprParser.get_optional_str(sexpr, "clearance"),
            anchor=SExprParser.get_optional_str(sexpr, "anchor"),
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("options")]
        if self.clearance:
            result.append([Symbol("clearance"), Symbol(self.clearance)])
        if self.anchor:
            result.append([Symbol("anchor"), Symbol(self.anchor)])
        return result


@dataclass
class CustomPadOptions(KiCadObject):
    """Custom pad options definition"""

    clearance: CustomPadClearanceType = CustomPadClearanceType.OUTLINE
    anchor: CustomPadAnchorShape = CustomPadAnchorShape.RECT

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "CustomPadOptions":
        clearance_str = SExprParser.get_optional_str(sexpr, "clearance")
        anchor_str = SExprParser.get_optional_str(sexpr, "anchor")

        clearance = (
            CustomPadClearanceType(clearance_str)
            if clearance_str
            else CustomPadClearanceType.OUTLINE
        )
        anchor = (
            CustomPadAnchorShape(anchor_str)
            if anchor_str
            else CustomPadAnchorShape.RECT
        )

        return cls(clearance=clearance, anchor=anchor)

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("options")]
        result.append([Symbol("clearance"), Symbol(self.clearance.value)])
        result.append([Symbol("anchor"), Symbol(self.anchor.value)])
        return result


@dataclass
class FootprintPrimitives(KiCadObject):
    """Footprint primitives definition"""

    width: Optional[float] = None
    fill: Optional[bool] = None
    lines: List[GraphicalLine] = field(default_factory=list)
    rectangles: List[GraphicalRectangle] = field(default_factory=list)
    circles: List[GraphicalCircle] = field(default_factory=list)
    arcs: List[GraphicalArc] = field(default_factory=list)
    polygons: List[GraphicalPolygon] = field(default_factory=list)

    @property
    def graphics(self) -> Sequence[KiCadObject]:
        """Return all graphics elements as a single list"""
        result: List[KiCadObject] = []
        result.extend(self.lines)
        result.extend(self.rectangles)
        result.extend(self.circles)
        result.extend(self.arcs)
        result.extend(self.polygons)
        return result

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "FootprintPrimitives":
        width = SExprParser.get_optional_float(sexpr, "width")
        fill_value = SExprParser.get_optional_str(sexpr, "fill")
        fill = fill_value == "yes" if fill_value is not None else None

        primitives = cls(width=width, fill=fill)

        for line_token in SExprParser.find_all_tokens(sexpr, "gr_line"):
            primitives.lines.append(GraphicalLine.from_sexpr(line_token))
        for rect_token in SExprParser.find_all_tokens(sexpr, "gr_rect"):
            primitives.rectangles.append(GraphicalRectangle.from_sexpr(rect_token))
        for circle_token in SExprParser.find_all_tokens(sexpr, "gr_circle"):
            primitives.circles.append(GraphicalCircle.from_sexpr(circle_token))
        for arc_token in SExprParser.find_all_tokens(sexpr, "gr_arc"):
            primitives.arcs.append(GraphicalArc.from_sexpr(arc_token))
        for poly_token in SExprParser.find_all_tokens(sexpr, "gr_poly"):
            primitives.polygons.append(GraphicalPolygon.from_sexpr(poly_token))

        return primitives

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("primitives")]

        if self.width is not None:
            result.append([Symbol("width"), self.width])
        if self.fill is not None:
            result.append([Symbol("fill"), Symbol("yes" if self.fill else "no")])

        for line in self.lines:
            result.append(line.to_sexpr())
        for rect in self.rectangles:
            result.append(rect.to_sexpr())
        for circle in self.circles:
            result.append(circle.to_sexpr())
        for arc in self.arcs:
            result.append(arc.to_sexpr())
        for polygon in self.polygons:
            result.append(polygon.to_sexpr())

        return result


@dataclass
class CustomPadPrimitives(KiCadObject):
    """Custom pad primitives definition"""

    width: float = 0.15
    fill: bool = False
    lines: List[GraphicalLine] = field(default_factory=list)
    rectangles: List[GraphicalRectangle] = field(default_factory=list)
    circles: List[GraphicalCircle] = field(default_factory=list)
    arcs: List[GraphicalArc] = field(default_factory=list)
    polygons: List[GraphicalPolygon] = field(default_factory=list)

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "CustomPadPrimitives":
        width = SExprParser.get_required_float(sexpr, "width", default=0.15)
        fill = SExprParser.get_optional_str(sexpr, "fill") == "yes"

        primitives = cls(width=width, fill=fill)

        for line_token in SExprParser.find_all_tokens(sexpr, "gr_line"):
            primitives.lines.append(GraphicalLine.from_sexpr(line_token))
        for rect_token in SExprParser.find_all_tokens(sexpr, "gr_rect"):
            primitives.rectangles.append(GraphicalRectangle.from_sexpr(rect_token))
        for circle_token in SExprParser.find_all_tokens(sexpr, "gr_circle"):
            primitives.circles.append(GraphicalCircle.from_sexpr(circle_token))
        for arc_token in SExprParser.find_all_tokens(sexpr, "gr_arc"):
            primitives.arcs.append(GraphicalArc.from_sexpr(arc_token))
        for poly_token in SExprParser.find_all_tokens(sexpr, "gr_poly"):
            primitives.polygons.append(GraphicalPolygon.from_sexpr(poly_token))

        return primitives

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("primitives")]

        for line in self.lines:
            result.append(line.to_sexpr())
        for rect in self.rectangles:
            result.append(rect.to_sexpr())
        for circle in self.circles:
            result.append(circle.to_sexpr())
        for arc in self.arcs:
            result.append(arc.to_sexpr())
        for poly in self.polygons:
            result.append(poly.to_sexpr())

        result.append([Symbol("width"), self.width])
        if self.fill:
            result.append([Symbol("fill"), Symbol("yes")])

        return result


class FootprintTextType(Enum):
    """Footprint text types"""

    REFERENCE = "reference"
    VALUE = "value"
    USER = "user"


@dataclass
class FootprintText(GraphicalText):
    """Footprint text with type information"""

    type: FootprintTextType = FootprintTextType.USER
    unlocked: Optional[bool] = None
    hide: Optional[bool] = None

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "FootprintText":
        text_type = SExprParser.parse_enum(
            SExprParser.get_value(sexpr, 1), FootprintTextType, FootprintTextType.USER
        )

        text = SExprParser.normalize_text_content(
            str(SExprParser.get_value(sexpr, 2, ""))
        )

        layer_token = SExprParser.find_token(sexpr, "layer")
        uuid_token = SExprParser.find_token(sexpr, "uuid")
        effects_token = SExprParser.find_token(sexpr, "effects")

        knockout = False
        layer = "F.SilkS"
        if layer_token:
            layer = str(SExprParser.get_value(layer_token, 1, "F.SilkS"))
            knockout = SExprParser.has_symbol(layer_token, "knockout")

        # Parse position with angle support
        at_token = SExprParser.find_token(sexpr, "at")
        position = Position.from_sexpr(at_token)

        return cls(
            type=text_type,
            text=text,
            position=position,
            layer=layer,
            knockout=knockout,
            uuid=UUID.from_sexpr(uuid_token) if uuid_token else None,
            effects=(
                TextEffectsDefinition.from_sexpr(effects_token)
                if effects_token
                else TextEffectsDefinition()
            ),
            unlocked=SExprParser.get_optional_bool_flag(sexpr, "unlocked"),
            hide=SExprParser.get_optional_bool_flag(sexpr, "hide"),
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("fp_text"), Symbol(self.type.value)]
        result.extend(super().to_sexpr()[1:])

        if self.unlocked is not None and self.unlocked:
            result.insert(-1, Symbol("unlocked"))
        if self.hide is not None and self.hide:
            result.insert(-1, Symbol("hide"))

        return result


@dataclass
class FootprintLine(GraphicalLine):
    """Footprint line"""

    locked: Optional[bool] = None

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "FootprintLine":
        base = GraphicalLine.from_sexpr(sexpr)
        return cls(
            start=base.start,
            end=base.end,
            angle=base.angle,
            layer=base.layer,
            stroke=base.stroke,
            uuid=base.uuid,
            locked=SExprParser.get_optional_bool_flag(sexpr, "locked"),
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("fp_line")]
        result.extend(super().to_sexpr()[1:])

        if self.locked is not None and self.locked:
            result.insert(-1, Symbol("locked"))

        return result


# Footprint-specific graphics classes with correct tokens


@dataclass
class FootprintRectangle(KiCadObject):
    """Footprint rectangle definition.

    The 'fp_rect' token defines a graphic rectangle in a footprint definition in the format:
    (fp_rect
        (start X Y)
        (end X Y)
        (layer LAYER_DEFINITION)
        (width WIDTH)
        STROKE_DEFINITION
        [(fill yes | no)]
        [(locked)]
        (uuid UUID)
    )

    Where:
        start: Coordinates of the upper left corner of the rectangle
        end: Coordinates of the lower right corner of the rectangle
        layer: Canonical layer the rectangle resides on
        width: Line width of the rectangle (prior to version 7)
        STROKE_DEFINITION: Line width and style of the rectangle (from version 7)
        fill: Optional flag defining if the rectangle is filled
        locked: Optional flag defining if the rectangle cannot be edited
        uuid: Unique identifier of the rectangle object
    """

    __token_name__ = "fp_rect"

    start: Position = field(default_factory=Position)
    end: Position = field(default_factory=Position)
    layer: Optional[str] = None
    width: Optional[float] = None
    stroke: Optional[StrokeDefinition] = None
    fill: bool = False
    locked: bool = False
    uuid: Optional[UUID] = None

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "FootprintRectangle":
        if not sexpr:
            return cls()

        start_token = SExprParser.find_token(sexpr, "start")
        start = (
            Position(
                SExprParser.safe_float(SExprParser.get_value(start_token, 1)),
                SExprParser.safe_float(SExprParser.get_value(start_token, 2)),
            )
            if start_token
            else Position()
        )

        end_token = SExprParser.find_token(sexpr, "end")
        end = (
            Position(
                SExprParser.safe_float(SExprParser.get_value(end_token, 1)),
                SExprParser.safe_float(SExprParser.get_value(end_token, 2)),
            )
            if end_token
            else Position()
        )

        stroke_token = SExprParser.find_token(sexpr, "stroke")
        stroke = StrokeDefinition.from_sexpr(stroke_token) if stroke_token else None

        fill_token = SExprParser.find_token(sexpr, "fill")
        fill = False
        if fill_token and len(fill_token) > 1:
            fill = str(fill_token[1]) == "yes"

        uuid_token = SExprParser.find_token(sexpr, "uuid")
        uuid_obj = UUID.from_sexpr(uuid_token) if uuid_token else None

        return cls(
            start=start,
            end=end,
            layer=SExprParser.get_optional_str(sexpr, "layer"),
            width=SExprParser.get_optional_float(sexpr, "width"),
            stroke=stroke,
            fill=fill,
            locked=SExprParser.has_symbol(sexpr, "locked"),
            uuid=uuid_obj,
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol(self.__token_name__)]
        result.append([Symbol("start"), self.start.x, self.start.y])
        result.append([Symbol("end"), self.end.x, self.end.y])

        if self.layer:
            result.append([Symbol("layer"), self.layer])
        if self.width is not None:
            result.append([Symbol("width"), self.width])
        if self.stroke:
            result.append(self.stroke.to_sexpr())
        if self.fill:
            result.append([Symbol("fill"), Symbol("yes")])
        if self.locked:
            result.append(Symbol("locked"))
        if self.uuid:
            result.append(self.uuid.to_sexpr())

        return result


@dataclass
class FootprintCircle(KiCadObject):
    """Footprint circle definition.

    The 'fp_circle' token defines a graphic circle in a footprint definition in the format:
    (fp_circle
        (center X Y)
        (end X Y)
        (layer LAYER_DEFINITION)
        (width WIDTH)
        STROKE_DEFINITION
        [(fill yes | no)]
        [(locked)]
        (uuid UUID)
    )

    Where:
        center: Coordinates of the center of the circle
        end: Coordinates of the end of the radius of the circle
        layer: Canonical layer the circle resides on
        width: Line width of the circle (prior to version 7)
        STROKE_DEFINITION: Line width and style of the circle (from version 7)
        fill: Optional flag defining if the circle is filled
        locked: Optional flag defining if the circle cannot be edited
        uuid: Unique identifier of the circle object
    """

    __token_name__ = "fp_circle"

    center: Position = field(default_factory=Position)
    end: Position = field(default_factory=Position)
    layer: Optional[str] = None
    width: Optional[float] = None
    stroke: Optional[StrokeDefinition] = None
    fill: bool = False
    locked: bool = False
    uuid: Optional[UUID] = None

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "FootprintCircle":
        if not sexpr:
            return cls()

        center_token = SExprParser.find_token(sexpr, "center")
        center = (
            Position(
                SExprParser.safe_float(SExprParser.get_value(center_token, 1)),
                SExprParser.safe_float(SExprParser.get_value(center_token, 2)),
            )
            if center_token
            else Position()
        )

        end_token = SExprParser.find_token(sexpr, "end")
        end = (
            Position(
                SExprParser.safe_float(SExprParser.get_value(end_token, 1)),
                SExprParser.safe_float(SExprParser.get_value(end_token, 2)),
            )
            if end_token
            else Position()
        )

        stroke_token = SExprParser.find_token(sexpr, "stroke")
        stroke = StrokeDefinition.from_sexpr(stroke_token) if stroke_token else None

        fill_token = SExprParser.find_token(sexpr, "fill")
        fill = False
        if fill_token and len(fill_token) > 1:
            fill = str(fill_token[1]) == "yes"

        uuid_token = SExprParser.find_token(sexpr, "uuid")
        uuid_obj = UUID.from_sexpr(uuid_token) if uuid_token else None

        return cls(
            center=center,
            end=end,
            layer=SExprParser.get_optional_str(sexpr, "layer"),
            width=SExprParser.get_optional_float(sexpr, "width"),
            stroke=stroke,
            fill=fill,
            locked=SExprParser.has_symbol(sexpr, "locked"),
            uuid=uuid_obj,
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol(self.__token_name__)]
        result.append([Symbol("center"), self.center.x, self.center.y])
        result.append([Symbol("end"), self.end.x, self.end.y])

        if self.layer:
            result.append([Symbol("layer"), self.layer])
        if self.width is not None:
            result.append([Symbol("width"), self.width])
        if self.stroke:
            result.append(self.stroke.to_sexpr())
        if self.fill:
            result.append([Symbol("fill"), Symbol("yes")])
        if self.locked:
            result.append(Symbol("locked"))
        if self.uuid:
            result.append(self.uuid.to_sexpr())

        return result


@dataclass
class FootprintArc(KiCadObject):
    """Footprint arc definition.

    The 'fp_arc' token defines a graphic arc in a footprint definition in the format:
    (fp_arc
        (start X Y)
        (mid X Y)
        (end X Y)
        (layer LAYER_DEFINITION)
        (width WIDTH)
        STROKE_DEFINITION
        [(locked)]
        (uuid UUID)
    )

    Where:
        start: Coordinates of the start position of the arc radius
        mid: Coordinates of the midpoint along the arc
        end: Coordinates of the end position of the arc radius
        layer: Canonical layer the arc resides on
        width: Line width of the arc (prior to version 7)
        STROKE_DEFINITION: Line width and style of the arc (from version 7)
        locked: Optional flag defining if the arc cannot be edited
        uuid: Unique identifier of the arc object
    """

    __token_name__ = "fp_arc"

    start: Position = field(default_factory=Position)
    mid: Position = field(default_factory=Position)
    end: Position = field(default_factory=Position)
    layer: Optional[str] = None
    width: Optional[float] = None
    stroke: Optional["StrokeDefinition"] = None
    locked: bool = False
    uuid: Optional["UUID"] = None

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "FootprintArc":
        if not sexpr:
            return cls()

        start_token = SExprParser.find_token(sexpr, "start")
        start = (
            Position(
                SExprParser.safe_float(SExprParser.get_value(start_token, 1)),
                SExprParser.safe_float(SExprParser.get_value(start_token, 2)),
            )
            if start_token
            else Position()
        )

        mid_token = SExprParser.find_token(sexpr, "mid")
        mid = (
            Position(
                SExprParser.safe_float(SExprParser.get_value(mid_token, 1)),
                SExprParser.safe_float(SExprParser.get_value(mid_token, 2)),
            )
            if mid_token
            else Position()
        )

        end_token = SExprParser.find_token(sexpr, "end")
        end = (
            Position(
                SExprParser.safe_float(SExprParser.get_value(end_token, 1)),
                SExprParser.safe_float(SExprParser.get_value(end_token, 2)),
            )
            if end_token
            else Position()
        )

        stroke_token = SExprParser.find_token(sexpr, "stroke")
        stroke = StrokeDefinition.from_sexpr(stroke_token) if stroke_token else None

        uuid_token = SExprParser.find_token(sexpr, "uuid")
        uuid_obj = UUID.from_sexpr(uuid_token) if uuid_token else None

        return cls(
            start=start,
            mid=mid,
            end=end,
            layer=SExprParser.get_optional_str(sexpr, "layer"),
            width=SExprParser.get_optional_float(sexpr, "width"),
            stroke=stroke,
            locked=SExprParser.has_symbol(sexpr, "locked"),
            uuid=uuid_obj,
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol(self.__token_name__)]
        result.append([Symbol("start"), self.start.x, self.start.y])
        result.append([Symbol("mid"), self.mid.x, self.mid.y])
        result.append([Symbol("end"), self.end.x, self.end.y])

        if self.layer:
            result.append([Symbol("layer"), self.layer])
        if self.width is not None:
            result.append([Symbol("width"), self.width])
        if self.stroke:
            result.append(self.stroke.to_sexpr())
        if self.locked:
            result.append(Symbol("locked"))
        if self.uuid:
            result.append(self.uuid.to_sexpr())

        return result


@dataclass
class FootprintPolygon(GraphicalPolygon):
    """Footprint polygon - uses fp_poly token"""

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("fp_poly")]
        result.append(self.points.to_sexpr())
        result.append([Symbol("layer"), self.layer])
        result.append(self.stroke.to_sexpr())

        if self.fill:
            result.append([Symbol("fill"), Symbol("yes")])

        if self.uuid:
            result.append(self.uuid.to_sexpr())

        return result


@dataclass
class Net:
    """Net definition"""

    number: int
    name: str

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "Net":
        return cls(
            number=SExprParser.safe_get_int(sexpr, 1, 0),
            name=SExprParser.safe_get_str(sexpr, 2, ""),
        )

    def to_sexpr(self) -> SExpr:
        return [Symbol("net"), self.number, self.name]


@dataclass
class Drill(KiCadObject):
    """Drill definition for pads"""

    oval: bool = False
    diameter: float = 0.8
    width: Optional[float] = None
    diameter_y: Optional[float] = None
    offset: Optional[Position] = None

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "Drill":
        oval = SExprParser.has_symbol(sexpr, "oval")
        diameter = SExprParser.safe_float(
            SExprParser.get_value(sexpr, 1 if not oval else 2), 0.8
        )
        width = None
        diameter_y = None
        if oval and len(sexpr) > 2:
            width = float(sexpr[2])
            diameter_y = float(sexpr[2])
        if oval and len(sexpr) > 3:
            diameter_y = float(sexpr[3])

        offset_token = SExprParser.find_token(sexpr, "offset")
        offset = None
        if offset_token:
            offset = Position.from_sexpr(offset_token)

        return cls(
            oval=oval,
            diameter=diameter,
            width=width,
            diameter_y=diameter_y,
            offset=offset,
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("drill")]
        if self.oval:
            result.append(Symbol("oval"))
        result.append(self.diameter)
        if self.diameter_y is not None:
            result.append(self.diameter_y)
        elif self.width is not None:
            result.append(self.width)
        if self.offset:
            result.append([Symbol("offset"), self.offset.x, self.offset.y])
        return result


@dataclass
class DrillDefinition:
    """Drill definition for pads"""

    oval: bool = False
    diameter: float = 0.8
    width: Optional[float] = None
    offset: Optional[Position] = None

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "DrillDefinition":
        oval = SExprParser.has_symbol(sexpr, "oval")
        diameter = SExprParser.safe_float(
            SExprParser.get_value(sexpr, 1 if not oval else 2), 0.8
        )
        width = None
        if oval and len(sexpr) > 2:
            width = float(sexpr[2])

        offset_token = SExprParser.find_token(sexpr, "offset")
        offset = None
        if offset_token:
            offset = Position.from_sexpr(offset_token)

        return cls(oval=oval, diameter=diameter, width=width, offset=offset)

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("drill")]
        if self.oval:
            result.append(Symbol("oval"))
        result.append(self.diameter)
        if self.width is not None:
            result.append(self.width)
        if self.offset:
            result.append([Symbol("offset"), self.offset.x, self.offset.y])
        return result


@dataclass
class PadAttribute(KiCadObject):
    """Pad attribute definition"""

    type: FootprintType
    board_only: bool = False
    exclude_from_pos_files: bool = False
    exclude_from_bom: bool = False

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "PadAttribute":
        type_str = str(SExprParser.get_value(sexpr, 1, "smd"))
        attr_type = FootprintType(type_str)

        attrs = cls(type=attr_type)

        for item in sexpr[2:]:
            if item == Symbol("board_only"):
                attrs.board_only = True
            elif item == Symbol("exclude_from_pos_files"):
                attrs.exclude_from_pos_files = True
            elif item == Symbol("exclude_from_bom"):
                attrs.exclude_from_bom = True

        return attrs

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("attr"), Symbol(self.type.value)]

        if self.board_only:
            result.append(Symbol("board_only"))
        if self.exclude_from_pos_files:
            result.append(Symbol("exclude_from_pos_files"))
        if self.exclude_from_bom:
            result.append(Symbol("exclude_from_bom"))

        return result


@dataclass
class FootprintAttributes:
    """Footprint attributes"""

    type: FootprintType = FootprintType.THROUGH_HOLE
    board_only: bool = False
    exclude_from_pos_files: bool = False
    exclude_from_bom: bool = False

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "FootprintAttributes":
        attrs = cls()

        for item in sexpr[1:]:
            if item == Symbol("smd"):
                attrs.type = FootprintType.SMD
            elif item == Symbol("through_hole"):
                attrs.type = FootprintType.THROUGH_HOLE
            elif item == Symbol("board_only"):
                attrs.board_only = True
            elif item == Symbol("exclude_from_pos_files"):
                attrs.exclude_from_pos_files = True
            elif item == Symbol("exclude_from_bom"):
                attrs.exclude_from_bom = True

        return attrs

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("attr"), Symbol(self.type.value)]

        if self.board_only:
            result.append(Symbol("board_only"))
        if self.exclude_from_pos_files:
            result.append(Symbol("exclude_from_pos_files"))
        if self.exclude_from_bom:
            result.append(Symbol("exclude_from_bom"))

        return result


@dataclass
class FootprintPad(KiCadObject):
    """Footprint pad definition"""

    number: str
    type: PadType
    shape: PadShape
    position: Position
    locked: Optional[bool] = None
    size: Tuple[float, float] = (1.5, 1.5)
    drill: Optional[DrillDefinition] = None
    layers: List[str] = field(default_factory=lambda: ["F.Cu", "F.Mask"])
    property: Optional[PadProperty] = None
    remove_unused_layers: bool = False
    keep_end_layers: bool = False
    roundrect_rratio: Optional[float] = None
    chamfer_ratio: Optional[float] = None
    chamfer_corners: List[str] = field(default_factory=list)
    net: Optional[Net] = None
    uuid: Optional[UUID] = None
    pin_function: Optional[str] = None
    pin_type: Optional[str] = None
    pintype: Optional[str] = None
    die_length: Optional[float] = None
    solder_mask_margin: Optional[float] = None
    solder_paste_margin: Optional[float] = None
    solder_paste_margin_ratio: Optional[float] = None
    clearance: Optional[float] = None
    zone_connect: Optional[PadConnection] = None
    thermal_width: Optional[float] = None
    thermal_gap: Optional[float] = None

    # Custom pad support
    custom_options: Optional[CustomPadOptions] = None
    custom_primitives: Optional[CustomPadPrimitives] = None

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "FootprintPad":
        number = SExprParser.safe_get_str(sexpr, 1, "")
        pad_type_str = SExprParser.safe_str(
            SExprParser.get_value(sexpr, 2), "thru_hole"
        )
        shape_str = SExprParser.safe_get_str(sexpr, 3, "circle")

        pad_type = PadType(pad_type_str)
        shape = PadShape(shape_str)

        at_token = SExprParser.find_token(sexpr, "at")
        size_token = SExprParser.find_token(sexpr, "size")
        drill_token = SExprParser.find_token(sexpr, "drill")
        layers_token = SExprParser.find_token(sexpr, "layers")
        property_token = SExprParser.find_token(sexpr, "property")
        net_token = SExprParser.find_token(sexpr, "net")
        uuid_token = SExprParser.find_token(sexpr, "uuid")

        # Advanced pad features
        chamfer_token = SExprParser.find_token(sexpr, "chamfer")

        # Custom pad tokens
        options_token = SExprParser.find_token(sexpr, "options")
        primitives_token = SExprParser.find_token(sexpr, "primitives")

        # Parse layers
        layers = ["F.Cu", "F.Mask"]
        if layers_token and len(layers_token) > 1:
            layers = [str(layer) for layer in layers_token[1:]]

        # Parse size
        size = (1.5, 1.5)
        if size_token:
            size = (
                float(SExprParser.get_value(size_token, 1, 1.5)),
                float(SExprParser.get_value(size_token, 2, 1.5)),
            )

        # Parse property
        pad_property = None
        if property_token:
            pad_property = PadProperty(str(property_token[1]))

        # Parse net
        net = None
        if net_token and len(net_token) >= 3:
            net = Net(number=int(net_token[1]), name=str(net_token[2]))

        # Parse chamfer corners
        chamfer_corners = []
        if chamfer_token and len(chamfer_token) > 1:
            chamfer_corners = [str(corner) for corner in chamfer_token[1:]]

        return cls(
            number=number,
            type=pad_type,
            shape=shape,
            position=Position.from_sexpr(at_token),
            locked=SExprParser.get_optional_bool_flag(sexpr, "locked"),
            size=size,
            drill=DrillDefinition.from_sexpr(drill_token) if drill_token else None,
            layers=layers,
            property=pad_property,
            remove_unused_layers=SExprParser.has_symbol(sexpr, "remove_unused_layers"),
            keep_end_layers=SExprParser.has_symbol(sexpr, "keep_end_layers"),
            roundrect_rratio=SExprParser.get_optional_float(sexpr, "roundrect_rratio"),
            chamfer_ratio=SExprParser.get_optional_float(sexpr, "chamfer_ratio"),
            chamfer_corners=chamfer_corners,
            net=net,
            uuid=UUID.from_sexpr(uuid_token) if uuid_token else None,
            pin_function=SExprParser.get_optional_str(sexpr, "pin_function"),
            pin_type=SExprParser.get_optional_str(sexpr, "pin_type"),
            pintype=SExprParser.get_optional_str(sexpr, "pintype"),
            die_length=SExprParser.get_optional_float(sexpr, "die_length"),
            solder_mask_margin=SExprParser.get_optional_float(
                sexpr, "solder_mask_margin"
            ),
            solder_paste_margin=SExprParser.get_optional_float(
                sexpr, "solder_paste_margin"
            ),
            solder_paste_margin_ratio=SExprParser.get_optional_float(
                sexpr, "solder_paste_margin_ratio"
            ),
            clearance=SExprParser.get_optional_float(sexpr, "clearance"),
            zone_connect=parse_zone_connect(sexpr),
            thermal_width=SExprParser.get_optional_float(sexpr, "thermal_width"),
            thermal_gap=SExprParser.get_optional_float(sexpr, "thermal_gap"),
            custom_options=(
                CustomPadOptions.from_sexpr(options_token) if options_token else None
            ),
            custom_primitives=(
                CustomPadPrimitives.from_sexpr(primitives_token)
                if primitives_token
                else None
            ),
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [
            Symbol("pad"),
            self.number,
            Symbol(self.type.value),
            Symbol(self.shape.value),
        ]
        result.append(self.position.to_sexpr())

        if self.locked is not None and self.locked:
            result.append(Symbol("locked"))

        result.append([Symbol("size"), self.size[0], self.size[1]])

        if self.drill:
            result.append(self.drill.to_sexpr())

        result.append([Symbol("layers")] + [Symbol(layer) for layer in self.layers])

        if self.property:
            result.append([Symbol("property"), Symbol(self.property.value)])

        if self.remove_unused_layers:
            result.append(Symbol("remove_unused_layers"))

        if self.keep_end_layers:
            result.append(Symbol("keep_end_layers"))

        # Add advanced pad attributes
        if self.roundrect_rratio is not None:
            result.append([Symbol("roundrect_rratio"), self.roundrect_rratio])

        if self.chamfer_ratio is not None:
            result.append([Symbol("chamfer_ratio"), self.chamfer_ratio])

        if self.chamfer_corners:
            result.append(
                [Symbol("chamfer")]
                + [Symbol(corner) for corner in self.chamfer_corners]
            )

        if self.pin_function:
            result.append([Symbol("pin_function"), self.pin_function])

        if self.pin_type:
            result.append([Symbol("pin_type"), self.pin_type])
        if self.pintype:
            result.append([Symbol("pintype"), self.pintype])

        if self.die_length is not None:
            result.append([Symbol("die_length"), self.die_length])

        if self.solder_mask_margin is not None:
            result.append([Symbol("solder_mask_margin"), self.solder_mask_margin])

        if self.solder_paste_margin is not None:
            result.append([Symbol("solder_paste_margin"), self.solder_paste_margin])

        if self.solder_paste_margin_ratio is not None:
            result.append(
                [Symbol("solder_paste_margin_ratio"), self.solder_paste_margin_ratio]
            )

        if self.clearance is not None:
            result.append([Symbol("clearance"), self.clearance])

        if self.zone_connect is not None:
            result.append([Symbol("zone_connect"), Symbol(self.zone_connect.value)])

        if self.thermal_width is not None:
            result.append([Symbol("thermal_width"), self.thermal_width])

        if self.thermal_gap is not None:
            result.append([Symbol("thermal_gap"), self.thermal_gap])

        if self.net:
            result.append(self.net.to_sexpr())

        if self.uuid:
            result.append(self.uuid.to_sexpr())

        # Add custom pad options and primitives
        if self.custom_options:
            result.append(self.custom_options.to_sexpr())

        if self.custom_primitives:
            result.append(self.custom_primitives.to_sexpr())

        return result


class KeepoutType(Enum):
    """Keepout types"""

    ALLOWED = "allowed"
    NOT_ALLOWED = "not_allowed"


@dataclass
class KeepoutSettings(KiCadObject):
    """Zone keepout settings"""

    tracks: KeepoutType = KeepoutType.NOT_ALLOWED
    vias: KeepoutType = KeepoutType.NOT_ALLOWED
    pads: KeepoutType = KeepoutType.NOT_ALLOWED
    copperpour: KeepoutType = KeepoutType.NOT_ALLOWED
    footprints: KeepoutType = KeepoutType.NOT_ALLOWED

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "KeepoutSettings":
        tracks_token = SExprParser.find_token(sexpr, "tracks")
        vias_token = SExprParser.find_token(sexpr, "vias")
        pads_token = SExprParser.find_token(sexpr, "pads")
        copperpour_token = SExprParser.find_token(sexpr, "copperpour")
        footprints_token = SExprParser.find_token(sexpr, "footprints")

        tracks = None
        if tracks_token:
            tracks = KeepoutType(str(tracks_token[1]))

        vias = None
        if vias_token:
            vias = KeepoutType(str(vias_token[1]))

        pads = None
        if pads_token:
            pads = KeepoutType(str(pads_token[1]))

        copperpour = None
        if copperpour_token:
            copperpour = KeepoutType(str(copperpour_token[1]))

        footprints = None
        if footprints_token:
            footprints = KeepoutType(str(footprints_token[1]))

        return cls(
            tracks=tracks or KeepoutType.NOT_ALLOWED,
            vias=vias or KeepoutType.NOT_ALLOWED,
            pads=pads or KeepoutType.NOT_ALLOWED,
            copperpour=copperpour or KeepoutType.NOT_ALLOWED,
            footprints=footprints or KeepoutType.NOT_ALLOWED,
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("keepout")]
        result.append([Symbol("tracks"), Symbol(self.tracks.value)])
        result.append([Symbol("vias"), Symbol(self.vias.value)])
        result.append([Symbol("pads"), Symbol(self.pads.value)])
        result.append([Symbol("copperpour"), Symbol(self.copperpour.value)])
        result.append([Symbol("footprints"), Symbol(self.footprints.value)])
        return result


@dataclass
class KeepoutZone(KiCadObject):
    """Keepout zone definition"""

    tracks: Optional[KeepoutType] = None
    vias: Optional[KeepoutType] = None
    pads: Optional[KeepoutType] = None
    copperpour: Optional[KeepoutType] = None
    footprints: Optional[KeepoutType] = None

    @property
    def tracks_allowed(self) -> Optional[bool]:
        """Convert tracks enum to boolean for compatibility"""
        if self.tracks is None:
            return None
        elif self.tracks == KeepoutType.NOT_ALLOWED:
            return False
        elif self.tracks == KeepoutType.ALLOWED:
            return True

    @property
    def vias_allowed(self) -> Optional[bool]:
        """Convert vias enum to boolean for compatibility"""
        if self.vias is None:
            return None
        elif self.vias == KeepoutType.NOT_ALLOWED:
            return False
        elif self.vias == KeepoutType.ALLOWED:
            return True

    @property
    def pads_allowed(self) -> Optional[bool]:
        """Convert pads enum to boolean for compatibility"""
        if self.pads is None:
            return None
        elif self.pads == KeepoutType.NOT_ALLOWED:
            return False
        elif self.pads == KeepoutType.ALLOWED:
            return True

    @property
    def copperpour_allowed(self) -> Optional[bool]:
        """Convert copperpour enum to boolean for compatibility"""
        if self.copperpour is None:
            return None
        elif self.copperpour == KeepoutType.NOT_ALLOWED:
            return False
        elif self.copperpour == KeepoutType.ALLOWED:
            return True

    @property
    def footprints_allowed(self) -> Optional[bool]:
        """Convert footprints enum to boolean for compatibility"""
        if self.footprints is None:
            return None
        elif self.footprints == KeepoutType.NOT_ALLOWED:
            return False
        elif self.footprints == KeepoutType.ALLOWED:
            return True

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "KeepoutZone":
        tracks_token = SExprParser.find_token(sexpr, "tracks")
        vias_token = SExprParser.find_token(sexpr, "vias")
        pads_token = SExprParser.find_token(sexpr, "pads")
        copperpour_token = SExprParser.find_token(sexpr, "copperpour")
        footprints_token = SExprParser.find_token(sexpr, "footprints")

        tracks = None
        if tracks_token:
            tracks = KeepoutType(str(tracks_token[1]))

        vias = None
        if vias_token:
            vias = KeepoutType(str(vias_token[1]))

        pads = None
        if pads_token:
            pads = KeepoutType(str(pads_token[1]))

        copperpour = None
        if copperpour_token:
            copperpour = KeepoutType(str(copperpour_token[1]))

        footprints = None
        if footprints_token:
            footprints = KeepoutType(str(footprints_token[1]))

        return cls(
            tracks=tracks,
            vias=vias,
            pads=pads,
            copperpour=copperpour,
            footprints=footprints,
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("keepout")]
        if self.tracks:
            result.append([Symbol("tracks"), Symbol(self.tracks.value)])
        if self.vias:
            result.append([Symbol("vias"), Symbol(self.vias.value)])
        if self.pads:
            result.append([Symbol("pads"), Symbol(self.pads.value)])
        if self.copperpour:
            result.append([Symbol("copperpour"), Symbol(self.copperpour.value)])
        if self.footprints:
            result.append([Symbol("footprints"), Symbol(self.footprints.value)])
        return result


@dataclass
class FootprintGroup(KiCadObject):
    """Footprint group of objects"""

    name: str
    id: Optional[str] = None
    members: List[str] = field(default_factory=list)

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "FootprintGroup":
        name = SExprParser.safe_get_str(sexpr, 1, "")
        group = cls(
            name=name,
            id=SExprParser.get_optional_str(sexpr, "id"),
        )

        # Parse member UUIDs
        members_token = SExprParser.find_token(sexpr, "members")
        if members_token and len(members_token) > 1:
            for member_id in members_token[1:]:
                if isinstance(member_id, str):
                    group.members.append(member_id)

        return group

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("group"), self.name]
        if self.id:
            result.append([Symbol("id"), self.id])

        if self.members:
            members_list: SExpr = [Symbol("members")]
            for member in self.members:
                members_list.append(member)
            result.append(members_list)

        return result


@dataclass
class Group(KiCadObject):
    """Group of objects"""

    name: str
    id: UUID
    members: List[UUID] = field(default_factory=list)

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "Group":
        name = SExprParser.safe_get_str(sexpr, 1, "")
        id_token = SExprParser.find_token(sexpr, "id")

        if not id_token:
            raise ValueError("Group must have an ID")

        group = cls(
            name=name,
            id=UUID.from_sexpr(id_token),
        )

        # Parse member UUIDs
        members_token = SExprParser.find_token(sexpr, "members")
        if members_token and len(members_token) > 1:
            for member_id in members_token[1:]:
                if isinstance(member_id, str):
                    group.members.append(UUID(member_id))

        return group

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("group"), self.name]
        result.append([Symbol("id"), self.id.uuid])

        if self.members:
            members_list: SExpr = [Symbol("members")]
            for member in self.members:
                members_list.append(member.uuid)
            result.append(members_list)

        return result


@dataclass
class Model3D(KiCadObject):
    """3D model definition with advanced features"""

    filename: str
    at: Position = field(default_factory=Position)
    scale: Optional[Position] = None
    rotate: Optional[Position] = None
    hide: bool = False
    opacity: Optional[float] = None
    offset: Optional[Position] = None

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "Model3D":
        filename = SExprParser.safe_get_str(sexpr, 1, "")
        at_token = SExprParser.find_token(sexpr, "at")
        scale_token = SExprParser.find_token(sexpr, "scale")
        rotate_token = SExprParser.find_token(sexpr, "rotate")
        offset_token = SExprParser.find_token(sexpr, "offset")
        hide = SExprParser.has_symbol(sexpr, "hide")
        at = Position.from_sexpr(at_token)
        scale = (
            Position(x=1, y=1, z=1)
            if not scale_token
            else Position.from_sexpr(scale_token)
        )
        rotate = Position.from_sexpr(rotate_token)
        offset = None if not offset_token else Position.from_sexpr(offset_token)

        opacity = SExprParser.get_optional_float(sexpr, "opacity")

        return cls(
            filename=filename,
            at=at,
            scale=scale,
            rotate=rotate,
            hide=hide,
            opacity=opacity,
            offset=offset,
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("model"), self.filename]

        if self.at and (
            self.at.x != 0
            or self.at.y != 0
            or (self.at.z is not None and self.at.z != 0)
        ):
            result.append(self.at.to_sexpr("at"))
        if self.scale and (
            self.scale.x != 1
            or self.scale.y != 1
            or (self.scale.z is not None and self.scale.z != 1)
        ):
            result.append(self.scale.to_sexpr("scale"))
        if self.rotate and (
            self.rotate.x != 0
            or self.rotate.y != 0
            or (self.rotate.z is not None and self.rotate.z != 0)
        ):
            result.append(self.rotate.to_sexpr("rotate"))
        if self.offset and (
            self.offset.x != 0
            or self.offset.y != 0
            or (self.offset.z is not None and self.offset.z != 0)
        ):
            result.append(self.offset.to_sexpr("offset"))
        if self.hide:
            result.append(Symbol("hide"))
        if self.opacity is not None:
            result.append([Symbol("opacity"), self.opacity])

        return result


@dataclass
class Footprint3DModel:
    """3D model definition with advanced features"""

    filename: str
    at: Position = field(default_factory=Position)
    scale: Position = field(default_factory=lambda: Position(1, 1, 1))
    rotate: Position = field(default_factory=Position)

    # Advanced 3D model features
    hide: bool = False  # Hide model in 3D viewer
    opacity: Optional[float] = None  # Model opacity (0.0-1.0)
    offset: Optional[Position] = None  # Additional offset for model positioning

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "Footprint3DModel":
        filename = SExprParser.safe_get_str(sexpr, 1, "")
        at_token = SExprParser.find_token(sexpr, "at")
        scale_token = SExprParser.find_token(sexpr, "scale")
        rotate_token = SExprParser.find_token(sexpr, "rotate")

        # Advanced 3D model features
        hide_token = SExprParser.find_token(sexpr, "hide")
        offset_token = SExprParser.find_token(sexpr, "offset")

        # Parse 3D positions (xyz format)
        at_pos = Position(0, 0, 0)
        if at_token:
            xyz_token = SExprParser.find_token(at_token, "xyz")
            if xyz_token:
                at_pos = Position.from_sexpr(xyz_token)

        scale_pos = Position(1, 1, 1)
        if scale_token:
            xyz_token = SExprParser.find_token(scale_token, "xyz")
            if xyz_token:
                scale_pos = Position.from_sexpr(xyz_token)

        rotate_pos = Position(0, 0, 0)
        if rotate_token:
            xyz_token = SExprParser.find_token(rotate_token, "xyz")
            if xyz_token:
                rotate_pos = Position.from_sexpr(xyz_token)

        # Parse advanced features
        hide = hide_token is not None
        opacity = SExprParser.get_optional_float(sexpr, "opacity")

        offset_pos = None
        if offset_token:
            xyz_token = SExprParser.find_token(offset_token, "xyz")
            if xyz_token:
                offset_pos = Position.from_sexpr(xyz_token)

        return cls(
            filename=filename,
            at=at_pos,
            scale=scale_pos,
            rotate=rotate_pos,
            hide=hide,
            opacity=opacity,
            offset=offset_pos,
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("model"), self.filename]
        result.append(
            [Symbol("at"), [Symbol("xyz"), self.at.x, self.at.y, self.at.angle]]
        )
        result.append(
            [
                Symbol("scale"),
                [Symbol("xyz"), self.scale.x, self.scale.y, self.scale.angle],
            ]
        )
        result.append(
            [
                Symbol("rotate"),
                [Symbol("xyz"), self.rotate.x, self.rotate.y, self.rotate.angle],
            ]
        )

        # Add advanced features
        if self.hide:
            result.append(Symbol("hide"))

        if self.opacity is not None:
            result.append([Symbol("opacity"), self.opacity])

        if self.offset:
            result.append(
                [
                    Symbol("offset"),
                    [Symbol("xyz"), self.offset.x, self.offset.y, self.offset.angle],
                ]
            )

        return result


@dataclass
class Footprint(KiCadObject):
    """Footprint definition"""

    name: str
    position: Position = field(default_factory=Position)
    locked: Optional[bool] = None
    placed: Optional[bool] = None
    layer: str = "F.Cu"
    uuid: Optional[UUID] = None
    tedit: Optional[str] = None
    descr: Optional[str] = None
    tags: Optional[str] = None
    path: Optional[str] = None
    autoplace_cost90: Optional[int] = None
    autoplace_cost180: Optional[int] = None
    solder_mask_margin: Optional[float] = None
    solder_paste_margin: Optional[float] = None
    solder_paste_ratio: Optional[float] = None
    clearance: Optional[float] = None
    zone_connect: Optional[PadConnection] = None
    thermal_width: Optional[float] = None
    thermal_gap: Optional[float] = None

    # Components
    texts: List[FootprintText] = field(default_factory=list)
    pads: List[FootprintPad] = field(default_factory=list)
    models: List[Model3D] = field(default_factory=list)
    properties: List[Property] = field(default_factory=list)
    graphics: List[KiCadObject] = field(default_factory=list)

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "Footprint":
        name = SExprParser.safe_get_str(sexpr, 1, "")

        # Parse position
        at_token = SExprParser.find_token(sexpr, "at")
        position = Position.from_sexpr(at_token)

        # Parse basic attributes
        locked = SExprParser.get_optional_bool_flag(sexpr, "locked")
        placed = SExprParser.get_optional_bool_flag(sexpr, "placed")
        layer = SExprParser.get_required_str(sexpr, "layer", default="F.Cu")

        # Parse UUID
        uuid = None
        uuid_token = SExprParser.find_token(sexpr, "uuid")
        if uuid_token:
            uuid = UUID.from_sexpr(uuid_token)

        # Parse strings
        tedit = SExprParser.get_optional_str(sexpr, "tedit")
        descr = SExprParser.get_optional_str(sexpr, "descr")
        tags = SExprParser.get_optional_str(sexpr, "tags")
        path = SExprParser.get_optional_str(sexpr, "path")

        # Parse zone_connect
        zone_connect = parse_zone_connect(sexpr)

        footprint = cls(
            name=name,
            position=position,
            locked=locked,
            placed=placed,
            layer=layer,
            uuid=uuid,
            tedit=tedit,
            descr=descr,
            tags=tags,
            path=path,
            zone_connect=zone_connect,
        )

        return footprint

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("footprint"), self.name]

        if self.position:
            result.append(self.position.to_sexpr())
        if self.locked is not None:
            result.append(Symbol("locked"))
        if self.placed is not None:
            result.append(Symbol("placed"))
        if self.layer != "F.Cu":
            result.append([Symbol("layer"), self.layer])
        if self.uuid:
            result.append(self.uuid.to_sexpr())
        if self.tedit:
            result.append([Symbol("tedit"), self.tedit])
        if self.descr:
            result.append([Symbol("descr"), self.descr])
        if self.tags:
            result.append([Symbol("tags"), self.tags])
        if self.path:
            result.append([Symbol("path"), self.path])
        if self.zone_connect is not None:
            result.append([Symbol("zone_connect"), self.zone_connect.value])

        return result


@dataclass
class KiCadFootprint(KiCadObject):
    """KiCad footprint definition.

    The 'footprint' token defines a footprint in the format:
    (footprint
        ["LIBRARY_LINK"]
        [locked]
        [placed]
        (layer LAYER_DEFINITIONS)
        (tedit TIME_STAMP)
        [(uuid UUID)]
        [POSITION_IDENTIFIER]
        [(descr "DESCRIPTION")]
        [(tags "NAME")]
        [(property "KEY" "VALUE") ...]
        (path "PATH")
        [(autoplace_cost90 COST)]
        [(autoplace_cost180 COST)]
        [(solder_mask_margin MARGIN)]
        [(solder_paste_margin MARGIN)]
        [(solder_paste_ratio RATIO)]
        [(clearance CLEARANCE)]
        [(zone_connect CONNECTION_TYPE)]
        [(thermal_width WIDTH)]
        [(thermal_gap DISTANCE)]
        [ATTRIBUTES]
        [(private_layers LAYER_DEFINITIONS)]
        [(net_tie_pad_groups PAD_GROUP_DEFINITIONS)]
        GRAPHIC_ITEMS...
        PADS...
        ZONES...
        GROUPS...
        3D_MODEL
    )
    """

    __token_name__ = "footprint"

    # Core identification
    library_link: Optional[str] = None  # LIBRARY_LINK for board footprints

    # Placement and state flags
    locked: bool = False  # Cannot be edited flag
    placed: bool = True  # Has been placed flag

    # Layer and positioning
    layer: str = "F.Cu"  # Canonical layer the footprint is placed
    position: Position = field(
        default_factory=Position
    )  # X, Y coordinates and rotation

    # Timestamps and identification
    tedit: Optional[str] = None  # Last edit timestamp
    uuid: Optional[UUID] = None  # Unique identifier (board footprints)

    # Description and metadata
    descr: Optional[str] = None  # Description string
    tags: Optional[str] = None  # Search tags string
    properties: List[Property] = field(default_factory=list)  # Custom properties
    path: Optional[str] = None  # Hierarchical path to schematic symbol

    # Autoplace settings (board footprints)
    autoplace_cost90: Optional[int] = None  # Vertical autoplace cost (1-10)
    autoplace_cost180: Optional[int] = None  # Horizontal autoplace cost (1-10)

    # Solder settings
    solder_mask_margin: Optional[float] = None  # Distance from pads to solder mask
    solder_paste_margin: Optional[float] = None  # Distance from pads to solder paste
    solder_paste_ratio: Optional[float] = (
        None  # Percentage of pad size for solder paste
    )

    # Electrical settings
    clearance: Optional[float] = None  # Clearance to copper objects
    zone_connect: Optional[PadConnection] = None  # How pads connect to zones (0-3)
    thermal_width: Optional[float] = None  # Thermal relief spoke width
    thermal_gap: Optional[float] = None  # Distance from pad to zone for thermals

    # Advanced features
    attributes: Optional[FootprintAttributes] = None  # Footprint attributes
    private_layers: List[str] = field(default_factory=list)  # Private layer names
    net_tie_pad_groups: List[str] = field(default_factory=list)  # Net-tie pad groups

    # Graphical elements
    texts: List[FootprintText] = field(default_factory=list)  # Text objects
    lines: List[FootprintLine] = field(default_factory=list)  # Line objects
    rectangles: List[FootprintRectangle] = field(
        default_factory=list
    )  # Rectangle objects
    circles: List[FootprintCircle] = field(default_factory=list)  # Circle objects
    arcs: List[FootprintArc] = field(default_factory=list)  # Arc objects
    polygons: List[FootprintPolygon] = field(default_factory=list)  # Polygon objects

    # Electrical elements
    pads: List[FootprintPad] = field(default_factory=list)  # Pad definitions
    zones: List["Zone"] = field(default_factory=list)  # Zone definitions
    keepout_zones: List["Zone"] = field(default_factory=list)  # Keepout zones

    # Organization
    groups: List[Group] = field(default_factory=list)  # Grouped objects

    # 3D model
    model: Optional[Footprint3DModel] = None  # 3D model association

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "KiCadFootprint":
        library_link = (
            str(SExprParser.get_value(sexpr, 1))
            if len(sexpr) > 1 and isinstance(sexpr[1], str)
            else None
        )

        uuid_token = SExprParser.find_token(sexpr, "uuid")
        at_token = SExprParser.find_token(sexpr, "at")
        attr_token = SExprParser.find_token(sexpr, "attr")
        model_token = SExprParser.find_token(sexpr, "model")

        footprint = cls(
            library_link=library_link,
            locked=SExprParser.has_symbol(sexpr, "locked"),
            placed=(
                not SExprParser.has_symbol(sexpr, "placed")
                if SExprParser.has_symbol(sexpr, "placed")
                else True
            ),
            layer=SExprParser.get_required_str(sexpr, "layer", default="F.Cu"),
            position=Position.from_sexpr(at_token) if at_token else Position(),
            tedit=SExprParser.get_optional_str(sexpr, "tedit"),
            uuid=UUID.from_sexpr(uuid_token) if uuid_token else None,
            descr=SExprParser.get_optional_str(sexpr, "descr"),
            tags=SExprParser.get_optional_str(sexpr, "tags"),
            path=SExprParser.get_optional_str(sexpr, "path"),
            autoplace_cost90=SExprParser.get_optional_int(sexpr, "autoplace_cost90"),
            autoplace_cost180=SExprParser.get_optional_int(sexpr, "autoplace_cost180"),
            solder_mask_margin=SExprParser.get_optional_float(
                sexpr, "solder_mask_margin"
            ),
            solder_paste_margin=SExprParser.get_optional_float(
                sexpr, "solder_paste_margin"
            ),
            solder_paste_ratio=SExprParser.get_optional_float(
                sexpr, "solder_paste_ratio"
            ),
            clearance=SExprParser.get_optional_float(sexpr, "clearance"),
            zone_connect=parse_zone_connect(sexpr),
            thermal_width=SExprParser.get_optional_float(sexpr, "thermal_width"),
            thermal_gap=SExprParser.get_optional_float(sexpr, "thermal_gap"),
            attributes=(
                FootprintAttributes.from_sexpr(attr_token) if attr_token else None
            ),
            model=Footprint3DModel.from_sexpr(model_token) if model_token else None,
        )

        # Parse properties
        for prop_token in SExprParser.find_all_tokens(sexpr, "property"):
            footprint.properties.append(Property.from_sexpr(prop_token))

        # Parse private layers
        private_layers_token = SExprParser.find_token(sexpr, "private_layers")
        if private_layers_token:
            for layer_name in private_layers_token[1:]:
                if isinstance(layer_name, str):
                    footprint.private_layers.append(layer_name)

        # Parse net tie pad groups
        net_tie_token = SExprParser.find_token(sexpr, "net_tie_pad_groups")
        if net_tie_token:
            for group_name in net_tie_token[1:]:
                if isinstance(group_name, str):
                    footprint.net_tie_pad_groups.append(group_name)

        # Parse graphic items
        for text_token in SExprParser.find_all_tokens(sexpr, "fp_text"):
            footprint.texts.append(FootprintText.from_sexpr(text_token))
        for line_token in SExprParser.find_all_tokens(sexpr, "fp_line"):
            footprint.lines.append(FootprintLine.from_sexpr(line_token))
        for rect_token in SExprParser.find_all_tokens(sexpr, "fp_rect"):
            footprint.rectangles.append(FootprintRectangle.from_sexpr(rect_token))
        for circle_token in SExprParser.find_all_tokens(sexpr, "fp_circle"):
            footprint.circles.append(
                cast(FootprintCircle, FootprintCircle.from_sexpr(circle_token))
            )
        for arc_token in SExprParser.find_all_tokens(sexpr, "fp_arc"):
            footprint.arcs.append(
                cast(FootprintArc, FootprintArc.from_sexpr(arc_token))
            )
        for poly_token in SExprParser.find_all_tokens(sexpr, "fp_poly"):
            footprint.polygons.append(
                cast(FootprintPolygon, FootprintPolygon.from_sexpr(poly_token))
            )

        # Parse pads
        for pad_token in SExprParser.find_all_tokens(sexpr, "pad"):
            footprint.pads.append(FootprintPad.from_sexpr(pad_token))

        # Parse zones
        for zone_token in SExprParser.find_all_tokens(sexpr, "zone"):
            zone = Zone.from_sexpr(zone_token)
            if zone.keepout:
                footprint.keepout_zones.append(zone)
            else:
                footprint.zones.append(zone)

        # Parse groups
        for group_token in SExprParser.find_all_tokens(sexpr, "group"):
            footprint.groups.append(Group.from_sexpr(group_token))

        return footprint

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("footprint")]

        if self.library_link:
            result.append(self.library_link)

        if self.locked is not None and self.locked:
            result.append(Symbol("locked"))
        if self.placed is not None and self.placed:
            result.append(Symbol("placed"))

        result.append([Symbol("layer"), self.layer])

        if self.tedit:
            result.append([Symbol("tedit"), self.tedit])
        if self.uuid:
            result.append(self.uuid.to_sexpr())
        if self.position:
            result.append(self.position.to_sexpr())
        if self.descr:
            result.append([Symbol("descr"), self.descr])
        if self.tags:
            result.append([Symbol("tags"), self.tags])

        # Add properties
        for prop in self.properties:
            result.append(prop.to_sexpr())

        if self.path:
            result.append([Symbol("path"), self.path])

        # Add autoplace costs
        if self.autoplace_cost90 is not None:
            result.append([Symbol("autoplace_cost90"), self.autoplace_cost90])
        if self.autoplace_cost180 is not None:
            result.append([Symbol("autoplace_cost180"), self.autoplace_cost180])

        # Add solder settings
        if self.solder_mask_margin is not None:
            result.append([Symbol("solder_mask_margin"), self.solder_mask_margin])
        if self.solder_paste_margin is not None:
            result.append([Symbol("solder_paste_margin"), self.solder_paste_margin])
        if self.solder_paste_ratio is not None:
            result.append([Symbol("solder_paste_ratio"), self.solder_paste_ratio])

        # Add electrical settings
        if self.clearance is not None:
            result.append([Symbol("clearance"), self.clearance])
        if self.zone_connect is not None:
            result.append([Symbol("zone_connect"), self.zone_connect.value])
        if self.thermal_width is not None:
            result.append([Symbol("thermal_width"), self.thermal_width])
        if self.thermal_gap is not None:
            result.append([Symbol("thermal_gap"), self.thermal_gap])

        # Add attributes
        if self.attributes:
            result.append(self.attributes.to_sexpr())

        # Add private layers
        if self.private_layers:
            private_layers_list: SExpr = [Symbol("private_layers")]
            for layer in self.private_layers:
                private_layers_list.append(layer)
            result.append(private_layers_list)

        # Add net tie pad groups
        if self.net_tie_pad_groups:
            net_tie_list: SExpr = [Symbol("net_tie_pad_groups")]
            for group in self.net_tie_pad_groups:
                net_tie_list.append(group)
            result.append(net_tie_list)

        # Add graphic items
        for text in self.texts:
            result.append(text.to_sexpr())
        for line in self.lines:
            result.append(line.to_sexpr())
        for rect in self.rectangles:
            result.append(rect.to_sexpr())
        for circle in self.circles:
            result.append(circle.to_sexpr())
        for arc in self.arcs:
            result.append(arc.to_sexpr())
        for poly in self.polygons:
            result.append(poly.to_sexpr())

        # Add pads
        for pad in self.pads:
            result.append(pad.to_sexpr())

        # Add zones
        for zone in self.zones:
            result.append(zone.to_sexpr())

        # Add keepout zones
        for keepout_zone in self.keepout_zones:
            result.append(keepout_zone.to_sexpr())

        # Add groups
        for group in self.groups:
            result.append(group.to_sexpr())

        # Add 3D model
        if self.model:
            result.append(self.model.to_sexpr())

        return result


# High-level API functions


def parse_kicad_footprint_file(file_content: str) -> KiCadFootprint:
    """Parse KiCad footprint file from string content"""
    return cast(KiCadFootprint, parse_kicad_file(file_content, KiCadFootprint))


def write_kicad_footprint_file(footprint: KiCadFootprint) -> str:
    """Write KiCad footprint to string"""
    return write_kicad_file(footprint)


def load_footprint_file(filepath: str) -> KiCadFootprint:
    """Load footprint file from disk"""
    with open(filepath, "r", encoding="utf-8") as f:
        return parse_kicad_footprint_file(f.read())


def save_footprint_file(footprint: KiCadFootprint, filepath: str) -> None:
    """Save footprint to disk

    Returns:
        None
    """
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(write_kicad_footprint_file(footprint))
