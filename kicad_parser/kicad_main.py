"""
KiCad S-Expression Parser - Main Module

This module provides high-level functions and demonstrates usage of the
complete KiCad S-Expression parsing library.
"""

from typing import Optional, cast

from .kicad_board import (
    FootprintAttributes,
    FootprintPad,
    FootprintRectangle,
    FootprintText,
    FootprintTextType,
    FootprintType,
    KiCadFootprint,
    PadShape,
    PadType,
)

# Import all modules
from .kicad_common import (
    Fill,
    FillType,
    KiCadObject,
    Position,
    Stroke,
)
from .kicad_design_rules import (
    KiCadDesignRules,
)
from .kicad_design_rules import create_basic_design_rules as _create_basic_design_rules
from .kicad_design_rules import load_design_rules as _load_design_rules
from .kicad_design_rules import save_design_rules as _save_design_rules
from .kicad_file import (
    convert_file,
    detect_file_type,
    load_kicad_file,
    load_symbol_library,
    parse_kicad_file,
    save_kicad_file,
    save_symbol_library,
    serialize_kicad_object,
)
from .kicad_pcb import KiCadPCB
from .kicad_schematic import KiCadSchematic
from .kicad_symbol import (
    KiCadSymbol,
    KiCadSymbolLibrary,
    PinElectricalType,
    PinGraphicStyle,
    SymbolPin,
    SymbolRectangle,
)
from .kicad_worksheet import (
    CornerType,
    KiCadWorksheet,
    WorksheetRectangle,
    WorksheetText,
)

# File type detection and parsing


def detect_kicad_file_type(content: str) -> str:
    """Detect the type of KiCad file from its content

    Returns:
        str: File type identifier
    """
    return detect_file_type(content)


def parse_any_kicad_file(content: str) -> KiCadObject:
    """Parse any KiCad file and return appropriate object

    Returns:
        KiCadObject: Parsed KiCad object
    """
    file_type = detect_kicad_file_type(content)

    if file_type == "symbol_library":
        return parse_kicad_file(content, KiCadSymbolLibrary)
    elif file_type == "footprint":
        return parse_kicad_file(content, KiCadFootprint)
    elif file_type == "worksheet":
        return parse_kicad_file(content, KiCadWorksheet)
    elif file_type == "schematic":
        return parse_kicad_file(content, KiCadSchematic)
    elif file_type == "board":
        return parse_kicad_file(content, KiCadPCB)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")


def load_any_kicad_file(filepath: str) -> KiCadObject:
    """Load any KiCad file from disk

    Returns:
        KiCadObject: Loaded KiCad object
    """
    return load_kicad_file(filepath)


def save_any_kicad_file(obj: KiCadObject, filepath: str) -> None:
    """Save any KiCad object to disk

    Returns:
        None
    """
    save_kicad_file(obj, filepath)


# Utility functions for common operations


def create_basic_symbol(
    name: str, reference: str = "U", value: Optional[str] = None
) -> KiCadSymbol:
    """Create a basic symbol with minimal required properties

    Returns:
        KiCadSymbol: Basic symbol with standard properties
    """
    if value is None:
        value = name

    symbol = KiCadSymbol(name=name)

    # Add mandatory properties
    symbol.set_property("Reference", reference, id=0, position=Position(0, 2.54))
    symbol.set_property("Value", value, id=1, position=Position(0, -2.54))
    symbol.set_property("Footprint", "", id=2, position=Position(0, -5.08))
    symbol.set_property("Datasheet", "", id=3, position=Position(0, -7.62))

    return symbol


def create_basic_footprint(
    name: str, reference: str = "REF**", value: Optional[str] = None
) -> KiCadFootprint:
    """Create a basic footprint with minimal required elements

    Returns:
        KiCadFootprint: Basic footprint with reference and value texts
    """
    if value is None:
        value = name

    footprint = KiCadFootprint(library_link=name)

    # Add mandatory reference and value texts
    footprint.texts.append(
        FootprintText(
            type=FootprintTextType.REFERENCE,
            text=reference,
            position=Position(0, -3),
            layer="F.SilkS",
        )
    )

    footprint.texts.append(
        FootprintText(
            type=FootprintTextType.VALUE,
            text=value,
            position=Position(0, 3),
            layer="F.Fab",
        )
    )

    return footprint


# Example usage and testing


def example_symbol_creation() -> KiCadSymbolLibrary:
    """Example of creating and modifying a symbol library

    Returns:
        KiCadSymbolLibrary: Example symbol library with resistor
    """
    # Create a new symbol library
    library = KiCadSymbolLibrary(version=20211014, generator="kicad_parser")

    # Create a basic resistor symbol
    resistor = create_basic_symbol("R_Generic", "R", "R")

    # Add a simple rectangle for the resistor body
    resistor.rectangles.append(
        SymbolRectangle(
            start=Position(-2.54, -1.27),
            end=Position(2.54, 1.27),
            stroke=Stroke(width=0.254),
            fill=Fill(type=FillType.NONE),
        )
    )

    # Add pins
    resistor.pins.append(
        SymbolPin(
            electrical_type=PinElectricalType.PASSIVE,
            graphic_style=PinGraphicStyle.LINE,
            position=Position(-5.08, 0, 0),
            length=2.54,
            name="~",
            number="1",
        )
    )

    resistor.pins.append(
        SymbolPin(
            electrical_type=PinElectricalType.PASSIVE,
            graphic_style=PinGraphicStyle.LINE,
            position=Position(5.08, 0, 180),
            length=2.54,
            name="~",
            number="2",
        )
    )

    # Add symbol to library
    library.add_symbol(resistor)

    return library


def example_footprint_creation() -> KiCadFootprint:
    """Example of creating a basic footprint

    Returns:
        KiCadFootprint: Example footprint for 0805 resistor
    """
    # Create a basic resistor footprint
    footprint = create_basic_footprint("R_0805_2012Metric", "R**", "R_0805")

    # Add outline rectangle
    footprint.rectangles.append(
        FootprintRectangle(
            start=Position(-1, -0.625),
            end=Position(1, 0.625),
            layer="F.Fab",
            stroke=Stroke(width=0.1),
        )
    )

    # Add pads
    footprint.pads.append(
        FootprintPad(
            number="1",
            type=PadType.SMD,
            shape=PadShape.RECT,
            position=Position(-0.9, 0),
            size=(1.0, 1.3),
            layers=["F.Cu", "F.Paste", "F.Mask"],
        )
    )

    footprint.pads.append(
        FootprintPad(
            number="2",
            type=PadType.SMD,
            shape=PadShape.RECT,
            position=Position(0.9, 0),
            size=(1.0, 1.3),
            layers=["F.Cu", "F.Paste", "F.Mask"],
        )
    )

    # Set attributes
    footprint.attributes = FootprintAttributes(
        type=FootprintType.SMD, exclude_from_bom=False, exclude_from_pos_files=False
    )

    return footprint


def create_basic_worksheet(
    title: str = "Title", company: str = "Company"
) -> KiCadWorksheet:
    """Create a basic worksheet with title block elements

    Args:
        title: Title text for the worksheet
        company: Company name for the worksheet

    Returns:
        KiCadWorksheet: Basic worksheet with title block
    """
    worksheet = KiCadWorksheet(version=20220228, generator="kicad_parser")

    # Add basic title block rectangle
    worksheet.add_rectangle(
        WorksheetRectangle(
            start=Position(110.0, 5.0),
            end=Position(200.0, 35.0),
            linewidth=0.15,
            corner=CornerType.RIGHT_BOTTOM,
        )
    )

    # Add title text
    worksheet.add_text(
        WorksheetText(
            text=title,
            position=Position(155.0, 15.0),
            corner=CornerType.RIGHT_BOTTOM,
            maxlen=30,
        )
    )

    # Add company text
    worksheet.add_text(
        WorksheetText(
            text=company,
            position=Position(155.0, 25.0),
            corner=CornerType.RIGHT_BOTTOM,
            maxlen=30,
        )
    )

    return worksheet


def load_design_rules(filepath: str) -> KiCadDesignRules:
    """Load KiCad design rules from .kicad_dru file

    Args:
        filepath: Path to the .kicad_dru file

    Returns:
        KiCadDesignRules: Loaded design rules object
    """
    return _load_design_rules(filepath)


def save_design_rules(design_rules: KiCadDesignRules, filepath: str) -> None:
    """Save KiCad design rules to .kicad_dru file

    Args:
        design_rules: Design rules object to save
        filepath: Path where to save the .kicad_dru file
    """
    _save_design_rules(design_rules, filepath)


def create_basic_design_rules() -> KiCadDesignRules:
    """Create a basic design rules file with common rules

    Returns:
        KiCadDesignRules: Basic design rules with example clearance rule
    """
    return _create_basic_design_rules()


def main() -> None:
    """Main function demonstrating library usage

    Returns:
        None
    """
    print("KiCad S-Expression Parser Demo")
    print("=" * 40)

    # Example 1: Create and save a symbol library
    print("\n1. Creating symbol library...")
    library = example_symbol_creation()

    # Convert to S-Expression and display
    sexpr_output = serialize_kicad_object(library)
    print(f"Symbol library created with {len(library.symbols)} symbol(s)")
    print("First few lines of S-Expression output:")
    print("\n".join(sexpr_output.split("\n")[:10]) + "\n...")

    # Example 2: Create footprint
    print("\n2. Creating footprint...")
    footprint = example_footprint_creation()

    footprint_output = serialize_kicad_object(footprint)
    print(f"Footprint created with {len(footprint.pads)} pad(s)")
    print("First few lines of footprint S-Expression:")
    print("\n".join(footprint_output.split("\n")[:10]) + "\n...")

    # Example 3: Load, modify, and save (if file exists)
    print("\n3. File operations example:")
    try:
        # Try to load from your test file
        test_library = load_symbol_library("examples/test_data/small.kicad_sym")
        print(f"Loaded library with {len(test_library.symbols)} symbol(s)")

        if test_library.symbols:
            symbol = test_library.symbols[0]
            print(f"First symbol: {symbol.name}")

            # Modify a property
            old_ref = symbol.get_property("Reference")
            print(f"Original Reference: {old_ref.value if old_ref else 'None'}")

            symbol.set_property("Reference", "IC")
            ref_prop = symbol.get_property("Reference")
            print(f"Modified Reference: {ref_prop.value if ref_prop else 'None'}")

            # Save modified version
            save_symbol_library(
                test_library, "examples/output/modified_output.kicad_sym"
            )
            print("Saved modified library to examples/output/modified_output.kicad_sym")

    except FileNotFoundError:
        print("Test file not found - skipping load/modify example")
    except Exception as e:
        print(f"Error in file operations: {e}")

    print("\nDemo completed successfully!")


def integrate_with_original_code() -> None:
    """Demonstrates unified file API usage

    Returns:
        None
    """
    print("\n4. Unified file API example:")

    try:
        # Load using unified API
        library = cast(
            KiCadSymbolLibrary, load_kicad_file("examples/test_data/small.kicad_sym")
        )
        print(f"Library loaded with {len(library.symbols)} symbols")

        # Create original copy
        convert_file(
            "examples/test_data/small.kicad_sym",
            "examples/output/output_original.kicad_sym",
        )

        # Modify symbol properties
        if library.symbols:
            symbol = library.symbols[0]
            symbol.set_property("Reference", "IC_NEW")
            symbol.set_property("Description", "Modified via API")

        # Save modified version
        save_kicad_file(library, "examples/output/output_modified.kicad_sym")

        print("Output files created:")
        print("  - examples/output/output_original.kicad_sym (original)")
        print("  - examples/output/output_modified.kicad_sym (modified)")

    except Exception as e:
        print(f"API example failed: {e}")


if __name__ == "__main__":
    main()
    integrate_with_original_code()
