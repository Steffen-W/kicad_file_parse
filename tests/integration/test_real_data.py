"""
Integration tests with real KiCad data files
"""

from pathlib import Path

import pytest

from kicad_parser import (
    detect_file_type,
    load_kicad_file,
    load_symbol_library,
    save_symbol_library,
    validate_kicad_file,
)


class TestRealDataFiles:
    """Test with actual KiCad data files"""

    @pytest.fixture
    def real_data_dir(self):
        """Real test data directory"""
        return Path(__file__).parent.parent.parent / "examples" / "test_data"

    def test_load_real_symbol_library(self, real_data_dir):
        """Test loading real symbol library file"""
        symbol_file = real_data_dir / "small.kicad_sym"

        if not symbol_file.exists():
            pytest.skip("Real test data not available")

        # Load the library
        library = load_symbol_library(symbol_file)

        assert library is not None
        assert len(library.symbols) > 0

        # Check first symbol has basic properties
        symbol = library.symbols[0]
        assert symbol.name is not None
        assert len(symbol.properties) > 0

        # Check required properties exist
        ref_prop = symbol.get_property("Reference")
        val_prop = symbol.get_property("Value")

        assert ref_prop is not None
        assert val_prop is not None

    def test_validate_real_files(self, real_data_dir):
        """Test validating real KiCad files"""
        if not real_data_dir.exists():
            pytest.skip("Real test data directory not available")

        # Test all .kicad_sym files
        for file_path in real_data_dir.glob("*.kicad_sym"):
            result = validate_kicad_file(file_path)

            assert (
                result["valid"] is True
            ), f"File {file_path.name} failed validation: {result['error']}"
            assert result["file_type"] == "symbol_library"
            assert result["object_type"] == "KiCadSymbolLibrary"

        # Test all .kicad_mod files
        for file_path in real_data_dir.glob("*.kicad_mod"):
            result = validate_kicad_file(file_path)

            assert (
                result["valid"] is True
            ), f"File {file_path.name} failed validation: {result['error']}"
            assert result["file_type"] == "footprint"
            assert result["object_type"] == "KiCadFootprint"

    def test_detect_real_file_types(self, real_data_dir):
        """Test file type detection with real files"""
        if not real_data_dir.exists():
            pytest.skip("Real test data directory not available")

        # Test symbol library files
        for file_path in real_data_dir.glob("*.kicad_sym"):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            file_type = detect_file_type(content)
            assert (
                file_type == "symbol_library"
            ), f"Wrong type detected for {file_path.name}"

        # Test footprint files
        for file_path in real_data_dir.glob("*.kicad_mod"):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            file_type = detect_file_type(content)
            assert file_type == "footprint", f"Wrong type detected for {file_path.name}"

    def test_round_trip_real_data(self, real_data_dir, tmp_path):
        """Test round-trip: load -> save -> load with real data"""
        symbol_file = real_data_dir / "small.kicad_sym"

        if not symbol_file.exists():
            pytest.skip("Real test data not available")

        # Load original
        original_library = load_symbol_library(symbol_file)

        # Save to temporary file
        temp_file = tmp_path / "temp_output.kicad_sym"
        save_symbol_library(original_library, temp_file)

        # Load saved version
        saved_library = load_symbol_library(temp_file)

        # Compare libraries
        assert len(saved_library.symbols) == len(original_library.symbols)
        assert saved_library.version == original_library.version

        # Compare first symbol in detail
        if len(original_library.symbols) > 0:
            orig_symbol = original_library.symbols[0]
            saved_symbol = saved_library.symbols[0]

            assert saved_symbol.name == orig_symbol.name
            assert len(saved_symbol.properties) == len(orig_symbol.properties)

            # Check key properties match
            for orig_prop in orig_symbol.properties:
                saved_prop = saved_symbol.get_property(orig_prop.key)
                assert (
                    saved_prop is not None
                ), f"Property {orig_prop.key} missing in saved symbol"
                assert (
                    saved_prop.value == orig_prop.value
                ), f"Property {orig_prop.key} value mismatch"

    def test_modify_real_data(self, real_data_dir, tmp_path):
        """Test modifying real data and saving"""
        symbol_file = real_data_dir / "small.kicad_sym"

        if not symbol_file.exists():
            pytest.skip("Real test data not available")

        # Load library
        library = load_symbol_library(symbol_file)

        if len(library.symbols) == 0:
            pytest.skip("No symbols in test library")

        # Modify first symbol
        symbol = library.symbols[0]
        original_ref = symbol.get_property("Reference")
        original_ref_value = original_ref.value if original_ref else "U"

        # Change reference
        symbol.set_property("Reference", "IC_MODIFIED")

        # Add new property
        symbol.set_property("TestModification", "pytest_integration_test")

        # Save modified version
        modified_file = tmp_path / "modified.kicad_sym"
        save_symbol_library(library, modified_file)

        # Load and verify modifications
        modified_library = load_symbol_library(modified_file)
        modified_symbol = modified_library.symbols[0]

        ref_prop = modified_symbol.get_property("Reference")
        test_prop = modified_symbol.get_property("TestModification")

        assert ref_prop.value == "IC_MODIFIED"
        assert test_prop is not None
        assert test_prop.value == "pytest_integration_test"

        # Validate modified file
        validation = validate_kicad_file(modified_file)
        assert validation["valid"] is True


class TestComplexRealDataOperations:
    """Test complex operations with real data"""

    @pytest.fixture
    def real_data_dir(self):
        """Real test data directory"""
        return Path(__file__).parent.parent.parent / "examples" / "test_data"

    def test_merge_libraries(self, real_data_dir, tmp_path):
        """Test merging multiple symbol libraries"""
        if not real_data_dir.exists():
            pytest.skip("Real test data directory not available")

        # Find multiple symbol files
        symbol_files = list(real_data_dir.glob("*.kicad_sym"))

        if len(symbol_files) < 1:
            pytest.skip("Not enough symbol files for merge test")

        # Create new library for merging
        merged_library = load_symbol_library(symbol_files[0])
        original_count = len(merged_library.symbols)

        # If we have more files, merge them
        for file_path in symbol_files[1:]:
            try:
                other_library = load_symbol_library(file_path)

                # Add symbols with unique names
                for i, symbol in enumerate(other_library.symbols):
                    # Rename to avoid conflicts
                    symbol.name = f"{symbol.name}_merged_{file_path.stem}_{i}"
                    merged_library.add_symbol(symbol)

            except Exception as e:
                # Skip files that can't be loaded
                print(f"Skipping {file_path}: {e}")
                continue

        # Save merged library
        merged_file = tmp_path / "merged_library.kicad_sym"
        save_symbol_library(merged_library, merged_file)

        # Validate merged library
        validation = validate_kicad_file(merged_file)
        assert validation["valid"] is True

        # Load and check merged library
        final_library = load_symbol_library(merged_file)
        assert len(final_library.symbols) >= original_count
