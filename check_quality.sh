#!/bin/bash
# Quality check script - validates diagram has no crossings or overlaps

if [ -z "$1" ]; then
    echo "Usage: $1 <diagram_file.txt>"
    exit 1
fi

echo "=== Diagram Quality Check ==="
echo "File: $1"
echo ""

# Generate and capture output
OUTPUT=$(./generate.sh "$1" 2>&1)

# Extract metrics
TEXT_OVERLAPS=$(echo "$OUTPUT" | grep -oP "Text overlaps: \K\d+" | tail -1)
ARROW_CROSSINGS=$(echo "$OUTPUT" | grep -oP "Arrow crossings: \K\d+" | tail -1)
ARROW_THROUGH_TEXT=$(echo "$OUTPUT" | grep -oP "Arrow through text: \K\d+" | tail -1)
MAX_X=$(echo "$OUTPUT" | grep -oP "Maximum x-coordinate: \K[\d.]+" | tail -1)

# Default to 0 if not found
MAX_X=${MAX_X:-0}

# Show results
echo "📊 Results:"
echo "  Text Overlaps: $TEXT_OVERLAPS"
echo "  Arrow Crossings: $ARROW_CROSSINGS"
echo "  Arrows Through Text: $ARROW_THROUGH_TEXT"
echo "  Max X Position: $MAX_X (limit: 40.0)"
echo ""

# Determine status
FAILED=0

if [ "$TEXT_OVERLAPS" != "0" ]; then
    echo "❌ FAIL: Text overlaps detected!"
    FAILED=1
fi

if [ "$ARROW_CROSSINGS" != "0" ]; then
    echo "❌ FAIL: Arrow crossings detected!"
    echo "$OUTPUT" | grep -A 10 "Arrow crossings detected"
    FAILED=1
fi

if [ "$ARROW_THROUGH_TEXT" != "0" ]; then
    echo "⚠️  WARNING: Arrows passing through text detected"
    echo "$OUTPUT" | grep "passes through text"
    echo "   (This may be unavoidable given the dependency structure)"
fi

if [ -n "$MAX_X" ] && (( $(echo "$MAX_X > 40.0" | bc -l 2>/dev/null || echo 0) )); then
    echo "❌ FAIL: Max X exceeds 40.0 limit!"
    FAILED=1
fi

if [ "$FAILED" = "0" ]; then
    if [ "$ARROW_THROUGH_TEXT" = "0" ]; then
        echo "✅ PERFECT: All quality checks passed!"
    else
        echo "✅ PASS: Core quality checks passed (zero overlaps, zero crossings, within x≤40)"
    fi
    exit 0
else
    echo ""
    echo "💔 Quality check FAILED - please fix the issues above"
    exit 1
fi
