#!/usr/bin/env python3
"""
KiCad Worksheet Example

This example demonstrates how to create, modify, and save KiCad worksheet files (.kicad_wks).
Worksheets define the page layout and title block for KiCad schematics and PCB layouts.
"""

import os
import sys

# Add the parent directory to Python path to import kicad_parser
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from kicad_parser import (
    CornerType,
    KiCadWorksheet,
    Position,
    WorksheetLine,
    WorksheetRectangle,
    WorksheetSetup,
    WorksheetText,
    create_basic_worksheet,
    save_worksheet,
    serialize_kicad_object,
)


def create_custom_worksheet():
    """Create a custom worksheet with various elements"""
    print("Creating custom worksheet...")
    
    # Create a new worksheet
    worksheet = KiCadWorksheet(
        version=20220228,
        generator="worksheet_example"
    )
    
    # Configure setup parameters
    worksheet.setup = WorksheetSetup(
        textsize=Position(1.8, 1.8),  # Larger text
        linewidth=0.2,  # Thicker lines
        textlinewidth=0.15,
        left_margin=15.0,  # Wider margins
        right_margin=15.0,
        top_margin=12.0,
        bottom_margin=12.0
    )
    
    # Add main title block rectangle
    worksheet.add_rectangle(
        WorksheetRectangle(
            start=Position(100.0, 5.0),
            end=Position(210.0, 45.0),
            linewidth=0.25,
            corner=CornerType.RIGHT_BOTTOM
        )
    )
    
    # Add subdividing lines in title block
    worksheet.add_line(
        WorksheetLine(
            start=Position(100.0, 25.0),
            end=Position(210.0, 25.0),
            linewidth=0.15,
            corner=CornerType.RIGHT_BOTTOM
        )
    )
    
    worksheet.add_line(
        WorksheetLine(
            start=Position(155.0, 5.0),
            end=Position(155.0, 45.0),
            linewidth=0.15,
            corner=CornerType.RIGHT_BOTTOM
        )
    )
    
    # Add text elements
    worksheet.add_text(
        WorksheetText(
            text="Project Title",
            position=Position(177.5, 15.0),
            corner=CornerType.RIGHT_BOTTOM,
            maxlen=25
        )
    )
    
    worksheet.add_text(
        WorksheetText(
            text="Company Name",
            position=Position(127.5, 35.0),
            corner=CornerType.RIGHT_BOTTOM,
            maxlen=20
        )
    )
    
    worksheet.add_text(
        WorksheetText(
            text="Date:",
            position=Position(177.5, 35.0),
            corner=CornerType.RIGHT_BOTTOM,
            maxlen=15
        )
    )
    
    # Add revision block
    worksheet.add_rectangle(
        WorksheetRectangle(
            start=Position(5.0, 5.0),
            end=Position(35.0, 25.0),
            linewidth=0.15,
            corner=CornerType.RIGHT_BOTTOM
        )
    )
    
    worksheet.add_text(
        WorksheetText(
            text="Rev:",
            position=Position(20.0, 15.0),
            corner=CornerType.RIGHT_BOTTOM,
            maxlen=10
        )
    )
    
    return worksheet


def demonstrate_basic_worksheet():
    """Demonstrate basic worksheet creation"""
    print("\n" + "="*50)
    print("KiCad Worksheet Example")
    print("="*50)
    
    # Create a basic worksheet using the helper function
    print("\n1. Creating basic worksheet...")
    basic_worksheet = create_basic_worksheet(
        title="Example Project", 
        company="Example Company"
    )
    
    print(f"   - Version: {basic_worksheet.version}")
    print(f"   - Generator: {basic_worksheet.generator}")
    print(f"   - Elements: {len(basic_worksheet.rectangles)} rectangles, {len(basic_worksheet.texts)} texts")
    
    # Show S-expression output (first few lines)
    sexpr = serialize_kicad_object(basic_worksheet)
    lines = sexpr.split('\n')[:15]
    print(f"\n   First 15 lines of S-expression output:")
    for line in lines:
        print(f"   {line}")
    print("   ...")
    
    return basic_worksheet


def demonstrate_custom_worksheet():
    """Demonstrate custom worksheet creation"""
    print("\n2. Creating custom worksheet with multiple elements...")
    custom_worksheet = create_custom_worksheet()
    
    print(f"   - Setup margins: L={custom_worksheet.setup.left_margin}, R={custom_worksheet.setup.right_margin}")
    print(f"   - Text size: {custom_worksheet.setup.textsize.x} x {custom_worksheet.setup.textsize.y}")
    print(f"   - Elements: {len(custom_worksheet.rectangles)} rectangles, {len(custom_worksheet.lines)} lines, {len(custom_worksheet.texts)} texts")
    
    return custom_worksheet


def save_worksheets(basic_worksheet, custom_worksheet):
    """Save worksheets to files"""
    print("\n3. Saving worksheets to files...")
    
    # Create output directory if it doesn't exist
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Save basic worksheet
        basic_path = os.path.join(output_dir, "basic_worksheet.kicad_wks")
        save_worksheet(basic_worksheet, basic_path)
        print(f"   [OK] Basic worksheet saved to: {basic_path}")
        
        # Save custom worksheet
        custom_path = os.path.join(output_dir, "custom_worksheet.kicad_wks")
        save_worksheet(custom_worksheet, custom_path)
        print(f"   [OK] Custom worksheet saved to: {custom_path}")
        
        print(f"\n   Output files created in '{output_dir}/' directory")
        print("   You can import these worksheets in KiCad using:")
        print("   File > Page Settings > Page Layout Description File")
        
    except Exception as e:
        print(f"   [ERROR] Error saving worksheets: {e}")


def demonstrate_worksheet_modification():
    """Demonstrate modifying an existing worksheet"""
    print("\n4. Modifying worksheet...")
    
    # Start with basic worksheet
    worksheet = create_basic_worksheet("Original Title", "Original Company")
    print(f"   Original: {len(worksheet.texts)} text elements")
    
    # Add a new text element
    worksheet.add_text(
        WorksheetText(
            text="Drawing Number: DWG-001",
            position=Position(155.0, 30.0),
            corner=CornerType.RIGHT_BOTTOM,
            maxlen=25
        )
    )
    
    # Add a border line
    worksheet.add_line(
        WorksheetLine(
            start=Position(5.0, 5.0),
            end=Position(5.0, 290.0),
            linewidth=0.5,
            corner=CornerType.LEFT_BOTTOM
        )
    )
    
    print(f"   Modified: {len(worksheet.texts)} text elements, {len(worksheet.lines)} lines")
    
    return worksheet


def main():
    """Main function demonstrating worksheet functionality"""
    
    # Basic worksheet creation
    basic_worksheet = demonstrate_basic_worksheet()
    
    # Custom worksheet creation  
    custom_worksheet = demonstrate_custom_worksheet()
    
    # Worksheet modification
    modified_worksheet = demonstrate_worksheet_modification()
    
    # Save all worksheets
    save_worksheets(basic_worksheet, custom_worksheet)
    
    print("\n" + "="*50)
    print("Worksheet example completed successfully!")
    print("="*50)
    
    print("\nKey features demonstrated:")
    print("- Basic worksheet creation with helper function")
    print("- Custom worksheet with setup configuration")
    print("- Adding rectangles, lines, and text elements")
    print("- Corner positioning (RIGHT_BOTTOM, LEFT_BOTTOM, etc.)")
    print("- Text length and height limits")
    print("- S-expression serialization")
    print("- File saving in .kicad_wks format")


if __name__ == "__main__":
    main()