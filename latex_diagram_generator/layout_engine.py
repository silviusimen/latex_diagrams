#!/usr/bin/env python3
"""Layout engine for computing diagram layout."""

from typing import Dict, List, Tuple, Set
from .dependency_analyzer import DependencyAnalyzer
from .group_positioner import GroupPositioner
from .bottom_group_placer import BottomGroupPlacer
from .row_placer import RowPlacer


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
        
        # Helper components (initialized when layout is computed)
        self.analyzer = None
        self.positioner = None
        self.bottom_placer = None
        self.row_placer = None
    
    def _initialize_layout(self, group_name_to_group, element_to_group):
        """
        Initialize layout data structures and helper components.
        
        Args:
            group_name_to_group: Dictionary mapping group names to group objects
            element_to_group: Dictionary mapping element names to their containing group
            
        Returns:
            Tuple of (all_groups, levels, positions, node_positions, placed_groups, current_y)
        """
        self.group_name_to_group = group_name_to_group
        self.element_to_group = element_to_group
        
        # Initialize helper components
        self.analyzer = DependencyAnalyzer(group_name_to_group, element_to_group)
        self.positioner = GroupPositioner(group_name_to_group, self.WITHIN_GROUP_SPACING)
        self.bottom_placer = BottomGroupPlacer(group_name_to_group, self.positioner)
        self.row_placer = RowPlacer(group_name_to_group, element_to_group, 
                                     self.positioner, self.analyzer)
        
        all_groups = set(group_name_to_group.keys())
        levels = {}  # group_name -> y_level
        positions = {}  # group_name -> (start_x, elements)
        node_positions = {}  # elem -> x position
        placed_groups = set()
        current_y = 0
        
        return all_groups, levels, positions, node_positions, placed_groups, current_y
    
    def _place_initial_bottom_groups(self, all_groups, outgoing, incoming, current_y,
                                    levels, positions, node_positions, placed_groups):
        """
        Find and place bottom groups (leaf nodes).
        
        Args:
            all_groups: Set of all group names
            outgoing, incoming: Link dictionaries
            current_y: Current y-level
            levels, positions, node_positions, placed_groups: Dicts to update
            
        Returns:
            Updated current_y (max y-level used)
        """
        bottom_groups = self.analyzer.find_bottom_groups(all_groups, outgoing)
        print(f"\n=== Bottom-Up Layout ===")
        print(f"Bottom groups: {bottom_groups}")
        
        # Find dependencies among bottom groups
        source_to_target = self.analyzer.find_bottom_group_dependencies(bottom_groups, outgoing)
        
        # Place bottom groups intelligently
        max_y_used = self.bottom_placer.place_bottom_groups_intelligently(
            bottom_groups, current_y, levels, positions, node_positions, 
            source_to_target, self.row_placer.place_groups_on_row
        )
        placed_groups.update(bottom_groups)
        return max_y_used
    
    def _process_next_layer(self, iteration, all_groups, placed_groups, outgoing, incoming,
                           current_y, levels, positions, node_positions):
        """
        Process next layer of groups in bottom-up traversal.
        
        Args:
            iteration: Current iteration number
            all_groups: Set of all group names
            placed_groups: Set of already placed groups
            outgoing, incoming: Link dictionaries
            current_y: Current y-level
            levels, positions, node_positions: Dicts to update
            
        Returns:
            List of groups placed in this iteration
        """
        # Find groups linking to placed groups
        next_groups = self.analyzer.find_next_layer_groups(all_groups, placed_groups, outgoing)
        
        if not next_groups:
            # No more groups link to placed groups, place remaining
            next_groups = [g for g in all_groups if g not in placed_groups]
        
        if not next_groups:
            return []
        
        print(f"\nIteration {iteration}: Processing {len(next_groups)} groups")
        
        # Sort groups by destination position and place them
        sorted_groups = self.analyzer.sort_groups_by_destination(next_groups, outgoing, node_positions)
        self.row_placer.place_groups_on_row_with_overflow(
            sorted_groups, current_y, levels, positions, node_positions, 
            incoming, outgoing, placed_groups
        )
        
        return sorted_groups
    
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
        # Initialize data structures
        all_groups, levels, positions, node_positions, placed_groups, current_y = \
            self._initialize_layout(group_name_to_group, element_to_group)
        
        # Find and place bottom groups
        current_y = self._place_initial_bottom_groups(
            all_groups, outgoing, incoming, current_y,
            levels, positions, node_positions, placed_groups
        )
        
        # Iterate upward through remaining layers
        iteration = 0
        while len(placed_groups) < len(all_groups):
            iteration += 1
            current_y += 1
            
            sorted_groups = self._process_next_layer(
                iteration, all_groups, placed_groups, outgoing, incoming,
                current_y, levels, positions, node_positions
            )
            
            if not sorted_groups:
                break
            
            placed_groups.update(sorted_groups)
        
        print(f"\n=== Layout Complete: {len(placed_groups)} groups placed ===")
        return levels, positions

