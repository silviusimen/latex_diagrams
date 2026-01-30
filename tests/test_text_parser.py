#!/usr/bin/env python3
"""
Tests for the text format parser.
"""

import unittest
from latex_diagram_generator import parse_text_format


class TestTextFormatParser(unittest.TestCase):
    """Test cases for text format parser."""
    
    def test_simple_groups(self):
        """Test parsing simple single-element groups."""
        text = """
# Groups
A
B
C
"""
        spec = parse_text_format(text)
        
        self.assertEqual(len(spec['groups']), 3)
        self.assertEqual(spec['groups'][0]['name'], 'A')
        self.assertEqual(spec['groups'][1]['name'], 'B')
        self.assertEqual(spec['groups'][2]['name'], 'C')
    
    def test_multi_element_group(self):
        """Test parsing multi-element groups with brackets."""
        text = """
# Groups
[A B C]
"""
        spec = parse_text_format(text)
        
        self.assertEqual(len(spec['groups']), 1)
        self.assertIn('elements', spec['groups'][0])
        self.assertEqual(spec['groups'][0]['elements'], ['A', 'B', 'C'])
    
    def test_underline_modifier(self):
        """Test parsing underline modifier."""
        text = """
# Groups
A
[B C D] underline
E
"""
        spec = parse_text_format(text)
        
        self.assertEqual(len(spec['groups']), 3)
        self.assertNotIn('underline', spec['groups'][0])
        self.assertTrue(spec['groups'][1].get('underline', False))
        self.assertNotIn('underline', spec['groups'][2])
    
    def test_simple_links(self):
        """Test parsing simple links."""
        text = """
# Groups
A
B
C

# Links
A -> B
B -> C
"""
        spec = parse_text_format(text)
        
        self.assertEqual(len(spec['links']), 2)
        self.assertEqual(spec['links']['A'], 'B')
        self.assertEqual(spec['links']['B'], 'C')
    
    def test_chained_links(self):
        """Test parsing chained links."""
        text = """
# Groups
A
B
C
D

# Links
A -> B -> C -> D
"""
        spec = parse_text_format(text)
        
        self.assertEqual(len(spec['links']), 3)
        self.assertEqual(spec['links']['A'], 'B')
        self.assertEqual(spec['links']['B'], 'C')
        self.assertEqual(spec['links']['C'], 'D')
    
    def test_group_links(self):
        """Test parsing links from multi-element groups."""
        text = """
# Groups
A
[B C D] underline
E

# Links
A -> B
[B C D] -> E
"""
        spec = parse_text_format(text)
        
        self.assertEqual(len(spec['links']), 2)
        self.assertEqual(spec['links']['A'], 'B')
        # The group should be referenced by its auto-generated name
        group_name = spec['groups'][1]['name']
        self.assertEqual(spec['links'][group_name], 'E')
    
    def test_example_file(self):
        """Test parsing the example file format."""
        text = """
# Groups (multi-element groups use [brackets])
P1
P2
P3
[P4 + P5] underline
C

# Links
P1 -> P2 -> P3 -> P4
[P4 + P5] -> C
"""
        spec = parse_text_format(text)
        
        # Check groups
        self.assertEqual(len(spec['groups']), 5)
        self.assertEqual(spec['groups'][0]['name'], 'P1')
        self.assertEqual(spec['groups'][1]['name'], 'P2')
        self.assertEqual(spec['groups'][2]['name'], 'P3')
        self.assertIn('elements', spec['groups'][3])
        self.assertEqual(spec['groups'][3]['elements'], ['P4', '+', 'P5'])
        self.assertTrue(spec['groups'][3].get('underline', False))
        self.assertEqual(spec['groups'][4]['name'], 'C')
        
        # Check links
        self.assertEqual(len(spec['links']), 4)
        self.assertEqual(spec['links']['P1'], 'P2')
        self.assertEqual(spec['links']['P2'], 'P3')
        self.assertEqual(spec['links']['P3'], 'P4')
        
        # The multi-element group link
        group_name = spec['groups'][3]['name']
        self.assertEqual(spec['links'][group_name], 'C')
    
    def test_without_section_headers(self):
        """Test parsing without explicit section headers."""
        text = """
A
B
[C D] underline

A -> B -> C
[C D] -> E
E
"""
        spec = parse_text_format(text)
        
        # Should still parse correctly
        self.assertGreater(len(spec['groups']), 0)
        self.assertGreater(len(spec['links']), 0)
    
    def test_comments_and_empty_lines(self):
        """Test handling of comments and empty lines."""
        text = """
# This is a comment about groups

A

B

# Another comment

# Links section
A -> B
"""
        spec = parse_text_format(text)
        
        self.assertEqual(len(spec['groups']), 2)
        self.assertEqual(len(spec['links']), 1)


if __name__ == '__main__':
    unittest.main()
