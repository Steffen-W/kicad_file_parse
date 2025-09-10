"""
Tests for version parsing in KiCad files with different version numbers
"""

import pytest

from kicad_parser.kicad_file import parse_kicad_file
from kicad_parser.kicad_symbol import KiCadSymbolLibrary
from kicad_parser.sexpdata import Symbol, loads


class TestVersionParsing:
    """Test version parsing for different version numbers"""

    def test_version_20211014(self):
        """Test parsing with standard version 20211014"""
        content = """
        (kicad_symbol_lib (version 20211014) (generator kicad_symbol_editor)
          (symbol "TestSymbol" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)
            (property "Reference" "U" (id 0) (at 0 2.54 0)
              (effects (font (size 1.27 1.27)) (justify left))
            )
          )
        )
        """
        library = parse_kicad_file(content, KiCadSymbolLibrary)
        assert library.version == 20211014

    def test_version_20220914(self):
        """Test parsing with newer version 20220914"""
        content = """
        (kicad_symbol_lib (version 20220914) (generator kicad_symbol_editor)
          (symbol "TestSymbol" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)
            (property "Reference" "U" (id 0) (at 0 2.54 0)
              (effects (font (size 1.27 1.27)) (justify left))
            )
          )
        )
        """
        library = parse_kicad_file(content, KiCadSymbolLibrary)
        assert library.version == 20220914

    def test_version_older_20201216(self):
        """Test parsing with older version 20201216"""
        content = """
        (kicad_symbol_lib (version 20201216) (generator kicad_symbol_editor)
          (symbol "TestSymbol" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)
            (property "Reference" "U" (id 0) (at 0 2.54 0)
              (effects (font (size 1.27 1.27)) (justify left))
            )
          )
        )
        """
        library = parse_kicad_file(content, KiCadSymbolLibrary)
        assert library.version == 20201216

    def test_version_very_old_format(self):
        """Test parsing with very old version format"""
        content = """
        (kicad_symbol_lib (version 20180914) (generator kicad_symbol_editor)
          (symbol "TestSymbol" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)
            (property "Reference" "U" (id 0) (at 0 2.54 0)
              (effects (font (size 1.27 1.27)) (justify left))
            )
          )
        )
        """
        library = parse_kicad_file(content, KiCadSymbolLibrary)
        assert library.version == 20180914

    def test_version_future_format(self):
        """Test parsing with hypothetical future version"""
        content = """
        (kicad_symbol_lib (version 20251201) (generator kicad_symbol_editor)
          (symbol "TestSymbol" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)
            (property "Reference" "U" (id 0) (at 0 2.54 0)
              (effects (font (size 1.27 1.27)) (justify left))
            )
          )
        )
        """
        library = parse_kicad_file(content, KiCadSymbolLibrary)
        assert library.version == 20251201

    def test_version_missing_uses_default(self):
        """Test that missing version uses default value"""
        content = """
        (kicad_symbol_lib (generator kicad_symbol_editor)
          (symbol "TestSymbol" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)
            (property "Reference" "U" (id 0) (at 0 2.54 0)
              (effects (font (size 1.27 1.27)) (justify left))
            )
          )
        )
        """
        library = parse_kicad_file(content, KiCadSymbolLibrary)
        assert library.version == 20211014  # Should use default

    def test_version_invalid_string_uses_default(self):
        """Test that invalid version string falls back to default"""
        content = """
        (kicad_symbol_lib (version "invalid") (generator kicad_symbol_editor)
          (symbol "TestSymbol" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)
            (property "Reference" "U" (id 0) (at 0 2.54 0)
              (effects (font (size 1.27 1.27)) (justify left))
            )
          )
        )
        """
        library = parse_kicad_file(content, KiCadSymbolLibrary)
        assert (
            library.version == 20211014
        )  # Should fall back to default due to safe_int

    def test_version_float_gets_truncated(self):
        """Test that float version gets truncated to int"""
        content = """
        (kicad_symbol_lib (version 20211014.5) (generator kicad_symbol_editor)
          (symbol "TestSymbol" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)
            (property "Reference" "U" (id 0) (at 0 2.54 0)
              (effects (font (size 1.27 1.27)) (justify left))
            )
          )
        )
        """
        library = parse_kicad_file(content, KiCadSymbolLibrary)
        assert library.version == 20211014  # Float should be truncated

    def test_version_zero(self):
        """Test parsing with version 0"""
        content = """
        (kicad_symbol_lib (version 0) (generator kicad_symbol_editor)
          (symbol "TestSymbol" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)
            (property "Reference" "U" (id 0) (at 0 2.54 0)
              (effects (font (size 1.27 1.27)) (justify left))
            )
          )
        )
        """
        library = parse_kicad_file(content, KiCadSymbolLibrary)
        assert library.version == 0

    def test_version_negative_number(self):
        """Test parsing with negative version (edge case)"""
        content = """
        (kicad_symbol_lib (version -1) (generator kicad_symbol_editor)
          (symbol "TestSymbol" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)
            (property "Reference" "U" (id 0) (at 0 2.54 0)
              (effects (font (size 1.27 1.27)) (justify left))
            )
          )
        )
        """
        library = parse_kicad_file(content, KiCadSymbolLibrary)
        assert library.version == -1

    def test_version_large_number(self):
        """Test parsing with very large version number"""
        content = """
        (kicad_symbol_lib (version 999999999) (generator kicad_symbol_editor)
          (symbol "TestSymbol" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)
            (property "Reference" "U" (id 0) (at 0 2.54 0)
              (effects (font (size 1.27 1.27)) (justify left))
            )
          )
        )
        """
        library = parse_kicad_file(content, KiCadSymbolLibrary)
        assert library.version == 999999999


class TestVersionParsingDirectSExpr:
    """Test version parsing directly with S-expressions"""

    def test_direct_sexpr_parsing_different_versions(self):
        """Test direct S-expression parsing with different versions"""
        from kicad_parser.kicad_common import SExprParser

        test_cases = [
            ([Symbol("root"), [Symbol("version"), 20211014]], 20211014),
            ([Symbol("root"), [Symbol("version"), 20220914]], 20220914),
            ([Symbol("root"), [Symbol("version"), 12345]], 12345),
            ([Symbol("root"), [Symbol("version"), 0]], 0),
            ([Symbol("root")], 20211014),  # Missing version, should use default
        ]

        for sexpr, expected_version in test_cases:
            result = SExprParser.get_required_int(sexpr, "version", default=20211014)
            assert (
                result == expected_version
            ), f"Failed for {sexpr}: got {result}, expected {expected_version}"

    def test_safe_int_conversion_edge_cases(self):
        """Test safe_int conversion with various edge cases"""
        from kicad_parser.kicad_common import SExprParser

        test_cases = [
            (20211014, 20211014),  # Normal int
            ("20220914", 20220914),  # String number
            (20211014.9, 20211014),  # Float truncation
            ("invalid", 123),  # Invalid string, uses default
            (None, 456),  # None, uses default
            ("", 789),  # Empty string, uses default
        ]

        for value, default in test_cases:
            result = SExprParser.safe_int(value, default)
            expected = (
                default
                if isinstance(value, str) and value not in ["20220914"] or value is None
                else int(float(str(value)))
            )
            if isinstance(value, str) and value in ["invalid", ""]:
                expected = default
            elif value is None:
                expected = default
            else:
                try:
                    expected = int(float(str(value)))
                except (ValueError, TypeError):
                    expected = default

            assert (
                result == expected
            ), f"safe_int({value}, {default}) = {result}, expected {expected}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
