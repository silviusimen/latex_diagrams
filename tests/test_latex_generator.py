#!/usr/bin/env python3
"""Unit tests for LaTeX generator."""

import unittest
import tempfile
import os
from latex_diagram_generator.latex_generator import LaTeXGenerator


class TestLatexGenerator(unittest.TestCase):
    """Tests for LaTeXGenerator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary template file
        self.temp_template = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.tex')
        self.temp_template.write("""\\documentclass{article}
\\begin{document}
\\begin{tikzpicture}[x=1.00cm, y=1cm, fontsize{12}{12}]
[[nodes]]
[[underlines]]
[[links]]
\\end{tikzpicture}
\\end{document}
""")
        self.temp_template.close()
        self.template_path = self.temp_template.name
        self.gen = LaTeXGenerator(self.template_path, within_group_spacing=2.0)
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.template_path):
            os.unlink(self.template_path)
    
    # Tests for __init__
    def test_init_sets_template_path(self):
        """Test that init sets template path correctly."""
        gen = LaTeXGenerator("/path/to/template.tex")
        self.assertEqual(gen.template_path, "/path/to/template.tex")
    
    def test_init_sets_default_spacing(self):
        """Test that init sets default within group spacing."""
        gen = LaTeXGenerator("/path/to/template.tex")
        self.assertEqual(gen.WITHIN_GROUP_SPACING, 2.0)
    
    def test_init_sets_custom_spacing(self):
        """Test that init accepts custom spacing value."""
        gen = LaTeXGenerator("/path/to/template.tex", within_group_spacing=3.5)
        self.assertEqual(gen.WITHIN_GROUP_SPACING, 3.5)
    
    # Tests for _calculate_spacing_and_font
    def test_calculate_spacing_and_font_with_empty_positions(self):
        """Test spacing calculation with empty positions dict."""
        positions = {}
        x_spacing, font_size = self.gen._calculate_spacing_and_font(positions)
        self.assertEqual(x_spacing, 1.0)
        self.assertEqual(font_size, 14)
    
    def test_calculate_spacing_and_font_with_narrow_diagram(self):
        """Test spacing calculation for narrow diagram (high spacing)."""
        positions = {
            'Group1': (0, ['A']),
            'Group2': (1, ['B'])
        }
        x_spacing, font_size = self.gen._calculate_spacing_and_font(positions)
        self.assertGreaterEqual(x_spacing, 1.0)
        self.assertEqual(font_size, 14)
    
    def test_calculate_spacing_and_font_with_wide_diagram(self):
        """Test spacing calculation for wide diagram (low spacing)."""
        positions = {
            'Group1': (0, ['A', 'B', 'C', 'D', 'E', 'F']),
            'Group2': (10, ['G', 'H', 'I'])
        }
        x_spacing, font_size = self.gen._calculate_spacing_and_font(positions)
        self.assertLess(x_spacing, 1.0)
        # Font size should be 10 or 12 depending on exact spacing
        self.assertIn(font_size, [10, 12])
    
    def test_calculate_spacing_and_font_clamping_min(self):
        """Test that x_spacing is clamped to minimum 0.5."""
        # Very wide diagram
        positions = {
            'Group1': (0, ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'])
        }
        positions['Group1'] = (0, positions['Group1'][1])
        positions['Group2'] = (50, ['K'])
        x_spacing, _ = self.gen._calculate_spacing_and_font(positions)
        self.assertGreaterEqual(x_spacing, 0.5)
    
    def test_calculate_spacing_and_font_clamping_max(self):
        """Test that x_spacing is clamped to maximum 1.5."""
        positions = {
            'Group1': (0, ['A'])
        }
        x_spacing, _ = self.gen._calculate_spacing_and_font(positions)
        self.assertLessEqual(x_spacing, 1.5)
    
    def test_calculate_spacing_and_font_size_small(self):
        """Test font size is 10 when spacing < 0.8."""
        positions = {
            'Group1': (0, ['A', 'B', 'C', 'D', 'E', 'F']),
            'Group2': (20, ['G'])
        }
        _, font_size = self.gen._calculate_spacing_and_font(positions)
        self.assertEqual(font_size, 10)
    
    def test_calculate_spacing_and_font_size_medium(self):
        """Test font size is 12 when 0.8 <= spacing < 1.0."""
        positions = {
            'Group1': (0, ['A', 'B', 'C']),
            'Group2': (10, ['D'])
        }
        x_spacing, font_size = self.gen._calculate_spacing_and_font(positions)
        if 0.8 <= x_spacing < 1.0:
            self.assertEqual(font_size, 12)
    
    # Tests for _sanitize_node_id
    def test_sanitize_node_id_with_plus(self):
        """Test sanitization of node IDs with plus signs."""
        self.assertEqual(self.gen._sanitize_node_id("A+"), "aplus")
    
    def test_sanitize_node_id_with_minus(self):
        """Test sanitization of node IDs with minus signs."""
        self.assertEqual(self.gen._sanitize_node_id("B-"), "bminus")
    
    def test_sanitize_node_id_with_apostrophe(self):
        """Test sanitization of node IDs with apostrophes."""
        self.assertEqual(self.gen._sanitize_node_id("P'"), "pp")
    
    def test_sanitize_node_id_with_dot(self):
        """Test sanitization of node IDs with dots."""
        self.assertEqual(self.gen._sanitize_node_id("N.1"), "n_1")
    
    def test_sanitize_node_id_with_space(self):
        """Test sanitization of node IDs with spaces."""
        self.assertEqual(self.gen._sanitize_node_id("Node Name"), "node_name")
    
    def test_sanitize_node_id_lowercase_conversion(self):
        """Test that node IDs are converted to lowercase."""
        self.assertEqual(self.gen._sanitize_node_id("ABC"), "abc")
    
    def test_sanitize_node_id_complex(self):
        """Test sanitization with multiple special characters."""
        self.assertEqual(self.gen._sanitize_node_id("A+ B-C'.D"), "aplus_bminuscp_d")
    
    # Tests for _create_node_for_element
    def test_create_node_for_element_basic(self):
        """Test creating a node for basic element."""
        node_line, node_id, elem = self.gen._create_node_for_element("A", 0.0, 5)
        self.assertEqual(elem, "A")
        self.assertEqual(node_id, "a_0_5")
        self.assertIn("\\node (a_0_5)", node_line)
        self.assertIn("at (0.0, 5)", node_line)
        self.assertIn("{A}", node_line)
    
    def test_create_node_for_element_with_special_chars(self):
        """Test creating a node for element with special characters."""
        node_line, node_id, elem = self.gen._create_node_for_element("P'", 2.5, 3)
        self.assertEqual(elem, "P'")
        self.assertEqual(node_id, "pp_2_3")
        self.assertIn("\\node (pp_2_3)", node_line)
    
    def test_create_node_for_element_float_coords(self):
        """Test creating a node with floating point coordinates."""
        node_line, node_id, elem = self.gen._create_node_for_element("X", 3.7, 2)
        self.assertEqual(node_id, "x_3_2")  # Coordinates are cast to int in node_id
        self.assertIn("at (3.7, 2)", node_line)
    
    # Tests for _get_center_node_for_underlined_group
    def test_get_center_node_underlined_group_with_underline(self):
        """Test getting center node for underlined group."""
        group_obj = {'underline': True}
        elements = ['A', 'B', 'C']
        center_node = self.gen._get_center_node_for_underlined_group(
            'Group1', group_obj, elements, 0.0, 5
        )
        self.assertEqual(center_node, "b_2_5")  # Middle element B at x=2
    
    def test_get_center_node_underlined_group_without_underline(self):
        """Test getting center node for non-underlined group."""
        group_obj = {'underline': False}
        elements = ['A', 'B', 'C']
        center_node = self.gen._get_center_node_for_underlined_group(
            'Group1', group_obj, elements, 0.0, 5
        )
        self.assertIsNone(center_node)
    
    def test_get_center_node_underlined_group_empty_elements(self):
        """Test getting center node with empty elements list."""
        group_obj = {'underline': True}
        elements = []
        center_node = self.gen._get_center_node_for_underlined_group(
            'Group1', group_obj, elements, 0.0, 5
        )
        self.assertIsNone(center_node)
    
    def test_get_center_node_underlined_group_even_count(self):
        """Test center node selection with even number of elements."""
        group_obj = {'underline': True}
        elements = ['A', 'B', 'C', 'D']
        center_node = self.gen._get_center_node_for_underlined_group(
            'Group1', group_obj, elements, 0.0, 5
        )
        self.assertEqual(center_node, "c_4_5")  # Element at index 2
    
    # Tests for _generate_node_definitions
    def test_generate_node_definitions_single_group(self):
        """Test node generation for single group."""
        levels = {'Group1': 5}
        positions = {'Group1': (0.0, ['A', 'B'])}
        group_name_to_group = {'Group1': {}}
        
        nodes, node_positions, group_center_nodes = self.gen._generate_node_definitions(
            levels, positions, group_name_to_group
        )
        
        self.assertEqual(len(nodes), 2)
        self.assertEqual(len(node_positions), 2)
        self.assertIn('A', node_positions)
        self.assertIn('B', node_positions)
    
    def test_generate_node_definitions_multiple_groups(self):
        """Test node generation for multiple groups."""
        levels = {'Group1': 5, 'Group2': 3}
        positions = {
            'Group1': (0.0, ['A']),
            'Group2': (2.0, ['B', 'C'])
        }
        group_name_to_group = {'Group1': {}, 'Group2': {}}
        
        nodes, node_positions, group_center_nodes = self.gen._generate_node_definitions(
            levels, positions, group_name_to_group
        )
        
        self.assertEqual(len(nodes), 3)
        self.assertEqual(len(node_positions), 3)
    
    def test_generate_node_definitions_with_underlined_group(self):
        """Test that underlined groups get center node tracking."""
        levels = {'Group1': 5}
        positions = {'Group1': (0.0, ['A', 'B', 'C'])}
        group_name_to_group = {'Group1': {'underline': True}}
        
        nodes, node_positions, group_center_nodes = self.gen._generate_node_definitions(
            levels, positions, group_name_to_group
        )
        
        self.assertIn('Group1', group_center_nodes)
        self.assertEqual(group_center_nodes['Group1'], "b_2_5")
    
    def test_generate_node_definitions_node_positions_structure(self):
        """Test that node_positions has correct structure."""
        levels = {'Group1': 5}
        positions = {'Group1': (0.0, ['A'])}
        group_name_to_group = {'Group1': {}}
        
        nodes, node_positions, group_center_nodes = self.gen._generate_node_definitions(
            levels, positions, group_name_to_group
        )
        
        node_id, x, y = node_positions['A']
        self.assertEqual(node_id, "a_0_5")
        self.assertEqual(x, 0.0)
        self.assertEqual(y, 5)
    
    # Tests for _create_underline_for_group
    def test_create_underline_for_group_with_multiple_elements(self):
        """Test underline creation for group with multiple elements."""
        positions = {'Group1': (0.0, ['A', 'B', 'C'])}
        levels = {'Group1': 5}
        
        underline = self.gen._create_underline_for_group('Group1', positions, levels)
        
        self.assertIsNotNone(underline)
        self.assertIn("\\draw[blue]", underline)
        self.assertIn("a_0_5.south west", underline)
        self.assertIn("c_4_5.south east", underline)
    
    def test_create_underline_for_group_with_single_element(self):
        """Test that no underline is created for single element."""
        positions = {'Group1': (0.0, ['A'])}
        levels = {'Group1': 5}
        
        underline = self.gen._create_underline_for_group('Group1', positions, levels)
        
        self.assertIsNone(underline)
    
    # Tests for _generate_underlines
    def test_generate_underlines_with_underlined_group(self):
        """Test underline generation for underlined groups."""
        links = {'Group1': 'A'}
        positions = {'Group1': (0.0, ['X', 'Y', 'Z'])}
        levels = {'Group1': 5}
        group_name_to_group = {'Group1': {'underline': True}}
        element_to_group = {'X': 'Group1', 'Y': 'Group1', 'Z': 'Group1'}
        
        underlines = self.gen._generate_underlines(
            links, positions, levels, group_name_to_group, element_to_group
        )
        
        self.assertEqual(len(underlines), 1)
        self.assertIn("\\draw[blue]", underlines[0])
    
    def test_generate_underlines_without_underline_flag(self):
        """Test that no underlines are generated without underline flag."""
        links = {'Group1': 'A'}
        positions = {'Group1': (0.0, ['X', 'Y'])}
        levels = {'Group1': 5}
        group_name_to_group = {'Group1': {'underline': False}}
        element_to_group = {'X': 'Group1', 'Y': 'Group1'}
        
        underlines = self.gen._generate_underlines(
            links, positions, levels, group_name_to_group, element_to_group
        )
        
        self.assertEqual(len(underlines), 0)
    
    def test_generate_underlines_element_link_not_group(self):
        """Test that element links don't generate underlines."""
        links = {'X': 'A'}  # Link from element X, not group
        positions = {'Group1': (0.0, ['X', 'Y'])}
        levels = {'Group1': 5}
        group_name_to_group = {'Group1': {'underline': True}}
        element_to_group = {'X': 'Group1', 'Y': 'Group1'}
        
        underlines = self.gen._generate_underlines(
            links, positions, levels, group_name_to_group, element_to_group
        )
        
        self.assertEqual(len(underlines), 0)
    
    # Tests for _get_source_node_id
    def test_get_source_node_id_from_underlined_group(self):
        """Test getting source node from underlined group."""
        element_to_group = {'A': 'Group1'}
        group_name_to_group = {'Group1': {'underline': True}}
        group_center_nodes = {'Group1': 'center_node_id'}
        positions = {}
        levels = {}
        node_positions = {}
        
        source_id = self.gen._get_source_node_id(
            'Group1', element_to_group, group_name_to_group,
            group_center_nodes, positions, levels, node_positions
        )
        
        self.assertEqual(source_id, 'center_node_id')
    
    def test_get_source_node_id_from_underlined_group_fallback(self):
        """Test fallback for underlined group without center node."""
        element_to_group = {'A': 'Group1'}
        group_name_to_group = {'Group1': {'underline': True}}
        group_center_nodes = {}
        positions = {'Group1': (0.0, ['A'])}
        levels = {'Group1': 5}
        node_positions = {}
        
        source_id = self.gen._get_source_node_id(
            'Group1', element_to_group, group_name_to_group,
            group_center_nodes, positions, levels, node_positions
        )
        
        self.assertEqual(source_id, 'a_0_5')
    
    def test_get_source_node_id_from_regular_element(self):
        """Test getting source node from regular element."""
        element_to_group = {'A': 'Group1'}
        group_name_to_group = {'Group1': {'underline': False}}
        group_center_nodes = {}
        positions = {}
        levels = {}
        node_positions = {'A': ('a_0_5', 0.0, 5)}
        
        source_id = self.gen._get_source_node_id(
            'A', element_to_group, group_name_to_group,
            group_center_nodes, positions, levels, node_positions
        )
        
        self.assertEqual(source_id, 'a_0_5')
    
    def test_get_source_node_id_missing_element(self):
        """Test that missing element returns None when not in node_positions."""
        element_to_group = {'Missing': 'Group1'}
        group_name_to_group = {'Group1': {'underline': False}}
        group_center_nodes = {}
        positions = {}
        levels = {}
        node_positions = {}  # Missing is not in node_positions
        
        source_id = self.gen._get_source_node_id(
            'Missing', element_to_group, group_name_to_group,
            group_center_nodes, positions, levels, node_positions
        )
        
        self.assertIsNone(source_id)
    
    # Tests for _generate_link_arrows
    def test_generate_link_arrows_basic(self):
        """Test basic arrow generation."""
        links = {'A': 'B'}
        node_positions = {
            'A': ('a_0_5', 0.0, 5),
            'B': ('b_2_3', 2.0, 3)
        }
        element_to_group = {'A': 'Group1', 'B': 'Group2'}
        group_name_to_group = {'Group1': {}, 'Group2': {}}
        group_center_nodes = {}
        positions = {}
        levels = {}
        
        arrows = self.gen._generate_link_arrows(
            links, node_positions, element_to_group, group_name_to_group,
            group_center_nodes, positions, levels
        )
        
        self.assertEqual(len(arrows), 1)
        self.assertIn("\\draw[->, blue] (a_0_5) -- (b_2_3);", arrows[0])
    
    def test_generate_link_arrows_missing_target(self):
        """Test that missing target is skipped."""
        links = {'A': 'Missing'}
        node_positions = {'A': ('a_0_5', 0.0, 5)}
        element_to_group = {'A': 'Group1'}
        group_name_to_group = {'Group1': {}}
        group_center_nodes = {}
        positions = {}
        levels = {}
        
        arrows = self.gen._generate_link_arrows(
            links, node_positions, element_to_group, group_name_to_group,
            group_center_nodes, positions, levels
        )
        
        self.assertEqual(len(arrows), 0)
    
    def test_generate_link_arrows_missing_source(self):
        """Test that missing source is skipped."""
        links = {'Missing': 'B'}
        node_positions = {'B': ('b_2_3', 2.0, 3)}
        element_to_group = {'Missing': 'Group1', 'B': 'Group2'}
        group_name_to_group = {'Group1': {}, 'Group2': {}}
        group_center_nodes = {}
        positions = {}
        levels = {}
        
        arrows = self.gen._generate_link_arrows(
            links, node_positions, element_to_group, group_name_to_group,
            group_center_nodes, positions, levels
        )
        
        self.assertEqual(len(arrows), 0)
    
    # Tests for _apply_template
    def test_apply_template_basic(self):
        """Test basic template application."""
        template = "[[nodes]]\n[[links]]\n[[underlines]]\nx=1.00cm\nfontsize{12}{12}"
        nodes = ["node1", "node2"]
        links = ["link1"]
        underlines = ["underline1"]
        
        result = self.gen._apply_template(template, nodes, links, underlines, 1.5, 14)
        
        self.assertIn("node1", result)
        self.assertIn("node2", result)
        self.assertIn("link1", result)
        self.assertIn("underline1", result)
        self.assertIn("x=1.50cm", result)
        self.assertIn("fontsize{14}{14}", result)
    
    def test_apply_template_empty_lists(self):
        """Test template application with empty component lists."""
        template = "[[nodes]]\n[[links]]\n[[underlines]]"
        
        result = self.gen._apply_template(template, [], [], [], 1.0, 12)
        
        self.assertNotIn("[[nodes]]", result)
        self.assertNotIn("[[links]]", result)
        self.assertNotIn("[[underlines]]", result)
    
    def test_apply_template_spacing_replacement(self):
        """Test that x-spacing is properly replaced."""
        template = "x=1.00cm"
        
        result = self.gen._apply_template(template, [], [], [], 0.75, 12)
        
        self.assertIn("x=0.75cm", result)
        self.assertNotIn("x=1.00cm", result)
    
    def test_apply_template_font_size_replacement(self):
        """Test that font size is properly replaced."""
        template = "fontsize{12}{12}"
        
        result = self.gen._apply_template(template, [], [], [], 1.0, 10)
        
        self.assertIn("fontsize{10}{10}", result)
        self.assertNotIn("fontsize{12}{12}", result)
    
    # Tests for _load_template
    def test_load_template_success(self):
        """Test successful template loading."""
        content = self.gen._load_template()
        self.assertIn("\\documentclass", content)
        self.assertIn("[[nodes]]", content)
    
    def test_load_template_file_not_found(self):
        """Test that FileNotFoundError is raised for missing template."""
        gen = LaTeXGenerator("/nonexistent/template.tex")
        with self.assertRaises(FileNotFoundError) as cm:
            gen._load_template()
        self.assertIn("Template file not found", str(cm.exception))
    
    # Tests for _generate_all_components
    def test_generate_all_components_integration(self):
        """Test integration of all component generation."""
        levels = {'Group1': 5, 'Group2': 3}
        positions = {
            'Group1': (0.0, ['A', 'B']),
            'Group2': (2.0, ['C'])
        }
        links = {'A': 'C'}
        group_name_to_group = {
            'Group1': {'underline': True},
            'Group2': {}
        }
        element_to_group = {'A': 'Group1', 'B': 'Group1', 'C': 'Group2'}
        
        nodes, underlines, links_code = self.gen._generate_all_components(
            levels, positions, links, group_name_to_group, element_to_group
        )
        
        self.assertEqual(len(nodes), 3)  # A, B, C
        self.assertGreater(len(links_code), 0)  # At least one arrow
    
    # Tests for generate (main method)
    def test_generate_complete_workflow(self):
        """Test complete LaTeX generation workflow."""
        levels = {'Group1': 5}
        positions = {'Group1': (0.0, ['A', 'B'])}
        links = {'A': 'B'}
        group_name_to_group = {'Group1': {}}
        element_to_group = {'A': 'Group1', 'B': 'Group1'}
        
        latex_code = self.gen.generate(
            levels, positions, links, group_name_to_group, element_to_group
        )
        
        self.assertIn("\\documentclass", latex_code)
        self.assertIn("\\node", latex_code)
        self.assertIn("\\draw", latex_code)
        self.assertIn("tikzpicture", latex_code)


if __name__ == '__main__':
    unittest.main()
