#!/usr/bin/env python3
"""
Unit tests for ConflictDetector class.
"""

import unittest
from latex_diagram_generator.conflict_detector import ConflictDetector


class TestBuildPositionLookup(unittest.TestCase):
    """Test build_position_lookup static method."""
    
    def test_build_position_lookup_valid_data(self):
        """Test building position lookup from valid node_positions."""
        node_positions = {
            'A': ('node_a', 0.0, 0),
            'B': ('node_b', 2.0, 1),
            'C': ('node_c', 4.0, 2)
        }
        
        positions = ConflictDetector.build_position_lookup(node_positions)
        
        self.assertEqual(positions['A'], (0.0, 0))
        self.assertEqual(positions['B'], (2.0, 1))
        self.assertEqual(positions['C'], (4.0, 2))
    
    def test_build_position_lookup_invalid_tuples(self):
        """Test with invalid tuple lengths (not 3 elements)."""
        node_positions = {
            'A': ('node_a', 0.0, 0),
            'B': (2.0, 1),  # Only 2 elements
            'C': 5.0  # Not a tuple
        }
        
        positions = ConflictDetector.build_position_lookup(node_positions)
        
        # Only 'A' should be included
        self.assertEqual(len(positions), 1)
        self.assertEqual(positions['A'], (0.0, 0))
    
    def test_build_position_lookup_empty(self):
        """Test with empty node_positions."""
        positions = ConflictDetector.build_position_lookup({})
        self.assertEqual(positions, {})


class TestBuildArrowList(unittest.TestCase):
    """Test build_arrow_list static method."""
    
    def test_build_arrow_list_single_targets(self):
        """Test building arrow list with single targets."""
        links = {'A': 'B', 'B': 'C'}
        positions = {'A': (0, 0), 'B': (2, 1), 'C': (4, 2)}
        
        arrows = ConflictDetector.build_arrow_list(links, positions)
        
        self.assertEqual(len(arrows), 2)
        self.assertIn(('A', 0, 0, 'B', 2, 1), arrows)
        self.assertIn(('B', 2, 1, 'C', 4, 2), arrows)
    
    def test_build_arrow_list_multiple_targets(self):
        """Test building arrow list with list of targets."""
        links = {'A': ['B', 'C']}
        positions = {'A': (0, 0), 'B': (2, 1), 'C': (4, 1)}
        
        arrows = ConflictDetector.build_arrow_list(links, positions)
        
        self.assertEqual(len(arrows), 2)
        self.assertIn(('A', 0, 0, 'B', 2, 1), arrows)
        self.assertIn(('A', 0, 0, 'C', 4, 1), arrows)
    
    def test_build_arrow_list_missing_positions(self):
        """Test when source or target not in positions."""
        links = {'A': 'B', 'C': 'D'}
        positions = {'A': (0, 0), 'B': (2, 1)}  # C and D missing
        
        arrows = ConflictDetector.build_arrow_list(links, positions)
        
        # Only A->B should be included
        self.assertEqual(len(arrows), 1)
        self.assertEqual(arrows[0], ('A', 0, 0, 'B', 2, 1))


class TestCheckTextOverlaps(unittest.TestCase):
    """Test check_text_overlaps static method."""
    
    def test_no_overlaps(self):
        """Test with no overlapping text."""
        positions = {
            'A': (0, 0),
            'B': (5, 0),
            'C': (10, 0)
        }
        
        overlaps = ConflictDetector.check_text_overlaps(positions)
        self.assertEqual(len(overlaps), 0)
    
    def test_same_position_overlap(self):
        """Test detection of exact same position."""
        positions = {
            'A': (0, 0),
            'B': (0.05, 0.05)  # Within 0.1 tolerance
        }
        
        overlaps = ConflictDetector.check_text_overlaps(positions)
        self.assertEqual(len(overlaps), 1)
        self.assertEqual(overlaps[0][:2], ('A', 0))
    
    def test_horizontal_overlap_same_level(self):
        """Test detection of horizontal overlap on same level."""
        positions = {
            'A': (0, 0),
            'B': (0.5, 0)  # < 0.64 (text_width) apart on same level
        }
        
        overlaps = ConflictDetector.check_text_overlaps(positions)
        self.assertEqual(len(overlaps), 1)
    
    def test_different_levels_no_overlap(self):
        """Test that different y levels don't trigger horizontal overlap."""
        positions = {
            'A': (0, 0),
            'B': (0.5, 1)  # Close horizontally but different level
        }
        
        overlaps = ConflictDetector.check_text_overlaps(positions)
        self.assertEqual(len(overlaps), 0)


class TestCheckArrowCrossings(unittest.TestCase):
    """Test check_arrow_crossings static method."""
    
    def test_no_crossings(self):
        """Test with parallel arrows that don't cross."""
        arrows = [
            ('A', 0, 0, 'B', 2, 0),
            ('C', 0, 1, 'D', 2, 1)
        ]
        
        crossings = ConflictDetector.check_arrow_crossings(arrows)
        self.assertEqual(len(crossings), 0)
    
    def test_arrows_share_endpoint(self):
        """Test that arrows sharing endpoints are skipped."""
        arrows = [
            ('A', 0, 0, 'B', 2, 1),
            ('A', 0, 0, 'C', 2, 2)  # Same source
        ]
        
        crossings = ConflictDetector.check_arrow_crossings(arrows)
        self.assertEqual(len(crossings), 0)
    
    def test_crossing_arrows(self):
        """Test detection of crossing arrows."""
        arrows = [
            ('A', 0, 0, 'B', 4, 4),
            ('C', 0, 4, 'D', 4, 0)  # Crosses first arrow
        ]
        
        crossings = ConflictDetector.check_arrow_crossings(arrows)
        self.assertEqual(len(crossings), 1)
        self.assertEqual(crossings[0][:4], ('A', 'B', 'C', 'D'))


class TestCheckArrowThroughText(unittest.TestCase):
    """Test check_arrow_through_text static method."""
    
    def test_no_arrow_through_text(self):
        """Test when arrows don't pass through any text."""
        arrows = [('A', 0, 0, 'B', 4, 0)]
        positions = {
            'A': (0, 0),
            'B': (4, 0),
            'C': (2, 5)  # Far away
        }
        
        conflicts = ConflictDetector.check_arrow_through_text(arrows, positions)
        self.assertEqual(len(conflicts), 0)
    
    def test_arrow_through_text_detected(self):
        """Test detection of arrow passing through text box."""
        arrows = [('A', 0, 0, 'C', 4, 0)]
        positions = {
            'A': (0, 0),
            'B': (2, 0),  # B is between A and C on same level
            'C': (4, 0)
        }
        
        conflicts = ConflictDetector.check_arrow_through_text(arrows, positions)
        # Should detect B as being in the path
        self.assertGreater(len(conflicts), 0)
    
    def test_skip_source_and_target(self):
        """Test that source and target nodes are skipped."""
        arrows = [('A', 0, 0, 'B', 4, 0)]
        positions = {
            'A': (0, 0),
            'B': (4, 0)
        }
        
        conflicts = ConflictDetector.check_arrow_through_text(arrows, positions)
        # A and B should be skipped
        self.assertEqual(len(conflicts), 0)


class TestDetectAllConflicts(unittest.TestCase):
    """Test detect_all_conflicts method."""
    
    def test_detect_all_conflicts_none(self):
        """Test when no conflicts exist."""
        node_positions = {
            'A': ('node_a', 0, 0),
            'B': ('node_b', 5, 0)
        }
        links = {'A': 'B'}
        
        text_overlaps, arrow_crossings, arrow_through_text = ConflictDetector.detect_all_conflicts(
            node_positions, links
        )
        
        self.assertEqual(len(text_overlaps), 0)
        self.assertEqual(len(arrow_crossings), 0)
        self.assertEqual(len(arrow_through_text), 0)
    
    def test_detect_all_conflicts_with_overlaps(self):
        """Test detection of text overlaps."""
        node_positions = {
            'A': ('node_a', 0, 0),
            'B': ('node_b', 0.3, 0)  # Overlapping
        }
        links = {}
        
        text_overlaps, arrow_crossings, arrow_through_text = ConflictDetector.detect_all_conflicts(
            node_positions, links
        )
        
        self.assertGreater(len(text_overlaps), 0)


if __name__ == '__main__':
    unittest.main()
