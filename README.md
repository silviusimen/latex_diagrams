# LaTeX Diagram Generator

A Python tool for generating LaTeX/TikZ diagrams from JSON specifications.

## Overview

This tool takes a JSON file describing a diagram structure and generates LaTeX code with TikZ for rendering. It's particularly useful for creating logic diagrams, flowcharts, and dependency graphs.

## Installation

No external dependencies required - uses only Python standard library.

```bash
chmod +x diagram_generator.py
```

## Usage

### Basic Usage

```bash
./diagram_generator.py diagrams/example.txt
```

### Save to File

```bash
./diagram_generator.py diagrams/example.txt -o output.tex
```

### Using the Shell Script

```bash
./generate.sh diagrams/example.txt
```

### Compile the LaTeX

```bash
pdflatex output.tex
```

## Text Specification Format

The input text file uses a simple, compact format with two sections:

### Groups Section

Define groups (one per line):
- Single element: Just write the element name
- Multi-element: Use `[element1 + element2 + ...]` with brackets
- Underline: Add `underline` after the group definition

Example:
```
# Groups (multi-element groups use [brackets])
P1
P2
P3
[P4 + P5] underline
C
```

### Links Section

Define links using arrow notation:
- Chain links: `A -> B -> C -> D`
- Single link: `A -> B`
- Multi-element group links: `[P4 + P5] -> C`

Example:
```
# Links
P1 -> P2 -> P3 -> P4
[P4 + P5] -> C
```

### Complete Example

```
# Groups (multi-element groups use [brackets])
P1
P2
P3
[P4 + P5] underline
C

# Links
P1 -> P2 -> P3 -> P4
[P4 + P5] -> C
```

## Features

- **Automatic Layout**: Computes vertical and horizontal positions based on dependencies
- **Group Support**: Elements in a group are rendered on the same horizontal line
- **Underlines**: Groups can have blue underlines with centered outgoing links
- **Arrow Links**: Directed links shown as blue arrows
- **Vertical Flow**: Links flow from top to bottom following tree structure

## Testing

Run the test suite:

```bash
python test_diagram_generator.py
```

Run with verbose output:

```bash
python test_diagram_generator.py -v
```

## Example

See [example.json](example.json) for a sample input file and [example.tex](example.tex) for expected output.

The example demonstrates:
- Simple single-element groups (P1, P2, P3, C)
- Multi-element group with underline (P4, +, P5)
- Chain of dependencies
- Group-to-element link

## Requirements

The tool follows these design requirements:
- Groups with multiple elements are rendered on the same virtual line
- Horizontal spacing of 1 unit between elements in the same group
- Links are vertical when possible
- Groups linking to elements are placed above their targets
- Blue arrows for all directed links
- Blue underlines for groups with `underline: true`
- Links from underlined groups originate from the center of the underline

## Note

The generated LaTeX assumes a `grid.tex` file exists in the same directory for the TikZ picture environment. Make sure this file is available when compiling the output.
