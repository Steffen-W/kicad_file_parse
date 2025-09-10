"""
KiCad Schematic S-Expression Classes

This module contains classes for schematic file format (.kicad_sch),
including all schematic-specific elements like junctions, wires, buses,
labels, symbols, and hierarchical sheets.

Based on: doc/file-formats/sexpr-schematic/_index.en.adoc
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, cast

from .kicad_common import (
    UUID,
    CoordinatePointList,
    Image,
    KiCadObject,
    PageSettings,
    Position,
    Property,
    SExpr,
    SExprParser,
    Stroke,
    Symbol,
    TextEffects,
    TitleBlock,
    parse_kicad_file,
    write_kicad_file,
)
from .kicad_symbol import KiCadSymbol


# Schematic-specific enums
class LabelShape(Enum):
    """Label and pin shapes for global labels, hierarchical labels, and sheet pins"""

    INPUT = "input"
    OUTPUT = "output"
    BIDIRECTIONAL = "bidirectional"
    TRI_STATE = "tri_state"
    PASSIVE = "passive"


class PinElectricalType(Enum):
    """Electrical connection types for hierarchical sheet pins"""

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


# Junction Section
@dataclass
class Junction(KiCadObject):
    """Junction in the schematic"""

    position: Position
    diameter: float = 0.0  # 0.0 = system default
    color: Optional[Tuple[float, float, float, float]] = None  # R, G, B, A
    uuid: UUID = field(default_factory=lambda: UUID(""))

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "Junction":
        at_token = SExprParser.find_token(sexpr, "at")
        diameter_token = SExprParser.find_token(sexpr, "diameter")
        color_token = SExprParser.find_token(sexpr, "color")
        uuid_token = SExprParser.find_token(sexpr, "uuid")

        return cls(
            position=Position.from_sexpr(at_token) if at_token else Position(0, 0),
            diameter=(
                SExprParser.safe_get_float(diameter_token, 1, 0.0)
                if diameter_token
                else 0.0
            ),
            color=(
                tuple(color_token[1:5])
                if color_token and len(color_token) >= 5
                else None
            ),
            uuid=UUID.from_sexpr(uuid_token) if uuid_token else UUID(""),
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("junction")]
        result.append(self.position.to_sexpr())
        result.append([Symbol("diameter"), self.diameter])

        if self.color:
            result.append([Symbol("color")] + list(self.color))

        result.append(self.uuid.to_sexpr())
        return result


# No Connect Section
@dataclass
class NoConnect(KiCadObject):
    """No connect marker for unused pins"""

    position: Position
    uuid: UUID = field(default_factory=lambda: UUID(""))

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "NoConnect":
        at_token = SExprParser.find_token(sexpr, "at")
        uuid_token = SExprParser.find_token(sexpr, "uuid")

        return cls(
            position=Position.from_sexpr(at_token) if at_token else Position(0, 0),
            uuid=UUID.from_sexpr(uuid_token) if uuid_token else UUID(""),
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("no_connect")]
        result.append(self.position.to_sexpr())
        result.append(self.uuid.to_sexpr())
        return result


# Bus Entry Section
@dataclass
class BusEntry(KiCadObject):
    """Bus entry connection"""

    position: Position
    size: Tuple[float, float]  # X, Y distance from position
    stroke: Stroke = field(default_factory=Stroke)
    uuid: UUID = field(default_factory=lambda: UUID(""))

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "BusEntry":
        at_token = SExprParser.find_token(sexpr, "at")
        size_token = SExprParser.find_token(sexpr, "size")
        stroke_token = SExprParser.find_token(sexpr, "stroke")
        uuid_token = SExprParser.find_token(sexpr, "uuid")

        size = (0.0, 0.0)
        if size_token and len(size_token) >= 3:
            size = (
                SExprParser.safe_float(size_token[1], 0.0),
                SExprParser.safe_float(size_token[2], 0.0),
            )

        return cls(
            position=Position.from_sexpr(at_token) if at_token else Position(0, 0),
            size=size,
            stroke=Stroke.from_sexpr(stroke_token) if stroke_token else Stroke(),
            uuid=UUID.from_sexpr(uuid_token) if uuid_token else UUID(""),
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("bus_entry")]
        result.append(self.position.to_sexpr())
        result.append([Symbol("size"), self.size[0], self.size[1]])
        result.append(self.stroke.to_sexpr())
        result.append(self.uuid.to_sexpr())
        return result


# Wire and Bus Section
@dataclass
class Wire(KiCadObject):
    """Wire connection"""

    points: CoordinatePointList  # Start and end points
    stroke: Stroke = field(default_factory=Stroke)
    uuid: UUID = field(default_factory=lambda: UUID(""))

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "Wire":
        pts_token = SExprParser.find_token(sexpr, "pts")
        stroke_token = SExprParser.find_token(sexpr, "stroke")
        uuid_token = SExprParser.find_token(sexpr, "uuid")

        return cls(
            points=(
                CoordinatePointList.from_sexpr(pts_token)
                if pts_token
                else CoordinatePointList()
            ),
            stroke=Stroke.from_sexpr(stroke_token) if stroke_token else Stroke(),
            uuid=UUID.from_sexpr(uuid_token) if uuid_token else UUID(""),
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("wire")]

        result.append(self.points.to_sexpr())
        result.append(self.stroke.to_sexpr())
        result.append(self.uuid.to_sexpr())
        return result


@dataclass
class Bus(KiCadObject):
    """Bus connection"""

    points: CoordinatePointList  # Start and end points
    stroke: Stroke = field(default_factory=Stroke)
    uuid: UUID = field(default_factory=lambda: UUID(""))

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "Bus":
        pts_token = SExprParser.find_token(sexpr, "pts")
        stroke_token = SExprParser.find_token(sexpr, "stroke")
        uuid_token = SExprParser.find_token(sexpr, "uuid")

        return cls(
            points=(
                CoordinatePointList.from_sexpr(pts_token)
                if pts_token
                else CoordinatePointList()
            ),
            stroke=Stroke.from_sexpr(stroke_token) if stroke_token else Stroke(),
            uuid=UUID.from_sexpr(uuid_token) if uuid_token else UUID(""),
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("bus")]

        result.append(self.points.to_sexpr())
        result.append(self.stroke.to_sexpr())
        result.append(self.uuid.to_sexpr())
        return result


# Graphical Line Section
@dataclass
class Polyline(KiCadObject):
    """Graphical polyline (one or more connected lines)"""

    points: CoordinatePointList  # Line points
    stroke: Stroke = field(default_factory=Stroke)
    uuid: UUID = field(default_factory=lambda: UUID(""))

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "Polyline":
        pts_token = SExprParser.find_token(sexpr, "pts")
        stroke_token = SExprParser.find_token(sexpr, "stroke")
        uuid_token = SExprParser.find_token(sexpr, "uuid")

        return cls(
            points=(
                CoordinatePointList.from_sexpr(pts_token)
                if pts_token
                else CoordinatePointList()
            ),
            stroke=Stroke.from_sexpr(stroke_token) if stroke_token else Stroke(),
            uuid=UUID.from_sexpr(uuid_token) if uuid_token else UUID(""),
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("polyline")]

        result.append(self.points.to_sexpr())
        result.append(self.stroke.to_sexpr())
        result.append(self.uuid.to_sexpr())
        return result


# Text and Label Sections
@dataclass
class SchematicText(KiCadObject):
    """Graphical text in schematic"""

    text: str
    position: Position
    effects: TextEffects = field(default_factory=TextEffects)
    uuid: UUID = field(default_factory=lambda: UUID(""))

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "SchematicText":
        text = SExprParser.normalize_text_content(
            str(SExprParser.get_value(sexpr, 1, ""))
        )
        at_token = SExprParser.find_token(sexpr, "at")
        effects_token = SExprParser.find_token(sexpr, "effects")
        uuid_token = SExprParser.find_token(sexpr, "uuid")

        return cls(
            text=text,
            position=Position.from_sexpr(at_token) if at_token else Position(0, 0),
            effects=(
                TextEffects.from_sexpr(effects_token)
                if effects_token
                else TextEffects()
            ),
            uuid=UUID.from_sexpr(uuid_token) if uuid_token else UUID(""),
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("text"), self.text]
        result.append(self.position.to_sexpr())
        result.append(self.effects.to_sexpr())
        result.append(self.uuid.to_sexpr())
        return result


@dataclass
class LocalLabel(KiCadObject):
    """Local wire/bus label"""

    text: str
    position: Position
    effects: TextEffects = field(default_factory=TextEffects)
    uuid: UUID = field(default_factory=lambda: UUID(""))

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "LocalLabel":
        text = SExprParser.normalize_text_content(
            str(SExprParser.get_value(sexpr, 1, ""))
        )
        at_token = SExprParser.find_token(sexpr, "at")
        effects_token = SExprParser.find_token(sexpr, "effects")
        uuid_token = SExprParser.find_token(sexpr, "uuid")

        return cls(
            text=text,
            position=Position.from_sexpr(at_token) if at_token else Position(0, 0),
            effects=(
                TextEffects.from_sexpr(effects_token)
                if effects_token
                else TextEffects()
            ),
            uuid=UUID.from_sexpr(uuid_token) if uuid_token else UUID(""),
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("label"), self.text]
        result.append(self.position.to_sexpr())
        result.append(self.effects.to_sexpr())
        result.append(self.uuid.to_sexpr())
        return result


@dataclass
class GlobalLabel(KiCadObject):
    """Global label visible across all schematics"""

    text: str
    shape: LabelShape = LabelShape.INPUT
    position: Position = field(default_factory=Position)
    effects: TextEffects = field(default_factory=TextEffects)
    uuid: UUID = field(default_factory=lambda: UUID(""))
    properties: List[Property] = field(default_factory=list)
    fields_autoplaced: bool = False

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "GlobalLabel":
        text = SExprParser.normalize_text_content(
            str(SExprParser.get_value(sexpr, 1, ""))
        )

        shape_token = SExprParser.find_token(sexpr, "shape")
        at_token = SExprParser.find_token(sexpr, "at")
        effects_token = SExprParser.find_token(sexpr, "effects")
        uuid_token = SExprParser.find_token(sexpr, "uuid")

        # Parse properties
        properties = []
        property_tokens = SExprParser.find_all_tokens(sexpr, "property")
        for prop_token in property_tokens:
            properties.append(Property.from_sexpr(prop_token))

        return cls(
            text=text,
            shape=SExprParser.parse_enum(
                SExprParser.get_value(shape_token, 1) if shape_token else None,
                LabelShape,
                LabelShape.INPUT,
            ),
            position=Position.from_sexpr(at_token) if at_token else Position(0, 0),
            effects=(
                TextEffects.from_sexpr(effects_token)
                if effects_token
                else TextEffects()
            ),
            uuid=UUID.from_sexpr(uuid_token) if uuid_token else UUID(""),
            properties=properties,
            fields_autoplaced=SExprParser.has_symbol(sexpr, "fields_autoplaced"),
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("global_label"), self.text]
        result.append([Symbol("shape"), Symbol(self.shape.value)])

        if self.fields_autoplaced:
            result.append(Symbol("fields_autoplaced"))

        result.append(self.position.to_sexpr())
        result.append(self.effects.to_sexpr())
        result.append(self.uuid.to_sexpr())

        for prop in self.properties:
            result.append(prop.to_sexpr())

        return result


@dataclass
class HierarchicalLabel(KiCadObject):
    """Hierarchical label for sheet connections"""

    text: str
    shape: LabelShape = LabelShape.INPUT
    position: Position = field(default_factory=Position)
    effects: TextEffects = field(default_factory=TextEffects)
    uuid: UUID = field(default_factory=lambda: UUID(""))

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "HierarchicalLabel":
        text = SExprParser.normalize_text_content(
            str(SExprParser.get_value(sexpr, 1, ""))
        )

        shape_token = SExprParser.find_token(sexpr, "shape")
        at_token = SExprParser.find_token(sexpr, "at")
        effects_token = SExprParser.find_token(sexpr, "effects")
        uuid_token = SExprParser.find_token(sexpr, "uuid")

        return cls(
            text=text,
            shape=SExprParser.parse_enum(
                SExprParser.get_value(shape_token, 1) if shape_token else None,
                LabelShape,
                LabelShape.INPUT,
            ),
            position=Position.from_sexpr(at_token) if at_token else Position(0, 0),
            effects=(
                TextEffects.from_sexpr(effects_token)
                if effects_token
                else TextEffects()
            ),
            uuid=UUID.from_sexpr(uuid_token) if uuid_token else UUID(""),
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("hierarchical_label"), self.text]
        result.append([Symbol("shape"), Symbol(self.shape.value)])
        result.append(self.position.to_sexpr())
        result.append(self.effects.to_sexpr())
        result.append(self.uuid.to_sexpr())
        return result


# Symbol Instance Classes
@dataclass
class SymbolInstance:
    """Symbol instance data for a specific project and path"""

    reference: str
    unit: int = 1

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "SymbolInstance":
        ref_token = SExprParser.find_token(sexpr, "reference")
        unit_token = SExprParser.find_token(sexpr, "unit")

        return cls(
            reference=str(SExprParser.get_value(ref_token, 1, "")) if ref_token else "",
            unit=(SExprParser.safe_get_int(unit_token, 1, 1) if unit_token else 1),
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = []
        result.append([Symbol("reference"), self.reference])
        result.append([Symbol("unit"), self.unit])
        return result


@dataclass
class SymbolProject:
    """Project-specific symbol instance data"""

    name: str
    instances: Dict[str, SymbolInstance] = field(
        default_factory=dict
    )  # path -> instance

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "SymbolProject":
        name = str(SExprParser.get_value(sexpr, 1, ""))
        instances = {}

        path_tokens = SExprParser.find_all_tokens(sexpr, "path")
        for path_token in path_tokens:
            if len(path_token) >= 2:
                path = str(path_token[1])
                instance = SymbolInstance.from_sexpr(path_token)
                instances[path] = instance

        return cls(name=name, instances=instances)

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("project"), self.name]

        for path, instance in sorted(self.instances.items()):
            path_sexpr = [Symbol("path"), path] + instance.to_sexpr()
            result.append(path_sexpr)

        return result


@dataclass
class SymbolPin:
    """Symbol pin with UUID"""

    number: str
    uuid: UUID

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "SymbolPin":
        number = str(SExprParser.get_value(sexpr, 1, ""))
        uuid_token = SExprParser.find_token(sexpr, "uuid")

        return cls(
            number=number, uuid=UUID.from_sexpr(uuid_token) if uuid_token else UUID("")
        )

    def to_sexpr(self) -> SExpr:
        return [Symbol("pin"), self.number, self.uuid.to_sexpr()]


# Symbol Section
@dataclass
class SchematicSymbol(KiCadObject):
    """Symbol instance in schematic"""

    library_id: str  # Library identifier
    position: Position = field(default_factory=Position)
    unit: int = 1
    in_bom: bool = True
    on_board: bool = True
    uuid: UUID = field(default_factory=lambda: UUID(""))
    properties: List[Property] = field(default_factory=list)
    pins: List[SymbolPin] = field(default_factory=list)
    projects: List[SymbolProject] = field(default_factory=list)

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "SchematicSymbol":
        library_id = str(SExprParser.get_value(sexpr, 1, ""))

        at_token = SExprParser.find_token(sexpr, "at")
        unit_token = SExprParser.find_token(sexpr, "unit")
        in_bom_token = SExprParser.find_token(sexpr, "in_bom")
        on_board_token = SExprParser.find_token(sexpr, "on_board")
        uuid_token = SExprParser.find_token(sexpr, "uuid")

        # Parse properties
        properties = []
        property_tokens = SExprParser.find_all_tokens(sexpr, "property")
        for prop_token in property_tokens:
            properties.append(Property.from_sexpr(prop_token))

        # Parse pins
        pins = []
        pin_tokens = SExprParser.find_all_tokens(sexpr, "pin")
        for pin_token in pin_tokens:
            pins.append(SymbolPin.from_sexpr(pin_token))

        # Parse instances
        projects = []
        instances_token = SExprParser.find_token(sexpr, "instances")
        if instances_token:
            project_tokens = SExprParser.find_all_tokens(instances_token, "project")
            for project_token in project_tokens:
                projects.append(SymbolProject.from_sexpr(project_token))

        return cls(
            library_id=library_id,
            position=Position.from_sexpr(at_token) if at_token else Position(0, 0),
            unit=(SExprParser.safe_get_int(unit_token, 1, 1) if unit_token else 1),
            in_bom=(
                str(SExprParser.get_value(in_bom_token, 1, "yes")).lower() == "yes"
                if in_bom_token
                else True
            ),
            on_board=(
                str(SExprParser.get_value(on_board_token, 1, "yes")).lower() == "yes"
                if on_board_token
                else True
            ),
            uuid=UUID.from_sexpr(uuid_token) if uuid_token else UUID(""),
            properties=properties,
            pins=pins,
            projects=projects,
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("symbol"), self.library_id]
        result.append(self.position.to_sexpr())
        result.append([Symbol("unit"), self.unit])
        result.append([Symbol("in_bom"), "yes" if self.in_bom else "no"])
        result.append([Symbol("on_board"), "yes" if self.on_board else "no"])
        result.append(self.uuid.to_sexpr())

        for prop in self.properties:
            result.append(prop.to_sexpr())

        for pin in self.pins:
            result.append(pin.to_sexpr())

        if self.projects:
            instances: SExpr = [Symbol("instances")]
            for project in self.projects:
                instances.append(project.to_sexpr())
            result.append(instances)

        return result


# Hierarchical Sheet Classes
@dataclass
class HierarchicalPin(KiCadObject):
    """Pin on hierarchical sheet"""

    name: str
    electrical_type: PinElectricalType = PinElectricalType.INPUT
    position: Position = field(default_factory=Position)
    effects: TextEffects = field(default_factory=TextEffects)
    uuid: UUID = field(default_factory=lambda: UUID(""))

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "HierarchicalPin":
        name = str(SExprParser.get_value(sexpr, 1, ""))

        # Electrical type is the second token
        elec_type = SExprParser.parse_enum(
            SExprParser.get_value(sexpr, 2), PinElectricalType, PinElectricalType.INPUT
        )

        at_token = SExprParser.find_token(sexpr, "at")
        effects_token = SExprParser.find_token(sexpr, "effects")
        uuid_token = SExprParser.find_token(sexpr, "uuid")

        return cls(
            name=name,
            electrical_type=elec_type,
            position=Position.from_sexpr(at_token) if at_token else Position(0, 0),
            effects=(
                TextEffects.from_sexpr(effects_token)
                if effects_token
                else TextEffects()
            ),
            uuid=UUID.from_sexpr(uuid_token) if uuid_token else UUID(""),
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("pin"), self.name, Symbol(self.electrical_type.value)]
        result.append(self.position.to_sexpr())
        result.append(self.effects.to_sexpr())
        result.append(self.uuid.to_sexpr())
        return result


@dataclass
class SheetInstance:
    """Sheet instance data for a specific project and path"""

    page: str = "1"

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "SheetInstance":
        page_token = SExprParser.find_token(sexpr, "page")

        return cls(
            page=str(SExprParser.get_value(page_token, 1, "1")) if page_token else "1"
        )

    def to_sexpr(self) -> SExpr:
        return [[Symbol("page"), self.page]]


@dataclass
class SheetProject:
    """Project-specific sheet instance data"""

    name: str
    instances: Dict[str, SheetInstance] = field(
        default_factory=dict
    )  # path -> instance

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "SheetProject":
        name = str(SExprParser.get_value(sexpr, 1, ""))
        instances = {}

        path_tokens = SExprParser.find_all_tokens(sexpr, "path")
        for path_token in path_tokens:
            if len(path_token) >= 2:
                path = str(path_token[1])
                instance = SheetInstance.from_sexpr(path_token)
                instances[path] = instance

        return cls(name=name, instances=instances)

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("project"), self.name]

        for path, instance in sorted(self.instances.items()):
            path_sexpr = [Symbol("path"), path] + instance.to_sexpr()
            result.append(path_sexpr)

        return result


@dataclass
class HierarchicalSheet(KiCadObject):
    """Hierarchical sheet"""

    position: Position = field(default_factory=Position)
    size: Tuple[float, float] = (25.4, 25.4)  # Width, Height
    stroke: Stroke = field(default_factory=Stroke)
    fill_color: Optional[Tuple[float, float, float, float]] = None  # R, G, B, A
    uuid: UUID = field(default_factory=lambda: UUID(""))
    sheet_name: str = ""
    file_name: str = ""
    pins: List[HierarchicalPin] = field(default_factory=list)
    projects: List[SheetProject] = field(default_factory=list)
    fields_autoplaced: bool = False

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "HierarchicalSheet":
        at_token = SExprParser.find_token(sexpr, "at")
        size_token = SExprParser.find_token(sexpr, "size")
        stroke_token = SExprParser.find_token(sexpr, "stroke")
        fill_token = SExprParser.find_token(sexpr, "fill")
        uuid_token = SExprParser.find_token(sexpr, "uuid")

        size = (25.4, 25.4)
        if size_token and len(size_token) >= 3:
            size = (
                SExprParser.safe_float(size_token[1], 25.4),
                SExprParser.safe_float(size_token[2], 25.4),
            )

        # Parse fill color
        fill_color = None
        if fill_token:
            color_token = SExprParser.find_token(fill_token, "color")
            if color_token and len(color_token) >= 5:
                fill_color = tuple(color_token[1:5])

        # Parse properties to find sheet name and file name
        sheet_name = ""
        file_name = ""
        property_tokens = SExprParser.find_all_tokens(sexpr, "property")
        for prop_token in property_tokens:
            if len(prop_token) >= 3:
                key = str(prop_token[1])
                value = str(prop_token[2])
                if key == "Sheetname":
                    sheet_name = value
                elif key == "Sheetfile":
                    file_name = value

        # Parse pins
        pins = []
        pin_tokens = SExprParser.find_all_tokens(sexpr, "pin")
        for pin_token in pin_tokens:
            pins.append(HierarchicalPin.from_sexpr(pin_token))

        # Parse instances
        projects = []
        instances_token = SExprParser.find_token(sexpr, "instances")
        if instances_token:
            project_tokens = SExprParser.find_all_tokens(instances_token, "project")
            for project_token in project_tokens:
                projects.append(SheetProject.from_sexpr(project_token))

        return cls(
            position=Position.from_sexpr(at_token) if at_token else Position(0, 0),
            size=size,
            stroke=Stroke.from_sexpr(stroke_token) if stroke_token else Stroke(),
            fill_color=fill_color,
            uuid=UUID.from_sexpr(uuid_token) if uuid_token else UUID(""),
            sheet_name=sheet_name,
            file_name=file_name,
            pins=pins,
            projects=projects,
            fields_autoplaced=SExprParser.has_symbol(sexpr, "fields_autoplaced"),
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("sheet")]
        result.append(self.position.to_sexpr())
        result.append([Symbol("size"), self.size[0], self.size[1]])

        if self.fields_autoplaced:
            result.append(Symbol("fields_autoplaced"))

        result.append(self.stroke.to_sexpr())

        # Fill definition
        if self.fill_color:
            fill_def: SExpr = [
                Symbol("fill"),
                [Symbol("color")] + list(self.fill_color),
            ]
        else:
            fill_def = [Symbol("fill"), [Symbol("type"), Symbol("none")]]
        result.append(fill_def)

        result.append(self.uuid.to_sexpr())

        # Add sheet name and file name as properties
        if self.sheet_name:
            result.append([Symbol("property"), "Sheetname", self.sheet_name])
        if self.file_name:
            result.append([Symbol("property"), "Sheetfile", self.file_name])

        # Add pins
        for pin in self.pins:
            result.append(pin.to_sexpr())

        # Add instances
        if self.projects:
            instances: SExpr = [Symbol("instances")]
            for project in self.projects:
                instances.append(project.to_sexpr())
            result.append(instances)

        return result


# Root Sheet Instance
@dataclass
class RootSheetInstance(KiCadObject):
    """Root sheet instance information"""

    page: str = "1"

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "RootSheetInstance":
        # Find the path token in sheet_instances
        path_token = SExprParser.find_token(sexpr, "path")
        page = "1"

        if path_token:
            # Look for page token within the path token
            page_token = SExprParser.find_token(path_token, "page")
            if page_token:
                page = str(SExprParser.get_value(page_token, 1, "1"))

        return cls(page=page)

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("sheet_instances")]
        result.append([Symbol("path"), "/", [Symbol("page"), self.page]])
        return result


# Main Schematic Class
@dataclass
class KiCadSchematic(KiCadObject):
    """Complete KiCad schematic file"""

    version: int = 20230121
    generator: str = "kicad-parser"
    uuid: UUID = field(default_factory=lambda: UUID(""))
    page_settings: PageSettings = field(default_factory=PageSettings)
    title_block: TitleBlock = field(default_factory=TitleBlock)
    lib_symbols: List[KiCadSymbol] = field(default_factory=list)
    junctions: List[Junction] = field(default_factory=list)
    no_connects: List[NoConnect] = field(default_factory=list)
    bus_entries: List[BusEntry] = field(default_factory=list)
    wires: List[Wire] = field(default_factory=list)
    buses: List[Bus] = field(default_factory=list)
    images: List[Image] = field(default_factory=list)
    polylines: List[Polyline] = field(default_factory=list)
    texts: List[SchematicText] = field(default_factory=list)
    local_labels: List[LocalLabel] = field(default_factory=list)
    global_labels: List[GlobalLabel] = field(default_factory=list)
    hierarchical_labels: List[HierarchicalLabel] = field(default_factory=list)
    symbols: List[SchematicSymbol] = field(default_factory=list)
    sheets: List[HierarchicalSheet] = field(default_factory=list)
    sheet_instances: Optional[RootSheetInstance] = None

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "KiCadSchematic":
        version_token = SExprParser.find_token(sexpr, "version")
        generator_token = SExprParser.find_token(sexpr, "generator")
        uuid_token = SExprParser.find_token(sexpr, "uuid")
        paper_token = SExprParser.find_token(sexpr, "paper")
        title_block_token = SExprParser.find_token(sexpr, "title_block")
        lib_symbols_token = SExprParser.find_token(sexpr, "lib_symbols")
        sheet_instances_token = SExprParser.find_token(sexpr, "sheet_instances")

        # Parse lib_symbols
        lib_symbols = []
        if lib_symbols_token:
            symbol_tokens = SExprParser.find_all_tokens(lib_symbols_token, "symbol")
            for symbol_token in symbol_tokens:
                lib_symbols.append(KiCadSymbol.from_sexpr(symbol_token))

        # Parse all schematic elements
        junctions = [
            Junction.from_sexpr(token)
            for token in SExprParser.find_all_tokens(sexpr, "junction")
        ]
        no_connects = [
            NoConnect.from_sexpr(token)
            for token in SExprParser.find_all_tokens(sexpr, "no_connect")
        ]
        bus_entries = [
            BusEntry.from_sexpr(token)
            for token in SExprParser.find_all_tokens(sexpr, "bus_entry")
        ]
        wires = [
            Wire.from_sexpr(token)
            for token in SExprParser.find_all_tokens(sexpr, "wire")
        ]
        buses = [
            Bus.from_sexpr(token) for token in SExprParser.find_all_tokens(sexpr, "bus")
        ]
        images = [
            Image.from_sexpr(token)
            for token in SExprParser.find_all_tokens(sexpr, "image")
        ]
        polylines = [
            Polyline.from_sexpr(token)
            for token in SExprParser.find_all_tokens(sexpr, "polyline")
        ]
        texts = [
            SchematicText.from_sexpr(token)
            for token in SExprParser.find_all_tokens(sexpr, "text")
        ]
        local_labels = [
            LocalLabel.from_sexpr(token)
            for token in SExprParser.find_all_tokens(sexpr, "label")
        ]
        global_labels = [
            GlobalLabel.from_sexpr(token)
            for token in SExprParser.find_all_tokens(sexpr, "global_label")
        ]
        hierarchical_labels = [
            HierarchicalLabel.from_sexpr(token)
            for token in SExprParser.find_all_tokens(sexpr, "hierarchical_label")
        ]
        symbols = [
            SchematicSymbol.from_sexpr(token)
            for token in SExprParser.find_all_tokens(sexpr, "symbol")
        ]
        sheets = [
            HierarchicalSheet.from_sexpr(token)
            for token in SExprParser.find_all_tokens(sexpr, "sheet")
        ]

        return cls(
            version=(
                SExprParser.safe_get_int(version_token, 1, 20230121)
                if version_token
                else 20230121
            ),
            generator=(
                str(SExprParser.get_value(generator_token, 1, "kicad-parser"))
                if generator_token
                else "kicad-parser"
            ),
            uuid=UUID.from_sexpr(uuid_token) if uuid_token else UUID(""),
            page_settings=(
                PageSettings.from_sexpr(paper_token) if paper_token else PageSettings()
            ),
            title_block=(
                TitleBlock.from_sexpr(title_block_token)
                if title_block_token
                else TitleBlock()
            ),
            lib_symbols=lib_symbols,
            junctions=junctions,
            no_connects=no_connects,
            bus_entries=bus_entries,
            wires=wires,
            buses=buses,
            images=images,
            polylines=polylines,
            texts=texts,
            local_labels=local_labels,
            global_labels=global_labels,
            hierarchical_labels=hierarchical_labels,
            symbols=symbols,
            sheets=sheets,
            sheet_instances=(
                RootSheetInstance.from_sexpr(sheet_instances_token)
                if sheet_instances_token
                else None
            ),
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("kicad_sch")]
        result.append([Symbol("version"), self.version])
        result.append([Symbol("generator"), self.generator])
        result.append(self.uuid.to_sexpr())
        result.append(self.page_settings.to_sexpr())

        if any(
            [
                self.title_block.title,
                self.title_block.date,
                self.title_block.revision,
                self.title_block.company,
                self.title_block.comments,
            ]
        ):
            result.append(self.title_block.to_sexpr())

        # Add lib_symbols section
        if self.lib_symbols:
            lib_symbols: SExpr = [Symbol("lib_symbols")]
            for lib_symbol in self.lib_symbols:
                lib_symbols.append(lib_symbol.to_sexpr())
            result.append(lib_symbols)

        # Add all schematic elements in order
        for junction in self.junctions:
            result.append(junction.to_sexpr())
        for no_connect in self.no_connects:
            result.append(no_connect.to_sexpr())
        for bus_entry in self.bus_entries:
            result.append(bus_entry.to_sexpr())
        for wire in self.wires:
            result.append(wire.to_sexpr())
        for bus in self.buses:
            result.append(bus.to_sexpr())
        for image in self.images:
            result.append(image.to_sexpr())
        for polyline in self.polylines:
            result.append(polyline.to_sexpr())
        for text in self.texts:
            result.append(text.to_sexpr())
        for label in self.local_labels:
            result.append(label.to_sexpr())
        for global_label in self.global_labels:
            result.append(global_label.to_sexpr())
        for hierarchical_label in self.hierarchical_labels:
            result.append(hierarchical_label.to_sexpr())
        for symbol in self.symbols:
            result.append(symbol.to_sexpr())
        for sheet in self.sheets:
            result.append(sheet.to_sexpr())

        # Add sheet instances
        if self.sheet_instances:
            result.append(self.sheet_instances.to_sexpr())

        return result


# Helper functions for API
def load_schematic(filepath: str) -> KiCadSchematic:
    """Load KiCad schematic from file"""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    return cast(KiCadSchematic, parse_kicad_file(content, KiCadSchematic))


def save_schematic(schematic: KiCadSchematic, filepath: str) -> None:
    """Save KiCad schematic to file"""
    content = write_kicad_file(schematic)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


def create_basic_schematic(
    title: str = "Schematic", company: str = ""
) -> KiCadSchematic:
    """Create a basic schematic with minimal setup"""

    schematic = KiCadSchematic(
        title_block=TitleBlock(title=title, company=company),
        sheet_instances=RootSheetInstance(page="1"),
    )
    return schematic
