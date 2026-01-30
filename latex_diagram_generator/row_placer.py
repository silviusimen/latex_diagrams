#!/usr/bin/env python3
"""Row placement with overflow and splitting logic."""

from typing import Dict, List, Tuple
from .group_positioner import GroupPositioner
from .dependency_analyzer import DependencyAnalyzer


class RowPlacer:
    """Handles row placement with overflow/splitting logic."""
    
    def __init__(self, group_name_to_group: Dict, element_to_group: Dict,
                 positioner: GroupPositioner, analyzer: DependencyAnalyzer):
        """
        Initialize the row placer.
        
        Args:
            group_name_to_group: Mapping of group names to group specs
            element_to_group: Mapping of element names to their containing group
            positioner: GroupPositioner instance
            analyzer: DependencyAnalyzer instance
        """
        self.group_name_to_group = group_name_to_group
        self.element_to_group = element_to_group
        self.positioner = positioner
        self.analyzer = analyzer
        self.WITHIN_GROUP_SPACING = positioner.WITHIN_GROUP_SPACING
    
    def place_groups_on_row(self, group_names, y_level, levels, positions, node_positions, center=False):
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
        
        # Calculate widths for all groups
        group_widths = self.positioner.calculate_group_widths(group_names)
        
        # Calculate starting x position
        current_x = self.positioner.calculate_starting_x(group_names, group_widths, center)
        
        # Place each group
        for group_name, width in zip(group_names, group_widths):
            current_x = self.positioner.place_group_at_position(
                group_name, width, current_x, y_level, levels, positions, node_positions
            )
    
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
    
    def classify_groups_by_incoming(self, group_names: List[str], incoming: Dict) -> Tuple[List[str], List[str]]:
        """
        Classify groups by whether they have inbound links.
        
        Args:
            group_names: List of group names to classify
            incoming: Dictionary of incoming links
            
        Returns:
            Tuple of (groups_with_incoming, groups_without_incoming)
        """
        groups_with_incoming = []
        groups_without_incoming = []
        
        for group_name in group_names:
            if self._group_has_incoming(group_name, incoming):
                groups_with_incoming.append(group_name)
            else:
                groups_without_incoming.append(group_name)
        
        return groups_with_incoming, groups_without_incoming
    
    def _group_has_incoming(self, group_name: str, incoming: Dict) -> bool:
        """
        Check if a group has any incoming links.
        
        Args:
            group_name: Name of group to check
            incoming: Dictionary of incoming links
            
        Returns:
            True if group has incoming links
        """
        group = self.group_name_to_group[group_name]
        
        if 'elements' in group:
            for elem in group['elements']:
                if elem in incoming:
                    return True
        elif group_name in incoming:
            return True
        
        return False
    
    def select_groups_by_priority(self, row_groups: List[str], groups_with_incoming: List[str],
                                   groups_without_incoming: List[str]) -> List[str]:
        """
        Select groups to move based on priority (prefer groups with incoming links).
        
        Args:
            row_groups: Groups currently on the row
            groups_with_incoming: Groups that have incoming links (priority)
            groups_without_incoming: Groups without incoming links
            
        Returns:
            List of groups to consider for moving
        """
        groups_to_move = [g for g in row_groups if g in groups_with_incoming]
        if not groups_to_move:
            groups_to_move = [g for g in row_groups if g in groups_without_incoming]
        return groups_to_move
    
    def sort_groups_by_distance_from_center(self, groups_to_move: List[str], 
                                             outgoing: Dict, node_positions: Dict) -> List[str]:
        """
        Sort groups by their distance from center (x=6.0).
        
        Args:
            groups_to_move: Groups to sort
            outgoing: Dictionary of outgoing links
            node_positions: Current node positions
            
        Returns:
            List of groups sorted by distance from center
        """
        center_x = 6.0
        groups_with_target_x = []
        for g in groups_to_move:
            target_x = self._get_group_target_x(g, outgoing, node_positions)
            groups_with_target_x.append((g, abs(target_x - center_x)))
        
        # Sort by distance from center
        groups_with_target_x.sort(key=lambda x: x[1])
        return [g for g, _ in groups_with_target_x]
    
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
    
    def move_groups_until_fit(self, sorted_groups: List[str], row_groups: List[str],
                              max_width: float) -> Tuple[List[str], List[str]]:
        """
        Move groups to next row until remaining groups fit in max width.
        
        Args:
            sorted_groups: Groups sorted by priority
            row_groups: All groups on the row
            max_width: Maximum allowed row width
            
        Returns:
            Tuple of (keep_on_row, move_to_next)
        """
        move_to_next = []
        keep_on_row = []
        
        for g in sorted_groups:
            move_to_next.append(g)
            test_keep = [x for x in row_groups if x not in move_to_next]
            if self.calculate_row_width(test_keep) <= max_width:
                keep_on_row = test_keep
                break
        
        return keep_on_row, move_to_next
    
    def split_overcrowded_row(self, row_groups: List[str], groups_with_incoming: List[str],
                               groups_without_incoming: List[str], outgoing: Dict,
                               node_positions: Dict, max_width: float) -> Tuple[List[str], List[str]]:
        """
        Split an overcrowded row into keep and move groups.
        
        Args:
            row_groups: Groups currently on the row
            groups_with_incoming: Groups that have incoming links (priority)
            groups_without_incoming: Groups without incoming links
            outgoing: Dictionary of outgoing links
            node_positions: Current node positions
            max_width: Maximum allowed row width
            
        Returns:
            Tuple of (keep_on_row, move_to_next)
        """
        # Select groups to move based on priority
        groups_to_move = self.select_groups_by_priority(
            row_groups, groups_with_incoming, groups_without_incoming
        )
        
        if groups_to_move:
            # Sort by distance from center
            sorted_groups = self.sort_groups_by_distance_from_center(
                groups_to_move, outgoing, node_positions
            )
            
            # Move groups until remaining fit
            keep_on_row, move_to_next = self.move_groups_until_fit(
                sorted_groups, row_groups, max_width
            )
            
            if not keep_on_row:
                # Still too wide, split in half as fallback
                mid = len(row_groups) // 2
                keep_on_row = row_groups[:mid]
                move_to_next = row_groups[mid:]
        else:
            # No prioritized groups, split in half
            mid = len(row_groups) // 2
            keep_on_row = row_groups[:mid]
            move_to_next = row_groups[mid:]
        
        return keep_on_row, move_to_next
    
    def split_rows_until_fit(self, rows, groups_with_incoming, groups_without_incoming,
                             outgoing, node_positions, max_row_width, start_y):
        """
        Split rows until all fit within maximum width.
        
        Args:
            rows: List of row groups
            groups_with_incoming, groups_without_incoming: Classified groups
            outgoing: Dictionary of outgoing links
            node_positions: Current node positions
            max_row_width: Maximum allowed row width
            start_y: Starting y-level
            
        Returns:
            List of rows that fit within width constraints
        """
        while True:
            all_fit = True
            
            for row_idx, row_groups in enumerate(rows):
                if not row_groups:
                    continue
                
                total_width = self.calculate_row_width(row_groups)
                
                if total_width > max_row_width:
                    all_fit = False
                    print(f"  Row {start_y + row_idx} too wide ({total_width:.1f} > {max_row_width}), splitting...")
                    
                    keep_on_row, move_to_next = self.split_overcrowded_row(
                        row_groups, groups_with_incoming, groups_without_incoming,
                        outgoing, node_positions, max_row_width
                    )
                    
                    rows[row_idx] = keep_on_row
                    if row_idx + 1 < len(rows):
                        rows[row_idx + 1] = move_to_next + rows[row_idx + 1]
                    else:
                        rows.append(move_to_next)
                    break
            
            if all_fit:
                break
        
        return rows
    
    def place_split_rows(self, rows, start_y, levels, positions, node_positions, outgoing):
        """
        Place groups on their assigned rows.
        
        Args:
            rows: List of row groups to place
            start_y: Starting y-level
            levels, positions, node_positions: Dicts to update
            outgoing: Dictionary of outgoing links
        """
        for row_idx, row_groups in enumerate(rows):
            if row_groups:
                y = start_y + row_idx
                self.place_groups_on_row_centered_by_target(
                    row_groups, y, levels, positions, node_positions, outgoing
                )
                print(f"  Placed {len(row_groups)} groups on row {y}: {row_groups}")
    
    def place_groups_on_row_with_overflow(self, group_names, start_y, levels, positions, 
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
        
        # Classify groups by incoming links
        groups_with_incoming, groups_without_incoming = self.classify_groups_by_incoming(
            group_names, incoming
        )
        
        # Try to fit all groups, splitting rows as needed
        rows = [group_names]
        rows = self.split_rows_until_fit(
            rows, groups_with_incoming, groups_without_incoming,
            outgoing, node_positions, MAX_ROW_WIDTH, start_y
        )
        
        # Place groups on their assigned rows
        self.place_split_rows(rows, start_y, levels, positions, node_positions, outgoing)
        
        return True
    
    def place_groups_on_row_centered_by_target(self, group_names, y_level, levels, 
                                                 positions, node_positions, outgoing):
        """Place groups on a row, each centered above its target."""
        for group_name in group_names:
            target_x = self._get_group_target_x(group_name, outgoing, node_positions)
            self.positioner.place_single_group_centered(
                group_name, y_level, target_x, levels, positions, node_positions
            )
