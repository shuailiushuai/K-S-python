"""
K+S Model Configuration Parser
Parses LSD configuration files and converts them to YAML format
"""

import re
import yaml
from typing import Dict, List, Any, Optional
from collections import defaultdict


class LSDConfigParser:
    """Parser for LSD configuration files"""
    
    def __init__(self, lsd_file: str):
        self.lsd_file = lsd_file
        self.config = {}
        self.hierarchy = []
        
    def parse(self) -> Dict[str, Any]:
        """Parse LSD file and extract configuration"""
        with open(self.lsd_file, 'r', encoding='latin-1') as f:
            content = f.read()
        
        # Split into structure and data sections
        if '\nDATA\n' in content:
            structure_part, data_part = content.split('\nDATA\n', 1)
            lines = structure_part.split('\n')
            data_lines = data_part.split('\n')
        else:
            lines = content.split('\n')
            data_lines = []
        
        self.config = {
            'simulation': {},
            'objects': {}
        }
        
        # First pass: parse structure
        current_object = None
        current_section = None
        indent_level = 0
        object_stack = []
        
        i = 0
        while i < len(lines):
            line = lines[i].rstrip()
            
            # Detect simulation parameters
            if 'MAX_STEP' in line:
                i = self._extract_sim_param(lines, i, 'max_step')
            elif 'EQUATION' in line:
                i = self._extract_sim_param(lines, i, 'equation')
            elif 'MODELREPORT' in line:
                i = self._extract_sim_param(lines, i, 'model_report')
                
            # Detect object hierarchy
            elif line.strip().startswith('Label '):
                object_name = line.strip().split('Label ')[1]
                object_stack.append(object_name)
                if object_name not in self.config['objects']:
                    self.config['objects'][object_name] = {
                        'parameters': {},
                        'variables': {},
                        'functions': {},
                        'children': []
                    }
                current_object = object_name
                
            elif line.strip() == '}' and object_stack:
                object_stack.pop()
                current_object = object_stack[-1] if object_stack else None
                
            elif line.strip().startswith('Son: '):
                if current_object:
                    child_name = line.strip().split('Son: ')[1]
                    if child_name not in self.config['objects'][current_object]['children']:
                        self.config['objects'][current_object]['children'].append(child_name)
                        
            # Extract parameters
            elif line.strip().startswith('Param: ') and current_object:
                param_name = line.strip().split('Param: ')[1]
                # Try to get value from next lines (skip empty lines)
                j = i + 1
                value = None
                while j < len(lines):
                    next_line = lines[j].strip()
                    if not next_line:
                        j += 1
                        continue
                    if next_line.startswith(('Param:', 'Var:', 'Func:', 'Son:', 'Label', '}')):
                        break
                    try:
                        value = float(next_line)
                        i = j  # Skip to this line
                        break
                    except ValueError:
                        break
                    j += 1
                self.config['objects'][current_object]['parameters'][param_name] = value
                            
            # Extract variables (initialized)
            elif line.strip().startswith('Var: ') and current_object:
                var_name = line.strip().split('Var: ')[1]
                self.config['objects'][current_object]['variables'][var_name] = None
                
            # Extract functions
            elif line.strip().startswith('Func: ') and current_object:
                func_name = line.strip().split('Func: ')[1]
                self.config['objects'][current_object]['functions'][func_name] = None
                
            i += 1
        
        # Second pass: parse DATA section for parameter values
        if data_lines:
            self._parse_data_section(data_lines)
            
        return self.config
    
    def _extract_sim_param(self, lines: List[str], start_idx: int, param_name: str) -> int:
        """Extract simulation parameter value"""
        i = start_idx + 1
        while i < len(lines) and lines[i].strip():
            line = lines[i].strip()
            if line and not line.startswith(('MAX_STEP', 'EQUATION', 'MODELREPORT')):
                try:
                    self.config['simulation'][param_name] = int(line) if param_name == 'max_step' else line
                except ValueError:
                    self.config['simulation'][param_name] = line
                break
            i += 1
        return i
    
    def _parse_data_section(self, data_lines: List[str]):
        """Parse DATA section to extract parameter values"""
        current_object = None
        i = 0
        
        while i < len(data_lines):
            line = data_lines[i].rstrip()
            
            # Detect object declaration
            if line.startswith('Object:'):
                parts = line.split()
                if len(parts) >= 2:
                    current_object = parts[1]
                    
            # Extract parameter/variable values
            elif line.startswith(('Param:', 'Var:')) and current_object:
                # Split by tabs and spaces
                parts = re.split(r'[\t\s]+', line)
                if len(parts) >= 2:
                    var_type = parts[0].rstrip(':')  # 'Param' or 'Var'
                    var_name = parts[1]
                    
                    # Value is typically the last element
                    value = None
                    if len(parts) > 2:
                        try:
                            value = float(parts[-1])
                        except ValueError:
                            pass
                    
                    if current_object in self.config['objects']:
                        if var_type == 'Param' and value is not None:
                            self.config['objects'][current_object]['parameters'][var_name] = value
                        
            i += 1
    
    def to_yaml(self, output_file: str):
        """Save configuration as YAML"""
        with open(output_file, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)
    
    def extract_flat_parameters(self) -> Dict[str, float]:
        """Extract all parameters as a flat dictionary"""
        params = {}
        for obj_name, obj_data in self.config['objects'].items():
            for param_name, param_value in obj_data['parameters'].items():
                if param_value is not None:
                    key = f"{obj_name}.{param_name}"
                    params[key] = param_value
        return params


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python config_parser.py <lsd_file> [output_yaml]")
        sys.exit(1)
    
    lsd_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'config.yaml'
    
    parser = LSDConfigParser(lsd_file)
    config = parser.parse()
    parser.to_yaml(output_file)
    
    print(f"Configuration parsed and saved to {output_file}")
    print(f"Total objects: {len(config['objects'])}")
    
    total_params = sum(len(obj['parameters']) for obj in config['objects'].values())
    print(f"Total parameters: {total_params}")
