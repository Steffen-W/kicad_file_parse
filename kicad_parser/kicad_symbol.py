"""
KiCad Symbol Library S-Expression Classes

This module contains classes for symbol library file formats,
including symbols, pins, graphic items, and symbol properties.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, cast

from .kicad_common import (
    CoordinatePoint,
    CoordinatePointList,
    Fill,
    KiCadObject,
    Position,
    SExpr,
    SExprParser,
    Stroke,
    Symbol,
    TextEffects,
    parse_kicad_file,
    write_kicad_file,
)

# Symbol-specific enums


class PinElectricalType(Enum):
    """Pin electrical types"""

    INPUT = "input"
    OUTPUT = "output"
    BIDIRECTIONAL = "bidirectional"
    TRI_STATE = "tri_state"
    PASSIVE = "passive"
    FREE = "free"
    UNSPECIFIED = "unspecified"
    POWER_IN = "power_in"
    POWER_OUT = "power_out"
    OPEN_COLLECTOR = "open_collector"
    OPEN_EMITTER = "open_emitter"
    NO_CONNECT = "no_connect"


class PinGraphicStyle(Enum):
    """Pin graphical styles"""

    LINE = "line"
    INVERTED = "inverted"
    CLOCK = "clock"
    INVERTED_CLOCK = "inverted_clock"
    INPUT_LOW = "input_low"
    CLOCK_LOW = "clock_low"
    OUTPUT_LOW = "output_low"
    EDGE_CLOCK_HIGH = "edge_clock_high"
    NON_LOGIC = "non_logic"


# Symbol graphic items


@dataclass
class SymbolArc(KiCadObject):
    """Symbol arc definition"""

    start: Position
    mid: Position
    end: Position
    stroke: Stroke = field(default_factory=Stroke)
    fill: Fill = field(default_factory=Fill)

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "SymbolArc":
        return cls(
            start=SExprParser.get_position_with_default(sexpr, "start"),
            mid=SExprParser.get_position_with_default(sexpr, "mid"),
            end=SExprParser.get_position_with_default(sexpr, "end"),
            stroke=SExprParser.parse_stroke_or_width(sexpr),
            fill=(
                Fill.from_sexpr(fill_token)
                if (fill_token := SExprParser.find_token(sexpr, "fill"))
                else Fill()
            ),
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("arc")]
        result.append([Symbol("start"), self.start.x, self.start.y])
        result.append([Symbol("mid"), self.mid.x, self.mid.y])
        result.append([Symbol("end"), self.end.x, self.end.y])
        result.append(self.stroke.to_sexpr())
        result.append(self.fill.to_sexpr())
        return result


@dataclass
class SymbolCircle(KiCadObject):
    """Symbol circle definition"""

    center: Position
    radius: float
    stroke: Stroke = field(default_factory=Stroke)
    fill: Fill = field(default_factory=Fill)

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "SymbolCircle":
        return cls(
            center=SExprParser.get_position_with_default(sexpr, "center"),
            radius=SExprParser.get_required_float(sexpr, "radius", default=0.0),
            stroke=SExprParser.parse_stroke_or_width(sexpr),
            fill=(
                Fill.from_sexpr(fill_token)
                if (fill_token := SExprParser.find_token(sexpr, "fill"))
                else Fill()
            ),
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("circle")]
        result.append([Symbol("center"), self.center.x, self.center.y])
        result.append([Symbol("radius"), self.radius])
        result.append(self.stroke.to_sexpr())
        result.append(self.fill.to_sexpr())
        return result


@dataclass
class SymbolBezier(KiCadObject):
    """Symbol Bezier curve definition"""

    points: CoordinatePointList
    stroke: Stroke = field(default_factory=Stroke)
    fill: Fill = field(default_factory=Fill)

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "SymbolBezier":
        pts_token = SExprParser.find_token(sexpr, "pts")

        # Handle direct coordinate points (legacy format)
        points = CoordinatePointList()
        if pts_token:
            points = CoordinatePointList.from_sexpr(pts_token)
        else:
            # Look for direct xy coordinates
            for item in sexpr[1:]:
                if isinstance(item, list) and len(item) > 0 and item[0] == Symbol("xy"):
                    if not points.points:
                        points = CoordinatePointList()
                    points.points.append(CoordinatePoint.from_sexpr(item))

        return cls(
            points=points,
            stroke=SExprParser.parse_stroke_or_width(sexpr),
            fill=(
                Fill.from_sexpr(fill_token)
                if (fill_token := SExprParser.find_token(sexpr, "fill"))
                else Fill()
            ),
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("bezier")]
        result.append(self.points.to_sexpr())
        result.append(self.stroke.to_sexpr())
        result.append(self.fill.to_sexpr())
        return result


@dataclass
class SymbolPolyline(KiCadObject):
    """Symbol polyline definition"""

    points: CoordinatePointList
    stroke: Stroke = field(default_factory=Stroke)
    fill: Fill = field(default_factory=Fill)

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "SymbolPolyline":
        pts_token = SExprParser.find_token(sexpr, "pts")

        return cls(
            points=(
                CoordinatePointList.from_sexpr(pts_token)
                if pts_token
                else CoordinatePointList()
            ),
            stroke=SExprParser.parse_stroke_or_width(sexpr),
            fill=(
                Fill.from_sexpr(fill_token)
                if (fill_token := SExprParser.find_token(sexpr, "fill"))
                else Fill()
            ),
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("polyline")]
        result.append(self.points.to_sexpr())
        result.append(self.stroke.to_sexpr())
        result.append(self.fill.to_sexpr())
        return result


@dataclass
class SymbolRectangle(KiCadObject):
    """Symbol rectangle definition"""

    start: Position
    end: Position
    stroke: Stroke = field(default_factory=Stroke)
    fill: Fill = field(default_factory=Fill)

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "SymbolRectangle":
        return cls(
            start=SExprParser.get_position_with_default(sexpr, "start"),
            end=SExprParser.get_position_with_default(sexpr, "end"),
            stroke=SExprParser.parse_stroke_or_width(sexpr),
            fill=(
                Fill.from_sexpr(fill_token)
                if (fill_token := SExprParser.find_token(sexpr, "fill"))
                else Fill()
            ),
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("rectangle")]
        result.append([Symbol("start"), self.start.x, self.start.y])
        result.append([Symbol("end"), self.end.x, self.end.y])
        result.append(self.stroke.to_sexpr())
        result.append(self.fill.to_sexpr())
        return result


@dataclass
class SymbolText(KiCadObject):
    """Symbol text definition"""

    text: str
    position: Position
    effects: TextEffects = field(default_factory=TextEffects)

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "SymbolText":
        text = SExprParser.normalize_text_content(
            str(SExprParser.get_value(sexpr, 1, ""))
        )
        return cls(
            text=text,
            position=(
                Position.from_sexpr(at_token)
                if (at_token := SExprParser.find_token(sexpr, "at"))
                else Position()
            ),
            effects=(
                TextEffects.from_sexpr(effects_token)
                if (effects_token := SExprParser.find_token(sexpr, "effects"))
                else TextEffects()
            ),
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("text"), self.text]
        result.append(self.position.to_sexpr())
        result.append(self.effects.to_sexpr())
        return result


@dataclass
class SymbolPin(KiCadObject):
    """Symbol pin definition"""

    electrical_type: PinElectricalType
    graphic_style: PinGraphicStyle
    position: Position
    length: float
    name: str
    name_effects: Optional[TextEffects] = None
    number: str = ""
    number_effects: Optional[TextEffects] = None

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "SymbolPin":
        electrical_type_str = str(SExprParser.get_value(sexpr, 1, "input"))
        # Normalize pin type for backward compatibility
        electrical_type_str = SExprParser.normalize_pin_electrical_type(
            electrical_type_str
        )

        electrical_type = PinElectricalType.INPUT
        try:
            electrical_type = PinElectricalType(electrical_type_str)
        except (ValueError, TypeError):
            # Invalid electrical type, use default
            electrical_type = PinElectricalType.INPUT

        graphic_style_str = str(SExprParser.get_value(sexpr, 2, "line"))
        graphic_style = PinGraphicStyle.LINE
        try:
            graphic_style = PinGraphicStyle(graphic_style_str)
        except (ValueError, TypeError):
            # Invalid graphic style, use default
            graphic_style = PinGraphicStyle.LINE

        name_token = SExprParser.find_token(sexpr, "name")
        number_token = SExprParser.find_token(sexpr, "number")

        name = ""
        name_effects = None
        if name_token and len(name_token) >= 2:
            name = SExprParser.normalize_text_content(str(name_token[1]))
            if len(name_token) > 2:
                effects_with_symbol = [Symbol("effects")] + name_token[2:]
                name_effects = TextEffects.from_sexpr(effects_with_symbol)

        number = ""
        number_effects = None
        if number_token and len(number_token) >= 2:
            number = str(number_token[1])
            if len(number_token) > 2:
                effects_with_symbol = [Symbol("effects")] + number_token[2:]
                number_effects = TextEffects.from_sexpr(effects_with_symbol)

        return cls(
            electrical_type=electrical_type,
            graphic_style=graphic_style,
            position=(
                Position.from_sexpr(at_token)
                if (at_token := SExprParser.find_token(sexpr, "at"))
                else Position()
            ),
            length=SExprParser.get_required_float(sexpr, "length", default=2.54),
            name=name,
            name_effects=name_effects,
            number=number,
            number_effects=number_effects,
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [
            Symbol("pin"),
            Symbol(self.electrical_type.value),
            Symbol(self.graphic_style.value),
        ]
        result.append(self.position.to_sexpr())
        result.append([Symbol("length"), self.length])

        name_expr = [Symbol("name"), self.name]
        if self.name_effects is not None and (
            self.name_effects.font.size_height != 1.27
            or self.name_effects.font.size_width != 1.27
            or self.name_effects.hide
        ):
            name_expr.extend(
                self.name_effects.to_sexpr()[1:]
            )  # Skip the 'effects' symbol
        result.append(name_expr)

        number_expr = [Symbol("number"), self.number]
        if self.number_effects is not None and (
            self.number_effects.font.size_height != 1.27
            or self.number_effects.font.size_width != 1.27
            or self.number_effects.hide
        ):
            number_expr.extend(
                self.number_effects.to_sexpr()[1:]
            )  # Skip the 'effects' symbol
        result.append(number_expr)

        return result


# Symbol properties


@dataclass
class SymbolProperty(KiCadObject):
    """Symbol property definition"""

    key: str
    value: str
    id: int
    position: Position
    effects: TextEffects = field(default_factory=TextEffects)

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "SymbolProperty":
        key = SExprParser.normalize_text_content(
            str(SExprParser.get_value(sexpr, 1, ""))
        )
        value = SExprParser.normalize_text_content(
            str(SExprParser.get_value(sexpr, 2, ""))
        )

        return cls(
            key=key,
            value=value,
            id=SExprParser.get_optional_int(sexpr, "id")
            or 0,  # Robustness: id optional (spec deviation)
            position=SExprParser.get_position_with_default(sexpr, "at"),
            effects=(
                TextEffects.from_sexpr(effects_token)
                if (effects_token := SExprParser.find_token(sexpr, "effects"))
                else TextEffects()
            ),
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("property"), self.key, self.value]
        result.append([Symbol("id"), self.id])
        result.append(self.position.to_sexpr())
        result.append(self.effects.to_sexpr())
        return result


# Symbol unit and main symbol classes


@dataclass
class SymbolUnit(KiCadObject):
    """Symbol unit definition"""

    name: str
    unit_name: Optional[str] = None

    # Graphic items
    arcs: List[SymbolArc] = field(default_factory=list)
    circles: List[SymbolCircle] = field(default_factory=list)
    beziers: List[SymbolBezier] = field(default_factory=list)
    polylines: List[SymbolPolyline] = field(default_factory=list)
    rectangles: List[SymbolRectangle] = field(default_factory=list)
    texts: List[SymbolText] = field(default_factory=list)
    pins: List[SymbolPin] = field(default_factory=list)

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "SymbolUnit":
        name = str(SExprParser.get_value(sexpr, 1, ""))

        unit = cls(
            name=name,
            unit_name=SExprParser.get_optional_str(sexpr, "unit_name"),
        )

        # Parse graphic items
        for arc_token in SExprParser.find_all_tokens(sexpr, "arc"):
            unit.arcs.append(SymbolArc.from_sexpr(arc_token))
        for circle_token in SExprParser.find_all_tokens(sexpr, "circle"):
            unit.circles.append(SymbolCircle.from_sexpr(circle_token))
        for bezier_token in SExprParser.find_all_tokens(sexpr, "bezier"):
            unit.beziers.append(SymbolBezier.from_sexpr(bezier_token))
        for polyline_token in SExprParser.find_all_tokens(sexpr, "polyline"):
            unit.polylines.append(SymbolPolyline.from_sexpr(polyline_token))
        for rectangle_token in SExprParser.find_all_tokens(sexpr, "rectangle"):
            unit.rectangles.append(SymbolRectangle.from_sexpr(rectangle_token))
        for text_token in SExprParser.find_all_tokens(sexpr, "text"):
            unit.texts.append(SymbolText.from_sexpr(text_token))
        for pin_token in SExprParser.find_all_tokens(sexpr, "pin"):
            unit.pins.append(SymbolPin.from_sexpr(pin_token))

        return unit

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("symbol"), self.name]

        # Add graphic items
        for arc in self.arcs:
            result.append(arc.to_sexpr())
        for circle in self.circles:
            result.append(circle.to_sexpr())
        for bezier in self.beziers:
            result.append(bezier.to_sexpr())
        for polyline in self.polylines:
            result.append(polyline.to_sexpr())
        for rectangle in self.rectangles:
            result.append(rectangle.to_sexpr())
        for text in self.texts:
            result.append(text.to_sexpr())
        for pin in self.pins:
            result.append(pin.to_sexpr())

        if self.unit_name:
            result.append([Symbol("unit_name"), self.unit_name])

        return result


@dataclass
class KiCadSymbol(KiCadObject):
    """Main KiCad symbol definition"""

    name: str
    extends: Optional[str] = None
    pin_numbers_hide: Optional[bool] = None
    pin_names_hide: Optional[bool] = None
    pin_names_offset: Optional[float] = None
    in_bom: Optional[bool] = None
    on_board: Optional[bool] = None
    exclude_from_sim: Optional[bool] = None
    exclude_from_bom: Optional[bool] = None
    exclude_from_board: Optional[bool] = None
    dnp: Optional[bool] = None
    power_flag: Optional[bool] = None

    # Symbol properties
    properties: List[SymbolProperty] = field(default_factory=list)

    # Graphic items (for main symbol)
    arcs: List[SymbolArc] = field(default_factory=list)
    circles: List[SymbolCircle] = field(default_factory=list)
    beziers: List[SymbolBezier] = field(default_factory=list)
    polylines: List[SymbolPolyline] = field(default_factory=list)
    rectangles: List[SymbolRectangle] = field(default_factory=list)
    texts: List[SymbolText] = field(default_factory=list)
    pins: List[SymbolPin] = field(default_factory=list)

    # Symbol units
    units: List[SymbolUnit] = field(default_factory=list)

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "KiCadSymbol":
        name = SExprParser.normalize_text_content(
            str(SExprParser.get_value(sexpr, 1, ""))
        )

        pin_numbers_token = SExprParser.find_token(sexpr, "pin_numbers")
        pin_names_token = SExprParser.find_token(sexpr, "pin_names")

        # Parse pin_names offset and hide flag
        pin_names_offset = None
        pin_names_hide = None
        if pin_names_token:
            pin_names_hide = SExprParser.has_symbol(pin_names_token, "hide")
            pin_names_offset = SExprParser.get_optional_float(pin_names_token, "offset")

        symbol = cls(
            name=name,
            extends=SExprParser.get_optional_str(sexpr, "extends"),
            pin_numbers_hide=(
                SExprParser.has_symbol(pin_numbers_token, "hide")
                if pin_numbers_token
                else None
            ),
            pin_names_hide=pin_names_hide,
            pin_names_offset=pin_names_offset,
            in_bom=(
                SExprParser.get_value(in_bom_token, 1) == Symbol("yes")
                if (in_bom_token := SExprParser.find_token(sexpr, "in_bom"))
                else None
            ),
            on_board=(
                SExprParser.get_value(on_board_token, 1) == Symbol("yes")
                if (on_board_token := SExprParser.find_token(sexpr, "on_board"))
                else None
            ),
            exclude_from_sim=(
                SExprParser.get_value(exclude_from_sim_token, 1) == Symbol("yes")
                if (
                    exclude_from_sim_token := SExprParser.find_token(
                        sexpr, "exclude_from_sim"
                    )
                )
                else None
            ),
            exclude_from_bom=(
                SExprParser.get_value(exclude_from_bom_token, 1) == Symbol("yes")
                if (
                    exclude_from_bom_token := SExprParser.find_token(
                        sexpr, "exclude_from_bom"
                    )
                )
                else None
            ),
            exclude_from_board=(
                SExprParser.get_value(exclude_from_board_token, 1) == Symbol("yes")
                if (
                    exclude_from_board_token := SExprParser.find_token(
                        sexpr, "exclude_from_board"
                    )
                )
                else None
            ),
            dnp=(
                SExprParser.get_value(dnp_token, 1) == Symbol("yes")
                if (dnp_token := SExprParser.find_token(sexpr, "dnp"))
                else None
            ),
            power_flag=(
                SExprParser.get_value(power_flag_token, 1) == Symbol("yes")
                if (power_flag_token := SExprParser.find_token(sexpr, "power_flag"))
                else None
            ),
        )

        # Parse properties
        for prop_token in SExprParser.find_all_tokens(sexpr, "property"):
            symbol.properties.append(SymbolProperty.from_sexpr(prop_token))

        # Parse graphic items (main symbol level)
        for arc_token in SExprParser.find_all_tokens(sexpr, "arc"):
            symbol.arcs.append(SymbolArc.from_sexpr(arc_token))
        for circle_token in SExprParser.find_all_tokens(sexpr, "circle"):
            symbol.circles.append(SymbolCircle.from_sexpr(circle_token))
        for bezier_token in SExprParser.find_all_tokens(sexpr, "bezier"):
            symbol.beziers.append(SymbolBezier.from_sexpr(bezier_token))
        for polyline_token in SExprParser.find_all_tokens(sexpr, "polyline"):
            symbol.polylines.append(SymbolPolyline.from_sexpr(polyline_token))
        for rectangle_token in SExprParser.find_all_tokens(sexpr, "rectangle"):
            symbol.rectangles.append(SymbolRectangle.from_sexpr(rectangle_token))
        for text_token in SExprParser.find_all_tokens(sexpr, "text"):
            symbol.texts.append(SymbolText.from_sexpr(text_token))
        for pin_token in SExprParser.find_all_tokens(sexpr, "pin"):
            symbol.pins.append(SymbolPin.from_sexpr(pin_token))

        # Parse symbol units
        for unit_token in SExprParser.find_all_tokens(sexpr, "symbol"):
            symbol.units.append(SymbolUnit.from_sexpr(unit_token))

        return symbol

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("symbol"), self.name]

        if self.extends:
            result.append([Symbol("extends"), self.extends])

        if self.pin_numbers_hide is not None and self.pin_numbers_hide:
            result.append([Symbol("pin_numbers"), Symbol("hide")])

        pin_names_expr: SExpr = []
        if self.pin_names_offset is not None or (
            self.pin_names_hide is not None and self.pin_names_hide
        ):
            pin_names_expr = [Symbol("pin_names")]
            if self.pin_names_offset is not None:
                pin_names_expr.append([Symbol("offset"), self.pin_names_offset])
            if self.pin_names_hide is not None and self.pin_names_hide:
                pin_names_expr.append(Symbol("hide"))
            result.append(pin_names_expr)

        if self.in_bom is not None:
            result.append([Symbol("in_bom"), Symbol("yes" if self.in_bom else "no")])
        if self.on_board is not None:
            result.append(
                [Symbol("on_board"), Symbol("yes" if self.on_board else "no")]
            )

        if self.exclude_from_sim is not None:
            result.append(
                [
                    Symbol("exclude_from_sim"),
                    Symbol("yes" if self.exclude_from_sim else "no"),
                ]
            )
        if self.exclude_from_bom is not None:
            result.append(
                [
                    Symbol("exclude_from_bom"),
                    Symbol("yes" if self.exclude_from_bom else "no"),
                ]
            )
        if self.exclude_from_board is not None:
            result.append(
                [
                    Symbol("exclude_from_board"),
                    Symbol("yes" if self.exclude_from_board else "no"),
                ]
            )
        if self.dnp is not None:
            result.append([Symbol("dnp"), Symbol("yes" if self.dnp else "no")])
        if self.power_flag is not None:
            result.append(
                [Symbol("power_flag"), Symbol("yes" if self.power_flag else "no")]
            )

        # Add properties
        for prop in self.properties:
            result.append(prop.to_sexpr())

        # Add graphic items
        for arc in self.arcs:
            result.append(arc.to_sexpr())
        for circle in self.circles:
            result.append(circle.to_sexpr())
        for bezier in self.beziers:
            result.append(bezier.to_sexpr())
        for polyline in self.polylines:
            result.append(polyline.to_sexpr())
        for rectangle in self.rectangles:
            result.append(rectangle.to_sexpr())
        for text in self.texts:
            result.append(text.to_sexpr())
        for pin in self.pins:
            result.append(pin.to_sexpr())

        # Add symbol units
        for unit in self.units:
            result.append(unit.to_sexpr())

        return result

    # Utility methods for property management
    def get_property(self, key: str) -> Optional[SymbolProperty]:
        """Get property by key"""
        return next((p for p in self.properties if p.key == key), None)

    def set_property(
        self,
        key: str,
        value: str,
        id: Optional[int] = None,
        position: Optional[Position] = None,
        effects: Optional[TextEffects] = None,
    ) -> None:
        """Set or add property"""
        prop = self.get_property(key)
        if prop:
            prop.value = value
            if position:
                prop.position = position
            if effects:
                prop.effects = effects
        else:
            if id is None:
                # Find highest ID and increment
                max_id = max([p.id for p in self.properties], default=-1)
                id = max_id + 1

            self.properties.append(
                SymbolProperty(
                    key=key,
                    value=value,
                    id=id,
                    position=position or Position(0, 0),
                    effects=effects or TextEffects(),
                )
            )

    def remove_property(self, key: str) -> bool:
        """Remove property by key"""
        original_count = len(self.properties)
        self.properties = [p for p in self.properties if p.key != key]
        return len(self.properties) < original_count


@dataclass
class KiCadSymbolLibrary(KiCadObject):
    """KiCad symbol library container"""

    version: int = 20211014
    generator: str = "kicad_symbol_editor"
    symbols: List[KiCadSymbol] = field(default_factory=list)

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "KiCadSymbolLibrary":
        library = cls(
            version=SExprParser.get_required_int(sexpr, "version", default=20211014),
            generator=SExprParser.get_optional_str(sexpr, "generator")
            or "kicad_symbol_editor",
        )

        # Parse symbols
        for symbol_token in SExprParser.find_all_tokens(sexpr, "symbol"):
            library.symbols.append(KiCadSymbol.from_sexpr(symbol_token))

        return library

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("kicad_symbol_lib")]
        result.append([Symbol("version"), self.version])
        result.append([Symbol("generator"), Symbol(self.generator)])

        for symbol in self.symbols:
            result.append(symbol.to_sexpr())

        return result

    # Utility methods
    def get_symbol(self, name: str) -> Optional[KiCadSymbol]:
        """Get symbol by name"""
        return next((s for s in self.symbols if s.name == name), None)

    def add_symbol(self, symbol: KiCadSymbol) -> None:
        """Add symbol to library

        Returns:
            None
        """
        # Remove existing symbol with same name
        self.symbols = [s for s in self.symbols if s.name != symbol.name]
        self.symbols.append(symbol)

    def remove_symbol(self, name: str) -> bool:
        """Remove symbol by name"""
        original_count = len(self.symbols)
        self.symbols = [s for s in self.symbols if s.name != name]
        return len(self.symbols) < original_count


# High-level API functions


def parse_kicad_symbol_file(file_content: str) -> KiCadSymbolLibrary:
    """Parse KiCad symbol file from string content"""
    return cast(KiCadSymbolLibrary, parse_kicad_file(file_content, KiCadSymbolLibrary))


def write_kicad_symbol_file(library: KiCadSymbolLibrary) -> str:
    """Write KiCad symbol library to string"""
    return write_kicad_file(library)


def load_symbol_file(filepath: str) -> KiCadSymbolLibrary:
    """Load symbol file from disk"""
    with open(filepath, "r", encoding="utf-8") as f:
        return parse_kicad_symbol_file(f.read())


def save_symbol_file(library: KiCadSymbolLibrary, filepath: str) -> None:
    """Save symbol library to disk

    Returns:
        None
    """
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(write_kicad_symbol_file(library))
