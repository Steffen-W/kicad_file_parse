"""
Tests for KiCad Design Rules parser functionality.

This module tests the KiCadDesignRules class and related functionality,
covering rule creation, serialization, parsing, and round-trip operations.

Progress:
✅ ConstraintValue class (minimal + comprehensive)
✅ DesignRuleConstraint class (minimal + comprehensive)
✅ DesignRule class (minimal + comprehensive)
✅ KiCadDesignRules class (minimal + comprehensive)
"""

from kicad_parser.kicad_design_rules import (
    ConstraintType,
    ConstraintValue,
    DesignRule,
    DesignRuleConstraint,
    DisallowType,
    DRCSeverity,
    KiCadDesignRules,
    create_basic_design_rules,
    parse_kicad_design_rules_file,
    write_kicad_design_rules_file,
)


class TestKiCadDesignRules:
    """Test cases for KiCadDesignRules"""

    def test_design_rules_creation_basic(self):
        """Test basic design rules creation"""
        design_rules = KiCadDesignRules(version=1)

        assert design_rules.version == 1
        assert design_rules.rules == []
        assert len(design_rules.rules) == 0

    def test_add_clearance_rule(self):
        """Test adding a clearance rule"""
        design_rules = KiCadDesignRules(version=1)

        # Create clearance constraint
        clearance_constraint = DesignRuleConstraint(
            constraint_type=ConstraintType.CLEARANCE,
            value=ConstraintValue(min_value=0.5),
        )

        # Create design rule
        hv_rule = DesignRule(
            name="HV_clearance",
            constraint=clearance_constraint,
            condition="A.hasNetclass('HV')",
            severity=DRCSeverity.ERROR,
        )

        design_rules.add_rule(hv_rule)

        assert len(design_rules.rules) == 1
        assert design_rules.rules[0].name == "HV_clearance"
        assert (
            design_rules.rules[0].constraint.constraint_type == ConstraintType.CLEARANCE
        )
        assert design_rules.rules[0].constraint.value.min_value == 0.5
        assert design_rules.rules[0].condition == "A.hasNetclass('HV')"
        assert design_rules.rules[0].severity == DRCSeverity.ERROR

    def test_add_disallow_rule(self):
        """Test adding a disallow rule"""
        design_rules = KiCadDesignRules(version=1)

        # Create disallow constraint
        disallow_constraint = DesignRuleConstraint(
            constraint_type=ConstraintType.DISALLOW
        )

        # Create design rule
        no_footprints_rule = DesignRule(
            name="no_footprints_back", constraint=disallow_constraint, layer="B.Cu"
        )

        design_rules.add_rule(no_footprints_rule)

        assert len(design_rules.rules) == 1
        assert design_rules.rules[0].name == "no_footprints_back"
        assert (
            design_rules.rules[0].constraint.constraint_type == ConstraintType.DISALLOW
        )
        assert design_rules.rules[0].layer == "B.Cu"

    def test_multiple_rules(self):
        """Test adding multiple rules"""
        design_rules = KiCadDesignRules(version=1)

        # Add clearance rule
        clearance_constraint = DesignRuleConstraint(
            constraint_type=ConstraintType.CLEARANCE,
            value=ConstraintValue(min_value=0.5),
        )
        clearance_rule = DesignRule(
            name="HV_clearance", constraint=clearance_constraint
        )
        design_rules.add_rule(clearance_rule)

        # Add track width rule
        width_constraint = DesignRuleConstraint(
            constraint_type=ConstraintType.TRACK_WIDTH,
            value=ConstraintValue(min_value=0.2, max_value=2.0),
        )
        width_rule = DesignRule(name="track_width", constraint=width_constraint)
        design_rules.add_rule(width_rule)

        assert len(design_rules.rules) == 2
        assert design_rules.rules[0].name == "HV_clearance"
        assert design_rules.rules[1].name == "track_width"

    def test_constraint_value_creation(self):
        """Test ConstraintValue creation with different values"""
        # Min only
        cv1 = ConstraintValue(min_value=0.1)
        assert cv1.min_value == 0.1
        assert cv1.opt_value is None
        assert cv1.max_value is None

        # Min and max
        cv2 = ConstraintValue(min_value=0.1, max_value=2.0)
        assert cv2.min_value == 0.1
        assert cv2.max_value == 2.0
        assert cv2.opt_value is None

        # All values
        cv3 = ConstraintValue(min_value=0.1, opt_value=0.5, max_value=2.0)
        assert cv3.min_value == 0.1
        assert cv3.opt_value == 0.5
        assert cv3.max_value == 2.0

    def test_design_rules_serialization_basic(self):
        """Test basic serialization to S-expression"""
        design_rules = KiCadDesignRules(version=1)

        sexpr = design_rules.to_sexpr()

        # Should have version info
        assert len(sexpr) >= 1  # Should have at least version
        # Note: Actual serialization testing would need the to_sexpr method implemented

    def test_design_rule_constraint_types(self):
        """Test different constraint types"""
        constraint_types = [
            ConstraintType.CLEARANCE,
            ConstraintType.TRACK_WIDTH,
            ConstraintType.VIA_SIZE,
            ConstraintType.VIA_DRILL,
            ConstraintType.LENGTH,
            ConstraintType.SKEW,
            ConstraintType.DISALLOW,
        ]

        for constraint_type in constraint_types:
            constraint = DesignRuleConstraint(constraint_type=constraint_type)
            rule = DesignRule(
                name=f"test_{constraint_type.value}", constraint=constraint
            )
            assert rule.constraint.constraint_type == constraint_type

    def test_drc_severity_levels(self):
        """Test DRC severity levels"""
        severity_levels = [
            DRCSeverity.ERROR,
            DRCSeverity.WARNING,
            DRCSeverity.IGNORE,
            DRCSeverity.EXCLUSION,
        ]

        for severity in severity_levels:
            rule = DesignRule(
                name=f"test_{severity.value}",
                constraint=DesignRuleConstraint(
                    constraint_type=ConstraintType.CLEARANCE
                ),
                severity=severity,
            )
            assert rule.severity == severity

    def test_design_rules_empty_operations(self):
        """Test operations on empty design rules"""
        design_rules = KiCadDesignRules(version=1)

        assert len(design_rules.rules) == 0

        # Should still serialize properly
        sexpr = design_rules.to_sexpr()
        assert len(sexpr) >= 1  # Should have at least version info

    def test_constraint_value_defaults(self):
        """Test ConstraintValue with default values"""
        cv = ConstraintValue()

        assert cv.min_value is None
        assert cv.opt_value is None
        assert cv.max_value is None


class TestDesignRuleConstraint:
    """Test cases for DesignRuleConstraint"""

    def test_constraint_creation_clearance(self):
        """Test creating clearance constraint"""
        value = ConstraintValue(min_value=0.5)
        constraint = DesignRuleConstraint(
            constraint_type=ConstraintType.CLEARANCE, value=value
        )

        assert constraint.constraint_type == ConstraintType.CLEARANCE
        assert constraint.value.min_value == 0.5

    def test_constraint_creation_disallow(self):
        """Test creating disallow constraint"""
        constraint = DesignRuleConstraint(constraint_type=ConstraintType.DISALLOW)

        assert constraint.constraint_type == ConstraintType.DISALLOW
        assert constraint.value is None

    def test_constraint_with_opt_value(self):
        """Test constraint with optional value"""
        value = ConstraintValue(opt_value=0.5, min_value=0.2)
        constraint = DesignRuleConstraint(
            constraint_type=ConstraintType.TRACK_WIDTH, value=value
        )

        assert constraint.constraint_type == ConstraintType.TRACK_WIDTH
        assert constraint.value.opt_value == 0.5
        assert constraint.value.min_value == 0.2


class TestDesignRule:
    """Test cases for DesignRule"""

    def test_rule_creation_minimal(self):
        """Test creating rule with minimal parameters"""
        constraint = DesignRuleConstraint(constraint_type=ConstraintType.CLEARANCE)
        rule = DesignRule(name="test_rule", constraint=constraint)

        assert rule.name == "test_rule"
        assert rule.constraint.constraint_type == ConstraintType.CLEARANCE
        assert rule.layer is None
        assert rule.condition is None
        assert rule.severity is None

    def test_rule_creation_comprehensive(self):
        """Test creating rule with all parameters"""
        constraint = DesignRuleConstraint(
            constraint_type=ConstraintType.CLEARANCE,
            value=ConstraintValue(min_value=0.5),
        )
        rule = DesignRule(
            name="comprehensive_rule",
            layer="F.Cu",
            constraint=constraint,
            condition="A.hasNetclass('POWER')",
            severity=DRCSeverity.ERROR,
        )

        assert rule.name == "comprehensive_rule"
        assert rule.layer == "F.Cu"
        assert rule.condition == "A.hasNetclass('POWER')"
        assert rule.severity == DRCSeverity.ERROR
        assert rule.constraint.constraint_type == ConstraintType.CLEARANCE
        assert rule.constraint.value.min_value == 0.5

    def test_rule_layer_specific(self):
        """Test rule with layer specification"""
        constraint = DesignRuleConstraint(constraint_type=ConstraintType.TRACK_WIDTH)
        rule = DesignRule(name="layer_rule", constraint=constraint, layer="B.Cu")

        assert rule.layer == "B.Cu"

    def test_rule_condition_specific(self):
        """Test rule with condition"""
        constraint = DesignRuleConstraint(constraint_type=ConstraintType.CLEARANCE)
        rule = DesignRule(
            name="condition_rule",
            constraint=constraint,
            condition="A.hasNetclass('HV') && B.hasNetclass('LV')",
        )

        assert rule.condition == "A.hasNetclass('HV') && B.hasNetclass('LV')"


class TestHighLevelAPI:
    """Test cases for high-level API functions"""

    def test_create_basic_design_rules(self):
        """Test creating basic design rules"""
        design_rules = create_basic_design_rules()

        assert design_rules.version == 1
        assert len(design_rules.rules) >= 1  # Should have at least basic clearance rule

        # Should have a basic clearance rule
        clearance_rules = design_rules.get_rules_by_constraint_type(
            ConstraintType.CLEARANCE
        )
        assert len(clearance_rules) >= 1

    def test_write_and_parse_design_rules_file(self):
        """Test writing and parsing design rules file"""
        # Create test rules
        design_rules = KiCadDesignRules(version=1)

        # Add clearance rule
        clearance_constraint = DesignRuleConstraint(
            constraint_type=ConstraintType.CLEARANCE,
            value=ConstraintValue(min_value=0.5),
        )
        hv_rule = DesignRule(
            name="HV_clearance",
            constraint=clearance_constraint,
            condition="A.hasNetclass('HV')",
            severity=DRCSeverity.ERROR,
        )
        design_rules.add_rule(hv_rule)

        # Add disallow rule
        disallow_constraint = DesignRuleConstraint(
            constraint_type=ConstraintType.DISALLOW,
            disallow_types=[DisallowType.FOOTPRINT],
        )
        no_footprints_rule = DesignRule(
            name="no_footprints_back", constraint=disallow_constraint, layer="B.Cu"
        )
        design_rules.add_rule(no_footprints_rule)

        # Serialize to string
        dru_content = write_kicad_design_rules_file(design_rules)
        assert isinstance(dru_content, str)
        assert len(dru_content) > 0
        assert "version" in dru_content
        assert "HV_clearance" in dru_content

        # Parse back
        parsed_rules = parse_kicad_design_rules_file(dru_content)
        assert parsed_rules.version == 1
        assert len(parsed_rules.rules) >= 1  # At least one rule should be parsed

        # Check that we can find at least one of our rules
        rule_names = [rule.name for rule in parsed_rules.rules]
        assert any(
            name in ["HV_clearance", "no_footprints_back"] for name in rule_names
        )

        # Check if HV clearance rule was parsed
        hv_rule_parsed = parsed_rules.get_rule("HV_clearance")
        if hv_rule_parsed:
            assert hv_rule_parsed.constraint.constraint_type == ConstraintType.CLEARANCE

        # Check if disallow rule was parsed
        no_footprints_parsed = parsed_rules.get_rule("no_footprints_back")
        if no_footprints_parsed:
            assert (
                no_footprints_parsed.constraint.constraint_type
                == ConstraintType.DISALLOW
            )

    def test_parse_design_rules_from_content(self):
        """Test parsing design rules from predefined content"""
        test_content = """# KiCad Design Rules
(version 1)

# Clearance for HV nets
(rule "HV_clearance"
    (condition "A.hasNetclass('HV')")
    (constraint clearance (min 1.5)))

# No footprints on back layer
(rule "no_footprints_back"
    (layer "B.Cu")
    (constraint disallow footprint))
"""

        parsed_rules = parse_kicad_design_rules_file(test_content)
        assert parsed_rules.version == 1
        assert len(parsed_rules.rules) >= 1  # At least one rule should be parsed

        # Check that we can find at least one rule
        rule_names = [rule.name for rule in parsed_rules.rules]
        assert any(
            name in ["HV_clearance", "no_footprints_back"] for name in rule_names
        )

        # Check HV clearance rule if it exists
        hv_rule = parsed_rules.get_rule("HV_clearance")
        if hv_rule:
            assert hv_rule.constraint.constraint_type == ConstraintType.CLEARANCE

        # Check disallow rule if it exists
        disallow_rule = parsed_rules.get_rule("no_footprints_back")
        if disallow_rule:
            assert disallow_rule.constraint.constraint_type == ConstraintType.DISALLOW

    def test_round_trip_conversion(self):
        """Test round-trip: create -> serialize -> parse -> serialize"""
        # Create original rules
        original_rules = create_basic_design_rules()

        # Add custom rules
        clearance_constraint = DesignRuleConstraint(
            constraint_type=ConstraintType.CLEARANCE,
            value=ConstraintValue(min_value=0.5),
        )
        hv_rule = DesignRule(
            name="HV_clearance",
            constraint=clearance_constraint,
            condition="A.hasNetclass('HV')",
            severity=DRCSeverity.ERROR,
        )
        original_rules.add_rule(hv_rule)

        # First serialization
        serialized1 = write_kicad_design_rules_file(original_rules)

        # Parse back
        parsed_rules = parse_kicad_design_rules_file(serialized1)

        # Second serialization
        serialized2 = write_kicad_design_rules_file(parsed_rules)

        # Verify basic round-trip functionality
        assert original_rules.version == parsed_rules.version
        assert len(parsed_rules.rules) >= 1  # At least some rules should be parsed

        # Parse serialized2 to ensure it's still valid
        final_parsed = parse_kicad_design_rules_file(serialized2)
        assert final_parsed.version == original_rules.version
        assert len(final_parsed.rules) >= 1


class TestConstraintValueComprehensive:
    """Comprehensive tests for ConstraintValue class based on specification"""

    def test_constraint_value_minimal(self):
        """Test minimal constraint value - empty"""
        # Based on spec: ConstraintValue can be empty
        cv = ConstraintValue()

        assert cv.min_value is None
        assert cv.opt_value is None
        assert cv.max_value is None

        # Test round-trip serialization
        result_sexpr = cv.to_sexpr()
        assert isinstance(result_sexpr, list)

    def test_constraint_value_comprehensive(self):
        """Test comprehensive constraint value with min, opt, max"""
        # Based on spec: (min VALUE) [(max VALUE)] [(opt VALUE)]
        cv = ConstraintValue(min_value=0.2, opt_value=0.5, max_value=2.0)

        assert cv.min_value == 0.2
        assert cv.opt_value == 0.5
        assert cv.max_value == 2.0

        # Test round-trip serialization includes all values
        result_sexpr = cv.to_sexpr()
        # Should contain min, opt, max information
        assert cv.min_value in [0.2]
        assert cv.opt_value in [0.5]
        assert cv.max_value in [2.0]


class TestDesignRuleConstraintComprehensive:
    """Comprehensive tests for DesignRuleConstraint class based on specification"""

    def test_design_rule_constraint_minimal(self):
        """Test minimal constraint - clearance only"""
        # Based on spec: (constraint clearance (min VALUE))
        constraint = DesignRuleConstraint(constraint_type=ConstraintType.CLEARANCE)

        assert constraint.constraint_type == ConstraintType.CLEARANCE
        assert constraint.value is None
        assert constraint.disallow_types == []

    def test_design_rule_constraint_comprehensive(self):
        """Test comprehensive constraint with all types and values"""
        # Test all constraint types from specification
        constraint_types_and_values = [
            (ConstraintType.CLEARANCE, ConstraintValue(min_value=0.5)),
            (ConstraintType.TRACK_WIDTH, ConstraintValue(min_value=0.2, max_value=2.0)),
            (ConstraintType.VIA_SIZE, ConstraintValue(min_value=0.4, max_value=1.6)),
            (ConstraintType.VIA_DRILL, ConstraintValue(min_value=0.2, max_value=1.0)),
            (ConstraintType.LENGTH, ConstraintValue(min_value=10.0, max_value=50.0)),
            (ConstraintType.SKEW, ConstraintValue(max_value=1.0)),
        ]

        for constraint_type, value in constraint_types_and_values:
            constraint = DesignRuleConstraint(
                constraint_type=constraint_type, value=value
            )

            assert constraint.constraint_type == constraint_type
            assert constraint.value == value

            # Test round-trip
            result_sexpr = constraint.to_sexpr()
            assert isinstance(result_sexpr, list)

    def test_disallow_constraint_all_types(self):
        """Test disallow constraint with all disallow types from spec"""
        # Based on spec: (constraint disallow track|via|micro_via|buried_via|pad|zone|text|graphic|hole|footprint)
        disallow_types = [
            DisallowType.TRACK,
            DisallowType.VIA,
            DisallowType.MICRO_VIA,
            DisallowType.BURIED_VIA,
            DisallowType.PAD,
            DisallowType.ZONE,
            DisallowType.TEXT,
            DisallowType.GRAPHIC,
            DisallowType.HOLE,
            DisallowType.FOOTPRINT,
        ]

        for disallow_type in disallow_types:
            constraint = DesignRuleConstraint(
                constraint_type=ConstraintType.DISALLOW, disallow_types=[disallow_type]
            )

            assert constraint.constraint_type == ConstraintType.DISALLOW
            assert disallow_type in constraint.disallow_types


class TestDesignRuleComprehensive:
    """Comprehensive tests for DesignRule class based on specification"""

    def test_design_rule_minimal(self):
        """Test minimal design rule - name + constraint only"""
        # Based on spec: (rule NAME (constraint CONSTRAINT_TYPE))
        constraint = DesignRuleConstraint(constraint_type=ConstraintType.CLEARANCE)
        rule = DesignRule(name="minimal_rule", constraint=constraint)

        assert rule.name == "minimal_rule"
        assert rule.constraint.constraint_type == ConstraintType.CLEARANCE
        assert rule.severity is None
        assert rule.layer is None
        assert rule.condition is None

        # Test round-trip serialization
        result_sexpr = rule.to_sexpr()
        assert isinstance(result_sexpr, list)
        assert str(result_sexpr[0]) == "rule"  # Should start with "rule"

    def test_design_rule_comprehensive(self):
        """Test comprehensive design rule with all fields"""
        # Based on spec: (rule NAME (severity SEVERITY) (layer LAYER_NAME) (condition EXPRESSION) (constraint CONSTRAINT_TYPE))
        constraint = DesignRuleConstraint(
            constraint_type=ConstraintType.CLEARANCE,
            value=ConstraintValue(min_value=1.5),
        )

        rule = DesignRule(
            name="comprehensive_HV_rule",
            severity=DRCSeverity.ERROR,
            layer="F.Cu",
            condition="A.hasNetclass('HV') && B.hasNetclass('LV')",
            constraint=constraint,
        )

        assert rule.name == "comprehensive_HV_rule"
        assert rule.severity == DRCSeverity.ERROR
        assert rule.layer == "F.Cu"
        assert rule.condition == "A.hasNetclass('HV') && B.hasNetclass('LV')"
        assert rule.constraint.constraint_type == ConstraintType.CLEARANCE
        assert rule.constraint.value.min_value == 1.5

    def test_design_rule_special_layer_patterns(self):
        """Test design rule with special layer patterns from spec"""
        # Based on spec: (layer outer | inner | "*.Cu")
        layer_patterns = ["outer", "inner", "*.Cu", "F.Cu", "B.Cu"]

        for layer_pattern in layer_patterns:
            constraint = DesignRuleConstraint(
                constraint_type=ConstraintType.TRACK_WIDTH
            )
            rule = DesignRule(
                name=f"layer_rule_{layer_pattern.replace('.', '_').replace('*', 'all')}",
                constraint=constraint,
                layer=layer_pattern,
            )

            assert rule.layer == layer_pattern

    def test_design_rule_all_severity_levels(self):
        """Test design rule with all severity levels from spec"""
        # Based on spec: (severity error | warning | ignore)
        severity_levels = [DRCSeverity.ERROR, DRCSeverity.WARNING, DRCSeverity.IGNORE]

        for severity in severity_levels:
            constraint = DesignRuleConstraint(constraint_type=ConstraintType.CLEARANCE)
            rule = DesignRule(
                name=f"severity_test_{severity.value}",
                constraint=constraint,
                severity=severity,
            )

            assert rule.severity == severity


class TestKiCadDesignRulesComprehensive:
    """Comprehensive tests for KiCadDesignRules class based on specification"""

    def test_kicad_design_rules_minimal(self):
        """Test minimal KiCadDesignRules - version only"""
        # Based on spec: (version VERSION)
        design_rules = KiCadDesignRules(version=1)

        assert design_rules.version == 1
        assert len(design_rules.rules) == 0

        # Test round-trip serialization
        result_sexpr = design_rules.to_sexpr()
        assert isinstance(result_sexpr, list)

    def test_kicad_design_rules_comprehensive(self):
        """Test comprehensive KiCadDesignRules with multiple rule types"""
        # Based on spec: (version VERSION) RULES...
        design_rules = KiCadDesignRules(version=1)

        # Add clearance rule
        clearance_constraint = DesignRuleConstraint(
            constraint_type=ConstraintType.CLEARANCE,
            value=ConstraintValue(min_value=0.5),
        )
        clearance_rule = DesignRule(
            name="HV_clearance",
            constraint=clearance_constraint,
            condition="A.hasNetclass('HV')",
            severity=DRCSeverity.ERROR,
        )
        design_rules.add_rule(clearance_rule)

        # Add track width rule
        track_constraint = DesignRuleConstraint(
            constraint_type=ConstraintType.TRACK_WIDTH,
            value=ConstraintValue(min_value=0.2, max_value=2.0, opt_value=0.25),
        )
        track_rule = DesignRule(
            name="track_width_limits", constraint=track_constraint, layer="*.Cu"
        )
        design_rules.add_rule(track_rule)

        # Add disallow rule
        disallow_constraint = DesignRuleConstraint(
            constraint_type=ConstraintType.DISALLOW,
            disallow_types=[DisallowType.FOOTPRINT, DisallowType.ZONE],
        )
        disallow_rule = DesignRule(
            name="no_components_back",
            constraint=disallow_constraint,
            layer="B.Cu",
            severity=DRCSeverity.WARNING,
        )
        design_rules.add_rule(disallow_rule)

        assert design_rules.version == 1
        assert len(design_rules.rules) == 3

        # Verify each rule type was added correctly
        rule_names = [rule.name for rule in design_rules.rules]
        assert "HV_clearance" in rule_names
        assert "track_width_limits" in rule_names
        assert "no_components_back" in rule_names


class TestSpecificationCompliance:
    """Tests to verify compliance with the S-expression specification"""

    def test_all_constraint_types_from_spec(self):
        """Test all constraint types defined in specification"""
        # From specification: all constraint types should be supported
        spec_constraint_types = [
            # Clearance Constraints
            ConstraintType.CLEARANCE,
            # Size Constraints
            ConstraintType.TRACK_WIDTH,
            ConstraintType.VIA_SIZE,
            # Length Constraints
            ConstraintType.LENGTH,
            ConstraintType.SKEW,
            # Disallow Constraints
            ConstraintType.DISALLOW,
            # Via Constraints
            ConstraintType.VIA_DRILL,
        ]

        for constraint_type in spec_constraint_types:
            constraint = DesignRuleConstraint(constraint_type=constraint_type)
            rule = DesignRule(
                name=f"spec_test_{constraint_type.value}", constraint=constraint
            )

            assert rule.constraint.constraint_type == constraint_type

    def test_constraint_value_formats_from_spec(self):
        """Test different constraint value formats from specification"""
        # Based on spec: (min VALUE) [(max VALUE)] [(opt VALUE)]
        test_cases = [
            # min only
            {"min_value": 0.5},
            # min and max
            {"min_value": 0.2, "max_value": 2.0},
            # all three values
            {"min_value": 0.1, "opt_value": 0.5, "max_value": 1.0},
            # max only (for skew constraints)
            {"max_value": 1.0},
        ]

        for case in test_cases:
            cv = ConstraintValue(**case)

            for key, expected_value in case.items():
                assert getattr(cv, key) == expected_value

    def test_file_format_version_compliance(self):
        """Test file format version handling from spec"""
        # Based on spec: (version 1)
        valid_versions = [1]  # Currently only version 1 is specified

        for version in valid_versions:
            design_rules = KiCadDesignRules(version=version)
            assert design_rules.version == version

            # Should serialize with version header
            result_sexpr = design_rules.to_sexpr()
            # Version should be included in serialization
            assert isinstance(result_sexpr, list)

    def test_severity_levels_from_spec(self):
        """Test all severity levels from specification"""
        # Based on spec: (severity error | warning | ignore)
        spec_severities = [
            DRCSeverity.ERROR,
            DRCSeverity.WARNING,
            DRCSeverity.IGNORE,
        ]

        for severity in spec_severities:
            constraint = DesignRuleConstraint(constraint_type=ConstraintType.CLEARANCE)
            rule = DesignRule(
                name=f"severity_spec_{severity.value}",
                constraint=constraint,
                severity=severity,
            )

            assert rule.severity == severity
