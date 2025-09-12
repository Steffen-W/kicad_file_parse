Examples and Usage
==================

This section provides practical examples of how to use the KiCad Parser library.

Basic File Operations
---------------------

Loading and Saving Files
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from kicad_parser import load_kicad_file, save_kicad_file
    
    # Load any KiCad file (auto-detection)
    kicad_object = load_kicad_file("example.kicad_sym")
    
    # Save to new location
    save_kicad_file(kicad_object, "modified_example.kicad_sym")

File Type Detection
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from kicad_parser import detect_file_type, KiCadFileType
    
    file_type = detect_file_type("example.kicad_pcb")
    if file_type == KiCadFileType.BOARD:
        print("This is a PCB file")

Working with Symbols
--------------------

Creating a New Symbol
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from kicad_parser import KiCadSymbolLibrary, KiCadSymbol, SymbolPin
    from kicad_parser import PinElectricalType, Position
    
    # Create a new symbol library
    lib = KiCadSymbolLibrary()
    
    # Create a symbol
    symbol = KiCadSymbol(name="MyComponent")
    
    # Add pins
    pin1 = SymbolPin(
        name="VCC",
        number="1", 
        position=Position(0, 2.54),
        electrical_type=PinElectricalType.POWER_INPUT
    )
    symbol.pins.append(pin1)
    
    # Add to library
    lib.symbols.append(symbol)

Modifying Existing Symbols
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from kicad_parser import load_symbol_library
    
    # Load existing library
    lib = load_symbol_library("existing.kicad_sym")
    
    # Modify all symbols
    for symbol in lib.symbols:
        symbol.name = f"Modified_{symbol.name}"
        
        # Update all pin names
        for pin in symbol.pins:
            pin.name = pin.name.upper()

Working with Footprints
-----------------------

Analyzing Pad Information
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from kicad_parser import load_footprint
    
    footprint = load_footprint("component.kicad_mod")
    
    print(f"Footprint: {footprint.name}")
    print(f"Number of pads: {len(footprint.pads)}")
    
    for i, pad in enumerate(footprint.pads):
        print(f"Pad {i+1}: {pad.name}, Type: {pad.type.value}")

Working with PCBs
-----------------

Analyzing Track Information
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from kicad_parser import load_pcb
    
    pcb = load_pcb("design.kicad_pcb")
    
    # Count tracks by layer
    track_count = {}
    for track in pcb.tracks:
        layer = track.layer
        track_count[layer] = track_count.get(layer, 0) + 1
    
    for layer, count in track_count.items():
        print(f"Layer {layer}: {count} tracks")

Working with Zones
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from kicad_parser import load_pcb
    
    pcb = load_pcb("design.kicad_pcb")
    
    # Analyze copper zones
    for zone in pcb.zones:
        if not zone.keepout:
            print(f"Zone on net '{zone.net_name}' covers layers: {zone.layers}")
            print(f"Connection type: {zone.connect_pads.value}")

File Conversion
---------------

Converting Between Formats
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from kicad_parser import convert_file
    
    # Convert with validation
    success = convert_file(
        input_file="old_format.kicad_sym",
        output_file="new_format.kicad_sym", 
        validate=True
    )
    
    if success:
        print("Conversion successful!")

Batch Processing
~~~~~~~~~~~~~~~~

.. code-block:: python

    import os
    from pathlib import Path
    from kicad_parser import load_kicad_file, save_kicad_file
    
    # Process all symbol files in a directory
    symbol_dir = Path("symbols/")
    
    for sym_file in symbol_dir.glob("*.kicad_sym"):
        try:
            # Load, modify, and save
            lib = load_kicad_file(sym_file)
            
            # Your modifications here
            for symbol in lib.symbols:
                # Example: add version info to description
                if symbol.properties:
                    for prop in symbol.properties:
                        if prop.name == "Description":
                            prop.value += " (v1.0)"
            
            # Save with backup
            backup_name = sym_file.with_suffix('.bak')
            sym_file.rename(backup_name)
            save_kicad_file(lib, sym_file)
            
            print(f"Processed: {sym_file.name}")
            
        except Exception as e:
            print(f"Error processing {sym_file.name}: {e}")

Error Handling
--------------

Robust File Processing
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from kicad_parser import load_kicad_file, KiCadParseError
    
    def safe_load_kicad_file(filename):
        try:
            return load_kicad_file(filename)
        except KiCadParseError as e:
            print(f"Parse error in {filename}: {e}")
            return None
        except FileNotFoundError:
            print(f"File not found: {filename}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None
    
    # Use the safe loader
    kicad_obj = safe_load_kicad_file("potentially_problematic.kicad_sym")
    if kicad_obj:
        print("File loaded successfully!")