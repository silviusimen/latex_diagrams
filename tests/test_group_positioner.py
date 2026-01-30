#!/usr/bin/env python3
"""Unit tests for GroupPositioner."""

import unittest
from latex_diagram_generator.group_positioner import GroupPositioner


class TestGroupPositioner(unittest.TestCase):
    """Tests for GroupPositioner class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Basic test data structures
        self.group_name_to_group = {
            'Group1': {'elements': ['A', 'B']},
            'Group2': {'elements': ['C']},
            'Group3': {'elements': ['D', 'E', 'F']}
        }
        
        self.positioner = GroupPositioner(self.group_name_to_group, within_group_spacing=2.0)
    
    # Tests for calculate_group_width
    def test_calculate_group_width_single(self):
        """Test width of single element."""
        result = self.positioner.calculate_group_width(['A'])
        self.assertEqual(result, 0.0)
    
    def test_calculate_group_width_multiple(self):
        """Test width of multiple elements."""
        result = self.positioner.calculate_group_width(['A', 'B', 'C'])
        # (3-1) * 2.0 = 4.0
        self.assertEqual(result, 4.0)
    
    def test_calculate_group_width_two_elements(self):
        """Test width of two elements."""
        result = self.positioner.calculate_group_width(['A', 'B'])
        # (2-1) * 2.0 = 2.0
        self.assertEqual(result, 2.0)
    
    # Tests for calculate_group_widths
    def test_calculate_group_widths_single_element(self):
        """Test width calculation for single element groups."""
        group_name_to_group = {'Group1': {'elements': ['A']}}
        positioner = GroupPositioner(group_name_to_group, 2.0)
        
        result = positioner.calculate_group_widths(['Group1'])
        
        self.assertEqual(result, [0.0])
    
    def test_calculate_group_widths_multiple_elements(self):
        """Test width calculation for multi-element groups."""
        result = self.positioner.calculate_group_widths(['Group3'])
        
        # 3 elements: (3-1) * 2.0 = 4.0
        self.assertEqual(result, [4.0])
    
    def test_calculate_group_widths_mixed(self):
        """Test width calculation for mixed groups."""
        result = self.positioner.calculate_group_widths(['Group1', 'Group2', 'Group3'])
        
        # Group1: 2 elements = 2.0, Group2: 1 element = 0.0, Group3: 3 elements = 4.0
        self.assertEqual(result, [2.0, 0.0, 4.0])
    
    def test_calculate_group_widths_no_elements_key(self):
        """Test width for group without elements key."""
        group_name_to_group = {'Group1': {}}
        positioner = GroupPositioner(group_name_to_group, 2.0)
        
        result = positioner.calculate_group_widths(['Group1'])
        
        self.assertEqual(result, [0.0])
    
    # Tests for calculate_starting_x
    def test_calculate_starting_x_centered(self):
        """Test calculating centered starting position."""
        group_names = ['Group1']
        group_widths = [4.0]
        
        result = self.positioner.calculate_starting_x(group_names, group_widths, center=True)
        
        # total_width = 4.0, centered at 6.0: start = 6.0 - 4.0/2 = 4.0
        self.assertEqual(result, 4.0)
    
    def test_calculate_starting_x_not_centered(self):
        """Test calculating non-centered starting position."""
        result = self.positioner.calculate_starting_x([], [], center=False)
        
        self.assertEqual(result, 0.0)
    
    def test_calculate_starting_x_multiple_groups(self):
        """Test starting x with multiple groups."""
        group_names = ['G1', 'G2']
        group_widths = [2.0, 4.0]
        
        result = self.positioner.calculate_starting_x(group_names, group_widths, center=True)
        
        # total = 2.0 + 4.0 + 2.0 (spacing) = 8.0, start = 6.0 - 4.0 = 2.0
        self.assertEqual(result, 2.0)
    
    # Tests for place_group_at_position
    def test_place_group_at_position_basic(self):
        """Test placing a group at position."""
        levels = {}
        positions = {}
        node_positions = {}
        
        result = self.positioner.place_group_at_position(
            'Group1', 2.0, 0.0, 5, levels, positions, node_positions
        )
        
        self.assertEqual(levels['Group1'], 5)
        self.assertEqual(positions['Group1'], (0.0, ['A', 'B']))
        self.assertEqual(node_positions['A'], 0.0)
        self.assertEqual(node_positions['B'], 2.0)
        self.assertEqual(result, 4.0)  # 0.0 + 2.0 + 2.0
    
    def test_place_group_at_position_single_element(self):
        """Test placing single element group."""
        group_name_to_group = {'G': {'elements': ['X']}}
        positioner = GroupPositioner(group_name_to_group, 2.0)
        
        levels = {}
        positions = {}
        node_positions = {}
        
        result = positioner.place_group_at_position(
            'G', 0.0, 5.0, 3, levels, positions, node_positions
        )
        
        self.assertEqual(node_positions['X'], 5.0)
        self.assertEqual(result, 7.0)  # 5.0 + 0.0 + 2.0
    
    # Tests for adjust_position_for_collisions
    def test_adjust_position_no_collision(self):
        """Test position adjustment when no collision."""
        levels = {}
        positions = {}
        
        result = self.positioner.adjust_position_for_collisions(
            5.0, 2.0, 3, 'Group1', levels, positions
        )
        
        self.assertEqual(result, 5.0)
    
    def test_adjust_position_with_collision(self):
        """Test position adjustment with collision."""
        levels = {'Group2': 3}
        positions = {'Group2': (5.0, ['X', 'Y'])}  # Width 2.0, ends at 7.0
        
        result = self.positioner.adjust_position_for_collisions(
            6.0, 2.0, 3, 'Group1', levels, positions
        )
        
        # Should be shifted to 7.0 + 2.0 = 9.0
        self.assertEqual(result, 9.0)
    
    def test_adjust_position_different_level(self):
        """Test no adjustment for different y-levels."""
        levels = {'Group2': 5}  # Different level
        positions = {'Group2': (5.0, ['X'])}
        
        result = self.positioner.adjust_position_for_collisions(
            5.0, 2.0, 3, 'Group1', levels, positions
        )
        
        self.assertEqual(result, 5.0)
    
    def test_adjust_position_no_overlap(self):
        """Test no adjustment when groups don't overlap."""
        levels = {'Group2': 3}
        positions = {'Group2': (0.0, ['X'])}  # Ends at 0.0
        
        result = self.positioner.adjust_position_for_collisions(
            3.0, 2.0, 3, 'Group1', levels, positions
        )
        
        self.assertEqual(result, 3.0)
    
    # Tests for place_single_group_centered
    def test_place_single_group_centered(self):
        """Test placing a single group centered above its target."""
        levels = {}
        positions = {}
        node_positions = {}
        target_x = 5.0
        
        self.positioner.place_single_group_centered(
            'Group1', 3, target_x, levels, positions, node_positions
        )
        
        self.assertEqual(levels['Group1'], 3)
        self.assertIn('Group1', positions)


if __name__ == '__main__':
    unittest.main()
