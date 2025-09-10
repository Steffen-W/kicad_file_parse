"""
Unit tests for kicad_file module (File I/O operations)
"""

from pathlib import Path

import pytest

from kicad_parser import (
    KiCadSymbolLibrary,
    create_basic_symbol,
    detect_file_type,
    load_kicad_file,
    parse_kicad_file,
    save_kicad_file,
    serialize_kicad_object,
    validate_kicad_file,
)


class TestFileTypeDetection:
    """Test file type detection"""

    def test_detect_symbol_library(self, sample_symbol_library_content):
        """Test detecting symbol library files"""
        file_type = detect_file_type(sample_symbol_library_content)
        assert file_type == "symbol_library"

    def test_detect_footprint(self, sample_footprint_content):
        """Test detecting footprint files"""
        file_type = detect_file_type(sample_footprint_content)
        assert file_type == "footprint"

    def test_detect_unknown(self):
        """Test detecting unknown file types"""
        content = "(unknown_format test)"
        file_type = detect_file_type(content)
        assert file_type == "unknown"

    def test_detect_invalid_content(self):
        """Test detecting invalid content"""
        content = "not valid s-expression"
        file_type = detect_file_type(content)
        assert file_type == "unknown"


class TestSerialization:
    """Test object serialization"""

    def test_serialize_symbol_library(self, sample_library):
        """Test serializing symbol library"""
        result = serialize_kicad_object(sample_library)

        assert isinstance(result, str)
        assert "(kicad_symbol_lib" in result
        assert "(version 20211014)" in result
        assert "(generator pytest)" in result

    def test_serialize_symbol(self, sample_symbol):
        """Test serializing individual symbol"""
        result = serialize_kicad_object(sample_symbol)

        assert isinstance(result, str)
        assert "(symbol" in result
        assert "TestSymbol" in result
        assert "(property" in result


class TestParsing:
    """Test S-expression parsing"""

    def test_parse_symbol_library(self, sample_symbol_library_content):
        """Test parsing symbol library content"""
        library = parse_kicad_file(sample_symbol_library_content, KiCadSymbolLibrary)

        assert isinstance(library, KiCadSymbolLibrary)
        assert library.version == 20211014
        assert len(library.symbols) >= 1
        assert library.symbols[0].name == "TestSymbol"

    def test_parse_invalid_content(self):
        """Test parsing invalid content"""
        with pytest.raises(ValueError, match="Failed to parse"):
            parse_kicad_file("invalid content", KiCadSymbolLibrary)


class TestFileIO:
    """Test file input/output operations"""

    def test_save_and_load_symbol_library(self, sample_library, temp_file):
        """Test saving and loading symbol library"""
        # Create temporary file
        temp_path = temp_file(".kicad_sym")

        # Save library
        save_kicad_file(sample_library, temp_path)
        assert temp_path.exists()

        # Load library back
        loaded_library = load_kicad_file(temp_path)

        assert isinstance(loaded_library, KiCadSymbolLibrary)
        assert loaded_library.version == sample_library.version
        assert len(loaded_library.symbols) == len(sample_library.symbols)

        # Check first symbol
        original_symbol = sample_library.symbols[0]
        loaded_symbol = loaded_library.symbols[0]
        assert loaded_symbol.name == original_symbol.name

    def test_load_nonexistent_file(self):
        """Test loading non-existent file"""
        with pytest.raises(FileNotFoundError):
            load_kicad_file("nonexistent_file.kicad_sym")

    def test_validate_valid_file(self, sample_library, temp_file):
        """Test validating a valid file"""
        # Create and save valid file
        temp_path = temp_file(".kicad_sym")
        save_kicad_file(sample_library, temp_path)

        # Validate
        result = validate_kicad_file(temp_path)

        assert result["valid"] is True
        assert result["file_type"] == "symbol_library"
        assert result["object_type"] == "KiCadSymbolLibrary"
        assert result["error"] is None

    def test_validate_nonexistent_file(self):
        """Test validating non-existent file"""
        result = validate_kicad_file("nonexistent_file.kicad_sym")

        assert result["valid"] is False
        assert result["error"] is not None

    def test_validate_invalid_file(self, temp_file):
        """Test validating invalid file content"""
        # Create file with invalid content
        temp_path = temp_file(".kicad_sym", "invalid content")

        result = validate_kicad_file(temp_path)

        assert result["valid"] is False
        assert result["error"] is not None


class TestCompleteWorkflow:
    """Test complete file I/O workflow"""

    def test_create_modify_save_load_workflow(self, temp_file):
        """Test complete workflow: create -> modify -> save -> load"""
        # 1. Create library and symbol
        library = KiCadSymbolLibrary(version=20211014, generator="pytest")
        symbol = create_basic_symbol("WorkflowTest", "U", "Test")
        library.add_symbol(symbol)

        # 2. Modify symbol
        symbol.set_property("Description", "Test workflow")

        # 3. Save to file
        temp_path = temp_file(".kicad_sym")
        save_kicad_file(library, temp_path)

        # 4. Load from file
        loaded_library = load_kicad_file(temp_path)
        loaded_symbol = loaded_library.get_symbol("WorkflowTest")

        # 5. Verify modifications persisted
        assert loaded_symbol is not None
        desc_prop = loaded_symbol.get_property("Description")
        assert desc_prop is not None
        assert desc_prop.value == "Test workflow"

        # 6. Validate final file
        validation = validate_kicad_file(temp_path)
        assert validation["valid"] is True
