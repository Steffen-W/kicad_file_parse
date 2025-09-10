# Work Sheet File Format

KiCad s-expression work sheet file format reference.

## File Structure

*Parsed by: `KiCadWorksheet.from_sexpr()` in `kicad_worksheet.py`*

```
(kicad_wks
  (version VERSION) ; Parsed within root parser (no specific class)
  (generator GENERATOR) ; Parsed within root parser (no specific class)
  
  ;; File sections:
  ;; - setup section [optional]
  ;; - drawing objects [optional]
)
```

## Setup Section

*Parsed by: `WorksheetSetup.from_sexpr()` in `kicad_worksheet.py`*

```
(setup
  (textsize WIDTH HEIGHT) ; optional
  (linewidth WIDTH) ; optional
  (textlinewidth WIDTH) ; optional
  (left_margin DISTANCE) ; optional
  (right_margin DISTANCE) ; optional
  (top_margin DISTANCE) ; optional
  (bottom_margin DISTANCE) ; optional
)
```

## Drawing Objects

### Title Block Text

*Parsed by: `WorksheetText.from_sexpr()` in `kicad_worksheet.py`*

```
(tbtext
  "TEXT"
  [(name "NAME")]                                             ; optional
  (pos X Y [CORNER])                                         ; CORNER: ltcorner|lbcorner|rbcorner|rtcorner
  [(at X Y [ANGLE])]                                         ; optional - alternative position format
  [(font (size WIDTH HEIGHT) [bold] [italic])]              ; optional
  [(repeat COUNT)]                                           ; optional
  [(incrx DISTANCE)]                                         ; optional
  [(incry DISTANCE)]                                         ; optional
  [(comment "COMMENT")]                                      ; optional
  [(maxlen LENGTH)]                                          ; optional
  [(maxheight HEIGHT)]                                       ; optional
)
```

### Graphical Line

*Parsed by: `WorksheetLine.from_sexpr()` in `kicad_worksheet.py`*

```
(line
  (name "NAME")
  (start X Y [CORNER]) ; CORNER: ltcorner|lbcorner|rbcorner|rtcorner ; Parsed by: Position.from_sexpr() in kicad_common.py
  (end X Y [CORNER]) ; CORNER: ltcorner|lbcorner|rbcorner|rtcorner ; Parsed by: Position.from_sexpr() in kicad_common.py
  (repeat COUNT) ; optional
  (incrx DISTANCE) ; optional
  (incry DISTANCE) ; optional
  (comment "COMMENT") ; optional
)
```

### Graphical Rectangle

*Parsed by: `WorksheetRectangle.from_sexpr()` in `kicad_worksheet.py`*

```
(rect
  (name "NAME")
  (start X Y [CORNER]) ; CORNER: ltcorner|lbcorner|rbcorner|rtcorner ; Parsed by: Position.from_sexpr() in kicad_common.py
  (end X Y [CORNER]) ; CORNER: ltcorner|lbcorner|rbcorner|rtcorner ; Parsed by: Position.from_sexpr() in kicad_common.py
  (repeat COUNT) ; optional
  (incrx DISTANCE) ; optional
  (incry DISTANCE) ; optional
  (comment "COMMENT") ; optional
)
```

### Graphical Polygon

*Parsed by: `WorksheetPolygon.from_sexpr()` in `kicad_worksheet.py`*

```
(polygon
  (name "NAME")
  (pos X Y [CORNER]) ; CORNER: ltcorner|lbcorner|rbcorner|rtcorner ; Parsed by: Position.from_sexpr() in kicad_common.py
  (rotate ANGLE) ; optional
  (linewidth WIDTH) ; optional
  (pts (xy X Y) (xy X Y) ...) ; coordinate point list ; Parsed by: CoordinatePointList.from_sexpr() in kicad_common.py (xy parsed by CoordinatePoint.from_sexpr())
  (repeat COUNT) ; optional
  (incrx DISTANCE) ; optional
  (incry DISTANCE) ; optional
  (comment "COMMENT") ; optional
)
```

### Image

*Parsed by: `WorksheetBitmap.from_sexpr()` in `kicad_worksheet.py`*

```
(bitmap
  (name "NAME")
  (pos X Y [CORNER]) ; CORNER: ltcorner|lbcorner|rbcorner|rtcorner ; Parsed by: Position.from_sexpr() in kicad_common.py
  (scale SCALAR)
  (repeat COUNT) ; optional
  (incrx DISTANCE) ; optional
  (incry DISTANCE) ; optional
  (comment "COMMENT") ; optional
  (pngdata
    (data HEX_DATA) ; maximum 32 bytes per data token
    ; additional data tokens as needed
  )
)
```
