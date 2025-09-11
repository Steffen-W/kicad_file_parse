"""
KiCad Worksheet S-Expression Classes

This module contains classes for worksheet file formats (.kicad_wks),
including setup parameters, drawing objects, and text elements.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from .kicad_common import (
    CoordinatePointList,
    Font,
    KiCadObject,
    Position,
    SExpr,
    SExprParser,
    Stroke,
    Symbol,
)

# Worksheet-specific enums


class CornerType(Enum):
    """Corner positioning types for worksheet elements"""

    LEFT_TOP = "ltcorner"
    LEFT_BOTTOM = "lbcorner"
    RIGHT_BOTTOM = "rbcorner"
    RIGHT_TOP = "rtcorner"


# Worksheet setup and configuration


@dataclass
class WorksheetSetup(KiCadObject):
    """Worksheet setup configuration"""

    textsize: Position = field(default_factory=lambda: Position(1.5, 1.5))
    linewidth: float = 0.15
    textlinewidth: float = 0.15
    left_margin: float = 10.0
    right_margin: float = 10.0
    top_margin: float = 10.0
    bottom_margin: float = 10.0

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "WorksheetSetup":
        return cls(
            textsize=SExprParser.get_position_with_default(sexpr, "textsize", 1.5, 1.5),
            linewidth=SExprParser.get_required_float(sexpr, "linewidth", default=0.15),
            textlinewidth=SExprParser.get_required_float(
                sexpr, "textlinewidth", default=0.15
            ),
            left_margin=SExprParser.get_required_float(
                sexpr, "left_margin", default=10.0
            ),
            right_margin=SExprParser.get_required_float(
                sexpr, "right_margin", default=10.0
            ),
            top_margin=SExprParser.get_required_float(
                sexpr, "top_margin", default=10.0
            ),
            bottom_margin=SExprParser.get_required_float(
                sexpr, "bottom_margin", default=10.0
            ),
        )

    def to_sexpr(self) -> SExpr:
        return [
            Symbol("setup"),
            [Symbol("textsize"), self.textsize.x, self.textsize.y],
            [Symbol("linewidth"), self.linewidth],
            [Symbol("textlinewidth"), self.textlinewidth],
            [Symbol("left_margin"), self.left_margin],
            [Symbol("right_margin"), self.right_margin],
            [Symbol("top_margin"), self.top_margin],
            [Symbol("bottom_margin"), self.bottom_margin],
        ]


# Worksheet drawing elements


@dataclass
class WorksheetLine(KiCadObject):
    """Worksheet line element"""

    start: Position
    end: Position
    name: Optional[str] = None
    stroke: Optional[Stroke] = None  # New format (version 7+)
    linewidth: Optional[float] = None  # Legacy format (pre-version 7)
    repeat: Optional[int] = None
    incrx: Optional[float] = None
    incry: Optional[float] = None
    corner: Optional[CornerType] = None
    comment: Optional[str] = None

    @property
    def width(self) -> Optional[float]:
        """Get width from stroke or legacy linewidth"""
        if self.stroke:
            return self.stroke.width
        return self.linewidth

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "WorksheetLine":
        # Check for corner positioning
        corner = None
        for corner_type in CornerType:
            if SExprParser.find_token(sexpr, corner_type.value):
                corner = corner_type
                break

        # Parse stroke (new format) or linewidth (legacy format)
        stroke = None
        linewidth = None

        # Try to parse stroke first (new format)
        stroke_token = SExprParser.find_token(sexpr, "stroke")
        if stroke_token:
            stroke = Stroke.from_sexpr(stroke_token)
        else:
            # Fallback to legacy linewidth
            linewidth = SExprParser.get_optional_float(sexpr, "linewidth")

        return cls(
            start=SExprParser.get_position_with_default(sexpr, "start"),
            end=SExprParser.get_position_with_default(sexpr, "end"),
            name=SExprParser.get_optional_str(sexpr, "name"),
            stroke=stroke,
            linewidth=linewidth,
            repeat=SExprParser.get_optional_int(sexpr, "repeat"),
            incrx=SExprParser.get_optional_float(sexpr, "incrx"),
            incry=SExprParser.get_optional_float(sexpr, "incry"),
            corner=corner,
            comment=SExprParser.get_optional_str(sexpr, "comment"),
        )

    def to_sexpr(self) -> SExpr:
        result = [
            Symbol("line"),
            [Symbol("start"), self.start.x, self.start.y],
            [Symbol("end"), self.end.x, self.end.y],
        ]

        if self.name is not None:
            result.append([Symbol("name"), self.name])

        # Always output stroke format (new format), convert legacy linewidth if needed
        if self.stroke is not None:
            result.append(self.stroke.to_sexpr())
        elif self.linewidth is not None:
            # Convert legacy linewidth to stroke format
            stroke = Stroke(width=self.linewidth)
            result.append(stroke.to_sexpr())

        if self.repeat is not None:
            result.append([Symbol("repeat"), self.repeat])
        if self.incrx is not None:
            result.append([Symbol("incrx"), self.incrx])
        if self.incry is not None:
            result.append([Symbol("incry"), self.incry])
        if self.corner is not None:
            result.append([Symbol(self.corner.value)])
        if self.comment is not None:
            result.append([Symbol("comment"), self.comment])

        return result


@dataclass
class WorksheetRectangle(KiCadObject):
    """Worksheet rectangle element"""

    start: Position
    end: Position
    name: Optional[str] = None
    stroke: Optional[Stroke] = None  # New format (version 7+)
    linewidth: Optional[float] = None  # Legacy format (pre-version 7)
    repeat: Optional[int] = None
    incrx: Optional[float] = None
    incry: Optional[float] = None
    corner: Optional[CornerType] = None
    comment: Optional[str] = None

    @property
    def width(self) -> Optional[float]:
        """Get width from stroke or legacy linewidth"""
        if self.stroke:
            return self.stroke.width
        return self.linewidth

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "WorksheetRectangle":
        # Check for corner positioning
        corner = None
        for corner_type in CornerType:
            if SExprParser.find_token(sexpr, corner_type.value):
                corner = corner_type
                break

        return cls(
            start=SExprParser.get_position_with_default(sexpr, "start"),
            end=SExprParser.get_position_with_default(sexpr, "end"),
            name=SExprParser.get_optional_str(sexpr, "name"),
            linewidth=SExprParser.get_optional_float(sexpr, "linewidth"),
            repeat=SExprParser.get_optional_int(sexpr, "repeat"),
            incrx=SExprParser.get_optional_float(sexpr, "incrx"),
            incry=SExprParser.get_optional_float(sexpr, "incry"),
            corner=corner,
            comment=SExprParser.get_optional_str(sexpr, "comment"),
        )

    def to_sexpr(self) -> SExpr:
        result = [
            Symbol("rect"),
            [Symbol("start"), self.start.x, self.start.y],
            [Symbol("end"), self.end.x, self.end.y],
        ]

        if self.name is not None:
            result.append([Symbol("name"), self.name])
        if self.linewidth is not None:
            result.append([Symbol("linewidth"), self.linewidth])
        if self.repeat is not None:
            result.append([Symbol("repeat"), self.repeat])
        if self.incrx is not None:
            result.append([Symbol("incrx"), self.incrx])
        if self.incry is not None:
            result.append([Symbol("incry"), self.incry])
        if self.corner is not None:
            result.append([Symbol(self.corner.value)])
        if self.comment is not None:
            result.append([Symbol("comment"), self.comment])

        return result


@dataclass
class WorksheetPolygon(KiCadObject):
    """Worksheet polygon element"""

    points: CoordinatePointList = field(default_factory=CoordinatePointList)
    name: Optional[str] = None
    pos: Optional[Position] = None
    rotate: Optional[float] = None
    stroke: Optional[Stroke] = None  # New format (version 7+)
    linewidth: Optional[float] = None  # Legacy format (pre-version 7)
    repeat: Optional[int] = None
    incrx: Optional[float] = None
    incry: Optional[float] = None
    corner: Optional[CornerType] = None
    comment: Optional[str] = None

    @property
    def width(self) -> Optional[float]:
        """Get width from stroke or legacy linewidth"""
        if self.stroke:
            return self.stroke.width
        return self.linewidth

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "WorksheetPolygon":
        # Parse points
        pts_token = SExprParser.find_token(sexpr, "pts")
        points = (
            CoordinatePointList.from_sexpr(pts_token)
            if pts_token
            else CoordinatePointList()
        )

        # Check for corner positioning
        corner = None
        for corner_type in CornerType:
            if SExprParser.find_token(sexpr, corner_type.value):
                corner = corner_type
                break

        return cls(
            points=points,
            name=SExprParser.get_optional_str(sexpr, "name"),
            pos=SExprParser.get_optional_position(sexpr, "pos"),
            rotate=SExprParser.get_optional_float(sexpr, "rotate"),
            linewidth=SExprParser.get_optional_float(sexpr, "linewidth"),
            repeat=SExprParser.get_optional_int(sexpr, "repeat"),
            incrx=SExprParser.get_optional_float(sexpr, "incrx"),
            incry=SExprParser.get_optional_float(sexpr, "incry"),
            corner=corner,
            comment=SExprParser.get_optional_str(sexpr, "comment"),
        )

    def to_sexpr(self) -> SExpr:
        result = [Symbol("polygon"), self.points.to_sexpr()]

        if self.name is not None:
            result.append([Symbol("name"), self.name])
        if self.pos is not None:
            result.append([Symbol("pos"), self.pos.x, self.pos.y])
        if self.rotate is not None:
            result.append([Symbol("rotate"), self.rotate])
        if self.linewidth is not None:
            result.append([Symbol("linewidth"), self.linewidth])
        if self.repeat is not None:
            result.append([Symbol("repeat"), self.repeat])
        if self.incrx is not None:
            result.append([Symbol("incrx"), self.incrx])
        if self.incry is not None:
            result.append([Symbol("incry"), self.incry])
        if self.corner is not None:
            result.append([Symbol(self.corner.value)])
        if self.comment is not None:
            result.append([Symbol("comment"), self.comment])

        return result


@dataclass
class WorksheetText(KiCadObject):
    """Worksheet text element (tbtext)"""

    text: str
    position: Position
    name: Optional[str] = None
    font: Optional[Font] = None
    justify: Optional[str] = None
    repeat: Optional[int] = None
    incrx: Optional[float] = None
    incry: Optional[float] = None
    incrlabel: Optional[int] = None
    corner: Optional[CornerType] = None
    maxlen: Optional[int] = None
    maxheight: Optional[float] = None
    comment: Optional[str] = None

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "WorksheetText":
        # Text is the second element after 'tbtext'
        text = str(SExprParser.get_value(sexpr, 1, ""))

        # Parse font
        font_token = SExprParser.find_token(sexpr, "font")
        font = Font.from_sexpr(font_token) if font_token else None

        # Check for corner positioning
        corner = None
        for corner_type in CornerType:
            if SExprParser.find_token(sexpr, corner_type.value):
                corner = corner_type
                break

        return cls(
            text=text,
            position=SExprParser.get_position_with_default(sexpr, "at"),
            name=SExprParser.get_optional_str(sexpr, "name"),
            font=font,
            justify=SExprParser.get_optional_str(sexpr, "justify"),
            repeat=SExprParser.get_optional_int(sexpr, "repeat"),
            incrx=SExprParser.get_optional_float(sexpr, "incrx"),
            incry=SExprParser.get_optional_float(sexpr, "incry"),
            incrlabel=SExprParser.get_optional_int(sexpr, "incrlabel"),
            maxlen=SExprParser.get_optional_int(sexpr, "maxlen"),
            maxheight=SExprParser.get_optional_float(sexpr, "maxheight"),
            corner=corner,
            comment=SExprParser.get_optional_str(sexpr, "comment"),
        )

    def to_sexpr(self) -> SExpr:
        result = [
            Symbol("tbtext"),
            self.text,
            [Symbol("at"), self.position.x, self.position.y],
        ]

        if self.name is not None:
            result.append([Symbol("name"), self.name])
        if self.font is not None:
            result.append(self.font.to_sexpr())
        if self.justify is not None:
            result.append([Symbol("justify"), self.justify])
        if self.repeat is not None:
            result.append([Symbol("repeat"), self.repeat])
        if self.incrx is not None:
            result.append([Symbol("incrx"), self.incrx])
        if self.incry is not None:
            result.append([Symbol("incry"), self.incry])
        if self.incrlabel is not None:
            result.append([Symbol("incrlabel"), self.incrlabel])
        if self.maxlen is not None:
            result.append([Symbol("maxlen"), self.maxlen])
        if self.maxheight is not None:
            result.append([Symbol("maxheight"), self.maxheight])
        if self.corner is not None:
            result.append([Symbol(self.corner.value)])
        if self.comment is not None:
            result.append([Symbol("comment"), self.comment])

        return result


@dataclass
class WorksheetBitmap(KiCadObject):
    """Worksheet bitmap/image element"""

    position: Position
    name: Optional[str] = None
    scale: Optional[float] = None
    image: Optional[str] = None  # PNG data as base64 string
    repeat: Optional[int] = None
    incrx: Optional[float] = None
    incry: Optional[float] = None
    corner: Optional[CornerType] = None
    comment: Optional[str] = None

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "WorksheetBitmap":
        # Parse pngdata according to spec: (pngdata (data HEX_DATA))
        image_data = None
        pngdata_token = SExprParser.find_token(sexpr, "pngdata")
        if pngdata_token:
            data_token = SExprParser.find_token(pngdata_token, "data")
            if data_token:
                image_data = SExprParser.get_value(data_token, 1)

        # Check for corner positioning
        corner = None
        for corner_type in CornerType:
            if SExprParser.find_token(sexpr, corner_type.value):
                corner = corner_type
                break

        return cls(
            position=SExprParser.get_position_with_default(sexpr, "at"),
            name=SExprParser.get_optional_str(sexpr, "name"),
            scale=SExprParser.get_optional_float(sexpr, "scale"),
            image=image_data,
            repeat=SExprParser.get_optional_int(sexpr, "repeat"),
            incrx=SExprParser.get_optional_float(sexpr, "incrx"),
            incry=SExprParser.get_optional_float(sexpr, "incry"),
            corner=corner,
            comment=SExprParser.get_optional_str(sexpr, "comment"),
        )

    def to_sexpr(self) -> SExpr:
        result = [
            Symbol("bitmap"),
            [Symbol("at"), self.position.x, self.position.y],
        ]

        if self.name is not None:
            result.append([Symbol("name"), self.name])
        if self.scale is not None:
            result.append([Symbol("scale"), self.scale])
        if self.image is not None:
            result.append([Symbol("pngdata"), [Symbol("data"), self.image]])
        if self.repeat is not None:
            result.append([Symbol("repeat"), self.repeat])
        if self.incrx is not None:
            result.append([Symbol("incrx"), self.incrx])
        if self.incry is not None:
            result.append([Symbol("incry"), self.incry])
        if self.corner is not None:
            result.append([Symbol(self.corner.value)])
        if self.comment is not None:
            result.append([Symbol("comment"), self.comment])

        return result


# Main worksheet container


@dataclass
class KiCadWorksheet(KiCadObject):
    """KiCad Worksheet (.kicad_wks) file representation"""

    version: int = 20220228
    generator: str = "kicad_parser"
    setup: WorksheetSetup = field(default_factory=WorksheetSetup)
    lines: List[WorksheetLine] = field(default_factory=list)
    rectangles: List[WorksheetRectangle] = field(default_factory=list)
    polygons: List[WorksheetPolygon] = field(default_factory=list)
    texts: List[WorksheetText] = field(default_factory=list)
    bitmaps: List[WorksheetBitmap] = field(default_factory=list)

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "KiCadWorksheet":
        version = SExprParser.safe_get_int(sexpr, 1, 20220228)
        generator = str(SExprParser.get_value(sexpr, 2, "kicad_parser"))

        # Parse setup
        setup_token = SExprParser.find_token(sexpr, "setup")
        setup = (
            WorksheetSetup.from_sexpr(setup_token) if setup_token else WorksheetSetup()
        )

        # Parse drawing elements
        lines = []
        rectangles = []
        polygons = []
        texts = []
        bitmaps = []

        for item in sexpr[1:]:
            if isinstance(item, list) and len(item) > 0:
                token = item[0]
                if token == Symbol("line"):
                    lines.append(WorksheetLine.from_sexpr(item))
                elif token == Symbol("rect"):
                    rectangles.append(WorksheetRectangle.from_sexpr(item))
                elif token == Symbol("polygon"):
                    polygons.append(WorksheetPolygon.from_sexpr(item))
                elif token == Symbol("tbtext"):
                    texts.append(WorksheetText.from_sexpr(item))
                elif token == Symbol("bitmap"):
                    bitmaps.append(WorksheetBitmap.from_sexpr(item))

        return cls(
            version=version,
            generator=generator,
            setup=setup,
            lines=lines,
            rectangles=rectangles,
            polygons=polygons,
            texts=texts,
            bitmaps=bitmaps,
        )

    def to_sexpr(self) -> SExpr:
        result = [Symbol("kicad_wks"), self.version, self.generator]

        # Add setup
        result.append(self.setup.to_sexpr())

        # Add drawing elements
        for line in self.lines:
            result.append(line.to_sexpr())
        for rect in self.rectangles:
            result.append(rect.to_sexpr())
        for polygon in self.polygons:
            result.append(polygon.to_sexpr())
        for text in self.texts:
            result.append(text.to_sexpr())
        for bitmap in self.bitmaps:
            result.append(bitmap.to_sexpr())

        return result

    def add_line(self, line: WorksheetLine) -> None:
        """Add a line to the worksheet"""
        self.lines.append(line)

    def add_rectangle(self, rectangle: WorksheetRectangle) -> None:
        """Add a rectangle to the worksheet"""
        self.rectangles.append(rectangle)

    def add_polygon(self, polygon: WorksheetPolygon) -> None:
        """Add a polygon to the worksheet"""
        self.polygons.append(polygon)

    def add_text(self, text: WorksheetText) -> None:
        """Add a text element to the worksheet"""
        self.texts.append(text)

    def add_bitmap(self, bitmap: WorksheetBitmap) -> None:
        """Add a bitmap to the worksheet"""
        self.bitmaps.append(bitmap)
