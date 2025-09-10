"""
KiCad Design Rules S-Expression Classes

This module contains classes for KiCad custom design rules file format (.kicad_dru),
supporting the custom design rule system with conditions, constraints, and layer specifications.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional, Union

from .kicad_common import (
    KiCadObject,
    SExpr,
    Symbol,
    sexpr_to_str,
    str_to_sexpr,
)


class DRCSeverity(Enum):
    """DRC violation severity levels"""

    ERROR = "error"
    WARNING = "warning"
    EXCLUSION = "exclusion"
    IGNORE = "ignore"


class ConstraintType(Enum):
    """Design rule constraint types"""

    CLEARANCE = "clearance"
    TRACK_WIDTH = "track_width"
    VIA_SIZE = "via_size"
    VIA_DRILL = "via_drill"
    HOLE_CLEARANCE = "hole_clearance"
    EDGE_CLEARANCE = "edge_clearance"
    HOLE_SIZE = "hole_size"
    COURTYARD_CLEARANCE = "courtyard_clearance"
    SILK_CLEARANCE = "silk_clearance"
    LENGTH = "length"
    SKEW = "skew"
    DISALLOW = "disallow"
    ZONE_CONNECTION = "zone_connection"
    THERMAL_RELIEF_GAP = "thermal_relief_gap"
    THERMAL_SPOKE_WIDTH = "thermal_spoke_width"
    MIN_RESOLVED_SPOKES = "min_resolved_spokes"


class DisallowType(Enum):
    """Types of objects that can be disallowed"""

    TRACK = "track"
    VIA = "via"
    MICRO_VIA = "micro_via"
    BURIED_VIA = "buried_via"
    PAD = "pad"
    FOOTPRINT = "footprint"
    TEXT = "text"
    GRAPHIC = "graphic"
    HOLE = "hole"
    COPPER_POUR = "copper_pour"
    ZONE = "zone"


@dataclass
class ConstraintValue(KiCadObject):
    """Design rule constraint value (min/max/opt)"""

    min_value: Optional[Union[float, str]] = None
    max_value: Optional[Union[float, str]] = None
    opt_value: Optional[Union[float, str]] = None

    @staticmethod
    def _parse_value(value: Any) -> Union[float, str]:
        """Parse value, trying float first, then string as fallback"""
        try:
            return float(value)
        except (ValueError, TypeError):
            return str(value)

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "ConstraintValue":
        """Parse constraint value from S-expression"""
        constraint_value = cls()

        # Handle different constraint value formats
        if isinstance(sexpr, list):
            for item in sexpr:
                if isinstance(item, list) and len(item) >= 2:
                    if item[0] == Symbol("min"):
                        constraint_value.min_value = cls._parse_value(item[1])
                    elif item[0] == Symbol("max"):
                        constraint_value.max_value = cls._parse_value(item[1])
                    elif item[0] == Symbol("opt"):
                        constraint_value.opt_value = cls._parse_value(item[1])

        return constraint_value

    def to_sexpr(self) -> SExpr:
        """Convert constraint value to S-expression"""
        result = []

        if self.min_value is not None:
            result.append([Symbol("min"), self.min_value])
        if self.opt_value is not None:
            result.append([Symbol("opt"), self.opt_value])
        if self.max_value is not None:
            result.append([Symbol("max"), self.max_value])

        return result


@dataclass
class DesignRuleConstraint(KiCadObject):
    """Design rule constraint definition"""

    constraint_type: ConstraintType
    value: Optional[ConstraintValue] = None
    disallow_types: List[DisallowType] = field(default_factory=list)

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "DesignRuleConstraint":
        """Parse design rule constraint from S-expression"""
        if not isinstance(sexpr, list) or len(sexpr) < 2:
            raise ValueError("Invalid constraint S-expression")

        constraint_type_str = str(sexpr[1])
        constraint_type = ConstraintType(constraint_type_str)

        constraint = cls(constraint_type=constraint_type)

        # Parse constraint arguments
        if constraint_type == ConstraintType.DISALLOW:
            # Handle disallow constraint - remaining items are disallowed types
            for i in range(2, len(sexpr)):
                disallow_type = DisallowType(str(sexpr[i]))
                constraint.disallow_types.append(disallow_type)
        else:
            # Handle value-based constraints
            if len(sexpr) > 2:
                constraint.value = ConstraintValue.from_sexpr(sexpr[2:])

        return constraint

    def to_sexpr(self) -> SExpr:
        """Convert design rule constraint to S-expression"""
        result: SExpr = [Symbol("constraint"), Symbol(self.constraint_type.value)]

        if self.constraint_type == ConstraintType.DISALLOW:
            # Add disallow types
            for disallow_type in self.disallow_types:
                result.append(Symbol(disallow_type.value))
        elif self.value:
            # Add constraint value
            value_sexpr = self.value.to_sexpr()
            if isinstance(value_sexpr, list):
                result.extend(value_sexpr)
            else:
                result.append(value_sexpr)  # type: ignore[unreachable]

        return result


@dataclass
class DesignRule(KiCadObject):
    """Custom design rule definition"""

    name: str
    constraint: DesignRuleConstraint
    severity: Optional[DRCSeverity] = None
    layer: Optional[str] = None
    condition: Optional[str] = None

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "DesignRule":
        """Parse design rule from S-expression"""
        if not isinstance(sexpr, list) or len(sexpr) < 3:
            raise ValueError("Invalid rule S-expression")

        name = str(sexpr[1])
        rule = cls(name=name, constraint=DesignRuleConstraint(ConstraintType.CLEARANCE))

        # Parse rule clauses
        for item in sexpr[2:]:
            if not isinstance(item, list) or len(item) < 2:
                continue

            clause_type = str(item[0])

            if clause_type == "severity":
                rule.severity = DRCSeverity(str(item[1]))

            elif clause_type == "layer":
                rule.layer = str(item[1])

            elif clause_type == "condition":
                rule.condition = str(item[1])

            elif clause_type == "constraint":
                rule.constraint = DesignRuleConstraint.from_sexpr(item)

        return rule

    def to_sexpr(self) -> SExpr:
        """Convert design rule to S-expression"""
        result: SExpr = [Symbol("rule"), self.name]

        if self.severity:
            result.append([Symbol("severity"), Symbol(self.severity.value)])

        if self.layer:
            result.append([Symbol("layer"), self.layer])

        if self.condition:
            result.append([Symbol("condition"), self.condition])

        result.append(self.constraint.to_sexpr())

        return result


@dataclass
class KiCadDesignRules(KiCadObject):
    """KiCad design rules file (.kicad_dru)"""

    version: int = 1
    rules: List[DesignRule] = field(default_factory=list)

    @classmethod
    def from_sexpr(cls, sexpr: SExpr) -> "KiCadDesignRules":
        """Parse design rules file from S-expression"""
        design_rules = cls()

        if not isinstance(sexpr, list):
            # Handle case where input is not a list
            sexpr = [sexpr]  # type: ignore[unreachable]

        # Parse each top-level S-expression
        for item in sexpr:
            if not isinstance(item, list):
                continue

            if len(item) >= 2 and str(item[0]) == "version":
                design_rules.version = int(item[1])

            elif len(item) >= 3 and str(item[0]) == "rule":
                rule = DesignRule.from_sexpr(item)
                design_rules.rules.append(rule)

        return design_rules

    def to_sexpr(self) -> List[SExpr]:
        """Convert design rules to list of S-expressions"""
        result = []

        # Add version header
        result.append([Symbol("version"), self.version])

        # Add rules
        for rule in self.rules:
            result.append(rule.to_sexpr())

        return result

    def add_rule(self, rule: DesignRule) -> None:
        """Add a design rule"""
        self.rules.append(rule)

    def remove_rule(self, name: str) -> bool:
        """Remove a design rule by name"""
        original_length = len(self.rules)
        self.rules = [rule for rule in self.rules if rule.name != name]
        return len(self.rules) < original_length

    def get_rule(self, name: str) -> Optional[DesignRule]:
        """Get a design rule by name"""
        for rule in self.rules:
            if rule.name == name:
                return rule
        return None

    def get_rules_by_layer(self, layer: str) -> List[DesignRule]:
        """Get all rules for a specific layer"""
        return [rule for rule in self.rules if rule.layer == layer]

    def get_rules_by_constraint_type(
        self, constraint_type: ConstraintType
    ) -> List[DesignRule]:
        """Get all rules with a specific constraint type"""
        return [
            rule
            for rule in self.rules
            if rule.constraint.constraint_type == constraint_type
        ]


# High-level API functions


def parse_kicad_design_rules_file(file_content: str) -> KiCadDesignRules:
    """Parse KiCad design rules file from string content"""

    # Remove comments and empty lines
    lines = [
        line
        for line in file_content.split("\n")
        if line.strip() and not line.strip().startswith("#")
    ]

    if not lines:
        return KiCadDesignRules()

    # Wrap content in parentheses and parse
    content = f"({'\n'.join(lines)})"

    sexpr = str_to_sexpr(content)
    return KiCadDesignRules.from_sexpr(sexpr)


def write_kicad_design_rules_file(design_rules: KiCadDesignRules) -> str:
    """Write KiCad design rules to string"""

    result_lines = []
    sexprs = design_rules.to_sexpr()

    for sexpr in sexprs:
        result_lines.append(sexpr_to_str(sexpr, pretty_print=True))

    return "\n".join(result_lines)


def load_design_rules(filepath: str) -> KiCadDesignRules:
    """Load KiCad design rules from .kicad_dru file"""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    return parse_kicad_design_rules_file(content)


def save_design_rules(design_rules: KiCadDesignRules, filepath: str) -> None:
    """Save KiCad design rules to .kicad_dru file"""
    content = write_kicad_design_rules_file(design_rules)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


def create_basic_design_rules() -> KiCadDesignRules:
    """Create a basic design rules file with common rules"""
    design_rules = KiCadDesignRules(version=1)

    # Example clearance rule
    clearance_constraint = DesignRuleConstraint(
        constraint_type=ConstraintType.CLEARANCE, value=ConstraintValue(min_value=0.2)
    )
    clearance_rule = DesignRule(name="basic_clearance", constraint=clearance_constraint)
    design_rules.add_rule(clearance_rule)

    return design_rules
