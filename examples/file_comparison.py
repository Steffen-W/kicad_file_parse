#!/usr/bin/env python3
"""
KiCad File Comparison Utility

This utility provides various methods to compare S-expression files with different levels of strictness:

1. **Exact Comparison** (`compare_files_exact`):
   - Files must be completely identical (same content, same order, same formatting)
   - Perfect for detecting any changes whatsoever
   
2. **Structural Comparison** (`compare_files_structural`):
   - Same content but order doesn't matter
   - Uses KiCad parser to compare parsed objects
   - Perfect for detecting if files have the same electrical/logical content
   
3. **Text Comparison** (`compare_files_text`):
   - Compares files as plain text
   - Option to ignore whitespace and empty lines
   - Perfect for detecting formatting differences

4. **Comprehensive Comparison** (`compare_files_comprehensive`):
   - Runs all comparison methods and shows results
   - Provides similarity scores for each method

Available Functions:
- `compare_files_exact(file1, file2)` -> ComparisonResult
- `compare_files_structural(file1, file2)` -> ComparisonResult  
- `compare_files_text(file1, file2, ignore_whitespace=False)` -> ComparisonResult
- `compare_files_comprehensive(file1, file2)` -> Dict[str, ComparisonResult]

Usage:
    # Command line - compare two files
    python file_comparison.py file1.kicad_sch file2.kicad_sch
    
    # Command line - run demo with test files
    python file_comparison.py
    
    # As module
    from examples.file_comparison import compare_files_exact, compare_files_structural
    from kicad_parser.file_comparison_utils import ComparisonResult
    
    result = compare_files_exact("file1.kicad_sch", "file2.kicad_sch")
    print(f"Files equal: {result.are_equal}")
    print(f"Similarity: {result.similarity_score:.2%}")
    
    # Comprehensive comparison
    results = compare_files_comprehensive("original.kicad_sch", "modified.kicad_sch")
    
Features:
- Automatic KiCad file type detection
- Built-in demo mode with test files
- Detailed similarity scoring and difference reporting
- Support for all KiCad file formats (schematics, PCBs, footprints, symbols)
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import Dict

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from kicad_parser import load_kicad_file
from kicad_parser.file_comparison_utils import (
    ComparisonResult,
    calculate_structural_similarity,
    calculate_text_similarity,
    find_structural_differences,
    load_file_as_sexpr,
    normalize_sexpr_for_comparison,
    normalize_whitespace,
)


def compare_files_exact(file1_path: str, file2_path: str) -> ComparisonResult:
    """
    Compare two files exactly (including order and formatting).
    Files must be identical in every way.
    """
    try:
        with open(file1_path, 'r', encoding='utf-8') as f1:
            content1 = f1.read()
        with open(file2_path, 'r', encoding='utf-8') as f2:
            content2 = f2.read()
        
        if content1 == content2:
            return ComparisonResult(True, similarity_score=1.0)
        else:
            # Find differences
            lines1 = content1.splitlines()
            lines2 = content2.splitlines()
            
            differences = []
            max_lines = max(len(lines1), len(lines2))
            
            for i in range(max_lines):
                line1 = lines1[i] if i < len(lines1) else "<EOF>"
                line2 = lines2[i] if i < len(lines2) else "<EOF>"
                
                if line1 != line2:
                    differences.append(f"Line {i+1}: '{line1}' vs '{line2}'")
            
            # Calculate similarity based on common lines
            common_lines = sum(1 for i in range(min(len(lines1), len(lines2))) 
                             if lines1[i] == lines2[i])
            similarity = common_lines / max_lines if max_lines > 0 else 0.0
            
            return ComparisonResult(False, differences, similarity)
            
    except Exception as e:
        return ComparisonResult(False, [f"Error reading files: {e}"])


def compare_files_structural(file1_path: str, file2_path: str) -> ComparisonResult:
    """
    Compare two files structurally (same content, order doesn't matter).
    Uses the KiCad parser to compare parsed objects.
    """
    try:
        # Try to parse as KiCad objects first
        try:
            obj1 = load_kicad_file(file1_path)
            obj2 = load_kicad_file(file2_path)
            
            # Convert to S-expressions for comparison
            sexpr1 = obj1.to_sexpr() if hasattr(obj1, 'to_sexpr') else obj1
            sexpr2 = obj2.to_sexpr() if hasattr(obj2, 'to_sexpr') else obj2
            
        except Exception:
            # Fall back to direct S-expression parsing
            sexpr1 = load_file_as_sexpr(file1_path)
            sexpr2 = load_file_as_sexpr(file2_path)
        
        # Normalize both S-expressions for comparison
        normalized1 = normalize_sexpr_for_comparison(sexpr1)
        normalized2 = normalize_sexpr_for_comparison(sexpr2)
        
        if normalized1 == normalized2:
            return ComparisonResult(True, similarity_score=1.0)
        else:
            # Find structural differences
            differences = find_structural_differences(normalized1, normalized2)
            
            # Calculate structural similarity
            similarity = calculate_structural_similarity(normalized1, normalized2)
            
            return ComparisonResult(False, differences, similarity)
            
    except Exception as e:
        return ComparisonResult(False, [f"Error parsing files: {e}"])


def compare_files_text(file1_path: str, file2_path: str, ignore_whitespace: bool = False) -> ComparisonResult:
    """
    Compare two files as text, optionally ignoring whitespace and empty lines.
    
    Args:
        file1_path: Path to first file
        file2_path: Path to second file  
        ignore_whitespace: If True, normalize all whitespace and remove empty lines
    """
    try:
        with open(file1_path, 'r', encoding='utf-8') as f1:
            content1 = f1.read()
        with open(file2_path, 'r', encoding='utf-8') as f2:
            content2 = f2.read()
        
        if ignore_whitespace:
            # Normalize whitespace: remove empty lines, normalize spaces/tabs
            content1 = normalize_whitespace(content1)
            content2 = normalize_whitespace(content2)
        
        if content1 == content2:
            return ComparisonResult(True, similarity_score=1.0)
        else:
            # Find text differences
            lines1 = content1.splitlines()
            lines2 = content2.splitlines()
            
            differences = []
            max_lines = max(len(lines1), len(lines2))
            
            # Show up to 10 different lines
            diff_count = 0
            for i in range(max_lines):
                if diff_count >= 10:
                    break
                    
                line1 = lines1[i] if i < len(lines1) else "<EOF>"
                line2 = lines2[i] if i < len(lines2) else "<EOF>"
                
                if line1 != line2:
                    differences.append(f"Line {i+1}: '{line1[:50]}...' vs '{line2[:50]}...'")
                    diff_count += 1
            
            # Calculate text similarity using longest common subsequence
            similarity = calculate_text_similarity(content1, content2)
            
            return ComparisonResult(False, differences, similarity)
            
    except Exception as e:
        return ComparisonResult(False, [f"Error reading files: {e}"])


def compare_files_comprehensive(file1_path: str, file2_path: str) -> Dict[str, ComparisonResult]:
    """
    Run all comparison methods on two files and return comprehensive results.
    """
    print(f"Comparing files:")
    print(f"  File 1: {file1_path}")
    print(f"  File 2: {file2_path}")
    print("=" * 70)
    
    results = {}
    
    # Exact comparison
    print("1. Exact Comparison (including order and formatting):")
    results['exact'] = compare_files_exact(file1_path, file2_path)
    print(f"   {results['exact']}")
    print()
    
    # Structural comparison
    print("2. Structural Comparison (content matters, order doesn't):")
    results['structural'] = compare_files_structural(file1_path, file2_path)
    print(f"   {results['structural']}")
    print()
    
    # Text comparison without whitespace normalization
    print("3. Text Comparison (with whitespace):")
    results['text_with_ws'] = compare_files_text(file1_path, file2_path, ignore_whitespace=False)
    print(f"   {results['text_with_ws']}")
    print()
    
    # Text comparison with whitespace normalization
    print("4. Text Comparison (ignoring whitespace):")
    results['text_no_ws'] = compare_files_text(file1_path, file2_path, ignore_whitespace=True)
    print(f"   {results['text_no_ws']}")
    print()
    
    return results


def create_test_files_demo():
    """Create some demo files for testing the comparison functions"""

    # Create temporary directory
    temp_dir = Path(tempfile.mkdtemp())
    print(f"Creating demo files in: {temp_dir}")
    
    # Original file
    original_content = '''(kicad_sch
    (version 20230121)
    (generator "test")
    
    (lib_symbols)
    
    (wire
        (pts (xy 0.0 0.0) (xy 10.0 0.0))
        (stroke (width 0.254))
        (uuid "wire-1")
    )
    
    (junction
        (at 10.0 0.0)
        (diameter 0.508)
        (uuid "junction-1")
    )
)'''
    
    # Same content, different order
    reordered_content = '''(kicad_sch
    (version 20230121)
    (generator "test")
    
    (junction
        (at 10.0 0.0)
        (diameter 0.508)
        (uuid "junction-1")
    )
    
    (lib_symbols)
    
    (wire
        (pts (xy 0.0 0.0) (xy 10.0 0.0))
        (stroke (width 0.254))
        (uuid "wire-1")
    )
)'''
    
    # Same content, different whitespace
    whitespace_content = '''(kicad_sch
      (version 20230121)
      (generator "test")


      (lib_symbols)

      (wire
          (pts (xy 0.0 0.0) (xy 10.0 0.0))
          (stroke (width 0.254))
          (uuid "wire-1")
      )

      (junction
          (at 10.0 0.0)
          (diameter 0.508)
          (uuid "junction-1")
      )


)'''
    
    # Different content
    different_content = '''(kicad_sch
    (version 20230121)
    (generator "test")
    
    (lib_symbols)
    
    (wire
        (pts (xy 0.0 0.0) (xy 20.0 0.0))
        (stroke (width 0.254))
        (uuid "wire-2")
    )
)'''
    
    # Write files
    files = {
        'original.kicad_sch': original_content,
        'reordered.kicad_sch': reordered_content,  
        'whitespace.kicad_sch': whitespace_content,
        'different.kicad_sch': different_content
    }
    
    file_paths = {}
    for filename, content in files.items():
        file_path = temp_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        file_paths[filename] = str(file_path)
    
    return file_paths


def main():
    """Main function for command line usage"""
    if len(sys.argv) != 3:
        print("Usage: python file_comparison.py <file1> <file2>")
        print("\nAlternatively, run without arguments to see a demo with test files.")
        
        # Run demo automatically if no files provided
        print("\nRunning demo with test files...")
        if True:  # Auto-run demo
            print("\n" + "="*70)
            print("DEMO: Creating test files and comparing them")
            print("="*70)
            
            # Create demo files
            file_paths = create_test_files_demo()
            
            print("\n" + "="*70)
            print("Demo 1: Original vs Reordered (same content, different order)")
            print("="*70)
            compare_files_comprehensive(file_paths['original.kicad_sch'], 
                                      file_paths['reordered.kicad_sch'])
            
            print("\n" + "="*70)
            print("Demo 2: Original vs Whitespace (same content, different formatting)")
            print("="*70)
            compare_files_comprehensive(file_paths['original.kicad_sch'],
                                      file_paths['whitespace.kicad_sch'])
            
            print("\n" + "="*70)
            print("Demo 3: Original vs Different (different content)")
            print("="*70)
            compare_files_comprehensive(file_paths['original.kicad_sch'],
                                      file_paths['different.kicad_sch'])
            
            print(f"\nDemo files created in: {Path(file_paths['original.kicad_sch']).parent}")
            
        return
    
    file1, file2 = sys.argv[1], sys.argv[2]
    
    if not os.path.exists(file1):
        print(f"Error: File '{file1}' not found")
        return
    
    if not os.path.exists(file2):
        print(f"Error: File '{file2}' not found")
        return
    
    compare_files_comprehensive(file1, file2)


if __name__ == "__main__":
    main()