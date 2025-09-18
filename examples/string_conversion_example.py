#!/usr/bin/env python3
"""
String Conversion Example for kicad_parserv2

This example demonstrates how to:
1. Create KiCad objects using the dataclass syntax
2. Convert objects to S-expression strings using to_sexpr_str()
3. Parse S-expression strings back to objects using from_sexpr()
4. Show round-trip conversion (object -> string -> object)
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from kicad_parserv2 import (  # Basic types; Graphics elements; Complex objects; Parser functions
    At,
    Center,
    Effects,
    End,
    Font,
    Footprint,
    FpCircle,
    FpLine,
    FpText,
    Layer,
    ParseMode,
    Size,
    Start,
    Stroke,
    Type,
    Width,
    sexpr_to_str,
    str_to_sexpr,
)


def demonstrate_basic_types():
    """Demonstrate string conversion with basic types"""
    print("=== Basic Types String Conversion ===\n")

    # Create basic position object
    position = At(x=10.5, y=20.0, angle=90.0)
    print(f"Position object: {position}")
    print(f"To string: {position.to_sexpr_str()}")

    # Parse it back
    position_str = position.to_sexpr_str()
    parsed_position = At.from_sexpr(position_str)
    print(f"Parsed back: {parsed_position}")
    print(f"Are equal: {position == parsed_position}\n")

    # Create layer object
    layer = Layer(name="F.Cu")
    print(f"Layer object: {layer}")
    print(f"To string: {layer.to_sexpr_str()}")

    # Round-trip conversion
    layer_parsed = Layer.from_sexpr(layer.to_sexpr_str())
    print(f"Parsed back: {layer_parsed}")
    print(f"Are equal: {layer == layer_parsed}\n")


def demonstrate_complex_objects():
    """Demonstrate string conversion with complex objects"""
    print("=== Complex Objects String Conversion ===\n")

    # Create a footprint text element
    fp_text = FpText(
        type=Type(value="reference"),
        text="R1",
        at=At(x=0.0, y=0.0, angle=0.0),
        layer=Layer(name="F.SilkS"),
        effects=Effects(font=Font(size=Size(width=1.0, height=1.0))),
    )

    print(f"FpText object created:")
    print(f"  Type: {fp_text.type}")
    print(f"  Text: {fp_text.text}")
    print(f"  Position: {fp_text.at}")
    print(f"  Layer: {fp_text.layer}")

    # Convert to string
    fp_text_str = fp_text.to_sexpr_str()
    print(f"\nConverted to S-expression:")
    print(fp_text_str)

    # Parse it back
    fp_text_parsed = FpText.from_sexpr(fp_text_str)
    print(f"\nParsed back:")
    print(f"  Type: {fp_text_parsed.type}")
    print(f"  Text: {fp_text_parsed.text}")
    print(f"  Position: {fp_text_parsed.at}")
    print(f"  Layer: {fp_text_parsed.layer}")
    print(f"  Are equal: {fp_text == fp_text_parsed}\n")


def demonstrate_graphics_elements():
    """Demonstrate string conversion with graphics elements"""
    print("=== Graphics Elements String Conversion ===\n")

    # Create a line
    line = FpLine(
        start=Start(x=0.0, y=0.0),
        end=End(x=5.0, y=5.0),
        stroke=Stroke(width=Width(value=0.12)),
        layer=Layer(name="F.SilkS"),
    )

    print(f"Line object: start={line.start}, end={line.end}")
    line_str = line.to_sexpr_str()
    print(f"To string: {line_str}")
    line_parsed = FpLine.from_sexpr(line_str)
    print(f"Round-trip successful: {line == line_parsed}\n")

    # Create a circle
    circle = FpCircle(
        center=Center(x=0.0, y=0.0),
        end=End(x=2.5, y=0.0),
        width=Width(value=0.12),
        layer=Layer(name="F.SilkS"),
    )

    print(f"Circle object: center={circle.center}, radius calculated from end")
    circle_str = circle.to_sexpr_str()
    print(f"To string: {circle_str}")
    circle_parsed = FpCircle.from_sexpr(circle_str)
    print(f"Round-trip successful: {circle == circle_parsed}\n")


def demonstrate_simple_footprint():
    """Demonstrate string conversion with a simple footprint"""
    print("=== Simple Footprint String Conversion ===\n")

    # Create a basic footprint with just essential elements
    footprint = Footprint(
        library_link="MyLib:MyFootprint",
        at=At(x=100.0, y=50.0, angle=0.0),
        layer=Layer(name="F.Cu"),
    )

    print("Created simple footprint object")
    print(f"Library link: {footprint.library_link}")
    print(f"Position: {footprint.at}")
    print(f"Layer: {footprint.layer}")

    # Convert to string
    print("\nConverting to S-expression string...")
    footprint_str = footprint.to_sexpr_str()
    print("String length:", len(footprint_str), "characters")
    print("\nS-expression:")
    print(footprint_str)

    # Parse it back
    print("\nParsing back from string...")
    footprint_parsed = Footprint.from_sexpr(footprint_str)
    print(f"Parsed library link: {footprint_parsed.library_link}")
    print(f"Parsed position: {footprint_parsed.at}")
    print(f"Round-trip successful: {footprint == footprint_parsed}")

    if footprint == footprint_parsed:
        print("✓ Perfect round-trip conversion!")
    else:
        print("✗ Round-trip conversion has differences")


def demonstrate_raw_sexpr_parsing():
    """Demonstrate raw S-expression parsing functions"""
    print("=== Raw S-Expression Parsing ===\n")

    # Create some raw S-expression strings
    simple_sexpr = "(at 10.5 20.0 90)"
    complex_sexpr = """(fp_text reference "R1"
        (at 0 -1.43)
        (layer "F.SilkS")
        (effects (font (size 1 1) (thickness 0.15)))
    )"""

    print("Simple S-expression:", simple_sexpr)

    # Parse to intermediate representation
    parsed_sexpr = str_to_sexpr(simple_sexpr)
    print(f"Parsed structure: {parsed_sexpr}")

    # Convert back to string
    back_to_str = sexpr_to_str(parsed_sexpr)
    print(f"Back to string: {back_to_str}")
    print(f"Strings match: {simple_sexpr == back_to_str}")

    print(f"\nComplex S-expression (first 100 chars): {complex_sexpr[:100]}...")
    parsed_complex = str_to_sexpr(complex_sexpr)
    print(f"Complex parsed structure type: {type(parsed_complex)}")
    back_to_complex = sexpr_to_str(parsed_complex)
    print(f"Round-trip for complex: {len(back_to_complex)} chars")


def main():
    """Main example function"""
    print("KiCad Parser v2 - String Conversion Examples")
    print("=" * 60)
    print("This example shows how to convert KiCad objects to/from strings\n")

    try:
        # Run all demonstrations
        demonstrate_basic_types()
        demonstrate_complex_objects()
        demonstrate_graphics_elements()
        demonstrate_simple_footprint()
        demonstrate_raw_sexpr_parsing()

        print("\n" + "=" * 60)
        print("✓ All string conversion examples completed successfully!")
        print("\nKey takeaways:")
        print("- Use obj.to_sexpr_str() to convert objects to S-expressions")
        print("- Use ClassName.from_sexpr(sexpr_str) to parse back")
        print("- Round-trip conversion preserves object equality")
        print("- Both simple and complex objects support string conversion")
        print("- The library handles proper S-expression formatting automatically")

    except Exception as e:
        print(f"Error during example: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":

    # Example of clean output showing only non-None values
    sexp = """(
    "footprint"
    ("library_link" "MyLib:MyFootprint")
    (
    "layer"
    ("name" "F.Cu")
    )
    ("tedit")
    (
    "at"
    ("x" 100.0)
    ("y" 50.0)
    ("angle" 0.0)
    )
    ("path" "")
    (
    "pad"
    ("number" "1")
    ("type" "smd")
    ("shape" "rect")
    (
    "at"
    ("x" 0.0)
    ("y" 0.0)
    )
    (
    "size"
    ("width" 1.0)
    ("height" 0.6)
    )
    (
    "layers"
    "F.Cu"
    "F.Paste"
    "F.Mask"
    )
    )
    (
    "pad"
    ("number" "2")
    ("type" "smd")
    ("shape" "rect")
    (
    "at"
    ("x" 1.0)
    ("y" 0.0)
    )
    (
    "size"
    ("width" )
    ("height" 0.6)
    )
    (
    "layers"
    "F.Cu"
    "F.Paste"
    "F.Mask"
    )
    )
    ("unknown_token" "some_value")
    ("another_unknown" 42)
    )"""
    parsed_sexpr = str_to_sexpr(sexp)
    print(f"\nParsed S-expression structure: {parsed_sexpr}")
    # Setup logging to see the new behavior
    import logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    print("\n=== STRICT Mode (errors and immediate fail) ===")
    try:
        foot_strict = Footprint.from_sexpr(parsed_sexpr, ParseMode.STRICT)
        print(foot_strict)
    except Exception as e:
        print(f"Error in STRICT mode: {e}")

    print("\n=== LENIENT Mode (warnings for missing fields) ===")
    foot_lenient = Footprint.from_sexpr(parsed_sexpr, ParseMode.LENIENT)
    print(foot_lenient)

    print("\n=== PERMISSIVE Mode (no logging) ===")
    foot_permissive = Footprint.from_sexpr(parsed_sexpr, ParseMode.PERMISSIVE)
    print(foot_permissive)

    print("\n=== COMPLETE Mode (warnings + check unused) ===")
    try:
        foot_complete = Footprint.from_sexpr(parsed_sexpr, ParseMode.COMPLETE)
        print(foot_complete)
    except Exception as e:
        print(f"Error in COMPLETE mode: {e}")

    # sys.exit(main())
