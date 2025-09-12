Supported File Formats
======================

KiCad Parser supports all major KiCad file formats with complete parsing fidelity.

Symbol Libraries (.kicad_sym)
------------------------------

Symbol library files contain electronic component symbols used in schematics.

.. autoclass:: kicad_parser.KiCadSymbolLibrary
   :members:
   :show-inheritance:
   :noindex:

.. autoclass:: kicad_parser.KiCadSymbol
   :members:
   :show-inheritance:
   :noindex:

Key Classes:

* ``SymbolProperty`` - Symbol properties (Reference, Value, etc.)
* ``SymbolPin`` - Component pins with electrical and graphical information
* ``SymbolGraphics`` - Graphical elements (lines, circles, rectangles, etc.)

Footprints (.kicad_mod)
-----------------------

Footprint files define the physical PCB layout for components.

.. autoclass:: kicad_parser.KiCadFootprint
   :members:
   :show-inheritance:
   :noindex:

Key Classes:

* ``FootprintPad`` - Component pads with shape, size, and layer information
* ``FootprintText`` - Reference and value text
* ``FootprintGraphics`` - Silkscreen and mechanical drawings

Schematics (.kicad_sch)
-----------------------

Schematic files contain circuit diagrams and connectivity information.

.. autoclass:: kicad_parser.KiCadSchematic
   :members:
   :show-inheritance:
   :noindex:

Key Classes:

* ``SchematicSymbol`` - Symbol instances with properties
* ``Wire`` - Electrical connections between components
* ``Junction`` - Wire junction points
* ``Labels`` - Net labels and hierarchical labels

PCB Layouts (.kicad_pcb)
------------------------

PCB files define the complete printed circuit board layout.

.. autoclass:: kicad_parser.KiCadPCB
   :members:
   :show-inheritance:
   :noindex:

Key Classes:

* ``TrackSegment`` - Copper track segments
* ``TrackVia`` - Via connections between layers
* ``Zone`` - Copper pour areas
* ``BoardLayer`` - Layer definitions

Worksheets (.kicad_wks)
-----------------------

Worksheet files define drawing frame templates for documentation.

.. autoclass:: kicad_parser.KiCadWorksheet
   :members:
   :show-inheritance:
   :noindex:

Design Rules (.kicad_dru)
-------------------------

Design rule files contain PCB manufacturing constraints and validation rules.

.. autoclass:: kicad_parser.KiCadDesignRules
   :members:
   :show-inheritance:
   :noindex: