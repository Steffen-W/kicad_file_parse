"""
KiCad PCB S-Expression Classes

This module contains classes for PCB/Board file format (.kicad_pcb),
including all PCB-specific elements like layers, tracks, vias, zones,
and board setup information.

Based on: doc/file-formats/sexpr-pcb/_index.en.adoc
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple, Union, cast

from .kicad_board import KiCadFootprint
from .kicad_board_elements import PadConnection, Zone, ZoneConnect
from .kicad_common import (
    UUID,
    Image,
    KiCadObject,
    PageSettings,
    Property,
    SExpr,
    SExprParser,
    Symbol,
    TitleBlock,
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


# PCB-specific enums
class LayerType(Enum):
    """PCB layer types"""

    SIGNAL = "signal"
    POWER = "power"
    MIXED = "mixed"
    JUMPER = "jumper"
    USER = "user"


class ViaType(Enum):
    """Via types"""

    THROUGH = "through"
    BLIND = "blind"
    MICRO = "micro"


# General Section
@dataclass
class GeneralSettings(KiCadObject):
    """General board settings"""

    thickness: float = 1.6  # mm

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "GeneralSettings":
        return cls(
            thickness=SExprParser.get_required_float(sexpr, "thickness", default=1.6)
        )

    def to_sexpr(self) -> SExpr:
        return [Symbol("general"), [Symbol("thickness"), self.thickness]]


# Layers Section
@dataclass
class BoardLayer(KiCadObject):
    """PCB layer definition"""

    ordinal: int
    canonical_name: str
    layer_type: LayerType
    user_name: Optional[str] = None

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "BoardLayer":
        if not isinstance(sexpr, list) or len(sexpr) < 3:
            raise ValueError("Invalid layer definition")

        ordinal = SExprParser.safe_int(sexpr[0], 0)
        canonical_name = str(sexpr[1])
        layer_type = SExprParser.parse_enum(sexpr[2], LayerType, LayerType.SIGNAL)
        user_name = str(sexpr[3]) if len(sexpr) > 3 else None

        return cls(
            ordinal=ordinal,
            canonical_name=canonical_name,
            layer_type=layer_type,
            user_name=user_name,
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [
            self.ordinal,
            self.canonical_name,
            Symbol(self.layer_type.value),
        ]
        if self.user_name:
            result.append(self.user_name)
        return result


# Setup Section
@dataclass
class BoardSetup(KiCadObject):
    """Board setup and design rules"""

    pad_to_mask_clearance: float = 0.0
    solder_mask_min_width: Optional[float] = None
    pad_to_paste_clearance: Optional[float] = None
    pad_to_paste_clearance_ratio: Optional[float] = None
    aux_axis_origin: Optional[Tuple[float, float]] = None
    grid_origin: Optional[Tuple[float, float]] = None

    # Zone connection defaults
    zone_connect_defaults: Optional[ZoneConnect] = None
    default_zone_connection: PadConnection = PadConnection.THERMAL

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "BoardSetup":
        aux_origin_token = SExprParser.find_token(sexpr, "aux_axis_origin")
        grid_origin_token = SExprParser.find_token(sexpr, "grid_origin")
        zone_connect_token = SExprParser.find_token(sexpr, "zone_connect")

        aux_origin = None
        if aux_origin_token and len(aux_origin_token) >= 3:
            aux_origin = (
                SExprParser.safe_float(aux_origin_token[1], 0.0),
                SExprParser.safe_float(aux_origin_token[2], 0.0),
            )

        grid_origin = None
        if grid_origin_token and len(grid_origin_token) >= 3:
            grid_origin = (
                SExprParser.safe_float(grid_origin_token[1], 0.0),
                SExprParser.safe_float(grid_origin_token[2], 0.0),
            )

        # Parse zone connection defaults
        zone_connect_defaults = None
        if zone_connect_token:
            zone_connect_defaults = ZoneConnect.from_sexpr(zone_connect_token)

        # Parse default zone connection type
        default_zone_connection = PadConnection.THERMAL
        zone_connection_token = SExprParser.find_token(sexpr, "default_zone_connection")
        if zone_connection_token and len(zone_connection_token) > 1:
            try:
                default_zone_connection = PadConnection(str(zone_connection_token[1]))
            except ValueError:
                default_zone_connection = PadConnection.THERMAL

        return cls(
            pad_to_mask_clearance=SExprParser.get_required_float(
                sexpr, "pad_to_mask_clearance", default=0.0
            ),
            solder_mask_min_width=SExprParser.get_optional_float(
                sexpr, "solder_mask_min_width"
            ),
            pad_to_paste_clearance=SExprParser.get_optional_float(
                sexpr, "pad_to_paste_clearance"
            ),
            pad_to_paste_clearance_ratio=SExprParser.get_optional_float(
                sexpr, "pad_to_paste_clearance_ratio"
            ),
            aux_axis_origin=aux_origin,
            grid_origin=grid_origin,
            zone_connect_defaults=zone_connect_defaults,
            default_zone_connection=default_zone_connection,
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("setup")]
        result.append([Symbol("pad_to_mask_clearance"), self.pad_to_mask_clearance])

        if self.solder_mask_min_width is not None:
            result.append([Symbol("solder_mask_min_width"), self.solder_mask_min_width])
        if self.pad_to_paste_clearance is not None:
            result.append(
                [Symbol("pad_to_paste_clearance"), self.pad_to_paste_clearance]
            )
        if self.pad_to_paste_clearance_ratio is not None:
            result.append(
                [
                    Symbol("pad_to_paste_clearance_ratio"),
                    self.pad_to_paste_clearance_ratio,
                ]
            )
        if self.aux_axis_origin:
            result.append(
                [
                    Symbol("aux_axis_origin"),
                    self.aux_axis_origin[0],
                    self.aux_axis_origin[1],
                ]
            )
        if self.grid_origin:
            result.append(
                [Symbol("grid_origin"), self.grid_origin[0], self.grid_origin[1]]
            )

        # Add zone connection settings
        if self.zone_connect_defaults:
            result.append(self.zone_connect_defaults.to_sexpr())
        if self.default_zone_connection != PadConnection.THERMAL:
            result.append(
                [
                    Symbol("default_zone_connection"),
                    Symbol(self.default_zone_connection.value),
                ]
            )

        return result


# Net Section
@dataclass
class BoardNet(KiCadObject):
    """PCB net definition"""

    ordinal: int
    name: str

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "BoardNet":
        ordinal = SExprParser.safe_get_int(sexpr, 1, 0)
        name = str(SExprParser.get_value(sexpr, 2, ""))

        return cls(ordinal=ordinal, name=name)

    def to_sexpr(self) -> SExpr:
        return [Symbol("net"), self.ordinal, self.name]


# Track Section Classes
@dataclass
class TrackSegment(KiCadObject):
    """PCB track segment"""

    start: Tuple[float, float]
    end: Tuple[float, float]
    width: float
    layer: str
    net: int
    uuid: UUID = field(default_factory=lambda: UUID(""))
    locked: Optional[bool] = None

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "TrackSegment":
        start_token = SExprParser.find_token(sexpr, "start")
        end_token = SExprParser.find_token(sexpr, "end")
        tstamp_token = SExprParser.find_token(sexpr, "tstamp")

        start = (0.0, 0.0)
        if start_token and len(start_token) >= 3:
            start = (
                SExprParser.safe_float(start_token[1], 0.0),
                SExprParser.safe_float(start_token[2], 0.0),
            )

        end = (0.0, 0.0)
        if end_token and len(end_token) >= 3:
            end = (
                SExprParser.safe_float(end_token[1], 0.0),
                SExprParser.safe_float(end_token[2], 0.0),
            )

        return cls(
            start=start,
            end=end,
            width=SExprParser.get_required_float(sexpr, "width", default=0.0),
            layer=SExprParser.get_required_str(sexpr, "layer", default=""),
            net=SExprParser.get_required_int(sexpr, "net", default=0),
            uuid=UUID.from_sexpr(tstamp_token),
            locked=SExprParser.get_optional_bool_flag(sexpr, "locked"),
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("segment")]
        result.append([Symbol("start"), self.start[0], self.start[1]])
        result.append([Symbol("end"), self.end[0], self.end[1]])
        result.append([Symbol("width"), self.width])
        result.append([Symbol("layer"), self.layer])
        if self.locked is not None and self.locked:
            result.append(Symbol("locked"))
        result.append([Symbol("net"), self.net])
        result.append([Symbol("tstamp"), self.uuid.uuid])
        return result


@dataclass
class TrackVia(KiCadObject):
    """PCB via"""

    position: Tuple[float, float]
    size: float
    drill: float
    layers: Tuple[str, str]  # Start and end layer
    net: int
    uuid: UUID = field(default_factory=lambda: UUID(""))
    via_type: Optional[ViaType] = None
    locked: Optional[bool] = None
    remove_unused_layers: Optional[bool] = None
    keep_end_layers: Optional[bool] = None
    free: Optional[bool] = None

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "TrackVia":
        at_token = SExprParser.find_token(sexpr, "at")
        layers_token = SExprParser.find_token(sexpr, "layers")
        tstamp_token = SExprParser.find_token(sexpr, "tstamp")

        position = (0.0, 0.0)
        if at_token and len(at_token) >= 3:
            position = (
                SExprParser.safe_float(at_token[1], 0.0),
                SExprParser.safe_float(at_token[2], 0.0),
            )

        layers = ("F.Cu", "B.Cu")
        if layers_token and len(layers_token) >= 3:
            layers = (str(layers_token[1]), str(layers_token[2]))

        # Check for via type in first position
        via_type = None
        if len(sexpr) > 1 and isinstance(sexpr[1], Symbol):
            via_type = ViaType(str(sexpr[1]))

        return cls(
            position=position,
            size=SExprParser.get_required_float(sexpr, "size", default=0.0),
            drill=SExprParser.get_required_float(sexpr, "drill", default=0.0),
            layers=layers,
            net=SExprParser.get_required_int(sexpr, "net", default=0),
            uuid=UUID.from_sexpr(tstamp_token),
            via_type=via_type,
            locked=SExprParser.get_optional_bool_flag(sexpr, "locked"),
            remove_unused_layers=(
                SExprParser.get_optional_bool_flag(sexpr, "remove_unused_layers")
            ),
            keep_end_layers=(
                SExprParser.get_optional_bool_flag(sexpr, "keep_end_layers")
            ),
            free=SExprParser.get_optional_bool_flag(sexpr, "free"),
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("via")]

        if self.via_type:
            result.append(Symbol(self.via_type.value))
        if self.locked is not None and self.locked:
            result.append(Symbol("locked"))

        result.append([Symbol("at"), self.position[0], self.position[1]])
        result.append([Symbol("size"), self.size])
        result.append([Symbol("drill"), self.drill])
        result.append([Symbol("layers"), self.layers[0], self.layers[1]])

        if self.remove_unused_layers is not None and self.remove_unused_layers:
            result.append(Symbol("remove_unused_layers"))
        if self.keep_end_layers is not None and self.keep_end_layers:
            result.append(Symbol("keep_end_layers"))
        if self.free is not None and self.free:
            result.append(Symbol("free"))

        result.append([Symbol("net"), self.net])
        result.append([Symbol("tstamp"), self.uuid.uuid])
        return result


@dataclass
class TrackArc(KiCadObject):
    """PCB track arc"""

    start: Tuple[float, float]
    mid: Tuple[float, float]
    end: Tuple[float, float]
    width: float
    layer: str
    net: int
    uuid: UUID = field(default_factory=lambda: UUID(""))
    locked: Optional[bool] = None
    tstamp: Optional[str] = None

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "TrackArc":
        start_token = SExprParser.find_token(sexpr, "start")
        mid_token = SExprParser.find_token(sexpr, "mid")
        end_token = SExprParser.find_token(sexpr, "end")
        tstamp_token = SExprParser.find_token(sexpr, "tstamp")

        start = (0.0, 0.0)
        if start_token and len(start_token) >= 3:
            start = (
                SExprParser.safe_float(start_token[1], 0.0),
                SExprParser.safe_float(start_token[2], 0.0),
            )

        mid = (0.0, 0.0)
        if mid_token and len(mid_token) >= 3:
            mid = (
                SExprParser.safe_float(mid_token[1], 0.0),
                SExprParser.safe_float(mid_token[2], 0.0),
            )

        end = (0.0, 0.0)
        if end_token and len(end_token) >= 3:
            end = (
                SExprParser.safe_float(end_token[1], 0.0),
                SExprParser.safe_float(end_token[2], 0.0),
            )

        return cls(
            start=start,
            mid=mid,
            end=end,
            width=SExprParser.get_required_float(sexpr, "width", default=0.0),
            layer=SExprParser.get_required_str(sexpr, "layer", default=""),
            net=SExprParser.get_required_int(sexpr, "net", default=0),
            uuid=UUID.from_sexpr(tstamp_token),
            locked=SExprParser.get_optional_bool_flag(sexpr, "locked"),
            tstamp=(
                str(tstamp_token[1]) if tstamp_token and len(tstamp_token) > 1 else None
            ),
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("arc")]
        result.append([Symbol("start"), self.start[0], self.start[1]])
        result.append([Symbol("mid"), self.mid[0], self.mid[1]])
        result.append([Symbol("end"), self.end[0], self.end[1]])
        result.append([Symbol("width"), self.width])
        result.append([Symbol("layer"), self.layer])
        if self.locked is not None and self.locked:
            result.append(Symbol("locked"))
        result.append([Symbol("net"), self.net])
        result.append([Symbol("tstamp"), self.uuid.uuid])
        return result


# Group Section
@dataclass
class Group(KiCadObject):
    """PCB group"""

    name: str
    uuid: UUID = field(default_factory=lambda: UUID(""))
    members: List[UUID] = field(default_factory=list)
    locked: Optional[bool] = None

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "Group":
        name = str(SExprParser.get_value(sexpr, 1, ""))
        uuid_token = SExprParser.find_token(sexpr, "uuid")
        members_token = SExprParser.find_token(sexpr, "members")

        members = []
        if members_token:
            for item in members_token[1:]:
                if isinstance(item, str):
                    members.append(UUID(item))

        return cls(
            name=name,
            uuid=UUID.from_sexpr(uuid_token),
            members=members,
            locked=SExprParser.get_optional_bool_flag(sexpr, "locked"),
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("group"), self.name]
        result.append(self.uuid.to_sexpr())

        if self.locked is not None and self.locked:
            result.append(Symbol("locked"))

        if self.members:
            members_expr: SExpr = [Symbol("members")]
            members_expr.extend([member.uuid for member in self.members])
            result.append(members_expr)

        return result


# Main PCB Class
@dataclass
class KiCadPCB(KiCadObject):
    """Complete KiCad PCB/Board file"""

    version: int = 20230121
    generator: str = "kicad-parser"
    general: GeneralSettings = field(default_factory=GeneralSettings)
    page_settings: PageSettings = field(default_factory=PageSettings)
    title_block: TitleBlock = field(default_factory=TitleBlock)
    layers: List[BoardLayer] = field(default_factory=list)
    setup: BoardSetup = field(default_factory=BoardSetup)
    properties: List[Property] = field(default_factory=list)
    nets: List[BoardNet] = field(default_factory=list)
    footprints: List["KiCadFootprint"] = field(default_factory=list)
    graphics: List[
        Union[
            GraphicalLine,
            GraphicalRectangle,
            GraphicalCircle,
            GraphicalArc,
            GraphicalPolygon,
            GraphicalText,
        ]
    ] = field(default_factory=list)
    images: List[Image] = field(default_factory=list)
    track_segments: List[TrackSegment] = field(default_factory=list)
    track_vias: List[TrackVia] = field(default_factory=list)
    track_arcs: List[TrackArc] = field(default_factory=list)
    zones: List[Zone] = field(default_factory=list)
    groups: List[Group] = field(default_factory=list)

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "KiCadPCB":
        version_token = SExprParser.find_token(sexpr, "version")
        generator_token = SExprParser.find_token(sexpr, "generator")
        general_token = SExprParser.find_token(sexpr, "general")
        paper_token = SExprParser.find_token(sexpr, "paper")
        title_block_token = SExprParser.find_token(sexpr, "title_block")
        layers_token = SExprParser.find_token(sexpr, "layers")
        setup_token = SExprParser.find_token(sexpr, "setup")

        # Parse layers
        layers = []
        if layers_token:
            for item in layers_token[1:]:
                if isinstance(item, list) and len(item) >= 3:
                    layers.append(BoardLayer.from_sexpr(item))

        # Parse properties
        properties = []
        property_tokens = SExprParser.find_all_tokens(sexpr, "property")
        for prop_token in property_tokens:
            properties.append(Property.from_sexpr(prop_token))

        # Parse nets
        nets = []
        net_tokens = SExprParser.find_all_tokens(sexpr, "net")
        for net_token in net_tokens:
            nets.append(BoardNet.from_sexpr(net_token))

        # Parse footprints
        footprints = []
        footprint_tokens = SExprParser.find_all_tokens(sexpr, "footprint")

        for footprint_token in footprint_tokens:
            footprints.append(KiCadFootprint.from_sexpr(footprint_token))

        # Parse graphics
        graphics: List[
            Union[
                GraphicalLine,
                GraphicalRectangle,
                GraphicalCircle,
                GraphicalArc,
                GraphicalPolygon,
                GraphicalText,
            ]
        ] = []
        for graphic_type in [
            "gr_line",
            "gr_rect",
            "gr_circle",
            "gr_arc",
            "gr_poly",
            "gr_text",
        ]:
            graphic_tokens = SExprParser.find_all_tokens(sexpr, graphic_type)
            for graphic_token in graphic_tokens:
                if graphic_type == "gr_line":
                    graphics.append(GraphicalLine.from_sexpr(graphic_token))
                elif graphic_type == "gr_rect":
                    graphics.append(GraphicalRectangle.from_sexpr(graphic_token))
                elif graphic_type == "gr_circle":
                    graphics.append(GraphicalCircle.from_sexpr(graphic_token))
                elif graphic_type == "gr_arc":
                    graphics.append(GraphicalArc.from_sexpr(graphic_token))
                elif graphic_type == "gr_poly":
                    graphics.append(GraphicalPolygon.from_sexpr(graphic_token))
                elif graphic_type == "gr_text":
                    graphics.append(GraphicalText.from_sexpr(graphic_token))

        # Parse images
        images = []
        image_tokens = SExprParser.find_all_tokens(sexpr, "image")
        for image_token in image_tokens:
            images.append(Image.from_sexpr(image_token))

        # Parse tracks
        track_segments = []
        segment_tokens = SExprParser.find_all_tokens(sexpr, "segment")
        for segment_token in segment_tokens:
            track_segments.append(TrackSegment.from_sexpr(segment_token))

        track_vias = []
        via_tokens = SExprParser.find_all_tokens(sexpr, "via")
        for via_token in via_tokens:
            track_vias.append(TrackVia.from_sexpr(via_token))

        track_arcs = []
        arc_tokens = SExprParser.find_all_tokens(sexpr, "arc")
        for arc_token in arc_tokens:
            track_arcs.append(TrackArc.from_sexpr(arc_token))

        # Parse zones
        zones = []
        zone_tokens = SExprParser.find_all_tokens(sexpr, "zone")
        for zone_token in zone_tokens:
            zones.append(Zone.from_sexpr(zone_token))

        # Parse groups
        groups = []
        group_tokens = SExprParser.find_all_tokens(sexpr, "group")
        for group_token in group_tokens:
            groups.append(Group.from_sexpr(group_token))

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
            general=(
                GeneralSettings.from_sexpr(general_token)
                if general_token
                else GeneralSettings()
            ),
            page_settings=(
                PageSettings.from_sexpr(paper_token) if paper_token else PageSettings()
            ),
            title_block=(
                TitleBlock.from_sexpr(title_block_token)
                if title_block_token
                else TitleBlock()
            ),
            layers=layers,
            setup=BoardSetup.from_sexpr(setup_token) if setup_token else BoardSetup(),
            properties=properties,
            nets=nets,
            footprints=footprints,
            graphics=graphics,
            images=images,
            track_segments=track_segments,
            track_vias=track_vias,
            track_arcs=track_arcs,
            zones=zones,
            groups=groups,
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("kicad_pcb")]
        result.append([Symbol("version"), self.version])
        result.append([Symbol("generator"), self.generator])
        result.append(self.general.to_sexpr())
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

        # Add layers
        if self.layers:
            layers_expr: SExpr = [Symbol("layers")]
            for layer in self.layers:
                layers_expr.append(layer.to_sexpr())
            result.append(layers_expr)

        # Add setup
        result.append(self.setup.to_sexpr())

        # Add properties
        for prop in self.properties:
            result.append(prop.to_sexpr())

        # Add nets
        for net in self.nets:
            result.append(net.to_sexpr())

        # Add footprints
        for footprint in self.footprints:
            result.append(footprint.to_sexpr())

        # Add graphics
        for graphic in self.graphics:
            result.append(graphic.to_sexpr())

        # Add images
        for image in self.images:
            result.append(image.to_sexpr())

        # Add tracks
        for segment in self.track_segments:
            result.append(segment.to_sexpr())
        for via in self.track_vias:
            result.append(via.to_sexpr())
        for arc in self.track_arcs:
            result.append(arc.to_sexpr())

        # Add zones
        for zone in self.zones:
            result.append(zone.to_sexpr())

        # Add groups
        for group in self.groups:
            result.append(group.to_sexpr())

        return result


# Helper functions for API
def load_pcb(filepath: Union[str, Path]) -> KiCadPCB:
    """Load KiCad PCB from file"""
    path = Path(filepath) if isinstance(filepath, str) else filepath
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return cast(KiCadPCB, parse_kicad_file(content, KiCadPCB))


def save_pcb(pcb: KiCadPCB, filepath: Union[str, Path]) -> None:
    """Save KiCad PCB to file"""
    path = Path(filepath) if isinstance(filepath, str) else filepath
    content = write_kicad_file(pcb)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def create_basic_pcb(title: str = "PCB", company: str = "") -> KiCadPCB:
    """Create a basic PCB with minimal setup"""

    # Create default layers (standard 2-layer board)
    layers = [
        BoardLayer(0, "F.Cu", LayerType.SIGNAL, "F.Cu"),
        BoardLayer(31, "B.Cu", LayerType.SIGNAL, "B.Cu"),
        BoardLayer(32, "B.Adhes", LayerType.USER, "B.Adhesive"),
        BoardLayer(33, "F.Adhes", LayerType.USER, "F.Adhesive"),
        BoardLayer(34, "B.Paste", LayerType.USER, "B.Paste"),
        BoardLayer(35, "F.Paste", LayerType.USER, "F.Paste"),
        BoardLayer(36, "B.SilkS", LayerType.USER, "B.Silkscreen"),
        BoardLayer(37, "F.SilkS", LayerType.USER, "F.Silkscreen"),
        BoardLayer(38, "B.Mask", LayerType.USER, "B.Mask"),
        BoardLayer(39, "F.Mask", LayerType.USER, "F.Mask"),
        BoardLayer(40, "Dwgs.User", LayerType.USER, "User.Drawings"),
        BoardLayer(41, "Cmts.User", LayerType.USER, "User.Comments"),
        BoardLayer(42, "Eco1.User", LayerType.USER, "User.Eco1"),
        BoardLayer(43, "Eco2.User", LayerType.USER, "User.Eco2"),
        BoardLayer(44, "Edge.Cuts", LayerType.USER, "Edge.Cuts"),
        BoardLayer(45, "Margin", LayerType.USER, "Margin"),
        BoardLayer(46, "B.CrtYd", LayerType.USER, "B.Courtyard"),
        BoardLayer(47, "F.CrtYd", LayerType.USER, "F.Courtyard"),
        BoardLayer(48, "B.Fab", LayerType.USER, "B.Fab"),
        BoardLayer(49, "F.Fab", LayerType.USER, "F.Fab"),
    ]

    # Add basic nets
    nets = [BoardNet(0, ""), BoardNet(1, "GND"), BoardNet(2, "VCC")]  # No net

    pcb = KiCadPCB(
        title_block=TitleBlock(title=title, company=company), layers=layers, nets=nets
    )
    return pcb
