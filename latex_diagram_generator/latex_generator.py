#!/usr/bin/env python3
"""LaTeX code generation for diagrams."""

import re
from typing import Dict, List, Tuple


class LaTeXGenerator:
    """Handles LaTeX/TikZ code generation."""
    
    def __init__(self, template_path: str, within_group_spacing: float = 2.0):
        """
        Initialize the LaTeX generator.
        
        Args:
            template_path: Path to LaTeX template file
            within_group_spacing: Spacing between elements within groups
        """
        self.template_path = template_path
        self.WITHIN_GROUP_SPACING = within_group_spacing
    
    def generate(self, levels, positions, links, group_name_to_group, element_to_group):
        """
        Generate LaTeX code from layout information.
        
        Args:
            levels: Dict mapping group names to y-levels
            positions: Dict mapping group names to (start_x, elements)
            links: Dict of source -> target links
            group_name_to_group: Mapping of group names to group specs
            element_to_group: Mapping of element names to their containing group
            
        Returns:
            LaTeX code as string
        """
        # Calculate maximum width to determine x-spacing
        max_width = 0
        for group_name, (start_x, elements) in positions.items():
            # Calculate actual rightmost position
            if len(elements) > 1:
                rightmost = start_x + (len(elements) - 1) * self.WITHIN_GROUP_SPACING
            else:
                rightmost = start_x
            max_width = max(max_width, rightmost)
        
        # Calculate x-spacing: aim for diagram to fit in reasonable width
        # Target width: ~12cm (fits on A4 with margins), max_width units
        # x_spacing = target_width / max_width
        target_width_cm = 12.0  # cm
        if max_width > 0:
            x_spacing = target_width_cm / max_width
            # Clamp to reasonable range
            x_spacing = max(0.5, min(1.5, x_spacing))
        else:
            x_spacing = 1.0
        
        # Adjust font size based on x-spacing (smaller spacing = smaller font)
        if x_spacing < 0.8:
            font_size = 10
        elif x_spacing < 1.0:
            font_size = 12
        else:
            font_size = 14
        
        # Generate node definitions
        nodes = []
        node_positions = {}  # Map element name to (x, y) for drawing links
        group_center_nodes = {}  # Map group name to center node_id for underlined groups
        
        for group_name in sorted(levels.keys(), key=lambda g: -levels[g]):
            level = levels[group_name]
            start_x, elements = positions[group_name]
            
            for i, elem in enumerate(elements):
                x = start_x + i * self.WITHIN_GROUP_SPACING
                y = level
                # Create unique node ID by appending position index if needed
                base_id = elem.lower().replace('+', 'plus').replace('-', 'minus').replace("'", 'p').replace('.', '_').replace(' ', '_')
                node_id = f"{base_id}_{int(x)}_{int(y)}"
                node_positions[elem] = (node_id, x, y)
                nodes.append(f"\t\t\t\\node ({node_id})   at ({x}, {y}) {{{elem}}};")
            
            # Store center node for underlined groups
            group_obj = group_name_to_group[group_name]
            if group_obj.get('underline', False) and len(elements) > 0:
                center_idx = len(elements) // 2
                center_elem = elements[center_idx]
                center_x = start_x + center_idx * self.WITHIN_GROUP_SPACING
                center_node_id = f"{center_elem.lower().replace('+', 'plus').replace('-', 'minus').replace("'", 'p').replace('.', '_').replace(' ', '_')}_{int(center_x)}_{int(level)}"
                group_center_nodes[group_name] = center_node_id
        
        # Generate links
        links_code = []
        underlines = []
        
        for source, target in links.items():
            # Check if source is a group or element
            source_group = element_to_group.get(source, source)
            group_obj = group_name_to_group[source_group]
            
            # Check if this group has underline
            has_underline = group_obj.get('underline', False)
            
            if has_underline and source == source_group:
                # Draw underline for the group
                start_x, elements = positions[source_group]
                level = levels[source_group]
                if len(elements) > 1:
                    first_elem = elements[0]
                    last_elem = elements[-1]
                    first_x = start_x
                    last_x = start_x + (len(elements) - 1) * self.WITHIN_GROUP_SPACING
                    first_base = first_elem.lower().replace('+', 'plus').replace('-', 'minus').replace("'", 'p').replace('.', '_').replace(' ', '_')
                    last_base = last_elem.lower().replace('+', 'plus').replace('-', 'minus').replace("'", 'p').replace('.', '_').replace(' ', '_')
                    first_id = f"{first_base}_{int(first_x)}_{int(level)}"
                    last_id = f"{last_base}_{int(last_x)}_{int(level)}"
                    underlines.append(f"\t\t\t\\draw[blue] ({first_id}.south west) -- ({last_id}.south east);")
                    
                    # Link from center node
                    source_id = group_center_nodes[source_group]
                else:
                    first_x = start_x
                    elem_base = elements[0].lower().replace('+', 'plus').replace('-', 'minus').replace("'", 'p').replace('.', '_').replace(' ', '_')
                    source_id = f"{elem_base}_{int(first_x)}_{int(level)}"
            else:
                # Regular link from element
                if source in node_positions:
                    source_id, _, _ = node_positions[source]
                else:
                    continue
            
            # Get target node
            if target in node_positions:
                target_id, target_x, target_y = node_positions[target]
                links_code.append(f"\t\t\t\\draw[->, blue] ({source_id}) -- ({target_id});")
        
        # Read template file
        try:
            with open(self.template_path, 'r') as f:
                template = f.read()
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Template file not found: {self.template_path}. "
                f"Please ensure the template file exists or specify a valid path with -t option."
            )
        
        # Format nodes, links, and underlines
        nodes_str = "\n".join(nodes) if nodes else ""
        links_str = "\n".join(links_code) if links_code else ""
        underlines_str = "\n".join(underlines) if underlines else ""
        
        # Replace placeholders using string replacement
        latex_code = template.replace('[[nodes]]', nodes_str)
        latex_code = latex_code.replace('[[links]]', links_str)
        latex_code = latex_code.replace('[[underlines]]', underlines_str)
        
        # Replace x-spacing with calculated value
        # Look for pattern like "x=1.1cm" and replace with dynamic value
        latex_code = re.sub(r'x=[\d.]+cm', f'x={x_spacing:.2f}cm', latex_code)
        
        # Replace font size
        latex_code = re.sub(r'fontsize\{[\d]+\}\{[\d]+\}', f'fontsize{{{font_size}}}{{{font_size}}}', latex_code)
        
        return latex_code
