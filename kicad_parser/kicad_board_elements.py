"""
KiCad Board Elements

This module contains shared board elements like zones, connections and related
classes that are used by both footprints and PCBs to avoid circular dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple

from .kicad_common import (
    UUID,
    CoordinatePointList,
    KiCadObject,
    SExpr,
    SExprParser,
    Symbol,
)


class PadConnection(Enum):
    """Pad connection types for zones"""

    SOLID = "solid"
    THERMAL = "thermal"
    NONE = "none"


def parse_zone_connect(sexpr: SExpr) -> Optional[PadConnection]:
    """Parse zone_connect value from S-expression

    Centralized function to parse PadConnection enum values with legacy support.
    Handles both integer (legacy) and string values.
    """
    zone_connect_token = SExprParser.find_token(sexpr, "zone_connect")
    if zone_connect_token and len(zone_connect_token) > 1:
        try:
            # Handle both int (legacy) and string values
            value = zone_connect_token[1]
            if isinstance(value, int):
                # Legacy mapping: 0=inherit, 1=solid, 2=thermal, 3=none
                if value == 1:
                    return PadConnection.SOLID
                elif value == 2:
                    return PadConnection.THERMAL
                elif value == 3:
                    return PadConnection.NONE
                else:
                    return None  # 0 or other values mean inherit/default
            else:
                # String value - direct mapping
                return PadConnection(str(value))
        except (ValueError, TypeError, IndexError):
            return None
    return None


# Zone Classes
@dataclass
class ZoneConnect(KiCadObject):
    """Zone connection settings"""

    clearance: float = 0.0
    min_thickness: float = 0.0

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "ZoneConnect":
        return cls(
            clearance=SExprParser.get_required_float(sexpr, "clearance", default=0.0),
            min_thickness=SExprParser.get_required_float(
                sexpr, "min_thickness", default=0.0
            ),
        )

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("connect")]
        if self.clearance != 0.0:
            result.append([Symbol("clearance"), self.clearance])
        if self.min_thickness != 0.0:
            result.append([Symbol("min_thickness"), self.min_thickness])
        return result


@dataclass
class ZoneFillSettings(KiCadObject):
    """Zone fill settings for advanced copper pour features"""

    filled: bool = True
    mode: Optional[str] = None  # "hatched" or None for solid
    thermal_gap: Optional[float] = None
    thermal_bridge_width: Optional[float] = None
    smoothing: Optional[str] = None  # "chamfer" or "fillet"
    radius: Optional[float] = None
    island_removal_mode: Optional[int] = None  # 0, 1, or 2
    island_area_min: Optional[float] = None
    hatch_thickness: Optional[float] = None
    hatch_gap: Optional[float] = None
    hatch_orientation: Optional[float] = None
    hatch_smoothing_level: Optional[int] = None  # 0-3
    hatch_smoothing_value: Optional[float] = None
    hatch_border_algorithm: Optional[int] = None  # 0 or 1
    hatch_min_hole_area: Optional[float] = None

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "ZoneFillSettings":
        """Parse zone fill settings from S-expression"""
        if not sexpr:
            return cls()

        return cls(
            filled=SExprParser.has_symbol(sexpr, "yes"),
            mode=SExprParser.get_optional_str(sexpr, "mode"),
            thermal_gap=SExprParser.get_optional_float(sexpr, "thermal_gap"),
            thermal_bridge_width=SExprParser.get_optional_float(
                sexpr, "thermal_bridge_width"
            ),
            smoothing=SExprParser.get_optional_str(sexpr, "smoothing"),
            radius=SExprParser.get_optional_float(sexpr, "radius"),
            island_removal_mode=SExprParser.get_optional_int(
                sexpr, "island_removal_mode"
            ),
            island_area_min=SExprParser.get_optional_float(sexpr, "island_area_min"),
            hatch_thickness=SExprParser.get_optional_float(sexpr, "hatch_thickness"),
            hatch_gap=SExprParser.get_optional_float(sexpr, "hatch_gap"),
            hatch_orientation=SExprParser.get_optional_float(
                sexpr, "hatch_orientation"
            ),
            hatch_smoothing_level=SExprParser.get_optional_int(
                sexpr, "hatch_smoothing_level"
            ),
            hatch_smoothing_value=SExprParser.get_optional_float(
                sexpr, "hatch_smoothing_value"
            ),
            hatch_border_algorithm=SExprParser.get_optional_int(
                sexpr, "hatch_border_algorithm"
            ),
            hatch_min_hole_area=SExprParser.get_optional_float(
                sexpr, "hatch_min_hole_area"
            ),
        )

    def to_sexpr(self) -> SExpr:
        """Export zone fill settings to S-expression"""
        result: SExpr = [Symbol("fill")]

        if self.filled:
            result.append(Symbol("yes"))
        if self.mode:
            result.append([Symbol("mode"), self.mode])
        if self.thermal_gap is not None:
            result.append([Symbol("thermal_gap"), self.thermal_gap])
        if self.thermal_bridge_width is not None:
            result.append([Symbol("thermal_bridge_width"), self.thermal_bridge_width])
        if self.smoothing:
            result.append([Symbol("smoothing"), self.smoothing])
        if self.radius is not None:
            result.append([Symbol("radius"), self.radius])
        if self.island_removal_mode is not None:
            result.append([Symbol("island_removal_mode"), self.island_removal_mode])
        if self.island_area_min is not None:
            result.append([Symbol("island_area_min"), self.island_area_min])
        if self.hatch_thickness is not None:
            result.append([Symbol("hatch_thickness"), self.hatch_thickness])
        if self.hatch_gap is not None:
            result.append([Symbol("hatch_gap"), self.hatch_gap])
        if self.hatch_orientation is not None:
            result.append([Symbol("hatch_orientation"), self.hatch_orientation])
        if self.hatch_smoothing_level is not None:
            result.append([Symbol("hatch_smoothing_level"), self.hatch_smoothing_level])
        if self.hatch_smoothing_value is not None:
            result.append([Symbol("hatch_smoothing_value"), self.hatch_smoothing_value])
        if self.hatch_border_algorithm is not None:
            result.append(
                [Symbol("hatch_border_algorithm"), self.hatch_border_algorithm]
            )
        if self.hatch_min_hole_area is not None:
            result.append([Symbol("hatch_min_hole_area"), self.hatch_min_hole_area])

        return result


@dataclass
class Zone(KiCadObject):
    """PCB zone/pour with advanced copper pour features"""

    net: int
    net_name: str
    layers: List[str] = field(default_factory=list)
    name: Optional[str] = None
    hatch_thickness: float = 0.508
    hatch_gap: float = 0.508
    connect_pads: PadConnection = PadConnection.THERMAL
    connect_pads_clearance: Optional[float] = None
    min_thickness: float = 0.254
    filled_areas_thickness: Optional[float] = None
    keepout: bool = False
    uuid: UUID = field(default_factory=lambda: UUID(""))

    # Advanced fill settings
    fill_settings: Optional[ZoneFillSettings] = field(
        default_factory=lambda: ZoneFillSettings()
    )
    filled_polygons: List[Tuple[str, List[Tuple[float, float]]]] = field(
        default_factory=list
    )
    filled_segments: List[Tuple[str, List[Tuple[float, float, float, float]]]] = field(
        default_factory=list
    )

    # Zone outline points (simplified - full implementation would include arcs)
    polygon_points: CoordinatePointList = field(default_factory=CoordinatePointList)

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "Zone":
        hatch_token = SExprParser.find_token(sexpr, "hatch")
        connect_pads_token = SExprParser.find_token(sexpr, "connect_pads")
        fill_token = SExprParser.find_token(sexpr, "fill")
        polygon_token = SExprParser.find_token(sexpr, "polygon")
        layers_token = SExprParser.find_token(sexpr, "layers")
        layers = []
        if layers_token and len(layers_token) > 1:
            layers = [
                str(item)
                for item in layers_token[1:]
                if isinstance(item, (str, Symbol))
            ]

        # Parse hatch settings - simplified with get_required_float defaults
        hatch_thickness = 0.508
        hatch_gap = 0.508
        hatch_orientation = None
        if hatch_token:
            # Check for new format: (hatch (thickness X) (gap Y) (orientation Z))
            hatch_thickness = SExprParser.get_required_float(
                hatch_token, "thickness", default=0.508
            )
            hatch_gap = SExprParser.get_required_float(
                hatch_token, "gap", default=0.508
            )
            hatch_orientation = SExprParser.get_optional_float(
                hatch_token, "orientation"
            )

            # Fallback to old format: (hatch edge THICKNESS GAP) if no nested tokens found
            if hatch_thickness == 0.508 and len(hatch_token) >= 3:
                hatch_thickness = SExprParser.safe_float(hatch_token[2], 0.508)
                if len(hatch_token) >= 4:
                    hatch_gap = SExprParser.safe_float(hatch_token[3], 0.508)

        # Parse connect pads - simplified parsing
        connect_pads = PadConnection.THERMAL  # Default
        connect_pads_clearance = None
        if connect_pads_token and len(connect_pads_token) > 1:
            # Try to parse connection type from token value
            try:
                if isinstance(connect_pads_token[1], list):
                    # Nested format like (connect_pads (clearance 0.5))
                    connect_pads_clearance = SExprParser.get_optional_float(
                        connect_pads_token, "clearance"
                    )
                else:
                    # Direct format like (connect_pads thermal)
                    connect_pads = PadConnection(str(connect_pads_token[1]))
            except (ValueError, TypeError):
                pass  # Keep default

        # Parse polygon points using existing CoordinatePointList parser
        polygon_points = CoordinatePointList()
        if polygon_token:
            pts_token = SExprParser.find_token(polygon_token, "pts")
            if pts_token:
                polygon_points = CoordinatePointList.from_sexpr(pts_token)

        return cls(
            net=SExprParser.get_required_int(sexpr, "net", default=0),
            net_name=SExprParser.get_required_str(sexpr, "net_name", default=""),
            layers=layers,
            name=SExprParser.get_optional_str(sexpr, "name"),
            hatch_thickness=hatch_thickness,
            hatch_gap=hatch_gap,
            connect_pads=connect_pads,
            connect_pads_clearance=connect_pads_clearance,
            min_thickness=SExprParser.get_required_float(
                sexpr, "min_thickness", default=0.254
            ),
            filled_areas_thickness=(
                cls._parse_filled_areas_thickness(
                    SExprParser.find_token(sexpr, "filled_areas_thickness")
                )
            ),
            keepout=SExprParser.has_symbol(sexpr, "keepout"),
            uuid=UUID.from_sexpr(SExprParser.find_token(sexpr, "tstamp")),
            fill_settings=cls._create_zone_fill_settings(fill_token, hatch_orientation),
            polygon_points=polygon_points,
        )

    @classmethod
    def _create_zone_fill_settings(
        cls, fill_token: Optional[SExpr], hatch_orientation: Optional[float]
    ) -> ZoneFillSettings:
        """Create ZoneFillSettings with merged hatch and fill data"""
        if fill_token:
            fill_settings = ZoneFillSettings.from_sexpr(fill_token)
        else:
            fill_settings = ZoneFillSettings()

        # Update hatch_orientation if we parsed it from hatch token
        if hatch_orientation is not None:
            fill_settings.hatch_orientation = hatch_orientation

        return fill_settings

    @classmethod
    def _parse_filled_areas_thickness(
        cls, filled_areas_token: Optional[SExpr]
    ) -> Optional[float]:
        """Parse filled_areas_thickness token which can be 'no', 'yes', or a float"""
        if not filled_areas_token:
            return None

        value = SExprParser.get_value(filled_areas_token, 1)
        if isinstance(value, Symbol) or isinstance(value, str):
            str_value = str(value)
            if str_value == "no":
                return False
            elif str_value == "yes":
                return True

        # Try to parse as float
        if value is None:
            return None
        return SExprParser.safe_float(value, 0.0)

    def to_sexpr(self) -> SExpr:
        result: SExpr = [Symbol("zone")]

        if self.keepout:
            result.append(Symbol("keepout"))

        result.append([Symbol("net"), self.net])
        result.append([Symbol("net_name"), self.net_name])

        if self.layers:
            layers_expr: SExpr = [Symbol("layers")]
            layers_expr.extend(self.layers)
            result.append(layers_expr)

        if self.name:
            result.append([Symbol("name"), self.name])

        result.append(
            [Symbol("hatch"), Symbol("edge"), self.hatch_thickness, self.hatch_gap]
        )
        result.append([Symbol("connect_pads"), Symbol(self.connect_pads.value)])
        result.append([Symbol("min_thickness"), self.min_thickness])

        if self.filled_areas_thickness:
            result.append(
                [Symbol("filled_areas_thickness"), self.filled_areas_thickness]
            )

        # Add advanced fill settings if present
        if self.fill_settings:
            result.append(self.fill_settings.to_sexpr())

        result.append([Symbol("tstamp"), self.uuid.uuid])

        # Add polygon if points exist
        if self.polygon_points.points:
            result.append([Symbol("polygon"), self.polygon_points.to_sexpr()])

        # Add filled polygons if present
        for layer, points in self.filled_polygons:
            filled_pts: SExpr = [Symbol("pts")]
            for point in points:
                filled_pts.append([Symbol("xy"), point[0], point[1]])
            result.append(
                [Symbol("filled_polygon"), [Symbol("layer"), layer], filled_pts]
            )

        # Add filled segments if present
        for layer, segments in self.filled_segments:
            segs: SExpr = [Symbol("pts")]
            for segment in segments:
                segs.append([Symbol("xy"), segment[0], segment[1]])
                segs.append([Symbol("xy"), segment[2], segment[3]])
            result.append([Symbol("filled_segments"), [Symbol("layer"), layer], segs])

        return result
