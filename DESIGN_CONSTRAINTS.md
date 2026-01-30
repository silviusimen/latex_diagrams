# Design Constraints and Assumptions

This document outlines the key assumptions and constraints used in the diagram layout algorithm.

## Layout Algorithm

### Bottom-Up Approach
- **Strategy**: Layout is computed bottom-up, starting from leaf nodes (groups with no outgoing links)
- **Iteration**: Groups are placed in iterations, processing groups that link to already-placed groups
- **Ordering**: Within each iteration, groups are ordered by their destination x-position (left-to-right)

### Vertical Positioning
- **Bottom Groups**: Groups with no outgoing links to other groups are placed at the bottom
- **Special Case - Internal Links**: When bottom groups link to each other (e.g., underlined group → C):
  - Target nodes are placed at `y_level` (bottom row)
  - Source nodes are placed at `y_level + 1` (one row above)
  - This ensures vertical arrows are properly separated
- **Subsequent Rows**: Each iteration places groups at progressively higher y-levels

## Spacing Constraints

### Within-Group Spacing
```python
WITHIN_GROUP_SPACING = 2.0  # units
```
- **Purpose**: Horizontal spacing between elements within the same group
- **Rationale**: Prevents text overlap for typical element names (~8 characters = ~0.64 units width)
- **Safety Margin**: 2.0 units provides sufficient clearance for most text labels

### Maximum Row Width
```python
MAX_ROW_WIDTH = 20.0  # units
```
- **Purpose**: Maximum horizontal span allowed for a single row
- **Behavior**: When exceeded, row is automatically split into multiple rows
- **Priority**: Groups with incoming links are moved first (from center outward)

### Target Diagram Width
```python
target_width_cm = 12.0  # cm
```
- **Purpose**: Target width for the final rendered diagram
- **Calculation**: `x_spacing = target_width_cm / max_width`
- **Constraints**: x_spacing is clamped to range [0.5, 1.5] cm
- **Result**: Ensures diagram fits on A4 page with standard margins

## Font Size Scaling

Font size is automatically adjusted based on x-spacing to maintain readability:

```python
if x_spacing < 0.8:
    font_size = 10pt
elif x_spacing < 1.0:
    font_size = 12pt
else:
    font_size = 14pt
```

## Collision Detection

### Three-Layer Validation
1. **Text-Text Overlaps**: Detects when node labels overlap spatially
2. **Arrow-Arrow Crossings**: Detects when arrows intersect each other
3. **Arrow-Through-Text**: Detects when arrows pass through text labels

### Resolution Strategy
- **Horizontal Shifts**: Groups are shifted horizontally to resolve conflicts
- **Iteration Limit**: Maximum 10 iterations of conflict resolution
- **Priority**: Groups with incoming links are prioritized for stable positioning

## Underlined Group Handling

### Center Node Calculation
For underlined groups (e.g., `[P1+P2+P3+P4+P5+P6]`):
- **Width Calculation**: `width = (num_elements - 1) * WITHIN_GROUP_SPACING`
- **Center Position**: `center_x = start_x + center_idx * WITHIN_GROUP_SPACING`
  - Note: Must multiply by WITHIN_GROUP_SPACING, not just use center_idx
- **Arrow Origin**: Arrows from underlined groups originate from the center node

### Layout Rules
- Elements are evenly spaced within the group
- Group is centered horizontally when possible
- Underline is drawn from first element's `.south west` to last element's `.south east`

## Coordinate System

### TikZ Coordinate Space
- **X-axis**: Horizontal, measured in units (converted to cm via x_spacing)
- **Y-axis**: Vertical, measured in units (fixed at 2.0cm per level)
- **Origin**: Groups centered around x=0, with bottom groups at lowest y-level

### Unit Conversions
- **Horizontal**: Calculated units × x_spacing (typically 0.5-1.5 cm)
- **Vertical**: Fixed at 2.0 cm per level
- **Text Width**: Approximated as `num_chars * 0.08` units

## Performance Considerations

### Maximum Iterations
- **Layout**: Bottom-up algorithm completes in O(n) iterations where n = number of group levels
- **Conflict Resolution**: Limited to 10 iterations maximum
- **Early Exit**: Stops immediately when 0 conflicts detected

### Complexity
- **Time**: O(n² × m) where n = number of groups, m = number of links
- **Space**: O(n) for storing positions and levels

## Known Limitations

1. **Very Long Element Names**: Names exceeding ~15 characters may still overlap with 2.0 spacing
2. **Dense Graphs**: Highly interconnected graphs may not resolve all conflicts within 10 iterations
3. **Wide Groups**: Underlined groups with many elements may still exceed page width
4. **Arrow Aesthetics**: Some arrow paths may not be optimal (e.g., diagonal vs. orthogonal routing)

## Future Improvements

1. **Dynamic Spacing**: Adjust WITHIN_GROUP_SPACING based on actual text width measurements
2. **Orthogonal Routing**: Implement proper orthogonal arrow routing to avoid diagonal arrows
3. **Group Reordering**: Optimize group ordering within rows to minimize conflicts
4. **Multi-Row Underlines**: Support splitting very wide underlined groups across multiple rows
