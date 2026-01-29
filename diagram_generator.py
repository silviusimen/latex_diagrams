#!/usr/bin/env python3
"""
LaTeX/TikZ Diagram Generator from JSON specification.

This script generates LaTeX diagrams with TikZ based on a JSON input specification.
It handles groups of elements, directed links, and special formatting like underlines.
"""

import json
import argparse
import os
from typing import Dict, List, Tuple, Set
from collections import defaultdict
from text_parser import parse_text_format


class DiagramGenerator:
    """Generates LaTeX/TikZ diagrams from JSON specifications."""
    
    def __init__(self, spec: Dict, template_path: str = 'template.tex'):
        """
        Initialize the diagram generator with a specification.
        
        Args:
            spec: Dictionary containing 'groups' and 'links' keys
            template_path: Path to the LaTeX template file
        """
        self.spec = spec
        self.groups = spec.get('groups', [])
        self.links = spec.get('links', {})
        self.template_path = template_path
        
        # Map element names to their group
        self.element_to_group = {}
        self.group_name_to_group = {}
        
        # Build element and group mappings
        for group in self.groups:
            group_name = group['name']
            self.group_name_to_group[group_name] = group
            
            # If group has elements, map each element to this group
            if 'elements' in group:
                for elem in group['elements']:
                    self.element_to_group[elem] = group_name
            else:
                # Group name itself is the element
                self.element_to_group[group_name] = group_name
    
    def _build_dependency_graph(self) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
        """
        Build forward and backward dependency graphs.
        
        Returns:
            Tuple of (outgoing_links, incoming_links) dictionaries
        """
        outgoing = defaultdict(list)
        incoming = defaultdict(list)
        
        for source, target in self.links.items():
            outgoing[source].append(target)
            incoming[target].append(source)
        
        return outgoing, incoming
    
    def _compute_levels(self) -> Dict[str, int]:
        """
        Compute the vertical level for each group (higher level = higher in diagram).
        Uses topological ordering based on links.
        
        Returns:
            Dictionary mapping group names to their vertical levels
        """
        outgoing, incoming = self._build_dependency_graph()
        
        # Find all groups/elements
        all_nodes = set(self.group_name_to_group.keys())
        
        # Compute levels using topological sort approach
        levels = {}
        
        # Start with nodes that have no incoming edges
        no_incoming = []
        for node in all_nodes:
            group = self.group_name_to_group[node]
            # Check if any element in the group has incoming links
            has_incoming = False
            
            if 'elements' in group:
                for elem in group['elements']:
                    if elem in incoming:
                        has_incoming = True
                        break
            else:
                if node in incoming:
                    has_incoming = True
            
            if not has_incoming:
                no_incoming.append(node)
        
        # Assign levels using BFS-like approach (higher number = higher in diagram)
        max_level = len(all_nodes)
        
        for node in no_incoming:
            levels[node] = max_level
        
        # Process remaining nodes
        processed = set(no_incoming)
        changed = True
        
        while changed:
            changed = False
            for node in all_nodes:
                if node in processed:
                    continue
                
                # Find all dependencies for this group
                group = self.group_name_to_group[node]
                max_dep_level = -1
                all_deps_processed = True
                
                if 'elements' in group:
                    for elem in group['elements']:
                        if elem in incoming:
                            for dep in incoming[elem]:
                                dep_group = self.element_to_group.get(dep, dep)
                                if dep_group not in processed:
                                    all_deps_processed = False
                                else:
                                    max_dep_level = max(max_dep_level, levels.get(dep_group, 0))
                else:
                    if node in incoming:
                        for dep in incoming[node]:
                            dep_group = self.element_to_group.get(dep, dep)
                            if dep_group not in processed:
                                all_deps_processed = False
                            else:
                                max_dep_level = max(max_dep_level, levels.get(dep_group, 0))
                
                if all_deps_processed:
                    levels[node] = max_dep_level - 1 if max_dep_level >= 0 else max_level - len(processed)
                    processed.add(node)
                    changed = True
        
        return levels
    
    def _compute_horizontal_positions(self, levels: Dict[str, int]) -> Dict[str, Tuple[float, List[str]]]:
        """
        Compute horizontal positions for elements in each group.
        
        Args:
            levels: Dictionary mapping group names to vertical levels
            
        Returns:
            Dictionary mapping group names to (start_x, element_list) tuples
        """
        # Group by level
        level_groups = defaultdict(list)
        for group_name, level in levels.items():
            level_groups[level].append(group_name)
        
        # Build reverse lookup: which groups link to which elements
        outgoing, incoming = self._build_dependency_graph()
        
        # Calculate center positions for groups with underlines
        group_centers = {}
        
        positions = {}
        current_x = 1.0  # Starting x position
        
        # Process each level from top to bottom
        for level in sorted(level_groups.keys(), reverse=True):
            groups_at_level = level_groups[level]
            level_x = 1.0
            
            for group_name in groups_at_level:
                group = self.group_name_to_group[group_name]
                
                # Check if this group should be centered under a source group
                target_x = None
                if group_name in incoming:
                    for source in incoming[group_name]:
                        source_group = self.element_to_group.get(source, source)
                        # If source is a group (not an element), and it has underline
                        if source == source_group and source in self.group_name_to_group:
                            source_group_obj = self.group_name_to_group[source]
                            if source_group_obj.get('underline', False) and source in group_centers:
                                target_x = group_centers[source]
                                break
                
                if 'elements' in group:
                    elements = group['elements']
                    num_elements = len(elements)
                    
                    # If target_x is set, center this single-element group under it
                    if target_x is not None and num_elements == 1:
                        start_x = target_x
                    else:
                        start_x = level_x
                    
                    positions[group_name] = (start_x, elements)
                    
                    # Calculate center for this group (for underlined groups)
                    center_x = start_x + (num_elements - 1) / 2.0
                    group_centers[group_name] = center_x
                    
                    # Move x for next group (spacing of 1 between elements)
                    if target_x is None:
                        level_x += num_elements
                    else:
                        level_x = max(level_x, start_x + num_elements)
                else:
                    # Single element group
                    if target_x is not None:
                        start_x = target_x
                    else:
                        start_x = level_x
                    
                    positions[group_name] = (start_x, [group_name])
                    group_centers[group_name] = start_x
                    
                    if target_x is None:
                        level_x += 1
                    else:
                        level_x = max(level_x, start_x + 1)
        
        return positions
    
    def generate_latex(self) -> str:
        """
        Generate the complete LaTeX document.
        
        Returns:
            String containing the LaTeX code
        """
        levels = self._compute_levels()
        positions = self._compute_horizontal_positions(levels)
        
        # Generate node definitions
        nodes = []
        node_positions = {}  # Map element name to (x, y) for drawing links
        
        for group_name in sorted(levels.keys(), key=lambda g: -levels[g]):
            level = levels[group_name]
            start_x, elements = positions[group_name]
            
            for i, elem in enumerate(elements):
                x = start_x + i
                y = level
                node_id = elem.lower().replace('+', 'plus').replace('-', 'minus')
                node_positions[elem] = (node_id, x, y)
                nodes.append(f"\t\t\t\\node ({node_id})   at ({x}, {y}) {{{elem}}};")
        
        # Generate links
        links_code = []
        underlines = []
        
        for source, target in self.links.items():
            # Check if source is a group or element
            source_group = self.element_to_group.get(source, source)
            group_obj = self.group_name_to_group[source_group]
            
            # Check if this group has underline
            has_underline = group_obj.get('underline', False)
            
            if has_underline and source == source_group:
                # Draw underline for the group
                _, elements = positions[source_group]
                if len(elements) > 1:
                    first_elem = elements[0]
                    last_elem = elements[-1]
                    first_id = first_elem.lower().replace('+', 'plus').replace('-', 'minus')
                    last_id = last_elem.lower().replace('+', 'plus').replace('-', 'minus')
                    underlines.append(f"\t\t\t\\draw[blue] ({first_id}.south west) -- ({last_id}.south east);")
                    
                    # Link from middle element or use calculated middle point
                    middle_idx = len(elements) // 2
                    middle_elem = elements[middle_idx]
                    source_id = middle_elem.lower().replace('+', 'plus').replace('-', 'minus')
                else:
                    source_id = elements[0].lower().replace('+', 'plus').replace('-', 'minus')
            else:
                # Regular link from element
                if source in node_positions:
                    source_id, _, _ = node_positions[source]
                else:
                    continue
            
            # Get target node
            if target in node_positions:
                target_id, _, _ = node_positions[target]
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
        
        return latex_code


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Generate LaTeX/TikZ diagrams from JSON specifications'
    )
    parser.add_argument(
        'input_file',
        help='Path to input JSON file'
    )
    parser.add_argument(
        '-o', '--output',
        help='Path to output LaTeX file (default: stdout)',
        default=None
    )
    parser.add_argument(
        '-t', '--template',
        help='Path to LaTeX template file (default: template.tex)',
        default='template.tex'
    )
    
    args = parser.parse_args()
    
    # Load specification from input file
    # Detect format based on file extension or content
    input_path = args.input_file
    
    if input_path.endswith('.json'):
        # JSON format
        with open(input_path, 'r') as f:
            spec = json.load(f)
    elif input_path.endswith('.txt'):
        # Text format
        with open(input_path, 'r') as f:
            text = f.read()
        spec = parse_text_format(text)
    else:
        # Try to auto-detect by reading first character
        with open(input_path, 'r') as f:
            content = f.read()
        
        # Check if it starts with JSON markers
        stripped = content.strip()
        if stripped.startswith('{') or stripped.startswith('['):
            spec = json.loads(content)
        else:
            # Assume text format
            spec = parse_text_format(content)
    
    # Generate LaTeX
    generator = DiagramGenerator(spec, template_path=args.template)
    latex_code = generator.generate_latex()
    
    # Output
    if args.output:
        with open(args.output, 'w') as f:
            f.write(latex_code)
        print(f"LaTeX diagram written to {args.output}")
    else:
        print(latex_code)


if __name__ == '__main__':
    main()
