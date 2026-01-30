#!/usr/bin/env python3
"""Dependency analysis for diagram layout."""

from typing import Dict, List, Set


class DependencyAnalyzer:
    """Analyzes dependency relationships between groups."""
    
    def __init__(self, group_name_to_group: Dict, element_to_group: Dict):
        """
        Initialize the dependency analyzer.
        
        Args:
            group_name_to_group: Mapping of group names to group specs
            element_to_group: Mapping of element names to their containing group
        """
        self.group_name_to_group = group_name_to_group
        self.element_to_group = element_to_group
    
    def has_outgoing_to_other_group(self, group_name: str, outgoing: Dict) -> bool:
        """
        Check if a group has outgoing links to other groups.
        
        Args:
            group_name: Name of group to check
            outgoing: Dictionary of outgoing links
            
        Returns:
            True if group has outgoing links to other groups
        """
        group = self.group_name_to_group[group_name]
        
        if 'elements' in group:
            for elem in group['elements']:
                if elem in outgoing:
                    target_list = outgoing[elem]
                    target = target_list[0] if isinstance(target_list, list) else target_list
                    target_group = self.element_to_group.get(target, target)
                    if target_group != group_name:
                        return True
        elif group_name in outgoing:
            target_list = outgoing[group_name]
            target = target_list[0] if isinstance(target_list, list) else target_list
            target_group = self.element_to_group.get(target, target)
            if target_group != group_name:
                return True
        
        return False
    
    def find_bottom_groups(self, all_groups: Set[str], outgoing: Dict) -> List[str]:
        """
        Find groups with no outgoing links to other groups (leaf nodes).
        
        Args:
            all_groups: Set of all group names
            outgoing: Dictionary of outgoing links
            
        Returns:
            List of group names with no outgoing links
        """
        bottom_groups = []
        for group_name in all_groups:
            if not self.has_outgoing_to_other_group(group_name, outgoing):
                bottom_groups.append(group_name)
        
        return bottom_groups
    
    def get_group_target(self, group_name: str, outgoing: Dict) -> str:
        """
        Get the target group for a given group.
        
        Args:
            group_name: Name of group
            outgoing: Dictionary of outgoing links
            
        Returns:
            Target group name, or None if no target
        """
        group = self.group_name_to_group[group_name]
        
        if 'elements' in group:
            for elem in group['elements']:
                if elem in outgoing:
                    target_list = outgoing[elem]
                    target = target_list[0] if isinstance(target_list, list) else target_list
                    return self.element_to_group.get(target, target)
        elif group_name in outgoing:
            target_list = outgoing[group_name]
            target = target_list[0] if isinstance(target_list, list) else target_list
            return self.element_to_group.get(target, target)
        
        return None
    
    def group_links_to_placed(self, group_name: str, placed_groups: Set[str], outgoing: Dict) -> bool:
        """
        Check if a group links to any already-placed groups.
        
        Args:
            group_name: Name of group to check
            placed_groups: Set of already placed groups
            outgoing: Dictionary of outgoing links
            
        Returns:
            True if group links to placed groups
        """
        target_group = self.get_group_target(group_name, outgoing)
        return target_group is not None and target_group in placed_groups
    
    def find_next_layer_groups(self, all_groups: Set[str], placed_groups: Set[str], 
                                outgoing: Dict) -> List[str]:
        """
        Find groups that link to already-placed groups.
        
        Args:
            all_groups: Set of all group names
            placed_groups: Set of already placed group names
            outgoing: Dictionary of outgoing links
            
        Returns:
            List of group names linking to placed groups
        """
        next_groups = []
        for group_name in all_groups:
            if group_name not in placed_groups:
                if self.group_links_to_placed(group_name, placed_groups, outgoing):
                    next_groups.append(group_name)
        
        return next_groups
    
    def get_group_destination_x(self, group_name: str, outgoing: Dict, node_positions: Dict) -> float:
        """
        Get the destination x-position for a group.
        
        Args:
            group_name: Name of the group
            outgoing: Dictionary of outgoing links
            node_positions: Dictionary of element positions
            
        Returns:
            Destination x-position, or 999 if not found
        """
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
        
        return 999  # Default for groups with no destination
    
    def sort_groups_by_destination(self, groups: List[str], outgoing: Dict, 
                                    node_positions: Dict) -> List[str]:
        """
        Sort groups by their destination x-positions (left to right).
        
        Args:
            groups: List of group names to sort
            outgoing: Dictionary of outgoing links
            node_positions: Dictionary of element positions
            
        Returns:
            Sorted list of group names
        """
        groups_with_dest = [
            (group_name, self.get_group_destination_x(group_name, outgoing, node_positions))
            for group_name in groups
        ]
        
        # Sort by destination x position
        groups_with_dest.sort(key=lambda x: (x[1], x[0]))
        return [g[0] for g in groups_with_dest]
    
    def find_group_target_in_set(self, group_name: str, group_names: List[str],
                                  outgoing: Dict) -> str:
        """
        Find target group for a group if it exists in the given set.
        
        Args:
            group_name: Source group name
            group_names: Set of valid target group names
            outgoing: Dictionary of outgoing links
            
        Returns:
            Target group name if found in group_names, else None
        """
        group = self.group_name_to_group[group_name]
        original_name = group.get('name', group_name)
        
        # Check if the original group name points to another group
        if original_name in outgoing:
            target = self._get_target_from_list(outgoing[original_name])
            target_group = self.element_to_group.get(target, target)
            if target_group in group_names:
                return target_group
        
        # Check if first element points to another group
        if 'elements' in group:
            first_elem = group['elements'][0]
            if first_elem in outgoing:
                target = self._get_target_from_list(outgoing[first_elem])
                target_group = self.element_to_group.get(target, target)
                if target_group in group_names:
                    return target_group
        
        return None
    
    def find_bottom_group_dependencies(self, group_names: List[str], outgoing: Dict) -> Dict[str, str]:
        """
        Find dependencies among bottom groups (groups pointing to each other).
        
        Args:
            group_names: List of bottom group names
            outgoing: Dictionary of outgoing links
            
        Returns:
            Dictionary mapping source group to target group
        """
        source_to_target = {}
        for group_name in group_names:
            target_group = self.find_group_target_in_set(group_name, group_names, outgoing)
            if target_group:
                source_to_target[group_name] = target_group
        
        return source_to_target
    
    def _get_target_from_list(self, target_list):
        """
        Extract single target from target list (handles both list and single value).
        
        Args:
            target_list: Either a list of targets or a single target
            
        Returns:
            Single target value
        """
        return target_list[0] if isinstance(target_list, list) else target_list
