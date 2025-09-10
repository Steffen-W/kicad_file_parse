# KiCad Board File Format (.kicad_pcb)

S-expression format definitions for KiCad PCB files.

## File Structure

*Parsed by: `KiCadPCB.from_sexpr()` in `kicad_pcb.py`*

```
(kicad_pcb
  (version VERSION) ; Parsed within root parser (no specific class)
  (generator GENERATOR) ; Parsed within root parser (no specific class)
  
  (general ; Parsed by: GeneralSettings.from_sexpr() in kicad_pcb.py
    (thickness THICKNESS)
  )
  
  (page PAGE_SIZE) ; optional - Parsed by: PageSettings.from_sexpr() in kicad_common.py
  
  (layers ; Parsed in KiCadPCB.from_sexpr() in kicad_pcb.py
    (LAYER_DEFINITIONS...)
  )
  
  (setup ; Parsed by: BoardSetup.from_sexpr() in kicad_pcb.py
    (SETUP_PARAMETERS...)
  )
  
  (property ...) ; optional - Parsed by: Property.from_sexpr() in kicad_common.py
  
  (net ...) ; multiple net definitions - Parsed by: BoardNet.from_sexpr() in kicad_pcb.py
  
  (footprint ...) ; optional - Parsed by: KiCadFootprint.from_sexpr() in kicad_board.py
  (gr_text ...) ; optional - Parsed by: GraphicalText.from_sexpr() in kicad_graphics.py
  (gr_line ...) ; optional - Parsed by: GraphicalLine.from_sexpr() in kicad_graphics.py
  (image ...) ; optional - see image definitions
  
  (segment ...) ; optional - Parsed by: TrackSegment.from_sexpr() in kicad_pcb.py
  (via ...) ; optional - Parsed by: TrackVia.from_sexpr() in kicad_pcb.py
  (arc ...) ; optional - Parsed by: TrackArc.from_sexpr() in kicad_pcb.py
  
  (zone ...) ; optional - Parsed by: Zone.from_sexpr() in kicad_pcb.py
  (group ...) ; optional - Parsed by: Group.from_sexpr() in kicad_pcb.py
)
```

## Header Section

*Parsed by: `KiCadPCB.from_sexpr()` in `kicad_pcb.py`*

```
(kicad_pcb
  (version VERSION) ; Parsed within root parser (no specific class)
  (generator GENERATOR) ; Parsed within root parser (no specific class)
)
```

## General Section

*Parsed by: `GeneralSettings.from_sexpr()` in `kicad_pcb.py`*

```
(general
  (thickness THICKNESS)
)
```

## Layers Section

*Parsed in: `KiCadPCB.from_sexpr()` in `kicad_pcb.py`*

```
(layers
  (ORDINAL "CANONICAL_NAME" TYPE [USER_NAME]) ; optional - Parsed by: BoardLayer.from_sexpr() in kicad_pcb.py
)
```

- TYPE: jumper|mixed|power|signal|user

## Setup Section

*Parsed by: `BoardSetup.from_sexpr()` in `kicad_pcb.py`*

```
(setup
  (stackup ...) ; [optional] - Parsed within BoardSetup in kicad_pcb.py
  (pad_to_mask_clearance CLEARANCE)
  (solder_mask_min_width MINIMUM_WIDTH) ; [optional]
  (pad_to_paste_clearance CLEARANCE) ; [optional] 
  (pad_to_paste_clearance_ratio RATIO) ; [optional]
  (aux_axis_origin X Y) ; [optional]
  (grid_origin X Y) ; [optional]
  (pcbplotparams ...) ; Parsed within BoardSetup in kicad_pcb.py
)
```

### Stack Up Settings

*Parsed within: `BoardSetup` in `kicad_pcb.py`*

```
(stackup
  (layer ...) ; Parsed within BoardStackup in kicad_pcb.py
  (copper_finish "FINISH") ; [optional]
  (dielectric_constraints yes|no) ; [optional]
  (edge_connector yes|bevelled) ; [optional]
  (castellated_pads yes) ; [optional]
  (edge_plating yes) ; [optional]
)
```

### Stack Up Layer Settings

*Parsed within: `BoardStackup` in `kicad_pcb.py`*

```
(layer
  "NAME"|dielectric
  NUMBER
  (type "DESCRIPTION")
  (color "COLOR") ; [optional]
  (thickness THICKNESS) ; [optional]
  (material "MATERIAL") ; [optional]
  (epsilon_r DIELECTRIC_RESISTANCE) ; [optional]
  (loss_tangent LOSS_TANGENT) ; [optional]
)
```

### Plot Settings

*Parsed within: `BoardSetup` in `kicad_pcb.py`*

```
(pcbplotparams
  (layerselection HEXADECIMAL_BIT_SET)
  (disableapertmacros true|false)
  (usegerberextensions true|false)
  (usegerberattributes true|false)
  (usegerberadvancedattributes true|false)
  (creategerberjobfile true|false)
  (svguseinch true|false)
  (svgprecision PRECISION)
  (excludeedgelayer true|false)
  (plotframeref true|false)
  (viasonmask true|false)
  (mode MODE) ; 1=normal, 2=outline
  (useauxorigin true|false)
  (hpglpennumber NUMBER)
  (hpglpenspeed SPEED)
  (hpglpendiameter DIAMETER)
  (dxfpolygonmode true|false)
  (dxfimperialunits true|false)
  (dxfusepcbnewfont true|false)
  (psnegative true|false)
  (psa4output true|false)
  (plotreference true|false)
  (plotvalue true|false)
  (plotinvisibletext true|false)
  (sketchpadsonfab true|false)
  (subtractmaskfromsilk true|false)
  (outputformat FORMAT) ; 0=gerber, 1=PostScript, 2=SVG, 3=DXF, 4=HPGL, 5=PDF
  (mirror true|false)
  (drillshape SHAPE)
  (scaleselection 1)
  (outputdirectory "PATH")
)
```

## Nets Section

*Parsed by: `BoardNet.from_sexpr()` in `kicad_pcb.py`*

```
(net ORDINAL "NET_NAME")
```

## Tracks Section

### Track Segment

*Parsed by: `TrackSegment.from_sexpr()` in `kicad_pcb.py`*

```
(segment
  (start X Y)
  (end X Y)
  (width WIDTH)
  (layer LAYER_NAME)
  (locked) ; [optional]
  (net NET_NUMBER)
  (tstamp UUID)
)
```

### Track Via

*Parsed by: `TrackVia.from_sexpr()` in `kicad_pcb.py`*

```
(via
  (blind|micro) ; [optional] - via type
  (locked) ; [optional]
  (at X Y)
  (size DIAMETER)
  (drill DIAMETER)
  (layers LAYER1 LAYER2)
  (remove_unused_layers) ; [optional]
  (keep_end_layers) ; [optional]
  (free) ; [optional]
  (net NET_NUMBER)
  (tstamp UUID)
)
```

### Track Arc

*Parsed by: `TrackArc.from_sexpr()` in `kicad_pcb.py`*

```
(arc
  (start X Y)
  (mid X Y)
  (end X Y)
  (width WIDTH)
  (layer LAYER_NAME)
  (locked) ; [optional]
  (net NET_NUMBER)
  (tstamp UUID)
)
```
