#!/usr/bin/env python3
"""
LaTeX/TikZ Diagram Generator from JSON specification.

This script generates LaTeX diagrams with TikZ based on a JSON input specification.
It handles groups of elements, directed links, and special formatting like underlines.
"""

import json
import argparse
import re
import os
from typing import Dict, List, Tuple, Set
from collections import defaultdict
from text_parser import parse_text_format


class DiagramGenerator:
    """Generates LaTeX/TikZ diagrams from JSON specifications."""
    
    # Spacing between elements within the same group
    WITHIN_GROUP_SPACING = 2.0
    
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
    
    def _validate_triangles(self, groups_with_targets, node_positions):
        """
        Validate that triangles (group to target arrows) do not intersect.
        This is called during positioning but we don't have y-coords yet.
        Will be enhanced to pass y-coordinates when available.
        
        Args:
            groups_with_targets: List of group dictionaries with positions
            node_positions: Dictionary of element positions
        """
        # For now, skip detailed validation since we don't have y-coordinates
        # The envelope-based row breaking should prevent most intersections
        pass
    
    def _check_arrow_intersections(self, node_positions, links, return_conflicts=False):
        """
        Check for arrow intersections using proper 2D line segment intersection.
        Also checks if arrows pass through text bounding boxes.
        
        Args:
            node_positions: Dict mapping element names to (node_id, x, y)
            links: Dict mapping source to target
            return_conflicts: If True, return conflict data instead of printing
            
        Returns:
            If return_conflicts is True, returns dict with 'text_overlaps', 'arrow_crossings', 'arrow_through_text'
        """
        # Build list of line segments (source_x, source_y) -> (target_x, target_y)
        segments = []
        for source, target in links.items():
            if source in node_positions and target in node_positions:
                _, sx, sy = node_positions[source]
                _, tx, ty = node_positions[target]
                segments.append((source, target, sx, sy, tx, ty))
        
        # Build bounding boxes for all text elements
        # Approximate text width based on character count (assume ~0.15 units per char at font size 12)
        bounding_boxes = []
        for elem_name, (node_id, x, y) in node_positions.items():
            # Estimate text dimensions
            text_len = len(elem_name)
            # Width: approximately 0.12 units per character
            # Height: approximately 0.3 units
            half_width = text_len * 0.08
            half_height = 0.15
            
            # Bounding box: (min_x, min_y, max_x, max_y)
            bbox = (x - half_width, y - half_height, x + half_width, y + half_height)
            bounding_boxes.append((elem_name, bbox))
        
        violations = []
        
        # Check bounding box overlaps - ensure text elements don't touch
        min_separation = 0.1  # Minimum gap between text elements
        for i in range(len(bounding_boxes)):
            for j in range(i + 1, len(bounding_boxes)):
                elem1, (min_x1, min_y1, max_x1, max_y1) = bounding_boxes[i]
                elem2, (min_x2, min_y2, max_x2, max_y2) = bounding_boxes[j]
                
                # Check if boxes overlap or are too close
                # Boxes overlap if they intersect in both x and y dimensions
                x_overlap = not (max_x1 + min_separation < min_x2 or max_x2 + min_separation < min_x1)
                y_overlap = not (max_y1 + min_separation < min_y2 or max_y2 + min_separation < min_y1)
                
                if x_overlap and y_overlap:
                    violations.append(
                        f"Text overlap: '{elem1}' at ({(min_x1+max_x1)/2:.1f}, {(min_y1+max_y1)/2:.1f}) "
                        f"overlaps '{elem2}' at ({(min_x2+max_x2)/2:.1f}, {(min_y2+max_y2)/2:.1f})"
                    )
        
        # Check segment-to-segment intersections
        for i in range(len(segments)):
            for j in range(i + 1, len(segments)):
                s1 = segments[i]
                s2 = segments[j]
                
                source1, target1, x1, y1, x2, y2 = s1
                source2, target2, x3, y3, x4, y4 = s2
                
                # Check if line segments intersect using parametric form
                dx1 = x2 - x1
                dy1 = y2 - y1
                dx2 = x4 - x3
                dy2 = y4 - y3
                
                det = dx1 * dy2 - dy1 * dx2
                
                if abs(det) < 0.0001:
                    continue
                
                t = ((x3 - x1) * dy2 - (y3 - y1) * dx2) / det
                s = ((x3 - x1) * dy1 - (y3 - y1) * dx1) / det
                
                # Check if intersection is within both segments (avoid endpoints)
                if 0.01 < t < 0.99 and 0.01 < s < 0.99:
                    x_int = x1 + t * dx1
                    y_int = y1 + t * dy1
                    violations.append(
                        f"Arrow intersection at ({x_int:.2f}, {y_int:.2f}): "
                        f"{source1}->{target1} crosses {source2}->{target2}"
                    )
        
        # Check if arrows pass through text bounding boxes
        for source, target, x1, y1, x2, y2 in segments:
            for elem_name, (min_x, min_y, max_x, max_y) in bounding_boxes:
                # Skip if this bbox belongs to source or target of this arrow
                if elem_name == source or elem_name == target:
                    continue
                
                # Check if line segment intersects the bounding box
                if self._line_intersects_box(x1, y1, x2, y2, min_x, min_y, max_x, max_y):
                    violations.append(
                        f"Arrow {source}->{target} passes through text '{elem_name}' at ({(min_x+max_x)/2:.1f}, {(min_y+max_y)/2:.1f})"
                    )
        
        if return_conflicts:
            # Parse violations into structured data
            conflicts = {
                'text_overlaps': [],
                'arrow_crossings': [],
                'arrow_through_text': []
            }
            
            for v in violations:
                if v.startswith('Text overlap:'):
                    # Extract element names and positions
                    match = re.search(r"'([^']+)'.*?\(([^)]+)\).*?'([^']+)'.*?\(([^)]+)\)", v)
                    if match:
                        elem1, pos1, elem2, pos2 = match.groups()
                        x1, y1 = map(float, pos1.split(','))
                        x2, y2 = map(float, pos2.split(','))
                        conflicts['text_overlaps'].append({
                            'elem1': elem1, 'pos1': (x1, y1),
                            'elem2': elem2, 'pos2': (x2, y2)
                        })
                elif 'Arrow intersection' in v:
                    match = re.search(r"at \(([^)]+)\): ([^-]+)->([^ ]+) crosses ([^-]+)->(.+)", v)
                    if match:
                        pos, src1, tgt1, src2, tgt2 = match.groups()
                        x, y = map(float, pos.split(','))
                        conflicts['arrow_crossings'].append({
                            'intersection': (x, y),
                            'arrow1': (src1.strip(), tgt1.strip()),
                            'arrow2': (src2.strip(), tgt2.strip())
                        })
                elif 'passes through text' in v:
                    match = re.search(r"Arrow ([^-]+)->([^ ]+) passes through text '([^']+)'.*?\(([^)]+)\)", v)
                    if match:
                        src, tgt, elem, pos = match.groups()
                        x, y = map(float, pos.split(','))
                        conflicts['arrow_through_text'].append({
                            'arrow': (src.strip(), tgt.strip()),
                            'text': elem,
                            'text_pos': (x, y)
                        })
            
            return conflicts
        
        if violations:
            print("\nWARNING: Arrow intersections detected!")
            for v in violations:
                print(f"  - {v}")
            print()
        
        return None
    
    def _line_intersects_box(self, x1, y1, x2, y2, box_min_x, box_min_y, box_max_x, box_max_y):
        """
        Check if a line segment intersects a rectangular bounding box.
        
        Args:
            x1, y1, x2, y2: Line segment endpoints
            box_min_x, box_min_y, box_max_x, box_max_y: Bounding box coordinates
            
        Returns:
            True if the line intersects the box
        """
        # Check if either endpoint is inside the box
        if (box_min_x <= x1 <= box_max_x and box_min_y <= y1 <= box_max_y) or \
           (box_min_x <= x2 <= box_max_x and box_min_y <= y2 <= box_max_y):
            return True
        
        # Check intersection with each of the 4 edges of the box
        # Top edge
        if self._segments_intersect(x1, y1, x2, y2, box_min_x, box_max_y, box_max_x, box_max_y):
            return True
        # Bottom edge
        if self._segments_intersect(x1, y1, x2, y2, box_min_x, box_min_y, box_max_x, box_min_y):
            return True
        # Left edge
        if self._segments_intersect(x1, y1, x2, y2, box_min_x, box_min_y, box_min_x, box_max_y):
            return True
        # Right edge
        if self._segments_intersect(x1, y1, x2, y2, box_max_x, box_min_y, box_max_x, box_max_y):
            return True
        
        return False
    
    def _segments_intersect(self, x1, y1, x2, y2, x3, y3, x4, y4):
        """
        Check if two line segments intersect.
        
        Returns:
            True if segments intersect (including at endpoints)
        """
        dx1 = x2 - x1
        dy1 = y2 - y1
        dx2 = x4 - x3
        dy2 = y4 - y3
        
        det = dx1 * dy2 - dy1 * dx2
        
        if abs(det) < 0.0001:
            return False
        
        t = ((x3 - x1) * dy2 - (y3 - y1) * dx2) / det
        s = ((x3 - x1) * dy1 - (y3 - y1) * dx1) / det
        
        return 0 <= t <= 1 and 0 <= s <= 1
    
    def _resolve_conflicts_iteratively(self, node_positions, levels, positions, max_iterations=10):
        """
        Iteratively detect and resolve layout conflicts.
        
        Args:
            node_positions: Dict mapping element names to (node_id, x, y)
            levels: Dict mapping group names to y-levels
            positions: Dict mapping group names to (start_x, element_list)
            max_iterations: Maximum number of resolution passes
            
        Returns:
            Updated (node_positions, levels, positions) after resolution
        """
        print("\n=== Starting Conflict Resolution ===")
        conflicts_history = []
        
        # Check initial state
        print("\n--- Initial State Before Resolution ---")
        initial_conflicts = self._check_arrow_intersections(node_positions, self.links, return_conflicts=True)
        total_initial = (len(initial_conflicts['text_overlaps']) + 
                        len(initial_conflicts['arrow_crossings']) + 
                        len(initial_conflicts['arrow_through_text']))
        print(f"Initial conflicts: {total_initial}")
        print(f"  - Text overlaps: {len(initial_conflicts['text_overlaps'])}")
        print(f"  - Arrow crossings: {len(initial_conflicts['arrow_crossings'])}")
        print(f"  - Arrow through text: {len(initial_conflicts['arrow_through_text'])}")
        
        for iteration in range(max_iterations):
            # Check for conflicts
            conflicts = self._check_arrow_intersections(node_positions, self.links, return_conflicts=True)
            
            total_conflicts = (len(conflicts['text_overlaps']) + 
                             len(conflicts['arrow_crossings']) + 
                             len(conflicts['arrow_through_text']))
            
            print(f"\nIteration {iteration + 1}: {total_conflicts} conflicts detected")
            print(f"  - Text overlaps: {len(conflicts['text_overlaps'])}")
            print(f"  - Arrow crossings: {len(conflicts['arrow_crossings'])}")
            print(f"  - Arrow through text: {len(conflicts['arrow_through_text'])}")
            
            if total_conflicts == 0:
                print("\n✓ All conflicts resolved!")
                break
            
            # Track if we made any changes
            changes_made = False
            modified_groups = set()  # Track which groups we've already moved this iteration
            
            # Strategy 1: Resolve text overlaps by increasing spacing or moving to new row
            for overlap in conflicts['text_overlaps']:
                elem1, elem2 = overlap['elem1'], overlap['elem2']
                x1, y1 = overlap['pos1']
                x2, y2 = overlap['pos2']
                
                # Find which groups these belong to
                group1 = self.element_to_group.get(elem1, elem1)
                group2 = self.element_to_group.get(elem2, elem2)
                
                # Skip if we already moved either group this iteration
                if group1 in modified_groups or group2 in modified_groups:
                    continue
                
                # If same level, push them apart or move one to new row
                if abs(y1 - y2) < 0.1:  # Same level
                    # Try horizontal shift first, but if groups are too far apart already, move to new row
                    if abs(x2 - x1) > 10:  # Groups are already widely separated
                        # Move one to a new row instead
                        shift_group = group2 if x2 > x1 else group1
                        if shift_group in levels:
                            old_y = levels[shift_group]
                            new_y = old_y + 1
                            levels[shift_group] = new_y
                            
                            elements = positions[shift_group][1] if shift_group in positions else [elem2 if x2 > x1 else elem1]
                            for elem in elements:
                                if elem in node_positions:
                                    old_node_id, old_x, _ = node_positions[elem]
                                    node_positions[elem] = (old_node_id, old_x, new_y)
                            
                            modified_groups.add(shift_group)
                            changes_made = True
                            print(f"    → Moved {shift_group} from y={old_y} to y={new_y}")
                    else:
                        # Push the rightmost group further right
                        if x2 > x1:
                            shift_group = group2
                            shift_amount = 1.0
                        else:
                            shift_group = group1
                            shift_amount = 1.0
                        
                        # Update positions
                        if shift_group in positions:
                            old_start, elements = positions[shift_group]
                            new_start = old_start + shift_amount
                            positions[shift_group] = (new_start, elements)
                            
                            # Update node_positions
                            for i, elem in enumerate(elements):
                                old_node_id, old_x, old_y = node_positions[elem]
                                node_positions[elem] = (old_node_id, new_start + i * self.WITHIN_GROUP_SPACING, old_y)
                            
                            modified_groups.add(shift_group)
                            changes_made = True
                            print(f"    → Shifted {shift_group} by +{shift_amount}")
            
            # Strategy 2: Resolve arrow crossings - be conservative to avoid creating more crossings
            # Limit arrow crossing fixes per iteration to prevent escalation
            arrow_crossings_fixed = 0
            for crossing in conflicts['arrow_crossings'][:3]:  # Only fix first 3 per iteration
                if arrow_crossings_fixed >= 3:
                    break
                    
                src1, tgt1 = crossing['arrow1']
                src2, tgt2 = crossing['arrow2']
                
                # Find groups involved
                group_src1 = self.element_to_group.get(src1, src1)
                group_src2 = self.element_to_group.get(src2, src2)
                
                # Skip if we already moved either group this iteration
                if group_src1 in modified_groups or group_src2 in modified_groups:
                    continue
                
                # Get positions
                _, x1, y1 = node_positions[src1]
                _, x2, y2 = node_positions[src2]
                
                # Try horizontal shift first (less disruptive than vertical move)
                if x1 > x2:
                    move_group = group_src1
                    shift_amount = 1.5
                else:
                    move_group = group_src2
                    shift_amount = 1.5
                
                # Update positions horizontally
                if move_group in positions:
                    old_start, elements = positions[move_group]
                    new_start = old_start + shift_amount
                    positions[move_group] = (new_start, elements)
                    
                    for i, elem in enumerate(elements):
                        if elem in node_positions:
                            old_node_id, old_x, old_y = node_positions[elem]
                            node_positions[elem] = (old_node_id, new_start + i * self.WITHIN_GROUP_SPACING, old_y)
                    
                    modified_groups.add(move_group)
                    changes_made = True
                    arrow_crossings_fixed += 1
                    print(f"    → Shifted {move_group} horizontally by +{shift_amount} to avoid crossing")
            
            # Strategy 3: Resolve arrow-through-text by shifting text perpendicular to arrow
            # Limit fixes per iteration to prevent escalation
            arrow_text_fixed = 0
            for conflict in conflicts['arrow_through_text'][:2]:  # Only fix first 2 per iteration
                if arrow_text_fixed >= 2:
                    break
                    
                src, tgt = conflict['arrow']
                text_elem = conflict['text']
                text_x, text_y = conflict['text_pos']
                
                text_group = self.element_to_group.get(text_elem, text_elem)
                
                # Skip if we already moved this group
                if text_group in modified_groups:
                    continue
                
                # Get arrow direction
                _, sx, sy = node_positions[src]
                _, tx, ty = node_positions[tgt]
                
                # Move text perpendicular to arrow direction
                # If arrow is mostly vertical, shift text horizontally
                # If arrow is mostly horizontal, shift text vertically
                dx = tx - sx
                dy = ty - sy
                
                if abs(dx) < abs(dy):  # Mostly vertical arrow
                    # Shift text horizontally
                    shift_amount = 1.5
                    if text_group in positions:
                        old_start, elements = positions[text_group]
                        new_start = old_start + shift_amount
                        positions[text_group] = (new_start, elements)
                        
                        for i, elem in enumerate(elements):
                            old_node_id, old_x, old_y = node_positions[elem]
                            node_positions[elem] = (old_node_id, new_start + i * self.WITHIN_GROUP_SPACING, old_y)
                        
                        modified_groups.add(text_group)
                        changes_made = True
                        arrow_text_fixed += 1
                        print(f"    → Shifted {text_group} horizontally by +{shift_amount}")
                else:  # Mostly horizontal arrow
                    # For horizontal arrows, try shifting horizontally instead of vertically
                    # (vertical moves create more problems)
                    shift_amount = 1.5
                    if text_group in positions:
                        old_start, elements = positions[text_group]
                        new_start = old_start + shift_amount
                        positions[text_group] = (new_start, elements)
                        
                        for i, elem in enumerate(elements):
                            old_node_id, old_x, old_y = node_positions[elem]
                            node_positions[elem] = (old_node_id, new_start + i * self.WITHIN_GROUP_SPACING, old_y)
                        
                        modified_groups.add(text_group)
                        changes_made = True
                        arrow_text_fixed += 1
                        print(f"    → Shifted {text_group} horizontally by +{shift_amount} (avoiding horizontal arrow)")
            
            if not changes_made:
                print("\n⚠ No changes could be made - some conflicts may remain")
                break
            
            # Prevent runaway iterations if conflicts are multiplying
            if iteration > 0 and total_conflicts > conflicts_history[-1] * 1.5:
                print(f"\n⚠ Conflicts increasing ({conflicts_history[-1]} → {total_conflicts}), stopping")
                break
            
            conflicts_history.append(total_conflicts)
        
        print("\n=== Conflict Resolution Complete ===")
        return node_positions, levels, positions
    
    def _compute_layout_bottom_up(self) -> Tuple[Dict[str, int], Dict[str, Tuple[float, List[str]]]]:
        """
        Compute both levels and positions using bottom-up approach with integrated collision avoidance.
        
        Algorithm:
        1. Start from bottom (leaf nodes with no outgoing links)
        2. For each iteration, process groups that link to previously placed groups
        3. Order by destination positions left-to-right
        4. Place on new row with collision checking
        5. If row too crowded, move groups up based on priority (groups with inbound links first, from center)
        
        Returns:
            Tuple of (levels dict, positions dict)
        """
        outgoing, incoming = self._build_dependency_graph()
        all_groups = set(self.group_name_to_group.keys())
        
        levels = {}  # group_name -> y_level
        positions = {}  # group_name -> (start_x, elements)
        node_positions = {}  # elem -> x position
        
        placed_groups = set()
        current_y = 0
        
        # Find bottom groups (those with no outgoing links to other groups)
        bottom_groups = []
        for group_name in all_groups:
            group = self.group_name_to_group[group_name]
            has_outgoing = False
            
            if 'elements' in group:
                for elem in group['elements']:
                    if elem in outgoing:
                        target_list = outgoing[elem]
                        target = target_list[0] if isinstance(target_list, list) else target_list
                        target_group = self.element_to_group.get(target, target)
                        if target_group != group_name:
                            has_outgoing = True
                            break
            elif group_name in outgoing:
                target_list = outgoing[group_name]
                target = target_list[0] if isinstance(target_list, list) else target_list
                target_group = self.element_to_group.get(target, target)
                if target_group != group_name:
                    has_outgoing = True
            
            if not has_outgoing:
                bottom_groups.append(group_name)
        
        print(f"\n=== Bottom-Up Layout ===")
        print(f"Bottom groups: {bottom_groups}")
        
        # Place bottom groups with special handling for groups that point to each other
        # E.g., if underlined group points to C, C should be centered below it
        max_y_used = self._place_bottom_groups_intelligently(bottom_groups, current_y, levels, positions, 
                                                              node_positions, outgoing, incoming)
        placed_groups.update(bottom_groups)
        
        # Start next iteration from the highest y-level used
        current_y = max_y_used
        
        # Iterate upward
        iteration = 0
        while len(placed_groups) < len(all_groups):
            iteration += 1
            current_y += 1
            
            # Find groups that link to already-placed groups
            next_groups = []
            for group_name in all_groups:
                if group_name in placed_groups:
                    continue
                
                group = self.group_name_to_group[group_name]
                links_to_placed = False
                
                if 'elements' in group:
                    for elem in group['elements']:
                        if elem in outgoing:
                            target_list = outgoing[elem]
                            target = target_list[0] if isinstance(target_list, list) else target_list
                            target_group = self.element_to_group.get(target, target)
                            if target_group in placed_groups:
                                links_to_placed = True
                                break
                elif group_name in outgoing:
                    target_list = outgoing[group_name]
                    target = target_list[0] if isinstance(target_list, list) else target_list
                    target_group = self.element_to_group.get(target, target)
                    if target_group in placed_groups:
                        links_to_placed = True
                
                if links_to_placed:
                    next_groups.append(group_name)
            
            if not next_groups:
                # No more groups link to placed groups, place remaining
                next_groups = [g for g in all_groups if g not in placed_groups]
            
            if not next_groups:
                break
            
            print(f"\nIteration {iteration}: Processing {len(next_groups)} groups")
            
            # Order groups by their destination positions (left to right)
            groups_with_dest = []
            for group_name in next_groups:
                group = self.group_name_to_group[group_name]
                dest_x = None
                
                if 'elements' in group:
                    first_elem = group['elements'][0]
                    if first_elem in outgoing:
                        target_list = outgoing[first_elem]
                        target = target_list[0] if isinstance(target_list, list) else target_list
                        if target in node_positions:
                            dest_x = node_positions[target]
                elif group_name in outgoing:
                    target_list = outgoing[group_name]
                    target = target_list[0] if isinstance(target_list, list) else target_list
                    if target in node_positions:
                        dest_x = node_positions[target]
                
                groups_with_dest.append((group_name, dest_x if dest_x is not None else 999))
            
            # Sort by destination x position
            groups_with_dest.sort(key=lambda x: (x[1], x[0]))
            sorted_groups = [g[0] for g in groups_with_dest]
            
            # Try to place all groups on current row
            success = self._place_groups_on_row_with_overflow(
                sorted_groups, current_y, levels, positions, node_positions, 
                incoming, outgoing, placed_groups
            )
            
            placed_groups.update(sorted_groups)
        
        print(f"\n=== Layout Complete: {len(placed_groups)} groups placed ===")
        return levels, positions
    
    def _compute_levels(self) -> Dict[str, int]:
        """
        DEPRECATED: Use _compute_layout_bottom_up() instead.
        Kept for compatibility.
        
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
        
        # Build a proper dependency graph at the group level
        # For a link A -> B, A must be placed HIGHER than B (A depends on nothing, B depends on A)
        # So we track: which groups must this group be placed BELOW
        group_must_be_below = defaultdict(set)  # group -> set of groups that must be above it
        
        for target, sources in incoming.items():
            # Find which group contains the target
            target_group = self.element_to_group.get(target, target)
            
            for source in sources if isinstance(sources, list) else [sources]:
                # Find which group contains the source
                source_group = self.element_to_group.get(source, source)
                
                # target_group must be BELOW source_group (source is drawn higher)
                if source_group != target_group and source_group in all_nodes and target_group in all_nodes:
                    group_must_be_below[target_group].add(source_group)
        
        # Start with nodes that have no dependencies (nothing above them)
        no_dependencies = []
        for node in all_nodes:
            if node not in group_must_be_below or len(group_must_be_below[node]) == 0:
                no_dependencies.append(node)
        
        # Assign levels using longest path from top
        max_level = len(all_nodes)
        
        # Start top nodes at max level
        for node in no_dependencies:
            levels[node] = max_level
        
        # Process remaining nodes in topological order
        processed = set(no_dependencies)
        changed = True
        
        while changed:
            changed = False
            for node in all_nodes:
                if node in processed:
                    continue
                
                # Check if all dependencies are processed
                deps = group_must_be_below.get(node, set())
                if all(dep in processed for dep in deps):
                    # Compute level as one below the MINIMUM level of all parent groups
                    # (we need to be below ALL of them)
                    if deps:
                        min_dep_level = min(levels[dep] for dep in deps)
                        levels[node] = min_dep_level - 1
                    else:
                        levels[node] = max_level - len(processed)
                    
                    processed.add(node)
                    changed = True
        
        # Post-process: Intelligently spread groups at the same level to minimize conflicts
        # Specifically handle P2 and P3 type scenarios where multiple groups feed same target
        level_groups_dict = defaultdict(list)
        for node, level in levels.items():
            level_groups_dict[level].append(node)
        
        # For each level, if there are multiple sibling groups targeting same element,
        # spread them to minimize arrow crossings
        for level in sorted(level_groups_dict.keys(), reverse=True):
            groups_at_level = level_groups_dict[level]
            if len(groups_at_level) <= 1:
                continue
            
            # Group by their targets
            groups_by_target = defaultdict(list)
            for group in groups_at_level:
                # Find what this group targets
                target_elem = None
                group_obj = self.group_name_to_group.get(group)
                if group_obj and 'elements' in group_obj:
                    first_elem = group_obj['elements'][0]
                    if first_elem in outgoing:
                        target_list = outgoing[first_elem]
                        target_elem = target_list[0] if isinstance(target_list, list) else target_list
                elif group in outgoing:
                    target_list = outgoing[group]
                    target_elem = target_list[0] if isinstance(target_list, list) else target_list
                
                if target_elem:
                    target_group = self.element_to_group.get(target_elem, target_elem)
                    groups_by_target[target_group].append(group)
            
            # For groups targeting the same element, spread them vertically
            # Sort by group name to get consistent ordering (P2 before P3)
            offset = 0
            for target_group, sibling_groups in sorted(groups_by_target.items()):
                if len(sibling_groups) > 1:
                    # Sort siblings for consistent ordering
                    sibling_groups.sort()
                    for i, group in enumerate(sibling_groups):
                        levels[group] = level + offset + i
                    offset += len(sibling_groups)
                else:
                    # Single group, keep at current level
                    levels[sibling_groups[0]] = level + offset
                    offset += 1
        
        return levels
    
    def _place_bottom_groups_intelligently(self, group_names, y_level, levels, positions, 
                                           node_positions, outgoing, incoming):
        """
        Place bottom groups with special logic:
        - If one group points to another, place target at y_level, source at y_level + 1
        - Otherwise center all groups at y_level
        
        Returns:
            Maximum y-level used
        """
        if not group_names:
            return y_level
        
        # Find if any bottom groups point to other bottom groups
        source_to_target = {}
        for group_name in group_names:
            group = self.group_name_to_group[group_name]
            original_name = group.get('name', group_name)
            
            # Check if the original group name (the one used in links) points to another group
            if original_name in outgoing:
                target_list = outgoing[original_name]
                target = target_list[0] if isinstance(target_list, list) else target_list
                target_group = self.element_to_group.get(target, target)
                if target_group in group_names:
                    source_to_target[group_name] = target_group
            elif 'elements' in group:
                first_elem = group['elements'][0]
                if first_elem in outgoing:
                    target_list = outgoing[first_elem]
                    target = target_list[0] if isinstance(target_list, list) else target_list
                    target_group = self.element_to_group.get(target, target)
                    if target_group in group_names:
                        source_to_target[group_name] = target_group
        
        if source_to_target:
            # Place source-target pairs with vertical alignment
            # Place sources one row above targets
            targets = set(source_to_target.values())
            sources = set(source_to_target.keys())
            independent = [g for g in group_names if g not in sources and g not in targets]
            
            # Place targets at y_level (bottom), sources at y_level + 1 (one row above)
            for target in targets:
                target_group = self.group_name_to_group[target]
                target_elements = target_group.get('elements', [target])
                
                # Place target centered at x=6.0
                if len(target_elements) > 1:
                    target_width = (len(target_elements) - 1) * self.WITHIN_GROUP_SPACING
                    target_start = 6.0 - target_width / 2.0
                else:
                    target_start = 6.0
                
                levels[target] = y_level
                positions[target] = (target_start, target_elements)
                
                for i, elem in enumerate(target_elements):
                    node_positions[elem] = target_start + i * self.WITHIN_GROUP_SPACING
            
            # Place sources at y_level + 1, centered above their targets
            for source, target in source_to_target.items():
                if target in positions:
                    target_start, target_elements = positions[target]
                    
                    # Calculate center of target
                    if len(target_elements) > 1:
                        target_width = (len(target_elements) - 1) * self.WITHIN_GROUP_SPACING
                        target_center = target_start + target_width / 2.0
                    else:
                        target_center = target_start
                    
                    # Place source centered above target
                    source_group = self.group_name_to_group[source]
                    source_elements = source_group.get('elements', [source])
                    
                    if len(source_elements) > 1:
                        source_width = (len(source_elements) - 1) * self.WITHIN_GROUP_SPACING
                        source_start = target_center - source_width / 2.0
                    else:
                        source_start = target_center
                    
                    levels[source] = y_level + 1
                    positions[source] = (source_start, source_elements)
                    
                    for i, elem in enumerate(source_elements):
                        node_positions[elem] = source_start + i * self.WITHIN_GROUP_SPACING
            
            # Place independent groups at y_level with the targets
            if independent:
                self._place_groups_on_row(independent, y_level, levels, positions, 
                                          node_positions, center=True)
            
            # Return max y-level used (sources are at y_level + 1)
            return y_level + 1 if source_to_target else y_level
        else:
            # No dependencies among bottom groups, just center them
            self._place_groups_on_row(group_names, y_level, levels, positions, 
                                      node_positions, center=True)
            return y_level

    
    def _place_groups_on_row(self, group_names, y_level, levels, positions, node_positions, center=False):
        """
        Place a list of groups on a single row.
        
        Args:
            group_names: List of group names to place
            y_level: Y-coordinate for this row
            levels: Dict to update with group levels
            positions: Dict to update with group positions
            node_positions: Dict to update with element positions
            center: If True, center the groups around x=6.0
        """
        if not group_names:
            return
        
        # Calculate total width needed
        group_widths = []
        for group_name in group_names:
            group = self.group_name_to_group[group_name]
            if 'elements' in group:
                num_elements = len(group['elements'])
                width = (num_elements - 1) * self.WITHIN_GROUP_SPACING if num_elements > 1 else 0
            else:
                width = 0
            group_widths.append(width)
        
        # Calculate starting x position
        if center:
            total_width = sum(group_widths) + (len(group_names) - 1) * 2.0  # 2.0 spacing between groups
            start_x = 6.0 - total_width / 2.0
        else:
            start_x = 0.0
        
        current_x = start_x
        for group_name, width in zip(group_names, group_widths):
            group = self.group_name_to_group[group_name]
            elements = group.get('elements', [group_name])
            
            levels[group_name] = y_level
            positions[group_name] = (current_x, elements)
            
            for i, elem in enumerate(elements):
                node_positions[elem] = current_x + i * self.WITHIN_GROUP_SPACING
            
            current_x += width + 2.0  # Move to next group position
    
    def _place_groups_on_row_with_overflow(self, group_names, start_y, levels, positions, 
                                           node_positions, incoming, outgoing, placed_groups):
        """
        Place groups on row(s) with overflow handling.
        
        If too crowded, moves groups to additional rows based on priority:
        1. Groups with inbound links (from center outward)
        2. Groups without inbound links (from center outward)
        
        Args:
            group_names: Ordered list of groups to place
            start_y: Starting y-level
            levels, positions, node_positions: Dicts to update
            incoming, outgoing: Dependency graphs
            placed_groups: Set of already placed groups
            
        Returns:
            True if successful
        """
        if not group_names:
            return True
        
        MAX_ROW_WIDTH = 20.0  # Maximum x-span for a row
        
        # Classify groups by whether they have inbound links
        groups_with_incoming = []
        groups_without_incoming = []
        
        for group_name in group_names:
            has_incoming = False
            group = self.group_name_to_group[group_name]
            
            if 'elements' in group:
                for elem in group['elements']:
                    if elem in incoming:
                        has_incoming = True
                        break
            elif group_name in incoming:
                has_incoming = True
            
            if has_incoming:
                groups_with_incoming.append(group_name)
            else:
                groups_without_incoming.append(group_name)
        
        # Try to place all on one row first
        rows = [group_names]
        current_y = start_y
        
        while True:
            all_fit = True
            
            for row_idx, row_groups in enumerate(rows):
                if not row_groups:
                    continue
                
                # Calculate width for this row
                total_width = self._calculate_row_width(row_groups)
                
                if total_width > MAX_ROW_WIDTH:
                    all_fit = False
                    print(f"  Row {current_y + row_idx} too wide ({total_width:.1f} > {MAX_ROW_WIDTH}), splitting...")
                    
                    # Split row - move groups with priority to new row
                    keep_on_row = []
                    move_to_next = []
                    
                    # Priority: groups with incoming links from center
                    groups_to_move = [g for g in row_groups if g in groups_with_incoming]
                    if not groups_to_move:
                        groups_to_move = [g for g in row_groups if g in groups_without_incoming]
                    
                    if groups_to_move:
                        # Find center and move closest group
                        center_x = 6.0
                        groups_with_target_x = []
                        for g in groups_to_move:
                            target_x = self._get_group_target_x(g, outgoing, node_positions)
                            groups_with_target_x.append((g, abs(target_x - center_x)))
                        
                        # Sort by distance from center
                        groups_with_target_x.sort(key=lambda x: x[1])
                        
                        # Move enough groups to make row fit
                        for g, _ in groups_with_target_x:
                            move_to_next.append(g)
                            test_keep = [x for x in row_groups if x not in move_to_next]
                            if self._calculate_row_width(test_keep) <= MAX_ROW_WIDTH:
                                keep_on_row = test_keep
                                break
                        
                        if not keep_on_row:
                            # Still too wide, move half
                            mid = len(row_groups) // 2
                            keep_on_row = row_groups[:mid]
                            move_to_next = row_groups[mid:]
                    else:
                        # Fallback: split in half
                        mid = len(row_groups) // 2
                        keep_on_row = row_groups[:mid]
                        move_to_next = row_groups[mid:]
                    
                    rows[row_idx] = keep_on_row
                    if row_idx + 1 < len(rows):
                        rows[row_idx + 1] = move_to_next + rows[row_idx + 1]
                    else:
                        rows.append(move_to_next)
                    break
            
            if all_fit:
                break
        
        # Place groups on their assigned rows
        for row_idx, row_groups in enumerate(rows):
            if row_groups:
                y = start_y + row_idx
                self._place_groups_on_row_centered_by_target(
                    row_groups, y, levels, positions, node_positions, outgoing
                )
                print(f"  Placed {len(row_groups)} groups on row {y}: {row_groups}")
        
        return True
    
    def _calculate_row_width(self, group_names):
        """Calculate total width needed for groups including spacing."""
        if not group_names:
            return 0.0
        
        total = 0.0
        for i, group_name in enumerate(group_names):
            group = self.group_name_to_group[group_name]
            if 'elements' in group:
                num_elements = len(group['elements'])
                width = (num_elements - 1) * self.WITHIN_GROUP_SPACING if num_elements > 1 else 0
            else:
                width = 0
            total += width
            if i < len(group_names) - 1:
                total += 2.0  # Inter-group spacing
        
        return total
    
    def _get_group_target_x(self, group_name, outgoing, node_positions):
        """Get the target x-position for a group based on where it points."""
        group = self.group_name_to_group[group_name]
        
        if 'elements' in group:
            first_elem = group['elements'][0]
            if first_elem in outgoing:
                target_list = outgoing[first_elem]
                target = target_list[0] if isinstance(target_list, list) else target_list
                if target in node_positions:
                    return node_positions[target]
        elif group_name in outgoing:
            target_list = outgoing[group_name]
            target = target_list[0] if isinstance(target_list, list) else target_list
            if target in node_positions:
                return node_positions[target]
        
        return 6.0  # Default center
    
    def _place_groups_on_row_centered_by_target(self, group_names, y_level, levels, 
                                                 positions, node_positions, outgoing):
        """Place groups on a row, each centered above its target."""
        for group_name in group_names:
            group = self.group_name_to_group[group_name]
            elements = group.get('elements', [group_name])
            
            # Get target position
            target_x = self._get_group_target_x(group_name, outgoing, node_positions)
            
            # Calculate group width
            if len(elements) > 1:
                width = (len(elements) - 1) * self.WITHIN_GROUP_SPACING
            else:
                width = 0
            
            # Center above target
            start_x = target_x - width / 2.0
            
            # Check for collisions with already placed groups at this level
            # and adjust if needed
            for other_group in levels:
                if levels[other_group] == y_level and other_group != group_name:
                    other_start, other_elements = positions[other_group]
                    other_width = (len(other_elements) - 1) * self.WITHIN_GROUP_SPACING if len(other_elements) > 1 else 0
                    other_end = other_start + other_width
                    
                    my_end = start_x + width
                    
                    # Check for overlap (need 2.0 spacing)
                    if not (my_end + 2.0 < other_start or start_x > other_end + 2.0):
                        # Overlap! Shift right
                        start_x = other_end + 2.0
            
            levels[group_name] = y_level
            positions[group_name] = (start_x, elements)
            
            for i, elem in enumerate(elements):
                node_positions[elem] = start_x + i * self.WITHIN_GROUP_SPACING
    
    def _compute_horizontal_positions(self, levels: Dict[str, int]) -> Dict[str, Tuple[float, List[str]]]:
        """
        Compute horizontal positions ensuring children align with parents vertically.
        Breaks up wide levels into multiple rows to prevent overcrowding.
        
        Args:
            levels: Dictionary mapping group names to vertical levels
            
        Returns:
            Dictionary mapping group names to (start_x, element_list) tuples
        """
        # Group by level while preserving declaration order
        level_groups = defaultdict(list)
        for group in self.groups:
            group_name = group['name']
            if group_name in levels:
                level = levels[group_name]
                level_groups[level].append(group_name)
        
        # Build reverse lookup
        outgoing, incoming = self._build_dependency_graph()
        
        positions = {}
        
        # Maximum elements per row before wrapping to next sub-level
        MAX_ELEMENTS_PER_ROW = 6
        
        # Track node positions as we place them (for aligning children)
        node_positions_temp = {}  # elem -> x position
        
        # Process levels from BOTTOM to TOP (so we know target positions)
        sorted_levels = sorted(level_groups.keys())  # Ascending order - bottom first
        
        # Track actual y-positions (may differ from logical levels due to row-wrapping)
        # Start from 0 for the bottom level
        actual_y_positions = {}
        current_y = 0
        
        for level_idx, level in enumerate(sorted_levels):
            groups_at_level = level_groups[level]
            
            if level_idx == 0:
                # Bottom level: center single nodes in the middle of the layout
                for group_name in groups_at_level:
                    group = self.group_name_to_group[group_name]
                    
                    if 'elements' in group:
                        elements = group['elements']
                        num_elements = len(elements)
                        # Calculate actual width with spacing
                        actual_width = (num_elements - 1) * self.WITHIN_GROUP_SPACING if num_elements > 1 else 0
                        # Center multi-element groups around x=6
                        level_x = 6.0 - actual_width / 2.0
                        positions[group_name] = (level_x, elements)
                        for i, elem in enumerate(elements):
                            node_positions_temp[elem] = level_x + i * self.WITHIN_GROUP_SPACING
                    else:
                        # Single element - center it at x=6
                        level_x = 6.0
                        positions[group_name] = (level_x, [group_name])
                        node_positions_temp[group_name] = level_x
                    
                    actual_y_positions[group_name] = current_y
                current_y += 1
            else:
                # For higher levels, use slot-based positioning to avoid crossings
                # Each group gets a slot centered on its target
                groups_with_targets = []
                
                for group_name in groups_at_level:
                    group = self.group_name_to_group[group_name]
                    
                    # Calculate group width (accounting for spacing between elements)
                    if 'elements' in group:
                        # Width spans from first to last element position
                        num_elements = len(group['elements'])
                        width = (num_elements - 1) * self.WITHIN_GROUP_SPACING + 1 if num_elements > 1 else 1
                        elements = group['elements']
                    else:
                        width = 1
                        elements = [group_name]
                    
                    # Find the target position
                    target_x = None
                    first_elem = elements[0]
                    if first_elem in outgoing:
                        target_list = outgoing[first_elem]
                        target_elem = target_list[0] if isinstance(target_list, list) else target_list
                        if target_elem in node_positions_temp:
                            target_x = node_positions_temp[target_elem]
                    
                    groups_with_targets.append({
                        'name': group_name,
                        'width': width,
                        'elements': elements,
                        'target_x': target_x if target_x is not None else 999,
                        'desired_start': (target_x - (width - 1) / 2.0) if target_x is not None else None
                    })
                
                # Sort by target position
                groups_with_targets.sort(key=lambda x: (x['target_x'], x['name']))
                
                # Position groups to avoid any overlaps
                # Ensure minimum spacing of 1.0 between adjacent elements
                placed_groups = []
                
                for g in groups_with_targets:
                    target_x = g['target_x']
                    width = g['width']
                    
                    # Start with ideal position: centered above target
                    if target_x < 999:
                        # Center the group above its target
                        ideal_start = target_x - width / 2.0
                    else:
                        ideal_start = 1.0
                    
                    # Find a non-overlapping position
                    best_start = ideal_start
                    
                    for attempt in range(50):
                        test_start = ideal_start + attempt * 2.0  # Move by min spacing amount
                        test_end = test_start + width - 1  # Last element position
                        
                        # Check against all placed groups
                        # Require at least 2.0 unit gap between any elements (increased for text width)
                        has_overlap = False
                        for placed in placed_groups:
                            placed_start = placed['actual_start']
                            placed_end = placed['actual_start'] + placed['width'] - 1
                            
                            # Elements need 2.0 unit minimum separation
                            # Overlap if test_start to test_end is within 2.0 of placed range
                            if test_end + 2.0 > placed_start and test_start < placed_end + 2.0:
                                has_overlap = True
                                break
                        
                        if not has_overlap:
                            best_start = test_start
                            break
                    
                    # If we couldn't find a spot, place after all others with proper spacing
                    if has_overlap and placed_groups:
                        rightmost = max(p['actual_start'] + p['width'] - 1 for p in placed_groups)
                        best_start = rightmost + 2.0  # 2 unit gap from rightmost element
                    
                    g['actual_start'] = best_start
                    placed_groups.append(g)
                
                # Break into rows based on triangle envelope overlap to avoid visual crossings
                rows = []
                current_row = []
                
                for g in groups_with_targets:
                    target_x = g['target_x']
                    g_start = g['actual_start']
                    g_end = g['actual_start'] + g['width'] - 1
                    
                    # Calculate this group's triangle envelope
                    g_envelope_min = min(g_start, target_x) if target_x < 999 else g_start
                    g_envelope_max = max(g_end, target_x) if target_x < 999 else g_end
                    
                    # Decide if we should start a new row
                    should_break = False
                    
                    if current_row:
                        # Check for significant envelope overlap with any group in current row
                        for existing_g in current_row:
                            existing_start = existing_g['actual_start']
                            existing_end = existing_g['actual_start'] + existing_g['width'] - 1
                            existing_target = existing_g['target_x']
                            
                            existing_envelope_min = min(existing_start, existing_target) if existing_target < 999 else existing_start
                            existing_envelope_max = max(existing_end, existing_target) if existing_target < 999 else existing_end
                            
                            # Calculate envelope overlap
                            overlap_start = max(g_envelope_min, existing_envelope_min)
                            overlap_end = min(g_envelope_max, existing_envelope_max)
                            overlap = overlap_end - overlap_start
                            
                            # Break if ANY envelope overlap to avoid crossings
                            # Being very aggressive to prevent arrow intersections
                            if overlap > 0.5:
                                should_break = True
                                break
                        
                        # Also break if row is getting very wide
                        if not should_break:
                            all_starts = [eg['actual_start'] for eg in current_row] + [g_start]
                            all_ends = [eg['actual_start'] + eg['width'] - 1 for eg in current_row] + [g_end]
                            total_span = max(all_ends) - min(all_starts)
                            if total_span > 12:
                                should_break = True
                    
                    if should_break:
                        rows.append(current_row)
                        current_row = []
                    
                    current_row.append(g)
                
                if current_row:
                    rows.append(current_row)
                
                # Validate: check for triangle intersections
                self._validate_triangles(groups_with_targets, node_positions_temp)
                
                # Place each row
                for row in rows:
                    for g in row:
                        group = self.group_name_to_group[g['name']]
                        start_x = g['actual_start']
                        
                        if 'elements' in group:
                            positions[g['name']] = (start_x, group['elements'])
                            for i, elem in enumerate(group['elements']):
                                node_positions_temp[elem] = start_x + i * self.WITHIN_GROUP_SPACING
                        else:
                            positions[g['name']] = (start_x, [g['name']])
                            node_positions_temp[g['name']] = start_x
                        
                        actual_y_positions[g['name']] = current_y
                    
                    current_y += 1
        
        # Update the levels dict with actual y positions
        for group_name in actual_y_positions:
            levels[group_name] = actual_y_positions[group_name]
        
        return positions
    
    def generate_latex(self) -> str:
        """
        Generate the complete LaTeX document with dynamic spacing.
        
        Returns:
            String containing the LaTeX code
        """
        # Use new bottom-up layout algorithm
        levels, positions = self._compute_layout_bottom_up()
        
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
            group_obj = self.group_name_to_group[group_name]
            if group_obj.get('underline', False) and len(elements) > 0:
                center_idx = len(elements) // 2
                center_elem = elements[center_idx]
                center_x = start_x + center_idx * self.WITHIN_GROUP_SPACING
                center_node_id = f"{center_elem.lower().replace('+', 'plus').replace('-', 'minus').replace("'", 'p').replace('.', '_').replace(' ', '_')}_{int(center_x)}_{int(level)}"
                group_center_nodes[group_name] = center_node_id
        
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
        
        # Resolve conflicts iteratively
        node_positions, levels, positions = self._resolve_conflicts_iteratively(
            node_positions, levels, positions, max_iterations=10
        )
        
        # Final validation check
        self._check_arrow_intersections(node_positions, self.links)
        
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
