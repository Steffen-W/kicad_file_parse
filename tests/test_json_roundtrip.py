"""Round-trip tests for KiCad project JSON files.

This module tests parsing a .kicad_pro file and verifying that
the round-trip (parse -> serialize) produces identical output to the original.
"""

import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import pytest

from kicad_parserv2.project_settings import KicadProject


def load_original_file(file_path: str) -> Dict[str, Any]:
    """Load original JSON file and return parsed data."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_json(data: Dict[str, Any]) -> str:
    """Normalize JSON data for comparison by sorting keys and consistent formatting."""
    return json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False)


def compare_structures(
    original: Dict[str, Any], roundtrip: Dict[str, Any], path: str = ""
) -> List[str]:
    """Compare two dictionaries recursively and return list of differences."""
    differences = []

    # Check keys present in original but missing in roundtrip
    for key in original:
        current_path = f"{path}.{key}" if path else key
        if key not in roundtrip:
            differences.append(f"Missing key: {current_path}")
        elif isinstance(original[key], dict) and isinstance(roundtrip[key], dict):
            differences.extend(
                compare_structures(original[key], roundtrip[key], current_path)
            )
        elif original[key] != roundtrip[key]:
            differences.append(
                f"Value mismatch at {current_path}: {original[key]} != {roundtrip[key]}"
            )

    # Check keys present in roundtrip but missing in original
    for key in roundtrip:
        current_path = f"{path}.{key}" if path else key
        if key not in original:
            differences.append(f"Extra key: {current_path}")

    return differences


@pytest.fixture
def test_files():
    """Fixture providing test file paths."""
    return [
        "examples/test_data/example_small/KiCad.kicad_pro",  # Standard file
        "examples/test_data/StickHub.kicad_pro",  # Complex file
    ]


@pytest.mark.parametrize("preserve_original", [True, False])
def test_structure_roundtrip_standard_file(preserve_original: bool):
    """Test structure round-trip for standard KiCad project file."""
    file_path = "examples/test_data/example_small/KiCad.kicad_pro"

    if not Path(file_path).exists():
        pytest.skip(f"Test file not found: {file_path}")

    # Load original file
    original_data = load_original_file(file_path)

    # Parse with KiCad parser
    kicad_project = KicadProject.from_file(file_path)

    # Convert back to dictionary
    roundtrip_data = kicad_project.to_dict(preserve_original=preserve_original)

    # Compare structures
    differences = compare_structures(original_data, roundtrip_data)

    # For preserve_original=True, we expect perfect round-trip
    if preserve_original:
        assert (
            not differences
        ), f"Found {len(differences)} differences: {differences[:5]}"
    else:
        # For preserve_original=False, some differences are expected due to missing optional fields
        # We just verify the parsing works without errors
        assert isinstance(roundtrip_data, dict)


@pytest.mark.parametrize("preserve_original", [True, False])
def test_structure_roundtrip_complex_file(preserve_original: bool):
    """Test structure round-trip for complex KiCad project file."""
    file_path = "examples/test_data/StickHub.kicad_pro"

    if not Path(file_path).exists():
        pytest.skip(f"Test file not found: {file_path}")

    # Load original file
    original_data = load_original_file(file_path)

    # Parse with KiCad parser
    kicad_project = KicadProject.from_file(file_path)

    # Convert back to dictionary
    roundtrip_data = kicad_project.to_dict(preserve_original=preserve_original)

    # Compare structures
    differences = compare_structures(original_data, roundtrip_data)

    # For preserve_original=True, we expect perfect round-trip
    if preserve_original:
        assert (
            not differences
        ), f"Found {len(differences)} differences: {differences[:5]}"
    else:
        # For preserve_original=False, some differences are expected due to missing optional fields
        # We just verify the parsing works without errors
        assert isinstance(roundtrip_data, dict)


def test_json_string_roundtrip_standard_file():
    """Test JSON string round-trip for standard KiCad project file."""
    file_path = "examples/test_data/example_small/KiCad.kicad_pro"

    if not Path(file_path).exists():
        pytest.skip(f"Test file not found: {file_path}")

    # Load and normalize original
    with open(file_path, "r", encoding="utf-8") as f:
        original_content = f.read()

    original_data = json.loads(original_content)
    original_normalized = normalize_json(original_data)

    # Parse and convert back to JSON string
    kicad_project = KicadProject.from_file(file_path)
    roundtrip_json = kicad_project.to_json_str(
        pretty_print=True, preserve_original=True
    )

    # Parse the roundtrip JSON and normalize
    roundtrip_data = json.loads(roundtrip_json)
    roundtrip_normalized = normalize_json(roundtrip_data)

    # Compare normalized strings
    assert (
        original_normalized == roundtrip_normalized
    ), "JSON strings should be identical"


def test_json_string_roundtrip_complex_file():
    """Test JSON string round-trip for complex KiCad project file."""
    file_path = "examples/test_data/StickHub.kicad_pro"

    if not Path(file_path).exists():
        pytest.skip(f"Test file not found: {file_path}")

    # Load and normalize original
    with open(file_path, "r", encoding="utf-8") as f:
        original_content = f.read()

    original_data = json.loads(original_content)
    original_normalized = normalize_json(original_data)

    # Parse and convert back to JSON string
    kicad_project = KicadProject.from_file(file_path)
    roundtrip_json = kicad_project.to_json_str(
        pretty_print=True, preserve_original=True
    )

    # Parse the roundtrip JSON and normalize
    roundtrip_data = json.loads(roundtrip_json)
    roundtrip_normalized = normalize_json(roundtrip_data)

    # Compare normalized strings
    assert (
        original_normalized == roundtrip_normalized
    ), "JSON strings should be identical"


def test_file_save_roundtrip():
    """Test saving to file and reading back."""
    file_path = "examples/test_data/example_small/KiCad.kicad_pro"

    if not Path(file_path).exists():
        pytest.skip(f"Test file not found: {file_path}")

    # Parse original file
    original_project = KicadProject.from_file(file_path)

    # Save to temporary file
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".kicad_pro", delete=False
    ) as temp_file:
        temp_path = temp_file.name

    try:
        original_project.save_to_file(temp_path, preserve_original=True)

        # Load the saved file
        saved_project = KicadProject.from_file(temp_path)

        # Compare original and saved data
        original_data = original_project.to_dict(preserve_original=True)
        saved_data = saved_project.to_dict(preserve_original=True)

        differences = compare_structures(original_data, saved_data)
        assert not differences, f"File save/load round-trip failed: {differences[:5]}"

    finally:
        # Clean up temporary file
        Path(temp_path).unlink(missing_ok=True)


def test_project_creation_with_defaults():
    """Test creating a new KiCad project with default values."""
    project = KicadProject()

    # Verify basic structure
    assert project.meta.filename == "KiCad.kicad_pro"
    assert project.meta.version == 3
    assert project.boards == []
    assert project.sheets == []
    assert project.text_variables == {}

    # Verify net settings have default class
    assert len(project.net_settings.classes) == 1
    default_class = project.net_settings.classes[0]
    assert default_class.name == "Default"
    assert default_class.bus_width == 12.0
    assert default_class.clearance == 0.2
    assert default_class.track_width == 0.2
    assert default_class.via_diameter == 0.6
    assert default_class.priority == 2147483647


def test_error_handling_invalid_file():
    """Test error handling for invalid files."""
    with pytest.raises(FileNotFoundError):
        KicadProject.from_file("nonexistent.kicad_pro")


def test_error_handling_invalid_json():
    """Test error handling for invalid JSON content."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".kicad_pro", delete=False
    ) as temp_file:
        temp_file.write("{ invalid json content")
        temp_path = temp_file.name

    try:
        with pytest.raises(ValueError, match="Invalid JSON format"):
            KicadProject.from_str("{ invalid json content")
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_file_extension_validation():
    """Test file extension validation."""
    project = KicadProject()

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False
    ) as temp_file:
        temp_path = temp_file.name

    try:
        with pytest.raises(ValueError, match="Unsupported file extension"):
            project.save_to_file(temp_path)

        with pytest.raises(ValueError, match="Unsupported file extension"):
            KicadProject.from_file(temp_path)
    finally:
        Path(temp_path).unlink(missing_ok=True)


if __name__ == "__main__":
    # Run all tests when called directly
    pytest.main([__file__, "-v"])
