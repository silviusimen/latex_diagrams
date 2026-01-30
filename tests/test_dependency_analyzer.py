#!/usr/bin/env python3
"""Unit tests for DependencyAnalyzer."""

import unittest
from latex_diagram_generator.dependency_analyzer import DependencyAnalyzer


class TestDependencyAnalyzer(unittest.TestCase):
    """Tests for DependencyAnalyzer class."""
    
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
        
        self.analyzer = DependencyAnalyzer(self.group_name_to_group, self.element_to_group)
    
    # Tests for has_outgoing_to_other_group
    def test_has_outgoing_to_other_group_with_outgoing(self):
        """Test detecting outgoing links to other groups."""
        outgoing = {'A': 'C'}  # A in Group1 -> C in Group2
        result = self.analyzer.has_outgoing_to_other_group('Group1', outgoing)
        self.assertTrue(result)
    
    def test_has_outgoing_to_other_group_without_outgoing(self):
        """Test detecting no outgoing links."""
        outgoing = {}
        result = self.analyzer.has_outgoing_to_other_group('Group1', outgoing)
        self.assertFalse(result)
    
    def test_has_outgoing_to_other_group_same_group(self):
        """Test that links within same group return False."""
        outgoing = {'A': 'B'}  # Both in Group1
        result = self.analyzer.has_outgoing_to_other_group('Group1', outgoing)
        self.assertFalse(result)
    
    def test_has_outgoing_to_other_group_list_target(self):
        """Test with target as list."""
        outgoing = {'A': ['C', 'D']}
        result = self.analyzer.has_outgoing_to_other_group('Group1', outgoing)
        self.assertTrue(result)
    
    def test_has_outgoing_to_other_group_from_group_name(self):
        """Test with link from group name directly."""
        group_name_to_group = {
            'Group1': {},  # No elements - triggers group name check
            'Group2': {'elements': ['B']}
        }
        element_to_group = {'B': 'Group2'}
        analyzer = DependencyAnalyzer(group_name_to_group, element_to_group)
        
        outgoing = {'Group1': 'B'}
        result = analyzer.has_outgoing_to_other_group('Group1', outgoing)
        self.assertTrue(result)
    
    # Tests for find_bottom_groups
    def test_find_bottom_groups_with_one_bottom(self):
        """Test finding bottom groups when one exists."""
        all_groups = {'Group1', 'Group2'}
        outgoing = {'A': 'C'}  # Group1 -> Group2
        
        result = self.analyzer.find_bottom_groups(all_groups, outgoing)
        
        self.assertEqual(result, ['Group2'])
    
    def test_find_bottom_groups_with_multiple(self):
        """Test finding multiple bottom groups."""
        all_groups = {'Group1', 'Group2', 'Group3'}
        outgoing = {'A': 'D'}  # Only Group1 has outgoing
        
        result = self.analyzer.find_bottom_groups(all_groups, outgoing)
        
        self.assertIn('Group2', result)
        self.assertIn('Group3', result)
        self.assertEqual(len(result), 2)
    
    def test_find_bottom_groups_all_bottom(self):
        """Test when all groups are bottom groups."""
        all_groups = {'Group1', 'Group2'}
        outgoing = {}
        
        result = self.analyzer.find_bottom_groups(all_groups, outgoing)
        
        self.assertEqual(len(result), 2)
    
    # Tests for get_group_target
    def test_get_group_target_with_element_link(self):
        """Test getting target group from element link."""
        outgoing = {'A': 'C'}
        result = self.analyzer.get_group_target('Group1', outgoing)
        self.assertEqual(result, 'Group2')
    
    def test_get_group_target_no_link(self):
        """Test getting None when no target exists."""
        outgoing = {}
        result = self.analyzer.get_group_target('Group1', outgoing)
        self.assertIsNone(result)
    
    def test_get_group_target_with_list(self):
        """Test getting target when outgoing is a list."""
        outgoing = {'A': ['C', 'D']}
        result = self.analyzer.get_group_target('Group1', outgoing)
        self.assertEqual(result, 'Group2')
    
    def test_get_group_target_from_group_name(self):
        """Test getting target from group name link."""
        group_name_to_group = {
            'Group1': {'name': 'Group1'},
            'Group2': {'elements': ['B']}
        }
        element_to_group = {'B': 'Group2'}
        analyzer = DependencyAnalyzer(group_name_to_group, element_to_group)
        
        outgoing = {'Group1': 'B'}
        result = analyzer.get_group_target('Group1', outgoing)
        self.assertEqual(result, 'Group2')
    
    # Tests for group_links_to_placed
    def test_group_links_to_placed_true(self):
        """Test when group links to placed group."""
        placed_groups = {'Group2'}
        outgoing = {'A': 'C'}
        
        result = self.analyzer.group_links_to_placed('Group1', placed_groups, outgoing)
        
        self.assertTrue(result)
    
    def test_group_links_to_placed_false(self):
        """Test when group doesn't link to placed groups."""
        placed_groups = {'Group3'}
        outgoing = {'A': 'C'}  # Links to Group2, not Group3
        
        result = self.analyzer.group_links_to_placed('Group1', placed_groups, outgoing)
        
        self.assertFalse(result)
    
    def test_group_links_to_placed_no_target(self):
        """Test when group has no target."""
        placed_groups = {'Group2'}
        outgoing = {}
        
        result = self.analyzer.group_links_to_placed('Group1', placed_groups, outgoing)
        
        self.assertFalse(result)
    
    # Tests for find_next_layer_groups
    def test_find_next_layer_groups_one_group(self):
        """Test finding next layer with one group."""
        all_groups = {'Group1', 'Group2'}
        placed_groups = {'Group2'}
        outgoing = {'A': 'C'}
        
        result = self.analyzer.find_next_layer_groups(all_groups, placed_groups, outgoing)
        
        self.assertEqual(result, ['Group1'])
    
    def test_find_next_layer_groups_no_groups(self):
        """Test when no groups link to placed."""
        all_groups = {'Group1', 'Group2'}
        placed_groups = {'Group3'}
        outgoing = {}
        
        result = self.analyzer.find_next_layer_groups(all_groups, placed_groups, outgoing)
        
        self.assertEqual(result, [])
    
    def test_find_next_layer_groups_multiple(self):
        """Test finding multiple next layer groups."""
        group_name_to_group = {
            'Group1': {'elements': ['A']},
            'Group2': {'elements': ['B']},
            'Group3': {'elements': ['C']}
        }
        element_to_group = {'A': 'Group1', 'B': 'Group2', 'C': 'Group3'}
        analyzer = DependencyAnalyzer(group_name_to_group, element_to_group)
        
        all_groups = {'Group1', 'Group2', 'Group3'}
        placed_groups = {'Group3'}
        outgoing = {'A': 'C', 'B': 'C'}
        
        result = analyzer.find_next_layer_groups(all_groups, placed_groups, outgoing)
        
        self.assertEqual(len(result), 2)
        self.assertIn('Group1', result)
        self.assertIn('Group2', result)
    
    # Tests for get_group_destination_x
    def test_get_group_destination_x_with_position(self):
        """Test getting destination x when target has position."""
        outgoing = {'A': 'C'}
        node_positions = {'C': 5.0}
        
        result = self.analyzer.get_group_destination_x('Group1', outgoing, node_positions)
        
        self.assertEqual(result, 5.0)
    
    def test_get_group_destination_x_no_position(self):
        """Test getting default when no position found."""
        outgoing = {'A': 'C'}
        node_positions = {}
        
        result = self.analyzer.get_group_destination_x('Group1', outgoing, node_positions)
        
        self.assertEqual(result, 999)
    
    def test_get_group_destination_x_no_outgoing(self):
        """Test getting default when no outgoing links."""
        outgoing = {}
        node_positions = {}
        
        result = self.analyzer.get_group_destination_x('Group1', outgoing, node_positions)
        
        self.assertEqual(result, 999)
    
    def test_get_group_destination_x_from_group_name(self):
        """Test getting destination from group name link."""
        group_name_to_group = {
            'Group1': {'name': 'Group1'},
            'Group2': {'elements': ['B']}
        }
        element_to_group = {'B': 'Group2'}
        analyzer = DependencyAnalyzer(group_name_to_group, element_to_group)
        
        outgoing = {'Group1': 'B'}
        node_positions = {'B': 7.5}
        
        result = analyzer.get_group_destination_x('Group1', outgoing, node_positions)
        
        self.assertEqual(result, 7.5)
    
    # Tests for sort_groups_by_destination
    def test_sort_groups_by_destination_basic(self):
        """Test sorting groups by destination."""
        element_to_group = {
            'A': 'Group1', 'B': 'Group1',
            'C': 'Group2',
            'X': 'GroupX', 'Y': 'GroupY'
        }
        analyzer = DependencyAnalyzer(self.group_name_to_group, element_to_group)
        
        groups = ['Group1', 'Group2']
        outgoing = {'A': 'X', 'C': 'Y'}
        node_positions = {'X': 10.0, 'Y': 5.0}
        
        result = analyzer.sort_groups_by_destination(groups, outgoing, node_positions)
        
        # Group2 (dest 5.0) should come before Group1 (dest 10.0)
        self.assertEqual(result[0], 'Group2')
        self.assertEqual(result[1], 'Group1')
    
    def test_sort_groups_by_destination_alphabetical_tie(self):
        """Test alphabetical sorting when destinations match."""
        group_name_to_group = {
            'GroupB': {'elements': ['X']},
            'GroupA': {'elements': ['Y']}
        }
        element_to_group = {'X': 'GroupB', 'Y': 'GroupA'}
        analyzer = DependencyAnalyzer(group_name_to_group, element_to_group)
        
        groups = ['GroupB', 'GroupA']
        outgoing = {}
        node_positions = {}
        
        result = analyzer.sort_groups_by_destination(groups, outgoing, node_positions)
        
        # Both have dest 999, should be sorted alphabetically
        self.assertEqual(result[0], 'GroupA')
        self.assertEqual(result[1], 'GroupB')
    
    # Tests for _get_target_from_list
    def test_get_target_from_list_with_list(self):
        """Test extracting target from list."""
        result = self.analyzer._get_target_from_list(['A', 'B', 'C'])
        self.assertEqual(result, 'A')
    
    def test_get_target_from_list_with_single_value(self):
        """Test extracting target when not a list."""
        result = self.analyzer._get_target_from_list('A')
        self.assertEqual(result, 'A')
    
    # Tests for find_group_target_in_set
    def test_find_group_target_in_set_found(self):
        """Test finding target in set."""
        group_name_to_group = {
            'Group1': {'name': 'Group1', 'elements': ['A']},
            'Group2': {'elements': ['B']}
        }
        element_to_group = {'A': 'Group1', 'B': 'Group2'}
        analyzer = DependencyAnalyzer(group_name_to_group, element_to_group)
        
        outgoing = {'A': 'B'}
        result = analyzer.find_group_target_in_set('Group1', ['Group2'], outgoing)
        
        self.assertEqual(result, 'Group2')
    
    def test_find_group_target_in_set_not_in_set(self):
        """Test when target not in specified set."""
        outgoing = {'A': 'C'}
        result = self.analyzer.find_group_target_in_set('Group1', ['Group3'], outgoing)
        
        self.assertIsNone(result)
    
    def test_find_group_target_in_set_no_outgoing(self):
        """Test when group has no outgoing links."""
        outgoing = {}
        result = self.analyzer.find_group_target_in_set('Group1', ['Group2'], outgoing)
        
        self.assertIsNone(result)
    
    # Tests for find_bottom_group_dependencies
    def test_find_bottom_group_dependencies_with_deps(self):
        """Test finding dependencies among bottom groups."""
        outgoing = {'A': 'C'}
        result = self.analyzer.find_bottom_group_dependencies(['Group1', 'Group2'], outgoing)
        
        self.assertEqual(result, {'Group1': 'Group2'})
    
    def test_find_bottom_group_dependencies_no_deps(self):
        """Test when no dependencies exist."""
        outgoing = {}
        result = self.analyzer.find_bottom_group_dependencies(['Group1', 'Group2'], outgoing)
        
        self.assertEqual(result, {})


if __name__ == '__main__':
    unittest.main()
