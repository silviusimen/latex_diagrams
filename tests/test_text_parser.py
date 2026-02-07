#!/usr/bin/env python3
"""
Tests for the text format parser.
"""

import unittest
from latex_diagram_generator import parse_text_format


class TestTextFormatParser(unittest.TestCase):
    def test_export_input_with_positions(self):
            """Test exporting input file with rendered positions."""
            import os
            from latex_diagram_generator import DiagramGenerator
            text = """
            [A B] underline
            C
            # Links
            A -> C
            """
            spec = parse_text_format(text)
            generator = DiagramGenerator(spec)
            output_path = 'test_with_positions.txt'
            generator.export_input_with_positions(output_path)
            with open(output_path, 'r') as f:
                    content = f.read()
            os.remove(output_path)
            self.assertIn('at (', content)

    def test_group_with_position_override(self):
        """Test parsing group with at (x, y) position override."""
        text = """
        # Groups
        [A B C] at (5, 11)
        D at (2.5, 7)
        """
        spec = parse_text_format(text)
        self.assertEqual(len(spec['groups']), 2)
        group1 = spec['groups'][0]
        group2 = spec['groups'][1]
        self.assertIn('override_position', group1)
        self.assertEqual(group1['override_position'], (5.0, 11.0))
        self.assertIn('override_position', group2)
        self.assertEqual(group2['override_position'], (2.5, 7.0))
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


class TestTextParserEdgeCases(unittest.TestCase):
    """Test edge cases and branch coverage for text parser."""
    
    def test_mixed_order_groups_and_links(self):
        """Test when groups and links are mixed without section headers."""
        text = """
A
B -> C
C
D -> E
E
"""
        spec = parse_text_format(text)
        
        # Should correctly identify groups and links
        self.assertEqual(len(spec['groups']), 3)  # A, C, E
        self.assertEqual(len(spec['links']), 2)  # B->C, D->E
    
    def test_multi_element_group_without_underline(self):
        """Test multi-element group without underline modifier."""
        text = """
[A B C]
"""
        spec = parse_text_format(text)
        
        self.assertEqual(len(spec['groups']), 1)
        self.assertIn('elements', spec['groups'][0])
        self.assertEqual(spec['groups'][0]['elements'], ['A', 'B', 'C'])
        self.assertNotIn('underline', spec['groups'][0])
    
    def test_empty_input(self):
        """Test parsing empty input."""
        text = ""
        spec = parse_text_format(text)
        
        self.assertEqual(len(spec['groups']), 0)
        self.assertEqual(len(spec['links']), 0)
    
    def test_only_comments(self):
        """Test file with only comments."""
        text = """
# This is a comment
# Another comment
# Yet another comment
"""
        spec = parse_text_format(text)
        
        self.assertEqual(len(spec['groups']), 0)
        self.assertEqual(len(spec['links']), 0)
    
    def test_complex_link_chain(self):
        """Test complex link chain."""
        text = """
A
B
C
D
E

A -> B -> C -> D -> E
"""
        spec = parse_text_format(text)
        
        # Should create 4 links in chain
        self.assertEqual(len(spec['links']), 4)
        self.assertEqual(spec['links']['A'], 'B')
        self.assertEqual(spec['links']['B'], 'C')
        self.assertEqual(spec['links']['C'], 'D')
        self.assertEqual(spec['links']['D'], 'E')
    
    def test_multiple_multi_element_groups(self):
        """Test multiple multi-element groups."""
        text = """
[A B] underline
[C D]
[E F G] underline
"""
        spec = parse_text_format(text)
        
        self.assertEqual(len(spec['groups']), 3)
        self.assertTrue(spec['groups'][0].get('underline', False))
        self.assertFalse(spec['groups'][1].get('underline', False))
        self.assertTrue(spec['groups'][2].get('underline', False))
    
    def test_group_link_with_multiple_targets(self):
        """Test link from multi-element group."""
        text = """
[A B C]
D

[A B C] -> D
"""
        spec = parse_text_format(text)
        
        self.assertEqual(len(spec['groups']), 2)
        self.assertEqual(len(spec['links']), 1)
        
        # Multi-element group should have auto-generated name
        group_name = spec['groups'][0]['name']
        self.assertIn('group_', group_name)
        self.assertEqual(spec['links'][group_name], 'D')
    
    def test_special_characters_in_elements(self):
        """Test elements with special characters."""
        text = """
P1
P2+P3
[P4 + P5]

P1 -> P2+P3
"""
        spec = parse_text_format(text)
        
        # Should handle special characters
        self.assertGreater(len(spec['groups']), 0)
        self.assertGreater(len(spec['links']), 0)
    
    def test_section_headers_case_insensitive(self):
        """Test that section headers are case insensitive."""
        text = """
# GROUPS
A

# LINKS
A -> B
B
"""
        spec = parse_text_format(text)
        
        self.assertEqual(len(spec['groups']), 2)
        self.assertEqual(len(spec['links']), 1)


class TestTextParserNormalization(unittest.TestCase):
    """Test element normalization and parsing."""
    
    def test_whitespace_handling(self):
        """Test handling of extra whitespace."""
        text = """
   A   
  B  

  A   ->   B  
"""
        spec = parse_text_format(text)
        
        self.assertEqual(len(spec['groups']), 2)
        self.assertEqual(spec['groups'][0]['name'], 'A')
        self.assertEqual(spec['groups'][1]['name'], 'B')
    
    def test_multi_element_group_whitespace(self):
        """Test multi-element group with extra whitespace."""
        text = """
[  A   B   C  ]
"""
        spec = parse_text_format(text)
        
        self.assertEqual(len(spec['groups']), 1)
        self.assertEqual(spec['groups'][0]['elements'], ['A', 'B', 'C'])
    
    def test_comment_lines(self):
        """Test that lines starting with # are treated as section headers."""
        text = """
A
B
"""
        spec = parse_text_format(text)
        
        # Should parse A and B as groups
        self.assertEqual(len(spec['groups']), 2)
    
    def test_empty_lines_ignored(self):
        """Test that empty lines are properly handled."""
        text = """
A

B


C
"""
        spec = parse_text_format(text)
        
        self.assertEqual(len(spec['groups']), 3)
    
    def test_arrow_variations(self):
        """Test different arrow syntaxes."""
        text = """
A
B
C
A->B
B->C
"""
        spec = parse_text_format(text)
        
        # Should recognize -> as arrows
        self.assertEqual(len(spec['groups']), 3)
        # Check that links were created
        self.assertEqual(len(spec['links']), 2)
        self.assertIn('A', spec['links'])
        self.assertIn('B', spec['links'])
    
    def test_underline_flag_setting(self):
        """Test that underline flag is set on group (line 140)."""
        text = """
# Groups
[A B C] underline
"""
        spec = parse_text_format(text)
        
        # Should have one group with underline flag set
        self.assertEqual(len(spec['groups']), 1)
        self.assertTrue(spec['groups'][0].get('underline', False))
        self.assertEqual(spec['groups'][0]['elements'], ['A', 'B', 'C'])
    
    def test_invalid_link_chain(self):
        """Test parsing invalid link chains with less than 2 parts (line 200)."""
        text = """
# Groups
A
B

# Links
C
"""
        spec = parse_text_format(text)
        
        # "C" without "->" will be treated as a group first, but when parsing as link
        # it will split into just ['C'] which is < 2 parts
        # The parser should return early (line 200) and not add a link
        self.assertIn('A', [g['name'] for g in spec['groups']])
        self.assertIn('B', [g['name'] for g in spec['groups']])
        # C might be added as a group or ignored as a link
        # The key is that no link is created from the invalid line
        # and the code doesn't crash
        self.assertNotIn('C', spec['links'])
    
    def test_element_normalization_fallback(self):
        """Test element normalization with empty brackets fallback (line 229)."""
        text = """
# Groups
[]
A
B
"""
        spec = parse_text_format(text)
        
        # Empty bracket should be handled gracefully
        # Should have at least the non-empty groups
        self.assertGreaterEqual(len(spec['groups']), 2)
        # Check that valid groups are present
        group_names = [g['name'] for g in spec['groups']]
        self.assertIn('A', group_names)
        self.assertIn('B', group_names)


if __name__ == '__main__':
    unittest.main()
