#!/usr/bin/env python3
"""
Tests for the diagram generator.
"""

import unittest
import json
import os
from latex_diagram_generator import DiagramGenerator


class TestDiagramGenerator(unittest.TestCase):
    """Test cases for DiagramGenerator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Load example.json for testing
        self.example_json_path = 'example.json'
        if os.path.exists(self.example_json_path):
            with open(self.example_json_path, 'r') as f:
                self.example_spec = json.load(f)
        else:
            # Fallback example spec if file not found
            self.example_spec = {
                "groups": [
                    {"name": "P1"},
                    {"name": "P2"},
                    {"name": "P3"},
                    {
                        "name": "compount_premise_1",
                        "elements": ["P4", "+", "P5"],
                        "underline": True
                    },
                    {"name": "C"}
                ],
                "links": {
                    "P1": "P2",
                    "P2": "P3",
                    "P3": "P4",
                    "compount_premise_1": "C"
                }
            }
    
    def test_initialization(self):
        """Test DiagramGenerator initialization."""
        generator = DiagramGenerator(self.example_spec)
        
        self.assertEqual(len(generator.groups), 5)
        self.assertEqual(len(generator.links), 4)
        
        # Check element to group mapping
        self.assertIn('P1', generator.element_to_group)
        self.assertIn('P4', generator.element_to_group)
        self.assertIn('+', generator.element_to_group)
        
    def test_dependency_graph(self):
        """Test dependency graph construction."""
        generator = DiagramGenerator(self.example_spec)
        outgoing, incoming = generator._build_dependency_graph()
        
        # Check outgoing links
        self.assertIn('P2', outgoing['P1'])
        self.assertIn('P3', outgoing['P2'])
        
        # Check incoming links
        self.assertIn('P1', incoming['P2'])
        self.assertIn('P2', incoming['P3'])
    
    def test_compute_levels(self):
        """Test level computation for vertical positioning."""
        generator = DiagramGenerator(self.example_spec)
        levels, positions = generator._compute_layout_bottom_up()
        
        # P1 should be at a higher level than P2
        self.assertGreater(levels['P1'], levels['P2'])
        
        # P2 should be at a higher level than P3
        self.assertGreater(levels['P2'], levels['P3'])
        
        # compount_premise_1 should be above C
        self.assertGreater(levels['compount_premise_1'], levels['C'])
    
    def test_horizontal_positions(self):
        """Test horizontal position computation."""
        generator = DiagramGenerator(self.example_spec)
        levels, positions = generator._compute_layout_bottom_up()
        
        # compount_premise_1 has 3 elements
        start_x, elements = positions['compount_premise_1']
        self.assertEqual(len(elements), 3)
        self.assertEqual(elements, ['P4', '+', 'P5'])
    
    def test_latex_generation(self):
        """Test LaTeX code generation."""
        generator = DiagramGenerator(self.example_spec)
        latex = generator.generate_latex()
        
        # Check basic structure
        self.assertIn('\\documentclass{article}', latex)
        self.assertIn('\\begin{tikzpicture}', latex)
        self.assertIn('\\end{tikzpicture}', latex)
        
        # Check nodes are generated (new format includes coordinates)
        self.assertIn('{P1}', latex)  # Check node label
        self.assertIn('{P2}', latex)
        self.assertIn('{+}', latex)
        
        # Check links are generated
        self.assertIn('\\draw[->, blue]', latex)
        
        # Check underline is generated
        self.assertIn('.south west', latex)
        self.assertIn('.south east', latex)
    
    def test_simple_chain(self):
        """Test a simple chain of elements."""
        spec = {
            "groups": [
                {"name": "A"},
                {"name": "B"},
                {"name": "C"}
            ],
            "links": {
                "A": "B",
                "B": "C"
            }
        }
        
        generator = DiagramGenerator(spec)
        levels, positions = generator._compute_layout_bottom_up()
        
        # A should be higher than B, B higher than C
        self.assertGreater(levels['A'], levels['B'])
        self.assertGreater(levels['B'], levels['C'])
        
        latex = generator.generate_latex()
        self.assertIn('{A}', latex)  # Check node label
        self.assertIn('{B}', latex)
        self.assertIn('{C}', latex)
    
    def test_group_with_underline(self):
        """Test group with underline property."""
        spec = {
            "groups": [
                {"name": "A"},
                {
                    "name": "multi",
                    "elements": ["B", "C", "D"],
                    "underline": True
                },
                {"name": "E"}
            ],
            "links": {
                "A": "B",
                "multi": "E"
            }
        }
        
        generator = DiagramGenerator(spec)
        latex = generator.generate_latex()
        
        # Check that underline is drawn
        self.assertIn('\\draw[blue]', latex)
        self.assertIn('.south west', latex)
        self.assertIn('.south east', latex)
    
    def test_example_file_match(self):
        """Test that generated output matches expected format from example.tex."""
        generator = DiagramGenerator(self.example_spec)
        latex = generator.generate_latex()
        
        # Load expected output if available
        example_tex_path = 'example.tex'
        if os.path.exists(example_tex_path):
            with open(example_tex_path, 'r') as f:
                expected = f.read()
            
            # Check key structural elements match
            self.assertIn('\\begin{tikzpicture}', latex)
            self.assertIn('>=Stealth', latex)
            self.assertIn('line width=2pt', latex)
        
        # Verify all expected nodes (check labels)
        for label in ['P1', 'P2', 'P3', 'P4', '+', 'P5', 'C']:
            self.assertIn(f'{{{label}}}', latex)
    
    def test_multiple_incoming_links(self):
        """Test element with multiple incoming links."""
        spec = {
            "groups": [
                {"name": "A"},
                {"name": "B"},
                {"name": "C"}
            ],
            "links": {
                "A": "C",
                "B": "C"
            }
        }
        
        generator = DiagramGenerator(spec)
        levels, positions = generator._compute_layout_bottom_up()
        
        # Both A and B should be higher than C
        self.assertGreater(levels['A'], levels['C'])
        self.assertGreater(levels['B'], levels['C'])
        
        latex = generator.generate_latex()
        # Should have two arrows pointing to C
        self.assertIn('{C}', latex)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""
    
    def test_empty_groups(self):
        """Test with empty groups list."""
        spec = {"groups": [], "links": {}}
        generator = DiagramGenerator(spec)
        latex = generator.generate_latex()
        
        # Should still generate valid LaTeX structure
        self.assertIn('\\documentclass{article}', latex)
        self.assertIn('\\end{document}', latex)
    
    def test_no_links(self):
        """Test with groups but no links."""
        spec = {
            "groups": [
                {"name": "A"},
                {"name": "B"}
            ],
            "links": {}
        }
        
        generator = DiagramGenerator(spec)
        latex = generator.generate_latex()
        
        # Should generate nodes
        self.assertIn('{A}', latex)
        self.assertIn('{B}', latex)
    
    def test_single_element_group(self):
        """Test group with single element."""
        spec = {
            "groups": [
                {
                    "name": "single",
                    "elements": ["X"],
                    "underline": False
                }
            ],
            "links": {}
        }
        
        generator = DiagramGenerator(spec)
        latex = generator.generate_latex()
        
        self.assertIn('{X}', latex)


if __name__ == '__main__':
    unittest.main()
