#!/usr/bin/env python3
"""
LaTeX/TikZ Diagram Generator - Main Entry Point

This script generates LaTeX diagrams with TikZ based on a JSON or text input specification.
"""

import json
import argparse
from latex_diagram_generator import DiagramGenerator, parse_text_format


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Generate LaTeX/TikZ diagrams from JSON specifications'
    )
    parser.add_argument(
        'input_file',
        help='Path to input JSON file'
    )
    parser.add_argument(
        '-o', '--output',
        help='Path to output LaTeX file (default: stdout)',
        default=None
    )
    parser.add_argument(
        '-t', '--template',
        help='Path to LaTeX template file (default: templates/template.tex)',
        default='templates/template.tex'
    )
    
    args = parser.parse_args()
    
    # Load specification from input file
    # Detect format based on file extension or content
    input_path = args.input_file
    
    if input_path.endswith('.json'):
        # JSON format
        with open(input_path, 'r') as f:
            spec = json.load(f)
    elif input_path.endswith('.txt'):
        # Text format
        with open(input_path, 'r') as f:
            text = f.read()
        spec = parse_text_format(text)
    else:
        # Try to auto-detect by reading first character
        with open(input_path, 'r') as f:
            content = f.read()
        
        # Check if it starts with JSON markers
        stripped = content.strip()
        if stripped.startswith('{') or stripped.startswith('['):
            spec = json.loads(content)
        else:
            # Assume text format
            spec = parse_text_format(content)
    
    # Generate LaTeX
    generator = DiagramGenerator(spec, template_path=args.template)
    latex_code = generator.generate_latex()
    
    # Output
    if args.output:
        with open(args.output, 'w') as f:
            f.write(latex_code)
        print(f"LaTeX diagram written to {args.output}")
    else:
        print(latex_code)


if __name__ == '__main__':
    main()
