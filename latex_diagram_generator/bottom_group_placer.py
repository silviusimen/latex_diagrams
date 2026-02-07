#!/usr/bin/env python3
"""Specialized logic for placing bottom groups in the layout."""

from typing import Dict, List, Set
from .group_positioner import GroupPositioner

# Import spacing constants
from .spacing_constants import WITHIN_GROUP_SPACING


class BottomGroupPlacer:
    """Handles placement of bottom groups with dependency awareness."""
    
    def __init__(self, group_name_to_group: Dict, positioner: GroupPositioner):
        """
        Initialize the bottom group placer.
        
        Args:
            group_name_to_group: Mapping of group names to group specs
            positioner: GroupPositioner instance for placing groups
        """
        self.group_name_to_group = group_name_to_group
        self.positioner = positioner
        self.WITHIN_GROUP_SPACING = positioner.WITHIN_GROUP_SPACING
    
    def place_target_groups(self, targets: Set[str], y_level: int, levels: Dict, 
                            positions: Dict, node_positions: Dict) -> None:
        """
        Place target groups centered at x=6.0.
        
        Args:
            targets: Set of target group names
            y_level: Y-coordinate for placement
            levels, positions, node_positions: Dicts to update
        """
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
                # Skip special symbols like '+' - they're visual separators, not nodes
                if elem not in ['+', '-', '|']:
                    node_positions[elem] = target_start + i * self.WITHIN_GROUP_SPACING
    
    def place_source_groups_above_targets(self, source_to_target: Dict, y_level: int,
                                           levels: Dict, positions: Dict, node_positions: Dict) -> None:
        """
        Place source groups centered above their target groups.
        
        Args:
            source_to_target: Mapping of source to target groups
            y_level: Y-coordinate for placement (sources go at y_level + 1)
            levels, positions, node_positions: Dicts to update
        """
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
                    # Skip special symbols like '+' - they're visual separators, not nodes
                    if elem not in ['+', '-', '|']:
                        node_positions[elem] = source_start + i * self.WITHIN_GROUP_SPACING
    
    def place_dependent_bottom_groups(self, source_to_target, group_names, y_level,
                                       levels, positions, node_positions,
                                       place_groups_on_row_func):
        """
        Place bottom groups that have dependencies among themselves.
        
        Args:
            source_to_target: Dict mapping source groups to target groups
            group_names: All bottom group names
            y_level: Starting y-level
            levels, positions, node_positions: Dicts to update
            place_groups_on_row_func: Function to place independent groups
            
        Returns:
            Maximum y-level used
        """
        targets = set(source_to_target.values())
        sources = set(source_to_target.keys())
        independent = [g for g in group_names if g not in sources and g not in targets]
        
        # Place targets at y_level (bottom)
        self.place_target_groups(targets, y_level, levels, positions, node_positions)
        
        # Place sources at y_level + 1 (one row above), centered above their targets
        self.place_source_groups_above_targets(source_to_target, y_level, levels, positions, node_positions)
        
        # Place independent groups at y_level with the targets
        if independent:
            place_groups_on_row_func(independent, y_level, levels, positions, 
                                      node_positions, center=True)
        
        # Return max y-level used (sources are at y_level + 1)
        return y_level + 1
    
    def place_bottom_groups_intelligently(self, group_names, y_level, levels, positions, 
                                           node_positions, source_to_target,
                                           place_groups_on_row_func):
        """
        Place bottom groups with special logic:
        - If one group points to another, place target at y_level, source at y_level + 1
        - Otherwise center all groups at y_level
        
        Args:
            group_names: List of bottom group names
            y_level: Starting y-level
            levels, positions, node_positions: Dicts to update
            source_to_target: Pre-computed dependency mapping
            place_groups_on_row_func: Function to place groups on a row
            
        Returns:
            Maximum y-level used
        """
        if not group_names:
            return y_level
        
        if source_to_target:
            # Place source-target pairs with vertical alignment
            return self.place_dependent_bottom_groups(
                source_to_target, group_names, y_level,
                levels, positions, node_positions, place_groups_on_row_func
            )
        else:
            # No dependencies among bottom groups, just center them
            place_groups_on_row_func(group_names, y_level, levels, positions, 
                                      node_positions, center=True)
            return y_level
