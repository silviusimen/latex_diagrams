#!/usr/bin/env python3
"""
Web Service for LaTeX Diagram Generator

This module provides the core web service functionality for generating diagrams,
managing temporary files, and handling compilation.
"""

import os
import subprocess
import uuid
from pathlib import Path
from typing import Dict, Tuple, Optional
from .diagram_generator import DiagramGenerator
from .text_parser import parse_text_format


class DiagramWebService:
    """
    Service class for web-based diagram generation.
    
    Handles the complete pipeline from text specification to compiled PDF and PNG output.
    """
    
    DEFAULT_EXAMPLE = """# Groups (multi-element groups use [brackets])
P1 at (0, 0)
P2 at (0, 1)
P3 at (0, 2)
[P4 + P5] underline at (0, 3)
C at (2.5, 4)

# Links
P1 -> P2 -> P3 -> P4
[P4 + P5] -> C

"""
    
    def __init__(self, temp_dir: str = 'temp_diagrams', template_path: str = 'templates/template.tex'):
        """
        Initialize the web service.
        
        Args:
            temp_dir: Directory for temporary files
            template_path: Path to the LaTeX template file
        """
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(exist_ok=True)
        self.template_path = template_path
        
    def generate_diagram(self, specification_text: str) -> Tuple[bool, Dict]:
        """
        Generate a diagram from a text specification.
        
        Args:
            specification_text: The diagram specification in text format
            
        Returns:
            Tuple of (success: bool, result: dict)
            If successful, result contains: latex, image_url, download URLs
            If failed, result contains: error, details (optional)
        """
        # Validate input
        if not specification_text.strip():
            return False, {'error': 'Empty specification'}
        
        # Create unique ID for this generation
        diagram_id = str(uuid.uuid4())
        output_dir = self.temp_dir / diagram_id
        output_dir.mkdir(exist_ok=True)
        
        try:
            # Parse the text specification
            try:
                spec = parse_text_format(specification_text)
            except Exception as e:
                return False, {'error': f'Parse error: {str(e)}'}
            
            # Generate LaTeX
            generator = DiagramGenerator(spec, template_path=self.template_path)
            latex_code = generator.generate_latex()
            # Also generate the input with rendered positions
            input_with_positions = None
            try:
                temp_input_path = output_dir / 'input_with_positions.txt'
                generator.export_input_with_positions(str(temp_input_path))
                with open(temp_input_path, 'r') as f:
                    input_with_positions = f.read()
            except Exception:
                input_with_positions = None
            # Save LaTeX file
            tex_file = output_dir / 'diagram.tex'
            with open(tex_file, 'w') as f:
                f.write(latex_code)
            
            # Compile to PDF
            success, error_info = self._compile_latex(tex_file, output_dir)
            if not success:
                return False, error_info
            
            # Convert to PNG
            pdf_file = output_dir / 'diagram.pdf'
            png_file = output_dir / 'diagram.png'
            success, error_info = self._convert_pdf_to_png(pdf_file, png_file)
            if not success:
                return False, error_info
            
            # Return success response
            return True, {
                'latex': latex_code,
                'diagram_id': diagram_id,
                'image_url': f'/image/{diagram_id}',
                'download_tex_url': f'/download/{diagram_id}/tex',
                'download_pdf_url': f'/download/{diagram_id}/pdf',
                'download_png_url': f'/download/{diagram_id}/png',
                'input_with_positions': input_with_positions
            }
            
        except Exception as e:
            return False, {'error': f'Unexpected error: {str(e)}'}
    
    def _compile_latex(self, tex_file: Path, output_dir: Path) -> Tuple[bool, Dict]:
        """
        Compile a LaTeX file to PDF using pdflatex.
        
        Args:
            tex_file: Path to the .tex file
            output_dir: Directory for output files
            
        Returns:
            Tuple of (success: bool, error_info: dict)
        """
        try:
            subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', '-output-directory', 
                 str(output_dir), str(tex_file)],
                check=True,
                capture_output=True,
                timeout=30
            )
            return True, {}
        except subprocess.CalledProcessError as e:
            return False, {
                'error': 'LaTeX compilation failed',
                'details': e.stderr.decode('utf-8', errors='ignore')
            }
        except subprocess.TimeoutExpired:
            return False, {'error': 'LaTeX compilation timeout'}
        except FileNotFoundError:
            return False, {'error': 'pdflatex not found. Please install TeX Live or MiKTeX.'}
    
    def _convert_pdf_to_png(self, pdf_file: Path, png_file: Path) -> Tuple[bool, Dict]:
        """
        Convert a PDF file to PNG using ImageMagick.
        
        Args:
            pdf_file: Path to the PDF file
            png_file: Path for the output PNG file
            
        Returns:
            Tuple of (success: bool, error_info: dict)
        """
        try:
            subprocess.run(
                ['convert', '-density', '300', str(pdf_file), '-quality', '90', str(png_file)],
                check=True,
                capture_output=True,
                timeout=30
            )
            return True, {}
        except subprocess.CalledProcessError as e:
            return False, {
                'error': 'PDF to PNG conversion failed',
                'details': e.stderr.decode('utf-8', errors='ignore')
            }
        except subprocess.TimeoutExpired:
            return False, {'error': 'PDF conversion timeout'}
        except FileNotFoundError:
            return False, {'error': 'ImageMagick (convert) not found. Please install ImageMagick.'}
    
    def get_file_path(self, diagram_id: str, file_type: str) -> Optional[Tuple[Path, str, str]]:
        """
        Get the file path, mimetype, and download name for a generated file.
        
        Args:
            diagram_id: The unique diagram identifier
            file_type: Type of file ('tex', 'pdf', or 'png')
            
        Returns:
            Tuple of (file_path, mimetype, download_name) or None if invalid type
        """
        output_dir = self.temp_dir / diagram_id
        
        file_configs = {
            'tex': ('diagram.tex', 'text/plain', 'diagram.tex'),
            'pdf': ('diagram.pdf', 'application/pdf', 'diagram.pdf'),
            'png': ('diagram.png', 'image/png', 'diagram.png')
        }
        
        if file_type not in file_configs:
            return None
        
        filename, mimetype, download_name = file_configs[file_type]
        file_path = output_dir / filename
        
        return file_path, mimetype, download_name
    
    def get_image_path(self, diagram_id: str) -> Optional[Path]:
        """
        Get the path to a generated PNG image.
        
        Args:
            diagram_id: The unique diagram identifier
            
        Returns:
            Path to the PNG file or None if it doesn't exist
        """
        png_file = self.temp_dir / diagram_id / 'diagram.png'
        return png_file if png_file.exists() else None
    
    def cleanup_old_files(self, max_age_hours: int = 24):
        """
        Clean up temporary files older than the specified age.
        
        Args:
            max_age_hours: Maximum age in hours before files are deleted
        """
        import time
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        for item in self.temp_dir.iterdir():
            if item.is_dir():
                # Check directory modification time
                if current_time - item.stat().st_mtime > max_age_seconds:
                    import shutil
                    shutil.rmtree(item, ignore_errors=True)
