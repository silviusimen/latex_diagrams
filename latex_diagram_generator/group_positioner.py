#!/usr/bin/env python3
"""Group positioning and collision detection."""

from typing import Dict, List


class GroupPositioner:
    """Handles individual group positioning and collision detection."""

    def place_group_at(self, group_name: str, x: float, y_level: int, levels: Dict, positions: Dict, node_positions: Dict):
        """Place a group at a specific x, y position and update node_positions."""
        group = self.group_name_to_group[group_name]
        elements = group.get('elements', [group_name])
        levels[group_name] = y_level
        positions[group_name] = (x, elements)
        for i, elem in enumerate(elements):
            if elem not in ['+', '-', '|']:
                node_positions[elem] = (elem, x + i * self.WITHIN_GROUP_SPACING, y_level)

    def shift_group_horizontally(self, group_name: str, shift: float, positions: Dict, node_positions: Dict):
        """Shift a group and its elements horizontally by shift units."""
        if group_name not in positions:
            return
        x, elements = positions[group_name]
        new_x = x + shift
        positions[group_name] = (new_x, elements)
        for i, elem in enumerate(elements):
            if elem in node_positions:
                node_id, old_x, y = node_positions[elem]
                node_positions[elem] = (node_id, old_x + shift, y)
    
    def __init__(self, group_name_to_group: Dict, within_group_spacing: float = 2.0, between_group_spacing: float = 2.0):
        """
        Initialize the group positioner.
        
        Args:
            group_name_to_group: Mapping of group names to group specs
            within_group_spacing: Spacing between elements within a group
            between_group_spacing: Spacing between adjacent groups
        """
        self.group_name_to_group = group_name_to_group
        self.WITHIN_GROUP_SPACING = within_group_spacing
        self.BETWEEN_GROUP_SPACING = between_group_spacing
        self.MAX_X_POSITION = 40.0  # Maximum horizontal position allowed
    
    def calculate_group_width(self, elements: List[str]) -> float:
        """
        Calculate the width of a group based on its elements.
        
        Args:
            elements: List of element names
            
        Returns:
            Width in coordinate units
        """
        if len(elements) > 1:
            return (len(elements) - 1) * self.WITHIN_GROUP_SPACING
        return 0.0
    
    def calculate_group_widths(self, group_names: List[str]) -> List[float]:
        """
        Calculate widths for a list of groups.
        
        Args:
            group_names: List of group names
            
        Returns:
            List of group widths
        """
        group_widths = []
        for group_name in group_names:
            group = self.group_name_to_group[group_name]
            if 'elements' in group:
                num_elements = len(group['elements'])
                width = (num_elements - 1) * self.WITHIN_GROUP_SPACING if num_elements > 1 else 0
            else:
                width = 0
            group_widths.append(width)
        return group_widths
    
    def calculate_starting_x(self, group_names: List[str], group_widths: List[float], center: bool) -> float:
        """
        Calculate starting x position for a row of groups.
        
        Args:
            group_names: List of group names
            group_widths: List of corresponding group widths
            center: If True, center around x=6.0
            
        Returns:
            Starting x-coordinate
        """
        if center:
            total_width = sum(group_widths) + (len(group_names) - 1) * self.BETWEEN_GROUP_SPACING
            return 6.0 - total_width / 2.0
        return 0.0
    
    def place_group_at_position(self, group_name: str, width: float, current_x: float,
                                 y_level: int, levels: Dict, positions: Dict, node_positions: Dict) -> float:
        """
        Place a single group at specified position and update data structures.
        
        Args:
            group_name: Name of group to place
            width: Width of the group
            current_x: Current x-coordinate
            y_level: Y-coordinate
            levels, positions, node_positions: Dicts to update
            
        Returns:
            Next x-coordinate for subsequent groups
        """
        group = self.group_name_to_group[group_name]
        elements = group.get('elements', [group_name])
        
        levels[group_name] = y_level
        positions[group_name] = (current_x, elements)
        
        for i, elem in enumerate(elements):
            # Skip special symbols like '+' - they're visual separators, not nodes
            if elem not in ['+', '-', '|']:
                # Always assign as (elem, x, y_level)
                node_positions[elem] = (elem, current_x + i * self.WITHIN_GROUP_SPACING, y_level)
        
        return current_x + width + self.BETWEEN_GROUP_SPACING  # Move to next group position
    
    def adjust_position_for_collisions(self, start_x: float, width: float, y_level: int,
                                        group_name: str, levels: Dict, positions: Dict) -> float:
        """
        Adjust group position to avoid collisions with already placed groups.
        
        Args:
            start_x: Desired starting x position
            width: Width of the group
            y_level: Y-level of placement
            group_name: Name of group being placed
            levels: Dict of group levels
            positions: Dict of group positions
            
        Returns:
            Adjusted starting x position
        """
        REQUIRED_SPACING = 2.0
        adjusted_x = start_x
        
        for other_group in levels:
            if levels[other_group] == y_level and other_group != group_name:
                other_start, other_elements = positions[other_group]
                other_width = self.calculate_group_width(other_elements)
                other_end = other_start + other_width
                my_end = adjusted_x + width
                
                # Check for overlap (need REQUIRED_SPACING between groups)
                if not (my_end + REQUIRED_SPACING < other_start or adjusted_x > other_end + REQUIRED_SPACING):
                    # Overlap detected! Shift right
                    adjusted_x = other_end + REQUIRED_SPACING
        
        return adjusted_x
    
    def place_single_group_centered(self, group_name: str, y_level: int, target_x: float,
                                     levels: Dict, positions: Dict, node_positions: Dict):
        """
        Place a single group centered above its target with collision avoidance.
        
        Args:
            group_name: Name of group to place
            y_level: Y-level for placement
            target_x: Target x position to center on
            levels, positions, node_positions: Dicts to update
        """
        group = self.group_name_to_group[group_name]
        elements = group.get('elements', [group_name])
        
        # Get target position and calculate group width
        width = self.calculate_group_width(elements)
        
        # Center above target
        start_x = target_x - width / 2.0
        
        # Adjust for collisions
        start_x = self.adjust_position_for_collisions(
            start_x, width, y_level, group_name, levels, positions
        )
        
        # Update positions
        levels[group_name] = y_level
        positions[group_name] = (start_x, elements)
        
        for i, elem in enumerate(elements):
            # Skip special symbols like '+' - they're visual separators, not nodes
            if elem not in ['+', '-', '|']:
                node_positions[elem] = (elem, start_x + i * self.WITHIN_GROUP_SPACING, y_level)
