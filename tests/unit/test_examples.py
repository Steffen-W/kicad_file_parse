#!/usr/bin/env python3
"""
Tests for example functions in kicad_main.py to improve code coverage.

This test module specifically targets the example and demo functions that
were not covered by regular unit tests, improving overall coverage.
"""

import os
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import mock_open, patch

from kicad_parser import (
    CornerType,
    FootprintType,
    KiCadDesignRules,
    KiCadFootprint,
    KiCadSymbol,
    KiCadSymbolLibrary,
    KiCadWorksheet,
    PinElectricalType,
)

# Import the functions we want to test
from kicad_parser.kicad_main import (
    create_basic_design_rules,
    create_basic_worksheet,
    detect_kicad_file_type,
    example_footprint_creation,
    example_symbol_creation,
    integrate_with_original_code,
    load_any_kicad_file,
    main,
    parse_any_kicad_file,
    save_any_kicad_file,
)


class TestExampleFunctions(unittest.TestCase):
    """Test the example creation functions."""

    def test_example_symbol_creation(self):
        """Test the example_symbol_creation function."""
        library = example_symbol_creation()

        # Verify library structure
        self.assertIsInstance(library, KiCadSymbolLibrary)
        self.assertEqual(library.version, 20211014)
        self.assertEqual(library.generator, "kicad_parser")
        self.assertEqual(len(library.symbols), 1)

        # Verify resistor symbol
        resistor = library.symbols[0]
        self.assertEqual(resistor.name, "R_Generic")
        self.assertEqual(len(resistor.pins), 2)
        self.assertEqual(len(resistor.rectangles), 1)

        # Verify pins
        pin1, pin2 = resistor.pins
        self.assertEqual(pin1.electrical_type, PinElectricalType.PASSIVE)
        self.assertEqual(pin1.number, "1")
        self.assertEqual(pin2.electrical_type, PinElectricalType.PASSIVE)
        self.assertEqual(pin2.number, "2")

        # Verify properties
        ref_prop = resistor.get_property("Reference")
        val_prop = resistor.get_property("Value")
        self.assertIsNotNone(ref_prop)
        self.assertIsNotNone(val_prop)
        self.assertEqual(ref_prop.value, "R")
        self.assertEqual(val_prop.value, "R")

    def test_example_footprint_creation(self):
        """Test the example_footprint_creation function."""
        footprint = example_footprint_creation()

        # Verify footprint structure
        self.assertIsInstance(footprint, KiCadFootprint)
        self.assertEqual(footprint.library_link, "R_0805_2012Metric")
        self.assertEqual(len(footprint.pads), 2)
        self.assertEqual(len(footprint.rectangles), 1)
        self.assertEqual(len(footprint.texts), 2)

        # Verify attributes
        self.assertIsNotNone(footprint.attributes)
        self.assertEqual(footprint.attributes.type, FootprintType.SMD)
        self.assertFalse(footprint.attributes.exclude_from_bom)
        self.assertFalse(footprint.attributes.exclude_from_pos_files)

        # Verify pads
        pad1, pad2 = footprint.pads
        self.assertEqual(pad1.number, "1")
        self.assertEqual(pad2.number, "2")

    def test_create_basic_worksheet(self):
        """Test the create_basic_worksheet function."""
        worksheet = create_basic_worksheet("Test Title", "Test Company")

        # Verify worksheet structure
        self.assertIsInstance(worksheet, KiCadWorksheet)
        self.assertEqual(worksheet.version, 20220228)
        self.assertEqual(worksheet.generator, "kicad_parser")

        # Should have rectangle and text elements
        self.assertTrue(len(worksheet.rectangles) > 0)
        self.assertTrue(len(worksheet.texts) > 0)

        # Check for title and company text
        title_found = False
        company_found = False
        for text in worksheet.texts:
            if text.text == "Test Title":
                title_found = True
            if text.text == "Test Company":
                company_found = True

        self.assertTrue(title_found)
        self.assertTrue(company_found)

    def test_create_basic_design_rules(self):
        """Test the create_basic_design_rules function."""
        design_rules = create_basic_design_rules()

        # Verify design rules structure
        self.assertIsInstance(design_rules, KiCadDesignRules)
        self.assertEqual(design_rules.version, 1)

        # Should have at least one rule
        self.assertTrue(len(design_rules.rules) > 0)

    def test_detect_kicad_file_type(self):
        """Test the detect_kicad_file_type function."""
        # Test symbol library detection
        symbol_content = "(kicad_symbol_lib (version 20211014))"
        self.assertEqual(detect_kicad_file_type(symbol_content), "symbol_library")

        # Test footprint detection
        footprint_content = "(footprint R_0805 (version 20211014))"
        self.assertEqual(detect_kicad_file_type(footprint_content), "footprint")

        # Test unknown content
        unknown_content = "(unknown_format)"
        self.assertEqual(detect_kicad_file_type(unknown_content), "unknown")

    def test_parse_any_kicad_file(self):
        """Test the parse_any_kicad_file function."""
        # Test with symbol library
        symbol_content = """(kicad_symbol_lib
            (version 20211014)
            (generator kicad_parser)
        )"""

        result = parse_any_kicad_file(symbol_content)
        self.assertIsInstance(result, KiCadSymbolLibrary)

        # Test with unsupported type
        with self.assertRaises(ValueError):
            parse_any_kicad_file("(unknown_format)")


class TestFileOperations(unittest.TestCase):
    """Test file operation functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_file = os.path.join(self.temp_dir, "test.kicad_sym")

        # Create a simple symbol library content
        self.symbol_content = """(kicad_symbol_lib
            (version 20211014)
            (generator kicad_parser)
            (symbol "R" (property "Reference" "R"))
        )"""

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_any_kicad_file(self):
        """Test the load_any_kicad_file function."""
        # Write test file
        with open(self.temp_file, "w") as f:
            f.write(self.symbol_content)

        # Load and verify
        result = load_any_kicad_file(self.temp_file)
        self.assertIsInstance(result, KiCadSymbolLibrary)

    def test_save_any_kicad_file(self):
        """Test the save_any_kicad_file function."""
        # Create a library
        library = KiCadSymbolLibrary(version=20211014, generator="test")

        # Save and verify file exists
        save_any_kicad_file(library, self.temp_file)
        self.assertTrue(os.path.exists(self.temp_file))

        # Verify content
        with open(self.temp_file, "r") as f:
            content = f.read()
        self.assertIn("kicad_symbol_lib", content)


class TestDemoFunctions(unittest.TestCase):
    """Test demo and main functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("sys.stdout", new_callable=StringIO)
    def test_main_function_basic_flow(self, mock_stdout):
        """Test the main demo function basic flow."""
        # Mock the file operations to avoid dependency on actual files
        with patch("kicad_parser.kicad_main.load_symbol_library") as mock_load:
            # Configure mock to raise FileNotFoundError
            mock_load.side_effect = FileNotFoundError("Test file not found")

            # Call main function
            main()

            # Verify output contains expected messages
            output = mock_stdout.getvalue()
            self.assertIn("KiCad S-Expression Parser Demo", output)
            self.assertIn("Creating symbol library", output)
            self.assertIn("Creating footprint", output)
            self.assertIn("File operations example", output)
            self.assertIn("Test file not found - skipping", output)
            self.assertIn("Demo completed successfully", output)

    @patch("sys.stdout", new_callable=StringIO)
    def test_main_function_with_successful_file_operations(self, mock_stdout):
        """Test main function when file operations succeed."""
        # Create a mock symbol library
        mock_library = KiCadSymbolLibrary(version=20211014)
        mock_symbol = KiCadSymbol(name="TestSymbol")
        mock_symbol.set_property("Reference", "U")
        mock_library.add_symbol(mock_symbol)

        # Mock the file operations
        with patch(
            "kicad_parser.kicad_main.load_symbol_library", return_value=mock_library
        ), patch("kicad_parser.kicad_main.save_symbol_library") as mock_save:

            # Call main function
            main()

            # Verify output
            output = mock_stdout.getvalue()
            self.assertIn("Loaded library with 1 symbol(s)", output)
            self.assertIn("First symbol: TestSymbol", output)
            self.assertIn("Original Reference: U", output)
            self.assertIn("Modified Reference: IC", output)

            # Verify save was called
            mock_save.assert_called_once()

    @patch("sys.stdout", new_callable=StringIO)
    def test_integrate_with_original_code_function(self, mock_stdout):
        """Test the integrate_with_original_code demo function."""
        # Create a mock symbol library
        mock_library = KiCadSymbolLibrary(version=20211014)
        mock_symbol = KiCadSymbol(name="TestSymbol")
        mock_library.add_symbol(mock_symbol)

        # Mock all the file operations
        with patch(
            "kicad_parser.kicad_main.load_kicad_file", return_value=mock_library
        ), patch("kicad_parser.kicad_main.convert_file") as mock_convert, patch(
            "kicad_parser.kicad_main.save_kicad_file"
        ) as mock_save:

            # Call the function
            integrate_with_original_code()

            # Verify output
            output = mock_stdout.getvalue()
            self.assertIn("Unified file API example", output)
            self.assertIn("Library loaded with 1 symbols", output)
            self.assertIn("Output files created", output)

            # Verify function calls
            mock_convert.assert_called_once()
            mock_save.assert_called_once()

    @patch("sys.stdout", new_callable=StringIO)
    def test_integrate_with_original_code_file_error(self, mock_stdout):
        """Test integrate_with_original_code when file operations fail."""
        # Mock to raise an exception
        with patch(
            "kicad_parser.kicad_main.load_kicad_file",
            side_effect=FileNotFoundError("File not found"),
        ):

            # Call the function
            integrate_with_original_code()

            # Verify error handling
            output = mock_stdout.getvalue()
            self.assertIn("API example failed", output)

    @patch("sys.stdout", new_callable=StringIO)
    def test_main_function_with_general_error(self, mock_stdout):
        """Test main function handles general errors gracefully."""
        # Mock to raise a general exception during symbol property access
        mock_library = KiCadSymbolLibrary(version=20211014)
        mock_symbol = KiCadSymbol(name="TestSymbol")

        # Mock get_property to raise an exception
        with patch.object(
            mock_symbol, "get_property", side_effect=Exception("Test error")
        ):
            mock_library.add_symbol(mock_symbol)

            with patch(
                "kicad_parser.kicad_main.load_symbol_library", return_value=mock_library
            ):
                # Call main function
                main()

                # Verify error handling
                output = mock_stdout.getvalue()
                self.assertIn("Error in file operations: Test error", output)


if __name__ == "__main__":
    unittest.main()
