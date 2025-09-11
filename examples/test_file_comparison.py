#!/usr/bin/env python3
"""
Test script demonstrating how to use the file comparison utility
"""

import os
import sys
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from file_comparison import (
    compare_files_comprehensive,
    compare_files_exact,
    compare_files_structural,
    compare_files_text,
)


def test_programmatic_usage():
    """Demonstrate programmatic usage of the comparison functions"""
    
    # Create test files
    temp_dir = Path(tempfile.mkdtemp())
    
    # Create two files with same content but different formatting
    content1 = """(kicad_sch (version 20230121)
  (lib_symbols)
  (wire (pts (xy 0 0) (xy 10 0)) (stroke (width 0.254)) (uuid wire-1))
  (junction (at 10 0) (diameter 0.508) (uuid junction-1))
)"""

    content2 = """(kicad_sch   (version 20230121)

  (lib_symbols)
  
  (wire   (pts   (xy 0 0) (xy 10 0)) 
          (stroke (width 0.254)) 
          (uuid wire-1))
          
  (junction (at 10 0) (diameter 0.508) (uuid junction-1))
  
)"""
    
    file1 = temp_dir / "test1.kicad_sch"
    file2 = temp_dir / "test2.kicad_sch"
    
    with open(file1, 'w') as f:
        f.write(content1)
    with open(file2, 'w') as f:
        f.write(content2)
    
    print("Testing file comparison functions programmatically:")
    print(f"File 1: {file1}")
    print(f"File 2: {file2}")
    print("=" * 60)
    
    # Test exact comparison
    result = compare_files_exact(str(file1), str(file2))
    print(f"Exact comparison:")
    print(f"  Files equal: {result.are_equal}")
    print(f"  Similarity: {result.similarity_score:.2%}")
    print(f"  Differences: {len(result.differences)}")
    print()
    
    # Test structural comparison
    result = compare_files_structural(str(file1), str(file2))
    print(f"Structural comparison:")
    print(f"  Files equal: {result.are_equal}")
    print(f"  Similarity: {result.similarity_score:.2%}")
    print(f"  Differences: {len(result.differences)}")
    print()
    
    # Test text comparison without whitespace normalization
    result = compare_files_text(str(file1), str(file2), ignore_whitespace=False)
    print(f"Text comparison (with whitespace):")
    print(f"  Files equal: {result.are_equal}")
    print(f"  Similarity: {result.similarity_score:.2%}")
    print(f"  Differences: {len(result.differences)}")
    print()
    
    # Test text comparison with whitespace normalization
    result = compare_files_text(str(file1), str(file2), ignore_whitespace=True)
    print(f"Text comparison (ignoring whitespace):")
    print(f"  Files equal: {result.are_equal}")
    print(f"  Similarity: {result.similarity_score:.2%}")
    print(f"  Differences: {len(result.differences)}")
    print()
    
    # Example of using results for automation
    print("Example automation logic:")
    exact_result = compare_files_exact(str(file1), str(file2))
    text_result = compare_files_text(str(file1), str(file2), ignore_whitespace=True)
    
    if exact_result.are_equal:
        print("OK: Files are identical - no changes needed")
    elif text_result.are_equal:
        print("WARNING: Files have same content but different formatting")
        print("  -> Consider reformatting to match style")
    elif text_result.similarity_score and text_result.similarity_score > 0.8:
        print("WARNING: Files are very similar but have some differences")
        print(f"  -> {len(text_result.differences)} differences found")
    else:
        print("ERROR: Files are significantly different")
        print(f"  -> Only {text_result.similarity_score:.1%} similarity")
    
    print(f"\nTest files created in: {temp_dir}")


if __name__ == "__main__":
    test_programmatic_usage()