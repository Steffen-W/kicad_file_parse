#!/usr/bin/env python3
"""
Basic usage example for kicad-parser

This example demonstrates how to:
1. Load a KiCad symbol library
2. Modify symbol properties
3. Save the modified library
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from kicad_parser import load_symbol_library, save_symbol_library


def main() -> int:
    """Main example function
    
    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    # Define paths
    input_file = Path(__file__).parent / "test_data" / "small.kicad_sym"
    output_file = Path(__file__).parent / "output" / "modified_symbol.kicad_sym"
    
    # Create output directory if it doesn't exist
    output_file.parent.mkdir(exist_ok=True)
    
    if not input_file.exists():
        print(f"Test file not found: {input_file}")
        print("Please ensure the test data is available.")
        return 1
    
    try:
        # Load the symbol library
        print(f"Loading symbol library from: {input_file}")
        library = load_symbol_library(input_file)
        
        print(f"Library contains {len(library.symbols)} symbol(s)")
        
        if library.symbols:
            symbol = library.symbols[0]
            print(f"Working with symbol: {symbol.name}")
            
            # Show current properties
            print("\nCurrent properties:")
            for prop in symbol.properties:
                print(f"  {prop.key}: {prop.value}")
            
            # Modify symbol properties
            print("\nModifying properties...")
            symbol.set_property("Reference", "IC")
            symbol.set_property("Description", "Modified via kicad-parser")
            
            # Remove property if it exists
            if symbol.get_property("PARTREV"):
                symbol.remove_property("PARTREV")
                print("Removed PARTREV property")
            
            # Show modified properties
            print("\nModified properties:")
            for prop in symbol.properties:
                print(f"  {prop.key}: {prop.value}")
        
        # Save the modified library
        print(f"\nSaving modified library to: {output_file}")
        save_symbol_library(library, output_file)
        print("Successfully saved modified library!")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())