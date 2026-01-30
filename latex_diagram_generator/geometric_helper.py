#!/usr/bin/env python3
"""
Geometric utilities for intersection and collision detection.
"""


class GeometricHelper:
    """Handles geometric calculations for intersection detection."""
    
    @staticmethod
    def segments_intersect(x1, y1, x2, y2, x3, y3, x4, y4):
        """
        Check if two line segments intersect.
        
        Uses the orientation method to check if segments (x1,y1)-(x2,y2) and
        (x3,y3)-(x4,y4) intersect.
        
        Args:
            x1, y1: Start point of first segment
            x2, y2: End point of first segment
            x3, y3: Start point of second segment
            x4, y4: End point of second segment
            
        Returns:
            True if segments intersect
        """
        def ccw(ax, ay, bx, by, cx, cy):
            return (cy - ay) * (bx - ax) > (by - ay) * (cx - ax)
        
        return (ccw(x1, y1, x3, y3, x4, y4) != ccw(x2, y2, x3, y3, x4, y4) and
                ccw(x1, y1, x2, y2, x3, y3) != ccw(x1, y1, x2, y2, x4, y4))
    
    @staticmethod
    def line_intersects_box(x1, y1, x2, y2, box_min_x, box_min_y, box_max_x, box_max_y):
        """
        Check if line segment intersects with a rectangular box.
        
        Args:
            x1, y1: Start point of line
            x2, y2: End point of line
            box_min_x, box_min_y: Bottom-left corner of box
            box_max_x, box_max_y: Top-right corner of box
            
        Returns:
            True if line intersects box
        """
        # Check if either endpoint is inside box
        if (box_min_x <= x1 <= box_max_x and box_min_y <= y1 <= box_max_y):
            return True
        if (box_min_x <= x2 <= box_max_x and box_min_y <= y2 <= box_max_y):
            return True
        
        # Check intersection with each edge of the box
        edges = [
            (box_min_x, box_min_y, box_max_x, box_min_y),  # bottom
            (box_max_x, box_min_y, box_max_x, box_max_y),  # right
            (box_max_x, box_max_y, box_min_x, box_max_y),  # top
            (box_min_x, box_max_y, box_min_x, box_min_y),  # left
        ]
        
        for ex1, ey1, ex2, ey2 in edges:
            if GeometricHelper.segments_intersect(x1, y1, x2, y2, ex1, ey1, ex2, ey2):
                return True
        
        return False
