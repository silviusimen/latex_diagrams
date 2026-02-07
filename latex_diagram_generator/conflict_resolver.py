#!/usr/bin/env python3
"""
Conflict resolution for diagram layouts.
"""

from typing import Dict, List, Tuple
from .conflict_detector import ConflictDetector


class ConflictResolver:
    """Handles collision detection and resolution for diagram elements."""
    
    def __init__(self, within_group_spacing: float = 2.0):
        """
        Initialize the conflict resolver.
        
        Args:
            within_group_spacing: Spacing between elements within groups
        """
        self.WITHIN_GROUP_SPACING = within_group_spacing
        self.detector = ConflictDetector()
    
    def _report_conflicts(self, text_overlaps, arrow_crossings, arrow_through_text):
        """
        Print warning messages for detected conflicts.
        
        Args:
            text_overlaps: List of text overlap conflicts
            arrow_crossings: List of arrow crossing conflicts
            arrow_through_text: List of arrow-through-text conflicts
        """
        print("\nWARNING: Arrow intersections detected!")
        
        for name1, x1, y1, name2, x2, y2 in text_overlaps:
            print(f"  - Text overlap: '{name1}' at ({x1}, {y1}) overlaps '{name2}' at ({x2}, {y2})")
        
        for s1, t1, s2, t2, ix, iy in arrow_crossings:
            print(f"  - Arrow intersection at ({ix:.2f}, {iy:.2f}): {s1}->{t1} crosses {s2}->{t2}")
        
        for source, target, name, nx, ny in arrow_through_text:
            print(f"  - Arrow {source}->{target} passes through text '{name}' at ({nx}, {ny})")
    
    def check_arrow_intersections(self, node_positions, links, return_conflicts=False,
                                  element_to_group=None, group_name_to_group=None, group_center_nodes=None,
                                  positions=None, levels=None):
        """
        Check for arrow intersections and conflicts.
        
        Args:
            node_positions: Dict mapping element names to (node_id, x, y)
            links: Dict of source -> target links
            return_conflicts: If True, return conflicts instead of printing
            element_to_group: Mapping of elements to their groups
            group_name_to_group: Mapping of group names to specs
            group_center_nodes: Dict of center node IDs for underlined groups
            positions: Dict of group positions
            levels: Dict of group y-levels
            
        Returns:
            If return_conflicts=True, returns (text_overlaps, arrow_crossings, arrow_through_text)
            Otherwise returns None
        """
        # Detect all conflicts using the detector
        text_overlaps, arrow_crossings, arrow_through_text = self.detector.detect_all_conflicts(
            node_positions, links, element_to_group, group_name_to_group, group_center_nodes,
            positions, levels, self.WITHIN_GROUP_SPACING
        )
        
        if return_conflicts:
            return text_overlaps, arrow_crossings, arrow_through_text
        
        # Print warnings if conflicts found
        if text_overlaps or arrow_crossings or arrow_through_text:
            self._report_conflicts(text_overlaps, arrow_crossings, arrow_through_text)
    
    def _print_initial_status(self, total_conflicts: int, text_overlaps: List,
                             arrow_crossings: List, arrow_through_text: List):
        """
        Print initial conflict status.
        
        Args:
            total_conflicts: Total number of conflicts
            text_overlaps, arrow_crossings, arrow_through_text: Conflict lists
        """
        print(f"--- Initial State Before Resolution ---")
        print(f"Initial conflicts: {total_conflicts}")
        print(f"  - Text overlaps: {len(text_overlaps)}")
        print(f"  - Arrow crossings: {len(arrow_crossings)}")
        print(f"  - Arrow through text: {len(arrow_through_text)}\n")
    
    def _print_iteration_status(self, iteration: int, total_conflicts: int,
                               text_overlaps: List, arrow_crossings: List,
                               arrow_through_text: List):
        """
        Print status for a specific iteration.
        
        Args:
            iteration: Iteration number
            total_conflicts: Total number of conflicts
            text_overlaps, arrow_crossings, arrow_through_text: Conflict lists
        """
        if total_conflicts == 0:
            print(f"Iteration {iteration + 1}: 0 conflicts detected")
            print(f"  - Text overlaps: 0")
            print(f"  - Arrow crossings: 0")
            print(f"  - Arrow through text: 0\n")
        else:
            print(f"Iteration {iteration + 1}: {total_conflicts} conflicts detected")
            print(f"  - Text overlaps: {len(text_overlaps)}")
            print(f"  - Arrow crossings: {len(arrow_crossings)}")
            print(f"  - Arrow through text: {len(arrow_through_text)}")
    
    def _print_conflict_status(self, iteration: int, text_overlaps: List, 
                               arrow_crossings: List, arrow_through_text: List) -> int:
        """
        Print conflict status for current iteration.
        
        Args:
            iteration: Current iteration number (0-indexed)
            text_overlaps: List of text overlap conflicts
            arrow_crossings: List of arrow crossing conflicts
            arrow_through_text: List of arrow-through-text conflicts
            
        Returns:
            Total number of conflicts
        """
        total_conflicts = len(text_overlaps) + len(arrow_crossings) + len(arrow_through_text)
        
        if iteration == 0:
            self._print_initial_status(total_conflicts, text_overlaps, arrow_crossings, arrow_through_text)
        
        if total_conflicts == 0 and iteration == 0:
            self._print_iteration_status(iteration, total_conflicts, text_overlaps, arrow_crossings, arrow_through_text)
        elif total_conflicts > 0:
            self._print_iteration_status(iteration, total_conflicts, text_overlaps, arrow_crossings, arrow_through_text)
        
        return total_conflicts
    
    def _shift_group_horizontally(self, group_name: str, shift_amount: float, positions: Dict,
                                  node_positions: Dict) -> None:
        """
        Shift a group horizontally and update all its node positions.
        
        Args:
            group_name: Name of group to shift
            shift_amount: Amount to shift (positive = right)
            positions: Dict of group positions to update
            node_positions: Dict of node positions to update
        """
        start_x, elements = positions[group_name]
        new_start = start_x + shift_amount
        positions[group_name] = (new_start, elements)
        
        for i, elem in enumerate(elements):
            if elem in node_positions:
                old_node_id, old_x, old_y = node_positions[elem]
                node_positions[elem] = (old_node_id, new_start + i * self.WITHIN_GROUP_SPACING, old_y)
    
    def _shift_group_vertically(self, group_name: str, shift_amount: float, levels: Dict,
                                positions: Dict, node_positions: Dict) -> None:
        """
        Shift a group vertically and update all its node positions.
        
        Args:
            group_name: Name of group to shift
            shift_amount: Amount to shift (positive = up)
            levels: Dict of group levels to update
            positions: Dict of group positions
            node_positions: Dict of node positions to update
        """
        if group_name not in levels:
            return
            
        old_y = levels[group_name]
        new_y = old_y + shift_amount
        levels[group_name] = new_y
        
        start_x, elements = positions[group_name]
        for i, elem in enumerate(elements):
            if elem in node_positions:
                old_node_id, old_x, _ = node_positions[elem]
                node_positions[elem] = (old_node_id, old_x, new_y)
    
    def _find_group_for_element(self, element, group_name_to_group):
        """Find which group an element belongs to."""
        for group_name, group in group_name_to_group.items():
            if 'elements' in group:
                if element in group['elements']:
                    return group_name
            elif group_name == element:
                return group_name
        return None
    
    def _resolve_text_overlaps(self, text_overlaps: List, positions: Dict, 
                               node_positions: Dict, group_name_to_group: Dict) -> bool:
        """
        Resolve text overlap conflicts by shifting groups.
        
        Args:
            text_overlaps: List of (name1, x1, y1, name2, x2, y2) tuples
            positions: Dict of group positions to update
            node_positions: Dict of node positions to update
            group_name_to_group: Dict mapping group names to specs
            
        Returns:
            True if any conflict was resolved
        """
        for name1, x1, y1, name2, x2, y2 in text_overlaps:
            group1 = self._find_group_for_element(name1, group_name_to_group)
            
            if group1 and group1 in positions:
                self._shift_group_horizontally(group1, 1.0, positions, node_positions)
                print(f"    → Shifted {group1} by +1.0")
                return True
        
        return False
    
    def _resolve_arrow_crossings(self, arrow_crossings: List, positions: Dict,
                                 node_positions: Dict, group_name_to_group: Dict) -> bool:
        """
        Resolve arrow crossing conflicts by increasing horizontal separation between groups.
        
        Strategy: Identify the two groups whose arrows are crossing, then push them
        further apart horizontally - move left group more left and right group more right.
        
        Args:
            arrow_crossings: List of (s1, t1, s2, t2, ix, iy) tuples
            positions: Dict of group positions to update
            node_positions: Dict of node positions to update
            group_name_to_group: Dict mapping group names to specs
            
        Returns:
            True if any conflict was resolved
        """
        if not arrow_crossings:
            return False
            
        # Take the first crossing to resolve
        s1, t1, s2, t2, ix, iy = arrow_crossings[0]
        
        # Find groups for both arrow sources
        group_s1 = self._find_group_for_element(s1, group_name_to_group)
        group_s2 = self._find_group_for_element(s2, group_name_to_group)
        
        # If both sources are in different groups, push them apart
        if (group_s1 and group_s2 and group_s1 != group_s2 and 
            group_s1 in positions and group_s2 in positions):
            x1 = positions[group_s1][0]
            x2 = positions[group_s2][0]
            
            # Push groups apart: left one goes more left, right one goes more right
            if x1 < x2:
                # group_s1 is to the left
                self._shift_group_horizontally(group_s1, -1.0, positions, node_positions)
                self._shift_group_horizontally(group_s2, +1.0, positions, node_positions)
                print(f"    → Increased spacing: shifted {group_s1} left and {group_s2} right")
            else:
                # group_s2 is to the left
                self._shift_group_horizontally(group_s2, -1.0, positions, node_positions)
                self._shift_group_horizontally(group_s1, +1.0, positions, node_positions)
                print(f"    → Increased spacing: shifted {group_s2} left and {group_s1} right")
            return True
        
        # Fallback: if only one group found or both in same group, shift right
        elif group_s1 and group_s1 in positions:
            self._shift_group_horizontally(group_s1, 1.5, positions, node_positions)
            print(f"    → Shifted {group_s1} right by 1.5 to avoid crossing")
            return True
        elif group_s2 and group_s2 in positions:
            self._shift_group_horizontally(group_s2, 1.5, positions, node_positions)
            print(f"    → Shifted {group_s2} right by 1.5 to avoid crossing")
            return True
        
        return False
    
    def _resolve_arrow_through_text(self, arrow_through_text: List, positions: Dict,
                                    node_positions: Dict, incoming: Dict,
                                    group_name_to_group: Dict) -> bool:
        """
        Resolve arrow-through-text conflicts by shifting groups or staggering elements.
        
        Args:
            arrow_through_text: List of (source, target, name, nx, ny) tuples
            positions: Dict of group positions to update
            node_positions: Dict of node positions to update
            incoming: Dict of incoming links
            group_name_to_group: Dict mapping group names to specs
            
        Returns:
            True if any conflict was resolved
        """
        for source, target, name, nx, ny in arrow_through_text:
            # Find which group the obstructing text belongs to
            obstructing_group = self._find_group_for_element(name, group_name_to_group)
            # Find which group the arrow source belongs to
            source_group = self._find_group_for_element(source, group_name_to_group)
            
            # If source and obstructing text are in the same group (siblings)
            # apply vertical staggering to individual elements
            if obstructing_group and source_group and obstructing_group == source_group:
                if obstructing_group in positions:
                    start_x, elements = positions[obstructing_group]
                    
                    # Store y-offsets in the group_name_to_group dict so LaTeX generator can use them
                    group_obj = group_name_to_group[obstructing_group]
                    if 'y_offsets' not in group_obj:
                        group_obj['y_offsets'] = {}
                    
                    # Apply vertical offsets to elements to create spacing
                    # Pattern: 0, +0.5, +1.0 for 3 elements (generous spacing to clear arrows)
                    applied_stagger = False
                    for i, elem in enumerate(elements):
                        offset = (i % 3) * 0.5  # 0, 0.5, 1.0 pattern
                        if offset > 0:
                            group_obj['y_offsets'][elem] = offset
                            applied_stagger = True
                            # Also update node_positions for conflict detection
                            if elem in node_positions:
                                node_id, x, y = node_positions[elem]
                                node_positions[elem] = (node_id, x, y + offset)
                    
                    if applied_stagger:
                        print(f"    → Applied vertical micro-staggering to {obstructing_group} elements (avoiding sibling arrows)")
                        return True
            
            # Otherwise, try horizontal shift
            elif obstructing_group and obstructing_group in positions:
                # Check if this group has incoming links (should be stable)
                if incoming.get(obstructing_group):
                    shift_amount = 1.5
                    message = f"    → Shifted {obstructing_group} horizontally by +{shift_amount} (avoiding horizontal arrow)"
                else:
                    shift_amount = 1.0
                    message = f"    → Shifted {obstructing_group} horizontally by +{shift_amount}"
                
                self._shift_group_horizontally(obstructing_group, shift_amount, positions, node_positions)
                print(message)
                return True
        
        return False
    
    def _attempt_conflict_resolution(self, text_overlaps, arrow_crossings, arrow_through_text,
                                     positions, node_positions, incoming, group_name_to_group):
        """
        Attempt to resolve conflicts by trying different resolution strategies.
        
        Args:
            text_overlaps: List of text overlap conflicts
            arrow_crossings: List of arrow crossing conflicts
            arrow_through_text: List of arrow-through-text conflicts
            positions: Dict of group positions to update
            node_positions: Dict of node positions to update
            incoming: Dict of incoming links
            group_name_to_group: Dict mapping group names to specs
            
        Returns:
            True if any conflict was resolved
        """
        # Only try to resolve text overlaps - these are always fixable
        # Skip arrow crossings - horizontal shifting often makes them worse
        # Skip arrow-through-text - these are acceptable geometric artifacts
        return self._resolve_text_overlaps(text_overlaps, positions, node_positions, group_name_to_group)
    
    def resolve_conflicts_iteratively(self, node_positions, levels, positions, 
                                     outgoing, incoming, group_name_to_group,
                                     element_to_group=None, group_center_nodes=None,
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
            element_to_group: Mapping of elements to groups
            group_center_nodes: Dict of center node IDs for underlined groups
            max_iterations: Maximum number of iterations
            
        Returns:
            Updated (node_positions, levels, positions)
        """
        print("\n=== Starting Conflict Resolution ===\n")
        
        for iteration in range(max_iterations):
            # Detect current conflicts (using enhanced detection with .south anchors)
            text_overlaps, arrow_crossings, arrow_through_text = self.check_arrow_intersections(
                node_positions, outgoing, return_conflicts=True,
                element_to_group=element_to_group, group_name_to_group=group_name_to_group,
                group_center_nodes=group_center_nodes, positions=positions, levels=levels
            )
            
            # Print status and check if done
            total_conflicts = self._print_conflict_status(
                iteration, text_overlaps, arrow_crossings, arrow_through_text
            )
            
            if total_conflicts == 0:
                print("✓ All conflicts resolved!\n")
                break
            
            # Try to resolve conflicts in order of priority
            resolved_any = self._attempt_conflict_resolution(
                text_overlaps, arrow_crossings, arrow_through_text,
                positions, node_positions, incoming, group_name_to_group
            )
            
            if not resolved_any:
                print(f"  ⚠ Could not resolve conflicts in iteration {iteration + 1}")
                break
            
            print()
        
        print("=== Conflict Resolution Complete ===")
        return node_positions, levels, positions
    
    def _apply_vertical_staggering(self, levels: Dict, positions: Dict, 
                                   node_positions: Dict, group_name_to_group: Dict,
                                   outgoing: Dict) -> bool:
        """
        Apply vertical staggering to groups on the same row to reduce conflicts.
        Groups with no outgoing links can be moved up slightly.
        
        Args:
            levels: Dict of group levels
            positions: Dict of group positions
            node_positions: Dict of node positions
            group_name_to_group: Dict mapping group names to specs
            outgoing: Dict of outgoing links
            
        Returns:
            True if any groups were staggered
        """
        # Group elements by their current level
        level_to_groups = {}
        for group_name, level in levels.items():
            if level not in level_to_groups:
                level_to_groups[level] = []
            level_to_groups[level].append(group_name)
        
        staggered = False
        
        # For each level with multiple groups, stagger some vertically
        for level, groups in level_to_groups.items():
            if len(groups) <= 2:  # Don't stagger if only 1-2 groups
                continue
            
            # Sort groups by x position for consistent staggering
            groups_with_x = [(g, positions[g][0]) for g in groups]
            groups_with_x.sort(key=lambda x: x[1])
            
            # Apply more aggressive staggering pattern
            for i, (group_name, _) in enumerate(groups_with_x):
                # Stagger in a wave pattern: 0, +0.4, +0.2, 0, +0.4, +0.2, ...
                if i % 3 == 1:
                    shift = 0.4
                elif i % 3 == 2:
                    shift = 0.2
                else:
                    shift = 0.0
                
                if shift > 0:
                    self._shift_group_vertically(group_name, shift, levels, positions, node_positions)
                    print(f"    → Staggered {group_name} up by {shift} to reduce crowding")
                    staggered = True
        
        return staggered
    
    def _separate_conflicted_groups(self, arrow_crossings: List, arrow_through_text: List,
                                    levels: Dict, positions: Dict, node_positions: Dict,
                                    group_name_to_group: Dict, outgoing: Dict) -> bool:
        """
        Move highly conflicted groups to separate rows to reduce conflicts.
        
        Args:
            arrow_crossings: List of arrow crossing conflicts
            arrow_through_text: List of arrow-through-text conflicts
            levels: Dict of group levels
            positions: Dict of group positions
            node_positions: Dict of node positions
            group_name_to_group: Dict mapping group names to specs
            outgoing: Dict of outgoing links
            
        Returns:
            True if any groups were moved
        """
        # Count conflicts per group
        conflict_counts = {}
        
        # Count arrow crossings
        for s1, t1, s2, t2, ix, iy in arrow_crossings:
            g1 = self._find_group_for_element(s1, group_name_to_group)
            g2 = self._find_group_for_element(s2, group_name_to_group)
            if g1:
                conflict_counts[g1] = conflict_counts.get(g1, 0) + 1
            if g2:
                conflict_counts[g2] = conflict_counts.get(g2, 0) + 1
        
        # Count arrow through text
        for source, target, name, nx, ny in arrow_through_text:
            g_source = self._find_group_for_element(source, group_name_to_group)
            g_name = self._find_group_for_element(name, group_name_to_group)
            if g_source:
                conflict_counts[g_source] = conflict_counts.get(g_source, 0) + 1
            if g_name:
                conflict_counts[g_name] = conflict_counts.get(g_name, 0) + 1
        
        if not conflict_counts:
            return False
        
        # Sort groups by conflict count (descending)
        sorted_groups = sorted(conflict_counts.items(), key=lambda x: x[1], reverse=True)
        
        moved = False
        moved_groups = set()
        
        # Move the most conflicted groups to completely separate rows
        for group_name, count in sorted_groups[:3]:  # Top 3 most conflicted
            if group_name in moved_groups:
                continue
                
            current_level = levels[group_name]
            
            # Move to a completely separate row (full row increment)
            # This creates more vertical space and reduces arrow crossings
            shift_amount = 1.0
            new_level = current_level + shift_amount
            
            self._shift_group_vertically(group_name, shift_amount, levels, positions, node_positions)
            print(f"    → Moved {group_name} to separate row (y={new_level:.1f}) to reduce {count} conflicts")
            moved = True
            moved_groups.add(group_name)
        
        return moved
    
    def _apply_horizontal_spreading(self, arrow_crossings: List, arrow_through_text: List,
                                    levels: Dict, positions: Dict, node_positions: Dict,
                                    group_name_to_group: Dict) -> bool:
        """
        Spread groups horizontally to reduce remaining conflicts.
        
        Args:
            arrow_crossings: List of arrow crossing conflicts
            arrow_through_text: List of arrow-through-text conflicts
            levels: Dict of group levels
            positions: Dict of group positions
            node_positions: Dict of node positions
            group_name_to_group: Dict mapping group names to specs
            
        Returns:
            True if any groups were spread
        """
        # Find groups involved in conflicts
        conflicted_groups = set()
        
        for s1, t1, s2, t2, ix, iy in arrow_crossings:
            g1 = self._find_group_for_element(s1, group_name_to_group)
            g2 = self._find_group_for_element(s2, group_name_to_group)
            if g1:
                conflicted_groups.add(g1)
            if g2:
                conflicted_groups.add(g2)
        
        for source, target, name, nx, ny in arrow_through_text:
            g_name = self._find_group_for_element(name, group_name_to_group)
            if g_name:
                conflicted_groups.add(g_name)
        
        if not conflicted_groups:
            return False
        
        # Group by level and spread horizontally
        level_groups = {}
        for g in conflicted_groups:
            if g in levels:
                level = levels[g]
                if level not in level_groups:
                    level_groups[level] = []
                level_groups[level].append(g)
        
        spread = False
        for level, groups in level_groups.items():
            if len(groups) > 1:
                # Sort by x position
                groups_with_x = [(g, positions[g][0]) for g in groups]
                groups_with_x.sort(key=lambda x: x[1])
                
                # Spread rightmost groups further right
                for i, (group_name, x) in enumerate(groups_with_x):
                    if i >= len(groups_with_x) // 2:  # Right half
                        shift = 3.0 * (i - len(groups_with_x) // 2 + 1)
                        self._shift_group_horizontally(group_name, shift, positions, node_positions)
                        print(f"    → Spread {group_name} right by {shift} to reduce conflicts")
                        spread = True
        
        return spread
    
    def _apply_aggressive_strategies(self, arrow_crossings, arrow_through_text, 
                                    levels, positions, node_positions, 
                                    group_name_to_group, outgoing):
        """
        Apply aggressive resolution strategies when simple shifting doesn't work.
        Tries vertical staggering, row separation, and horizontal spreading.
        """
        # Strategy 1: Vertical staggering
        self._apply_vertical_staggering(
            levels, positions, node_positions, group_name_to_group, outgoing
        )
        
        # Strategy 2: Row separation for highly conflicted groups
        if arrow_crossings or arrow_through_text:
            self._separate_conflicted_groups(
                arrow_crossings, arrow_through_text, levels, positions,
                node_positions, group_name_to_group, outgoing
            )
        
        # Strategy 3: Horizontal spreading
        if arrow_crossings or arrow_through_text:
            self._apply_horizontal_spreading(
                arrow_crossings, arrow_through_text, levels, positions,
                node_positions, group_name_to_group
            )
