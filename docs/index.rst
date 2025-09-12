KiCad Parser Documentation
===========================

A comprehensive Python library for parsing and manipulating KiCad S-Expression files.

KiCad Parser provides a complete toolkit for working with KiCad files, including symbols,
footprints, schematics, PCB layouts, worksheets, and design rules. All parsing is done
with high fidelity, preserving the structure and data integrity of your KiCad projects.

Key Features
------------

* **Complete KiCad Support**: Parse and manipulate all major KiCad file formats
* **High Fidelity**: Preserves all data with 100% structural accuracy
* **Zero Dependencies**: Self-contained library with no external dependencies
* **Type Safety**: Full type annotations for better development experience
* **Extensive Testing**: Comprehensive test suite with round-trip validation

Quick Start
-----------

.. code-block:: python

    from kicad_parser import load_kicad_file, save_kicad_file
    
    # Load any KiCad file
    kicad_object = load_kicad_file("path/to/file.kicad_sym")
    
    # Manipulate the object (example: change symbol name)
    if hasattr(kicad_object, 'symbols'):
        for symbol in kicad_object.symbols:
            symbol.name = f"Modified_{symbol.name}"
    
    # Save back to file
    save_kicad_file(kicad_object, "path/to/modified_file.kicad_sym")

Installation
------------

.. code-block:: bash

    pip install kicad-parser

API Reference
=============

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   modules/kicad_parser
   modules/file_formats
   modules/examples

Core Modules
------------

.. autosummary::
   :toctree: _autosummary
   :template: custom-module-template.rst

   kicad_parser.kicad_file
   kicad_parser.kicad_common
   kicad_parser.kicad_symbol
   kicad_parser.kicad_board
   kicad_parser.kicad_pcb
   kicad_parser.kicad_schematic
   kicad_parser.kicad_worksheet
   kicad_parser.kicad_graphics
   kicad_parser.kicad_design_rules

File Format Support
-------------------

The library supports all major KiCad file formats:

* **Symbol Libraries** (``.kicad_sym``) - Electronic component symbols
* **Footprints** (``.kicad_mod``) - PCB component footprints  
* **Schematics** (``.kicad_sch``) - Circuit schematics
* **PCB Layouts** (``.kicad_pcb``) - Printed circuit board designs
* **Worksheets** (``.kicad_wks``) - Drawing frame templates
* **Design Rules** (``.kicad_dru``) - PCB design rule constraints

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`