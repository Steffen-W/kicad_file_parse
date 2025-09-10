"""
Test cases based on real-world KiCad design rules examples

This module tests parsing of actual .kicad_dru files used in practice,
ensuring compatibility with real-world usage patterns.
"""

from kicad_parser.kicad_design_rules import (
    ConstraintType,
    ConstraintValue,
    DesignRule,
    DesignRuleConstraint,
    parse_kicad_design_rules_file,
    write_kicad_design_rules_file,
)


class TestRealWorldExamples:
    """Test cases based on real-world KiCad design rules examples"""

    def test_real_world_netclass_clearance_rules(self):
        """Test parsing of real-world design rules with netclass conditions"""
        # Based on a real .kicad_dru file with netclass clearance rules
        dru_content = """(version 1)
(rule "class 3:2"
  (condition "A.NetClass == 'SCHUTZ' && B.NetClass == 'class2'")
  (constraint clearance (min 0.4mm)))

(rule "class 6:1"
  (condition "A.NetClass == 'USB' && B.NetClass == 'class1'")
  (constraint clearance (min 2mm)))

(rule "class 6:2"
  (condition "A.NetClass == 'USB' && B.NetClass == 'class2'")
  (constraint clearance (min 2mm)))

(rule "class 6:3"
  (condition "A.NetClass == 'USB' && B.NetClass == 'SCHUTZ'")
  (constraint clearance (min 2mm)))

(rule "class 6:4"
  (condition "A.NetClass == 'USB' && B.NetClass == 'class4'")
  (constraint clearance (min 2mm)))

(rule "class 7:0"
  (condition "A.NetClass == 'HFout' && B.NetClass == 'Default'")
  (constraint clearance (min 0.508mm)))

(rule "class 7:1"
  (condition "A.NetClass == 'HFout' && B.NetClass == 'class1'")
  (constraint clearance (min 0.508mm)))

(rule "class 8:0"
  (condition "A.NetClass == '100V' && B.NetClass == 'Default'")
  (constraint clearance (min 0.2mm)))

(rule "class 8:1"
  (condition "A.NetClass == '100V' && B.NetClass == 'class1'")
  (constraint clearance (min 0.2mm)))

(rule "class 8:2"
  (condition "A.NetClass == '100V' && B.NetClass == 'class2'")
  (constraint clearance (min 0.2mm)))"""

        # Parse the design rules
        design_rules = parse_kicad_design_rules_file(dru_content)

        # Verify basic structure
        assert design_rules.version == 1
        assert len(design_rules.rules) == 10

        # Test specific rules
        rule_32 = design_rules.get_rule("class 3:2")
        assert rule_32 is not None
        assert rule_32.condition == "A.NetClass == 'SCHUTZ' && B.NetClass == 'class2'"
        assert rule_32.constraint.constraint_type == ConstraintType.CLEARANCE
        assert rule_32.constraint.value.min_value == "0.4mm"

        rule_61 = design_rules.get_rule("class 6:1")
        assert rule_61 is not None
        assert rule_61.condition == "A.NetClass == 'USB' && B.NetClass == 'class1'"
        assert rule_61.constraint.constraint_type == ConstraintType.CLEARANCE
        assert rule_61.constraint.value.min_value == "2mm"

        rule_70 = design_rules.get_rule("class 7:0")
        assert rule_70 is not None
        assert rule_70.condition == "A.NetClass == 'HFout' && B.NetClass == 'Default'"
        assert rule_70.constraint.constraint_type == ConstraintType.CLEARANCE
        assert rule_70.constraint.value.min_value == "0.508mm"

        rule_80 = design_rules.get_rule("class 8:0")
        assert rule_80 is not None
        assert rule_80.condition == "A.NetClass == '100V' && B.NetClass == 'Default'"
        assert rule_80.constraint.constraint_type == ConstraintType.CLEARANCE
        assert rule_80.constraint.value.min_value == "0.2mm"

        # Test USB rules have consistent 2mm clearance
        usb_rules = [
            rule for rule in design_rules.rules if rule.name.startswith("class 6:")
        ]
        assert len(usb_rules) == 4
        for rule in usb_rules:
            assert "USB" in rule.condition
            assert rule.constraint.value.min_value == "2mm"

        # Test 100V rules have consistent 0.2mm clearance
        hv_rules = [
            rule for rule in design_rules.rules if rule.name.startswith("class 8:")
        ]
        assert len(hv_rules) == 3
        for rule in hv_rules:
            assert "100V" in rule.condition
            assert rule.constraint.value.min_value == "0.2mm"

    def test_real_world_netclass_rules_round_trip(self):
        """Test round-trip conversion of real-world netclass rules"""
        # Original content
        original_content = """(version 1)
(rule "class 3:2"
  (condition "A.NetClass == 'SCHUTZ' && B.NetClass == 'class2'")
  (constraint clearance (min 0.4mm)))

(rule "class 6:1"
  (condition "A.NetClass == 'USB' && B.NetClass == 'class1'")
  (constraint clearance (min 2mm)))

(rule "class 8:0"
  (condition "A.NetClass == '100V' && B.NetClass == 'Default'")
  (constraint clearance (min 0.2mm)))"""

        # Parse -> serialize -> parse again
        design_rules = parse_kicad_design_rules_file(original_content)
        serialized_content = write_kicad_design_rules_file(design_rules)
        design_rules_again = parse_kicad_design_rules_file(serialized_content)

        # Should have same structure
        assert design_rules_again.version == 1
        assert len(design_rules_again.rules) == 3

        # Check that all original rules are preserved
        original_rules = design_rules.rules
        reparsed_rules = design_rules_again.rules

        for orig_rule, reparsed_rule in zip(original_rules, reparsed_rules):
            assert orig_rule.name == reparsed_rule.name
            assert orig_rule.condition == reparsed_rule.condition
            assert (
                orig_rule.constraint.constraint_type
                == reparsed_rule.constraint.constraint_type
            )
            assert (
                orig_rule.constraint.value.min_value
                == reparsed_rule.constraint.value.min_value
            )

    def test_netclass_conditions_parsing(self):
        """Test parsing of various netclass condition formats"""
        test_conditions = [
            "A.NetClass == 'SCHUTZ' && B.NetClass == 'class2'",
            "A.NetClass == 'USB' && B.NetClass == 'class1'",
            "A.NetClass == 'HFout' && B.NetClass == 'Default'",
            "A.NetClass == '100V' && B.NetClass == 'Default'",
        ]

        for i, condition in enumerate(test_conditions):
            constraint = DesignRuleConstraint(
                constraint_type=ConstraintType.CLEARANCE,
                value=ConstraintValue(min_value=0.5),
            )
            rule = DesignRule(
                name=f"test_rule_{i}", constraint=constraint, condition=condition
            )

            # Test serialization includes condition
            sexpr = rule.to_sexpr()
            assert condition in str(sexpr)

            # Test round-trip preserves condition
            rule_reparsed = DesignRule.from_sexpr(sexpr)
            assert rule_reparsed.condition == condition

    def test_millimeter_unit_parsing(self):
        """Test parsing of values with millimeter units"""
        test_cases = [
            ("0.4mm", "0.4mm"),
            ("2mm", "2mm"),
            ("0.508mm", "0.508mm"),
            ("0.2mm", "0.2mm"),
        ]

        for mm_value, expected_string in test_cases:
            dru_content = f"""(version 1)
(rule "test_rule"
  (constraint clearance (min {mm_value})))"""

            design_rules = parse_kicad_design_rules_file(dru_content)
            rule = design_rules.rules[0]

            assert rule.constraint.value.min_value == expected_string

    def test_complex_netclass_names(self):
        """Test parsing of complex netclass names with special characters"""
        # Test various netclass name formats found in real projects
        complex_names = [
            "SCHUTZ",  # German protection class
            "100V",  # Voltage class with number
            "USB",  # Standard acronym
            "HFout",  # High frequency output
            "Default",  # Built-in default class
            "class1",  # Generic numbered class
            "class2",
            "class4",
        ]

        for netclass in complex_names:
            dru_content = f"""(version 1)
(rule "test_{netclass}"
  (condition "A.NetClass == '{netclass}' && B.NetClass == 'Default'")
  (constraint clearance (min 0.5mm)))"""

            design_rules = parse_kicad_design_rules_file(dru_content)
            rule = design_rules.rules[0]

            assert netclass in rule.condition
            assert rule.constraint.constraint_type == ConstraintType.CLEARANCE

    def test_different_clearance_values(self):
        """Test parsing of different clearance values used in practice"""
        clearance_values = [
            ("0.2", "0.2mm"),  # Fine pitch components
            ("0.4", "0.4mm"),  # Standard spacing
            ("0.508", "0.508mm"),  # 20 mil spacing
            ("2.0", "2.0mm"),  # High voltage isolation
        ]

        for clearance, expected in clearance_values:
            dru_content = f"""(version 1)
(rule "clearance_test"
  (constraint clearance (min {clearance}mm)))"""

            design_rules = parse_kicad_design_rules_file(dru_content)
            rule = design_rules.rules[0]

            assert rule.constraint.value.min_value == expected

    def test_rule_naming_conventions(self):
        """Test parsing of different rule naming conventions"""
        rule_names = [
            "class 3:2",  # Class matrix notation
            "class 6:1",
            "class 7:0",
            "class 8:2",
        ]

        for rule_name in rule_names:
            dru_content = f"""(version 1)
(rule "{rule_name}"
  (constraint clearance (min 0.5mm)))"""

            design_rules = parse_kicad_design_rules_file(dru_content)
            rule = design_rules.rules[0]

            assert rule.name == rule_name
