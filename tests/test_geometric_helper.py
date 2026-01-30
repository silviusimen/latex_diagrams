#!/usr/bin/env python3
"""
Unit tests for GeometricHelper class.
"""

import unittest
from latex_diagram_generator.geometric_helper import GeometricHelper


class TestSegmentsIntersect(unittest.TestCase):
    """Test segments_intersect static method."""
    
    def test_intersecting_segments(self):
        """Test detection of intersecting line segments."""
        # X pattern
        result = GeometricHelper.segments_intersect(0, 0, 4, 4, 0, 4, 4, 0)
        self.assertTrue(result)
    
    def test_non_intersecting_segments(self):
        """Test parallel non-intersecting segments."""
        result = GeometricHelper.segments_intersect(0, 0, 2, 0, 0, 1, 2, 1)
        self.assertFalse(result)
    
    def test_segments_same_line(self):
        """Test segments on same line."""
        result = GeometricHelper.segments_intersect(0, 0, 2, 0, 3, 0, 5, 0)
        self.assertFalse(result)


class TestLineIntersectsBox(unittest.TestCase):
    """Test line_intersects_box static method."""
    
    def test_line_start_inside_box(self):
        """Test when line start point is inside box."""
        result = GeometricHelper.line_intersects_box(
            1, 1, 5, 5,  # Line
            0, 0, 2, 2   # Box
        )
        self.assertTrue(result)
    
    def test_line_end_inside_box(self):
        """Test when line end point is inside box."""
        result = GeometricHelper.line_intersects_box(
            -1, -1, 1, 1,  # Line
            0, 0, 2, 2     # Box
        )
        self.assertTrue(result)
    
    def test_line_passes_through_box(self):
        """Test when line passes through box."""
        result = GeometricHelper.line_intersects_box(
            0, 0.5, 3, 0.5,  # Horizontal line through box
            1, 0, 2, 1       # Box
        )
        self.assertTrue(result)
    
    def test_line_misses_box(self):
        """Test when line doesn't intersect box."""
        result = GeometricHelper.line_intersects_box(
            0, 0, 1, 0,  # Line
            2, 2, 3, 3   # Box far away
        )
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
