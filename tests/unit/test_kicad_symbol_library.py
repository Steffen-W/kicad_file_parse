"""
Tests for KiCadSymbolLibrary class functionality.

This module tests the KiCadSymbolLibrary class based on the README documentation
and the KiCad S-expression specification, covering library operations,
symbol management, and serialization.
"""

import pytest

from kicad_parser.kicad_common import UUID, Position
from kicad_parser.kicad_symbol import (
    KiCadSymbol,
    KiCadSymbolLibrary,
    PinElectricalType,
    PinGraphicStyle,
    SymbolPin,
    SymbolProperty,
)
from kicad_parser.sexpdata import Symbol


class TestKiCadSymbolLibrary:
    """Test cases for KiCadSymbolLibrary"""

    def test_library_creation_basic(self):
        """Test basic library creation with required attributes"""
        library = KiCadSymbolLibrary(version=20211014, generator="test-parser")

        assert library.version == 20211014
        assert library.generator == "test-parser"
        assert library.symbols == []
        assert len(library.symbols) == 0

    def test_library_creation_with_symbols(self):
        """Test library creation with initial symbols"""
        # Create a basic symbol
        symbol = KiCadSymbol(
            name="R_Generic",
            pin_numbers_hide=False,
            pin_names_hide=False,
            pin_names_offset=0.508,
            in_bom=True,
            on_board=True,
        )

        library = KiCadSymbolLibrary(
            version=20211014, generator="test-parser", symbols=[symbol]
        )

        assert len(library.symbols) == 1
        assert library.symbols[0].name == "R_Generic"

    def test_get_symbol_existing(self):
        """Test getting an existing symbol by name"""
        symbol1 = KiCadSymbol(name="R_Generic")
        symbol2 = KiCadSymbol(name="C_Generic")

        library = KiCadSymbolLibrary(
            version=20211014, generator="test-parser", symbols=[symbol1, symbol2]
        )

        found_symbol = library.get_symbol("C_Generic")
        assert found_symbol is not None
        assert found_symbol.name == "C_Generic"
        assert found_symbol == symbol2

    def test_get_symbol_nonexistent(self):
        """Test getting a non-existent symbol returns None"""
        symbol = KiCadSymbol(name="R_Generic")
        library = KiCadSymbolLibrary(
            version=20211014, generator="test-parser", symbols=[symbol]
        )

        found_symbol = library.get_symbol("NonExistent")
        assert found_symbol is None

    def test_add_symbol(self):
        """Test adding a symbol to the library"""
        library = KiCadSymbolLibrary(version=20211014, generator="test-parser")

        symbol = KiCadSymbol(name="L_Generic")
        library.add_symbol(symbol)

        assert len(library.symbols) == 1
        assert library.symbols[0].name == "L_Generic"

    def test_add_multiple_symbols(self):
        """Test adding multiple symbols to the library"""
        library = KiCadSymbolLibrary(version=20211014, generator="test-parser")

        symbols = [
            KiCadSymbol(name="R_Generic"),
            KiCadSymbol(name="C_Generic"),
            KiCadSymbol(name="L_Generic"),
        ]

        for symbol in symbols:
            library.add_symbol(symbol)

        assert len(library.symbols) == 3
        assert library.get_symbol("R_Generic") is not None
        assert library.get_symbol("C_Generic") is not None
        assert library.get_symbol("L_Generic") is not None

    def test_remove_symbol_existing(self):
        """Test removing an existing symbol from the library"""
        symbols = [KiCadSymbol(name="R_Generic"), KiCadSymbol(name="C_Generic")]

        library = KiCadSymbolLibrary(
            version=20211014, generator="test-parser", symbols=symbols
        )

        result = library.remove_symbol("R_Generic")

        assert result is True
        assert len(library.symbols) == 1
        assert library.get_symbol("R_Generic") is None
        assert library.get_symbol("C_Generic") is not None

    def test_remove_symbol_nonexistent(self):
        """Test removing a non-existent symbol returns False"""
        symbol = KiCadSymbol(name="R_Generic")
        library = KiCadSymbolLibrary(
            version=20211014, generator="test-parser", symbols=[symbol]
        )

        result = library.remove_symbol("NonExistent")

        assert result is False
        assert len(library.symbols) == 1

    def test_library_with_complex_symbols(self):
        """Test library with symbols containing pins and properties"""
        # Create a complex resistor symbol
        resistor = KiCadSymbol(
            name="R_Generic",
            pin_numbers_hide=False,
            pin_names_hide=False,
            pin_names_offset=0.508,
            in_bom=True,
            on_board=True,
        )

        # Add properties with required parameters
        resistor.properties = [
            SymbolProperty(key="Reference", value="R", id=0, position=Position(0, 0)),
            SymbolProperty(
                key="Value", value="R_Generic", id=1, position=Position(0, 0)
            ),
            SymbolProperty(key="Footprint", value="", id=2, position=Position(0, 0)),
            SymbolProperty(key="Datasheet", value="~", id=3, position=Position(0, 0)),
        ]

        # Add pins
        resistor.pins = [
            SymbolPin(
                electrical_type=PinElectricalType.PASSIVE,
                graphic_style=PinGraphicStyle.LINE,
                position=Position(-2.54, 0, 0),
                length=2.54,
                name="~",
                number="1",
            ),
            SymbolPin(
                electrical_type=PinElectricalType.PASSIVE,
                graphic_style=PinGraphicStyle.LINE,
                position=Position(2.54, 0, 0),
                length=2.54,
                name="~",
                number="2",
            ),
        ]

        library = KiCadSymbolLibrary(
            version=20211014, generator="test-parser", symbols=[resistor]
        )

        # Verify library contains the complex symbol
        assert len(library.symbols) == 1
        symbol = library.get_symbol("R_Generic")
        assert symbol is not None
        assert len(symbol.properties) == 4
        assert len(symbol.pins) == 2
        assert symbol.properties[0].key == "Reference"
        assert symbol.properties[0].value == "R"
        assert symbol.pins[0].electrical_type == PinElectricalType.PASSIVE
        assert symbol.pins[0].number == "1"

    def test_library_serialization_basic(self):
        """Test basic library to S-expression serialization"""
        library = KiCadSymbolLibrary(version=20211014, generator="test-parser")

        sexpr = library.to_sexpr()

        # Verify S-expression structure
        assert sexpr[0] == Symbol("kicad_symbol_lib")
        assert [Symbol("version"), 20211014] in sexpr
        assert [Symbol("generator"), Symbol("test-parser")] in sexpr

    def test_library_serialization_with_symbols(self):
        """Test library serialization with symbols"""
        symbol = KiCadSymbol(name="R_Generic")
        library = KiCadSymbolLibrary(
            version=20211014, generator="test-parser", symbols=[symbol]
        )

        sexpr = library.to_sexpr()

        # Find symbol in S-expression
        symbol_found = False
        for item in sexpr:
            if isinstance(item, list) and len(item) > 0 and item[0] == Symbol("symbol"):
                if len(item) > 1 and item[1] == "R_Generic":
                    symbol_found = True
                    break

        assert symbol_found, "Symbol should be present in S-expression"

    def test_library_parsing_basic(self):
        """Test parsing basic library from S-expression"""
        sexpr = [
            Symbol("kicad_symbol_lib"),
            [Symbol("version"), 20211014],
            [Symbol("generator"), "test-parser"],
        ]

        library = KiCadSymbolLibrary.from_sexpr(sexpr)

        assert library.version == 20211014
        assert library.generator == "test-parser"
        assert len(library.symbols) == 0

    def test_library_roundtrip_serialization(self):
        """Test that library can be serialized and parsed back without data loss"""
        original_library = KiCadSymbolLibrary(
            version=20211014, generator="test-roundtrip"
        )

        # Add a simple symbol
        symbol = KiCadSymbol(name="TestSymbol", in_bom=True, on_board=True)
        original_library.add_symbol(symbol)

        # Serialize to S-expression
        sexpr = original_library.to_sexpr()

        # Parse back from S-expression
        parsed_library = KiCadSymbolLibrary.from_sexpr(sexpr)

        # Verify data integrity
        assert parsed_library.version == original_library.version
        assert parsed_library.generator == original_library.generator
        assert len(parsed_library.symbols) == len(original_library.symbols)
        assert parsed_library.get_symbol("TestSymbol") is not None
        assert parsed_library.get_symbol("TestSymbol").name == "TestSymbol"

    def test_library_default_version(self):
        """Test library with default version"""
        library = KiCadSymbolLibrary(generator="test-parser")

        # Should have a reasonable default version
        assert isinstance(library.version, int)
        assert library.version >= 20211014  # Should be at least this version

    def test_library_empty_operations(self):
        """Test operations on empty library"""
        library = KiCadSymbolLibrary(version=20211014, generator="test-parser")

        # Test operations on empty library
        assert library.get_symbol("anything") is None
        assert library.remove_symbol("anything") is False
        assert len(library.symbols) == 0

        # Should still serialize properly
        sexpr = library.to_sexpr()
        assert sexpr[0] == Symbol("kicad_symbol_lib")

    def test_library_duplicate_symbol_names(self):
        """Test handling of duplicate symbol names"""
        symbol1 = KiCadSymbol(name="R_Generic")
        symbol2 = KiCadSymbol(name="R_Generic")  # Same name

        library = KiCadSymbolLibrary(version=20211014, generator="test-parser")
        library.add_symbol(symbol1)
        library.add_symbol(symbol2)

        # Implementation might prevent duplicates or allow them
        # Check if add_symbol prevents duplicates or allows them
        assert len(library.symbols) >= 1  # At least one should be present

        # get_symbol should return one of them (typically the first)
        found_symbol = library.get_symbol("R_Generic")
        assert found_symbol is not None
        assert found_symbol.name == "R_Generic"

    def test_library_case_sensitivity(self):
        """Test that symbol names are case sensitive"""
        symbol_lower = KiCadSymbol(name="r_generic")
        symbol_upper = KiCadSymbol(name="R_GENERIC")
        symbol_mixed = KiCadSymbol(name="R_Generic")

        library = KiCadSymbolLibrary(
            version=20211014,
            generator="test-parser",
            symbols=[symbol_lower, symbol_upper, symbol_mixed],
        )

        # All should be different symbols
        assert library.get_symbol("r_generic") is not None
        assert library.get_symbol("R_GENERIC") is not None
        assert library.get_symbol("R_Generic") is not None
        assert library.get_symbol("r_Generic") is None  # This variant doesn't exist
