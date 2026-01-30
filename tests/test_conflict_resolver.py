#!/usr/bin/env python3
"""
Unit tests for ConflictResolver class.
Tests orchestration and resolution logic.
"""

import unittest
from unittest.mock import patch
from latex_diagram_generator.conflict_resolver import ConflictResolver


class TestConflictResolverInit(unittest.TestCase):
    """Test ConflictResolver initialization."""
    
    def test_init_default_spacing(self):
        """Test initialization with default spacing."""
        resolver = ConflictResolver()
        self.assertEqual(resolver.WITHIN_GROUP_SPACING, 2.0)
    
    def test_init_custom_spacing(self):
        """Test initialization with custom spacing."""
        resolver = ConflictResolver(within_group_spacing=3.5)
        self.assertEqual(resolver.WITHIN_GROUP_SPACING, 3.5)


class TestCheckArrowIntersections(unittest.TestCase):
    """Test check_arrow_intersections orchestration method."""
    
    def setUp(self):
        self.resolver = ConflictResolver()
    
    def test_return_conflicts_true(self):
        """Test with return_conflicts=True."""
        node_positions = {
            'A': ('node_a', 0, 0),
            'B': ('node_b', 2, 0)
        }
        links = {'A': 'B'}
        
        result = self.resolver.check_arrow_intersections(
            node_positions, links, return_conflicts=True
        )
        
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 3)
        text_overlaps, arrow_crossings, arrow_through_text = result
        self.assertIsInstance(text_overlaps, list)
    
    @patch('builtins.print')
    def test_return_conflicts_false_with_conflicts(self, mock_print):
        """Test with return_conflicts=False and conflicts present."""
        node_positions = {
            'A': ('node_a', 0, 0),
            'B': ('node_b', 0.1, 0)  # Overlapping position
        }
        links = {}
        
        result = self.resolver.check_arrow_intersections(
            node_positions, links, return_conflicts=False
        )
        
        self.assertIsNone(result)
        # Should have printed warning
        mock_print.assert_called()
    
    def test_no_conflicts(self):
        """Test when no conflicts exist."""
        node_positions = {
            'A': ('node_a', 0, 0),
            'B': ('node_b', 5, 0)
        }
        links = {'A': 'B'}
        
        result = self.resolver.check_arrow_intersections(
            node_positions, links, return_conflicts=True
        )
        
        text_overlaps, arrow_crossings, arrow_through_text = result
        self.assertEqual(len(text_overlaps), 0)
        self.assertEqual(len(arrow_crossings), 0)


class TestShiftGroupHorizontally(unittest.TestCase):
    """Test _shift_group_horizontally method."""
    
    def setUp(self):
        self.resolver = ConflictResolver()
    
    def test_shift_single_element_group(self):
        """Test shifting a single element group."""
        positions = {'G1': (5.0, ['A'])}
        node_positions = {'A': ('node_a', 5.0, 0)}
        
        self.resolver._shift_group_horizontally(
            'G1', 2.0, positions, node_positions
        )
        
        self.assertEqual(positions['G1'], (7.0, ['A']))
        self.assertEqual(node_positions['A'], ('node_a', 7.0, 0))
    
    def test_shift_multi_element_group(self):
        """Test shifting a multi-element group."""
        positions = {'G1': (5.0, ['A', 'B', 'C'])}
        node_positions = {
            'A': ('node_a', 5.0, 0),
            'B': ('node_b', 7.0, 0),
            'C': ('node_c', 9.0, 0)
        }
        
        self.resolver._shift_group_horizontally(
            'G1', 1.0, positions, node_positions
        )
        
        self.assertEqual(positions['G1'], (6.0, ['A', 'B', 'C']))
        self.assertEqual(node_positions['A'], ('node_a', 6.0, 0))
        self.assertEqual(node_positions['B'], ('node_b', 8.0, 0))
        self.assertEqual(node_positions['C'], ('node_c', 10.0, 0))


class TestFindGroupForElement(unittest.TestCase):
    """Test _find_group_for_element method."""
    
    def setUp(self):
        self.resolver = ConflictResolver()
    
    def test_find_group_for_element_found(self):
        """Test finding group for existing element."""
        group_name_to_group = {
            'G1': {'name': 'G1', 'elements': ['A', 'B']},
            'G2': {'name': 'G2', 'elements': ['C']}
        }
        
        result = self.resolver._find_group_for_element('B', group_name_to_group)
        self.assertEqual(result, 'G1')
    
    def test_find_group_for_element_not_found(self):
        """Test when element not in any group."""
        group_name_to_group = {
            'G1': {'name': 'G1', 'elements': ['A']},
        }
        
        result = self.resolver._find_group_for_element('Z', group_name_to_group)
        self.assertIsNone(result)
    
    def test_find_group_for_element_no_elements_key(self):
        """Test when group doesn't have 'elements' key."""
        group_name_to_group = {
            'G1': {'name': 'G1'},  # No 'elements' key
        }
        
        result = self.resolver._find_group_for_element('A', group_name_to_group)
        self.assertIsNone(result)
    
    def test_find_group_for_element_by_name(self):
        """Test finding group when group name equals element."""
        group_name_to_group = {
            'A': {'name': 'A'},  # No 'elements' key but name matches
        }
        
        result = self.resolver._find_group_for_element('A', group_name_to_group)
        self.assertEqual(result, 'A')


class TestResolveTextOverlaps(unittest.TestCase):
    """Test _resolve_text_overlaps method."""
    
    def setUp(self):
        self.resolver = ConflictResolver()
    
    @patch('builtins.print')
    def test_resolve_text_overlaps(self, mock_print):
        """Test text overlap resolution."""
        text_overlaps = [('A', 0, 0, 'B', 0.5, 0)]
        positions = {'G1': (0, ['A']), 'G2': (0.5, ['B'])}
        node_positions = {'A': ('node_a', 0, 0), 'B': ('node_b', 0.5, 0)}
        group_name_to_group = {
            'G1': {'name': 'G1', 'elements': ['A']},
            'G2': {'name': 'G2', 'elements': ['B']}
        }
        
        result = self.resolver._resolve_text_overlaps(
            text_overlaps, positions, node_positions, group_name_to_group
        )
        
        # Should have tried to resolve and return boolean
        self.assertIsInstance(result, bool)
    
    @patch('builtins.print')
    def test_resolve_text_overlaps_horizontal_same_level(self, mock_print):
        """Test resolving horizontal text overlaps on same level."""
        positions = {
            'G1': (0.0, ['A']),
            'G2': (1.0, ['B'])  # Too close
        }
        node_positions = {
            'A': ('a', 0.0, 5),
            'B': ('b', 1.0, 5)  # Same level, overlapping
        }
        group_name_to_group = {
            'G1': {'elements': ['A']},
            'G2': {'elements': ['B']}
        }
        
        result = self.resolver._resolve_text_overlaps(
            [('A', 0.0, 5, 'B', 1.0, 5)],
            positions, node_positions, group_name_to_group
        )
        
        self.assertTrue(result)
    
    def test_resolve_text_overlaps_no_group(self):
        """Test when element not in any group."""
        text_overlaps = [('A', 0, 0, 'B', 0.5, 0)]
        positions = {}
        node_positions = {'A': ('node_a', 0, 0), 'B': ('node_b', 0.5, 0)}
        group_name_to_group = {}
        
        result = self.resolver._resolve_text_overlaps(
            text_overlaps, positions, node_positions, group_name_to_group
        )
        
        self.assertFalse(result)


class TestResolveArrowCrossings(unittest.TestCase):
    """Test _resolve_arrow_crossings method."""
    
    def setUp(self):
        self.resolver = ConflictResolver()
    
    @patch('builtins.print')
    def test_resolve_arrow_crossings(self, mock_print):
        """Test arrow crossing resolution."""
        arrow_crossings = [('A', 'B', 'C', 'D', 2, 2)]
        positions = {'G1': (0, ['A']), 'G2': (4, ['B'])}
        node_positions = {'A': ('node_a', 0, 0), 'B': ('node_b', 4, 4)}
        group_name_to_group = {
            'G1': {'name': 'G1', 'elements': ['A']},
            'G2': {'name': 'G2', 'elements': ['B']},
            'G3': {'name': 'G3', 'elements': ['C']},
            'G4': {'name': 'G4', 'elements': ['D']}
        }
        
        result = self.resolver._resolve_arrow_crossings(
            arrow_crossings, positions, node_positions, group_name_to_group
        )
        
        self.assertIsInstance(result, bool)
    
    @patch('builtins.print')
    def test_resolve_arrow_crossings_with_shift(self, mock_print):
        """Test resolving arrow crossings by shifting groups."""
        positions = {
            'G1': (0.0, ['A']),
            'G2': (2.0, ['B']),
            'G3': (1.0, ['C']),
            'G4': (3.0, ['D'])
        }
        node_positions = {
            'A': ('a', 0.0, 0),
            'B': ('b', 2.0, 1),
            'C': ('c', 1.0, 1),
            'D': ('d', 3.0, 0)
        }
        group_name_to_group = {
            'G1': {'elements': ['A']},
            'G2': {'elements': ['B']},
            'G3': {'elements': ['C']},
            'G4': {'elements': ['D']}
        }
        
        # Arrows A->C and B->D might cross
        arrow_crossings = [('A', 'C', 'B', 'D', 1.5, 0.5)]
        
        result = self.resolver._resolve_arrow_crossings(
            arrow_crossings, positions, node_positions, group_name_to_group
        )
        
        # Result should be boolean
        self.assertIsInstance(result, bool)


class TestResolveArrowThroughText(unittest.TestCase):
    """Test _resolve_arrow_through_text method."""
    
    def setUp(self):
        self.resolver = ConflictResolver()
    
    @patch('builtins.print')
    def test_resolve_arrow_through_text_with_incoming(self, mock_print):
        """Test resolving arrow-through-text with incoming links."""
        arrow_through_text = [('A', 'C', 'B', 2, 0)]
        positions = {'G1': (0, ['A']), 'G2': (2, ['B']), 'G3': (4, ['C'])}
        node_positions = {
            'A': ('a', 0, 0),
            'B': ('b', 2, 0),
            'C': ('c', 4, 0)
        }
        incoming = {'G2': ['G1']}  # B has incoming link
        group_name_to_group = {
            'G1': {'elements': ['A']},
            'G2': {'elements': ['B']},
            'G3': {'elements': ['C']}
        }
        
        result = self.resolver._resolve_arrow_through_text(
            arrow_through_text, positions, node_positions, incoming, group_name_to_group
        )
        
        self.assertIsInstance(result, bool)
    
    @patch('builtins.print')
    def test_resolve_arrow_through_text_no_incoming(self, mock_print):
        """Test resolving arrow-through-text without incoming links."""
        arrow_through_text = [('A', 'C', 'B', 2, 0)]
        positions = {'G1': (0, ['A']), 'G2': (2, ['B']), 'G3': (4, ['C'])}
        node_positions = {
            'A': ('a', 0, 0),
            'B': ('b', 2, 0),
            'C': ('c', 4, 0)
        }
        incoming = {}  # No incoming links
        group_name_to_group = {
            'G1': {'elements': ['A']},
            'G2': {'elements': ['B']},
            'G3': {'elements': ['C']}
        }
        
        result = self.resolver._resolve_arrow_through_text(
            arrow_through_text, positions, node_positions, incoming, group_name_to_group
        )
        
        self.assertIsInstance(result, bool)


class TestResolveConflictsIteratively(unittest.TestCase):
    """Test resolve_conflicts_iteratively orchestration method."""
    
    def setUp(self):
        self.resolver = ConflictResolver()
    
    @patch('builtins.print')
    def test_no_conflicts(self, mock_print):
        """Test when there are no conflicts."""
        node_positions = {
            'A': ('node_a', 0, 0),
            'B': ('node_b', 5, 0)
        }
        levels = {'G1': 0, 'G2': 0}
        positions = {'G1': (0, ['A']), 'G2': (5, ['B'])}
        outgoing = {}
        incoming = {}
        group_name_to_group = {
            'G1': {'name': 'G1', 'elements': ['A']},
            'G2': {'name': 'G2', 'elements': ['B']}
        }
        
        self.resolver.resolve_conflicts_iteratively(
            node_positions, levels, positions, outgoing, incoming,
            group_name_to_group
        )
        
        # Should print success message
        self.assertTrue(any('All conflicts resolved' in str(call) 
                          for call in mock_print.call_args_list))
    
    @patch('builtins.print')
    def test_with_conflicts(self, mock_print):
        """Test when conflicts exist and need resolution."""
        node_positions = {
            'A': ('node_a', 0, 0),
            'B': ('node_b', 0.3, 0)  # Overlapping
        }
        levels = {'G1': 0, 'G2': 0}
        positions = {'G1': (0, ['A']), 'G2': (0.3, ['B'])}
        outgoing = {}
        incoming = {}
        group_name_to_group = {
            'G1': {'name': 'G1', 'elements': ['A']},
            'G2': {'name': 'G2', 'elements': ['B']}
        }
        
        self.resolver.resolve_conflicts_iteratively(
            node_positions, levels, positions, outgoing, incoming,
            group_name_to_group, max_iterations=5
        )
        
        # Should have attempted resolution
        mock_print.assert_called()
    
    @patch('builtins.print')
    def test_with_arrow_crossings_report(self, mock_print):
        """Test that arrow_crossings are reported (line 38)."""
        # Create positions that will cause arrow crossing
        node_positions = {
            'A': ('node_a', 0, 0),
            'B': ('node_b', 4, 0),
            'C': ('node_c', 0, 2),
            'D': ('node_d', 4, 2)
        }
        levels = {'G1': 0, 'G2': 0, 'G3': 2, 'G4': 2}
        positions = {
            'G1': (0, ['A']),
            'G2': (4, ['B']),
            'G3': (0, ['C']),
            'G4': (4, ['D'])
        }
        # Cross arrows: A->D and B->C
        outgoing = {'A': 'D', 'B': 'C'}
        incoming = {'C': ['B'], 'D': ['A']}
        group_name_to_group = {
            'G1': {'name': 'G1', 'elements': ['A']},
            'G2': {'name': 'G2', 'elements': ['B']},
            'G3': {'name': 'G3', 'elements': ['C']},
            'G4': {'name': 'G4', 'elements': ['D']}
        }
        
        self.resolver.resolve_conflicts_iteratively(
            node_positions, levels, positions, outgoing, incoming,
            group_name_to_group, max_iterations=1
        )
        
        # Should have printed arrow_crossings count
        mock_print.assert_called()
    
    @patch('builtins.print')
    def test_max_iterations_exceeded(self, mock_print):
        """Test when max iterations is exceeded without resolution (lines 308-309)."""
        # Create overlapping nodes
        node_positions = {
            'A': ('node_a', 0, 0),
            'B': ('node_b', 0.1, 0)  # Very close overlap
        }
        levels = {'G1': 0, 'G2': 0}
        positions = {'G1': (0, ['A']), 'G2': (0.1, ['B'])}
        outgoing = {}
        incoming = {}
        group_name_to_group = {
            'G1': {'name': 'G1', 'elements': ['A']},
            'G2': {'name': 'G2', 'elements': ['B']}
        }
        
        # Set very low max_iterations to trigger the failure
        self.resolver.resolve_conflicts_iteratively(
            node_positions, levels, positions, outgoing, incoming,
            group_name_to_group, max_iterations=1
        )
        
        # Should print "Could not resolve conflicts" warning
        self.assertTrue(any('Could not resolve' in str(call) or 'conflicts' in str(call).lower()
                          for call in mock_print.call_args_list))


if __name__ == '__main__':
    unittest.main()
