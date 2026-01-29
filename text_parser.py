"""
Parser for ultra-compact text format diagram specifications.
"""

import re
from typing import Dict, List, Tuple


class TextFormatParser:
    """Parses ultra-compact text format into diagram specification."""
    
    def __init__(self, text: str):
        """
        Initialize parser with text content.
        
        Args:
            text: Text format diagram specification
        """
        self.text = text
        self.groups = []
        self.links = {}
    
    def parse(self) -> Dict:
        """
        Parse the text format and return a dictionary specification.
        
        Returns:
            Dictionary with 'groups' and 'links' keys
        """
        lines = self.text.strip().split('\n')
        
        # First pass: collect all lines by type
        group_lines = []
        link_lines = []
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Check for section headers
            if line.startswith('#'):
                lower_line = line.lower()
                if 'group' in lower_line:
                    current_section = 'groups'
                elif 'link' in lower_line:
                    current_section = 'links'
                continue
            
            # Classify line
            if '->' in line:
                link_lines.append(line)
                if current_section is None:
                    current_section = 'links'
            else:
                group_lines.append(line)
                if current_section is None:
                    current_section = 'groups'
        
        # Parse groups first
        for i, line in enumerate(group_lines):
            self._parse_group_line(line, i)
        
        # Then parse links
        for line in link_lines:
            self._parse_link_line(line)
        
        return {
            'groups': self.groups,
            'links': self.links
        }
    
    def _parse_group_line(self, line: str, counter: int):
        """
        Parse a group definition line.
        
        Args:
            line: Line containing group definition
            counter: Counter for auto-generated group names
        """
        # Check if it's a multi-element group with brackets
        bracket_match = re.match(r'\[(.*?)\](.*)$', line)
        
        if bracket_match:
            # Multi-element group
            elements_str = bracket_match.group(1)
            modifiers = bracket_match.group(2).strip()
            
            # Split elements by spaces (but not within other brackets if any)
            elements = [elem.strip() for elem in elements_str.split() if elem.strip()]
            
            # Generate a group name
            group_name = f"group_{counter}"
            
            # Check for underline modifier
            has_underline = 'underline' in modifiers.lower()
            
            group = {
                'name': group_name,
                'elements': elements
            }
            
            if has_underline:
                group['underline'] = True
            
            self.groups.append(group)
        else:
            # Single element group
            # Check for underline modifier
            parts = line.split()
            element_name = parts[0]
            has_underline = len(parts) > 1 and 'underline' in parts[1].lower()
            
            group = {
                'name': element_name
            }
            
            if has_underline:
                group['underline'] = True
            
            self.groups.append(group)
    
    def _parse_link_line(self, line: str):
        """
        Parse a link definition line.
        
        Args:
            line: Line containing link definitions (may be chained)
        """
        # Split by '->' to get chain of links
        parts = [part.strip() for part in line.split('->')]
        
        if len(parts) < 2:
            return
        
        # Process each link in the chain
        for i in range(len(parts) - 1):
            source = self._normalize_element(parts[i])
            target = self._normalize_element(parts[i + 1])
            
            # Add link
            self.links[source] = target
    
    def _normalize_element(self, element: str) -> str:
        """
        Normalize element name (handle brackets for multi-element groups).
        
        Args:
            element: Element or group reference
            
        Returns:
            Normalized name
        """
        element = element.strip()
        
        # Check if it's a bracketed group reference
        bracket_match = re.match(r'\[(.*?)\]', element)
        if bracket_match:
            # Find matching group by elements
            elements_str = bracket_match.group(1)
            elements = [elem.strip() for elem in elements_str.split() if elem.strip()]
            
            # Find the group with these elements
            for group in self.groups:
                if 'elements' in group and group['elements'] == elements:
                    return group['name']
            
            # If not found, create a new group on the fly
            # This shouldn't happen if groups are properly defined first
            return element
        
        return element


def parse_text_format(text: str) -> Dict:
    """
    Parse ultra-compact text format into diagram specification.
    
    Args:
        text: Text format diagram specification
        
    Returns:
        Dictionary with 'groups' and 'links' keys
    """
    parser = TextFormatParser(text)
    return parser.parse()
