#!/usr/bin/env python3
"""
Detailed completeness check for K+S Model Python implementation
This script performs a comprehensive equation-by-equation comparison
"""

import sys
import re
from pathlib import Path
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Get paths to source files
ROOT_DIR = Path(__file__).parent.parent.parent
PYTHON_DIR = Path(__file__).parent.parent

def extract_cpp_equations():
    """Extract all EQUATION declarations from C++ files"""
    equations_by_file = defaultdict(list)
    
    cpp_files = [
        'fun_KS_bank.h',
        'fun_KS_capital.h',
        'fun_KS_consumption.h',
        'fun_KS_country.h',
        'fun_KS_financial.h',
        'fun_KS_firm1.h',
        'fun_KS_firm2.h',
        'fun_KS_labor.h',
        'fun_KS_vintage.h',
        'fun_KS_worker.h',
        'fun_KS_stats.h',
        'fun_KS_support.h',
        'fun_KS_test.h',
        'fun_KS.cpp',
    ]
    
    for cpp_file in cpp_files:
        file_path = ROOT_DIR / cpp_file
        if not file_path.exists():
            continue
            
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        # Find all EQUATION declarations
        pattern = r'EQUATION\(\s*"([^"]+)"\s*\)'
        matches = re.findall(pattern, content)
        equations_by_file[cpp_file] = sorted(set(matches))
    
    return equations_by_file

def extract_python_implementations():
    """Extract implemented features from Python files"""
    implementations = {
        'properties': set(),
        'methods': set(),
        'compute_methods': set(),
    }
    
    python_files = list((PYTHON_DIR / 'model').glob('*.py'))
    
    for py_file in python_files:
        with open(py_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract property definitions (self._name = ...)
        prop_pattern = r'self\.(_[A-Za-z0-9_]+)\s*='
        props = re.findall(prop_pattern, content)
        implementations['properties'].update(props)
        
        # Extract method definitions
        method_pattern = r'def\s+([a-z_][a-z0-9_]*)\s*\('
        methods = re.findall(method_pattern, content)
        implementations['methods'].update(methods)
        
        # Extract compute_ methods specifically
        compute_pattern = r'def\s+(compute_[a-z0-9_]+)\s*\('
        compute_methods = re.findall(compute_pattern, content)
        implementations['compute_methods'].update(compute_methods)
    
    return implementations

def check_equation_implementation(equation_name, implementations):
    """Check if an equation is implemented in various ways"""
    checks = {
        'property': False,
        'compute_method': False,
        'method': False,
        'likely_implemented': False,
    }
    
    # Check for exact property match
    if f'_{equation_name}' in implementations['properties']:
        checks['property'] = True
        checks['likely_implemented'] = True
    
    # Check for compute method
    compute_name = f'compute_{equation_name.lower()}'
    if compute_name in implementations['compute_methods']:
        checks['compute_method'] = True
        checks['likely_implemented'] = True
    
    # Check for method with similar name
    eq_lower = equation_name.lower()
    for method in implementations['methods']:
        if eq_lower in method or method in eq_lower:
            checks['method'] = True
            checks['likely_implemented'] = True
            break
    
    return checks

def analyze_completeness():
    """Perform detailed completeness analysis"""
    print("=" * 80)
    print("DETAILED K+S MODEL COMPLETENESS ANALYSIS")
    print("=" * 80)
    print()
    
    # Extract data
    cpp_equations = extract_cpp_equations()
    python_impl = extract_python_implementations()
    
    # Statistics
    total_equations = 0
    implemented = 0
    possibly_implemented = 0
    missing = 0
    
    results = {}
    
    # Analyze each file
    for cpp_file, equations in sorted(cpp_equations.items()):
        if not equations:
            continue
            
        print(f"\n{'=' * 80}")
        print(f"{cpp_file}")
        print(f"{'=' * 80}")
        
        file_results = {
            'total': len(equations),
            'implemented': 0,
            'possibly_implemented': 0,
            'missing': [],
        }
        
        for eq in equations:
            total_equations += 1
            check = check_equation_implementation(eq, python_impl)
            
            status = "❌"
            if check['likely_implemented']:
                if check['property']:
                    status = "✅"
                    file_results['implemented'] += 1
                    implemented += 1
                else:
                    status = "⚠️ "
                    file_results['possibly_implemented'] += 1
                    possibly_implemented += 1
            else:
                file_results['missing'].append(eq)
                missing += 1
            
            # Print equation status
            impl_details = []
            if check['property']:
                impl_details.append("property")
            if check['compute_method']:
                impl_details.append("compute")
            if check['method']:
                impl_details.append("method")
            
            details = f"({', '.join(impl_details)})" if impl_details else ""
            print(f"  {status} {eq:30s} {details}")
        
        results[cpp_file] = file_results
        
        # Summary for this file
        pct = (file_results['implemented'] / file_results['total'] * 100) if file_results['total'] > 0 else 0
        print(f"\n  Summary: {file_results['implemented']}/{file_results['total']} implemented ({pct:.1f}%)")
        if file_results['possibly_implemented'] > 0:
            print(f"           {file_results['possibly_implemented']} possibly implemented")
        if file_results['missing']:
            print(f"  Missing: {', '.join(file_results['missing'][:10])}")
            if len(file_results['missing']) > 10:
                print(f"           ... and {len(file_results['missing']) - 10} more")
    
    # Overall summary
    print("\n" + "=" * 80)
    print("OVERALL SUMMARY")
    print("=" * 80)
    print(f"Total equations in C++ code: {total_equations}")
    print(f"Clearly implemented (✅): {implemented} ({implemented/total_equations*100:.1f}%)")
    print(f"Possibly implemented (⚠️): {possibly_implemented} ({possibly_implemented/total_equations*100:.1f}%)")
    print(f"Missing (❌): {missing} ({missing/total_equations*100:.1f}%)")
    print()
    
    effective_completion = (implemented + possibly_implemented) / total_equations * 100
    print(f"Effective completion: {effective_completion:.1f}%")
    print()
    
    # Python implementation stats
    print("Python implementation statistics:")
    print(f"  Properties defined: {len(python_impl['properties'])}")
    print(f"  Methods defined: {len(python_impl['methods'])}")
    print(f"  Compute methods: {len(python_impl['compute_methods'])}")
    print()
    
    # Assessment
    if effective_completion >= 90:
        print("✅ EXCELLENT: Model is essentially complete")
    elif effective_completion >= 80:
        print("✅ GOOD: Model is largely complete, minor gaps remain")
    elif effective_completion >= 70:
        print("⚠️  FAIR: Model has good coverage but significant work remains")
    else:
        print("❌ INCOMPLETE: Substantial implementation work required")
    
    return results

if __name__ == "__main__":
    analyze_completeness()
