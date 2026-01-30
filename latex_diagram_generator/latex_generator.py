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
    
    def _calculate_spacing_and_font(self, positions: Dict) -> Tuple[float, int]:
        """
        Calculate x-spacing and font size based on diagram width.
        
        Args:
            positions: Dict mapping group names to (start_x, elements)
            
        Returns:
            Tuple of (x_spacing, font_size)
        """
        # Calculate maximum width
        max_width = 0
        for group_name, (start_x, elements) in positions.items():
            if len(elements) > 1:
                rightmost = start_x + (len(elements) - 1) * self.WITHIN_GROUP_SPACING
            else:
                rightmost = start_x
            max_width = max(max_width, rightmost)
        
        # Calculate x-spacing: aim for diagram to fit in reasonable width
        target_width_cm = 12.0  # cm (fits on A4 with margins)
        if max_width > 0:
            x_spacing = target_width_cm / max_width
            x_spacing = max(0.5, min(1.5, x_spacing))  # Clamp to reasonable range
        else:
            x_spacing = 1.0
        
        # Adjust font size based on x-spacing
        if x_spacing < 0.8:
            font_size = 10
        elif x_spacing < 1.0:
            font_size = 12
        else:
            font_size = 14
        
        return x_spacing, font_size
    
    def _sanitize_node_id(self, text: str) -> str:
        """
        Convert text to a valid LaTeX node ID.
        
        Args:
            text: Element name
            
        Returns:
            Sanitized node ID
        """
        return text.lower().replace('+', 'plus').replace('-', 'minus').replace("'", 'p').replace('.', '_').replace(' ', '_')
    
    def _create_node_for_element(self, elem: str, x: float, y: int) -> Tuple[str, str, str]:
        """
        Create a single node definition for an element.
        
        Args:
            elem: Element name
            x: X-coordinate
            y: Y-coordinate
            
        Returns:
            Tuple of (node_line, node_id, elem)
        """
        base_id = self._sanitize_node_id(elem)
        node_id = f"{base_id}_{int(x)}_{int(y)}"
        node_line = f"\t\t\t\\node ({node_id})   at ({x}, {y}) {{{elem}}};"
        return node_line, node_id, elem
    
    def _get_center_node_for_underlined_group(self, group_name: str, group_obj: Dict,
                                              elements: List[str], start_x: float,
                                              level: int) -> str:
        """
        Get center node ID for an underlined group.
        
        Args:
            group_name: Name of the group
            group_obj: Group specification dict
            elements: List of elements in group
            start_x: Starting x-coordinate
            level: Y-level
            
        Returns:
            Center node ID if group is underlined, else None
        """
        if group_obj.get('underline', False) and len(elements) > 0:
            center_idx = len(elements) // 2
            center_elem = elements[center_idx]
            center_x = start_x + center_idx * self.WITHIN_GROUP_SPACING
            center_node_id = f"{self._sanitize_node_id(center_elem)}_{int(center_x)}_{int(level)}"
            return center_node_id
        return None
    
    def _generate_node_definitions(self, levels: Dict, positions: Dict, 
                                   group_name_to_group: Dict) -> Tuple[List[str], Dict, Dict]:
        """
        Generate TikZ node definitions.
        
        Args:
            levels: Dict mapping group names to y-levels
            positions: Dict mapping group names to (start_x, elements)
            group_name_to_group: Mapping of group names to group specs
            
        Returns:
            Tuple of (node_lines, node_positions, group_center_nodes)
        """
        nodes = []
        node_positions = {}  # Map element name to (node_id, x, y)
        group_center_nodes = {}  # Map group name to center node_id for underlined groups
        
        for group_name in sorted(levels.keys(), key=lambda g: -levels[g]):
            level = levels[group_name]
            start_x, elements = positions[group_name]
            
            # Create nodes for each element
            for i, elem in enumerate(elements):
                x = start_x + i * self.WITHIN_GROUP_SPACING
                node_line, node_id, _ = self._create_node_for_element(elem, x, level)
                node_positions[elem] = (node_id, x, level)
                nodes.append(node_line)
            
            # Track center node for underlined groups
            group_obj = group_name_to_group[group_name]
            center_node_id = self._get_center_node_for_underlined_group(
                group_name, group_obj, elements, start_x, level
            )
            if center_node_id:
                group_center_nodes[group_name] = center_node_id
        
        return nodes, node_positions, group_center_nodes
    
    def _create_underline_for_group(self, source_group: str, positions: Dict, levels: Dict) -> str:
        """
        Create underline LaTeX code for a group with multiple elements.
        
        Args:
            source_group: Name of the source group
            positions: Dict mapping group names to (start_x, elements)
            levels: Dict mapping group names to y-levels
            
        Returns:
            LaTeX underline command or None if not applicable
        """
        start_x, elements = positions[source_group]
        level = levels[source_group]
        
        if len(elements) > 1:
            first_elem = elements[0]
            last_elem = elements[-1]
            first_x = start_x
            last_x = start_x + (len(elements) - 1) * self.WITHIN_GROUP_SPACING
            first_id = f"{self._sanitize_node_id(first_elem)}_{int(first_x)}_{int(level)}"
            last_id = f"{self._sanitize_node_id(last_elem)}_{int(last_x)}_{int(level)}"
            return f"\t\t\t\\draw[blue] ({first_id}.south west) -- ({last_id}.south east);"
        return None
    
    def _generate_underlines(self, links: Dict, positions: Dict, levels: Dict,
                            group_name_to_group: Dict, element_to_group: Dict) -> List[str]:
        """
        Generate underline code for groups with underline flag.
        
        Args:
            links: Dict of source -> target links
            positions: Dict mapping group names to (start_x, elements)
            levels: Dict mapping group names to y-levels
            group_name_to_group: Mapping of group names to group specs
            element_to_group: Mapping of element names to their containing group
            
        Returns:
            List of LaTeX underline commands
        """
        underlines = []
        
        for source, target in links.items():
            source_group = element_to_group.get(source, source)
            group_obj = group_name_to_group[source_group]
            has_underline = group_obj.get('underline', False)
            
            if has_underline and source == source_group:
                underline = self._create_underline_for_group(source_group, positions, levels)
                if underline:
                    underlines.append(underline)
        
        return underlines
    
    def _get_source_node_id(self, source: str, element_to_group: Dict, group_name_to_group: Dict,
                           group_center_nodes: Dict, positions: Dict, levels: Dict,
                           node_positions: Dict) -> str:
        """
        Get the node ID for a link source (handles underlined groups).
        
        Args:
            source: Source element or group name
            element_to_group: Mapping of element names to groups
            group_name_to_group: Mapping of group names to specs
            group_center_nodes: Dict of center node IDs for underlined groups
            positions: Dict of group positions
            levels: Dict of group levels
            node_positions: Dict of node positions
            
        Returns:
            Node ID string, or None if not found
        """
        source_group = element_to_group.get(source, source)
        group_obj = group_name_to_group[source_group]
        has_underline = group_obj.get('underline', False)
        
        if has_underline and source == source_group:
            # Link from center node of underlined group
            if source_group in group_center_nodes:
                return group_center_nodes[source_group]
            else:
                # Fallback for single-element underlined group
                start_x, elements = positions[source_group]
                level = levels[source_group]
                elem_base = self._sanitize_node_id(elements[0])
                return f"{elem_base}_{int(start_x)}_{int(level)}"
        else:
            # Regular link from element
            if source in node_positions:
                source_id, _, _ = node_positions[source]
                return source_id
        
        return None
    
    def _generate_link_arrows(self, links: Dict, node_positions: Dict, element_to_group: Dict,
                             group_name_to_group: Dict, group_center_nodes: Dict,
                             positions: Dict, levels: Dict) -> List[str]:
        """
        Generate arrow code for links between elements.
        
        Args:
            links: Dict of source -> target links
            node_positions: Dict mapping element names to (node_id, x, y)
            element_to_group: Mapping of element names to their containing group
            group_name_to_group: Mapping of group names to group specs
            group_center_nodes: Dict mapping group names to center node IDs
            positions: Dict mapping group names to (start_x, elements)
            levels: Dict mapping group names to y-levels
            
        Returns:
            List of LaTeX arrow commands
        """
        links_code = []
        
        for source, target in links.items():
            # Get source node ID
            source_id = self._get_source_node_id(
                source, element_to_group, group_name_to_group,
                group_center_nodes, positions, levels, node_positions
            )
            
            if source_id is None:
                continue
            
            # Get target node ID
            if target in node_positions:
                target_id, _, _ = node_positions[target]
                links_code.append(f"\t\t\t\\draw[->, blue] ({source_id}) -- ({target_id});")
        
        return links_code
    
    def _apply_template(self, template_content: str, nodes: List[str], links: List[str],
                       underlines: List[str], x_spacing: float, font_size: int) -> str:
        """
        Apply template substitutions.
        
        Args:
            template_content: Template file content
            nodes: List of node definition lines
            links: List of link arrow lines
            underlines: List of underline lines
            x_spacing: Calculated x-spacing value
            font_size: Calculated font size
            
        Returns:
            Complete LaTeX code
        """
        nodes_str = "\n".join(nodes) if nodes else ""
        links_str = "\n".join(links) if links else ""
        underlines_str = "\n".join(underlines) if underlines else ""
        
        latex_code = template_content.replace('[[nodes]]', nodes_str)
        latex_code = latex_code.replace('[[links]]', links_str)
        latex_code = latex_code.replace('[[underlines]]', underlines_str)
        
        # Replace x-spacing and font size with calculated values
        latex_code = re.sub(r'x=[\d.]+cm', f'x={x_spacing:.2f}cm', latex_code)
        latex_code = re.sub(r'fontsize\{[\d]+\}\{[\d]+\}', f'fontsize{{{font_size}}}{{{font_size}}}', latex_code)
        
        return latex_code
    
    def _load_template(self) -> str:
        """
        Load LaTeX template from file.
        
        Returns:
            Template content as string
            
        Raises:
            FileNotFoundError: If template file doesn't exist
        """
        try:
            with open(self.template_path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Template file not found: {self.template_path}. "
                f"Please ensure the template file exists or specify a valid path with -t option."
            )
    
    def _generate_all_components(self, levels: Dict, positions: Dict, links: Dict,
                                 group_name_to_group: Dict, element_to_group: Dict):
        """
        Generate all LaTeX components (nodes, underlines, arrows).
        
        Args:
            levels: Dict mapping group names to y-levels
            positions: Dict mapping group names to (start_x, elements)
            links: Dict of source -> target links
            group_name_to_group: Mapping of group names to group specs
            element_to_group: Mapping of element names to their containing group
            
        Returns:
            Tuple of (nodes, underlines, links_code)
        """
        # Generate node definitions
        nodes, node_positions, group_center_nodes = self._generate_node_definitions(
            levels, positions, group_name_to_group
        )
        
        # Generate underlines and link arrows
        underlines = self._generate_underlines(
            links, positions, levels, group_name_to_group, element_to_group
        )
        links_code = self._generate_link_arrows(
            links, node_positions, element_to_group, group_name_to_group,
            group_center_nodes, positions, levels
        )
        
        return nodes, underlines, links_code
    
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
        # Calculate spacing and font size
        x_spacing, font_size = self._calculate_spacing_and_font(positions)
        
        # Generate all components
        nodes, underlines, links_code = self._generate_all_components(
            levels, positions, links, group_name_to_group, element_to_group
        )
        
        # Load template and apply substitutions
        template = self._load_template()
        return self._apply_template(template, nodes, links_code, underlines, x_spacing, font_size)
