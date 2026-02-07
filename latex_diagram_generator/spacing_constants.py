# Spacing and dimension constants for the diagram generator
#
# Adjust these values to tune the appearance and compactness of generated diagrams.
# Each constant is documented with its effect on the layout.

WITHIN_GROUP_SPACING = 2.5
# Horizontal distance between elements within the same group.
# Increase for more space between elements in a group; decrease for a more compact group.

BETWEEN_GROUP_SPACING = 2.6
# Horizontal distance between adjacent groups on the same row.
# Increase to separate groups more; decrease to pack groups closer together.

TEXT_WIDTH = 0.64
# Estimated width of a text label (in layout units).
# Affects collision detection and arrow routing around text.
# Increase if text overlaps are detected; decrease for tighter layouts if text is short.

TEXT_HEIGHT = 0.3
# Estimated height of a text label (in layout units).
# Used for collision detection and arrow routing.

TARGET_WIDTH_CM = 12.0
# Target total width of the diagram in centimeters (for LaTeX output).
# Affects scaling and spacing calculations to fit diagrams on a page.

X_SPACING_MIN = 0.5
# Minimum allowed horizontal spacing between elements/groups after scaling.

X_SPACING_MAX = 1.5
# Maximum allowed horizontal spacing between elements/groups after scaling.

X_SPACING_DEFAULT = 1.0
# Default horizontal spacing if scaling is not applied.

MARGIN_CM = 0.25
# Page margin in centimeters for LaTeX output.

LINE_WIDTH_PT = 2.0
# Thickness of lines/arrows in the diagram (in TeX points).
