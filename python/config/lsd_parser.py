"""
LSD Configuration File Parser
Parses .lsd files and converts them to YAML format
"""

import yaml
import re
from pathlib import Path
from typing import Dict, Any, List, Optional


class LSDParser:
    """Parser for LSD configuration files (.lsd format)"""
    
    def __init__(self, lsd_file: str):
        self.lsd_file = Path(lsd_file)
        self.config = {}
        self.parameters = {}
        
    def parse(self) -> Dict[str, Any]:
        """Parse the LSD file and return a dictionary structure"""
        with open(self.lsd_file, 'r') as f:
            content = f.read()
        
        # Find DATA section which contains actual parameter values
        if 'DATA' in content:
            data_section = content.split('DATA')[1] if len(content.split('DATA')) > 1 else content
            self._parse_data_section(data_section)
        
        return self.parameters
    
    def _parse_data_section(self, data_section: str):
        """Parse the DATA section which contains actual parameter values"""
        lines = data_section.split('\n')
        current_object = "Root"
        object_stack = []
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Object definition
            if line.startswith('Object:'):
                parts = line.split()
                if len(parts) >= 2:
                    obj_name = parts[1]
                    object_stack.append(current_object)
                    current_object = obj_name
                continue
            
            # Parameter with value: "Param: name flags value"
            if line.startswith('Param:'):
                parts = line.split('\t')
                if len(parts) >= 2:
                    param_info = parts[0].split()
                    if len(param_info) >= 2:
                        param_name = param_info[1]
                        # Get the value (last part after tab)
                        value_str = parts[-1].strip()
                        try:
                            # Try to parse as number
                            if '.' in value_str:
                                value = float(value_str)
                            else:
                                value = int(value_str)
                            
                            # Store with object prefix
                            if current_object:
                                full_name = f"{current_object}.{param_name}"
                            else:
                                full_name = param_name
                            self.parameters[full_name] = value
                        except ValueError:
                            # Not a number, skip
                            pass
                continue
        
        return self.parameters
    
    def to_yaml(self, output_file: str):
        """Save the configuration to a YAML file"""
        with open(output_file, 'w') as f:
            yaml.dump(self.parameters, f, default_flow_style=False, sort_keys=True)
        
        print(f"Configuration saved to {output_file}")
        return self.parameters


def main():
    """Parse Cent_wage-Benchmark_v1.lsd and create YAML config"""
    import sys
    
    if len(sys.argv) > 1:
        lsd_file = sys.argv[1]
    else:
        lsd_file = '../../Cent_wage-Benchmark_v1.lsd'
    
    output_file = '../config/model_config.yaml'
    
    parser = LSDParser(lsd_file)
    config = parser.parse()
    params = parser.to_yaml(output_file)
    
    print(f"\nExtracted {len(params)} parameters from {lsd_file}")
    print("\nSample parameters:")
    for i, (key, value) in enumerate(list(sorted(params.items()))[:20]):
        print(f"  {key}: {value}")


if __name__ == '__main__':
    main()
