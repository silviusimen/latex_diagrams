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
    
    def _is_section_header(self, line: str) -> str:
        """
        Check if line is a section header or comment.
        
        Args:
            line: Line to check
            
        Returns:
            'groups', 'links', 'comment', or None
        """
        if line.startswith('#'):
            lower_line = line.lower()
            if 'group' in lower_line:
                return 'groups'
            elif 'link' in lower_line:
                return 'links'
            else:
                return 'comment'  # Any other # line is a comment
        return None
    
    def _classify_single_line(self, line: str, current_section: str) -> Tuple[str, str]:
        """
        Classify a single line as group or link.
        
        Args:
            line: Line to classify
            current_section: Current section context
            
        Returns:
            Tuple of (line_type, updated_section) where line_type is 'group' or 'link'
        """
        if '->' in line:
            return 'link', 'links' if current_section is None else current_section
        else:
            return 'group', 'groups' if current_section is None else current_section
    
    def _classify_lines(self, lines: List[str]) -> Tuple[List[str], List[str]]:
        """
        Classify lines into groups and links.
        
        Args:
            lines: List of input lines
            
        Returns:
            Tuple of (group_lines, link_lines)
        """
        group_lines = []
        link_lines = []
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Check for section headers and comments
            section_type = self._is_section_header(line)
            if section_type:
                if section_type in ('groups', 'links'):
                    current_section = section_type
                # Skip all lines starting with # (headers and comments)
                continue
            
            # Classify line
            line_type, current_section = self._classify_single_line(line, current_section)
            if line_type == 'link':
                link_lines.append(line)
            else:
                group_lines.append(line)
        
        return group_lines, link_lines
    
    def _parse_multi_element_group(self, elements_str: str, modifiers: str, counter: int) -> Dict:
        """
        Parse a multi-element group with brackets.
        
        Args:
            elements_str: String inside brackets
            modifiers: Modifiers after brackets
            counter: Counter for group naming
            
        Returns:
            Group dictionary
        """
        elements = [elem.strip() for elem in elements_str.split() if elem.strip()]
        group_name = f"group_{counter}"
        has_underline = 'underline' in modifiers.lower()
        # Parse optional at (x, y)
        pos_match = re.search(r'at\s*\(([^,]+),\s*([^)]+)\)', modifiers)
        group_position = None
        if pos_match:
            try:
                pos_x = float(pos_match.group(1))
                pos_y = float(pos_match.group(2))
                group_position = (pos_x, pos_y)
            except Exception:
                group_position = None
        
        group = {
            'name': group_name,
            'elements': elements
        }
        
        if has_underline:
            group['underline'] = True
        if group_position is not None:
            group['override_position'] = group_position
        
        return group
    
    def _parse_single_element_group(self, line: str) -> Dict:
        """
        Parse a single element group.
        
        Args:
            line: Line containing single element
            
        Returns:
            Group dictionary
        """
        parts = line.split()
        element_name = parts[0]
        has_underline = len(parts) > 1 and 'underline' in parts[1].lower()
        # Parse optional at (x, y)
        group_position = None
        if len(parts) > 1:
            pos_match = re.search(r'at\s*\(([^,]+),\s*([^)]+)\)', ' '.join(parts[1:]))
            if pos_match:
                try:
                    pos_x = float(pos_match.group(1))
                    pos_y = float(pos_match.group(2))
                    group_position = (pos_x, pos_y)
                except Exception:
                    group_position = None
        group = {'name': element_name}
        if has_underline:
            group['underline'] = True
        if group_position is not None:
            group['override_position'] = group_position
        return group
    
    def parse(self) -> Dict:
        """
        Parse the text format and return a dictionary specification.
        
        Returns:
            Dictionary with 'groups' and 'links' keys
            
        Raises:
            ValueError: If an element appears in multiple groups
        """
        lines = self.text.strip().split('\n')
        
        # Classify lines into groups and links
        group_lines, link_lines = self._classify_lines(lines)
        
        # Parse groups first
        for i, line in enumerate(group_lines):
            self._parse_group_line(line, i)
        
        # Validate that elements are unique across groups
        self._validate_unique_elements()
        
        # Validate plus element positioning
        self._validate_plus_elements()
        
        # Then parse links
        for line in link_lines:
            self._parse_link_line(line)
        
        return {
            'groups': self.groups,
            'links': self.links
        }
    
    def _validate_unique_elements(self):
        """
        Validate that each element appears in only one group.
        
        Raises:
            ValueError: If an element appears in multiple groups
        """
        element_to_groups = {}  # Map element name to list of groups it appears in
        
        for group in self.groups:
            # Get elements from the group
            if 'elements' in group:
                elements = group['elements']
            else:
                # Single element group
                elements = [group['name']]
            
            # Check each element
            for elem in elements:
                # Skip special symbols - they're separators, not actual elements
                if elem in ['+', '-', '|']:
                    continue
                
                if elem not in element_to_groups:
                    element_to_groups[elem] = []
                element_to_groups[elem].append(group.get('name', group.get('elements', ['?'])[0]))
        
        # Find duplicates
        duplicates = {elem: groups for elem, groups in element_to_groups.items() if len(groups) > 1}
        
        if duplicates:
            error_msg = "ERROR: The following elements appear in multiple groups:\n"
            for elem, groups in duplicates.items():
                error_msg += f"  - '{elem}' appears in groups: {', '.join(groups)}\n"
            error_msg += "\nEach element must appear in only one group."
            raise ValueError(error_msg)
    
    def _validate_plus_elements(self):
        """
        Validate that if a group contains plus (+) elements, they appear between all other elements.
        
        For example:
        - Valid: [P1 + P2 + P3] (plus between all elements)
        - Invalid: [P1 + P2 P3] (missing plus between P2 and P3)
        - Valid: [P1 P2 P3] (no plus at all is fine)
        
        Raises:
            ValueError: If a group has inconsistent plus element placement
        """
        errors = []
        
        for group in self.groups:
            # Get elements from the group
            if 'elements' in group:
                elements = group['elements']
            else:
                # Single element groups are always valid
                continue
            
            # Check if group has any plus elements
            has_plus = '+' in elements
            
            if not has_plus:
                # No plus elements, validation passes
                continue
            
            # If group has plus, verify plus appears between all non-plus elements
            non_plus_elements = [elem for elem in elements if elem != '+']
            
            if len(non_plus_elements) < 2:
                # Need at least 2 non-plus elements for this validation to make sense
                continue
            
            # Count plus elements - should be len(non_plus_elements) - 1
            plus_count = elements.count('+')
            expected_plus_count = len(non_plus_elements) - 1
            
            if plus_count != expected_plus_count:
                group_name = group.get('name', f"[{' '.join(elements)}]")
                errors.append(
                    f"  - Group {group_name} has {len(non_plus_elements)} elements but {plus_count} plus symbols "
                    f"(expected {expected_plus_count})"
                )
                continue
            
            # Verify plus elements are in the correct positions (between elements, not at start/end)
            # Expected pattern: elem + elem + elem (alternating)
            for i, elem in enumerate(elements):
                if i % 2 == 0:
                    # Even positions should be non-plus elements
                    if elem == '+':
                        group_name = group.get('name', f"[{' '.join(elements)}]")
                        errors.append(
                            f"  - Group {group_name} has plus (+) in wrong position (should alternate: elem + elem + elem)"
                        )
                        break
                else:
                    # Odd positions should be plus elements
                    if elem != '+':
                        group_name = group.get('name', f"[{' '.join(elements)}]")
                        errors.append(
                            f"  - Group {group_name} is missing plus (+) between elements (should alternate: elem + elem + elem)"
                        )
                        break
        
        if errors:
            error_msg = "ERROR: Groups with plus (+) elements must have plus between ALL elements:\n"
            error_msg += '\n'.join(errors)
            error_msg += "\n\nValid: [P1 + P2 + P3]  Invalid: [P1 + P2 P3]"
            raise ValueError(error_msg)
    
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
            elements_str = bracket_match.group(1)
            modifiers = bracket_match.group(2).strip()
            group = self._parse_multi_element_group(elements_str, modifiers, counter)
        else:
            group = self._parse_single_element_group(line)
        
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
    
    def _parse_bracketed_group_reference(self, bracket_match) -> str:
        """
        Parse a bracketed group reference and find matching group.
        
        Args:
            bracket_match: Regex match object for bracketed group
            
        Returns:
            Group name if found, else original bracketed string
        """
        elements_str = bracket_match.group(1)
        elements = [elem.strip() for elem in elements_str.split() if elem.strip()]
        
        # Find the group with these elements
        for group in self.groups:
            if 'elements' in group and group['elements'] == elements:
                return group['name']
        
        # If not found, return original (shouldn't happen if groups properly defined)
        return f"[{elements_str}]"
    
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
            return self._parse_bracketed_group_reference(bracket_match)
        
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
