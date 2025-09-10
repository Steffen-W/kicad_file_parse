#!/usr/bin/env python3
"""
KiCad Schematic Parser Example

This example demonstrates how to create, modify, and save KiCad schematic files
using the kicad-parser library. It covers all major schematic elements according
to the KiCad S-Expression format specification.

Based on: doc/file-formats/sexpr-schematic/_index.en.adoc
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from kicad_parser import *
from kicad_parser.kicad_common import JustifyHorizontal, PaperSize, StrokeType
from kicad_parser.kicad_schematic import *


def create_example_schematic():
    """Create a comprehensive example schematic with various elements"""
    print("[INFO] Creating comprehensive schematic example...")
    
    # Create basic schematic
    schematic = create_basic_schematic(
        title="LED Blinker Circuit",
        company="KiCad Parser Example"
    )
    
    # Set additional title block information
    schematic.title_block.date = "2024-01-15"
    schematic.title_block.revision = "Rev 1.0"
    schematic.title_block.comments = {
        1: "Basic LED blinker using 555 timer",
        2: "Example generated with kicad-parser"
    }
    
    # Set page to A4
    schematic.page_settings = PageSettings(paper_size=PaperSize.A4)
    
    print("[OK] Basic schematic structure created")
    return schematic


def add_library_symbols(schematic):
    """Add library symbol definitions to the schematic"""
    print("[INFO] Adding library symbols...")
    
    # Create a basic resistor symbol for the library
    resistor_symbol = create_basic_symbol("Device:R", "R", "R")
    
    # Add pins to resistor
    from kicad_parser.kicad_symbol import PinElectricalType as LibPinElectricalType
    from kicad_parser.kicad_symbol import PinGraphicStyle
    from kicad_parser.kicad_symbol import SymbolPin as LibrarySymbolPin
    
    resistor_symbol.pins.extend([
        LibrarySymbolPin(
            electrical_type=LibPinElectricalType.PASSIVE,
            graphic_style=PinGraphicStyle.LINE,
            position=Position(-2.54, 0, 180),  # Left pin
            length=0.635,
            name="~",
            number="1"
        ),
        LibrarySymbolPin(
            electrical_type=LibPinElectricalType.PASSIVE,
            graphic_style=PinGraphicStyle.LINE,
            position=Position(2.54, 0, 0),     # Right pin
            length=0.635,
            name="~", 
            number="2"
        )
    ])
    
    # Add to schematic library
    schematic.lib_symbols.append(resistor_symbol)
    
    print("[OK] Library symbols added")


def add_power_connections(schematic):
    """Add power supply connections"""
    print("[INFO] Adding power supply connections...")
    
    # Add VCC and GND global labels
    schematic.global_labels.extend([
        GlobalLabel(
            text="VCC",
            shape=LabelShape.INPUT,
            position=Position(50.0, 30.0),
            effects=TextEffects(
                font=Font(size_height=1.27, size_width=1.27, bold=True)
            ),
            uuid=UUID("vcc-label-1"),
            properties=[Property("Netname", "VCC")]
        ),
        GlobalLabel(
            text="GND",
            shape=LabelShape.INPUT,
            position=Position(50.0, 120.0),
            effects=TextEffects(
                font=Font(size_height=1.27, size_width=1.27, bold=True)
            ),
            uuid=UUID("gnd-label-1"),
            properties=[Property("Netname", "GND")]
        )
    ])
    
    # Add power supply wires
    schematic.wires.extend([
        Wire(
            points=CoordinatePointList([(50.0, 30.0), (80.0, 30.0)]),
            stroke=Stroke(width=0.152),
            uuid=UUID("vcc-wire-1")
        ),
        Wire(
            points=CoordinatePointList([(50.0, 120.0), (80.0, 120.0)]),
            stroke=Stroke(width=0.152),
            uuid=UUID("gnd-wire-1")
        )
    ])
    
    # Add power junctions
    schematic.junctions.extend([
        Junction(
            position=Position(80.0, 30.0),
            diameter=0.36,
            uuid=UUID("vcc-junction-1")
        ),
        Junction(
            position=Position(80.0, 120.0),
            diameter=0.36,
            uuid=UUID("gnd-junction-1")
        )
    ])
    
    print("[OK] Power connections added")


def add_main_circuit(schematic):
    """Add the main 555 timer circuit"""
    print("[INFO] Adding main circuit components...")
    
    # Add 555 timer IC symbol
    timer_555 = SchematicSymbol(
        library_id="Timer:NE555P",
        position=Position(120.0, 75.0),
        unit=1,
        in_bom=True,
        on_board=True,
        uuid=UUID("U1-555-timer")
    )
    
    # Add properties to 555 timer
    timer_555.properties.extend([
        Property("Reference", "U1"),
        Property("Value", "NE555P"),
        Property("Footprint", "Package_DIP:DIP-8_W7.62mm"),
        Property("Datasheet", "http://www.ti.com/lit/ds/symlink/ne555.pdf")
    ])
    
    # Add instance data
    project = SymbolProject(
        name="led_blinker",
        instances={"/": SymbolInstance(reference="U1", unit=1)}
    )
    timer_555.projects.append(project)
    
    schematic.symbols.append(timer_555)
    
    # Add timing resistor
    resistor_r1 = SchematicSymbol(
        library_id="Device:R",
        position=Position(90.0, 50.0),
        unit=1,
        uuid=UUID("R1-timing-resistor")
    )
    resistor_r1.properties.extend([
        Property("Reference", "R1"),
        Property("Value", "10k"),
        Property("Footprint", "Resistor_SMD:R_0603_1608Metric")
    ])
    
    project_r1 = SymbolProject(
        name="led_blinker",
        instances={"/": SymbolInstance(reference="R1", unit=1)}
    )
    resistor_r1.projects.append(project_r1)
    
    schematic.symbols.append(resistor_r1)
    
    # Add LED current limiting resistor
    resistor_r2 = SchematicSymbol(
        library_id="Device:R",
        position=Position(170.0, 60.0),
        unit=1,
        uuid=UUID("R2-current-limiting")
    )
    resistor_r2.properties.extend([
        Property("Reference", "R2"),
        Property("Value", "330"),
        Property("Footprint", "Resistor_SMD:R_0603_1608Metric")
    ])
    
    project_r2 = SymbolProject(
        name="led_blinker",
        instances={"/": SymbolInstance(reference="R2", unit=1)}
    )
    resistor_r2.projects.append(project_r2)
    
    schematic.symbols.append(resistor_r2)
    
    # Add LED
    led = SchematicSymbol(
        library_id="Device:LED",
        position=Position(200.0, 60.0),
        unit=1,
        uuid=UUID("D1-status-led")
    )
    led.properties.extend([
        Property("Reference", "D1"),
        Property("Value", "RED"),
        Property("Footprint", "LED_SMD:LED_0603_1608Metric")
    ])
    
    project_led = SymbolProject(
        name="led_blinker",
        instances={"/": SymbolInstance(reference="D1", unit=1)}
    )
    led.projects.append(project_led)
    
    schematic.symbols.append(led)
    
    print("[OK] Main circuit components added")


def add_circuit_connections(schematic):
    """Add wiring between components"""
    print("[INFO] Adding circuit connections...")
    
    # Add main circuit wires
    schematic.wires.extend([
        # VCC to 555 pin 8
        Wire(
            points=CoordinatePointList([(80.0, 30.0), (80.0, 55.0), (105.0, 55.0)]),
            stroke=Stroke(width=0.152),
            uuid=UUID("vcc-to-555")
        ),
        # GND to 555 pin 1
        Wire(
            points=CoordinatePointList([(80.0, 120.0), (80.0, 95.0), (105.0, 95.0)]),
            stroke=Stroke(width=0.152),
            uuid=UUID("gnd-to-555")
        ),
        # 555 pin 3 to R2
        Wire(
            points=CoordinatePointList([(135.0, 65.0), (155.0, 65.0), (155.0, 60.0)]),
            stroke=Stroke(width=0.152),
            uuid=UUID("555-output-to-r2")
        ),
        # R2 to LED anode
        Wire(
            points=CoordinatePointList([(185.0, 60.0), (190.0, 60.0)]),
            stroke=Stroke(width=0.152),
            uuid=UUID("r2-to-led")
        ),
        # LED cathode to GND
        Wire(
            points=CoordinatePointList([(210.0, 60.0), (220.0, 60.0), (220.0, 120.0), (80.0, 120.0)]),
            stroke=Stroke(width=0.152),
            uuid=UUID("led-to-gnd")
        )
    ])
    
    # Add timing network connections
    schematic.wires.extend([
        # R1 top to VCC
        Wire(
            points=CoordinatePointList([(90.0, 40.0), (90.0, 30.0), (80.0, 30.0)]),
            stroke=Stroke(width=0.152),
            uuid=UUID("r1-to-vcc")
        ),
        # R1 bottom to 555 pins 2,6,7
        Wire(
            points=CoordinatePointList([(90.0, 60.0), (90.0, 75.0), (105.0, 75.0)]),
            stroke=Stroke(width=0.152),
            uuid=UUID("timing-network")
        )
    ])
    
    # Add local labels for important nets
    schematic.local_labels.extend([
        LocalLabel(
            text="TIMER_OUT",
            position=Position(150.0, 65.0),
            effects=TextEffects(font=Font(size_height=1.0, size_width=1.0)),
            uuid=UUID("timer-out-label")
        ),
        LocalLabel(
            text="TIMING",
            position=Position(95.0, 75.0),
            effects=TextEffects(font=Font(size_height=1.0, size_width=1.0)),
            uuid=UUID("timing-label")
        )
    ])
    
    print("[OK] Circuit connections added")


def add_documentation(schematic):
    """Add documentation text and notes"""
    print("[INFO] Adding documentation...")
    
    # Add title text
    schematic.texts.append(SchematicText(
        text="555 Timer LED Blinker",
        position=Position(120.0, 20.0),
        effects=TextEffects(
            font=Font(size_height=2.5, size_width=2.5, bold=True),
            justify_horizontal=JustifyHorizontal.CENTER
        ),
        uuid=UUID("title-text")
    ))
    
    # Add circuit description
    schematic.texts.extend([
        SchematicText(
            text="Astable multivibrator configuration",
            position=Position(30.0, 140.0),
            effects=TextEffects(font=Font(size_height=1.2, size_width=1.2)),
            uuid=UUID("desc-1")
        ),
        SchematicText(
            text="Frequency ~= 1.44 / ((R1 + 2*R2) * C1)",
            position=Position(30.0, 145.0),
            effects=TextEffects(font=Font(size_height=1.0, size_width=1.0)),
            uuid=UUID("formula")
        ),
        SchematicText(
            text="LED flashes at ~1Hz with shown values",
            position=Position(30.0, 150.0),
            effects=TextEffects(
                font=Font(size_height=1.0, size_width=1.0, italic=True)
            ),
            uuid=UUID("note")
        )
    ])
    
    # Add design frame/border using polylines
    frame_width = 280.0
    frame_height = 200.0
    frame_x = 10.0
    frame_y = 10.0
    
    schematic.polylines.append(Polyline(
        points=CoordinatePointList([
            (frame_x, frame_y),
            (frame_x + frame_width, frame_y),
            (frame_x + frame_width, frame_y + frame_height),
            (frame_x, frame_y + frame_height),
            (frame_x, frame_y)
        ]),
        stroke=Stroke(width=0.254, type=StrokeType.SOLID),
        uuid=UUID("design-frame")
    ))
    
    print("[OK] Documentation added")


def demonstrate_hierarchical_design(schematic):
    """Add hierarchical sheet example"""
    print("[INFO] Adding hierarchical design example...")
    
    # Create a hierarchical sheet for power supply
    power_sheet = HierarchicalSheet(
        position=Position(250.0, 40.0),
        size=(50.0, 40.0),
        stroke=Stroke(width=0.152),
        uuid=UUID("power-supply-sheet"),
        sheet_name="Power Supply",
        file_name="power_supply.kicad_sch",
        fields_autoplaced=True
    )
    
    # Add hierarchical pins to the sheet
    power_sheet.pins.extend([
        HierarchicalPin(
            name="VCC_OUT",
            electrical_type=PinElectricalType.OUTPUT,
            position=Position(250.0, 50.0),
            effects=TextEffects(font=Font(size_height=1.0, size_width=1.0)),
            uuid=UUID("vcc-out-pin")
        ),
        HierarchicalPin(
            name="GND",
            electrical_type=PinElectricalType.PASSIVE,
            position=Position(250.0, 70.0),
            effects=TextEffects(font=Font(size_height=1.0, size_width=1.0)),
            uuid=UUID("gnd-pin")
        ),
        HierarchicalPin(
            name="VIN",
            electrical_type=PinElectricalType.INPUT,
            position=Position(300.0, 60.0),
            effects=TextEffects(font=Font(size_height=1.0, size_width=1.0)),
            uuid=UUID("vin-pin")
        )
    ])
    
    # Add sheet instance data
    sheet_project = SheetProject(
        name="led_blinker",
        instances={"/power_supply": SheetInstance(page="2")}
    )
    power_sheet.projects.append(sheet_project)
    
    schematic.sheets.append(power_sheet)
    
    # Connect hierarchical sheet to main circuit
    schematic.wires.extend([
        Wire(
            points=CoordinatePointList([(240.0, 50.0), (250.0, 50.0)]),
            stroke=Stroke(width=0.152),
            uuid=UUID("hier-vcc-connection")
        ),
        Wire(
            points=CoordinatePointList([(240.0, 70.0), (250.0, 70.0)]),
            stroke=Stroke(width=0.152),
            uuid=UUID("hier-gnd-connection")
        )
    ])
    
    # Add hierarchical labels in main sheet
    schematic.hierarchical_labels.extend([
        HierarchicalLabel(
            text="VCC_OUT",
            shape=LabelShape.INPUT,
            position=Position(240.0, 50.0),
            effects=TextEffects(font=Font(size_height=1.0, size_width=1.0)),
            uuid=UUID("hier-vcc-label")
        ),
        HierarchicalLabel(
            text="GND",
            shape=LabelShape.PASSIVE,
            position=Position(240.0, 70.0),
            effects=TextEffects(font=Font(size_height=1.0, size_width=1.0)),
            uuid=UUID("hier-gnd-label")
        )
    ])
    
    print("[OK] Hierarchical design elements added")


def add_bus_connections(schematic):
    """Add bus connection example"""
    print("[INFO] Adding bus connection example...")
    
    # Add a simple data bus example
    schematic.buses.extend([
        Bus(
            points=CoordinatePointList([(30.0, 160.0), (100.0, 160.0)]),
            stroke=Stroke(width=0.254),
            uuid=UUID("data-bus-main")
        ),
        Bus(
            points=CoordinatePointList([(100.0, 160.0), (100.0, 180.0)]),
            stroke=Stroke(width=0.254),
            uuid=UUID("data-bus-branch")
        )
    ])
    
    # Add bus entries
    schematic.bus_entries.extend([
        BusEntry(
            position=Position(50.0, 160.0),
            size=(2.54, 2.54),
            stroke=Stroke(width=0.127),
            uuid=UUID("bus-entry-d0")
        ),
        BusEntry(
            position=Position(60.0, 160.0),
            size=(2.54, 2.54),
            stroke=Stroke(width=0.127),
            uuid=UUID("bus-entry-d1")
        )
    ])
    
    # Add individual data lines
    schematic.wires.extend([
        Wire(
            points=CoordinatePointList([(50.0, 162.54), (50.0, 170.0)]),
            stroke=Stroke(width=0.152),
            uuid=UUID("d0-line")
        ),
        Wire(
            points=CoordinatePointList([(60.0, 162.54), (60.0, 170.0)]),
            stroke=Stroke(width=0.152),
            uuid=UUID("d1-line")
        )
    ])
    
    # Add bus labels
    schematic.local_labels.extend([
        LocalLabel(
            text="DATA[7..0]",
            position=Position(65.0, 158.0),
            effects=TextEffects(font=Font(size_height=1.0, size_width=1.0)),
            uuid=UUID("data-bus-label")
        ),
        LocalLabel(
            text="D0",
            position=Position(50.0, 175.0),
            effects=TextEffects(font=Font(size_height=0.8, size_width=0.8)),
            uuid=UUID("d0-label")
        ),
        LocalLabel(
            text="D1",
            position=Position(60.0, 175.0),
            effects=TextEffects(font=Font(size_height=0.8, size_width=0.8)),
            uuid=UUID("d1-label")
        )
    ])
    
    print("[OK] Bus connections added")


def add_no_connect_examples(schematic):
    """Add no-connect markers for unused pins"""
    print("[INFO] Adding no-connect markers...")
    
    # Add no-connect markers for unused 555 pins
    schematic.no_connects.extend([
        NoConnect(
            position=Position(105.0, 85.0),  # Pin 5 (Control Voltage)
            uuid=UUID("nc-555-pin5")
        ),
        NoConnect(
            position=Position(135.0, 85.0),  # Pin 4 (Reset) - though usually connected to VCC
            uuid=UUID("nc-555-pin4")
        )
    ])
    
    print("[OK] No-connect markers added")


def save_and_test_schematic(schematic):
    """Save the schematic and test loading it back"""
    print("[INFO] Saving and testing schematic...")
    
    # Create temporary file for testing
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.kicad_sch', delete=False) as f:
        temp_path = f.name
    
    try:
        # Save schematic
        save_schematic(schematic, temp_path)
        print(f"[OK] Schematic saved to: {temp_path}")
        
        # Load it back
        loaded = load_schematic(temp_path)
        print("[OK] Schematic loaded successfully")
        
        # Verify some key elements
        print(f"[INFO] Loaded schematic statistics:")
        print(f"   - Title: {loaded.title_block.title}")
        print(f"   - Library symbols: {len(loaded.lib_symbols)}")
        print(f"   - Symbols: {len(loaded.symbols)}")
        print(f"   - Wires: {len(loaded.wires)}")
        print(f"   - Buses: {len(loaded.buses)}")
        print(f"   - Junctions: {len(loaded.junctions)}")
        print(f"   - Local labels: {len(loaded.local_labels)}")
        print(f"   - Global labels: {len(loaded.global_labels)}")
        print(f"   - Hierarchical labels: {len(loaded.hierarchical_labels)}")
        print(f"   - Text elements: {len(loaded.texts)}")
        print(f"   - Hierarchical sheets: {len(loaded.sheets)}")
        print(f"   - No connects: {len(loaded.no_connects)}")
        print(f"   - Bus entries: {len(loaded.bus_entries)}")
        print(f"   - Polylines: {len(loaded.polylines)}")
        
        # Test round-trip by saving again
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.kicad_sch', delete=False) as f2:
            temp_path2 = f2.name
        
        try:
            save_schematic(loaded, temp_path2)
            loaded2 = load_schematic(temp_path2)
            
            # Compare some key elements
            assert loaded2.title_block.title == loaded.title_block.title
            assert len(loaded2.symbols) == len(loaded.symbols)
            assert len(loaded2.wires) == len(loaded.wires)
            
            print("[OK] Round-trip test passed")
            
        finally:
            if os.path.exists(temp_path2):
                os.unlink(temp_path2)
        
        print(f"[OK] Example schematic creation completed successfully!")
        print(f"[INFO] Temporary file: {temp_path}")
        print("   (Note: Temporary file will be cleaned up)")
        
    except Exception as e:
        print(f"[ERROR] Error during schematic operations: {e}")
        raise
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def demonstrate_advanced_features():
    """Demonstrate advanced schematic features"""
    print("\n[INFO] Demonstrating advanced schematic features...")
    
    # Create advanced schematic
    advanced = create_basic_schematic("Advanced Features Demo", "KiCad Parser")
    
    # Demonstrate custom UUID usage
    custom_junction = Junction(
        position=Position(100.0, 100.0),
        diameter=0.36,
        color=(0.8, 0.2, 0.2, 1.0),  # Custom red color
        uuid=UUID("custom-uuid-12345678-1234-1234-1234-123456789abc")
    )
    advanced.junctions.append(custom_junction)
    
    # Demonstrate symbol with multiple properties and instances
    microcontroller = SchematicSymbol(
        library_id="MCU_ST_STM32F4:STM32F407VGTx",
        position=Position(150.0, 150.0),
        unit=1,
        in_bom=True,
        on_board=True,
        uuid=UUID("mcu-main-controller")
    )
    
    # Add comprehensive properties
    microcontroller.properties.extend([
        Property("Reference", "U2"),
        Property("Value", "STM32F407VGTx"),
        Property("Footprint", "Package_QFP:LQFP-100_14x14mm_P0.5mm"),
        Property("Datasheet", "https://www.st.com/resource/en/datasheet/stm32f407vg.pdf"),
        Property("Description", "32-bit ARM Cortex-M4 microcontroller, 168MHz, 1024kB Flash, 192kB RAM"),
        Property("Manufacturer", "STMicroelectronics"),
        Property("MPN", "STM32F407VGT6")
    ])
    
    # Add instance data for multiple projects
    mcu_project1 = SymbolProject(
        name="main_project",
        instances={
            "/": SymbolInstance(reference="U2", unit=1),
            "/cpu_sheet": SymbolInstance(reference="U2", unit=1)
        }
    )
    mcu_project2 = SymbolProject(
        name="test_project", 
        instances={"/": SymbolInstance(reference="IC1", unit=1)}
    )
    microcontroller.projects.extend([mcu_project1, mcu_project2])
    
    advanced.symbols.append(microcontroller)
    
    # Demonstrate complex hierarchical sheet with multiple pins
    cpu_sheet = HierarchicalSheet(
        position=Position(200.0, 50.0),
        size=(80.0, 60.0),
        stroke=Stroke(width=0.152, type=StrokeType.SOLID),
        fill_color=(0.9, 0.9, 0.9, 0.3),  # Light gray fill
        uuid=UUID("cpu-subsystem-sheet"),
        sheet_name="CPU Subsystem",
        file_name="cpu_subsystem.kicad_sch",
        fields_autoplaced=True
    )
    
    # Add multiple pins with different types
    pin_types = [
        ("CLK", PinElectricalType.INPUT),
        ("RESET_N", PinElectricalType.INPUT),
        ("DATA_OUT", PinElectricalType.OUTPUT),
        ("ADDR_BUS", PinElectricalType.OUTPUT),
        ("DATA_BUS", PinElectricalType.BIDIRECTIONAL),
        ("INT_REQ", PinElectricalType.TRI_STATE),
        ("TEST_POINT", PinElectricalType.PASSIVE)
    ]
    
    y_pos = 60.0
    for pin_name, pin_type in pin_types:
        cpu_sheet.pins.append(HierarchicalPin(
            name=pin_name,
            electrical_type=pin_type,
            position=Position(200.0, y_pos),
            effects=TextEffects(font=Font(size_height=0.8, size_width=0.8)),
            uuid=UUID(f"pin-{pin_name.lower().replace('_', '-')}")
        ))
        y_pos += 8.0
    
    # Add sheet instance with custom page number
    cpu_project = SheetProject(
        name="main_project",
        instances={"/cpu_subsystem": SheetInstance(page="CPU-1")}
    )
    cpu_sheet.projects.append(cpu_project)
    
    advanced.sheets.append(cpu_sheet)
    
    # Test the advanced schematic
    sexpr = advanced.to_sexpr()
    parsed = KiCadSchematic.from_sexpr(sexpr)
    
    print("[OK] Advanced features test passed")
    print(f"   - Custom colored junction: {parsed.junctions[0].color}")
    print(f"   - MCU with {len(parsed.symbols[0].properties)} properties")
    print(f"   - Hierarchical sheet with {len(parsed.sheets[0].pins)} pins")
    print(f"   - Sheet page number: {parsed.sheets[0].projects[0].instances['/cpu_subsystem'].page}")


def main():
    """Main example function"""
    print("[INFO] KiCad Schematic Parser Example")
    print("=" * 50)
    
    try:
        # Create comprehensive example schematic
        schematic = create_example_schematic()
        add_library_symbols(schematic)
        add_power_connections(schematic)
        add_main_circuit(schematic)
        add_circuit_connections(schematic)
        add_documentation(schematic)
        demonstrate_hierarchical_design(schematic)
        add_bus_connections(schematic)
        add_no_connect_examples(schematic)
        
        # Save and test the schematic
        save_and_test_schematic(schematic)
        
        # Demonstrate advanced features
        demonstrate_advanced_features()
        
        print("\n[OK] All schematic examples completed successfully!")
        print("\nThis example demonstrated:")
        print("- Creating schematics with create_basic_schematic()")
        print("- Adding library symbols to schematics")
        print("- Placing and connecting symbols")
        print("- Adding various label types (local, global, hierarchical)")
        print("- Creating hierarchical sheets with pins")
        print("- Using bus connections and entries")
        print("- Adding documentation text and graphics")
        print("- Working with junctions and no-connects")
        print("- File I/O operations (save/load)")
        print("- Round-trip testing")
        print("- Advanced features like custom colors and multi-project instances")
        
    except Exception as e:
        print(f"\n[ERROR] Error in schematic example: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())