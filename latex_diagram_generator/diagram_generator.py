from typing import Dict, List, Tuple
from collections import defaultdict
from .conflict_resolver import ConflictResolver
from .layout_engine import LayoutEngine
from .latex_generator import LaTeXGenerator
from .geometric_helper import GeometricHelper

class DiagramGenerator:
    """Generates LaTeX/TikZ diagrams from JSON specifications."""
    
    # Import spacing constants
    from .spacing_constants import WITHIN_GROUP_SPACING, BETWEEN_GROUP_SPACING
    
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
        self.layout_engine = LayoutEngine(self.WITHIN_GROUP_SPACING, self.BETWEEN_GROUP_SPACING)
        
        # Initialize LaTeX generator
        self.latex_generator = LaTeXGenerator(template_path, self.WITHIN_GROUP_SPACING)

    @staticmethod
    def _round_coord(val):
        # If value is very close to an int, use int. Else, 1 decimal.
        if abs(val - round(val)) < 1e-4:
            return str(int(round(val)))
        return f"{val:.1f}"
    
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
    
    def _resolve_conflicts_iteratively(self, node_positions, levels, positions, group_center_nodes=None, max_iterations=10):
        """Delegate to ConflictResolver."""
        outgoing, incoming = self._build_dependency_graph()
        return self.conflict_resolver.resolve_conflicts_iteratively(
            node_positions, levels, positions, outgoing, incoming,
            self.group_name_to_group, self.element_to_group, group_center_nodes, max_iterations
        )
    def _compute_layout_bottom_up(self) -> Tuple[Dict[str, int], Dict[str, Tuple[float, List[str]]]]:
        """
        Compute both levels and positions using new bottom-up arrow-aware approach.
        """
        from .conflict_detector import ConflictDetector
        outgoing, incoming = self._build_dependency_graph()
        return self.layout_engine.compute_layout_bottom_up_arrow_aware(
            self.group_name_to_group,
            self.element_to_group,
            outgoing,
            incoming,
            ConflictDetector()
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
                # Skip special symbols like '+' - they're visual separators, not nodes
                if elem in ['+', '-', '|']:
                    continue
                x = start_x + i * self.WITHIN_GROUP_SPACING
                y = levels[group_name]
                base_id = elem.lower().replace('+', 'plus').replace('-', 'minus').replace("'", 'p').replace('.', '_').replace(' ', '_')
                node_id = f"{base_id}_{int(x)}_{int(y)}"
                node_positions[elem] = (node_id, x, y)
        
        # Compute center nodes for underlined groups (needed for accurate conflict detection)
        group_center_nodes = {}
        for group_name in levels.keys():
            start_x, elements = positions[group_name]
            group_obj = self.group_name_to_group[group_name]
            center_node_id = self.latex_generator._get_center_node_for_underlined_group(
                group_name, group_obj, elements, start_x, levels[group_name]
            )
            if center_node_id:
                group_center_nodes[group_name] = center_node_id
        
        # Resolve conflicts iteratively
        node_positions, levels, positions = self._resolve_conflicts_iteratively(
            node_positions, levels, positions, group_center_nodes, max_iterations=10
        )
        
        # Apply group position overrides (at (x, y))
        for group in self.groups:
            override = group.get('override_position')
            group_name = group['name']
            if override is not None and group_name in positions and group_name in levels:
                pos_x, pos_y = override
                elements = positions[group_name][1]
                levels[group_name] = pos_y
                positions[group_name] = (pos_x, elements)
                for i, elem in enumerate(elements):
                    if elem in node_positions:
                        node_id, _, _ = node_positions[elem]
                        node_positions[elem] = (node_id, pos_x + i * self.WITHIN_GROUP_SPACING, pos_y)
        # Final validation check
        self._check_arrow_intersections(node_positions, self.links)
        
        # Delegate to LaTeXGenerator for final code generation
        return self.latex_generator.generate(
            levels, positions, self.links, 
            self.group_name_to_group, self.element_to_group
        )

    def print_text_rows(self):
        """
        Print a text-only version of the diagram, row by row, matching the LaTeX row structure (no arrows).
        Adds extra spaces between groups for clarity.
        """
        levels, positions = self._compute_layout_bottom_up()
        rows = {}
        for group_name, y in levels.items():
            if y not in rows:
                rows[y] = []
            start_x, elements = positions[group_name]
            rows[y].append((start_x, elements))
        for y in sorted(rows.keys()):
            row = rows[y]
            row_sorted = sorted(row, key=lambda t: t[0])
            line = []
            for idx, (start_x, elements) in enumerate(row_sorted):
                if idx > 0:
                    line.append('   ')  # 3 spaces between groups
                line.extend(str(e) for e in elements)
            print(' '.join(line))



    def export_input_with_positions(self, output_path: str):
        """
        Export a version of the input file with groups annotated with their rendered positions.
        Args:
            output_path: Path to write the new input file
        """
        levels, positions = self._compute_layout_bottom_up()
        # Apply group position overrides so output matches rendered diagram
        self._apply_group_position_overrides(levels, positions)
        lines = []
        for group in self.groups:
            group_name = group['name']
            elements = group.get('elements', [group_name])
            start_x, _ = positions.get(group_name, (None, None))
            y = levels.get(group_name, None)
            if start_x is not None and y is not None:
                if 'elements' in group:
                    group_str = '[' + ' '.join(elements) + ']'
                else:
                    group_str = group_name
                modifiers = []
                if group.get('underline'):
                    modifiers.append('underline')
                sx = self._round_coord(start_x)
                sy = self._round_coord(y)
                modifiers.append(f'at ({sx}, {sy})')
                line = f'{group_str} {' '.join(modifiers)}'.strip()
            else:
                if 'elements' in group:
                    group_str = '[' + ' '.join(elements) + ']'
                else:
                    group_str = group_name
                modifiers = []
                if group.get('underline'):
                    modifiers.append('underline')
                line = f'{group_str} {' '.join(modifiers)}'.strip()
            lines.append(line)
        # Add links section
        lines.append('')
        lines.append('# Links')
        for source, target in self.links.items():
            lines.append(f'{source} -> {target}')
        with open(output_path, 'w') as f:
            f.write('\n'.join(lines) + '\n')

    def _apply_group_position_overrides(self, levels, positions, node_positions=None):
        """
        Apply group position overrides (at (x, y)) to levels and positions dicts, and optionally node_positions.
        """
        for group in self.groups:
            override = group.get('override_position')
            group_name = group['name']
            if override is not None and group_name in positions and group_name in levels:
                pos_x, pos_y = override
                elements = positions[group_name][1]
                levels[group_name] = pos_y
                positions[group_name] = (pos_x, elements)
                if node_positions is not None:
                    for i, elem in enumerate(elements):
                        if elem in node_positions:
                            node_id, _, _ = node_positions[elem]
                            node_positions[elem] = (node_id, pos_x + i * self.WITHIN_GROUP_SPACING, pos_y)

