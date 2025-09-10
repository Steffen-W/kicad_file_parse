"""
KiCad Graphics Items and Dimensions

This module contains classes for graphical elements used in boards,
footprints, and other KiCad objects, including dimensions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from .kicad_common import (
    UUID,
    CoordinatePointList,
    KiCadObject,
    Position,
    SExpr,
    SExprParser,
    Stroke,
    Symbol,
    TextEffects,
)

# Dimension types and formats


class DimensionType(Enum):
    """Dimension types"""

    ALIGNED = "aligned"
    LEADER = "leader"
    CENTER = "center"
    ORTHOGONAL = "orthogonal"
    RADIAL = "radial"


class DimensionUnits(Enum):
    """Dimension units"""

    INCHES = 0
    MILS = 1
    MILLIMETERS = 2
    AUTOMATIC = 3


class DimensionUnitsFormat(Enum):
    """Dimension units format"""

    NO_SUFFIX = 0
    BARE_SUFFIX = 1
    PARENTHESIS = 2


class TextPositionMode(Enum):
    """Text position modes"""

    OUTSIDE = 0
    INLINE = 1
    MANUAL = 2


class ArrowDirection(Enum):
    """Arrow direction"""

    OUTWARD = "outward"
    INWARD = "inward"


class TextFrameType(Enum):
    """Text frame types"""

    NONE = 0
    RECTANGLE = 1
    CIRCLE = 2
    ROUNDED_RECTANGLE = 3


@dataclass
class DimensionFormat:
    """Dimension format definition"""

    prefix: Optional[str] = None
    suffix: Optional[str] = None
    units: DimensionUnits = DimensionUnits.MILLIMETERS
    units_format: DimensionUnitsFormat = DimensionUnitsFormat.NO_SUFFIX
    precision: int = 2
    override_value: Optional[str] = None
    suppress_zeros: bool = False

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "DimensionFormat":
        units_token = SExprParser.find_token(sexpr, "units")
        units_format_token = SExprParser.find_token(sexpr, "units_format")
        suppress_zeros_token = SExprParser.find_token(sexpr, "suppress_zeros")

        units = DimensionUnits.MILLIMETERS
        if units_token:
            try:
                units = DimensionUnits(SExprParser.safe_get_int(units_token, 1, 2))
            except (ValueError, TypeError):
                units = DimensionUnits.MILLIMETERS

        units_format = DimensionUnitsFormat.NO_SUFFIX
        if units_format_token:
            try:
                units_format = DimensionUnitsFormat(
                    SExprParser.safe_int(
                        SExprParser.get_value(units_format_token, 1), 0
                    )
                )
            except (ValueError, TypeError):
                units_format = DimensionUnitsFormat.NO_SUFFIX

        return cls(
            prefix=SExprParser.get_optional_str(sexpr, "prefix"),
            suffix=SExprParser.get_optional_str(sexpr, "suffix"),
            units=units,
            units_format=units_format,
            precision=SExprParser.get_optional_int(sexpr, "precision") or 2,
            override_value=SExprParser.get_optional_str(sexpr, "override_value"),
            suppress_zeros=(
                SExprParser.get_value(suppress_zeros_token, 1) == Symbol("yes")
                if suppress_zeros_token
                else False
            ),
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("format")]

        if self.prefix:
            result.append([Symbol("prefix"), self.prefix])
        if self.suffix:
            result.append([Symbol("suffix"), self.suffix])

        result.append([Symbol("units"), self.units.value])
        result.append([Symbol("units_format"), self.units_format.value])
        result.append([Symbol("precision"), self.precision])

        if self.override_value:
            result.append([Symbol("override_value"), self.override_value])
        if self.suppress_zeros:
            result.append([Symbol("suppress_zeros"), Symbol("yes")])

        return result


@dataclass
class DimensionStyle:
    """Dimension style definition"""

    thickness: float = 0.15
    arrow_length: float = 1.27
    text_position_mode: TextPositionMode = TextPositionMode.OUTSIDE
    arrow_direction: Optional[ArrowDirection] = None
    extension_height: float = 1.27
    text_frame: TextFrameType = TextFrameType.NONE
    extension_offset: float = 0.5
    keep_text_aligned: bool = True

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "DimensionStyle":
        thickness_token = SExprParser.find_token(sexpr, "thickness")
        arrow_length_token = SExprParser.find_token(sexpr, "arrow_length")
        text_position_mode_token = SExprParser.find_token(sexpr, "text_position_mode")
        arrow_direction_token = SExprParser.find_token(sexpr, "arrow_direction")
        text_frame_token = SExprParser.find_token(sexpr, "text_frame")

        text_position_mode = TextPositionMode.OUTSIDE
        if text_position_mode_token:
            try:
                text_position_mode = TextPositionMode(
                    SExprParser.safe_int(
                        SExprParser.get_value(text_position_mode_token, 1), 0
                    )
                )
            except (ValueError, TypeError):
                text_position_mode = TextPositionMode.OUTSIDE

        arrow_direction = None
        if arrow_direction_token:
            try:
                arrow_direction = ArrowDirection(
                    str(SExprParser.get_value(arrow_direction_token, 1))
                )
            except ValueError:
                arrow_direction = None

        text_frame = TextFrameType.NONE
        if text_frame_token:
            try:
                text_frame = TextFrameType(
                    SExprParser.safe_get_int(text_frame_token, 1, 0)
                )
            except (ValueError, TypeError):
                text_frame = TextFrameType.NONE

        return cls(
            thickness=SExprParser.safe_float(
                SExprParser.get_value(thickness_token, 1) if thickness_token else None,
                0.15,
            ),
            arrow_length=SExprParser.safe_float(
                (
                    SExprParser.get_value(arrow_length_token, 1)
                    if arrow_length_token
                    else None
                ),
                1.27,
            ),
            text_position_mode=text_position_mode,
            arrow_direction=arrow_direction,
            extension_height=SExprParser.get_optional_float(sexpr, "extension_height")
            or 1.27,
            text_frame=text_frame,
            extension_offset=SExprParser.get_optional_float(sexpr, "extension_offset")
            or 0.5,
            keep_text_aligned=SExprParser.has_symbol(sexpr, "keep_text_aligned"),
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("style")]
        result.append([Symbol("thickness"), self.thickness])
        result.append([Symbol("arrow_length"), self.arrow_length])
        result.append([Symbol("text_position_mode"), self.text_position_mode.value])

        if self.arrow_direction:
            result.append(
                [Symbol("arrow_direction"), Symbol(self.arrow_direction.value)]
            )
        if self.extension_height is not None:
            result.append([Symbol("extension_height"), self.extension_height])
        if self.text_frame != TextFrameType.NONE:
            result.append([Symbol("text_frame"), self.text_frame.value])
        if self.extension_offset is not None:
            result.append([Symbol("extension_offset"), self.extension_offset])
        if self.keep_text_aligned:
            result.append(Symbol("keep_text_aligned"))

        return result


# Graphical items


@dataclass
class GraphicalText(KiCadObject):
    """Graphical text definition"""

    text: str
    position: Position
    layer: str
    knockout: bool = False
    uuid: Optional[UUID] = None
    effects: TextEffects = field(default_factory=TextEffects)

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "GraphicalText":
        text = SExprParser.normalize_text_content(
            str(SExprParser.get_value(sexpr, 1, ""))
        )
        layer_token = SExprParser.find_token(sexpr, "layer")
        uuid_token = SExprParser.find_token(sexpr, "uuid")
        effects_token = SExprParser.find_token(sexpr, "effects")

        # Check for knockout in layer token
        knockout = False
        layer = "F.SilkS"
        if layer_token:
            layer = str(SExprParser.get_value(layer_token, 1, "F.SilkS"))
            knockout = SExprParser.has_symbol(layer_token, "knockout")

        # Parse position with angle support
        at_token = SExprParser.find_token(sexpr, "at")
        position = Position.from_sexpr(at_token) if at_token else Position(0, 0)

        return cls(
            text=text,
            position=position,
            layer=layer,
            knockout=knockout,
            uuid=UUID.from_sexpr(uuid_token) if uuid_token else None,
            effects=(
                TextEffects.from_sexpr(effects_token)
                if effects_token
                else TextEffects()
            ),
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("gr_text"), self.text]
        result.append(self.position.to_sexpr())

        layer_expr = [Symbol("layer"), self.layer]
        if self.knockout:
            layer_expr.append(Symbol("knockout"))
        result.append(layer_expr)

        if self.uuid:
            result.append(self.uuid.to_sexpr())

        result.append(self.effects.to_sexpr())
        return result


@dataclass
class GraphicalLine(KiCadObject):
    """Graphical line definition"""

    start: Position
    end: Position
    angle: Optional[float] = None
    layer: str = "F.SilkS"
    stroke: Stroke = field(default_factory=Stroke)
    uuid: Optional[UUID] = None

    @property
    def width(self) -> Optional[float]:
        """Get width from stroke"""
        return self.stroke.width

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "GraphicalLine":
        start_token = SExprParser.find_token(sexpr, "start")
        end_token = SExprParser.find_token(sexpr, "end")
        angle_token = SExprParser.find_token(sexpr, "angle")
        layer_token = SExprParser.find_token(sexpr, "layer")
        uuid_token = SExprParser.find_token(sexpr, "uuid")

        stroke = SExprParser.parse_stroke_or_width(sexpr, 0.15)

        return cls(
            start=(Position.from_sexpr(start_token) if start_token else Position(0, 0)),
            end=(Position.from_sexpr(end_token) if end_token else Position(0, 0)),
            angle=SExprParser.get_value(angle_token, 1) if angle_token else None,
            layer=(
                str(SExprParser.get_value(layer_token, 1, "F.SilkS"))
                if layer_token
                else "F.SilkS"
            ),
            stroke=stroke,
            uuid=UUID.from_sexpr(uuid_token) if uuid_token else None,
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("gr_line")]
        result.append([Symbol("start"), self.start.x, self.start.y])
        result.append([Symbol("end"), self.end.x, self.end.y])

        if self.angle is not None:
            result.append([Symbol("angle"), self.angle])

        result.append([Symbol("layer"), self.layer])
        result.append(self.stroke.to_sexpr())

        if self.width is not None:
            result.append([Symbol("width"), self.width])

        if self.uuid:
            result.append(self.uuid.to_sexpr())

        return result


@dataclass
class GraphicalRectangle(KiCadObject):
    """Graphical rectangle definition"""

    start: Position
    end: Position
    layer: str = "F.SilkS"
    stroke: Stroke = field(default_factory=Stroke)
    fill: bool = False
    uuid: Optional[UUID] = None

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "GraphicalRectangle":
        start_token = SExprParser.find_token(sexpr, "start")
        end_token = SExprParser.find_token(sexpr, "end")
        layer_token = SExprParser.find_token(sexpr, "layer")
        fill_token = SExprParser.find_token(sexpr, "fill")
        uuid_token = SExprParser.find_token(sexpr, "uuid")

        stroke = SExprParser.parse_stroke_or_width(sexpr, 0.15)

        return cls(
            start=(Position.from_sexpr(start_token) if start_token else Position(0, 0)),
            end=(Position.from_sexpr(end_token) if end_token else Position(0, 0)),
            layer=(
                str(SExprParser.get_value(layer_token, 1, "F.SilkS"))
                if layer_token
                else "F.SilkS"
            ),
            stroke=stroke,
            fill=(
                SExprParser.get_value(fill_token, 1) == Symbol("yes")
                if fill_token
                else False
            ),
            uuid=UUID.from_sexpr(uuid_token) if uuid_token else None,
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("gr_rect")]
        result.append([Symbol("start"), self.start.x, self.start.y])
        result.append([Symbol("end"), self.end.x, self.end.y])
        result.append([Symbol("layer"), self.layer])
        result.append(self.stroke.to_sexpr())

        if self.fill:
            result.append([Symbol("fill"), Symbol("yes")])

        if self.uuid:
            result.append(self.uuid.to_sexpr())

        return result


@dataclass
class GraphicalCircle(KiCadObject):
    """Graphical circle definition"""

    center: Position
    end: Position  # End point of radius
    layer: str = "F.SilkS"
    stroke: Stroke = field(default_factory=Stroke)
    fill: bool = False
    uuid: Optional[UUID] = None

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "GraphicalCircle":
        center_token = SExprParser.find_token(sexpr, "center")
        end_token = SExprParser.find_token(sexpr, "end")
        layer_token = SExprParser.find_token(sexpr, "layer")
        fill_token = SExprParser.find_token(sexpr, "fill")
        uuid_token = SExprParser.find_token(sexpr, "uuid")

        stroke = SExprParser.parse_stroke_or_width(sexpr, 0.15)

        return cls(
            center=(
                Position.from_sexpr(center_token) if center_token else Position(0, 0)
            ),
            end=(Position.from_sexpr(end_token) if end_token else Position(0, 0)),
            layer=(
                str(SExprParser.get_value(layer_token, 1, "F.SilkS"))
                if layer_token
                else "F.SilkS"
            ),
            stroke=stroke,
            fill=(
                SExprParser.get_value(fill_token, 1) == Symbol("yes")
                if fill_token
                else False
            ),
            uuid=UUID.from_sexpr(uuid_token) if uuid_token else None,
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("gr_circle")]
        result.append([Symbol("center"), self.center.x, self.center.y])
        result.append([Symbol("end"), self.end.x, self.end.y])
        result.append([Symbol("layer"), self.layer])
        result.append(self.stroke.to_sexpr())

        if self.fill:
            result.append([Symbol("fill"), Symbol("yes")])

        if self.uuid:
            result.append(self.uuid.to_sexpr())

        return result


@dataclass
class GraphicalArc(KiCadObject):
    """Graphical arc definition"""

    start: Position
    mid: Position
    end: Position
    layer: str = "F.SilkS"
    stroke: Stroke = field(default_factory=Stroke)
    uuid: Optional[UUID] = None

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "GraphicalArc":
        start_token = SExprParser.find_token(sexpr, "start")
        mid_token = SExprParser.find_token(sexpr, "mid")
        end_token = SExprParser.find_token(sexpr, "end")
        layer_token = SExprParser.find_token(sexpr, "layer")
        uuid_token = SExprParser.find_token(sexpr, "uuid")

        stroke = SExprParser.parse_stroke_or_width(sexpr, 0.15)

        return cls(
            start=(Position.from_sexpr(start_token) if start_token else Position(0, 0)),
            mid=(Position.from_sexpr(mid_token) if mid_token else Position(0, 0)),
            end=(Position.from_sexpr(end_token) if end_token else Position(0, 0)),
            layer=(
                str(SExprParser.get_value(layer_token, 1, "F.SilkS"))
                if layer_token
                else "F.SilkS"
            ),
            stroke=stroke,
            uuid=UUID.from_sexpr(uuid_token) if uuid_token else None,
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("gr_arc")]
        result.append([Symbol("start"), self.start.x, self.start.y])
        result.append([Symbol("mid"), self.mid.x, self.mid.y])
        result.append([Symbol("end"), self.end.x, self.end.y])
        result.append([Symbol("layer"), self.layer])
        result.append(self.stroke.to_sexpr())

        if self.uuid:
            result.append(self.uuid.to_sexpr())

        return result


@dataclass
class GraphicalPolygon(KiCadObject):
    """Graphical polygon definition"""

    points: CoordinatePointList
    layer: str = "F.SilkS"
    stroke: Stroke = field(default_factory=Stroke)
    fill: bool = False
    uuid: Optional[UUID] = None

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "GraphicalPolygon":
        pts_token = SExprParser.find_token(sexpr, "pts")
        layer_token = SExprParser.find_token(sexpr, "layer")
        fill_token = SExprParser.find_token(sexpr, "fill")
        uuid_token = SExprParser.find_token(sexpr, "uuid")

        stroke = SExprParser.parse_stroke_or_width(sexpr, 0.15)

        return cls(
            points=(
                CoordinatePointList.from_sexpr(pts_token)
                if pts_token
                else CoordinatePointList()
            ),
            layer=(
                str(SExprParser.get_value(layer_token, 1, "F.SilkS"))
                if layer_token
                else "F.SilkS"
            ),
            stroke=stroke,
            fill=(
                SExprParser.get_value(fill_token, 1) == Symbol("yes")
                if fill_token
                else False
            ),
            uuid=UUID.from_sexpr(uuid_token) if uuid_token else None,
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("gr_poly")]
        result.append(self.points.to_sexpr())
        result.append([Symbol("layer"), self.layer])
        result.append(self.stroke.to_sexpr())

        if self.fill:
            result.append([Symbol("fill"), Symbol("yes")])

        if self.uuid:
            result.append(self.uuid.to_sexpr())

        return result


@dataclass
class Dimension(KiCadObject):
    """Dimension definition"""

    locked: Optional[bool] = None
    type: DimensionType = DimensionType.ALIGNED
    layer: str = "Dwgs.User"
    uuid: Optional[UUID] = None
    points: CoordinatePointList = field(default_factory=CoordinatePointList)
    height: Optional[float] = None
    orientation: Optional[float] = None
    leader_length: Optional[float] = None
    text: Optional[GraphicalText] = None
    format: Optional[DimensionFormat] = None
    style: DimensionStyle = field(default_factory=DimensionStyle)

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "Dimension":
        type_token = SExprParser.find_token(sexpr, "type")
        layer_token = SExprParser.find_token(sexpr, "layer")
        uuid_token = SExprParser.find_token(sexpr, "uuid")
        pts_token = SExprParser.find_token(sexpr, "pts")
        height_token = SExprParser.find_token(sexpr, "height")
        orientation_token = SExprParser.find_token(sexpr, "orientation")
        leader_length_token = SExprParser.find_token(sexpr, "leader_length")
        gr_text_token = SExprParser.find_token(sexpr, "gr_text")
        format_token = SExprParser.find_token(sexpr, "format")
        style_token = SExprParser.find_token(sexpr, "style")

        dim_type = DimensionType.ALIGNED
        if type_token:
            try:
                dim_type = DimensionType(
                    str(SExprParser.get_value(type_token, 1, "aligned"))
                )
            except ValueError:
                dim_type = DimensionType.ALIGNED

        return cls(
            locked=True if SExprParser.has_symbol(sexpr, "locked") else None,
            type=dim_type,
            layer=(
                str(SExprParser.get_value(layer_token, 1, "Dwgs.User"))
                if layer_token
                else "Dwgs.User"
            ),
            uuid=UUID.from_sexpr(uuid_token) if uuid_token else None,
            points=(
                CoordinatePointList.from_sexpr(pts_token)
                if pts_token
                else CoordinatePointList()
            ),
            height=SExprParser.get_value(height_token, 1) if height_token else None,
            orientation=(
                SExprParser.get_value(orientation_token, 1)
                if orientation_token
                else None
            ),
            leader_length=(
                SExprParser.get_value(leader_length_token, 1)
                if leader_length_token
                else None
            ),
            text=GraphicalText.from_sexpr(gr_text_token) if gr_text_token else None,
            format=DimensionFormat.from_sexpr(format_token) if format_token else None,
            style=(
                DimensionStyle.from_sexpr(style_token)
                if style_token
                else DimensionStyle()
            ),
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("dimension")]

        if self.locked is not None and self.locked:
            result.append(Symbol("locked"))

        result.append([Symbol("type"), Symbol(self.type.value)])
        result.append([Symbol("layer"), self.layer])

        if self.uuid:
            result.append(self.uuid.to_sexpr())

        result.append(self.points.to_sexpr())

        if self.height is not None:
            result.append([Symbol("height"), self.height])
        if self.orientation is not None:
            result.append([Symbol("orientation"), self.orientation])
        if self.leader_length is not None:
            result.append([Symbol("leader_length"), self.leader_length])

        if self.text:
            result.append(self.text.to_sexpr())
        if self.format:
            result.append(self.format.to_sexpr())

        result.append(self.style.to_sexpr())

        return result


@dataclass
class GraphicalTextBox(KiCadObject):
    """Graphical text box definition (from version 7)"""

    locked: Optional[bool] = None
    text: str = ""
    start: Optional[Position] = None
    end: Optional[Position] = None
    points: Optional[CoordinatePointList] = None
    angle: Optional[float] = None
    layer: str = "F.SilkS"
    uuid: Optional[UUID] = None
    effects: TextEffects = field(default_factory=TextEffects)
    stroke: Optional[Stroke] = None
    render_cache: Optional[str] = None

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "GraphicalTextBox":
        # Check if locked token is present at index 1
        text_index = 2 if len(sexpr) > 1 and sexpr[1] == Symbol("locked") else 1

        text = SExprParser.normalize_text_content(
            str(SExprParser.get_value(sexpr, text_index, ""))
        )
        start_token = SExprParser.find_token(sexpr, "start")
        end_token = SExprParser.find_token(sexpr, "end")
        at_token = SExprParser.find_token(sexpr, "at")
        size_token = SExprParser.find_token(sexpr, "size")
        pts_token = SExprParser.find_token(sexpr, "pts")
        angle_token = SExprParser.find_token(sexpr, "angle")
        layer_token = SExprParser.find_token(sexpr, "layer")
        uuid_token = SExprParser.find_token(sexpr, "uuid")
        effects_token = SExprParser.find_token(sexpr, "effects")
        stroke_token = SExprParser.find_token(sexpr, "stroke")
        render_cache_token = SExprParser.find_token(sexpr, "render_cache")

        # Handle both old format (start/end) and new format (at/size)
        start_pos = None
        end_pos = None

        if start_token and end_token:
            # Old format: (start x y) (end x y)
            start_pos = Position.from_sexpr(start_token)
            end_pos = Position.from_sexpr(end_token)
        elif at_token and size_token:
            # New format: (at x y) (size w h) -> convert to start/end
            center_pos = Position.from_sexpr(at_token)
            width = SExprParser.get_value(size_token, 1, 10)
            height = SExprParser.get_value(size_token, 2, 10)

            # Convert center+size to start/end coordinates
            start_pos = Position(center_pos.x - width / 2, center_pos.y - height / 2)
            end_pos = Position(center_pos.x + width / 2, center_pos.y + height / 2)

        return cls(
            locked=True if SExprParser.has_symbol(sexpr, "locked") else None,
            text=text,
            start=start_pos,
            end=end_pos,
            points=CoordinatePointList.from_sexpr(pts_token) if pts_token else None,
            angle=SExprParser.get_value(angle_token, 1) if angle_token else None,
            layer=(
                str(SExprParser.get_value(layer_token, 1, "F.SilkS"))
                if layer_token
                else "F.SilkS"
            ),
            uuid=UUID.from_sexpr(uuid_token) if uuid_token else None,
            effects=(
                TextEffects.from_sexpr(effects_token)
                if effects_token
                else TextEffects()
            ),
            stroke=Stroke.from_sexpr(stroke_token) if stroke_token else None,
            render_cache=(
                str(SExprParser.get_value(render_cache_token, 1))
                if render_cache_token
                else None
            ),
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("gr_text_box")]

        if self.locked is not None and self.locked:
            result.append(Symbol("locked"))

        result.append(self.text)

        if self.start and self.end:
            result.append([Symbol("start"), self.start.x, self.start.y])
            result.append([Symbol("end"), self.end.x, self.end.y])
        elif self.points:
            result.append(self.points.to_sexpr())

        if self.angle is not None:
            result.append([Symbol("angle"), self.angle])

        result.append([Symbol("layer"), self.layer])

        if self.uuid:
            result.append(self.uuid.to_sexpr())

        result.append(self.effects.to_sexpr())

        if self.stroke:
            result.append(self.stroke.to_sexpr())

        if self.render_cache:
            result.append([Symbol("render_cache"), self.render_cache])

        return result


@dataclass
class GraphicalBezier(KiCadObject):
    """Graphical Bezier curve definition"""

    points: CoordinatePointList
    layer: str = "F.SilkS"
    stroke: Stroke = field(default_factory=Stroke)
    uuid: Optional[UUID] = None

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "GraphicalBezier":
        pts_token = SExprParser.find_token(sexpr, "pts")
        layer_token = SExprParser.find_token(sexpr, "layer")
        uuid_token = SExprParser.find_token(sexpr, "uuid")

        stroke = SExprParser.parse_stroke_or_width(sexpr, 0.15)

        return cls(
            points=(
                CoordinatePointList.from_sexpr(pts_token)
                if pts_token
                else CoordinatePointList()
            ),
            layer=(
                str(SExprParser.get_value(layer_token, 1, "F.SilkS"))
                if layer_token
                else "F.SilkS"
            ),
            stroke=stroke,
            uuid=UUID.from_sexpr(uuid_token) if uuid_token else None,
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("bezier")]
        result.append(self.points.to_sexpr())
        result.append([Symbol("layer"), self.layer])
        result.append(self.stroke.to_sexpr())

        if self.uuid:
            result.append(self.uuid.to_sexpr())

        return result
