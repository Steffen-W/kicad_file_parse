# KiCad Design Rules Format

## Introduction

KiCad's custom design rule system uses s-expression format for storing design rules in `.kicad_dru` files.

## File Structure

*Parsed by: `KiCadDesignRules.from_sexpr()` in `kicad_design_rules.py`*

```
(version VERSION)                                               ; Parsed within root parser (no specific class)
RULES...
```

## Version Header

```
(version 1)
```

## Rule Definition

*Parsed by: `DesignRule.from_sexpr()` in `kicad_design_rules.py`*

```
(rule NAME
  [(severity SEVERITY)]                                         ; optional: error|warning|ignore
  [(layer LAYER_NAME)]                                          ; optional
  [(condition EXPRESSION)]                                      ; optional
  (constraint CONSTRAINT_TYPE [CONSTRAINT_ARGUMENTS])          ; Parsed by: DesignRuleConstraint.from_sexpr() in kicad_design_rules.py
)
```

## Layer Clause

```
(layer LAYER_NAME | outer | inner)                            ; optional
```

## Condition Clause

```
(condition "EXPRESSION")                                       ; optional
```

## Constraint Types

*All parsed by: `DesignRuleConstraint.from_sexpr()` in `kicad_design_rules.py`*

### Clearance Constraints

```
(constraint clearance (min VALUE))
(constraint hole_clearance (min VALUE))
(constraint edge_clearance (min VALUE))
(constraint silk_clearance (min VALUE))
```

### Size Constraints

```
(constraint track_width (min VALUE) [(max VALUE)])             ; optional
(constraint via_diameter (min VALUE) [(max VALUE)])            ; optional
(constraint hole_size (min VALUE) [(max VALUE)])               ; optional
(constraint courtyard_clearance (min VALUE))
```

### Thermal Constraints

```
(constraint thermal_relief_gap (min VALUE))
(constraint thermal_spoke_width (min VALUE))
```

### Disallow Constraints

```
(constraint disallow track)
(constraint disallow via)
(constraint disallow micro_via)
(constraint disallow buried_via)
(constraint disallow pad)
(constraint disallow zone)
(constraint disallow text)
(constraint disallow graphic)
(constraint disallow hole)
(constraint disallow footprint)
```

### Length Constraints

```
(constraint length (min VALUE) [(max VALUE)])                  ; optional
(constraint skew (max VALUE))
```

### Differential Pair Constraints

```
(constraint diff_pair_gap (min VALUE) [(max VALUE)])           ; optional
(constraint diff_pair_uncoupled (max VALUE))
```

### Via Constraints

```
(constraint via_diameter (min VALUE) [(max VALUE)])            ; optional
(constraint via_drill (min VALUE) [(max VALUE)])               ; optional
(constraint blind_via_ratio (max VALUE))                       ; optional
(constraint micro_via_diameter (min VALUE) [(max VALUE)])      ; optional
(constraint micro_via_drill (min VALUE) [(max VALUE)])         ; optional
```

### Advanced Clearance Constraints

```
(constraint hole_to_hole (min VALUE))
(constraint text_height (min VALUE) [(max VALUE)])             ; optional
(constraint text_thickness (min VALUE) [(max VALUE)])          ; optional
(constraint annular_width (min VALUE))
```

## Severity Levels

```
(severity error | warning | ignore)                           ; optional
```

## Text Variables

```
(constraint clearance (min ${VARIABLE_NAME}))
```

## Advanced Features

### Rule Priority

```
(rule NAME
  (priority PRIORITY_NUMBER)                                    ; optional: higher numbers = higher priority
  (constraint ...)
)
```

### Layer Matching

```
(layer outer)                                                  ; F.Cu and B.Cu
(layer inner)                                                  ; All inner copper layers  
(layer "*.Cu")                                                ; All copper layers
```
