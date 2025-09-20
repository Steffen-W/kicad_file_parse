"""Test OptionalFlag functionality with Font class round-trip tests."""

import pytest

from kicad_parserv2.base_element import OptionalFlag
from kicad_parserv2.base_types import Effects, Font, Size, Thickness


class TestOptionalFlag:
    """Test OptionalFlag basic functionality."""

    def test_optional_flag_creation(self):
        """Test OptionalFlag creation and attributes."""
        flag = OptionalFlag("italic")
        assert flag._value_ == "italic"
        assert flag.is_present() == False

        flag.__found__ = True
        assert flag.is_present() == True

    def test_optional_flag_different_values(self):
        """Test OptionalFlag with different expected values."""
        bold_flag = OptionalFlag("bold")
        italic_flag = OptionalFlag("italic")
        locked_flag = OptionalFlag("locked")

        assert bold_flag._value_ == "bold"
        assert italic_flag._value_ == "italic"
        assert locked_flag._value_ == "locked"

    def test_optional_flag_equality(self):
        """Test OptionalFlag equality comparison."""
        # Same expected value, both not found
        flag1 = OptionalFlag("italic")
        flag2 = OptionalFlag("italic")
        assert flag1 == flag2

        # Same expected value, both found
        flag1.__found__ = True
        flag2.__found__ = True
        assert flag1 == flag2

        # Same expected value, one found, one not found
        flag1.__found__ = True
        flag2.__found__ = False
        assert flag1 != flag2

        # Different expected values
        flag3 = OptionalFlag("bold")
        flag4 = OptionalFlag("italic")
        assert flag3 != flag4

        # Different expected values, both found
        flag3.__found__ = True
        flag4.__found__ = True
        assert flag3 != flag4


class TestFontOptionalFlags:
    """Test OptionalFlag with Font class round-trip tests."""

    def test_font_no_flags_round_trip(self):
        """Test Font with no optional flags."""
        # S-expression with only size and thickness
        sexpr_str = "(font (size 1.27 1.27) (thickness 0.254))"

        # Parse from S-expression
        font = Font.from_sexpr(sexpr_str)

        # Check that flags are not found
        assert font.bold is not None
        assert font.bold._value_ == "bold"
        assert font.bold.is_present() == False

        assert font.italic is not None
        assert font.italic._value_ == "italic"
        assert font.italic.is_present() == False

        # Convert back to S-expression
        result_sexpr = font.to_sexpr()

        # Should not contain bold or italic flags
        result_str = str(result_sexpr)
        assert "bold" not in result_str
        assert "italic" not in result_str
        assert "size" in result_str
        assert "thickness" in result_str

    def test_font_italic_flag_round_trip(self):
        """Test Font with italic flag."""
        # S-expression with italic flag
        sexpr_str = "(font (size 1.27 1.27) (thickness 0.254) italic)"

        # Parse from S-expression
        font = Font.from_sexpr(sexpr_str)

        # Check that italic flag is found, bold is not
        assert font.italic is not None
        assert font.italic._value_ == "italic"
        assert font.italic.is_present() == True

        assert font.bold is not None
        assert font.bold._value_ == "bold"
        assert font.bold.is_present() == False

        # Convert back to S-expression
        result_sexpr = font.to_sexpr()
        result_str = str(result_sexpr)

        # Should contain italic but not bold
        assert "italic" in result_str
        assert "bold" not in result_str

    def test_font_bold_flag_round_trip(self):
        """Test Font with bold flag."""
        # S-expression with bold flag
        sexpr_str = "(font (size 1.27 1.27) (thickness 0.254) bold)"

        # Parse from S-expression
        font = Font.from_sexpr(sexpr_str)

        # Check that bold flag is found, italic is not
        assert font.bold is not None
        assert font.bold._value_ == "bold"
        assert font.bold.is_present() == True

        assert font.italic is not None
        assert font.italic._value_ == "italic"
        assert font.italic.is_present() == False

        # Convert back to S-expression
        result_sexpr = font.to_sexpr()
        result_str = str(result_sexpr)

        # Should contain bold but not italic
        assert "bold" in result_str
        assert "italic" not in result_str

    def test_font_both_flags_round_trip(self):
        """Test Font with both bold and italic flags."""
        # S-expression with both flags
        sexpr_str = "(font (size 1.27 1.27) (thickness 0.254) bold italic)"

        # Parse from S-expression
        font = Font.from_sexpr(sexpr_str)

        # Check that both flags are found
        assert font.bold is not None
        assert font.bold._value_ == "bold"
        assert font.bold.is_present() == True

        assert font.italic is not None
        assert font.italic._value_ == "italic"
        assert font.italic.is_present() == True

        # Convert back to S-expression
        result_sexpr = font.to_sexpr()
        result_str = str(result_sexpr)

        # Should contain both flags
        assert "bold" in result_str
        assert "italic" in result_str

    def test_font_flags_different_order(self):
        """Test Font with flags in different order."""
        # S-expression with flags in different order
        sexpr_str = "(font (size 1.27 1.27) italic (thickness 0.254) bold)"

        # Parse from S-expression
        font = Font.from_sexpr(sexpr_str)

        # Check that both flags are found regardless of order
        assert font.bold.is_present() == True
        assert font.italic.is_present() == True

        # Convert back to S-expression
        result_sexpr = font.to_sexpr()
        result_str = str(result_sexpr)

        # Should contain both flags
        assert "bold" in result_str
        assert "italic" in result_str

    def test_font_minimal_round_trip(self):
        """Test Font with minimal required fields."""
        # Create Font object programmatically
        font = Font()
        font.size = Size(width=1.27, height=1.27)
        font.thickness = Thickness(value=0.254)

        # Set italic flag as found
        font.italic.__found__ = True

        # Convert to S-expression
        result_sexpr = font.to_sexpr()
        result_str = str(result_sexpr)

        # Should contain italic but not bold
        assert "italic" in result_str
        assert "bold" not in result_str

        # Parse back from S-expression
        font_parsed = Font.from_sexpr(result_sexpr)

        # Should be equal to original font
        assert font == font_parsed

    def test_font_complete_round_trip(self):
        """Test complete round-trip: S-expr -> Font -> S-expr -> Font."""
        original_sexpr = "(font (size 1.27 1.143) (thickness 0.254) italic)"

        # First parse
        font1 = Font.from_sexpr(original_sexpr)

        # Convert to S-expression
        middle_sexpr = font1.to_sexpr()

        # Second parse
        font2 = Font.from_sexpr(middle_sexpr)

        # Both Font objects should be equivalent
        assert font1 == font2

        # Final S-expression should contain italic
        final_sexpr = font2.to_sexpr()
        final_str = str(final_sexpr)
        assert "italic" in final_str
        assert "bold" not in final_str


class TestNestedOptionalFlagEquality:
    """Test OptionalFlag equality with nested structures (Effects with Font)."""

    def test_nested_optional_flag_equality_same_flags(self):
        """Test nested OptionalFlag equality when both have same flags."""
        # S-expression with bold flag in nested font
        sexpr_with_bold = """(effects (font (size 1.27 1.27) (thickness 0.254) bold))"""

        # Parse both from same S-expression
        effects1 = Effects.from_sexpr(sexpr_with_bold)
        effects2 = Effects.from_sexpr(sexpr_with_bold)

        # Should be equal
        assert effects1 == effects2

        # Verify font bold flag is set in both
        assert effects1.font.bold.is_present() == True
        assert effects2.font.bold.is_present() == True
        assert effects1.font.italic.is_present() == False
        assert effects2.font.italic.is_present() == False

    def test_nested_optional_flag_equality_different_flags(self):
        """Test nested OptionalFlag equality when flags differ."""
        # S-expression with bold flag
        sexpr_with_bold = """(effects (font (size 1.27 1.27) (thickness 0.254) bold))"""

        # S-expression without bold flag
        sexpr_without_bold = """(effects (font (size 1.27 1.27) (thickness 0.254)))"""

        # Parse from different S-expressions
        effects_with_bold = Effects.from_sexpr(sexpr_with_bold)
        effects_without_bold = Effects.from_sexpr(sexpr_without_bold)

        # Should NOT be equal due to different bold flag states
        assert effects_with_bold != effects_without_bold

        # Verify font bold flag states
        assert effects_with_bold.font.bold.is_present() == True
        assert effects_without_bold.font.bold.is_present() == False

        # Both should have same italic flag state (not found)
        assert effects_with_bold.font.italic.is_present() == False
        assert effects_without_bold.font.italic.is_present() == False

    def test_nested_optional_flag_equality_multiple_flags(self):
        """Test nested OptionalFlag equality with multiple flags."""
        # S-expression with both bold and italic flags
        sexpr_both_flags = (
            """(effects (font (size 1.27 1.27) (thickness 0.254) bold italic))"""
        )

        # S-expression with only italic flag
        sexpr_italic_only = (
            """(effects (font (size 1.27 1.27) (thickness 0.254) italic))"""
        )

        # Parse from different S-expressions
        effects_both = Effects.from_sexpr(sexpr_both_flags)
        effects_italic = Effects.from_sexpr(sexpr_italic_only)

        # Should NOT be equal due to different bold flag states
        assert effects_both != effects_italic

        # Verify flag states
        assert effects_both.font.bold.is_present() == True
        assert effects_both.font.italic.is_present() == True

        assert effects_italic.font.bold.is_present() == False
        assert effects_italic.font.italic.is_present() == True

    def test_nested_optional_flag_equality_with_hide_flag(self):
        """Test nested OptionalFlag equality including Effects hide flag."""
        # S-expression with font bold and effects hide
        sexpr_with_hide = (
            """(effects (font (size 1.27 1.27) (thickness 0.254) bold) hide)"""
        )

        # S-expression with font bold but no hide
        sexpr_without_hide = (
            """(effects (font (size 1.27 1.27) (thickness 0.254) bold))"""
        )

        # Parse from different S-expressions
        effects_with_hide = Effects.from_sexpr(sexpr_with_hide)
        effects_without_hide = Effects.from_sexpr(sexpr_without_hide)

        # Should NOT be equal due to different hide flag states
        assert effects_with_hide != effects_without_hide

        # Verify hide flag states
        assert effects_with_hide.hide.is_present() == True
        assert effects_without_hide.hide.is_present() == False

        # Both should have same font bold flag state (found)
        assert effects_with_hide.font.bold.is_present() == True
        assert effects_without_hide.font.bold.is_present() == True


if __name__ == "__main__":
    pytest.main([__file__])
