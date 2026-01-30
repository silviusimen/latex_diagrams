#!/usr/bin/env python3
"""Layout engine for computing diagram layout."""

from typing import Dict, List, Tuple, Set
from collections import defaultdict


class LayoutEngine:
    """Handles layout computation for diagram elements."""
    
    def __init__(self, within_group_spacing: float = 2.0):
        """
        Initialize LayoutEngine.
        
        Args:
            within_group_spacing: Spacing between elements within a group
        """
        self.WITHIN_GROUP_SPACING = within_group_spacing
        self.group_name_to_group = None  # Set during compute_layout_bottom_up
        self.element_to_group = None
    
    def compute_layout_bottom_up(self, group_name_to_group, element_to_group, 
                                 outgoing, incoming) -> Tuple[Dict[str, int], Dict[str, Tuple[float, List[str]]]]:
        """
        Compute both levels and positions using bottom-up approach with integrated collision avoidance.
        
        Algorithm:
        1. Start from bottom (leaf nodes with no outgoing links)
        2. For each iteration, process groups that link to previously placed groups
        3. Order by destination positions left-to-right
        4. Place on new row with collision checking
        5. If row too crowded, move groups up based on priority (groups with inbound links first, from center)
        
        Args:
            group_name_to_group: Dictionary mapping group names to group objects
            element_to_group: Dictionary mapping element names to their containing group
            outgoing: Dictionary of outgoing links (element -> targets)
            incoming: Dictionary of incoming links (element -> sources)
            
        Returns:
            Tuple of (levels dict, positions dict)
        """
        self.group_name_to_group = group_name_to_group
        self.element_to_group = element_to_group
        
        all_groups = set(group_name_to_group.keys())
        
        levels = {}  # group_name -> y_level
        positions = {}  # group_name -> (start_x, elements)
        node_positions = {}  # elem -> x position
        
        placed_groups = set()
        current_y = 0
        
        # Find bottom groups (those with no outgoing links to other groups)
        bottom_groups = []
        for group_name in all_groups:
            group = group_name_to_group[group_name]
            has_outgoing = False
            
            if 'elements' in group:
                for elem in group['elements']:
                    if elem in outgoing:
                        target_list = outgoing[elem]
                        target = target_list[0] if isinstance(target_list, list) else target_list
                        target_group = element_to_group.get(target, target)
                        if target_group != group_name:
                            has_outgoing = True
                            break
            elif group_name in outgoing:
                target_list = outgoing[group_name]
                target = target_list[0] if isinstance(target_list, list) else target_list
                target_group = element_to_group.get(target, target)
                if target_group != group_name:
                    has_outgoing = True
            
            if not has_outgoing:
                bottom_groups.append(group_name)
        
        print(f"\n=== Bottom-Up Layout ===")
        print(f"Bottom groups: {bottom_groups}")
        
        # Place bottom groups with special handling for groups that point to each other
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
                
                group = group_name_to_group[group_name]
                links_to_placed = False
                
                if 'elements' in group:
                    for elem in group['elements']:
                        if elem in outgoing:
                            target_list = outgoing[elem]
                            target = target_list[0] if isinstance(target_list, list) else target_list
                            target_group = element_to_group.get(target, target)
                            if target_group in placed_groups:
                                links_to_placed = True
                                break
                elif group_name in outgoing:
                    target_list = outgoing[group_name]
                    target = target_list[0] if isinstance(target_list, list) else target_list
                    target_group = element_to_group.get(target, target)
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
                group = group_name_to_group[group_name]
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
                total_width = self.calculate_row_width(row_groups)
                
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
                            if self.calculate_row_width(test_keep) <= MAX_ROW_WIDTH:
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
    
    def calculate_row_width(self, group_names):
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
