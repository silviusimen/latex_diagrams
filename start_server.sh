#!/bin/bash
# Start the LaTeX Diagram Generator Web Server

echo "==================================="
echo "LaTeX Diagram Generator Web Server"
echo "==================================="
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or later."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip."
    exit 1
fi

# Check if pdflatex is installed
if ! command -v pdflatex &> /dev/null; then
    echo "⚠️  WARNING: pdflatex is not installed."
    echo "   Please install TeX Live or MiKTeX to generate diagrams."
    echo "   Ubuntu/Debian: sudo apt-get install texlive-latex-base texlive-latex-extra"
    echo "   macOS: brew install --cask mactex"
    echo ""
fi

# Check if ImageMagick is installed
if ! command -v convert &> /dev/null; then
    echo "⚠️  WARNING: ImageMagick is not installed."
    echo "   Please install ImageMagick to convert PDFs to PNG."
    echo "   Ubuntu/Debian: sudo apt-get install imagemagick"
    echo "   macOS: brew install imagemagick"
    echo ""
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."

# Check if we're in a virtual environment or if one exists
if [ -d "venv" ] && [ -z "$VIRTUAL_ENV" ]; then
    echo "   Using virtual environment in venv/"
    PYTHON_CMD="venv/bin/python3"
    PIP_CMD="venv/bin/pip3"
else
    PYTHON_CMD="python3"
    PIP_CMD="pip3"
fi

$PIP_CMD install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies."
    exit 1
fi

# Create temp directory if it doesn't exist
mkdir -p temp_diagrams

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 Starting web server..."
echo "   Open your browser to: http://localhost:5000"
echo ""
echo "   Press Ctrl+C to stop the server"
echo ""

# Start the server
$PYTHON_CMD web_server.py
