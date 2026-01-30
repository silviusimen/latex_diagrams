#!/usr/bin/env python3
"""Unit tests for BottomGroupPlacer."""

import unittest
from latex_diagram_generator.bottom_group_placer import BottomGroupPlacer
from latex_diagram_generator.group_positioner import GroupPositioner


class TestBottomGroupPlacer(unittest.TestCase):
    """Tests for BottomGroupPlacer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Basic test data structures
        self.group_name_to_group = {
            'Group1': {'elements': ['A', 'B']},
            'Group2': {'elements': ['C']},
            'Group3': {'elements': ['D', 'E', 'F']}
        }
        
        self.positioner = GroupPositioner(self.group_name_to_group, 2.0)
        self.placer = BottomGroupPlacer(self.group_name_to_group, self.positioner)
    
    # Tests for place_target_groups
    def test_place_target_groups(self):
        """Test placing target groups centered."""
        levels = {}
        positions = {}
        node_positions = {}
        
        self.placer.place_target_groups(
            {'Group1'}, 3, levels, positions, node_positions
        )
        
        self.assertEqual(levels['Group1'], 3)
        self.assertIn('Group1', positions)
        # Group1 has 2 elements, should be centered around 6.0
        start_x, elements = positions['Group1']
        self.assertEqual(elements, ['A', 'B'])
    
    def test_place_target_groups_single_element(self):
        """Test placing single element target group."""
        levels = {}
        positions = {}
        node_positions = {}
        
        self.placer.place_target_groups(
            {'Group2'}, 3, levels, positions, node_positions
        )
        
        # Single element should be at 6.0
        start_x, elements = positions['Group2']
        self.assertEqual(start_x, 6.0)
    
    # Tests for place_source_groups_above_targets
    def test_place_source_groups_above_targets(self):
        """Test placing source groups above targets."""
        levels = {}
        positions = {'Group2': (6.0, ['C'])}
        node_positions = {}
        
        source_to_target = {'Group1': 'Group2'}
        
        self.placer.place_source_groups_above_targets(
            source_to_target, 3, levels, positions, node_positions
        )
        
        # Source should be at y_level + 1 = 4
        self.assertEqual(levels['Group1'], 4)
    
    def test_place_source_groups_above_targets_single_element(self):
        """Test placing single-element source group above target (line 79)."""
        levels = {}
        # Group2 needs to be placed first
        positions = {'Group1': (6.0, ['A', 'B'])}
        node_positions = {}
        
        # Use Group2 (single element) as source
        source_to_target = {'Group2': 'Group1'}
        
        self.placer.place_source_groups_above_targets(
            source_to_target, 3, levels, positions, node_positions
        )
        
        # Source should be placed at y_level + 1 = 4
        self.assertEqual(levels['Group2'], 4)
        self.assertIn('Group2', positions)
    
    # Tests for place_bottom_level
    def test_place_bottom_groups_with_independent_groups(self):
        """Test place_dependent_bottom_groups with independent groups (line 115)."""
        levels = {}
        positions = {}
        node_positions = {}
        groups_to_place = ['Group1', 'Group2', 'Group3']
        source_to_target = {}  # No links
        
        # Use a simple place_groups_on_row function
        def place_func(group_names, y_level, levels, positions, node_positions, center=False):
            for group_name in group_names:
                levels[group_name] = y_level
                positions[group_name] = (6.0, self.group_name_to_group[group_name]['elements'])
        
        level = 2
        max_y = self.placer.place_bottom_groups_intelligently(
            groups_to_place, level, levels, positions, node_positions,
            source_to_target, place_func
        )
        
        # All groups should be placed as independent
        self.assertEqual(len(levels), 3)
        self.assertEqual(levels['Group1'], level)
        self.assertEqual(levels['Group2'], level)
        self.assertEqual(levels['Group3'], level)
        self.assertEqual(max_y, level)


if __name__ == '__main__':
    unittest.main()
