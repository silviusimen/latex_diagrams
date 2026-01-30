#!/usr/bin/env python3
"""Unit tests for Layout Engine."""

import unittest
from latex_diagram_generator.layout_engine import LayoutEngine


class TestLayoutEngine(unittest.TestCase):
    """Tests for LayoutEngine class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = LayoutEngine(within_group_spacing=2.0)
        
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
    
    # Tests for __init__
    def test_init_sets_default_spacing(self):
        """Test that init sets default spacing."""
        engine = LayoutEngine()
        self.assertEqual(engine.WITHIN_GROUP_SPACING, 2.0)
    
    def test_init_sets_custom_spacing(self):
        """Test that init accepts custom spacing."""
        engine = LayoutEngine(within_group_spacing=3.5)
        self.assertEqual(engine.WITHIN_GROUP_SPACING, 3.5)
    
    def test_init_sets_none_attributes(self):
        """Test that init sets group mappings to None."""
        engine = LayoutEngine()
        self.assertIsNone(engine.group_name_to_group)
        self.assertIsNone(engine.element_to_group)
    
    # Tests for _initialize_layout
    def test_initialize_layout_returns_correct_structure(self):
        """Test that initialize_layout returns correct data structures."""
        result = self.engine._initialize_layout(
            self.group_name_to_group,
            self.element_to_group
        )
        
        all_groups, levels, positions, node_positions, placed_groups, current_y = result
        
        self.assertEqual(all_groups, set(self.group_name_to_group.keys()))
        self.assertEqual(levels, {})
        self.assertEqual(positions, {})
        self.assertEqual(node_positions, {})
        self.assertEqual(placed_groups, set())
        self.assertEqual(current_y, 0)
    
    def test_initialize_layout_sets_engine_attributes(self):
        """Test that initialize_layout sets engine attributes."""
        engine = LayoutEngine()
        
        engine._initialize_layout(
            self.group_name_to_group,
            self.element_to_group
        )
        
        self.assertEqual(engine.group_name_to_group, self.group_name_to_group)
        self.assertEqual(engine.element_to_group, self.element_to_group)
        # Check that helper components are initialized
        self.assertIsNotNone(engine.analyzer)
        self.assertIsNotNone(engine.positioner)
        self.assertIsNotNone(engine.bottom_placer)
        self.assertIsNotNone(engine.row_placer)
    
    # Integration tests for complete layout computation
    def test_compute_layout_bottom_up_simple(self):
        """Test complete layout computation for simple case."""
        group_name_to_group = {
            'Bottom': {'elements': ['A']},
            'Top': {'elements': ['B']}
        }
        element_to_group = {'A': 'Bottom', 'B': 'Top'}
        outgoing = {'B': 'A'}
        incoming = {'A': ['B']}
        
        engine = LayoutEngine()
        levels, positions = engine.compute_layout_bottom_up(
            group_name_to_group, element_to_group, outgoing, incoming
        )
        
        # Bottom should be at y=0, Top at y=1
        self.assertIn('Bottom', levels)
        self.assertIn('Top', levels)
        self.assertLess(levels['Bottom'], levels['Top'])
        
        # Both should have positions
        self.assertIn('Bottom', positions)
        self.assertIn('Top', positions)
    
    def test_compute_layout_bottom_up_no_links(self):
        """Test layout with no links between groups."""
        group_name_to_group = {
            'G1': {'elements': ['A']},
            'G2': {'elements': ['B']}
        }
        element_to_group = {'A': 'G1', 'B': 'G2'}
        outgoing = {}
        incoming = {}
        
        engine = LayoutEngine()
        levels, positions = engine.compute_layout_bottom_up(
            group_name_to_group, element_to_group, outgoing, incoming
        )
        
        # Both should be placed
        self.assertEqual(len(levels), 2)
        self.assertEqual(len(positions), 2)
    
    def test_compute_layout_bottom_up_complex(self):
        """Test layout with multiple groups and dependencies."""
        group_name_to_group = {
            'G1': {'elements': ['A']},
            'G2': {'elements': ['B']},
            'G3': {'elements': ['C']},
            'G4': {'elements': ['D']}
        }
        element_to_group = {'A': 'G1', 'B': 'G2', 'C': 'G3', 'D': 'G4'}
        # G4 -> G3 -> G2 -> G1 (chain)
        outgoing = {'D': 'C', 'C': 'B', 'B': 'A'}
        incoming = {'C': ['D'], 'B': ['C'], 'A': ['B']}
        
        engine = LayoutEngine()
        levels, positions = engine.compute_layout_bottom_up(
            group_name_to_group, element_to_group, outgoing, incoming
        )
        
        # All groups should be placed
        self.assertEqual(len(levels), 4)
        self.assertEqual(len(positions), 4)
        
        # Check ordering: G1 at bottom, G4 at top
        self.assertLess(levels['G1'], levels['G2'])
        self.assertLess(levels['G2'], levels['G3'])
        self.assertLess(levels['G3'], levels['G4'])
    
    def test_compute_layout_with_empty_next_groups(self):
        """Test compute_layout_bottom_up with empty next_groups scenario (line 114)."""
        # Create a scenario where all groups are placed on first level
        group_name_to_group = {
            'G1': {'elements': ['A']},
            'G2': {'elements': ['B']}
        }
        element_to_group = {'A': 'G1', 'B': 'G2'}
        # No links - all placed on first level, next_groups will be empty
        outgoing = {}
        incoming = {}
        
        engine = LayoutEngine()
        levels, positions = engine.compute_layout_bottom_up(
            group_name_to_group, element_to_group, outgoing, incoming
        )
        
        # Both groups should be placed at same level
        self.assertEqual(len(levels), 2)
        self.assertEqual(levels['G1'], levels['G2'])
    
    def test_compute_layout_with_empty_sorted_groups(self):
        """Test compute_layout_bottom_up with empty sorted_groups scenario (line 170)."""
        # Single group, no dependencies
        group_name_to_group = {
            'G1': {'elements': ['A']}
        }
        element_to_group = {'A': 'G1'}
        outgoing = {}
        incoming = {}
        
        engine = LayoutEngine()
        levels, positions = engine.compute_layout_bottom_up(
            group_name_to_group, element_to_group, outgoing, incoming
        )
        
        # Single group should be placed
        self.assertEqual(len(levels), 1)
        self.assertEqual(len(positions), 1)
        self.assertIn('G1', levels)


if __name__ == '__main__':
    unittest.main()
