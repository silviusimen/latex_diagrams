#!/usr/bin/env python3
"""
Conflict detection for diagram layouts.
"""

from typing import Dict, List, Tuple
from .geometric_helper import GeometricHelper

# Import spacing constants
from .spacing_constants import TEXT_WIDTH, TEXT_HEIGHT, WITHIN_GROUP_SPACING


class ConflictDetector:
    """Detects various types of conflicts in diagram layouts."""
    
    @staticmethod
    def build_position_lookup(node_positions: Dict) -> Dict:
        """
        Build a simple position lookup from node_positions.
        
        Args:
            node_positions: Dict mapping element names to (node_id, x, y)
            
        Returns:
            Dict mapping element names to (x, y)
        """
        positions = {}
        for elem, data in node_positions.items():
            if isinstance(data, tuple) and len(data) == 3:
                node_id, x, y = data
                positions[elem] = (x, y)
        return positions
    
    @staticmethod
    def build_arrow_list(links: Dict, positions: Dict) -> List:
        """
        Build list of arrows from links dictionary.
        
        Args:
            links: Dict of source -> target links
            positions: Dict mapping element names to (x, y)
            
        Returns:
            List of (source, sx, sy, target, tx, ty) tuples
        """
        arrows = []
        for source, targets in links.items():
            if not isinstance(targets, list):
                targets = [targets]
            for target in targets:
                if source in positions and target in positions:
                    sx, sy = positions[source]
                    tx, ty = positions[target]
                    arrows.append((source, sx, sy, target, tx, ty))
        return arrows
    
    @staticmethod
    def check_text_overlaps(positions: Dict) -> List:
        """
        Check for overlapping text elements.
        
        Args:
            positions: Dict mapping element names to (x, y)
            
        Returns:
            List of (name1, x1, y1, name2, x2, y2) tuples
        """
        text_overlaps = []
        node_list = list(positions.items())
        
        for i, (name1, (x1, y1)) in enumerate(node_list):
            for name2, (x2, y2) in node_list[i+1:]:
                # Same position = overlap
                if abs(x1 - x2) < 0.1 and abs(y1 - y2) < 0.1:
                    text_overlaps.append((name1, x1, y1, name2, x2, y2))
                # Horizontal overlap on same level
                elif abs(y1 - y2) < 0.1:
                    text_width = TEXT_WIDTH  # from spacing_constants
                    if abs(x1 - x2) < text_width:
                        text_overlaps.append((name1, x1, y1, name2, x2, y2))
        
        return text_overlaps
    
    @staticmethod
    def check_arrow_crossings(arrows: List) -> List:
        """
        Check for arrow-arrow intersections.
        
        Args:
            arrows: List of (source, sx, sy, target, tx, ty) tuples
            
        Returns:
            List of (s1, t1, s2, t2, ix, iy) tuples
        """
        arrow_crossings = []
        
        for i, (s1, sx1, sy1, t1, tx1, ty1) in enumerate(arrows):
            for s2, sx2, sy2, t2, tx2, ty2 in arrows[i+1:]:
                # Skip if arrows share endpoints
                if s1 == s2 or s1 == t2 or t1 == s2 or t1 == t2:
                    continue
                
                # Check if segments intersect
                if GeometricHelper.segments_intersect(sx1, sy1, tx1, ty1, sx2, sy2, tx2, ty2):
                    # Calculate intersection point
                    denom = (sx1 - tx1) * (sy2 - ty2) - (sy1 - ty1) * (sx2 - tx2)
                    if abs(denom) > 0.0001:
                        t = ((sx1 - sx2) * (sy2 - ty2) - (sy1 - sy2) * (sx2 - tx2)) / denom
                        ix = sx1 + t * (tx1 - sx1)
                        iy = sy1 + t * (ty1 - sy1)
                        arrow_crossings.append((s1, t1, s2, t2, ix, iy))
        
        return arrow_crossings
    
    @staticmethod
    def check_arrow_through_text(arrows: List, positions: Dict) -> List:
        """
        Check for arrows passing through text boxes.
        
        Args:
            arrows: List of (source, sx, sy, target, tx, ty) tuples
            positions: Dict mapping element names to (x, y)
            
        Returns:
            List of (source, target, name, nx, ny) tuples
        """
        arrow_through_text = []
        text_width = TEXT_WIDTH
        text_height = TEXT_HEIGHT
        
        for source, sx, sy, target, tx, ty in arrows:
            for name, (nx, ny) in positions.items():
                # Skip source and target nodes
                if name == source or name == target:
                    continue
                
                # Check if arrow passes through text box
                box_min_x = nx - text_width / 2
                box_max_x = nx + text_width / 2
                box_min_y = ny - text_height / 2
                box_max_y = ny + text_height / 2
                
                if GeometricHelper.line_intersects_box(sx, sy, tx, ty, box_min_x, box_min_y, box_max_x, box_max_y):
                    arrow_through_text.append((source, target, name, nx, ny))
        
        return arrow_through_text
    
    @staticmethod
    def detect_all_conflicts(node_positions: Dict, links: Dict, 
                           element_to_group: Dict = None, 
                           group_name_to_group: Dict = None,
                           group_center_nodes: Dict = None,
                           positions: Dict = None,
                           levels: Dict = None,
                           within_group_spacing: float = WITHIN_GROUP_SPACING) -> Tuple[List, List, List]:
        """
        Detect all types of conflicts in the diagram.
        
        Args:
            node_positions: Dict mapping element names to (node_id, x, y)
            links: Dict of source -> target links
            element_to_group: Mapping of elements to their containing groups
            group_name_to_group: Mapping of group names to group specs
            group_center_nodes: Dict of center node IDs for underlined groups
            positions: Dict of group positions (start_x, elements)
            levels: Dict of group y-levels
            within_group_spacing: Spacing between elements within groups
            
        Returns:
            Tuple of (text_overlaps, arrow_crossings, arrow_through_text)
        """
        pos_lookup = ConflictDetector.build_position_lookup(node_positions)
        
        # Adjust positions for arrows from underlined groups
        adjusted_positions = pos_lookup.copy()
        if (element_to_group and group_name_to_group and group_center_nodes and 
            positions and levels):
            for source in links.keys():
                source_group = element_to_group.get(source, source)
                if source_group in group_name_to_group:
                    group_obj = group_name_to_group[source_group]
                    has_underline = group_obj.get('underline', False)
                    if has_underline and source == source_group and source_group in group_center_nodes:
                        # For underlined groups, compute center node position from group data
                        start_x, elements = positions[source_group]
                        y = levels[source_group]
                        
                        # Find middle element (which is the center node)
                        middle_idx = len(elements) // 2
                        x = start_x + middle_idx * within_group_spacing
                        
                        # Offset y by -0.3 to simulate .south anchor
                        adjusted_positions[source] = (x, y - 0.3)
        
        arrows = ConflictDetector.build_arrow_list(links, adjusted_positions)
        
        text_overlaps = ConflictDetector.check_text_overlaps(pos_lookup)
        arrow_crossings = ConflictDetector.check_arrow_crossings(arrows)
        arrow_through_text = ConflictDetector.check_arrow_through_text(arrows, pos_lookup)
        
        return text_overlaps, arrow_crossings, arrow_through_text
