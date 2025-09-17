#!/usr/bin/env python3
"""
Robust parser for sexpr-*/_index.en.adoc files to extract sections and tokens.

This parser extracts structured information from AsciiDoc files:
- Sections starting with == at line beginning
- First `token` in the first paragraph of each section
- Code blocks enclosed in ``` ... ```
- Annotation blocks starting with <1>, <2>, etc.

Usage Examples:
    # Parse all sexpr documentation files
    python parse_sexpr_docs.py

    # Parse specific file with verbose output
    python parse_sexpr_docs.py --verbose doc/file-formats/sexpr-symbol-lib/_index.en.adoc

    # Run with strict validation (fails on warnings)
    python parse_sexpr_docs.py --strict

    # Show debug output during parsing
    python parse_sexpr_docs.py --debug

    # Test the parser with sample data
    python parse_sexpr_docs.py --test

    # Parse annotations to extract token names, optionality, etc.
    python parse_sexpr_docs.py --parse-annotations

    # Parse S-expression code blocks for structured information
    python parse_sexpr_docs.py --parse-code-blocks

    # Parse both annotations and code blocks with linking
    python parse_sexpr_docs.py --parse-annotations --parse-code-blocks

    # Export parsed sections to YAML files
    python parse_sexpr_docs.py --export-yaml --parse-annotations --parse-code-blocks

    # Export to custom directory
    python parse_sexpr_docs.py --export-yaml --yaml-output-dir custom/output/

    # Parse multiple specific files
    python parse_sexpr_docs.py doc/file-formats/sexpr-*/_index.en.adoc

    # Get help with all options
    python parse_sexpr_docs.py --help

Expected Output:
    - Found tokens: kicad_symbol_lib, footprint, kicad_sch, etc.
    - Code blocks with S-expression syntax and inline annotations
    - Annotation explanations linked to code references
    - Validation warnings for missing/unused annotations
    - Summary statistics per file
"""

import glob
import os
import re
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml


class ParseState(Enum):
    """Parsing states for the state machine."""

    NORMAL = "normal"
    CODE_BLOCK = "code_block"
    ANNOTATION = "annotation"


class ParseError(Exception):
    """Custom exception for parsing errors."""

    pass


@dataclass
class ParsedAnnotation:
    """Represents parsed structured information from an annotation."""

    token_name: Optional[str] = None
    is_optional: bool = False
    description: str = ""
    attribute_type: Optional[str] = None  # e.g., "token", "attribute", "section"

    def __str__(self) -> str:
        parts = []
        if self.token_name:
            parts.append(f"Token: {self.token_name}")
        if self.is_optional:
            parts.append("Optional")
        if self.attribute_type:
            parts.append(f"Type: {self.attribute_type}")
        if self.description:
            parts.append(
                f"Description: {self.description[:100]}{'...' if len(self.description) > 100 else ''}"
            )
        return " | ".join(parts)


class AnnotationParser:
    """Utility class for parsing annotation content."""

    @staticmethod
    def parse_annotation_text(text: str) -> ParsedAnnotation:
        """
        Parse annotation text to extract structured information.

        Examples:
        - "The `version` token attribute defines..."
        - "The optional `scale` token attribute..."
        - "The WIDTH attribute defines the width..."
        """
        parsed = ParsedAnnotation()

        # Clean up the text
        text = text.strip()
        parsed.description = text

        # Check for optionality
        parsed.is_optional = AnnotationParser._is_optional(text)

        # Extract token name
        parsed.token_name = AnnotationParser._extract_token_name(text)

        # Determine attribute type
        parsed.attribute_type = AnnotationParser._determine_type(text)

        return parsed

    @staticmethod
    def _is_optional(text: str) -> bool:
        """Check if the annotation describes an optional element."""
        optional_patterns = [
            r"\boptional\b",
            r"\[.*\]",  # Square brackets often indicate optional
            r"\bmay\b",
            r"\bcan be\b",
            r"\bif defined\b",
            r"\bif not defined\b",
        ]

        text_lower = text.lower()
        for pattern in optional_patterns:
            if re.search(pattern, text_lower):
                return True
        return False

    @staticmethod
    def _extract_token_name(text: str) -> Optional[str]:
        """Extract token name from annotation text."""
        # Pattern 1: `token_name` token
        match = re.search(r"`([^`]+)`\s+token", text)
        if match:
            return match.group(1)

        # Pattern 2: `token_name` attribute
        match = re.search(r"`([^`]+)`\s+attribute", text)
        if match:
            return match.group(1)

        # Pattern 3: The `token_name`
        match = re.search(r"The\s+`([^`]+)`\s+", text)
        if match:
            return match.group(1)

        # Pattern 4: uppercase ATTRIBUTE_NAME
        match = re.search(r"\b([A-Z][A-Z_]+)\b", text)
        if match:
            # Avoid common words
            token = match.group(1)
            if token not in [
                "THE",
                "AND",
                "OR",
                "NOT",
                "IF",
                "IS",
                "OF",
                "TO",
                "IN",
                "ON",
                "AT",
                "BY",
            ]:
                return token.lower()

        return None

    @staticmethod
    def _determine_type(text: str) -> Optional[str]:
        """Determine the type of the annotation (token, attribute, section, etc.)."""
        text_lower = text.lower()

        if "token" in text_lower:
            if "attribute" in text_lower:
                return "token_attribute"
            else:
                return "token"
        elif "attribute" in text_lower:
            return "attribute"
        elif "section" in text_lower:
            return "section"
        elif "identifier" in text_lower:
            return "identifier"
        elif "definition" in text_lower:
            return "definition"
        else:
            return "other"


@dataclass
class ParsedCodeElement:
    """Represents a parsed element in S-expression code."""

    token_name: str
    attributes: List[str] = field(default_factory=list)
    children: List["ParsedCodeElement"] = field(default_factory=list)
    annotation_ref: Optional[int] = None
    line_number: int = 0
    is_list: bool = True  # True for (token ...), False for simple values
    is_optional: bool = False  # True if token was wrapped in [] brackets

    def __str__(self) -> str:
        if self.is_list:
            parts = [self.token_name] + self.attributes
            if self.children:
                parts.append(f"[{len(self.children)} children]")
            if self.annotation_ref:
                parts.append(f"<{self.annotation_ref}>")
            return f"({' '.join(parts)})"
        else:
            return self.token_name


@dataclass
class ParsedCodeBlock:
    """Represents parsed structured information from a code block."""

    root_elements: List[ParsedCodeElement] = field(default_factory=list)
    annotation_map: Dict[int, ParsedCodeElement] = field(
        default_factory=dict
    )  # Maps annotation numbers to elements

    def get_element_by_annotation(
        self, annotation_num: int
    ) -> Optional[ParsedCodeElement]:
        """Get the code element that has the given annotation reference."""
        return self.annotation_map.get(annotation_num)


class CodeBlockParser:
    """Utility class for parsing S-expression code blocks."""

    @staticmethod
    def parse_sexpr_text(text: str) -> ParsedCodeBlock:
        """
        Parse S-expression text to extract structured information.

        Examples:
        - (kicad_symbol_lib (version VERSION) <1> (generator GENERATOR) <2>)
        - (footprint "NAME" <1> (version VERSION) <2>)
        """
        parsed_block = ParsedCodeBlock()

        # Clean up the text and split into lines
        lines = text.strip().split("\n")
        if not lines:
            return parsed_block

        # Parse each significant line
        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line or line.startswith(";"):  # Skip empty lines and comments
                continue

            # Parse this line for S-expression elements
            elements = CodeBlockParser._parse_line(line, line_num)
            for element in elements:
                parsed_block.root_elements.append(element)
                # Map annotation references
                if element.annotation_ref:
                    parsed_block.annotation_map[element.annotation_ref] = element

        return parsed_block

    @staticmethod
    def _parse_line(line: str, line_num: int) -> List[ParsedCodeElement]:
        """Parse a single line for S-expression elements."""
        elements = []

        # Look for annotation references first
        annotation_refs = {}
        for match in re.finditer(r"<(\d+)>", line):
            annotation_refs[match.start()] = int(match.group(1))

        # Remove annotation references for parsing
        clean_line = re.sub(r"\s*<\d+>", "", line)

        # Simple S-expression parsing - look for (token ...)
        paren_matches = list(re.finditer(r"\(([^)]+)\)", clean_line))

        for match in paren_matches:
            content = match.group(1).strip()
            parts = content.split()

            if parts:
                # Clean token name - remove brackets that indicate optionality
                token_name = parts[0]
                token_name = re.sub(
                    r"^\[|\]$", "", token_name
                )  # Remove leading [ and trailing ]

                # Determine if this token is optional based on brackets
                is_optional = parts[0].startswith("[") and parts[0].endswith("]")

                element = ParsedCodeElement(
                    token_name=token_name,
                    attributes=parts[1:] if len(parts) > 1 else [],
                    line_number=line_num,
                    is_list=True,
                )

                # Store optionality information
                element.is_optional = is_optional

                # Find closest annotation reference
                match_pos = match.start()
                closest_annotation = None
                min_distance = float("inf")

                for ref_pos, ref_num in annotation_refs.items():
                    distance = abs(ref_pos - match_pos)
                    if distance < min_distance:
                        min_distance = distance
                        closest_annotation = ref_num

                element.annotation_ref = closest_annotation
                elements.append(element)

        # If no parentheses found, try to parse as simple tokens
        if not elements and clean_line:
            parts = clean_line.split()
            for i, part in enumerate(parts):
                if part and not part.startswith(";;"):  # Skip comments
                    # Clean token name - remove brackets that indicate optionality
                    original_part = part
                    token_name = re.sub(
                        r"^\[|\]$", "", part
                    )  # Remove leading [ and trailing ]

                    # Skip if this results in an empty token
                    if not token_name:
                        continue

                    # Determine if this token is optional based on brackets
                    is_optional = original_part.startswith(
                        "["
                    ) and original_part.endswith("]")

                    element = ParsedCodeElement(
                        token_name=token_name,
                        line_number=line_num,
                        is_list=False,
                        is_optional=is_optional,
                    )

                    # Check for annotation reference near this token
                    for ref_pos, ref_num in annotation_refs.items():
                        # Simple heuristic: annotation belongs to token if close enough
                        if abs(ref_pos - line.find(part)) < 50:  # 50 char tolerance
                            element.annotation_ref = ref_num
                            break

                    elements.append(element)

        return elements


@dataclass
class Annotation:
    """Represents an annotation block."""

    number: int
    content: List[str] = field(default_factory=list)
    line_number: int = 0
    parsed: Optional[ParsedAnnotation] = None

    def add_line(self, line: str) -> None:
        """Add a line to the annotation content."""
        self.content.append(line.rstrip())

    def get_text(self) -> str:
        """Get the complete annotation text."""
        return "\n".join(self.content)

    def parse_content(self) -> None:
        """Parse the annotation content to extract structured information."""
        if not self.content:
            return

        full_text = self.get_text()
        self.parsed = AnnotationParser.parse_annotation_text(full_text)


@dataclass
class CodeBlock:
    """Represents a code block."""

    content: List[str] = field(default_factory=list)
    annotations: Dict[int, int] = field(
        default_factory=dict
    )  # Maps annotation numbers to line indices
    line_number: int = 0
    parsed: Optional[ParsedCodeBlock] = None

    def add_line(self, line: str) -> None:
        """Add a line to the code block and detect inline annotations."""
        # Check for inline annotations like <1>, <2>, etc.
        annotation_match = re.search(r"<(\d+)>", line)
        if annotation_match:
            self.annotations[int(annotation_match.group(1))] = len(self.content)
        self.content.append(line.rstrip())

    def get_text(self) -> str:
        """Get the complete code block text."""
        return "\n".join(self.content)

    def parse_content(self) -> None:
        """Parse the S-expression content to extract structured information."""
        if not self.content:
            return

        full_text = self.get_text()
        self.parsed = CodeBlockParser.parse_sexpr_text(full_text)


@dataclass
class Section:
    """Represents a section in the AsciiDoc file."""

    title: str
    line_number: int
    token: Optional[str] = None
    code_blocks: List[CodeBlock] = field(default_factory=list)
    annotations: List[Annotation] = field(default_factory=list)
    raw_content: List[str] = field(default_factory=list)

    def link_code_and_annotations(self) -> None:
        """Link parsed code blocks with their corresponding annotations."""
        if not (self.code_blocks and self.annotations):
            return

        # Create a mapping of annotation numbers to annotation objects
        annotation_map = {ann.number: ann for ann in self.annotations}

        # For each code block, try to link with annotations
        for block in self.code_blocks:
            if block.parsed:
                for element in block.parsed.root_elements:
                    if (
                        element.annotation_ref
                        and element.annotation_ref in annotation_map
                    ):
                        # Link found - we could store additional cross-references here
                        pass

    def validate(self) -> Tuple[bool, List[str]]:
        """
        Validate the section structure.
        Returns (is_valid, list_of_warnings)
        """
        warnings = []

        # Check if annotations match code block references
        if self.code_blocks and self.annotations:
            code_annotation_refs = set()
            for block in self.code_blocks:
                code_annotation_refs.update(block.annotations.keys())

            annotation_numbers = {ann.number for ann in self.annotations}

            # Check for missing annotations
            missing = code_annotation_refs - annotation_numbers
            if missing:
                warnings.append(
                    f"Code references annotations {missing} but they are not defined"
                )

            # Check for unused annotations
            unused = annotation_numbers - code_annotation_refs
            if unused:
                warnings.append(
                    f"Annotations {unused} are defined but not referenced in code"
                )

        # Warn if no token found
        if not self.token:
            warnings.append("No token found in first paragraph")

        return len(warnings) == 0, warnings


class AsciiDocParser:
    """Parser for AsciiDoc files with KiCad documentation structure."""

    def __init__(
        self,
        strict_mode: bool = False,
        debug: bool = False,
        parse_annotations: bool = False,
        parse_code_blocks: bool = False,
    ):
        """
        Initialize the parser.

        Args:
            strict_mode: If True, parser will raise exceptions on validation errors
            debug: If True, show debug output during parsing
            parse_annotations: If True, parse annotation content for structured information
            parse_code_blocks: If True, parse S-expression code blocks for structured information
        """
        self.strict_mode = strict_mode
        self.debug = debug
        self.parse_annotations = parse_annotations
        self.parse_code_blocks = parse_code_blocks
        self.state = ParseState.NORMAL
        self.current_section: Optional[Section] = None
        self.sections: List[Section] = []
        self.current_code_block: Optional[CodeBlock] = None
        self.current_annotation: Optional[Annotation] = None
        self.first_paragraph_complete = False

    def parse_file(self, file_path: str) -> List[Section]:
        """
        Parse an AsciiDoc file and extract sections.

        Args:
            file_path: Path to the AsciiDoc file

        Returns:
            List of parsed sections

        Raises:
            ParseError: If strict_mode is True and validation fails
        """
        # Reset parser state for new file
        self.sections = []
        self.state = ParseState.NORMAL
        self.current_section = None
        self.current_code_block = None
        self.current_annotation = None
        self.first_paragraph_complete = False

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except IOError as e:
            raise ParseError(f"Failed to read file {file_path}: {e}")

        for line_num, line in enumerate(lines, 1):
            self._process_line(line, line_num)

        # Finalize last section
        self._finalize_current_section()

        # Validate all sections if in strict mode
        if self.strict_mode:
            self._validate_all_sections()

        return self.sections

    def _process_line(self, line: str, line_num: int) -> None:
        """Process a single line based on current state."""
        # Check for section header
        if line.startswith("=="):
            self._handle_section_header(line, line_num)
            return

        # If no current section, skip line
        if not self.current_section:
            return

        # Add to raw content
        self.current_section.raw_content.append(line)

        # Process based on state
        if self.state == ParseState.CODE_BLOCK:
            self._handle_code_block_line(line, line_num)
        elif self.state == ParseState.ANNOTATION:
            self._handle_annotation_line(line, line_num)
        else:
            self._handle_normal_line(line, line_num)

    def _handle_section_header(self, line: str, line_num: int) -> None:
        """Handle a section header line."""
        # Finalize previous section
        self._finalize_current_section()

        # Start new section
        self.current_section = Section(title=line.strip(), line_number=line_num)
        self.state = ParseState.NORMAL
        self.first_paragraph_complete = False
        self.current_code_block = None
        self.current_annotation = None

        if self.debug:
            print(f"DEBUG [line {line_num}]: Starting new section '{line.strip()}'")

    def _handle_normal_line(self, line: str, line_num: int) -> None:
        """Handle a line in normal parsing state."""
        stripped = line.strip()

        # Check for code block start
        if stripped == "```":
            self.state = ParseState.CODE_BLOCK
            self.current_code_block = CodeBlock(line_number=line_num)
            self.first_paragraph_complete = True
            return

        # Check for annotation start
        annotation_match = re.match(r"^<(\d+)>", stripped)
        if annotation_match:
            self._start_annotation(int(annotation_match.group(1)), line, line_num)
            return

        # Look for token in first paragraph
        if (
            not self.first_paragraph_complete
            and self.current_section
            and not self.current_section.token
        ):
            if not stripped.startswith(("NOTE:", "WARNING:", "TIP:")):
                token_match = re.search(r"`([^`]+)`\s+token", line)
                if token_match:
                    self.current_section.token = token_match.group(1)
                    if self.debug:
                        print(
                            f"DEBUG [line {line_num}]: Found token '{self.current_section.token}'"
                        )

        # Mark first paragraph complete when we hit special blocks (but not empty lines immediately after header)
        if not self.first_paragraph_complete and self.current_section:
            # Skip empty lines right after section headers
            if stripped and stripped.startswith(("```", "....", "|====", "[options")):
                self.first_paragraph_complete = True
                if self.debug:
                    print(
                        f"DEBUG [line {line_num}]: First paragraph complete (special block)"
                    )

    def _handle_code_block_line(self, line: str, line_num: int) -> None:
        """Handle a line inside a code block."""
        stripped = line.strip()

        # Check for code block end
        if stripped == "```":
            if self.current_code_block and self.current_section:
                # Parse the code block content if enabled
                if self.parse_code_blocks:
                    self.current_code_block.parse_content()
                self.current_section.code_blocks.append(self.current_code_block)
                self.current_code_block = None
            self.state = ParseState.NORMAL
        elif self.current_code_block:
            self.current_code_block.add_line(line.rstrip())

    def _handle_annotation_line(self, line: str, line_num: int) -> None:
        """Handle a line inside an annotation block."""
        stripped = line.strip()

        # Check for annotation end (empty line or new section/annotation)
        if not stripped or stripped.startswith("=="):
            self._finalize_annotation()
            self.state = ParseState.NORMAL
            return

        # Check for new annotation
        annotation_match = re.match(r"^<(\d+)>", stripped)
        if annotation_match:
            self._finalize_annotation()
            self._start_annotation(int(annotation_match.group(1)), line, line_num)
        elif self.current_annotation:
            self.current_annotation.add_line(line.rstrip())

    def _start_annotation(self, number: int, line: str, line_num: int) -> None:
        """Start a new annotation block."""
        self._finalize_annotation()
        self.current_annotation = Annotation(number=number, line_number=line_num)
        # Add the content after <n>
        content_after_marker = re.sub(r"^<\d+>\s*", "", line.strip())
        if content_after_marker:
            self.current_annotation.add_line(content_after_marker)
        self.state = ParseState.ANNOTATION

    def _finalize_annotation(self) -> None:
        """Finalize current annotation and add to section."""
        if self.current_annotation and self.current_section:
            if self.current_annotation.content:  # Only add if has content
                # Parse the annotation content if enabled
                if self.parse_annotations:
                    self.current_annotation.parse_content()
                self.current_section.annotations.append(self.current_annotation)
            self.current_annotation = None

    def _finalize_current_section(self) -> None:
        """Finalize the current section."""
        if not self.current_section:
            return

        # Clean up any pending states
        if self.current_code_block:
            if self.strict_mode:
                raise ParseError(
                    f"Unclosed code block in section {self.current_section.title}"
                )
            # Parse the code block content if enabled
            if self.parse_code_blocks:
                self.current_code_block.parse_content()
            self.current_section.code_blocks.append(self.current_code_block)

        if self.current_annotation:
            self._finalize_annotation()

        # Link code blocks and annotations
        if self.parse_code_blocks and self.parse_annotations:
            self.current_section.link_code_and_annotations()

        self.sections.append(self.current_section)
        self.current_section = None

    def _validate_all_sections(self) -> None:
        """Validate all parsed sections."""
        errors = []
        for section in self.sections:
            is_valid, warnings = section.validate()
            if not is_valid:
                errors.append(
                    f"Section '{section.title}' (line {section.line_number}): {'; '.join(warnings)}"
                )

        if errors and self.strict_mode:
            raise ParseError("Validation errors:\n" + "\n".join(errors))


class TextExporter:
    """Utility class for exporting parsed sections to text files."""

    @staticmethod
    def sanitize_filename(text: str) -> str:
        """Convert section title to valid filename."""
        # Remove == markers and clean up
        text = re.sub(r"^=+\s*", "", text)
        text = re.sub(r"\s*=+$", "", text)

        # Replace problematic characters
        text = re.sub(r"[^\w\s-]", "", text)
        text = re.sub(r"\s+", "_", text)
        text = text.lower().strip("_")

        # Ensure it's not empty
        if not text:
            text = "unnamed_section"

        return text

    @staticmethod
    def export_section(section: Section, output_dir: Path, source_file: str) -> str:
        """Export a single section to a text file with title and token headers."""
        # Create filename based on section title
        filename = TextExporter.sanitize_filename(section.title)
        if not filename.endswith(".txt"):
            filename += ".txt"

        # Create full path
        output_path = output_dir / filename

        # Create the text content
        content_lines = []

        # Add title header
        section_title = re.sub(r"^=+\s*", "", section.title)
        section_title = re.sub(r"\s*=+$", "", section_title)
        content_lines.append(f"title: {section_title}")

        # Add token header
        token_name = section.token if section.token else "unknown"
        content_lines.append(f"token: {token_name}")
        content_lines.append("")  # Empty line after headers

        # Add the complete raw content of the section (preserving everything)
        for line in section.raw_content:
            content_lines.append(line.rstrip())

        # Export to text file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(content_lines))

        return str(output_path)

    @staticmethod
    def export_sections(
        sections: List[Section], output_dir: Path, source_file: str
    ) -> List[str]:
        """Export multiple sections to separate text files."""
        output_dir.mkdir(parents=True, exist_ok=True)
        exported_files = []

        for section in sections:
            # Only export sections with tokens (unless we want all sections)
            if section.token:
                output_file = TextExporter.export_section(
                    section, output_dir, source_file
                )
                exported_files.append(output_file)

        return exported_files


class YamlExporter:
    """Utility class for exporting parsed sections to YAML files."""

    @staticmethod
    def sanitize_filename(text: str) -> str:
        """Convert section title to valid filename."""
        # Remove == markers and clean up
        text = re.sub(r"^=+\s*", "", text)
        text = re.sub(r"\s*=+$", "", text)

        # Replace problematic characters
        text = re.sub(r"[^\w\s-]", "", text)
        text = re.sub(r"\s+", "_", text)
        text = text.lower().strip("_")

        # Ensure it's not empty
        if not text:
            text = "unnamed_section"

        return text

    @staticmethod
    def section_to_dict(section: Section) -> Dict:
        """Convert a Section object to a dictionary suitable for YAML export."""
        result = {"title": section.title, "token": section.token}

        # Only add validation info if there are warnings
        is_valid, warnings = section.validate()
        if warnings:
            result["warnings"] = warnings

        # Add code blocks
        if section.code_blocks:
            result["code_blocks"] = []
            for block in section.code_blocks:
                block_data = {"content": block.get_text()}

                # Add parsed elements if available
                if block.parsed and block.parsed.root_elements:
                    block_data["parsed_elements"] = []
                    for element in block.parsed.root_elements:
                        element_data = {
                            "token_name": element.token_name,
                            "attributes": (
                                element.attributes if element.attributes else None
                            ),
                            "is_optional": (
                                element.is_optional if element.is_optional else None
                            ),
                        }
                        # Remove None values
                        element_data = {
                            k: v for k, v in element_data.items() if v is not None
                        }
                        block_data["parsed_elements"].append(element_data)

                result["code_blocks"].append(block_data)

        # Add annotations
        if section.annotations:
            result["annotations"] = []
            for ann in section.annotations:
                ann_data = {"number": ann.number, "content": ann.get_text()}

                # Add parsed annotation data if available and useful
                if ann.parsed:
                    parsed_data = {}
                    if ann.parsed.token_name:
                        parsed_data["token_name"] = ann.parsed.token_name
                    if ann.parsed.is_optional:
                        parsed_data["is_optional"] = ann.parsed.is_optional
                    if (
                        ann.parsed.attribute_type
                        and ann.parsed.attribute_type != "other"
                    ):
                        parsed_data["attribute_type"] = ann.parsed.attribute_type

                    if parsed_data:
                        ann_data["parsed"] = parsed_data

                result["annotations"].append(ann_data)

        return result

    @staticmethod
    def export_section(section: Section, output_dir: Path, source_file: str) -> str:
        """Export a single section to a YAML file."""
        # Create filename based on section title
        filename = YamlExporter.sanitize_filename(section.title)
        if not filename.endswith(".yaml"):
            filename += ".yaml"

        # Create full path
        output_path = output_dir / filename

        # Convert section to dictionary
        section_data = YamlExporter.section_to_dict(section)

        # Export to YAML
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(
                section_data,
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )

        return str(output_path)

    @staticmethod
    def export_sections(
        sections: List[Section], output_dir: Path, source_file: str
    ) -> List[str]:
        """Export multiple sections to separate YAML files."""
        output_dir.mkdir(parents=True, exist_ok=True)
        exported_files = []

        for section in sections:
            # Only export sections with tokens (unless we want all sections)
            if section.token:
                output_file = YamlExporter.export_section(
                    section, output_dir, source_file
                )
                exported_files.append(output_file)

        return exported_files


class AsciiDocPrinter:
    """Utility class for printing parsed sections."""

    @staticmethod
    def print_section(section: Section, verbose: bool = False) -> None:
        """Print a parsed section."""
        print(f"\n{'='*60}")
        print(f"SECTION: {section.title} (line {section.line_number})")

        if section.token:
            print(f"TOKEN: {section.token}")
        else:
            print("TOKEN: [NOT FOUND]")

        # Validate and show warnings
        _, warnings = section.validate()
        if warnings:
            print(f"WARNINGS: {'; '.join(warnings)}")

        # Print code blocks
        if section.code_blocks:
            print(f"\nCODE BLOCKS ({len(section.code_blocks)}):")
            for i, block in enumerate(section.code_blocks, 1):
                print(f"  Block {i} (line {block.line_number}):")
                for line in block.get_text().split("\n")[:5]:  # Show first 5 lines
                    print(f"    {line}")
                if len(block.content) > 5:
                    print(f"    ... ({len(block.content) - 5} more lines)")
                if block.annotations:
                    print(f"    References: {sorted(block.annotations.keys())}")

                # Show parsed elements if available
                if block.parsed and block.parsed.root_elements:
                    print(f"    Parsed Elements:")
                    for element in block.parsed.root_elements:
                        if element.annotation_ref:
                            print(f"      {element} -> <{element.annotation_ref}>")
                        else:
                            print(f"      {element}")
                    if block.parsed.annotation_map:
                        print(
                            f"    Annotation Links: {sorted(block.parsed.annotation_map.keys())}"
                        )

        # Print annotations
        if section.annotations:
            print(f"\nANNOTATIONS ({len(section.annotations)}):")
            for ann in section.annotations:
                text = ann.get_text()
                if len(text) > 100:
                    text = text[:100] + "..."

                # Show parsed information if available
                if ann.parsed and (ann.parsed.token_name or ann.parsed.is_optional):
                    parsed_info = []
                    if ann.parsed.token_name:
                        parsed_info.append(f"Token: {ann.parsed.token_name}")
                    if ann.parsed.is_optional:
                        parsed_info.append("Optional")
                    if ann.parsed.attribute_type:
                        parsed_info.append(f"Type: {ann.parsed.attribute_type}")

                    parsed_str = " | ".join(parsed_info)
                    print(f"  <{ann.number}> [{parsed_str}] {text}")
                else:
                    print(f"  <{ann.number}> {text}")

        if verbose and section.raw_content:
            print(f"\nRAW CONTENT ({len(section.raw_content)} lines)")


def main():
    """Main function to parse all sexpr-*/_index.en.adoc files."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Parse KiCad AsciiDoc documentation files"
    )
    parser.add_argument(
        "--strict", action="store_true", help="Enable strict validation mode"
    )
    parser.add_argument("--verbose", action="store_true", help="Show verbose output")
    parser.add_argument(
        "--debug", action="store_true", help="Show debug output during parsing"
    )
    parser.add_argument("--test", action="store_true", help="Run with test data")
    parser.add_argument(
        "--parse-annotations",
        action="store_true",
        help="Parse annotation content for structured information",
    )
    parser.add_argument(
        "--parse-code-blocks",
        action="store_true",
        help="Parse S-expression code blocks for structured information",
    )
    parser.add_argument(
        "--export-yaml",
        action="store_true",
        help="Export parsed sections to YAML files in doc/parsed/",
    )
    parser.add_argument(
        "--yaml-output-dir",
        default="doc/parsed",
        help="Directory for YAML exports (default: doc/parsed)",
    )
    parser.add_argument(
        "--export-text",
        action="store_true",
        help="Export parsed sections to text files with title and token headers",
    )
    parser.add_argument(
        "--text-output-dir",
        default="doc/parsed/text",
        help="Directory for text exports (default: doc/parsed/text)",
    )
    parser.add_argument("files", nargs="*", help="Specific files to parse")

    args = parser.parse_args()

    if args.test:
        test_parsing()
        return

    # Determine files to parse
    if args.files:
        adoc_files = args.files
    else:
        base_dir = Path(__file__).parent
        pattern = base_dir / "sexpr-*" / "_index.en.adoc"
        adoc_files = glob.glob(str(pattern))

    if not adoc_files:
        print("No files found to parse")
        return

    print(f"Found {len(adoc_files)} file(s) to parse")

    # Parse each file
    doc_parser = AsciiDocParser(
        strict_mode=args.strict,
        debug=args.debug,
        parse_annotations=args.parse_annotations,
        parse_code_blocks=args.parse_code_blocks,
    )
    printer = AsciiDocPrinter()

    for file_path in sorted(adoc_files):
        print(f"\n{'='*80}")
        print(f"FILE: {file_path}")
        print(f"{'='*80}")

        try:
            sections = doc_parser.parse_file(file_path)

            # Export to YAML if requested
            if args.export_yaml:
                output_dir = Path(args.yaml_output_dir)
                source_filename = Path(file_path).name
                exported_files = YamlExporter.export_sections(
                    sections, output_dir, source_filename
                )

                if exported_files:
                    print(f"\nEXPORTED {len(exported_files)} sections to YAML:")
                    for yaml_file in exported_files:
                        print(f"  {yaml_file}")

            # Export to text if requested
            if args.export_text:
                output_dir = Path(args.text_output_dir)
                source_filename = Path(file_path).name
                exported_files = TextExporter.export_sections(
                    sections, output_dir, source_filename
                )

                if exported_files:
                    print(f"\nEXPORTED {len(exported_files)} sections to text:")
                    for text_file in exported_files:
                        print(f"  {text_file}")

            # Print sections if not in export-only mode
            if not (args.export_yaml or args.export_text) or args.verbose:
                for section in sections:
                    if (
                        section.token or args.verbose
                    ):  # Only show sections with tokens unless verbose
                        printer.print_section(section, verbose=args.verbose)

            # Summary
            total = len(sections)
            with_tokens = sum(1 for s in sections if s.token)
            print(f"\nSUMMARY: {with_tokens}/{total} sections have tokens")

        except ParseError as e:
            print(f"ERROR parsing {file_path}: {e}")
            if args.strict:
                break


def test_parsing():
    """Test the parsing logic with sample data."""
    test_content = """== Header Section

The `kicad_symbol_lib` token indicates that it is KiCad symbol library file.

```
(kicad_symbol_lib
  (version VERSION)                                             <1>
  (generator GENERATOR)                                         <2>
)
```

<1> The `version` token attribute defines the symbol library version.
<2> The `generator` token attribute defines the program used to write the file.

== Another Section

The `test_token` token is used for testing.

```
(test_structure
  (field VALUE)  <1>
)
```

<1> This is a test annotation.
<3> This annotation has no reference in code.

== Section Without Token

This section has no token in the first paragraph.
But it mentions `something` token later.
"""

    print("=== TESTING PARSING LOGIC ===\n")

    # Write test content to temporary file
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".adoc", delete=False) as f:
        f.write(test_content)
        temp_file = f.name

    try:
        # Test normal mode
        parser = AsciiDocParser(
            strict_mode=False,
            debug=True,
            parse_annotations=True,
            parse_code_blocks=True,
        )
        sections = parser.parse_file(temp_file)
        printer = AsciiDocPrinter()

        print("NORMAL MODE:")
        for section in sections:
            printer.print_section(section)

        # Test strict mode
        print("\n\nSTRICT MODE:")
        strict_parser = AsciiDocParser(strict_mode=True)
        try:
            sections = strict_parser.parse_file(temp_file)
            print("Parsing succeeded in strict mode")
        except ParseError as e:
            print(f"Expected validation error in strict mode: {e}")

    finally:
        os.unlink(temp_file)


if __name__ == "__main__":
    main()
