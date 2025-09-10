"""
Pytest configuration and fixtures for kicad-parser tests
"""

from pathlib import Path

import pytest

from kicad_parser import (
    KiCadFootprint,
    KiCadSymbol,
    KiCadSymbolLibrary,
    Position,
    SymbolProperty,
    create_basic_footprint,
    create_basic_symbol,
)

# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture
def basic_position():
    """Basic position fixture"""
    return Position(1.0, 2.0, 90.0)


@pytest.fixture
def sample_symbol():
    """Sample symbol fixture"""
    return create_basic_symbol("TestSymbol", "U", "TestValue")


@pytest.fixture
def sample_library():
    """Sample symbol library fixture"""
    library = KiCadSymbolLibrary(version=20211014, generator="pytest")

    # Add a few test symbols
    for i in range(3):
        symbol = create_basic_symbol(f"Symbol_{i}", "U", f"Value_{i}")
        library.add_symbol(symbol)

    return library


@pytest.fixture
def sample_footprint():
    """Sample footprint fixture"""
    return create_basic_footprint("TestFootprint", "U**", "TestFP")


@pytest.fixture
def test_data_dir():
    """Test data directory fixture"""
    return TEST_DATA_DIR


@pytest.fixture
def sample_symbol_library_content():
    """Sample symbol library S-expression content"""
    return """(kicad_symbol_lib (version 20211014) (generator kicad_symbol_editor)
  (symbol "TestSymbol" (in_bom yes) (on_board yes)
    (property "Reference" "U" (id 0) (at 0 2.54) (effects (font (size 1.27 1.27))))
    (property "Value" "TestSymbol" (id 1) (at 0 -2.54) (effects (font (size 1.27 1.27))))
    (property "Footprint" "" (id 2) (at 0 -5.08) (effects (font (size 1.27 1.27))))
    (property "Datasheet" "" (id 3) (at 0 -7.62) (effects (font (size 1.27 1.27))))
  )
)"""


@pytest.fixture
def sample_footprint_content():
    """Sample footprint S-expression content"""
    return """(footprint "TestFootprint" (layer F.Cu)
  (at 0 0)
  (fp_text reference "REF**" (at 0 -3) (layer F.SilkS) (effects (font (size 1 1) (thickness 0.15))))
  (fp_text value "TestFootprint" (at 0 3) (layer F.Fab) (effects (font (size 1 1) (thickness 0.15))))
)"""


@pytest.fixture
def temp_file(tmp_path):
    """Temporary file fixture"""

    def _temp_file(suffix=".tmp", content=""):
        file = tmp_path / f"test_{suffix}"
        if content:
            file.write_text(content, encoding="utf-8")
        return file

    return _temp_file
