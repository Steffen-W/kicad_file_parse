"""
Comprehensive tests for SExprParser class functionality
"""

import pytest

from kicad_parser.kicad_common import Position, SExprParser
from kicad_parser.sexpdata import Symbol


class TestSExprParserBasics:
    """Test basic S-expression parsing functionality"""

    def test_find_token_simple(self):
        """Test finding a simple token"""
        sexpr = [Symbol("root"), [Symbol("target"), "value"]]
        token = SExprParser.find_token(sexpr, "target")
        assert token == [Symbol("target"), "value"]

    def test_find_token_not_found(self):
        """Test behavior when token is not found"""
        sexpr = [Symbol("root"), [Symbol("other"), "value"]]
        token = SExprParser.find_token(sexpr, "missing")
        assert token is None

    def test_find_token_nested(self):
        """Test finding token in nested structure"""
        sexpr = [
            Symbol("root"),
            [Symbol("level1"), [Symbol("target"), "nested_value"]],
            [Symbol("target"), "top_level"],
        ]
        token = SExprParser.find_token(sexpr, "target")
        assert token == [Symbol("target"), "top_level"]  # Should find first occurrence

    def test_find_all_tokens(self):
        """Test finding all occurrences of a token"""
        sexpr = [
            Symbol("root"),
            [Symbol("item"), "first"],
            [Symbol("item"), "second"],
            [Symbol("other"), "value"],
        ]
        tokens = SExprParser.find_all_tokens(sexpr, "item")
        assert len(tokens) == 2
        assert tokens[0] == [Symbol("item"), "first"]
        assert tokens[1] == [Symbol("item"), "second"]

    def test_get_value_by_index(self):
        """Test getting values by index"""
        token = [Symbol("test"), "value1", "value2", 42]
        assert SExprParser.get_value(token, 0) == Symbol("test")
        assert SExprParser.get_value(token, 1) == "value1"
        assert SExprParser.get_value(token, 2) == "value2"
        assert SExprParser.get_value(token, 3) == 42

    def test_get_value_out_of_bounds(self):
        """Test getting value with index out of bounds"""
        token = [Symbol("test"), "value"]
        assert SExprParser.get_value(token, 5) is None
        assert SExprParser.get_value(token, 5, "default") == "default"

    def test_has_symbol(self):
        """Test checking for symbol presence"""
        sexpr = [Symbol("root"), Symbol("flag1"), [Symbol("nested")], Symbol("flag2")]
        assert SExprParser.has_symbol(sexpr, "flag1") is True
        assert SExprParser.has_symbol(sexpr, "flag2") is True
        assert SExprParser.has_symbol(sexpr, "missing") is False


class TestSExprParserSafeConversions:
    """Test safe type conversion functions"""

    def test_safe_float_valid_values(self):
        """Test safe_float with valid numeric values"""
        assert SExprParser.safe_float(42, 0.0) == 42.0
        assert SExprParser.safe_float("3.14", 0.0) == 3.14
        assert SExprParser.safe_float(-1.5, 0.0) == -1.5

    def test_safe_float_invalid_values(self):
        """Test safe_float with invalid values returns default"""
        assert SExprParser.safe_float("invalid", 1.5) == 1.5
        assert SExprParser.safe_float(None, 2.0) == 2.0
        assert SExprParser.safe_float("", 3.0) == 3.0

    def test_safe_int_valid_values(self):
        """Test safe_int with valid numeric values"""
        assert SExprParser.safe_int(42, 0) == 42
        assert SExprParser.safe_int("123", 0) == 123
        assert SExprParser.safe_int(-5, 0) == -5
        assert SExprParser.safe_int(3.14, 0) == 3  # Truncation

    def test_safe_int_invalid_values(self):
        """Test safe_int with invalid values returns default"""
        assert SExprParser.safe_int("invalid", 10) == 10
        assert SExprParser.safe_int(None, 20) == 20
        assert SExprParser.safe_int("", 30) == 30

    def test_safe_str_conversion(self):
        """Test safe_str conversion"""
        assert SExprParser.safe_str("text", "default") == "text"
        assert SExprParser.safe_str(42, "default") == "42"
        assert SExprParser.safe_str(None, "default") == "default"


class TestSExprParserOptionalGetters:
    """Test optional getter functions"""

    def test_get_optional_str(self):
        """Test optional string getter"""
        sexpr = [Symbol("root"), [Symbol("text"), "hello"]]
        assert SExprParser.get_optional_str(sexpr, "text") == "hello"
        assert SExprParser.get_optional_str(sexpr, "missing") is None

    def test_get_optional_float(self):
        """Test optional float getter"""
        sexpr = [Symbol("root"), [Symbol("value"), 3.14]]
        assert SExprParser.get_optional_float(sexpr, "value") == 3.14
        assert SExprParser.get_optional_float(sexpr, "missing") is None

    def test_get_optional_int(self):
        """Test optional int getter"""
        sexpr = [Symbol("root"), [Symbol("count"), 42]]
        assert SExprParser.get_optional_int(sexpr, "count") == 42
        assert SExprParser.get_optional_int(sexpr, "missing") is None

    def test_get_optional_position(self):
        """Test optional position getter"""
        sexpr = [Symbol("root"), [Symbol("pos"), 1.0, 2.0]]
        pos = SExprParser.get_optional_position(sexpr, "pos")
        assert pos is not None
        assert pos.x == 1.0
        assert pos.y == 2.0
        assert SExprParser.get_optional_position(sexpr, "missing") is None


class TestSExprParserRequiredGetters:
    """Test required getter functions with defaults"""

    def test_get_required_str_with_token(self):
        """Test required string getter when token exists"""
        sexpr = [Symbol("root"), [Symbol("name"), "test"]]
        assert SExprParser.get_required_str(sexpr, "name") == "test"

    def test_get_required_str_missing_no_default(self):
        """Test required string getter raises when missing and no default"""
        sexpr = [Symbol("root")]
        with pytest.raises(ValueError, match="Required token 'missing' not found"):
            SExprParser.get_required_str(sexpr, "missing")

    def test_get_required_str_missing_with_default(self):
        """Test required string getter returns default when missing"""
        sexpr = [Symbol("root")]
        assert (
            SExprParser.get_required_str(sexpr, "missing", default="fallback")
            == "fallback"
        )

    def test_get_required_float_with_token(self):
        """Test required float getter when token exists"""
        sexpr = [Symbol("root"), [Symbol("value"), 2.5]]
        assert SExprParser.get_required_float(sexpr, "value") == 2.5

    def test_get_required_float_missing_no_default(self):
        """Test required float getter raises when missing and no default"""
        sexpr = [Symbol("root")]
        with pytest.raises(ValueError, match="Required token 'missing' not found"):
            SExprParser.get_required_float(sexpr, "missing")

    def test_get_required_float_missing_with_default(self):
        """Test required float getter returns default when missing"""
        sexpr = [Symbol("root")]
        assert SExprParser.get_required_float(sexpr, "missing", default=1.5) == 1.5

    def test_get_required_int_with_token(self):
        """Test required int getter when token exists"""
        sexpr = [Symbol("root"), [Symbol("count"), 10]]
        assert SExprParser.get_required_int(sexpr, "count") == 10

    def test_get_required_int_missing_no_default(self):
        """Test required int getter raises when missing and no default"""
        sexpr = [Symbol("root")]
        with pytest.raises(ValueError, match="Required token 'missing' not found"):
            SExprParser.get_required_int(sexpr, "missing")

    def test_get_required_int_missing_with_default(self):
        """Test required int getter returns default when missing"""
        sexpr = [Symbol("root")]
        assert SExprParser.get_required_int(sexpr, "missing", default=42) == 42

    def test_get_required_position_with_token(self):
        """Test required position getter when token exists"""
        sexpr = [Symbol("root"), [Symbol("at"), 5.0, 10.0]]
        pos = SExprParser.get_required_position(sexpr, "at")
        assert pos.x == 5.0
        assert pos.y == 10.0

    def test_get_required_position_missing_no_default(self):
        """Test required position getter raises when missing and no default"""
        sexpr = [Symbol("root")]
        with pytest.raises(ValueError, match="Required token 'missing' not found"):
            SExprParser.get_required_position(sexpr, "missing")

    def test_get_required_position_missing_with_default(self):
        """Test required position getter returns default when missing"""
        sexpr = [Symbol("root")]
        default_pos = Position(3.0, 4.0)
        pos = SExprParser.get_required_position(sexpr, "missing", default=default_pos)
        assert pos == default_pos


class TestSExprParserPositionUtilities:
    """Test position-related utility functions"""

    def test_get_position_with_default(self):
        """Test position getter with default values"""
        sexpr = [Symbol("root"), [Symbol("pos"), 1.5, 2.5]]
        pos = SExprParser.get_position_with_default(sexpr, "pos")
        assert pos.x == 1.5
        assert pos.y == 2.5

    def test_get_position_with_default_missing(self):
        """Test position getter with missing token uses default"""
        sexpr = [Symbol("root")]
        pos = SExprParser.get_position_with_default(sexpr, "missing", 10.0, 20.0)
        assert pos.x == 10.0
        assert pos.y == 20.0

    def test_get_position_with_default_partial(self):
        """Test position getter with partially invalid data"""
        sexpr = [Symbol("root"), [Symbol("pos"), "invalid"]]
        pos = SExprParser.get_position_with_default(sexpr, "pos", 1.0, 2.0)
        assert pos.x == 1.0  # Falls back to default due to invalid data
        assert pos.y == 2.0


class TestSExprParserTextNormalization:
    """Test text normalization functionality"""

    def test_normalize_text_content_basic(self):
        """Test basic text normalization"""
        assert SExprParser.normalize_text_content("hello") == "hello"
        assert SExprParser.normalize_text_content("") == ""

    def test_normalize_text_content_overbar(self):
        """Test overbar notation handling"""
        # Test single character overbar
        assert "~" in SExprParser.normalize_text_content("~A")
        # Test multi-character overbar
        assert "{" in SExprParser.normalize_text_content("{ABC}")


class TestSExprParserSafeGetters:
    """Test position-based safe getter functions"""

    def test_safe_get_str(self):
        """Test safe string getter by index"""
        from kicad_parser.kicad_common import SExprParser

        sexpr = [Symbol("net"), 42, "GND", "extra"]
        assert SExprParser.safe_get_str(sexpr, 2, "default") == "GND"
        assert (
            SExprParser.safe_get_str(sexpr, 10, "default") == "default"
        )  # Out of bounds
        assert SExprParser.safe_get_str(sexpr, 1, "default") == "42"  # Number to string

    def test_safe_get_int(self):
        """Test safe int getter by index"""
        from kicad_parser.kicad_common import SExprParser

        sexpr = [Symbol("net"), 42, "123", 3.14]
        assert SExprParser.safe_get_int(sexpr, 1, 0) == 42
        assert SExprParser.safe_get_int(sexpr, 2, 0) == 123  # String number
        assert SExprParser.safe_get_int(sexpr, 3, 0) == 3  # Float truncation
        assert SExprParser.safe_get_int(sexpr, 10, 99) == 99  # Out of bounds

    def test_safe_get_float(self):
        """Test safe float getter by index"""
        from kicad_parser.kicad_common import SExprParser

        sexpr = [Symbol("value"), 42, "3.14", "invalid"]
        assert SExprParser.safe_get_float(sexpr, 1, 0.0) == 42.0
        assert SExprParser.safe_get_float(sexpr, 2, 0.0) == 3.14
        assert SExprParser.safe_get_float(sexpr, 3, 1.5) == 1.5  # Invalid string
        assert SExprParser.safe_get_float(sexpr, 10, 2.5) == 2.5  # Out of bounds

    def test_safe_get_edge_cases(self):
        """Test safe getters with edge cases"""
        from kicad_parser.kicad_common import SExprParser

        # Empty list
        empty_sexpr = []
        assert SExprParser.safe_get_str(empty_sexpr, 1, "default") == "default"
        assert SExprParser.safe_get_int(empty_sexpr, 1, 42) == 42
        assert SExprParser.safe_get_float(empty_sexpr, 1, 3.14) == 3.14

        # None values
        none_sexpr = [Symbol("test"), None, None]
        assert SExprParser.safe_get_str(none_sexpr, 1, "fallback") == "fallback"
        assert SExprParser.safe_get_int(none_sexpr, 1, 100) == 100
        assert SExprParser.safe_get_float(none_sexpr, 1, 2.71) == 2.71


class TestSExprParserEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_sexpr(self):
        """Test parsing empty S-expression"""
        sexpr = []
        assert SExprParser.find_token(sexpr, "any") is None
        assert SExprParser.find_all_tokens(sexpr, "any") == []
        assert SExprParser.has_symbol(sexpr, "any") is False

    def test_non_list_sexpr(self):
        """Test handling of non-list S-expressions"""
        sexpr = "not_a_list"
        # Should handle gracefully without crashing
        assert SExprParser.find_token(sexpr, "any") is None

    def test_deeply_nested_structure(self):
        """Test parsing deeply nested structures"""
        sexpr = [Symbol("root")]
        for i in range(10):
            sexpr.append([Symbol(f"level{i}"), f"value{i}"])

        token = SExprParser.find_token(sexpr, "level5")
        assert token == [Symbol("level5"), "value5"]

    def test_complex_mixed_types(self):
        """Test parsing with mixed data types"""
        sexpr = [
            Symbol("root"),
            [Symbol("string"), "text"],
            [Symbol("integer"), 42],
            [Symbol("float"), 3.14],
            [Symbol("boolean"), True],
            [Symbol("none"), None],
            [Symbol("nested"), [Symbol("deep"), "value"]],
        ]

        assert SExprParser.get_optional_str(sexpr, "string") == "text"
        assert SExprParser.get_optional_int(sexpr, "integer") == 42
        assert SExprParser.get_optional_float(sexpr, "float") == 3.14

        nested_token = SExprParser.find_token(sexpr, "nested")
        assert nested_token is not None
        deep_token = SExprParser.find_token(nested_token, "deep")
        assert deep_token == [Symbol("deep"), "value"]


if __name__ == "__main__":
    pytest.main([__file__])
