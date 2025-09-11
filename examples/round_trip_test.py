#!/usr/bin/env python3
"""
KiCad Round-Trip Test

This example demonstrates the accuracy of the KiCad parser by performing round-trip tests:
1. Load KiCad files from test_data directory
2. Parse them into Python objects
3. Save them back to files
4. Compare original vs converted files using all comparison methods
5. Generate a comprehensive accuracy report

This validates that the parser can read and write KiCad files with high fidelity.
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from kicad_parser import load_kicad_file, save_kicad_file
from kicad_parser.file_comparison_utils import (
    KiCadFileType, 
    detect_kicad_file_type,
    ComparisonResult
)
from examples.file_comparison import compare_files_comprehensive


def find_test_files() -> List[Tuple[str, KiCadFileType]]:
    """Find all KiCad test files and determine their types"""
    test_data_dir = Path(__file__).parent / "test_data"
    
    if not test_data_dir.exists():
        print(f"Warning: Test data directory not found at {test_data_dir}")
        return []
    
    test_files = []
    
    # Find all KiCad files recursively
    for file_path in test_data_dir.rglob("*.kicad_*"):
        if file_path.is_file():
            file_type = detect_kicad_file_type(str(file_path))
            if file_type != KiCadFileType.UNKNOWN:
                test_files.append((str(file_path), file_type))
    
    return sorted(test_files)


def perform_round_trip_test(original_file: str, file_type: KiCadFileType) -> Dict[str, ComparisonResult]:
    """
    Perform round-trip test on a single file
    
    Args:
        original_file: Path to original KiCad file
        file_type: Detected file type
        
    Returns:
        Dictionary of comparison results
    """
    try:
        # Load the original file
        kicad_obj = load_kicad_file(original_file)
        
        # Create temporary file for converted version
        with tempfile.NamedTemporaryFile(
            mode='w', 
            suffix=Path(original_file).suffix, 
            delete=False,
            encoding='utf-8'
        ) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Save the loaded object back to file
            save_kicad_file(kicad_obj, temp_path)
            
            # Compare original vs converted
            comparison_results = compare_files_comprehensive(original_file, temp_path)
            
            return comparison_results
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                
    except Exception as e:
        # Return error results
        error_msg = f"Error during round-trip: {e}"
        return {
            'exact': ComparisonResult(False, [error_msg]),
            'structural': ComparisonResult(False, [error_msg]),
            'text_with_ws': ComparisonResult(False, [error_msg]),
            'text_no_ws': ComparisonResult(False, [error_msg])
        }


def print_file_results(file_path: str, file_type: KiCadFileType, results: Dict[str, ComparisonResult]) -> None:
    """Print results for a single file"""
    rel_path = os.path.relpath(file_path, Path(__file__).parent)
    
    print(f"\n[FILE] {rel_path}")
    print(f"       Type: {file_type.value}")
    print(f"       Size: {os.path.getsize(file_path)} bytes")
    
    # Print comparison results
    method_names = {
        'exact': 'Exact Match',
        'structural': 'Structural',
        'text_with_ws': 'Text (w/ WS)',
        'text_no_ws': 'Text (no WS)'
    }
    
    for method, result in results.items():
        method_name = method_names.get(method, method)
        if result.are_equal:
            print(f"       [PASS] {method_name}: PERFECT MATCH (100.00%)")
        elif result.similarity_score is not None:
            print(f"       [WARN] {method_name}: {result.similarity_score:.2%} similarity")
        else:
            print(f"       [FAIL] {method_name}: FAILED")
            if result.differences:
                print(f"              First error: {result.differences[0]}")


def generate_summary_report(all_results: List[Tuple[str, KiCadFileType, Dict[str, ComparisonResult]]]) -> None:
    """Generate summary statistics"""
    if not all_results:
        print("\n[SUMMARY] No files tested!")
        return
        
    print(f"\n" + "="*70)
    print(f"ROUND-TRIP TEST SUMMARY")
    print(f"="*70)
    
    total_files = len(all_results)
    method_stats = {
        'exact': {'perfect': 0, 'total_similarity': 0.0},
        'structural': {'perfect': 0, 'total_similarity': 0.0},
        'text_with_ws': {'perfect': 0, 'total_similarity': 0.0},
        'text_no_ws': {'perfect': 0, 'total_similarity': 0.0}
    }
    
    file_type_counts = {}
    
    # Collect statistics
    for file_path, file_type, results in all_results:
        # Count file types
        file_type_counts[file_type.value] = file_type_counts.get(file_type.value, 0) + 1
        
        # Count perfect matches and accumulate similarity scores
        for method, result in results.items():
            if method in method_stats:
                if result.are_equal:
                    method_stats[method]['perfect'] += 1
                    method_stats[method]['total_similarity'] += 1.0
                elif result.similarity_score is not None:
                    method_stats[method]['total_similarity'] += result.similarity_score
    
    # Print file type breakdown
    print(f"\nFile Types Tested:")
    for file_type, count in sorted(file_type_counts.items()):
        print(f"   {file_type}: {count} files")
    
    # Print method statistics
    print(f"\nAccuracy Results:")
    method_names = {
        'exact': 'Exact Match',
        'structural': 'Structural',
        'text_with_ws': 'Text (with whitespace)',
        'text_no_ws': 'Text (normalized whitespace)'
    }
    
    for method, stats in method_stats.items():
        method_name = method_names.get(method, method)
        perfect_count = stats['perfect']
        avg_similarity = stats['total_similarity'] / total_files if total_files > 0 else 0
        
        print(f"   {method_name:25}: {perfect_count:2d}/{total_files} perfect ({perfect_count/total_files:.1%}), "
              f"avg similarity: {avg_similarity:.1%}")
    
    # Find best and worst performers
    print(f"\nBest Performers:")
    perfect_structural = []
    for file_path, file_type, results in all_results:
        if results['structural'].are_equal:
            rel_path = os.path.relpath(file_path, Path(__file__).parent)
            perfect_structural.append(f"   [PERFECT] {rel_path}")
    
    if perfect_structural:
        for line in perfect_structural:
            print(line)
    else:
        print("   No files with perfect structural matches")
    
    print(f"\nFiles Needing Attention:")
    issues_found = []
    for file_path, file_type, results in all_results:
        if not results['structural'].are_equal:
            rel_path = os.path.relpath(file_path, Path(__file__).parent)
            similarity = results['structural'].similarity_score or 0.0
            issues_found.append(f"   [ISSUE] {rel_path} ({similarity:.1%} structural similarity)")
    
    if issues_found:
        for line in issues_found:
            print(line)
    else:
        print("   All files have perfect structural matches!")


def main():
    """Main function"""
    print("KiCad Parser Round-Trip Test")
    print("="*50)
    print("Testing parser accuracy by loading and saving KiCad files...")
    
    # Find all test files
    test_files = find_test_files()
    
    if not test_files:
        print("[ERROR] No test files found!")
        print("\nMake sure you have KiCad files in the examples/test_data directory.")
        return
    
    print(f"Found {len(test_files)} test files")
    
    all_results = []
    
    # Process each file
    for i, (file_path, file_type) in enumerate(test_files, 1):
        print(f"\n[{i}/{len(test_files)}] Testing file...")
        
        # Perform round-trip test
        results = perform_round_trip_test(file_path, file_type)
        all_results.append((file_path, file_type, results))
        
        # Print results for this file
        print_file_results(file_path, file_type, results)
    
    # Generate summary report
    generate_summary_report(all_results)
    
    print(f"\n[COMPLETE] Round-trip testing completed!")
    print(f"[STATS] Tested {len(test_files)} files across {len(set(ft.value for _, ft in test_files))} different file types.")


if __name__ == "__main__":
    main()