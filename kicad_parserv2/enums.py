"""Common enumeration types for KiCad S-expressions."""

from enum import Enum


class PinElectricalType(Enum):
    """Pin electrical types for symbols."""

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
    """Pin graphical styles for symbols."""

    LINE = "line"
    INVERTED = "inverted"
    CLOCK = "clock"
    INVERTED_CLOCK = "inverted_clock"
    INPUT_LOW = "input_low"
    CLOCK_LOW = "clock_low"
    OUTPUT_LOW = "output_low"
    EDGE_CLOCK_HIGH = "edge_clock_high"
    NON_LOGIC = "non_logic"


class PadType(Enum):
    """Pad types for footprints."""

    THRU_HOLE = "thru_hole"
    SMD = "smd"
    CONNECT = "connect"
    NP_THRU_HOLE = "np_thru_hole"


class PadShape(Enum):
    """Pad shapes for footprints."""

    CIRCLE = "circle"
    RECT = "rect"
    OVAL = "oval"
    TRAPEZOID = "trapezoid"
    ROUNDRECT = "roundrect"
    CUSTOM = "custom"


class StrokeType(Enum):
    """Valid stroke line styles for graphics."""

    DASH = "dash"
    DASH_DOT = "dash_dot"
    DASH_DOT_DOT = "dash_dot_dot"
    DOT = "dot"
    DEFAULT = "default"
    SOLID = "solid"


class JustifyHorizontal(Enum):
    """Horizontal text justification."""

    LEFT = "left"
    RIGHT = "right"
    CENTER = "center"


class JustifyVertical(Enum):
    """Vertical text justification."""

    TOP = "top"
    BOTTOM = "bottom"
    CENTER = "center"


class FillType(Enum):
    """Fill types for graphical objects."""

    NONE = "none"
    OUTLINE = "outline"
    BACKGROUND = "background"
    COLOR = "color"


class LabelShape(Enum):
    """Label and pin shapes for global labels, hierarchical labels, and sheet pins."""

    INPUT = "input"
    OUTPUT = "output"
    BIDIRECTIONAL = "bidirectional"
    TRI_STATE = "tri_state"
    PASSIVE = "passive"


class FootprintTextType(Enum):
    """Footprint text types."""

    REFERENCE = "reference"
    VALUE = "value"
    USER = "user"


class LayerType(Enum):
    """PCB layer types."""

    SIGNAL = "signal"
    POWER = "power"
    MIXED = "mixed"
    JUMPER = "jumper"


class ViaType(Enum):
    """Via types for PCB."""

    THROUGH = "through"
    BLIND_BURIED = "blind_buried"
    MICRO = "micro"


class ZoneConnection(Enum):
    """Zone connection types for pads."""

    INHERITED = 0
    SOLID = 1
    THERMAL_RELIEF = 2
    NONE = 3


class ZoneFillMode(Enum):
    """Zone fill modes."""

    SOLID = "solid"
    HATCHED = "hatched"


class ZoneKeepoutSetting(Enum):
    """Zone keepout settings."""

    ALLOWED = "allowed"
    NOT_ALLOWED = "not_allowed"


class HatchStyle(Enum):
    """Zone hatch display styles."""

    NONE = "none"
    EDGE = "edge"
    FULL = "full"


class SmoothingStyle(Enum):
    """Zone corner smoothing styles."""

    NONE = "none"
    CHAMFER = "chamfer"
    FILLET = "fillet"


class ClearanceType(Enum):
    """Custom pad clearance types."""

    OUTLINE = "outline"
    CONVEXHULL = "convexhull"
