#!/usr/bin/env python3
"""
Unit tests for the DiagramWebService class
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from latex_diagram_generator.web_service import DiagramWebService


class TestDiagramWebService(unittest.TestCase):
    """Test cases for DiagramWebService."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for tests
        self.test_temp_dir = tempfile.mkdtemp()
        self.service = DiagramWebService(
            temp_dir=self.test_temp_dir,
            template_path='templates/template.tex'
        )
        
    def tearDown(self):
        """Clean up test fixtures."""
        # Remove temporary directory
        shutil.rmtree(self.test_temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test service initialization."""
        self.assertTrue(Path(self.test_temp_dir).exists())
        self.assertEqual(self.service.template_path, 'templates/template.tex')
    
    def test_empty_specification(self):
        """Test handling of empty specification."""
        success, result = self.service.generate_diagram('')
        self.assertFalse(success)
        self.assertIn('error', result)
        self.assertIn('Empty', result['error'])
    
    def test_whitespace_only_specification(self):
        """Test handling of whitespace-only specification."""
        success, result = self.service.generate_diagram('   \n\t  ')
        self.assertFalse(success)
        self.assertIn('error', result)
    
    def test_invalid_specification(self):
        """Test handling of invalid specification."""
        success, result = self.service.generate_diagram('invalid -> -> syntax')
        self.assertFalse(success)
        self.assertIn('error', result)
    
    def test_valid_specification_structure(self):
        """Test that valid specification creates proper structure."""
        spec = """P1
P2
P1 -> P2
"""
        success, result = self.service.generate_diagram(spec)
        
        # Even if compilation tools aren't installed, the structure should be created
        if not success:
            # If it failed, it should be due to missing tools, not parsing
            self.assertTrue(
                'pdflatex not found' in result.get('error', '') or
                'LaTeX compilation' in result.get('error', '') or
                'ImageMagick' in result.get('error', '')
            )
        else:
            # If successful, check the result structure
            self.assertIn('latex', result)
            self.assertIn('diagram_id', result)
            self.assertIn('image_url', result)
            self.assertIn('download_tex_url', result)
            self.assertIn('download_pdf_url', result)
            self.assertIn('download_png_url', result)
    
    def test_get_file_path_valid_types(self):
        """Test getting file paths for valid file types."""
        diagram_id = 'test-id'
        
        for file_type in ['tex', 'pdf', 'png']:
            result = self.service.get_file_path(diagram_id, file_type)
            self.assertIsNotNone(result)
            file_path, mimetype, download_name = result
            self.assertIsInstance(file_path, Path)
            self.assertIsInstance(mimetype, str)
            self.assertIsInstance(download_name, str)
    
    def test_get_file_path_invalid_type(self):
        """Test getting file path for invalid file type."""
        result = self.service.get_file_path('test-id', 'invalid')
        self.assertIsNone(result)
    
    def test_get_image_path_nonexistent(self):
        """Test getting image path for non-existent diagram."""
        result = self.service.get_image_path('nonexistent-id')
        self.assertIsNone(result)
    
    def test_file_path_mimetypes(self):
        """Test that correct mimetypes are returned."""
        expected_mimetypes = {
            'tex': 'text/plain',
            'pdf': 'application/pdf',
            'png': 'image/png'
        }
        
        for file_type, expected_mime in expected_mimetypes.items():
            _, mimetype, _ = self.service.get_file_path('test-id', file_type)
            self.assertEqual(mimetype, expected_mime)
    
    def test_file_path_download_names(self):
        """Test that correct download names are returned."""
        for file_type in ['tex', 'pdf', 'png']:
            _, _, download_name = self.service.get_file_path('test-id', file_type)
            self.assertEqual(download_name, f'diagram.{file_type}')
    
    def test_default_example_exists(self):
        """Test that default example is defined."""
        self.assertIsNotNone(DiagramWebService.DEFAULT_EXAMPLE)
        self.assertTrue(len(DiagramWebService.DEFAULT_EXAMPLE) > 0)
        self.assertIn('P1', DiagramWebService.DEFAULT_EXAMPLE)
        self.assertIn('->', DiagramWebService.DEFAULT_EXAMPLE)
    
    def test_cleanup_creates_no_errors(self):
        """Test that cleanup method runs without errors."""
        try:
            self.service.cleanup_old_files(max_age_hours=0)
        except Exception as e:
            self.fail(f"Cleanup raised an exception: {e}")


class TestDiagramWebServiceIntegration(unittest.TestCase):
    """Integration tests for DiagramWebService (requires external tools)."""
    
    @unittest.skipUnless(shutil.which('pdflatex') and shutil.which('convert'),
                         "Requires pdflatex and ImageMagick")
    def test_full_generation_pipeline(self):
        """Test complete generation pipeline with real tools."""
        test_temp_dir = tempfile.mkdtemp()
        try:
            service = DiagramWebService(
                temp_dir=test_temp_dir,
                template_path='templates/template.tex'
            )
            
            spec = """P1
P2
P3
P1 -> P2 -> P3
"""
            
            success, result = service.generate_diagram(spec)
            
            self.assertTrue(success, f"Generation failed: {result}")
            self.assertIn('latex', result)
            self.assertIn('diagram_id', result)
            
            # Verify files were created
            diagram_id = result['diagram_id']
            tex_path, _, _ = service.get_file_path(diagram_id, 'tex')
            pdf_path, _, _ = service.get_file_path(diagram_id, 'pdf')
            png_path, _, _ = service.get_file_path(diagram_id, 'png')
            
            self.assertTrue(tex_path.exists())
            self.assertTrue(pdf_path.exists())
            self.assertTrue(png_path.exists())
            
            # Verify image can be retrieved
            image_path = service.get_image_path(diagram_id)
            self.assertIsNotNone(image_path)
            self.assertTrue(image_path.exists())
            
        finally:
            shutil.rmtree(test_temp_dir, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
