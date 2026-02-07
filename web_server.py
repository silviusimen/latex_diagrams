#!/usr/bin/env python3
"""
Web server for LaTeX Diagram Generator
Provides a web interface for non-technical users to create diagrams
"""

from flask import Flask, render_template, request, jsonify, send_file
from latex_diagram_generator import DiagramWebService

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize the web service
web_service = DiagramWebService(
    temp_dir='temp_diagrams',
    template_path='templates/template.tex'
)


@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html', default_text=DiagramWebService.DEFAULT_EXAMPLE)


@app.route('/generate', methods=['POST'])
def generate_diagram():
    """
    Generate diagram from input specification.
    Returns JSON with LaTeX source and PNG image path.
    """
    # Get input specification from request
    spec_text = request.json.get('specification', '')
    
    # Generate the diagram using the service
    success, result = web_service.generate_diagram(spec_text)
    
    if success:
        return jsonify({
            'success': True,
            'latex': result['latex'],
            'image_url': result['image_url'],
            'download_tex_url': result['download_tex_url'],
            'download_pdf_url': result['download_pdf_url'],
            'download_png_url': result['download_png_url'],
            'input_with_positions': result.get('input_with_positions', None)
        })
    else:
        # Determine appropriate status code
        error = result.get('error', 'Unknown error')
        if 'not found' in error.lower():
            status_code = 500
        elif 'parse error' in error.lower() or 'empty' in error.lower():
            status_code = 400
        elif 'compilation failed' in error.lower() or 'conversion failed' in error.lower():
            status_code = 400
        elif 'timeout' in error.lower():
            status_code = 400
        else:
            status_code = 500
        
        return jsonify(result), status_code


@app.route('/image/<diagram_id>')
def get_image(diagram_id):
    """Serve the generated PNG image."""
    image_path = web_service.get_image_path(diagram_id)
    if image_path:
        return send_file(image_path, mimetype='image/png')
    return 'Image not found', 404


@app.route('/download/<diagram_id>/<file_type>')
def download_file(diagram_id, file_type):
    """Download generated files (tex, pdf, or png)."""
    file_info = web_service.get_file_path(diagram_id, file_type)
    
    if not file_info:
        return 'Invalid file type', 400
    
    file_path, mimetype, download_name = file_info
    
    if file_path.exists():
        return send_file(file_path, mimetype=mimetype, as_attachment=True, download_name=download_name)
    return 'File not found', 404


@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    print("Starting LaTeX Diagram Generator Web Server...")
    print("Open your browser to: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
