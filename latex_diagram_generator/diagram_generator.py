#!/usr/bin/env python3
"""
LaTeX/TikZ Diagram Generator from JSON specification.

This script generates LaTeX diagrams with TikZ based on a JSON input specification.
It handles groups of elements, directed links, and special formatting like underlines.
"""

from typing import Dict, List, Tuple
from collections import defaultdict
from .conflict_resolver import ConflictResolver
from .layout_engine import LayoutEngine
from .latex_generator import LaTeXGenerator
from .geometric_helper import GeometricHelper


class DiagramGenerator:
    """Generates LaTeX/TikZ diagrams from JSON specifications."""
    
    # Spacing between elements within the same group
    WITHIN_GROUP_SPACING = 2.0
    
    def __init__(self, spec: Dict, template_path: str = 'templates/template.tex'):
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
        
        # Initialize conflict resolver
        self.conflict_resolver = ConflictResolver(self.WITHIN_GROUP_SPACING)
        
        # Initialize layout engine
        self.layout_engine = LayoutEngine(self.WITHIN_GROUP_SPACING)
        
        # Initialize LaTeX generator
        self.latex_generator = LaTeXGenerator(template_path, self.WITHIN_GROUP_SPACING)
    
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
    

    
    def _check_arrow_intersections(self, node_positions, links, return_conflicts=False):
        """Delegate to ConflictResolver."""
        return self.conflict_resolver.check_arrow_intersections(
            node_positions, links, return_conflicts
        )
    
    def _segments_intersect(self, x1, y1, x2, y2, x3, y3, x4, y4):
        """Delegate to GeometricHelper."""
        return GeometricHelper.segments_intersect(x1, y1, x2, y2, x3, y3, x4, y4)
    
    def _line_intersects_box(self, x1, y1, x2, y2, box_min_x, box_min_y, box_max_x, box_max_y):
        """Delegate to GeometricHelper."""
        return GeometricHelper.line_intersects_box(
            x1, y1, x2, y2, box_min_x, box_min_y, box_max_x, box_max_y
        )
    
    def _resolve_conflicts_iteratively(self, node_positions, levels, positions, max_iterations=10):
        """Delegate to ConflictResolver."""
        outgoing, incoming = self._build_dependency_graph()
        return self.conflict_resolver.resolve_conflicts_iteratively(
            node_positions, levels, positions, outgoing, incoming,
            self.group_name_to_group, max_iterations
        )
    def _compute_layout_bottom_up(self) -> Tuple[Dict[str, int], Dict[str, Tuple[float, List[str]]]]:
        """
        Compute both levels and positions using bottom-up approach with integrated collision avoidance.
        
        Delegates to LayoutEngine.
        
        Returns:
            Tuple of (levels dict, positions dict)
        """
        outgoing, incoming = self._build_dependency_graph()
        return self.layout_engine.compute_layout_bottom_up(
            self.group_name_to_group,
            self.element_to_group,
            outgoing,
            incoming
        )
    
    def generate_latex(self) -> str:
        """
        Generate the complete LaTeX document with dynamic spacing.
        
        Returns:
            String containing the LaTeX code
        """
        # Use new bottom-up layout algorithm
        levels, positions = self._compute_layout_bottom_up()
        
        # Build node positions for conflict resolution
        # (LaTeXGenerator will rebuild this, but we need it for conflict resolution)
        node_positions = {}
        for group_name, (start_x, elements) in positions.items():
            for i, elem in enumerate(elements):
                x = start_x + i * self.WITHIN_GROUP_SPACING
                y = levels[group_name]
                base_id = elem.lower().replace('+', 'plus').replace('-', 'minus').replace("'", 'p').replace('.', '_').replace(' ', '_')
                node_id = f"{base_id}_{int(x)}_{int(y)}"
                node_positions[elem] = (node_id, x, y)
        
        # Resolve conflicts iteratively
        node_positions, levels, positions = self._resolve_conflicts_iteratively(
            node_positions, levels, positions, max_iterations=10
        )
        
        # Final validation check
        self._check_arrow_intersections(node_positions, self.links)
        
        # Delegate to LaTeXGenerator for final code generation
        return self.latex_generator.generate(
            levels, positions, self.links, 
            self.group_name_to_group, self.element_to_group
        )


