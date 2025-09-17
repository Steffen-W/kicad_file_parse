"""
KiCad Parser - Python Library for Parsing KiCad Files

A comprehensive Python library for parsing and manipulating KiCad S-Expression files,
including symbol libraries (.kicad_sym) and footprints (.kicad_mod).

Main Classes:
- KiCadSymbolLibrary: Symbol library container
- KiCadSymbol: Individual symbol definition
- KiCadFootprint: Footprint definition
- Position, Stroke, Fill, TextEffects: Common data structures

Main Functions:
- load_kicad_file: Load any KiCad file with auto-detection
- save_kicad_file: Save KiCad objects to files
- detect_file_type: Detect KiCad file type from content
"""

__version__ = "1.0.0"
__author__ = "Steffen-W"
__email__ = "your.email@example.com"

from .file_comparison_utils import (
    KiCadFileType,
    detect_kicad_file_type,
)
from .kicad_board import (
    DrillDefinition,
    Footprint3DModel,
    FootprintArc,
    FootprintAttributes,
    FootprintCircle,
    FootprintLine,
    FootprintPad,
    FootprintPolygon,
    FootprintRectangle,
    FootprintText,
    FootprintTextType,
    FootprintType,
    KiCadFootprint,
    Net,
    PadShape,
    PadType,
)
from .kicad_board_elements import (
    PadConnection,
    Zone,
    ZoneConnect,
    ZoneFillSettings,
    parse_zone_connect,
)
from .kicad_common import (
    UUID,
    CoordinatePoint,
    CoordinatePointList,
    Fill,
    FillType,
    Font,
    FontDefinition,
    FootprintLine,
    FootprintText,
    FootprintTextBox,
    FootprintTextType,
    Image,
    JustifyHorizontal,
    JustifyVertical,
    KiCadObject,
    Layer,
    PageSettings,
    Position,
    PositionIdentifier,
    Property,
    Stroke,
    StrokeDefinition,
    StrokeType,
    TextEffects,
    TextEffectsDefinition,
    TitleBlock,
    XYCoordinate,
    sexpr_to_str,
    str_to_sexpr,
)
from .kicad_design_rules import (
    ConstraintType,
    ConstraintValue,
    DesignRule,
    DesignRuleConstraint,
    DisallowType,
    DRCSeverity,
    KiCadDesignRules,
    create_basic_design_rules,
    load_design_rules,
    parse_kicad_design_rules_file,
    save_design_rules,
    write_kicad_design_rules_file,
)
from .kicad_file import (
    convert_file,
    detect_file_type,
    detect_file_type_from_path,
    load_footprint,
    load_kicad_file,
    load_symbol_library,
    load_worksheet,
    parse_kicad_file,
    save_footprint,
    save_kicad_file,
    save_symbol_library,
    save_worksheet,
    serialize_kicad_object,
    validate_kicad_file,
)
from .kicad_graphics import (
    Dimension,
    DimensionFormat,
    DimensionStyle,
    DimensionType,
    GraphicalArc,
    GraphicalBezier,
    GraphicalCircle,
    GraphicalLine,
    GraphicalPolygon,
    GraphicalRectangle,
    GraphicalText,
    GraphicalTextBox,
)
from .kicad_main import (
    create_basic_footprint,
    create_basic_symbol,
    create_basic_worksheet,
    example_footprint_creation,
    example_symbol_creation,
    load_any_kicad_file,
    parse_any_kicad_file,
    save_any_kicad_file,
)
from .kicad_pcb import (
    BoardLayer,
    BoardNet,
    BoardSetup,
    GeneralSettings,
    KiCadPCB,
    LayerType,
    TrackArc,
    TrackSegment,
    TrackVia,
    ViaType,
    create_basic_pcb,
    load_pcb,
    save_pcb,
)
from .kicad_schematic import (
    Bus,
    BusEntry,
    GlobalLabel,
    HierarchicalLabel,
    HierarchicalPin,
    HierarchicalSheet,
    Junction,
    KiCadSchematic,
    LabelShape,
    LocalLabel,
    NoConnect,
    Polyline,
    RootSheetInstance,
    SchematicSymbol,
    SchematicText,
    SheetInstance,
    SheetProject,
    SymbolInstance,
    SymbolProject,
    Wire,
    create_basic_schematic,
    load_schematic,
    save_schematic,
)
from .kicad_symbol import (
    KiCadSymbol,
    KiCadSymbolLibrary,
    PinElectricalType,
    PinGraphicStyle,
    SymbolArc,
    SymbolBezier,
    SymbolCircle,
    SymbolPin,
    SymbolPolyline,
    SymbolProperty,
    SymbolRectangle,
    SymbolText,
    SymbolUnit,
)
from .kicad_worksheet import (
    CornerType,
    KiCadWorksheet,
    WorksheetBitmap,
    WorksheetLine,
    WorksheetPolygon,
    WorksheetRectangle,
    WorksheetSetup,
    WorksheetText,
)

# Define what gets imported with "from kicad_parser import *"
__all__ = [
    # Version info
    "__version__",
    # File comparison utilities
    "KiCadFileType",
    "detect_kicad_file_type",
    # Common classes
    "KiCadObject",
    "Position",  # Symbol("at") or Symbol("xyz")
    "PositionIdentifier",  # Symbol("at")
    "CoordinatePoint",  # Symbol("xy")
    "CoordinatePointList",  # Symbol("pts")
    "XYCoordinate",  # Symbol("xy")
    "Stroke",  # Backward compatibility alias
    "StrokeDefinition",  # Symbol("stroke")
    "StrokeType",
    "Fill",  # Symbol("fill")
    "FillType",
    "TextEffects",  # Backward compatibility alias
    "TextEffectsDefinition",  # Symbol("effects")
    "Font",  # Backward compatibility alias
    "FontDefinition",  # Symbol("font")
    "FootprintLine",  # Symbol("fp_line")
    "FootprintText",  # Symbol("fp_text")
    "FootprintTextBox",  # Symbol("fp_text_box")
    "FootprintTextType",
    "JustifyHorizontal",
    "JustifyVertical",
    "Layer",  # Symbol("layer")
    "UUID",  # Symbol("tstamp") or Symbol("uuid")
    "Property",  # Symbol("property")
    "PageSettings",  # Symbol("page")
    "TitleBlock",  # Symbol("title_block")
    "Image",  # Symbol("image")
    "str_to_sexpr",
    "sexpr_to_str",
    # Symbol classes
    "KiCadSymbolLibrary",  # Symbol("kicad_symbol_lib")
    "KiCadSymbol",  # Symbol("symbol")
    "SymbolUnit",  # Symbol("symbol")
    "SymbolProperty",  # Symbol("property")
    "SymbolPin",  # Symbol("pin")
    "SymbolArc",  # Symbol("arc")
    "SymbolCircle",  # Symbol("circle")
    "SymbolRectangle",  # Symbol("rectangle")
    "SymbolText",  # Symbol("text")
    "SymbolPolyline",  # Symbol("polyline")
    "SymbolBezier",  # Symbol("bezier")
    "PinElectricalType",
    "PinGraphicStyle",
    # Board/Footprint classes
    "KiCadFootprint",  # Symbol("footprint")
    "FootprintText",  # Symbol("fp_text")
    "FootprintLine",  # Symbol("fp_line")
    "FootprintRectangle",  # Symbol("fp_rect")
    "FootprintCircle",  # Symbol("fp_circle")
    "FootprintArc",  # Symbol("fp_arc")
    "FootprintPolygon",  # Symbol("fp_poly")
    "FootprintPad",  # Symbol("pad")
    "Footprint3DModel",  # Symbol("model")
    "Net",  # Symbol("net")
    "FootprintAttributes",  # Symbol("attr")
    "DrillDefinition",  # Symbol("drill")
    "PadType",
    "PadShape",
    "FootprintType",
    "FootprintTextType",
    # Board Element classes
    "Zone",  # Symbol("zone")
    "ZoneConnect",  # Symbol("connect")
    "ZoneFillSettings",  # Symbol("fill")
    "PadConnection",
    "parse_zone_connect",
    # Graphics classes
    "GraphicalText",  # Symbol("gr_text")
    "GraphicalLine",  # Symbol("gr_line")
    "GraphicalRectangle",  # Symbol("gr_rect")
    "GraphicalCircle",  # Symbol("gr_circle")
    "GraphicalArc",  # Symbol("gr_arc")
    "GraphicalPolygon",  # Symbol("gr_poly")
    "GraphicalBezier",  # Symbol("gr_curve")
    "GraphicalTextBox",  # Symbol("gr_text_box")
    "Dimension",  # Symbol("dimension")
    "DimensionFormat",  # Symbol("format")
    "DimensionStyle",  # Symbol("style")
    "DimensionType",
    # File I/O functions
    "load_kicad_file",
    "save_kicad_file",
    "load_symbol_library",
    "save_symbol_library",
    "load_footprint",
    "save_footprint",
    "load_worksheet",
    "save_worksheet",
    # Parsing functions
    "parse_kicad_file",
    "serialize_kicad_object",
    # Utility functions
    "detect_file_type",
    "detect_file_type_from_path",
    "convert_file",
    "validate_kicad_file",
    "detect_kicad_file_type",
    "parse_any_kicad_file",
    "load_any_kicad_file",
    "save_any_kicad_file",
    "create_basic_symbol",
    "create_basic_footprint",
    "create_basic_worksheet",
    "example_symbol_creation",
    "example_footprint_creation",
    # Worksheet classes
    "KiCadWorksheet",  # Symbol("kicad_wks")
    "WorksheetSetup",  # Symbol("setup")
    "WorksheetLine",  # Symbol("line")
    "WorksheetRectangle",  # Symbol("rect")
    "WorksheetPolygon",  # Symbol("polygon")
    "WorksheetText",  # Symbol("tbtext")
    "WorksheetBitmap",  # Symbol("bitmap")
    "CornerType",
    # Schematic classes
    "KiCadSchematic",  # Symbol("kicad_sch")
    "Junction",  # Symbol("junction")
    "NoConnect",  # Symbol("no_connect")
    "BusEntry",  # Symbol("bus_entry")
    "Wire",  # Symbol("wire")
    "Bus",  # Symbol("bus")
    "Polyline",  # Symbol("polyline")
    "SchematicText",  # Symbol("text")
    "LocalLabel",  # Symbol("label")
    "GlobalLabel",  # Symbol("global_label")
    "HierarchicalLabel",  # Symbol("hierarchical_label")
    "SchematicSymbol",  # Symbol("symbol")
    "HierarchicalSheet",  # Symbol("sheet")
    "HierarchicalPin",  # Symbol("pin")
    "RootSheetInstance",  # Symbol("sheet_instances")
    "SymbolInstance",  # Symbol("symbol_instances")
    "SymbolProject",  # Symbol("project")
    "SheetInstance",  # Symbol("path")
    "SheetProject",  # Symbol("project")
    "LabelShape",
    # Schematic functions
    "load_schematic",
    "save_schematic",
    "create_basic_schematic",
    # PCB classes
    "KiCadPCB",  # Symbol("kicad_pcb")
    "GeneralSettings",  # Symbol("general")
    "BoardLayer",  # Symbol("layer")
    "BoardSetup",  # Symbol("setup")
    "BoardNet",  # Symbol("net")
    "TrackSegment",  # Symbol("segment")
    "TrackVia",  # Symbol("via")
    "TrackArc",  # Symbol("arc")
    "LayerType",
    "ViaType",
    # PCB functions
    "load_pcb",
    "save_pcb",
    "create_basic_pcb",
    # Design Rules classes
    "KiCadDesignRules",  # Symbol("kicad_dru")
    "DesignRule",  # Symbol("rule")
    "DesignRuleConstraint",  # Symbol("constraint")
    "ConstraintValue",
    "ConstraintType",
    "DisallowType",
    "DRCSeverity",
    # Design Rules functions
    "load_design_rules",
    "save_design_rules",
    "parse_kicad_design_rules_file",
    "write_kicad_design_rules_file",
    "create_basic_design_rules",
]
