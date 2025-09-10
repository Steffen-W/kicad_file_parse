# Schematic File Format

## Label and Pin Shapes

Valid shape tokens for global labels, hierarchical labels, and hierarchical sheet pins:

- `input` - Input shape
- `output` - Output shape  
- `bidirectional` - Bidirectional shape
- `tri_state` - Tri-state shape
- `passive` - Passive shape

## Header Section

*Parsed by: `KiCadSchematic.from_sexpr()` in `kicad_schematic.py`*

```
(kicad_sch
  (version VERSION)
  (generator GENERATOR)
  ;; schematic sections...
)
```

## Unique Identifier Section

*Parsed by: `UUID.from_sexpr()` in `kicad_common.py`*

```
(uuid UNIQUE_IDENTIFIER)
```

## Page Settings Section

*Parsed by: `PageSettings.from_sexpr()` in `kicad_common.py`*

```
(page_settings
  POSITION_IDENTIFIER
  [title_block TITLE_BLOCK] ; optional
)
```

## Title Block Section

*Parsed by: `TitleBlock.from_sexpr()` in `kicad_common.py`*

```
(title_block
  [title "TITLE"] ; optional
  [date "DATE"] ; optional
  [rev "REVISION"] ; optional
  [company "COMPANY"] ; optional
  [comment 1 "COMMENT1"] ; optional
  [comment 2 "COMMENT2"] ; optional
  [comment 3 "COMMENT3"] ; optional
  [comment 4 "COMMENT4"] ; optional
)
```

## Library Symbol Section

*Parsed in: `KiCadSchematic.from_sexpr()` in `kicad_schematic.py`*

```
(lib_symbols
  SYMBOL_DEFINITIONS... ; optional
)
```

## Junction Section

*Parsed by: `Junction.from_sexpr()` in `kicad_schematic.py`*

```
(junction
  POSITION_IDENTIFIER
  [(diameter DIAMETER)] ; optional
  [(color R G B A)] ; optional
  UNIQUE_IDENTIFIER
)
```

## No Connect Section

*Parsed by: `NoConnect.from_sexpr()` in `kicad_schematic.py`*

```
(no_connect
  POSITION_IDENTIFIER
  UNIQUE_IDENTIFIER
)
```

## Bus Entry Section

*Parsed by: `BusEntry.from_sexpr()` in `kicad_schematic.py`*

```
(bus_entry
  POSITION_IDENTIFIER
  (size X Y)
  STROKE_DEFINITION
  UNIQUE_IDENTIFIER
)
```

## Wire and Bus Section

*Parsed by: `Wire.from_sexpr()` in `kicad_schematic.py`*

```
(wire
  COORDINATE_POINT_LIST
  STROKE_DEFINITION
  UNIQUE_IDENTIFIER
)
```

*Parsed by: `Bus.from_sexpr()` in `kicad_schematic.py`*

```
(bus
  COORDINATE_POINT_LIST
  STROKE_DEFINITION
  UNIQUE_IDENTIFIER
)
```

## Image Section

```
(image
  POSITION_IDENTIFIER
  (scale SCALE_FACTOR)
  UNIQUE_IDENTIFIER
  (data "BASE64_IMAGE_DATA")
)
```

## Graphical Line Section

*Parsed by: `Polyline.from_sexpr()` in `kicad_schematic.py`*

```
(polyline
  COORDINATE_POINT_LIST
  STROKE_DEFINITION
  UNIQUE_IDENTIFIER
)
```

## Graphical Text Section

*Parsed by: `SchematicText.from_sexpr()` in `kicad_schematic.py`*

```
(text
  "TEXT"
  POSITION_IDENTIFIER
  TEXT_EFFECTS
  UNIQUE_IDENTIFIER
)
```

## Local Label Section

*Parsed by: `LocalLabel.from_sexpr()` in `kicad_schematic.py`*

```
(label
  "TEXT"
  POSITION_IDENTIFIER
  TEXT_EFFECTS
  UNIQUE_IDENTIFIER
)
```

## Global Label Section

*Parsed by: `GlobalLabel.from_sexpr()` in `kicad_schematic.py`*

```
(global_label
  "TEXT"
  (shape SHAPE) ; input|output|bidirectional|tri_state|passive
  [(fields_autoplaced)] ; optional
  POSITION_IDENTIFIER
  TEXT_EFFECTS
  UNIQUE_IDENTIFIER
  [PROPERTIES] ; optional
)
```

## Hierarchical Label Section

*Parsed by: `HierarchicalLabel.from_sexpr()` in `kicad_schematic.py`*

```
(hierarchical_label
  "TEXT"
  (shape SHAPE) ; input|output|bidirectional|tri_state|passive
  POSITION_IDENTIFIER
  TEXT_EFFECTS
  UNIQUE_IDENTIFIER
)
```

## Symbol Section

*Parsed by: `SchematicSymbol.from_sexpr()` in `kicad_schematic.py`*

```
(symbol
  "LIBRARY_IDENTIFIER"
  POSITION_IDENTIFIER
  (unit UNIT)
  [(in_bom yes|no)] ; optional
  [(on_board yes|no)] ; optional
  UNIQUE_IDENTIFIER
  [PROPERTIES] ; optional
  [(pin "PIN_NUMBER" (uuid UNIQUE_IDENTIFIER))] ; optional
  (instances
    (project "PROJECT_NAME"
      (path "PATH_INSTANCE"
        (reference "REFERENCE")
        (unit UNIT)
      )
    )
  )
)
```

## Hierarchical Sheet Section

*Parsed by: `HierarchicalSheet.from_sexpr()` in `kicad_schematic.py`*

```
(sheet
  POSITION_IDENTIFIER
  (size WIDTH HEIGHT)
  [(fields_autoplaced)] ; optional
  STROKE_DEFINITION
  FILL_DEFINITION
  UNIQUE_IDENTIFIER
  SHEET_NAME_PROPERTY
  FILE_NAME_PROPERTY
  [HIERARCHICAL_PINS] ; optional
  (instances
    (project "PROJECT_NAME"
      (path "PATH_INSTANCE"
        (page "PAGE_NUMBER")
      )
    )
  )
)
```

### Hierarchical Sheet Pin Definition

*Parsed by: `HierarchicalPin.from_sexpr()` in `kicad_schematic.py`*

```
(pin
  "NAME"
  ELECTRICAL_TYPE ; input|output|bidirectional|tri_state|passive
  POSITION_IDENTIFIER
  TEXT_EFFECTS
  UNIQUE_IDENTIFIER
)
```

## Root Sheet Instance Section

*Parsed by: `RootSheetInstance.from_sexpr()` in `kicad_schematic.py`*

```
(sheet_instances
  (path "/"
    (page "PAGE")
  )
)
