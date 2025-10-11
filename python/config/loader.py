"""
Configuration loader for K+S model .lsd files.

Parses LSD (Laboratory for Simulation Development) configuration files
to extract model parameters and initial conditions.
"""

from typing import Dict, Any, List, Optional, Tuple
import re
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class LSDParameter:
    """Represents a single parameter from LSD file."""
    name: str
    value: float
    parent_label: Optional[str] = None


@dataclass
class LSDVariable:
    """Represents a variable from LSD file."""
    name: str
    initial_value: Optional[float] = None
    parent_label: Optional[str] = None


@dataclass
class LSDObject:
    """Represents an object/container from LSD file."""
    label: str
    parent: Optional[str] = None
    parameters: Dict[str, float] = field(default_factory=dict)
    variables: Dict[str, Optional[float]] = field(default_factory=dict)
    functions: List[str] = field(default_factory=list)
    children: List['LSDObject'] = field(default_factory=list)


class LSDConfigLoader:
    """
    Loader for LSD configuration files (.lsd extension).
    
    Parses hierarchical LSD file format to extract:
    - Model parameters (Param:)
    - Variables (Var:)
    - Functions (Func:)
    - Object hierarchy (Son:, Label:)
    
    Example LSD file structure:
        Label Root
        {
            Son: Country
            Label Country
            {
                Param: tr
                Var: GDP
                Func: timeStep
            }
        }
    """
    
    def __init__(self, file_path: str):
        """
        Initialize loader with configuration file path.
        
        Args:
            file_path: Path to .lsd configuration file
        """
        self.file_path = Path(file_path)
        self.root: Optional[LSDObject] = None
        self.all_parameters: Dict[str, float] = {}
        self.all_variables: Dict[str, Optional[float]] = {}
        
    def load(self) -> Dict[str, Any]:
        """
        Load and parse the LSD configuration file.
        
        Returns:
            Dictionary containing:
                - 'parameters': All parameters with values
                - 'objects': Hierarchical object structure
                - 'metadata': File metadata
        """
        if not self.file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.file_path}")
        
        with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Parse the hierarchical structure
        self.root = self._parse_object(content)
        
        # Collect all parameters recursively
        self._collect_parameters(self.root)
        
        return {
            'parameters': self.all_parameters,
            'variables': self.all_variables,
            'objects': self.root,
            'metadata': {
                'file_path': str(self.file_path),
                'file_name': self.file_path.name,
            }
        }
    
    def _parse_object(
        self,
        content: str,
        start: int = 0,
        parent_label: Optional[str] = None
    ) -> Optional[LSDObject]:
        """
        Recursively parse LSD object structure.
        
        Args:
            content: File content string
            start: Starting position in content
            parent_label: Label of parent object
            
        Returns:
            Parsed LSDObject or None
        """
        lines = content[start:].split('\n')
        
        obj = None
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Match Label
            if line.startswith('Label '):
                label = line.split('Label ', 1)[1].strip()
                obj = LSDObject(label=label, parent=parent_label)
            
            # Match Parameter
            elif line.startswith('Param: '):
                param_name = line.split('Param: ', 1)[1].strip()
                # Look for value in next lines
                value = self._find_value(lines, i + 1)
                if obj:
                    obj.parameters[param_name] = value
            
            # Match Variable
            elif line.startswith('Var: '):
                var_name = line.split('Var: ', 1)[1].strip()
                # Variables may not have initial values
                if obj:
                    obj.variables[var_name] = None
            
            # Match Function
            elif line.startswith('Func: '):
                func_name = line.split('Func: ', 1)[1].strip()
                if obj:
                    obj.functions.append(func_name)
            
            # Match Son (child object)
            elif line.startswith('Son: '):
                child_label = line.split('Son: ', 1)[1].strip()
                # Child will be parsed when we encounter its Label
            
            # Match opening brace (start of nested object)
            elif line == '{':
                # Find matching closing brace
                brace_content, end_pos = self._extract_braced_content(lines, i)
                if obj:
                    # Parse child object
                    child = self._parse_object('\n'.join(brace_content), 0, obj.label)
                    if child:
                        obj.children.append(child)
                i += end_pos
            
            i += 1
        
        return obj
    
    def _extract_braced_content(self, lines: List[str], start: int) -> Tuple[List[str], int]:
        """
        Extract content between matching braces.
        
        Args:
            lines: List of file lines
            start: Index of opening brace
            
        Returns:
            Tuple of (content lines, number of lines consumed)
        """
        content = []
        depth = 0
        i = start
        
        while i < len(lines):
            line = lines[i].strip()
            
            if line == '{':
                depth += 1
                if depth > 1:
                    content.append(lines[i])
            elif line == '}':
                depth -= 1
                if depth == 0:
                    return content, i - start
                content.append(lines[i])
            else:
                if depth > 0:
                    content.append(lines[i])
            
            i += 1
        
        return content, i - start
    
    def _find_value(self, lines: List[str], start: int) -> float:
        """
        Find numeric value following a parameter declaration.
        
        Args:
            lines: List of file lines
            start: Starting line index
            
        Returns:
            Numeric value or 0.0 if not found
        """
        for i in range(start, min(start + 3, len(lines))):
            line = lines[i].strip()
            # Try to parse as float
            try:
                return float(line)
            except ValueError:
                # Check if line contains a number
                match = re.search(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', line)
                if match:
                    return float(match.group())
        
        return 0.0
    
    def _collect_parameters(self, obj: Optional[LSDObject]) -> None:
        """
        Recursively collect all parameters from object tree.
        
        Args:
            obj: LSD object to collect from
        """
        if obj is None:
            return
        
        # Add this object's parameters
        for param_name, param_value in obj.parameters.items():
            # Use hierarchical name to avoid conflicts
            full_name = f"{obj.label}.{param_name}"
            self.all_parameters[full_name] = param_value
            # Also add short name (may overwrite)
            self.all_parameters[param_name] = param_value
        
        # Add variables
        for var_name, var_value in obj.variables.items():
            full_name = f"{obj.label}.{var_name}"
            self.all_variables[full_name] = var_value
            self.all_variables[var_name] = var_value
        
        # Recursively collect from children
        for child in obj.children:
            self._collect_parameters(child)
    
    def get_parameter(self, name: str, default: Any = None) -> Any:
        """
        Get a parameter value by name.
        
        Args:
            name: Parameter name (can include object prefix)
            default: Default value if parameter not found
            
        Returns:
            Parameter value or default
        """
        return self.all_parameters.get(name, default)
    
    def get_parameters_by_object(self, object_label: str) -> Dict[str, float]:
        """
        Get all parameters for a specific object.
        
        Args:
            object_label: Label of the object
            
        Returns:
            Dictionary of parameters for that object
        """
        prefix = f"{object_label}."
        return {
            k.split('.')[-1]: v
            for k, v in self.all_parameters.items()
            if k.startswith(prefix)
        }
    
    def print_structure(self, obj: Optional[LSDObject] = None, indent: int = 0) -> None:
        """
        Print the hierarchical structure (for debugging).
        
        Args:
            obj: Object to print (None = root)
            indent: Indentation level
        """
        if obj is None:
            obj = self.root
        
        if obj is None:
            return
        
        prefix = "  " * indent
        print(f"{prefix}Object: {obj.label}")
        
        if obj.parameters:
            print(f"{prefix}  Parameters: {list(obj.parameters.keys())}")
        
        if obj.variables:
            print(f"{prefix}  Variables: {list(obj.variables.keys())}")
        
        if obj.functions:
            print(f"{prefix}  Functions: {obj.functions}")
        
        for child in obj.children:
            self.print_structure(child, indent + 1)


def load_configuration(file_path: str) -> Dict[str, Any]:
    """
    Convenience function to load an LSD configuration file.
    
    Args:
        file_path: Path to .lsd file
        
    Returns:
        Configuration dictionary
    """
    loader = LSDConfigLoader(file_path)
    return loader.load()
