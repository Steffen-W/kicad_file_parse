#!/usr/bin/env python3
"""
Symbol creation example for kicad-parser

This example demonstrates how to:
1. Create symbols from scratch
2. Create symbol libraries
3. Add pins, graphics, and properties
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from kicad_parser import (
    Fill,
    FillType,
    KiCadSymbol,
    KiCadSymbolLibrary,
    PinElectricalType,
    PinGraphicStyle,
    Position,
    Stroke,
    SymbolPin,
    SymbolRectangle,
    create_basic_footprint,
    create_basic_symbol,
)


def create_resistor_symbol() -> KiCadSymbol:
    """Create a basic resistor symbol
    
    Returns:
        KiCadSymbol: Resistor symbol with rectangle body and pins
    """
    # Create basic symbol
    resistor = create_basic_symbol("R_Generic", "R", "R")
    
    # Add symbol body rectangle
    resistor.rectangles.append(SymbolRectangle(
        start=Position(-2.54, -1.27),
        end=Position(2.54, 1.27),
        stroke=Stroke(width=0.254),
        fill=Fill(type=FillType.NONE)
    ))
    
    # Add pins
    resistor.pins.append(SymbolPin(
        electrical_type=PinElectricalType.PASSIVE,
        graphic_style=PinGraphicStyle.LINE,
        position=Position(-5.08, 0, 0),  # x, y, angle
        length=2.54,
        name="~",
        number="1"
    ))
    
    resistor.pins.append(SymbolPin(
        electrical_type=PinElectricalType.PASSIVE,
        graphic_style=PinGraphicStyle.LINE,
        position=Position(5.08, 0, 180),  # x, y, angle (180 deg rotated)
        length=2.54,
        name="~",
        number="2"
    ))
    
    return resistor

def main() -> int:
    """Main symbol creation example
    
    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    try:
        print("Creating symbol library...")
        library = KiCadSymbolLibrary(version=20211014, generator="kicad-parser")
        
        # Create resistor symbol
        print("Creating resistor symbol...")
        resistor = create_resistor_symbol()
        library.add_symbol(resistor)
        
        print(f"Created resistor symbol with:")
        print(f"  - {len(resistor.properties)} properties")
        print(f"  - {len(resistor.rectangles)} rectangles")
        print(f"  - {len(resistor.pins)} pins")
        
        # Create more symbols using the helper function
        print("Creating capacitor symbol...")
        capacitor = create_basic_symbol("C_Generic", "C", "C")
        library.add_symbol(capacitor)
        
        print("Creating inductor symbol...")
        inductor = create_basic_symbol("L_Generic", "L", "L")
        library.add_symbol(inductor)
        
        print(f"\nLibrary now contains {len(library.symbols)} symbols:")
        for symbol in library.symbols:
            print(f"  - {symbol.name}")
        
        # Save the library
        output_file = output_dir / "custom_library.kicad_sym"
        print(f"\nSaving library to: {output_file}")
        
        from kicad_parser import save_symbol_library
        save_symbol_library(library, output_file)
        
        print("[OK] Symbol library created successfully!")
        
        # Display some statistics
        file_size = output_file.stat().st_size
        print(f"\nLibrary statistics:")
        print(f"  File size: {file_size} bytes")
        print(f"  Symbols: {len(library.symbols)}")
        total_pins = sum(len(s.pins) for s in library.symbols)
        print(f"  Total pins: {total_pins}")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())