"""
LaTeX Diagram Generator Package

A package for generating LaTeX/TikZ diagrams from structured specifications.
"""

from .generator import DiagramGenerator
from .text_parser import parse_text_format

__all__ = ['DiagramGenerator', 'parse_text_format']
