#!/usr/bin/env python3
"""Unit tests for RowPlacer."""

import unittest
from latex_diagram_generator.row_placer import RowPlacer
from latex_diagram_generator.group_positioner import GroupPositioner
from latex_diagram_generator.dependency_analyzer import DependencyAnalyzer


class TestRowPlacer(unittest.TestCase):
    """Tests for RowPlacer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Basic test data structures
        self.group_name_to_group = {
            'Group1': {'elements': ['A', 'B']},
            'Group2': {'elements': ['C']},
            'Group3': {'elements': ['D', 'E', 'F']}
        }
        self.element_to_group = {
            'A': 'Group1', 'B': 'Group1',
            'C': 'Group2',
            'D': 'Group3', 'E': 'Group3', 'F': 'Group3'
        }
        
        self.positioner = GroupPositioner(self.group_name_to_group, 2.0)
        self.analyzer = DependencyAnalyzer(self.group_name_to_group, self.element_to_group)
        self.row_placer = RowPlacer(
            self.group_name_to_group,
            self.element_to_group,
            self.positioner,
            self.analyzer
        )
    
    # Tests for _group_has_incoming
    def test_group_has_incoming_true(self):
        """Test detecting incoming links."""
        incoming = {'A': ['X']}
        result = self.row_placer._group_has_incoming('Group1', incoming)
        self.assertTrue(result)
    
    def test_group_has_incoming_false(self):
        """Test detecting no incoming links."""
        incoming = {}
        result = self.row_placer._group_has_incoming('Group1', incoming)
        self.assertFalse(result)
    
    def test_group_has_incoming_group_level(self):
        """Test incoming at group level."""
        group_name_to_group = {'Group1': {'name': 'Group1'}}
        element_to_group = {}
        positioner = GroupPositioner(group_name_to_group, 2.0)
        analyzer = DependencyAnalyzer(group_name_to_group, element_to_group)
        row_placer = RowPlacer(group_name_to_group, element_to_group, positioner, analyzer)
        
        incoming = {'Group1': ['X']}
        result = row_placer._group_has_incoming('Group1', incoming)
        self.assertTrue(result)
    
    # Tests for classify_groups_by_incoming
    def test_classify_groups_by_incoming_mixed(self):
        """Test classifying groups by incoming links."""
        incoming = {'A': ['X']}  # Group1 has incoming
        
        with_inc, without_inc = self.row_placer.classify_groups_by_incoming(
            ['Group1', 'Group2'], incoming
        )
        
        self.assertIn('Group1', with_inc)
        self.assertIn('Group2', without_inc)
    
    def test_classify_groups_by_incoming_all_with(self):
        """Test when all groups have incoming."""
        incoming = {'A': ['X'], 'C': ['Y']}
        
        with_inc, without_inc = self.row_placer.classify_groups_by_incoming(
            ['Group1', 'Group2'], incoming
        )
        
        self.assertEqual(len(with_inc), 2)
        self.assertEqual(len(without_inc), 0)
    
    def test_classify_groups_by_incoming_all_without(self):
        """Test when no groups have incoming."""
        incoming = {}
        
        with_inc, without_inc = self.row_placer.classify_groups_by_incoming(
            ['Group1', 'Group2'], incoming
        )
        
        self.assertEqual(len(with_inc), 0)
        self.assertEqual(len(without_inc), 2)
    
    # Tests for calculate_row_width
    def test_calculate_row_width_empty(self):
        """Test row width for empty group list."""
        result = self.row_placer.calculate_row_width([])
        self.assertEqual(result, 0.0)
    
    def test_calculate_row_width_single_group(self):
        """Test row width for single group."""
        result = self.row_placer.calculate_row_width(['Group1'])
        # Group1 has 2 elements: width = 2.0, no inter-group spacing
        self.assertEqual(result, 2.0)
    
    def test_calculate_row_width_multiple_groups(self):
        """Test row width for multiple groups."""
        result = self.row_placer.calculate_row_width(['Group1', 'Group2', 'Group3'])
        # Group1: 2.0, Group2: 0.0, Group3: 4.0, spacing: 2*2.0 = 4.0
        # Total: 2.0 + 0.0 + 4.0 + 4.0 = 10.0
        self.assertEqual(result, 10.0)
    
    # Tests for _get_group_target_x
    def test_get_group_target_x_with_position(self):
        """Test getting target x position."""
        outgoing = {'A': 'X'}
        node_positions = {'X': 8.5}
        
        result = self.row_placer._get_group_target_x('Group1', outgoing, node_positions)
        
        self.assertEqual(result, 8.5)
    
    def test_get_group_target_x_default(self):
        """Test getting default center position."""
        outgoing = {}
        node_positions = {}
        
        result = self.row_placer._get_group_target_x('Group1', outgoing, node_positions)
        
        self.assertEqual(result, 6.0)
    
    def test_get_group_target_x_no_position(self):
        """Test when target exists but has no position."""
        outgoing = {'A': 'X'}
        node_positions = {}
        
        result = self.row_placer._get_group_target_x('Group1', outgoing, node_positions)
        
        self.assertEqual(result, 6.0)
    
    # Tests for select_groups_by_priority
    def test_select_groups_by_priority_with_incoming(self):
        """Test selecting groups with priority for those with incoming."""
        row_groups = ['Group1', 'Group2']
        groups_with_incoming = ['Group1']
        groups_without_incoming = ['Group2']
        
        result = self.row_placer.select_groups_by_priority(
            row_groups, groups_with_incoming, groups_without_incoming
        )
        
        # Should return groups with incoming
        self.assertEqual(result, ['Group1'])
    
    def test_select_groups_by_priority_without_incoming(self):
        """Test selecting groups when none have incoming."""
        row_groups = ['Group1', 'Group2']
        groups_with_incoming = []
        groups_without_incoming = ['Group1', 'Group2']
        
        result = self.row_placer.select_groups_by_priority(
            row_groups, groups_with_incoming, groups_without_incoming
        )
        
        # Should return all groups without incoming
        self.assertEqual(len(result), 2)
    
    # Tests for sort_groups_by_distance_from_center
    def test_sort_groups_by_distance_from_center(self):
        """Test sorting groups by distance from center."""
        element_to_group = {
            'A': 'Group1', 'B': 'Group1',
            'C': 'Group2',
            'X': 'GroupX', 'Y': 'GroupY'
        }
        row_placer = RowPlacer(
            self.group_name_to_group,
            element_to_group,
            self.positioner,
            self.analyzer
        )
        
        groups_to_move = ['Group1', 'Group2']
        outgoing = {'A': 'X', 'C': 'Y'}
        node_positions = {'X': 8.0, 'Y': 4.0}  # 8.0 is farther from 6.0 than 4.0
        
        result = row_placer.sort_groups_by_distance_from_center(
            groups_to_move, outgoing, node_positions
        )
        
        # Group2 (target at 4.0, dist=2.0) should come before Group1 (target at 8.0, dist=2.0)
        # Both are same distance, so order maintained or by name
        self.assertIn('Group1', result)
        self.assertIn('Group2', result)
    
    # Tests for move_groups_until_fit
    def test_move_groups_until_fit(self):
        """Test moving groups until row fits."""
        group_name_to_group = {
            'G1': {'elements': ['A']},
            'G2': {'elements': ['B']},
            'G3': {'elements': ['C', 'D', 'E', 'F', 'G', 'H']}, # Wide group
        }
        element_to_group = {'A': 'G1', 'B': 'G2', 'C': 'G3', 'D': 'G3', 'E': 'G3', 'F': 'G3', 'G': 'G3', 'H': 'G3'}
        positioner = GroupPositioner(group_name_to_group, 2.0)
        analyzer = DependencyAnalyzer(group_name_to_group, element_to_group)
        row_placer = RowPlacer(group_name_to_group, element_to_group, positioner, analyzer)
        
        sorted_groups = ['G3', 'G2', 'G1']
        row_groups = ['G1', 'G2', 'G3']
        max_width = 5.0  # Small width
        
        keep, move = row_placer.move_groups_until_fit(
            sorted_groups, row_groups, max_width
        )
        
        # Should move groups until width fits
        self.assertGreater(len(move), 0)
    
    # Tests for split_overcrowded_row
    def test_split_overcrowded_row_fallback(self):
        """Test fallback splitting when no prioritized groups."""
        group_name_to_group = {
            'G1': {'elements': ['A']},
            'G2': {'elements': ['B']},
        }
        element_to_group = {'A': 'G1', 'B': 'G2'}
        positioner = GroupPositioner(group_name_to_group, 2.0)
        analyzer = DependencyAnalyzer(group_name_to_group, element_to_group)
        row_placer = RowPlacer(group_name_to_group, element_to_group, positioner, analyzer)
        
        row_groups = ['G1', 'G2']
        groups_with_incoming = []
        groups_without_incoming = []
        outgoing = {}
        node_positions = {}
        max_width = 0.1  # Very small
        
        keep, move = row_placer.split_overcrowded_row(
            row_groups, groups_with_incoming, groups_without_incoming,
            outgoing, node_positions, max_width
        )
        
        # Should split in half as fallback
        self.assertEqual(len(keep), 1)
        self.assertEqual(len(move), 1)
    
    # Tests for place_groups_on_row_centered_by_target
    def test_place_groups_on_row_centered_by_target(self):
        """Test placing groups centered by their targets."""
        element_to_group = self.element_to_group.copy()
        element_to_group['X'] = 'GroupX'
        
        row_placer = RowPlacer(
            self.group_name_to_group,
            element_to_group,
            self.positioner,
            self.analyzer
        )
        
        levels = {}
        positions = {}
        node_positions = {'X': 5.0}
        outgoing = {'A': 'X'}
        
        row_placer.place_groups_on_row_centered_by_target(
            ['Group1'], 3, levels, positions, node_positions, outgoing
        )
        
        self.assertEqual(levels['Group1'], 3)
        self.assertIn('Group1', positions)
    
    def test_place_groups_on_row_centered_by_target_empty(self):
        """Test placing empty group list (line 42)."""
        levels = {}
        positions = {}
        node_positions = {}
        outgoing = {}
        
        # Test place_groups_on_row with empty list - should return early (line 42)
        result = self.row_placer.place_groups_on_row(
            [], 3, levels, positions, node_positions, center=False
        )
        
        # Should not modify levels or positions and returns None
        self.assertIsNone(result)
        self.assertEqual(len(levels), 0)
        self.assertEqual(len(positions), 0)
    
    # Tests for split_overcrowded_row fallback when no prioritized groups
    def test_split_overcrowded_row_empty_priorities(self):
        """Test fallback splitting when select_groups_by_priority returns empty (lines 228-241)."""
        group_name_to_group = {
            'G1': {'elements': ['A']},
            'G2': {'elements': ['B']},
        }
        element_to_group = {'A': 'G1', 'B': 'G2'}
        positioner = GroupPositioner(group_name_to_group, 2.0)
        analyzer = DependencyAnalyzer(group_name_to_group, element_to_group)
        row_placer = RowPlacer(group_name_to_group, element_to_group, positioner, analyzer)
        
        row_groups = ['G1', 'G2']
        groups_with_incoming = []
        groups_without_incoming = []
        outgoing = {}
        node_positions = {}
        max_width = 0.1  # Very small to trigger split
        
        keep, move = row_placer.split_overcrowded_row(
            row_groups, groups_with_incoming, groups_without_incoming,
            outgoing, node_positions, max_width
        )
        
        # Should fallback to splitting in half
        self.assertEqual(len(keep), 1)
        self.assertEqual(len(move), 1)
        self.assertIn(keep[0], row_groups)
        self.assertIn(move[0], row_groups)
    
    # Tests for place_groups_on_row with overflow scenario
    def test_place_groups_on_row_with_overflow(self):
        """Test place_groups_on_row_with_overflow with row overflow requiring iterative splits (lines 271, 276-289)."""
        group_name_to_group = {
            'G1': {'elements': ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']},
            'G2': {'elements': ['I', 'J', 'K', 'L']},
            'G3': {'elements': ['M', 'N', 'O']},
        }
        element_to_group = {
            'A': 'G1', 'B': 'G1', 'C': 'G1', 'D': 'G1', 'E': 'G1', 'F': 'G1', 'G': 'G1', 'H': 'G1',
            'I': 'G2', 'J': 'G2', 'K': 'G2', 'L': 'G2',
            'M': 'G3', 'N': 'G3', 'O': 'G3',
        }
        positioner = GroupPositioner(group_name_to_group, 2.0)
        analyzer = DependencyAnalyzer(group_name_to_group, element_to_group)
        row_placer = RowPlacer(group_name_to_group, element_to_group, positioner, analyzer)
        
        levels = {}
        positions = {}
        incoming = {}
        outgoing = {}
        node_positions = {}
        level = 2
        placed_groups = set()
        
        # This should trigger the overflow handling with splits
        result = row_placer.place_groups_on_row_with_overflow(
            ['G1', 'G2', 'G3'], level, levels, positions,
            node_positions, incoming, outgoing, placed_groups
        )
        
        # Should complete successfully
        self.assertTrue(result)
        # Some groups should be placed
        self.assertGreater(len(levels), 0)
    
    def test_place_groups_on_row_empty(self):
        """Test place_groups_on_row_with_overflow with empty group list (line 334)."""
        levels = {}
        positions = {}
        incoming = {}
        outgoing = {}
        node_positions = {}
        placed_groups = set()
        
        # Call with empty list - should return True
        result = self.row_placer.place_groups_on_row_with_overflow(
            [], 2, levels, positions, node_positions, incoming, outgoing, placed_groups
        )
        
        self.assertTrue(result)
        self.assertEqual(len(levels), 0)


if __name__ == '__main__':
    unittest.main()
