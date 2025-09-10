# S-Expression Format

## Introduction

KiCad uses an s-expression file format for symbol libraries, footprint libraries, schematics, printed circuit boards, and title block and border worksheets.

## Syntax

* Token definitions are delimited by opening `(` and closing `)` parenthesis.
* All tokens are lowercase.
* Tokens cannot contain any white space characters or special characters other than the underscore '_' character.
* All strings are quoted using the double quote character (") and are UTF-8 encoded.
* Tokens can have zero or more attributes.

## Conventions

* Token attributes are upper case descriptive names.
* Some tokens have a limited number of possible attribute values which are separated by a logical or character '|'.
* Some tokens have optional attributes which are enclosed in square braces `[optional]`.

## Coordinates and Sizes

* All values are given in millimeters.
* All coordinates are relative to the origin of their containing object.

## Common Syntax

### Position Identifier

*Parsed by: `Position.from_sexpr()` in `kicad_common.py`*

```
(at
  X
  Y
  [ANGLE]                                                     ; optional
)
```

### Coordinate Point List

*Parsed by: `CoordinatePointList.from_sexpr()` in `kicad_common.py`*
*Point parsed by: `CoordinatePoint.from_sexpr()` in `kicad_common.py`*

```
(pts
  (xy X Y)
  ...
  (xy X Y)
)
```

### Stroke Definition

*Parsed by: `Stroke.from_sexpr()` in `kicad_common.py`*

```
(stroke
  (width WIDTH)
  (type TYPE)                                                 ; dash|dash_dot|dash_dot_dot|dot|default|solid
  (color R G B A)
)
```

### Text Effects

*Parsed by: `TextEffects.from_sexpr()` in `kicad_common.py`*
*Font parsed by: `Font.from_sexpr()` in `kicad_common.py`*

```
(effects
  (font
    [(face FACE_NAME)]                                        ; optional
    (size HEIGHT WIDTH)
    [(thickness THICKNESS)]                                   ; optional
    [bold]                                                    ; optional
    [italic]                                                  ; optional
    [(line_spacing LINE_SPACING)]                             ; optional
  )
  [(justify [left | right] [top | bottom] [mirror])]          ; optional
  [hide]                                                      ; optional
)
```

### Page Settings

*Parsed by: `PageSettings.from_sexpr()` in `kicad_common.py`*

```
(paper
  PAPER_SIZE | WIDTH HEIGHT                                   ; A0|A1|A2|A3|A4|A5|A|B|C|D|E or custom WIDTH HEIGHT
  [portrait]                                                  ; optional
)
```

### Title Block

*Parsed by: `TitleBlock.from_sexpr()` in `kicad_common.py`*

```
(title_block
  (title "TITLE")
  (date "DATE")
  (rev "REVISION")
  (company "COMPANY_NAME")
  (comment N "COMMENT")
)
```

### Properties

*Parsed by: `Property.from_sexpr()` in `kicad_common.py`*

```
(property
  "KEY"
  "VALUE"
)
```

### Universally Unique Identifier

*Parsed by: `UUID.from_sexpr()` in `kicad_common.py`*

```
(uuid
  UUID
)
```

### Images

*Parsed by: `Image.from_sexpr()` in `kicad_common.py`*

```
(image
  POSITION_IDENTIFIER
  [(scale SCALAR)]                                            ; optional
  [(layer LAYER_DEFINITIONS)]                                 ; optional
  UNIQUE_IDENTIFIER
  (data IMAGE_DATA)
)
```

## Board Common Syntax

### Layers

*Parsed by: `BoardLayer.from_sexpr()` in `kicad_pcb.py`*

```
(layer
  LAYER_DEFINITION
)
```

### Canonical Layer Names

Valid layer names: F.Cu, In1.Cu-In30.Cu, B.Cu, B.Adhes, F.Adhes, B.Paste, F.Paste, B.SilkS, F.SilkS, B.Mask, F.Mask, Dwgs.User, Cmts.User, Eco1.User, Eco2.User, Edge.Cuts, F.CrtYd, B.CrtYd, F.Fab, B.Fab, User.1-User.9

### Footprint

*Parsed by: `KiCadFootprint.from_sexpr()` in `kicad_board.py`*

```
(footprint
  ["LIBRARY_LINK"]                                            ; optional
  [locked]                                                    ; optional
  [placed]                                                    ; optional
  (layer LAYER_DEFINITIONS)
  (tedit TIME_STAMP)
  [(uuid UUID)]                                               ; optional
  [POSITION_IDENTIFIER]                                       ; optional
  [(descr "DESCRIPTION")]                                     ; optional
  [(tags "NAME")]                                             ; optional
  [(property "KEY" "VALUE") ...]                              ; optional
  (path "PATH")
  [(autoplace_cost90 COST)]                                   ; optional
  [(autoplace_cost180 COST)]                                  ; optional
  [(solder_mask_margin MARGIN)]                               ; optional
  [(solder_paste_margin MARGIN)]                              ; optional
  [(solder_paste_ratio RATIO)]                                ; optional
  [(clearance CLEARANCE)]                                     ; optional
  [(zone_connect CONNECTION_TYPE)]                            ; optional
  [(thermal_width WIDTH)]                                     ; optional
  [(thermal_gap DISTANCE)]                                    ; optional
  [ATTRIBUTES]                                                ; optional
  [(private_layers LAYER_DEFINITIONS)]                        ; optional
  [(net_tie_pad_groups PAD_GROUP_DEFINITIONS)]                ; optional
  GRAPHIC_ITEMS...
  PADS...
  ZONES...
  GROUPS...
  3D_MODEL
)
```

#### Footprint Attributes

*Parsed within FootprintAttributes in `kicad_board.py`*

```
(attr
  TYPE                                                        ; smd|through_hole
  [board_only]                                                ; optional
  [exclude_from_pos_files]                                    ; optional
  [exclude_from_bom]                                          ; optional
)
```

#### Footprint Text

*Parsed by: `FootprintText.from_sexpr()` in `kicad_board.py`*

```
(fp_text
  TYPE                                                        ; reference|value|user
  "TEXT"
  POSITION_IDENTIFIER
  [unlocked]                                                  ; optional
  (layer LAYER_DEFINITION)
  [hide]                                                      ; optional
  (effects TEXT_EFFECTS)
  (uuid UUID)
)
```

#### Footprint Text Box

*Parsed by: `FootprintTextBox.from_sexpr()` in `kicad_board.py`*

```
(fp_text_box
  [locked]                                                    ; optional
  "TEXT"
  [(start X Y)]                                               ; optional
  [(end X Y)]                                                 ; optional
  [(pts (xy X Y) (xy X Y) (xy X Y) (xy X Y))]                 ; optional
  [(angle ROTATION)]                                          ; optional
  (layer LAYER_DEFINITION)
  (uuid UUID)
  TEXT_EFFECTS
  [STROKE_DEFINITION]                                         ; optional
  [(render_cache RENDER_CACHE)]                               ; optional
)
```

#### Footprint Line

*Parsed by: `FootprintLine.from_sexpr()` in `kicad_board.py`*

```
(fp_line
  (start X Y)
  (end X Y)
  (layer LAYER_DEFINITION)
  [(width WIDTH)]                                             ; optional (prior to version 7)
  [STROKE_DEFINITION]                                         ; optional (from version 7)
  [(locked)]                                                  ; optional
  (uuid UUID)
)
```

#### Footprint Rectangle

*Parsed by: `FootprintRectangle.from_sexpr()` in `kicad_board.py`*

```
(fp_rect
  (start X Y)
  (end X Y)
  (layer LAYER_DEFINITION)
  [(width WIDTH)]                                             ; optional (prior to version 7)
  [STROKE_DEFINITION]                                         ; optional (from version 7)
  [(fill yes | no)]                                           ; optional
  [(locked)]                                                  ; optional
  (uuid UUID)
)
```

#### Footprint Circle

*Parsed by: `FootprintCircle.from_sexpr()` in `kicad_board.py`*

```
(fp_circle
  (center X Y)
  (end X Y)
  (layer LAYER_DEFINITION)
  [(width WIDTH)]                                             ; optional (prior to version 7)
  [STROKE_DEFINITION]                                         ; optional (from version 7)
  [(fill yes | no)]                                           ; optional
  [(locked)]                                                  ; optional
  (uuid UUID)
)
```

#### Footprint Arc

*Parsed by: `FootprintArc.from_sexpr()` in `kicad_board.py`*

```
(fp_arc
  (start X Y)
  (mid X Y)
  (end X Y)
  (layer LAYER_DEFINITION)
  [(width WIDTH)]                                             ; optional (prior to version 7)
  [STROKE_DEFINITION]                                         ; optional (from version 7)
  [(locked)]                                                  ; optional
  (uuid UUID)
)
```

#### Footprint Polygon

*Parsed by: `FootprintPolygon.from_sexpr()` in `kicad_board.py`*

```
(fp_poly
  COORDINATE_POINT_LIST
  (layer LAYER_DEFINITION)
  [(width WIDTH)]                                             ; optional (prior to version 7)
  [STROKE_DEFINITION]                                         ; optional (from version 7)
  [(fill yes | no)]                                           ; optional
  [(locked)]                                                  ; optional
  (uuid UUID)
)
```

#### Footprint Curve

*Parsed by: `FootprintCurve.from_sexpr()` in `kicad_board.py`*

```
(fp_curve
  COORDINATE_POINT_LIST
  (layer LAYER_DEFINITION)
  [(width WIDTH)]                                             ; optional (prior to version 7)
  [STROKE_DEFINITION]                                         ; optional (from version 7)
  [(locked)]                                                  ; optional
  (uuid UUID)
)
```

### Footprint Pad

*Parsed by: `FootprintPad.from_sexpr()` in `kicad_board.py`*

```
(pad
  "NUMBER"
  TYPE                                                        ; thru_hole|smd|connect|np_thru_hole
  SHAPE                                                       ; circle|rect|oval|trapezoid|roundrect|custom
  POSITION_IDENTIFIER
  [(locked)]                                                  ; optional
  (size X Y)
  [(drill DRILL_DEFINITION)]                                  ; optional
  (layers "CANONICAL_LAYER_LIST")
  [(property PROPERTY)]                                       ; optional
  [(remove_unused_layer)]                                     ; optional
  [(keep_end_layers)]                                         ; optional
  [(roundrect_rratio RATIO)]                                  ; optional
  [(chamfer_ratio RATIO)]                                     ; optional
  [(chamfer CORNER_LIST)]                                     ; optional
  (net NUMBER "NAME")
  (uuid UUID)
  [(pinfunction "PIN_FUNCTION")]                              ; optional
  [(pintype "PIN_TYPE")]                                      ; optional
  [(die_length LENGTH)]                                       ; optional
  [(solder_mask_margin MARGIN)]                               ; optional
  [(solder_paste_margin MARGIN)]                              ; optional
  [(solder_paste_margin_ratio RATIO)]                         ; optional
  [(clearance CLEARANCE)]                                     ; optional
  [(zone_connect ZONE)]                                       ; optional
  [(thermal_width WIDTH)]                                     ; optional
  [(thermal_gap DISTANCE)]                                    ; optional
  [CUSTOM_PAD_OPTIONS]                                        ; optional
  [CUSTOM_PAD_PRIMITIVES]                                     ; optional
)
```

#### Pad Drill Definition

*Parsed within FootprintPad as `DrillDefinition` in `kicad_board.py`*

```
(drill
  [oval]                                                      ; optional
  DIAMETER
  [WIDTH]                                                     ; optional
  [(offset X Y)]                                              ; optional
)
```

#### Custom Pad Options

*Parsed within CustomPadOptions in `kicad_board.py`*

```
(options
  (clearance CLEARANCE_TYPE)                                  ; outline|convexhull
  (anchor PAD_SHAPE)                                          ; rect|circle
)
```

#### Custom Pad Primitives

*Parsed within CustomPadPrimitives in `kicad_board.py`*

```
(primitives
  GRAPHIC_ITEMS...
  (width WIDTH)
  [(fill yes)]                                                ; optional
)
```

### Footprint 3D Model

*Parsed within KiCadFootprint as `Footprint3DModel` in `kicad_board.py`*

```
(model
  "3D_MODEL_FILE"
  (at (xyz X Y Z))
  (scale (xyz X Y Z))
  (rotate (xyz X Y Z))
  [hide]                                                      ; optional
  [(opacity OPACITY)]                                         ; optional: 0.0-1.0
  [(offset (xyz X Y Z))]                                      ; optional
)
```

## Graphic Items

### Graphical Text

*Parsed by: `GraphicalText.from_sexpr()` in `kicad_graphics.py`*

```
(gr_text
  "TEXT"
  POSITION_INDENTIFIER
  (layer LAYER_DEFINITION [knockout])
  (uuid UUID)
  (effects TEXT_EFFECTS)
)
```

### Graphical Text Box

*Parsed by: `GraphicalTextBox.from_sexpr()` in `kicad_graphics.py`*

```
(gr_text_box
  [locked]                                                    ; optional
  "TEXT"
  [(start X Y)]                                               ; optional
  [(end X Y)]                                                 ; optional
  [(pts (xy X Y) (xy X Y) (xy X Y) (xy X Y))]                 ; optional
  [(angle ROTATION)]                                          ; optional
  (layer LAYER_DEFINITION)
  (uuid UUID)
  TEXT_EFFECTS
  [STROKE_DEFINITION]                                         ; optional
  [(render_cache RENDER_CACHE)]                               ; optional
)
```

### Graphical Line

*Parsed by: `GraphicalLine.from_sexpr()` in `kicad_graphics.py`*

```
(gr_line
  (start X Y)
  (end X Y)
  [(angle ANGLE)]                                             ; optional
  (layer LAYER_DEFINITION)
  (width WIDTH)
  (uuid UUID)
)
```

### Graphical Rectangle

*Parsed by: `GraphicalRectangle.from_sexpr()` in `kicad_graphics.py`*

```
(gr_rect
  (start X Y)
  (end X Y)
  (layer LAYER_DEFINITION)
  (width WIDTH)
  [(fill yes | no)]                                           ; optional
  (uuid UUID)
)
```

### Graphical Circle

*Parsed by: `GraphicalCircle.from_sexpr()` in `kicad_graphics.py`*

```
(gr_circle
  (center X Y)
  (end X Y)
  (layer LAYER_DEFINITION)
  (width WIDTH)
  [(fill yes | no)]                                           ; optional
  (uuid UUID)
)
```

### Graphical Arc

*Parsed by: `GraphicalArc.from_sexpr()` in `kicad_graphics.py`*

```
(gr_arc
  (start X Y)
  (mid X Y)
  (end X Y)
  (layer LAYER_DEFINITION)
  (width WIDTH)
  (uuid UUID)
)
```

### Graphical Polygon

*Parsed by: `GraphicalPolygon.from_sexpr()` in `kicad_graphics.py`*

```
(gr_poly
  COORDINATE_POINT_LIST
  (layer LAYER_DEFINITION)
  (width WIDTH)
  [(fill yes | no)]                                           ; optional
  (uuid UUID)
)
```

### Graphical Curve

*Parsed by: `GraphicalBezier.from_sexpr()` in `kicad_graphics.py`*

```
(bezier
  COORDINATE_POINT_LIST
  (layer LAYER_DEFINITION)
  (width WIDTH)
  (uuid UUID)
)
```

### Annotation Bounding Box

*Parsed by: `GraphicalBoundingBox.from_sexpr()` in `kicad_graphics.py`*

```
(gr_bbox
  (start X Y)
  (end X Y)
)
```

### Dimension

*Parsed by: `Dimension.from_sexpr()` in `kicad_graphics.py`*

```
(dimension
  [locked]                                                    ; optional
  (type DIMENSION_TYPE)                                       ; aligned|leader|center|orthogonal|radial
  (layer LAYER_DEFINITION)
  (uuid UUID)
  (pts (xy X Y) (xy X Y))
  [(height HEIGHT)]                                           ; optional
  [(orientation ORIENTATION)]                                 ; optional
  [(leader_length LEADER_LENGTH)]                             ; optional
  [(gr_text GRAPHICAL_TEXT)]                                  ; optional
  [(format DIMENSION_FORMAT)]                                 ; optional
  (style DIMENSION_STYLE)
)
```

#### Dimension Format

*Parsed within Dimension as `DimensionFormat` in `kicad_graphics.py`*

```
(format
  [(prefix "PREFIX")]                                         ; optional
  [(suffix "SUFFIX")]                                         ; optional
  (units UNITS)                                               ; 0=Inches|1=Mils|2=Millimeters|3=Automatic
  (units_format UNITS_FORMAT)                                 ; 0=No suffix|1=Bare suffix|2=Wrap suffix
  (precision PRECISION)
  [(override_value "VALUE")]                                  ; optional
  [(suppress_zeros yes | no)]                                 ; optional
)
```

#### Dimension Style

*Parsed within Dimension as `DimensionStyle` in `kicad_graphics.py`*

```
(style
  (thickness THICKNESS)
  (arrow_length LENGTH)
  (text_position_mode MODE)                                   ; 0=Outside|1=Inline|2=Manual
  [(arrow_direction DIRECTION)]                               ; optional: outward|inward
  [(extension_height HEIGHT)]                                 ; optional
  [(text_frame TEXT_FRAME_TYPE)]                              ; optional: 0=None|1=Rectangle|2=Circle|3=Rounded
  [(extension_offset OFFSET)]                                 ; optional
  [(keep_text_aligned yes | no)]                              ; optional
)
```

## Zone

*Parsed by: `Zone.from_sexpr()` in `kicad_pcb.py`*

```
(zone
  (net NET_NUMBER)
  (net_name "NET_NAME")
  (layer LAYER_DEFINITION)
  (uuid UUID)
  [(name "NAME")]                                             ; optional
  (hatch STYLE PITCH)                                         ; none|edge|full
  [(priority PRIORITY)]                                       ; optional
  (connect_pads [CONNECTION_TYPE] (clearance CLEARANCE))      ; thru_hole_only|full|no
  (min_thickness THICKNESS)
  [(filled_areas_thickness no)]                               ; optional
  [ZONE_KEEPOUT_SETTINGS]                                     ; optional
  ZONE_FILL_SETTINGS
  (polygon COORDINATE_POINT_LIST)
  [ZONE_FILL_POLYGONS...]                                     ; optional
  [ZONE_FILL_SEGMENTS...]                                     ; optional
)
```

### Zone Keep Out Settings

*Parsed by: `KeepoutSettings.from_sexpr()` in `kicad_board.py`*

```
(keepout
  (tracks KEEPOUT)                                            ; allowed|not_allowed
  (vias KEEPOUT)                                              ; allowed|not_allowed
  (pads KEEPOUT)                                              ; allowed|not_allowed
  (copperpour KEEPOUT)                                        ; allowed|not_allowed
  (footprints KEEPOUT)                                        ; allowed|not_allowed
)
```

### Zone Fill Settings

*Parsed by: `ZoneFillSettings.from_sexpr()` in `kicad_pcb.py` (zone context) or `Fill.from_sexpr()` in `kicad_common.py` (graphics context)*

```
(fill
  [yes]                                                       ; optional
  [(mode FILL_MODE)]                                          ; optional: hatched
  (thermal_gap GAP)
  (thermal_bridge_width WIDTH)
  [(smoothing STYLE)]                                         ; optional: chamfer|fillet
  [(radius RADIUS)]                                           ; optional
  [(island_removal_mode MODE)]                                ; optional: 0=Always|1=Never|2=Minimum area
  [(island_area_min AREA)]                                    ; optional
  [(hatch_thickness THICKNESS)]                               ; optional
  [(hatch_gap GAP)]                                           ; optional
  [(hatch_orientation ORIENTATION)]                           ; optional
  [(hatch_smoothing_level LEVEL)]                             ; optional: 0=None|1=Fillet|2=Arc min|3=Arc max
  [(hatch_smoothing_value VALUE)]                             ; optional
  [(hatch_border_algorithm TYPE)]                             ; optional: 0=Zone min thickness|1=Hatch thickness
  [(hatch_min_hole_area AREA)]                                ; optional
)
```

### Zone Fill Polygons

*Parsed within Zone in `kicad_pcb.py`*

```
(filled_polygon
  (layer LAYER_DEFINITION)
  COORDINATE_POINT_LIST
)
```

### Zone Fill Segments

*Parsed within Zone in `kicad_pcb.py`*

```
(fill_segments
  (layer LAYER_DEFINITION)
  COORDINATED_POINT_LIST
)
```

## Group

*Parsed by: `Group.from_sexpr()` in `kicad_pcb.py`*

```
(group
  "NAME"
  (id UUID)
  (members UUID1 ... UUIDN)
)
```

## Schematic and Symbol Library Common Syntax

### Fill Definition

*Parsed by: `Fill.from_sexpr()` in `kicad_common.py`*

```
(fill
  (type none | outline | background)
)
```

### Symbols

*Parsed by: `KiCadSymbol.from_sexpr()` or `SymbolUnit.from_sexpr()` in `kicad_symbol.py`*

```
(symbol
  "LIBRARY_ID" | "UNIT_ID"
  [(extends "LIBRARY_ID")]                                    ; optional
  [(pin_numbers hide)]                                        ; optional
  [(pin_names [(offset OFFSET)] hide)]                        ; optional
  (in_bom yes | no)
  (on_board yes | no)
  SYMBOL_PROPERTIES...
  GRAPHIC_ITEMS...
  PINS...
  UNITS...
  [(unit_name "UNIT_NAME")]                                   ; optional
)
```

#### Symbol Properties

```
(property
  "KEY"
  "VALUE"
  (id N)
  POSITION_IDENTIFIER
  TEXT_EFFECTS
)
```

### Symbol Graphic Items

#### Symbol Arc

*Parsed by: `SymbolArc.from_sexpr()` in `kicad_symbol.py`*

```
(arc
  (start X Y)
  (mid X Y)
  (end X Y)
  STROKE_DEFINITION
  FILL_DEFINITION
)
```

#### Symbol Circle

*Parsed by: `SymbolCircle.from_sexpr()` in `kicad_symbol.py`*

```
(circle
  (center X Y)
  (radius RADIUS)
  STROKE_DEFINITION
  FILL_DEFINITION
)
```

#### Symbol Curve

*Parsed by: `SymbolBezier.from_sexpr()` in `kicad_symbol.py`*

```
(bezier
  COORDINATE_POINT_LIST
  STROKE_DEFINITION
  FILL_DEFINITION
)
```

#### Symbol Line

*Parsed by: `SymbolPolyline.from_sexpr()` in `kicad_symbol.py`*

```
(polyline
  COORDINATE_POINT_LIST
  STROKE_DEFINITION
  FILL_DEFINITION
)
```

#### Symbol Rectangle

*Parsed by: `SymbolRectangle.from_sexpr()` in `kicad_symbol.py`*

```
(rectangle
  (start X Y)
  (end X Y)
  STROKE_DEFINITION
  FILL_DEFINITION
)
```

#### Symbol Text

*Parsed by: `SymbolText.from_sexpr()` in `kicad_symbol.py`*

```
(text
  "TEXT"
  POSITION_IDENTIFIER
  (effects TEXT_EFFECTS)
)
```

#### Symbol Pin

*Parsed by: `SymbolPin.from_sexpr()` in `kicad_symbol.py`*

```
(pin
  PIN_ELECTRICAL_TYPE                                         ; input|output|bidirectional|tri_state|passive|free|unspecified|power_in|power_out|open_collector|open_emitter|no_connect
  PIN_GRAPHIC_STYLE                                           ; line|inverted|clock|inverted_clock|input_low|clock_low|output_low|edge_clock_high|non_logic
  POSITION_IDENTIFIER
  (length LENGTH)
  (name "NAME" TEXT_EFFECTS)
  (number "NUMBER" TEXT_EFFECTS)
)
```
