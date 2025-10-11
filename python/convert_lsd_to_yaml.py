#!/usr/bin/env python3
"""
Convert LSD configuration files to YAML format
This script parses all .lsd files and converts them to clean YAML configurations
"""

import sys
import yaml
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from model.config_parser import LSDConfigParser


def convert_lsd_to_yaml(lsd_file: Path, output_dir: Path):
    """
    Convert a single LSD file to YAML format
    
    Args:
        lsd_file: Path to .lsd file
        output_dir: Directory for output YAML file
    """
    print(f"Converting {lsd_file.name}...")
    
    try:
        # Parse LSD file
        parser = LSDConfigParser(str(lsd_file))
        config = parser.parse()
        
        # Generate output filename
        yaml_name = lsd_file.stem.lower().replace('-', '_') + '.yaml'
        output_path = output_dir / yaml_name
        
        # Write YAML file with nice formatting
        with open(output_path, 'w') as f:
            f.write(f"# K+S Model Configuration\n")
            f.write(f"# Converted from: {lsd_file.name}\n")
            f.write(f"# Original LSD configuration file\n\n")
            
            yaml.dump(config, f, 
                     default_flow_style=False,
                     sort_keys=False,
                     indent=2,
                     allow_unicode=True)
        
        print(f"  → Created {yaml_name}")
        return True
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def main():
    """Main conversion function"""
    # Paths
    repo_root = Path(__file__).parent.parent
    lsd_dir = repo_root
    yaml_dir = Path(__file__).parent / 'configs'
    
    # Create output directory if it doesn't exist
    yaml_dir.mkdir(exist_ok=True)
    
    # Find all LSD files
    lsd_files = list(lsd_dir.glob('*.lsd'))
    
    if not lsd_files:
        print("No .lsd files found in repository root")
        return 1
    
    print(f"Found {len(lsd_files)} LSD configuration files\n")
    
    # Convert each file
    success_count = 0
    for lsd_file in sorted(lsd_files):
        if convert_lsd_to_yaml(lsd_file, yaml_dir):
            success_count += 1
    
    print(f"\nConversion complete: {success_count}/{len(lsd_files)} files converted successfully")
    
    # Generate comparison document
    print("\nGenerating configuration comparison document...")
    generate_comparison_doc(lsd_files, yaml_dir)
    
    return 0 if success_count == len(lsd_files) else 1


def generate_comparison_doc(lsd_files, yaml_dir):
    """Generate a document comparing all configurations"""
    output_path = yaml_dir.parent / 'CONFIG_COMPARISON.md'
    
    with open(output_path, 'w') as f:
        f.write("# K+S Model Configuration Comparison\n\n")
        f.write("## LSD to YAML Conversion Summary\n\n")
        f.write(f"This document describes the {len(lsd_files)} configuration files ")
        f.write("converted from LSD format to YAML format.\n\n")
        
        f.write("## Converted Files\n\n")
        f.write("| LSD File | YAML File | Purpose |\n")
        f.write("|----------|-----------|----------|\n")
        
        config_descriptions = {
            'Cent_wage-Baseline_v2.lsd': 'Centralized wage, baseline configuration (v2)',
            'Cent_wage-Benchmark_v1.lsd': 'Centralized wage, benchmark configuration (v1)',
            'No_skills-Fix_entry-No_fin.lsd': 'No skills, fixed entry, minimal finance',
            'Ten_skills-Free_entry-Bas_fin.lsd': 'Ten skills, free entry, basic finance',
            'Ten_skills-Free_entry-Full_fin.lsd': 'Ten skills, free entry, full finance',
            'Ten_skills-Free_entry-No_fin.lsd': 'Ten skills, free entry, no finance',
            'Sim1.lsd': 'Simulation scenario 1',
            'Sim2.lsd': 'Simulation scenario 2',
            'sa-ee.lsd': 'Sensitivity analysis - Elementary Effects',
            'sa-sobol.lsd': 'Sensitivity analysis - Sobol indices',
        }
        
        for lsd_file in sorted(lsd_files):
            yaml_name = lsd_file.stem.lower().replace('-', '_') + '.yaml'
            desc = config_descriptions.get(lsd_file.name, 'Configuration file')
            f.write(f"| {lsd_file.name} | {yaml_name} | {desc} |\n")
        
        f.write("\n## Key Differences Between Configurations\n\n")
        f.write("### 1. Wage Mechanism\n")
        f.write("- **Centralized**: All firms offer same wage based on economy-wide conditions\n")
        f.write("- **Decentralized**: Firms set individual wages based on local conditions\n\n")
        
        f.write("### 2. Skills System\n")
        f.write("- **No skills**: All workers have identical productivity\n")
        f.write("- **Ten skills**: Workers differentiated by skill levels (10 categories)\n\n")
        
        f.write("### 3. Entry/Exit Dynamics\n")
        f.write("- **Fixed entry**: Number of firms remains constant\n")
        f.write("- **Free entry**: Firms can enter/exit based on profitability\n\n")
        
        f.write("### 4. Financial System\n")
        f.write("- **No finance**: Minimal banking (1 bank, fixed rates)\n")
        f.write("- **Basic finance**: Multiple banks with credit constraints\n")
        f.write("- **Full finance**: Complete banking system with Basel rules\n\n")
        
        f.write("## YAML Format Benefits\n\n")
        f.write("1. **Human-readable**: Easy to understand and edit\n")
        f.write("2. **Version control friendly**: Clean diffs in git\n")
        f.write("3. **Standard format**: Works with many tools and languages\n")
        f.write("4. **Type-safe**: Clear data types (numbers, strings, lists)\n")
        f.write("5. **Hierarchical**: Natural representation of model structure\n")
        f.write("6. **Comments**: Full support for documentation inline\n\n")
        
        f.write("## Usage\n\n")
        f.write("```python\n")
        f.write("import yaml\n")
        f.write("from pathlib import Path\n\n")
        f.write("# Load a configuration\n")
        f.write("with open('configs/baseline.yaml') as f:\n")
        f.write("    config = yaml.safe_load(f)\n\n")
        f.write("# Access parameters\n")
        f.write("periods = config['simulation']['periods']\n")
        f.write("tax_rate = config['country']['tr']\n")
        f.write("```\n")
    
    print(f"  → Created CONFIG_COMPARISON.md")


if __name__ == '__main__':
    sys.exit(main())
