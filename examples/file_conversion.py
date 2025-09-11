#!/usr/bin/env python3
"""
File conversion example for kicad-parser

This example demonstrates how to:
1. Convert between KiCad file formats
2. Use the convert_file function
3. Validate KiCad files
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from kicad_parser import convert_file, detect_file_type, validate_kicad_file


def main() -> int:
    """Main conversion example
    
    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    # Define paths
    input_file = Path(__file__).parent / "test_data" / "small.kicad_sym"
    output_file = Path(__file__).parent / "output" / "converted_symbol.kicad_sym"
    
    # Create output directory if it doesn't exist
    output_file.parent.mkdir(exist_ok=True)
    
    if not input_file.exists():
        print(f"Test file not found: {input_file}")
        print("Please ensure the test data is available.")
        return 1
    
    try:
        # Validate input file
        print(f"Validating input file: {input_file}")
        validation = validate_kicad_file(input_file)
        
        if validation["valid"]:
            print(f"[OK] File is valid {validation['file_type']}")
            print(f"  Object type: {validation['object_type']}")
        else:
            print(f"[FAIL] File validation failed: {validation['error']}")
            return 1
        
        # Detect file type from content
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        file_type = detect_file_type(content)
        print(f"Detected file type: {file_type}")
        
        # Convert file (copy with potential modifications)
        print(f"\nConverting file...")
        print(f"Input:  {input_file}")
        print(f"Output: {output_file}")
        
        convert_file(input_file, output_file)
        
        # Validate output file
        print(f"\nValidating output file...")
        output_validation = validate_kicad_file(output_file)
        
        if output_validation["valid"]:
            print("[OK] Conversion successful - output file is valid")
        else:
            print(f"[FAIL] Conversion failed: {output_validation['error']}")
            return 1
            
        print(f"\nFiles comparison:")
        input_size = input_file.stat().st_size
        output_size = output_file.stat().st_size
        print(f"Input size:  {input_size} bytes")
        print(f"Output size: {output_size} bytes")
        
        if input_size == output_size:
            print("[OK] File sizes match - perfect copy")
        else:
            print(f"-> Size difference: {output_size - input_size} bytes")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())