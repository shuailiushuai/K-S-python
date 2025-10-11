#!/usr/bin/env python3
"""
Fix imports for files in subdirectories
Adds proper path setup to allow importing from parent directory
"""

import os
import re
from pathlib import Path

def fix_imports_in_file(filepath):
    """Add sys.path setup to a Python file if needed"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Check if it already has proper sys.path setup
    if 'sys.path.insert(0, str(Path(__file__).parent.parent))' in content:
        print(f"  - Already has proper path setup")
        return False
    
    lines = content.split('\n')
    
    # Find module comment/docstring end and first real import
    in_docstring = False
    docstring_char = None
    comment_end_idx = 0
    first_import_idx = None
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Track docstrings
        if stripped.startswith('"""') or stripped.startswith("'''"):
            if not in_docstring:
                in_docstring = True
                docstring_char = stripped[:3]
                if stripped.count(docstring_char) == 2:  # Single line docstring
                    in_docstring = False
                    comment_end_idx = i + 1
            elif stripped.endswith(docstring_char):
                in_docstring = False
                comment_end_idx = i + 1
        elif not in_docstring:
            if stripped.startswith('#') or not stripped:
                comment_end_idx = i + 1
            elif stripped.startswith(('import ', 'from ')):
                if first_import_idx is None:
                    first_import_idx = i
                    break
    
    if first_import_idx is None:
        print(f"  - No imports found")
        return False
    
    # Build path setup code
    path_setup = [
        "import sys",
        "from pathlib import Path",
        "",
        "# Add parent directory to path for imports",
        "sys.path.insert(0, str(Path(__file__).parent.parent))",
        ""
    ]
    
    # Check if sys and Path are already imported in the imports block
    has_sys = False
    has_pathlib = False
    for i in range(first_import_idx, min(first_import_idx + 10, len(lines))):
        if 'import sys' in lines[i]:
            has_sys = True
        if 'from pathlib import Path' in lines[i] or 'import pathlib' in lines[i]:
            has_pathlib = True
    
    # Adjust path_setup based on existing imports
    if has_sys and has_pathlib:
        path_setup = ["", "# Add parent directory to path for imports",
                     "sys.path.insert(0, str(Path(__file__).parent.parent))", ""]
        # Insert before first import
        insert_idx = first_import_idx
    elif has_sys:
        path_setup = ["from pathlib import Path",
                     "", "# Add parent directory to path for imports",
                     "sys.path.insert(0, str(Path(__file__).parent.parent))", ""]
        insert_idx = first_import_idx
    elif has_pathlib:
        path_setup = ["import sys",
                     "", "# Add parent directory to path for imports",
                     "sys.path.insert(0, str(Path(__file__).parent.parent))", ""]
        insert_idx = first_import_idx
    else:
        # Insert after docstring/comments
        insert_idx = comment_end_idx
    
    # Insert path setup
    lines = lines[:insert_idx] + path_setup + lines[insert_idx:]
    
    # Write back
    with open(filepath, 'w') as f:
        f.write('\n'.join(lines))
    
    return True

def main():
    """Fix imports in all subdirectory files"""
    base_dir = Path(__file__).parent
    
    # Directories to process
    subdirs = ['examples', 'tests', 'tools']
    
    fixed_count = 0
    for subdir in subdirs:
        subdir_path = base_dir / subdir
        if not subdir_path.exists():
            continue
        
        print(f"\nProcessing {subdir}/:")
        for py_file in sorted(subdir_path.glob('*.py')):
            if py_file.name == '__init__.py':
                continue
            
            print(f"  {py_file.name}")
            if fix_imports_in_file(py_file):
                print(f"    ✓ Fixed")
                fixed_count += 1
    
    print(f"\nTotal fixed: {fixed_count} files")

if __name__ == '__main__':
    main()
