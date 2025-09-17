#!/usr/bin/env python3
"""
Simple script to build the documentation using Sphinx.

This script provides a platform-independent way to build the documentation
without needing make or make.bat.

Usage:
    python build-docs.py [format]

Where format can be:
    html (default) - Build HTML documentation
    pdf           - Build PDF documentation
    epub          - Build EPUB documentation
    clean         - Clean build directory
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def run_sphinx_build(format_type="html", clean=False):
    """Run sphinx-build with the specified format."""
    docs_dir = Path(__file__).parent
    source_dir = docs_dir
    build_dir = docs_dir / "_build"

    if clean:
        if build_dir.exists():
            print(f"Cleaning build directory: {build_dir}")
            shutil.rmtree(build_dir)
            return True

    # Ensure we're in the docs directory
    os.chdir(docs_dir)

    # Build the documentation
    cmd = [
        "sphinx-build",
        "-b",
        format_type,
        str(source_dir),
        str(build_dir / format_type),
        "-v",  # Verbose output
        "--keep-going",  # Continue on errors
    ]

    print(f"Building {format_type.upper()} documentation...")
    print(f"Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"[SUCCESS] Documentation built successfully!")
            output_dir = build_dir / format_type
            if format_type == "html":
                index_file = output_dir / "index.html"
                print(f"[HTML] Open: {index_file}")
            elif format_type == "pdf":
                # For LaTeX/PDF builds, the output might be in a different location
                pdf_files = list(output_dir.glob("*.pdf"))
                if pdf_files:
                    print(f"[PDF] File: {pdf_files[0]}")
            print(f"[OUTPUT] Directory: {output_dir}")
        else:
            print(f"[ERROR] Build failed with return code {result.returncode}")
            print(f"STDOUT:\n{result.stdout}")
            print(f"STDERR:\n{result.stderr}")
            return False

    except FileNotFoundError:
        print("[ERROR] sphinx-build not found!")
        print("Install Sphinx: pip install -e .[docs]")
        return False
    except Exception as e:
        print(f"[ERROR] Error running sphinx-build: {e}")
        return False

    return True


def main():
    """Main function."""
    format_type = "html"

    if len(sys.argv) > 1:
        format_type = sys.argv[1].lower()

    if format_type == "clean":
        return run_sphinx_build(clean=True)

    # Validate format type
    valid_formats = ["html", "pdf", "latexpdf", "epub", "man"]
    if format_type not in valid_formats:
        print(f"[ERROR] Unknown format: {format_type}")
        print(f"Valid formats: {', '.join(valid_formats)}")
        return False

    return run_sphinx_build(format_type)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
