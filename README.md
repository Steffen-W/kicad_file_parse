# KiCad Parser

A comprehensive Python library for parsing and manipulating KiCad S-Expression files, including symbol libraries (.kicad_sym), footprints (.kicad_mod), worksheets (.kicad_wks), schematics (.kicad_sch), PCBs (.kicad_pcb), and related formats.

## Features

- **Full KiCad Format Support**: Parse and write KiCad symbol libraries, footprints, worksheets, schematics, and PCBs
- **Type-Safe**: Complete type hints for better IDE support and code safety
- **High-Level API**: Easy-to-use functions for common operations
- **Low-Level Access**: Direct access to S-expression data structures when needed
- **Multi-Unit Symbols**: Full support for complex symbols with multiple units and alternate representations
- **Advanced Pin Types**: Complete pin electrical type support (passive, input, output, bidirectional, tri_state, power_in, power_out, open_collector, open_emitter, free, unspecified, no_connect)
- **Hierarchical Schematics**: Support for hierarchical sheets, sheet pins, and complex project structures
- **Advanced PCB Features**: Zones with thermal reliefs and hatching patterns, advanced copper pours with complex fill settings, track arcs, board stackup definitions, and layer management
- **Modern Python**: Supports Python 3.8+
- **Zero Dependencies**: No external dependencies - includes bundled S-expression parser
- **Comprehensive Testing**: 385+ test cases ensuring reliability

## Installation

```bash
pip install kicad-parser
```

Or install from source:

```bash
git clone https://github.com/Steffen-W/kicad-parser.git
cd kicad-parser
pip install -e .
```

## Quick Start

### Loading and Modifying a Symbol Library

```python
from kicad_parser import load_symbol_library, save_symbol_library

# Load a KiCad symbol library
library = load_symbol_library("path/to/library.kicad_sym")

# Access symbols
symbol = library.symbols[0]
print(f"Symbol: {symbol.name}")

# Modify properties
symbol.set_property("Reference", "IC")
symbol.set_property("Description", "Modified with kicad-parser")

# Save changes
save_symbol_library(library, "path/to/modified_library.kicad_sym")
```

### Creating Symbols from Scratch

```python
from kicad_parser import (
    create_basic_symbol, KiCadSymbolLibrary, 
    SymbolPin, PinElectricalType, PinGraphicStyle, Position
)

# Create a new symbol library
library = KiCadSymbolLibrary(version=20211014, generator="kicad-parser")

# Create a basic resistor symbol
resistor = create_basic_symbol("R_Generic", "R", "R")

# Add pins
resistor.pins.extend([
    SymbolPin(
        electrical_type=PinElectricalType.PASSIVE,
        graphic_style=PinGraphicStyle.LINE,
        position=Position(-5.08, 0, 0),
        length=2.54,
        name="~",
        number="1"
    ),
    SymbolPin(
        electrical_type=PinElectricalType.PASSIVE,
        graphic_style=PinGraphicStyle.LINE,
        position=Position(5.08, 0, 0),
        length=2.54,
        name="~",
        number="2"
    )
])

# Add to library and save
library.add_symbol(resistor)
save_symbol_library(library, "custom_library.kicad_sym")
```

### Working with Footprints

```python
from kicad_parser import load_footprint, save_footprint, create_basic_footprint

# Load footprint
footprint = load_footprint("path/to/footprint.kicad_mod")

# Create basic footprint
new_footprint = create_basic_footprint("0805_Resistor", "R", "0805")

# Save footprint
save_footprint(new_footprint, "0805_resistor.kicad_mod")
```

### Working with Worksheets

```python
from kicad_parser import (
    load_worksheet, save_worksheet, create_basic_worksheet,
    KiCadWorksheet, WorksheetText, WorksheetRectangle, 
    Position, CornerType
)

# Load existing worksheet
worksheet = load_worksheet("path/to/worksheet.kicad_wks")

# Create basic worksheet
new_worksheet = create_basic_worksheet("My Project", "My Company")

# Create custom worksheet
custom_worksheet = KiCadWorksheet()

# Add title block rectangle
custom_worksheet.add_rectangle(
    WorksheetRectangle(
        start=Position(110.0, 5.0),
        end=Position(210.0, 35.0),
        corner=CornerType.RIGHT_BOTTOM
    )
)

# Add title text
custom_worksheet.add_text(
    WorksheetText(
        text="Project Title",
        position=Position(160.0, 20.0),
        corner=CornerType.RIGHT_BOTTOM,
        maxlen=25
    )
)

# Save worksheet
save_worksheet(custom_worksheet, "custom_worksheet.kicad_wks")
```

### Generating UUIDs

KiCad objects often require unique identifiers. Use the `generate_UUID()` function instead of creating UUIDs manually:

```python
from kicad_parser import generate_UUID, KiCadSchematic, TitleBlock

# Generate UUIDs for new objects
schematic = KiCadSchematic(
    uuid=generate_UUID(),
    title_block=TitleBlock(title="My Project")
)

# For groups, symbols, or other objects requiring UUIDs
group_id = generate_UUID()
symbol_uuid = generate_UUID()
```

**Note**: UUIDs are no longer generated automatically. Always use `generate_UUID()` when creating objects that require unique identifiers.

### Working with Schematics

```python
from kicad_parser import (
    load_schematic, save_schematic, create_basic_schematic,
    KiCadSchematic, Junction, Wire, Bus, SchematicSymbol,
    GlobalLabel, HierarchicalSheet, HierarchicalPin, 
    LabelShape, PinElectricalType, Position, UUID, Property, TitleBlock
)

# Load existing schematic
schematic = load_schematic("path/to/schematic.kicad_sch")

# Create basic schematic
new_schematic = create_basic_schematic("LED Blinker", "My Company")

# Create comprehensive schematic
custom_schematic = KiCadSchematic(
    title_block=TitleBlock(
        title="Custom Circuit",
        date="2024-01-01",
        revision="Rev 1.0"
    )
)

# Add junctions (connection points)
custom_schematic.junctions.append(
    Junction(
        position=Position(50.0, 50.0),
        diameter=0.36,
        uuid=UUID("junction-1")
    )
)

# Add wires (connections)
custom_schematic.wires.extend([
    Wire(
        points=[(25.4, 25.4), (50.0, 25.4)],
        uuid=UUID("wire-1")
    ),
    Wire(
        points=[(50.0, 25.4), (50.0, 50.0)],  
        uuid=UUID("wire-2")
    )
])

# Add components/symbols
custom_schematic.symbols.append(
    SchematicSymbol(
        library_id="Device:R",
        position=Position(75.0, 50.0),
        uuid=UUID("R1"),
        properties=[
            Property("Reference", "R1"),
            Property("Value", "10k"),
            Property("Footprint", "Resistor_SMD:R_0603_1608Metric")
        ]
    )
)

# Add global labels for cross-sheet connections
custom_schematic.global_labels.append(
    GlobalLabel(
        text="VCC",
        shape=LabelShape.INPUT,
        position=Position(25.4, 75.0),
        uuid=UUID("vcc-label")
    )
)

# Add hierarchical sheets for complex designs
power_sheet = HierarchicalSheet(
    position=Position(150.0, 100.0),
    size=(50.0, 40.0),
    sheet_name="Power Supply",
    file_name="power.kicad_sch",
    uuid=UUID("power-sheet")
)

# Add pins to hierarchical sheet
power_sheet.pins.append(
    HierarchicalPin(
        name="VCC_OUT",
        electrical_type=PinElectricalType.OUTPUT,
        position=Position(150.0, 110.0),
        uuid=UUID("vcc-out-pin")
    )
)

custom_schematic.sheets.append(power_sheet)

# Add bus connections for multi-signal connections
custom_schematic.buses.append(
    Bus(
        points=[(100.0, 150.0), (200.0, 150.0)],
        uuid=UUID("data-bus")
    )
)

# Save schematic
save_schematic(custom_schematic, "custom_circuit.kicad_sch")
```

### Working with PCBs (Boards)

```python
from kicad_parser import (
    load_pcb, save_pcb, create_basic_pcb,
    KiCadPCB, BoardLayer, BoardNet, GeneralSettings, Zone,
    TrackSegment, TrackVia, TrackArc, LayerType, ViaType, 
    PadConnection, UUID
)

# Load existing PCB
pcb = load_pcb("path/to/board.kicad_pcb")

# Create basic PCB
new_pcb = create_basic_pcb()

# Create comprehensive PCB
custom_pcb = KiCadPCB(
    version=20230121,
    generator="kicad-parser",
    general=GeneralSettings(thickness=1.6)
)

# Define standard layer stackup
layers = [
    BoardLayer(ordinal=0, canonical_name="F.Cu", layer_type=LayerType.SIGNAL, user_name="Front Copper"),
    BoardLayer(ordinal=31, canonical_name="B.Cu", layer_type=LayerType.SIGNAL, user_name="Back Copper"),
    BoardLayer(ordinal=36, canonical_name="B.SilkS", layer_type=LayerType.USER, user_name="B.Silkscreen"),
    BoardLayer(ordinal=37, canonical_name="F.SilkS", layer_type=LayerType.USER, user_name="F.Silkscreen"),
    BoardLayer(ordinal=44, canonical_name="Edge.Cuts", layer_type=LayerType.USER, user_name="Edge Cuts"),
]
custom_pcb.layers = layers

# Create nets
nets = [
    BoardNet(ordinal=0, name=""),  # Unconnected net
    BoardNet(ordinal=1, name="GND"),
    BoardNet(ordinal=2, name="VCC"),
    BoardNet(ordinal=3, name="SIGNAL_DATA"),
]
custom_pcb.nets = nets

# Add track segments (copper traces)
custom_pcb.track_segments.extend([
    TrackSegment(
        start=(10.0, 10.0),
        end=(20.0, 10.0),
        width=0.25,  # 0.25mm width
        layer="F.Cu",
        net=1,  # GND net
        uuid=UUID("track-gnd-1")
    ),
    TrackSegment(
        start=(10.0, 15.0),
        end=(20.0, 15.0),
        width=0.25,
        layer="F.Cu",
        net=2,  # VCC net
        uuid=UUID("track-vcc-1")
    )
])

# Add vias (layer connections)
custom_pcb.track_vias.extend([
    TrackVia(
        position=(15.0, 10.0),
        size=0.8,      # Via diameter
        drill=0.4,     # Drill diameter
        layers=("F.Cu", "B.Cu"),
        net=1,         # GND net
        via_type=ViaType.THROUGH,
        uuid=UUID("via-gnd-1")
    ),
    TrackVia(
        position=(15.0, 15.0),
        size=0.8,
        drill=0.4,
        layers=("F.Cu", "B.Cu"),
        net=2,         # VCC net
        via_type=ViaType.THROUGH,
        uuid=UUID("via-vcc-1")
    )
])

# Add copper zones/pours
custom_pcb.zones.append(
    Zone(
        net=1,  # GND net
        net_name="GND",
        layers=["F.Cu"],
        polygon_points=[
            (5.0, 5.0), (25.0, 5.0), (25.0, 25.0), (5.0, 25.0)
        ],
        connect_pads=PadConnection.THERMAL,
        min_thickness=0.254,
        uuid=UUID("ground-zone-1")
    )
)

# Add curved traces (track arcs)
custom_pcb.track_arcs.append(
    TrackArc(
        start=(30.0, 10.0),
        mid=(32.0, 12.0),
        end=(34.0, 10.0),
        width=0.25,
        layer="F.Cu",
        net=3,  # SIGNAL_DATA net
        uuid=UUID("arc-signal-1")
    )
)

# Save PCB
save_pcb(custom_pcb, "custom_board.kicad_pcb")
```

## API Reference

### High-Level Functions

#### File I/O

- `load_symbol_library(filepath)` → `KiCadSymbolLibrary`
- `save_symbol_library(library, filepath)` → `None`
- `load_footprint(filepath)` → `KiCadFootprint`
- `save_footprint(footprint, filepath)` → `None`
- `load_worksheet(filepath)` → `KiCadWorksheet`
- `save_worksheet(worksheet, filepath)` → `None`
- `load_schematic(filepath)` → `KiCadSchematic`
- `save_schematic(schematic, filepath)` → `None`
- `load_pcb(filepath)` → `KiCadPCB`
- `save_pcb(pcb, filepath)` → `None`
- `load_kicad_file(filepath)` → `KiCadObject` (auto-detects type)
- `save_kicad_file(obj, filepath)` → `None`

#### Creation Helpers

- `create_basic_symbol(name, reference, value)` → `KiCadSymbol`
- `create_basic_footprint(name, reference, value)` → `KiCadFootprint`
- `create_basic_worksheet(title, company)` → `KiCadWorksheet`
- `create_basic_schematic(title, company)` → `KiCadSchematic`
- `create_basic_pcb()` → `KiCadPCB`

#### Utilities

- `detect_file_type(content)` → `str`
- `validate_kicad_file(filepath)` → `dict`
- `convert_file(input_path, output_path, modifier_func=None)` → `None`
- `str_to_sexpr(content)` → `SExpr` - Convert string content to S-expression
- `sexpr_to_str(sexpr, pretty_print=True)` → `str` - Convert S-expression to formatted string
- `generate_UUID()` → `UUID` - Generate a new random UUID for KiCad objects

### Core Classes

#### Symbol Library (`KiCadSymbolLibrary`)

- `symbols: List[KiCadSymbol]` - List of symbols in library
- `version: int` - KiCad format version
- `generator: str` - Generator identifier
- `get_symbol(name)` → `Optional[KiCadSymbol]`
- `add_symbol(symbol)` → `None`
- `remove_symbol(name)` → `bool`

*Detailed S-expression format reference: [sexp-intro.md](doc/file-formats/sexp-intro.md)*

#### Symbol (`KiCadSymbol`)

- `name: str` - Symbol name
- `extends: Optional[str]` - Parent symbol for inheritance (symbol extends/parent support)
- `pin_numbers_hide: bool` - Hide pin numbers
- `pin_names_hide: bool` - Hide pin names  
- `pin_names_offset: float` - Pin name offset distance (advanced pin properties)
- `in_bom: bool` - Include in bill of materials
- `on_board: bool` - Export to PCB
- `properties: List[SymbolProperty]` - Symbol properties
- `pins: List[SymbolPin]` - Symbol pins with all electrical types
- `units: List[SymbolUnit]` - Symbol units for multi-unit symbols
- `rectangles: List[SymbolRectangle]` - Graphic rectangles
- `circles: List[SymbolCircle]` - Graphic circles
- `arcs: List[SymbolArc]` - Graphic arcs
- `beziers: List[SymbolBezier]` - Bézier curves
- `polylines: List[SymbolPolyline]` - Multi-point lines
- `texts: List[SymbolText]` - Text elements
- `get_property(key)` → `Optional[SymbolProperty]`
- `set_property(key, value, **kwargs)` → `None`
- `remove_property(key)` → `bool`

*Detailed S-expression format reference: [sexp-intro.md](doc/file-formats/sexp-intro.md)*

#### Footprint (`KiCadFootprint`)

- `library_link: str` - Link to symbol library
- `pads: List[FootprintPad]` - Footprint pads with custom primitives and complex shapes support
- `zones: List[Zone]` - Footprint-level copper zones
- `keepout_zones: List[Zone]` - Footprint keepout areas with configurable restrictions
- `groups: List[Group]` - Footprint object grouping for organization
- `net_tie_pad_groups: List[str]` - Net-tie pad group definitions for shorts allowed between pads
- `private_layers: List[str]` - Private layer definitions for footprint-specific layers
- `texts: List[FootprintText]` - Text elements
- `lines: List[FootprintLine]` - Graphic lines
- `rectangles: List[FootprintRectangle]` - Graphic rectangles
- `circles: List[FootprintCircle]` - Graphic circles
- `arcs: List[FootprintArc]` - Graphic arcs
- `polygons: List[FootprintPolygon]` - Graphic polygons
- `model: Footprint3DModel` - Advanced 3D model with positioning, scaling, rotation, opacity, and visibility control
- `position: Position` - Footprint position
- `layer: str` - Footprint placement layer
- `locked: bool` - Footprint lock status
- `attributes: FootprintAttributes` - Footprint attributes (SMD, through-hole, exclude from BOM/board)

*Detailed S-expression format reference: [sexp-intro.md](doc/file-formats/sexp-intro.md)*

#### Worksheet (`KiCadWorksheet`)

- `version: int` - KiCad format version
- `generator: str` - Generator identifier
- `setup: WorksheetSetup` - Page setup configuration
- `lines: List[WorksheetLine]` - Line elements
- `rectangles: List[WorksheetRectangle]` - Rectangle elements
- `polygons: List[WorksheetPolygon]` - Polygon elements
- `texts: List[WorksheetText]` - Title block text elements
- `bitmaps: List[WorksheetBitmap]` - Image elements
- `add_line(line)` → `None`
- `add_rectangle(rectangle)` → `None`
- `add_polygon(polygon)` → `None`
- `add_text(text)` → `None`
- `add_bitmap(bitmap)` → `None`

*Detailed S-expression format reference: [sexp-worksheet.md](doc/file-formats/sexp-worksheet.md)*

#### Schematic (`KiCadSchematic`)

- `version: int` - KiCad format version
- `generator: str` - Generator identifier
- `uuid: UUID` - Schematic unique identifier
- `page_settings: PageSettings` - Paper size and orientation
- `title_block: TitleBlock` - Title block information
- `lib_symbols: List[KiCadSymbol]` - Symbol library definitions
- `junctions: List[Junction]` - Connection junctions
- `no_connects: List[NoConnect]` - Unused pin markers
- `wires: List[Wire]` - Wire connections
- `buses: List[Bus]` - Bus connections
- `symbols: List[SchematicSymbol]` - Component instances
- `global_labels: List[GlobalLabel]` - Cross-sheet labels
- `hierarchical_labels: List[HierarchicalLabel]` - Sheet connection labels
- `local_labels: List[LocalLabel]` - Wire/bus labels
- `sheets: List[HierarchicalSheet]` - Sub-schematic sheets
- `texts: List[SchematicText]` - Text annotations
- `polylines: List[Polyline]` - Graphical lines
- `images: List[Image]` - Embedded images

*Detailed S-expression format reference: [sexp-schematic.md](doc/file-formats/sexp-schematic.md)*

### Data Types

#### Core S-Expression Types

- `Position(x, y, angle, layer)` - Position identifier with coordinates, rotation, and optional layer
- `CoordinatePoint(x, y)` - Single coordinate point with X/Y values
- `CoordinatePointList(points)` - Point list for polygons and curves with XY coordinate pairs
- `Stroke(width, type, color)` - Stroke definition with line styles, width, and color
- `StrokeType` - DEFAULT, NONE, SOLID, DASH, DOT, DASH_DOT, DASH_DOT_DOT - Line style types
- `TextEffects(font, justify, hide, mirror)` - Complete text formatting with alignment and visibility
- `Font(size, thickness, bold, italic, line_spacing, face)` - Font definition with all typography attributes
- `Fill(type, color)` - Fill definition with type and color
- `FillType` - NONE, OUTLINE, BACKGROUND - Fill style types
- `PageSettings(paper, width, height, portrait)` - Page configuration with size and orientation
- `TitleBlock(title, date, revision, company, comment_1_4)` - Title block with project information
- `Property(key, value, id, position, effects, show_name, do_not_autoplace)` - Properties with positioning and display control
- `UUID(uuid_string)` - Universally unique identifiers for object tracking
- `Image(position, scale, layer, data, uuid)` - Embedded PNG/bitmap images with positioning and Base64 data
- `Color(r, g, b, a)` - RGBA color definition with transparency support
- `Justify` - LEFT, CENTER, RIGHT, TOP, BOTTOM - Text alignment options
- `PaperSize` - A4, A3, A2, A1, A0, LETTER, LEGAL, TABLOID, USR - Standard paper sizes

#### Board-Specific Types

- `CANONICAL_LAYER_NAMES` - All 58 standard KiCad layers (F.Cu, B.Cu, F.SilkS, etc.)

#### Symbol Types

- `SymbolPin(electrical_type, graphic_style, position, length, name, number)` - Symbol pins with all electrical types
- `SymbolProperty(key, value, id, position, effects)` - Symbol properties with positioning
- `SymbolUnit(name, unit_id)` - Multi-unit symbol definitions for complex components
- `SymbolArc(start, mid, end, stroke, fill, uuid)` - Graphic arc elements
- `SymbolCircle(center, radius, stroke, fill, uuid)` - Graphic circle elements  
- `SymbolRectangle(start, end, stroke, fill, uuid)` - Graphic rectangle elements
- `SymbolBezier(points, stroke, fill, uuid)` - Bézier curve elements
- `SymbolPolyline(points, stroke, fill, uuid)` - Multi-point line elements
- `SymbolText(text, position, angle, effects, uuid)` - Text annotations and labels

#### Pin Types

- `PinElectricalType` - PASSIVE, INPUT, OUTPUT, BIDIRECTIONAL, TRI_STATE, POWER_IN, POWER_OUT, OPEN_COLLECTOR, OPEN_EMITTER, FREE, UNSPECIFIED, NO_CONNECT
- `PinGraphicStyle` - LINE, INVERTED, CLOCK, INVERTED_CLOCK, INPUT_LOW, CLOCK_LOW, OUTPUT_LOW, EDGE_CLOCK_HIGH, NONLOGIC

#### Footprint Types

- `FootprintPad(number, type, shape, size, drill, layers, position, net, uuid)` - Footprint pads with all pad types and shapes
- `FootprintText(type, text, position, layer, effects, uuid)` - Footprint text elements (reference, value, user)
- `FootprintLine(start, end, layer, width, uuid)` - Footprint graphic lines
- `FootprintRectangle(start, end, layer, stroke, fill, uuid)` - Footprint graphic rectangles
- `FootprintCircle(center, end, layer, stroke, fill, uuid)` - Footprint graphic circles
- `FootprintArc(start, mid, end, layer, stroke, uuid)` - Footprint graphic arcs
- `FootprintPolygon(points, layer, stroke, fill, uuid)` - Footprint graphic polygons
- `FootprintAttributes(type, board_only, exclude_from_pos_files, exclude_from_bom)` - Footprint placement attributes
- `FootprintOptions(clearance, solder_mask_margin, solder_paste_margin, zone_connect, thermal_width, thermal_gap)` - Advanced footprint options and clearances
- `CustomPadOptions(clearance, solder_mask_margin, solder_paste_margin, thermal_gap)` - Custom pad-specific options
- `FootprintPrimitives(primitives_list)` - Custom pad primitive shapes and geometries
- `CustomPadPrimitives(primitives_list)` - Advanced custom pad shape definitions
- `Net(code, name)` - Network connection definitions for pads
- `Drill(diameter, oval_width)` - Drill hole specifications with oval support
- `DrillDefinition(size, offset, shape)` - Complete drill definition with positioning
- `PadAttribute(type, value)` - Pad electrical and mechanical attributes
- `KeepoutSettings(tracks, vias, pads, copperpour, footprints)` - Keepout zone restrictions
- `KeepoutZone(layers, settings, polygon, uuid)` - Keepout areas with configurable restrictions
- `FootprintGroup(name, members, uuid)` - Footprint object grouping for organization
- `Model3D(filename, offset, scale, rotate)` - 3D model positioning and transformation
- `Footprint3DModel(filename, offset, scale, rotate, opacity, hide)` - 3D model with full control
- `FootprintType` - SMD, THROUGH_HOLE, EXCLUDE_FROM_POS_FILES, EXCLUDE_FROM_BOM - Footprint classifications
- `FootprintTextType` - REFERENCE, VALUE, USER - Text element types

#### Worksheet Types

- `WorksheetSetup(textsize, linewidth, textlinewidth, margins)` - Page setup with text sizes and margins
- `WorksheetLine(start, end, name, linewidth, repeat, increment)` - Lines with optional repetition and increments
- `WorksheetRectangle(start, end, name, linewidth, repeat, increment)` - Rectangles for borders and frames
- `WorksheetPolygon(points, name, linewidth, repeat, increment)` - Custom polygon shapes with coordinate points
- `WorksheetText(text, position, corner, name, maxlen, maxheight, font, justify)` - Title block text with positioning and limits
- `WorksheetBitmap(position, scale, data, name, repeat, increment)` - Embedded bitmap images with Base64 data
- `CornerType` - LEFT_TOP, LEFT_BOTTOM, RIGHT_BOTTOM, RIGHT_TOP - Position reference points

#### Schematic Types

- `Junction(position, diameter, color, uuid)` - Connection junction points
- `BusEntry(position, size, stroke, uuid)` - Bus connection entries with angle and direction
- `Wire(points, stroke, uuid)` - Electrical wire connections with multi-point routing
- `Bus(points, stroke, uuid)` - Multi-signal bus connections with stroke styling
- `SchematicText(text, position, effects, exclude_from_sim, uuid)` - Text annotations with simulation control
- `LocalLabel(text, position, effects, exclude_from_sim, uuid)` - Wire/bus name labels
- `GlobalLabel(text, shape, position, fields, properties, uuid)` - Cross-sheet labels with custom fields
- `HierarchicalLabel(text, shape, position, effects, uuid)` - Sheet connection labels
- `SchematicSymbol(library_id, position, unit, convert, exclude_from_sim, properties, instances)` - Component instances with simulation control
- `SheetInstance(path, page, uuid)` - Sheet instance definitions for hierarchical designs
- `SheetProject(file, name, description)` - Project information for sheet references
- `HierarchicalSheet(position, size, sheet_name, file_name, pins, project, instances, uuid)` - Sub-schematic sheets with project data
- `HierarchicalPin(name, electrical_type, position, uuid)` - Sheet connection pins
- `RootSheetInstance(project, page, uuid)` - Root sheet instance for project hierarchy
- `LabelShape` - INPUT, OUTPUT, BIDIRECTIONAL, TRI_STATE, PASSIVE - Label and pin shapes
- `NoConnect(position, uuid)` - Unused pin markers
- `Polyline(points, stroke, uuid)` - Graphical line drawings
- `Image(position, scale, layer, data, uuid)` - Embedded PNG images with Base64 data

#### PCB Types

- `KiCadPCB(version, generator, general, paper, layers, setup, nets, footprints, track_segments, track_vias, track_arcs, zones, groups)` - Complete PCB definition with all elements
- `GeneralSettings(thickness, legacy_teardrops)` - Board general settings and thickness
- `BoardLayer(ordinal, canonical_name, layer_type, user_name)` - PCB layer definition with all 58 standard layers
- `BoardSetup(stackup, design_rules, defaults, diff_pair_dimensions, pad_to_mask_clearance)` - Complete PCB setup with design rules and stackup
- `BoardNet(ordinal, name)` - Electrical net definition with net classes
- `TrackSegment(start, end, width, layer, net, tstamp, uuid)` - Copper trace segment with timestamps
- `TrackVia(position, size, drill, layers, net, via_type, remove_unused_layers, keep_end_layers, uuid)` - Via with advanced layer management
- `TrackArc(start, mid, end, width, layer, net, tstamp, uuid)` - Curved copper trace with arc geometry
- `Zone(net, net_name, layers, tstamp, name, hatch, priority, connect_pads, min_thickness, filled_polygons, fill_segments)` - Complete zone with fill geometry
- `ZoneConnect(clearance, min_thickness, thermal_gap, thermal_bridge_width)` - Zone connection settings
- `ZoneFillSettings(yes, mode, thermal_gap, thermal_bridge_width, smoothing, island_removal_mode, island_area_min)` - Zone fill configuration
- `Group(name, id, locked, members, uuid)` - Object grouping with locking and member tracking
- `Net(ordinal, name, uuid)` - Net definition with UUID tracking
- `Dimension(type, layer, tstamp, pts, height, orientation, leader_length, text_position, format, style, uuid)` - PCB dimensions and measurements
- `LayerType` - SIGNAL, POWER, MIXED, JUMPER, USER - Layer type classification
- `ViaType` - THROUGH, BLIND, MICRO - Via type specification with advanced drilling
- `PadConnection` - INHERITED, SOLID, THERMAL_RELIEFS, THRU_HOLE_ONLY, NONE - Zone connection styles
- `PadShape` - CIRCLE, RECT, OVAL, TRAPEZOID, ROUNDRECT, CUSTOM - Pad shape definitions
- `DrillShape` - CIRCLE, OVAL - Drill hole shapes

*Detailed S-expression format reference: [sexp-pcb.md](doc/file-formats/sexp-pcb.md)*

#### Design Rules Types

- `KiCadDesignRules(version, generator, rules)` - Complete design rules definition with all DRC rules
- `DesignRule(name, layer, constraint, condition, severity)` - Individual design rule with conditions and constraints
- `DesignRuleConstraint(type, value, opt_value, comment)` - Design rule constraint with value ranges
- `ConstraintValue(min, opt, max, units)` - Constraint value with optional minimum, optimal, and maximum values
- `ConstraintType` - CLEARANCE, TRACK_WIDTH, VIA_SIZE, DRILL_SIZE, LENGTH, SKEW, DISALLOW - Constraint classifications
- `DRCSeverity` - ERROR, WARNING, IGNORE, EXCLUSION - DRC violation severity levels

*Detailed S-expression format reference: [sexp-design-rules.md](doc/file-formats/sexp-design-rules.md)*

#### Graphics Types

- `GraphicalText(text, position, angle, layer, effects, uuid)` - Text elements with positioning and styling
- `GraphicalLine(start, end, layer, stroke, uuid)` - Straight line segments with stroke styling
- `GraphicalRectangle(start, end, layer, stroke, fill, uuid)` - Rectangle shapes with fill and stroke
- `GraphicalCircle(center, radius, layer, stroke, fill, uuid)` - Circle shapes with customizable appearance
- `GraphicalArc(start, mid, end, layer, stroke, uuid)` - Arc segments defined by three points
- `GraphicalPolygon(points, layer, stroke, fill, uuid)` - Multi-point polygon shapes
- `GraphicalBezier(points, layer, stroke, fill, uuid)` - Bézier curve segments for smooth curves
- `GraphicalTextBox(text, position, size, angle, layer, effects, stroke, uuid)` - Text with background box
- `Dimension(type, layer, pts, height, orientation, leader_length, format, style, uuid)` - PCB measurements and annotations
- `DimensionFormat(prefix, suffix, units, units_format, precision, suppress_zeros)` - Dimension text formatting
- `DimensionStyle(thickness, arrow_length, text_position_mode, extension_height, text_frame)` - Dimension appearance settings

#### Design Rules Types

- `KiCadDesignRules(version, generator, rules)` - Complete design rules definition with all DRC rules
- `DesignRule(name, layer, constraint, condition, severity)` - Individual design rule with conditions and constraints
- `DesignRuleConstraint(type, value, opt_value, comment)` - Design rule constraint with value ranges
- `ConstraintValue(min, opt, max, units)` - Constraint value with optional minimum, optimal, and maximum values
- `ConstraintType` - CLEARANCE, TRACK_WIDTH, VIA_SIZE, DRILL_SIZE, LENGTH, SKEW, DISALLOW - Constraint classifications
- `DRCSeverity` - ERROR, WARNING, IGNORE, EXCLUSION - DRC violation severity levels

## Examples

The `examples/` directory contains complete working examples:

- `basic_usage.py` - Loading, modifying, and saving symbol libraries
- `create_symbol.py` - Creating custom symbols and libraries from scratch
- `file_conversion.py` - File validation and conversion utilities
- `worksheet_example.py` - Creating custom worksheets and page layouts
- `schematic_example.py` - Creating comprehensive schematics with all element types
- `pcb_example.py` - Creating PCBs with layers, nets, tracks, and vias

Run examples:

```bash
cd examples
python basic_usage.py
python create_symbol.py
python file_conversion.py
python worksheet_example.py
python schematic_example.py
```

## Development

### Setup Development Environment

```bash
git clone https://github.com/Steffen-W/kicad-parser.git
cd kicad-parser
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=kicad_parser

# Generate coverage report
pytest --cov=kicad_parser --cov-report=html
pytest --cov=kicad_parser --cov-report=term-missing
```

### Code Quality

```bash
# Install required tools
pip install black isort flake8 mypy
npm install -g pyright

# Format entire codebase with black
black .

# Sort imports for entire codebase
isort .

# Lint code with flake8
flake8 kicad_parser

# Static type checking with Pyright
pyright

# Static type checking with mypy
mypy kicad_parser
```

## Implementation Reference

This library was developed based on the official KiCad S-Expression file format documentation:
**<https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html>**

The data schema for parsing KiCad files is sourced from:
**<https://gitlab.com/kicad/services/kicad-dev-docs/-/tree/master/content/file-formats>**

The DRC (Design Rule Checking) implementation is based on:
**<https://docs.kicad.org/master/id/pcbnew/pcbnew_advanced.html#custom-design-rules>**

The Python functions and data structures closely follow the specifications described in the KiCad documentation to ensure maximum compatibility and correctness when parsing and generating KiCad files.

## S-Expression Format Support

This library provides **complete implementation** of the KiCad S-Expression format specification with support for all positioning, styling, layering, and embedded content elements.

## Module Structure

The library is organized into focused modules to avoid circular dependencies and provide clear separation of concerns:

- **`kicad_common.py`** - Common classes and utilities (UUID, Position, SExpr parsing, etc.)
- **`kicad_symbol.py`** - Symbol library and symbol definitions
- **`kicad_board.py`** - Footprint definitions and board-level footprint components
- **`kicad_board_elements.py`** - Shared board elements (zones, connections) used by both footprints and PCBs
- **`kicad_pcb.py`** - PCB definitions, layers, nets, tracks, and board-specific components
- **`kicad_schematic.py`** - Schematic definitions and hierarchical designs
- **`kicad_worksheet.py`** - Worksheet/template definitions for documentation
- **`kicad_graphics.py`** - Graphical primitives (lines, arcs, text, etc.)
- **`kicad_design_rules.py`** - Design rule checking (DRC) definitions
- **`kicad_file.py`** - File I/O operations and format detection
- **`kicad_main.py`** - High-level convenience functions and examples

The separation of board elements allows both footprints and PCBs to use shared zone and connection classes without circular import issues.

## Supported File Formats

- **Symbol Libraries** (`.kicad_sym`) - Complete support with all S-Expression features (see [doc/file-formats/sexp-intro.md](doc/file-formats/sexp-intro.md))
- **Footprints** (`.kicad_mod`) - Complete support with advanced pad features, includes legacy `module` format (see [doc/file-formats/sexp-intro.md](doc/file-formats/sexp-intro.md))
- **Worksheets** (`.kicad_wks`) - Complete support with custom layouts (see [doc/file-formats/sexp-worksheet.md](doc/file-formats/sexp-worksheet.md))
- **Schematics** (`.kicad_sch`) - Complete support with hierarchical designs, buses, and all element types (see [doc/file-formats/sexp-schematic.md](doc/file-formats/sexp-schematic.md))
- **PCBs** (`.kicad_pcb`) - Complete support with layers, nets, tracks, vias, and zones (see [doc/file-formats/sexp-pcb.md](doc/file-formats/sexp-pcb.md))
- **Design Rules** (`.kicad_dru`) - Complete support for design rule checking (see [doc/file-formats/sexp-design-rules.md](doc/file-formats/sexp-design-rules.md))

## Version Compatibility

This library provides backward compatibility for different KiCad S-Expression formats without requiring explicit version detection. Supports KiCad 5.x+ with automatic format modernization during parsing while preserving the original version numbers when saving.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Run the test suite (`pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Based on the official KiCad S-Expression documentation
- Includes a modified version of `sexpdata` for S-expression parsing
- Inspired by the KiCad development community

---

**Documentation**: [KiCad S-Expression Format](https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html)  
**Issues**: [GitHub Issues](https://github.com/Steffen-W/kicad-parser/issues)  
**Repository**: [GitHub Repository](https://github.com/Steffen-W/kicad-parser)
