#!/usr/bin/env python3
"""
Conflict detection and resolution for diagram layouts.
"""

from typing import Dict, List, Tuple, Set
from collections import defaultdict


class ConflictResolver:
    """Handles collision detection and resolution for diagram elements."""
    
    def __init__(self, within_group_spacing: float = 2.0):
        """
        Initialize the conflict resolver.
        
        Args:
            within_group_spacing: Spacing between elements within groups
        """
        self.WITHIN_GROUP_SPACING = within_group_spacing
    
    def check_arrow_intersections(self, node_positions, links, return_conflicts=False):
        """
        Check for arrow intersections and conflicts.
        
        Args:
            node_positions: Dict mapping element names to (node_id, x, y)
            links: Dict of source -> target links
            return_conflicts: If True, return conflicts instead of printing
            
        Returns:
            If return_conflicts=True, returns (text_overlaps, arrow_crossings, arrow_through_text)
            Otherwise returns None
        """
        text_overlaps = []
        arrow_crossings = []
        arrow_through_text = []
        
        # Build position lookup
        positions = {}
        for elem, data in node_positions.items():
            if isinstance(data, tuple) and len(data) == 3:
                node_id, x, y = data
                positions[elem] = (x, y)
        
        # Check for text overlaps
        node_list = list(positions.items())
        for i, (name1, (x1, y1)) in enumerate(node_list):
            for name2, (x2, y2) in node_list[i+1:]:
                # Same position = overlap
                if abs(x1 - x2) < 0.1 and abs(y1 - y2) < 0.1:
                    text_overlaps.append((name1, x1, y1, name2, x2, y2))
                # Horizontal overlap on same level
                elif abs(y1 - y2) < 0.1:
                    # Estimate text width (~8 chars * 0.08 units)
                    text_width = 0.64
                    if abs(x1 - x2) < text_width:
                        text_overlaps.append((name1, x1, y1, name2, x2, y2))
        
        # Build arrow list
        arrows = []
        for source, targets in links.items():
            if not isinstance(targets, list):
                targets = [targets]
            for target in targets:
                if source in positions and target in positions:
                    sx, sy = positions[source]
                    tx, ty = positions[target]
                    arrows.append((source, sx, sy, target, tx, ty))
        
        # Check arrow-arrow intersections
        for i, (s1, sx1, sy1, t1, tx1, ty1) in enumerate(arrows):
            for s2, sx2, sy2, t2, tx2, ty2 in arrows[i+1:]:
                # Skip if arrows share endpoints
                if s1 == s2 or s1 == t2 or t1 == s2 or t1 == t2:
                    continue
                
                # Check if segments intersect
                if self._segments_intersect(sx1, sy1, tx1, ty1, sx2, sy2, tx2, ty2):
                    # Calculate intersection point
                    denom = (sx1 - tx1) * (sy2 - ty2) - (sy1 - ty1) * (sx2 - tx2)
                    if abs(denom) > 0.0001:
                        t = ((sx1 - sx2) * (sy2 - ty2) - (sy1 - sy2) * (sx2 - tx2)) / denom
                        ix = sx1 + t * (tx1 - sx1)
                        iy = sy1 + t * (ty1 - sy1)
                        arrow_crossings.append((s1, t1, s2, t2, ix, iy))
        
        # Check arrow-through-text
        for source, sx, sy, target, tx, ty in arrows:
            for name, (nx, ny) in positions.items():
                # Skip source and target nodes
                if name == source or name == target:
                    continue
                
                # Check if arrow passes through text box
                text_width = 0.64
                text_height = 0.3
                box_min_x = nx - text_width / 2
                box_max_x = nx + text_width / 2
                box_min_y = ny - text_height / 2
                box_max_y = ny + text_height / 2
                
                if self._line_intersects_box(sx, sy, tx, ty, box_min_x, box_min_y, box_max_x, box_max_y):
                    arrow_through_text.append((source, target, name, nx, ny))
        
        if return_conflicts:
            return text_overlaps, arrow_crossings, arrow_through_text
        
        # Print warnings
        if text_overlaps or arrow_crossings or arrow_through_text:
            print("\nWARNING: Arrow intersections detected!")
            for name1, x1, y1, name2, x2, y2 in text_overlaps:
                print(f"  - Text overlap: '{name1}' at ({x1}, {y1}) overlaps '{name2}' at ({x2}, {y2})")
            for s1, t1, s2, t2, ix, iy in arrow_crossings:
                print(f"  - Arrow intersection at ({ix:.2f}, {iy:.2f}): {s1}->{t1} crosses {s2}->{t2}")
            for source, target, name, nx, ny in arrow_through_text:
                print(f"  - Arrow {source}->{target} passes through text '{name}' at ({nx}, {ny})")
    
    def _line_intersects_box(self, x1, y1, x2, y2, box_min_x, box_min_y, box_max_x, box_max_y):
        """
        Check if line segment intersects with a rectangular box.
        
        Args:
            x1, y1: Start point of line
            x2, y2: End point of line
            box_min_x, box_min_y: Bottom-left corner of box
            box_max_x, box_max_y: Top-right corner of box
            
        Returns:
            True if line intersects box
        """
        # Check if either endpoint is inside box
        if (box_min_x <= x1 <= box_max_x and box_min_y <= y1 <= box_max_y):
            return True
        if (box_min_x <= x2 <= box_max_x and box_min_y <= y2 <= box_max_y):
            return True
        
        # Check intersection with each edge of the box
        edges = [
            (box_min_x, box_min_y, box_max_x, box_min_y),  # bottom
            (box_max_x, box_min_y, box_max_x, box_max_y),  # right
            (box_max_x, box_max_y, box_min_x, box_max_y),  # top
            (box_min_x, box_max_y, box_min_x, box_min_y),  # left
        ]
        
        for ex1, ey1, ex2, ey2 in edges:
            if self._segments_intersect(x1, y1, x2, y2, ex1, ey1, ex2, ey2):
                return True
        
        return False
    
    def _segments_intersect(self, x1, y1, x2, y2, x3, y3, x4, y4):
        """
        Check if two line segments intersect.
        
        Uses the orientation method to check if segments (x1,y1)-(x2,y2) and
        (x3,y3)-(x4,y4) intersect.
        
        Returns:
            True if segments intersect
        """
        def ccw(ax, ay, bx, by, cx, cy):
            return (cy - ay) * (bx - ax) > (by - ay) * (cx - ax)
        
        return (ccw(x1, y1, x3, y3, x4, y4) != ccw(x2, y2, x3, y3, x4, y4) and
                ccw(x1, y1, x2, y2, x3, y3) != ccw(x1, y1, x2, y2, x4, y4))
    
    def resolve_conflicts_iteratively(self, node_positions, levels, positions, 
                                     outgoing, incoming, group_name_to_group,
                                     max_iterations=10):
        """
        Iteratively resolve conflicts by shifting groups.
        
        Args:
            node_positions: Dict mapping element names to (node_id, x, y)
            levels: Dict mapping group names to y-levels
            positions: Dict mapping group names to (start_x, elements)
            outgoing: Dict of outgoing links from each group
            incoming: Dict of incoming links to each group
            group_name_to_group: Dict mapping group names to group specs
            max_iterations: Maximum number of iterations
            
        Returns:
            Updated (node_positions, levels, positions)
        """
        print("\n=== Starting Conflict Resolution ===\n")
        
        for iteration in range(max_iterations):
            # Check current conflicts
            text_overlaps, arrow_crossings, arrow_through_text = self.check_arrow_intersections(
                node_positions, outgoing, return_conflicts=True
            )
            
            total_conflicts = len(text_overlaps) + len(arrow_crossings) + len(arrow_through_text)
            
            if iteration == 0:
                print(f"--- Initial State Before Resolution ---")
                print(f"Initial conflicts: {total_conflicts}")
                print(f"  - Text overlaps: {len(text_overlaps)}")
                print(f"  - Arrow crossings: {len(arrow_crossings)}")
                print(f"  - Arrow through text: {len(arrow_through_text)}\n")
            
            if total_conflicts == 0:
                if iteration == 0:
                    print(f"Iteration 1: 0 conflicts detected")
                    print(f"  - Text overlaps: 0")
                    print(f"  - Arrow crossings: 0")
                    print(f"  - Arrow through text: 0\n")
                print("✓ All conflicts resolved!\n")
                break
            
            print(f"Iteration {iteration + 1}: {total_conflicts} conflicts detected")
            print(f"  - Text overlaps: {len(text_overlaps)}")
            print(f"  - Arrow crossings: {len(arrow_crossings)}")
            print(f"  - Arrow through text: {len(arrow_through_text)}")
            
            # Try to resolve conflicts
            resolved_any = False
            
            # Resolve text overlaps by shifting horizontally
            for name1, x1, y1, name2, x2, y2 in text_overlaps:
                # Find which groups these elements belong to
                group1 = self._find_group_for_element(name1, group_name_to_group)
                group2 = self._find_group_for_element(name2, group_name_to_group)
                
                if group1 and group1 in positions:
                    start_x, elements = positions[group1]
                    # Shift group1 right
                    new_start = start_x + 1.0
                    positions[group1] = (new_start, elements)
                    
                    # Update node positions
                    for i, elem in enumerate(elements):
                        if elem in node_positions:
                            old_node_id, old_x, old_y = node_positions[elem]
                            node_positions[elem] = (old_node_id, new_start + i * self.WITHIN_GROUP_SPACING, old_y)
                    
                    print(f"    → Shifted {group1} by +1.0")
                    resolved_any = True
                    break
            
            # Resolve arrow crossings by shifting groups vertically or horizontally
            if not resolved_any:
                for s1, t1, s2, t2, ix, iy in arrow_crossings:
                    # Find groups for sources
                    group_s1 = self._find_group_for_element(s1, group_name_to_group)
                    group_s2 = self._find_group_for_element(s2, group_name_to_group)
                    
                    # Try shifting one of the source groups horizontally
                    if group_s1 and group_s1 in positions:
                        start_x, elements = positions[group_s1]
                        new_start = start_x + 1.5
                        positions[group_s1] = (new_start, elements)
                        
                        for i, elem in enumerate(elements):
                            if elem in node_positions:
                                old_node_id, old_x, old_y = node_positions[elem]
                                node_positions[elem] = (old_node_id, new_start + i * self.WITHIN_GROUP_SPACING, old_y)
                        
                        print(f"    → Shifted {group_s1} horizontally by +1.5 to avoid crossing")
                        resolved_any = True
                        break
            
            # Resolve arrow-through-text by shifting the text group
            if not resolved_any:
                for source, target, name, nx, ny in arrow_through_text:
                    group = self._find_group_for_element(name, group_name_to_group)
                    
                    if group and group in positions:
                        start_x, elements = positions[group]
                        
                        # Check if this group has incoming links (should be stable)
                        if incoming.get(group):
                            # Shift horizontally with smaller amount (avoiding horizontal arrow)
                            new_start = start_x + 1.5
                            positions[group] = (new_start, elements)
                            
                            for i, elem in enumerate(elements):
                                if elem in node_positions:
                                    old_node_id, old_x, old_y = node_positions[elem]
                                    node_positions[elem] = (old_node_id, new_start + i * self.WITHIN_GROUP_SPACING, old_y)
                            
                            print(f"    → Shifted {group} horizontally by +1.5 (avoiding horizontal arrow)")
                        else:
                            # Shift horizontally
                            new_start = start_x + 1.0
                            positions[group] = (new_start, elements)
                            
                            for i, elem in enumerate(elements):
                                if elem in node_positions:
                                    old_node_id, old_x, old_y = node_positions[elem]
                                    node_positions[elem] = (old_node_id, new_start + i * self.WITHIN_GROUP_SPACING, old_y)
                            
                            print(f"    → Shifted {group} horizontally by +1.0")
                        
                        resolved_any = True
                        break
            
            if not resolved_any:
                print(f"  ⚠ Could not resolve conflicts in iteration {iteration + 1}")
                break
            
            print()
        
        print("=== Conflict Resolution Complete ===")
        return node_positions, levels, positions
    
    def _find_group_for_element(self, element, group_name_to_group):
        """Find which group an element belongs to."""
        for group_name, group in group_name_to_group.items():
            if 'elements' in group:
                if element in group['elements']:
                    return group_name
            elif group_name == element:
                return group_name
        return None
