#!/usr/bin/env python3
"""Layout engine for computing diagram layout."""

from typing import Dict, List, Tuple, Set
from .dependency_analyzer import DependencyAnalyzer
from .group_positioner import GroupPositioner
from .bottom_group_placer import BottomGroupPlacer
from .row_placer import RowPlacer

# Import spacing constants
from .spacing_constants import WITHIN_GROUP_SPACING, BETWEEN_GROUP_SPACING



class LayoutEngine:
    """Handles layout computation for diagram elements."""

    def __init__(self, within_group_spacing: float = WITHIN_GROUP_SPACING, between_group_spacing: float = BETWEEN_GROUP_SPACING):
        self.WITHIN_GROUP_SPACING = within_group_spacing
        self.BETWEEN_GROUP_SPACING = between_group_spacing
        self.group_name_to_group = None
        self.element_to_group = None
        self.analyzer = None
        self.positioner = None
        self.bottom_placer = None
        self.row_placer = None

    def _initialize_layout(self, group_name_to_group, element_to_group):
        """
        Initialize layout data structures and helper components.
        Args:
            group_name_to_group: Dictionary mapping group names to group objects
            element_to_group: Dictionary mapping element names to their containing group
        Returns:
            Tuple of (all_groups, levels, positions, node_positions, placed_groups, current_y)
        """
        self.group_name_to_group = group_name_to_group
        self.element_to_group = element_to_group
        # Initialize helper components
        self.analyzer = DependencyAnalyzer(group_name_to_group, element_to_group)
        self.positioner = GroupPositioner(group_name_to_group, self.WITHIN_GROUP_SPACING, self.BETWEEN_GROUP_SPACING)
        self.bottom_placer = BottomGroupPlacer(group_name_to_group, self.positioner)
        self.row_placer = RowPlacer(group_name_to_group, element_to_group, self.positioner, self.analyzer)
        all_groups = set(group_name_to_group.keys())
        levels = {}  # group_name -> y_level
        positions = {}  # group_name -> (start_x, elements)
        node_positions = {}  # elem -> x position
        placed_groups = set()
        current_y = 0
        return all_groups, levels, positions, node_positions, placed_groups, current_y

    def __init__(self, within_group_spacing: float = 2.0, between_group_spacing: float = 3.0):
        self.WITHIN_GROUP_SPACING = within_group_spacing
        self.BETWEEN_GROUP_SPACING = between_group_spacing
        self.group_name_to_group = None
        self.element_to_group = None
        self.analyzer = None
        self.positioner = None
        self.bottom_placer = None
        self.row_placer = None

    def compute_layout_bottom_up_arrow_aware(self, group_name_to_group, element_to_group, outgoing, incoming, conflict_detector) -> Tuple[Dict[str, int], Dict[str, Tuple[float, List[str]]]]:
        """Compute layout bottom-up, using backtracking to find the best group ordering per level to minimize crossings."""
        import itertools
        # --- Post-processing: Try local swaps in 2D to further reduce crossings ---
        def try_swap_groups_2d(levels, positions, node_positions, outgoing, conflict_detector, max_passes=3):
            """
            For each layer, try swapping adjacent groups and keep the swap if it reduces crossings.
            Repeat for a few passes.
            """
            import copy
            group_y_to_names = {}
            for g, y in levels.items():
                group_y_to_names.setdefault(y, []).append(g)
            for _ in range(max_passes):
                improved = False
                for y, group_names in group_y_to_names.items():
                    # Sort by x position
                    group_names_sorted = sorted(group_names, key=lambda g: positions[g][0])
                    for i in range(len(group_names_sorted)-1):
                        g1, g2 = group_names_sorted[i], group_names_sorted[i+1]
                        # Swap g1 and g2
                        # Copy positions and node_positions
                        pos_copy = copy.deepcopy(positions)
                        node_pos_copy = copy.deepcopy(node_positions)
                        # Swap their x positions
                        x1, elems1 = pos_copy[g1]
                        x2, elems2 = pos_copy[g2]
                        pos_copy[g1] = (x2, elems1)
                        pos_copy[g2] = (x1, elems2)
                        # Update node_positions for all elements in g1 and g2
                        for idx, elem in enumerate(elems1):
                            if elem in node_pos_copy:
                                node_pos_copy[elem] = (elem, x2 + idx * self.WITHIN_GROUP_SPACING, node_pos_copy[elem][2])
                        for idx, elem in enumerate(elems2):
                            if elem in node_pos_copy:
                                node_pos_copy[elem] = (elem, x1 + idx * self.WITHIN_GROUP_SPACING, node_pos_copy[elem][2])
                        # Count crossings before and after
                        arrows_before = self._collect_arrows(node_positions, outgoing)
                        arrows_after = self._collect_arrows(node_pos_copy, outgoing)
                        crossings_before = len(conflict_detector.check_arrow_crossings(arrows_before))
                        crossings_after = len(conflict_detector.check_arrow_crossings(arrows_after))
                        if crossings_after < crossings_before:
                            # Accept swap
                            positions[g1], positions[g2] = pos_copy[g1], pos_copy[g2]
                            for elem in elems1:
                                if elem in node_positions:
                                    node_positions[elem] = node_pos_copy[elem]
                            for elem in elems2:
                                if elem in node_positions:
                                    node_positions[elem] = node_pos_copy[elem]
                            improved = True
                if not improved:
                    break
        # ...existing code...
        all_groups, levels, positions, node_positions, placed_groups, current_y = self._initialize_layout(group_name_to_group, element_to_group)
        analyzer = DependencyAnalyzer(group_name_to_group, element_to_group)
        group_input_order = list(group_name_to_group.keys())
        # Build group-to-group dependency graph
        group_dependencies = {g: set() for g in all_groups}
        for src_group in all_groups:
            src_obj = group_name_to_group[src_group]
            src_elems = src_obj.get('elements', [src_group])
            for elem in src_elems:
                if elem in outgoing:
                    tgts = outgoing[elem]
                    if not isinstance(tgts, list):
                        tgts = [tgts]
                    for tgt in tgts:
                        if tgt in element_to_group:
                            tgt_group = element_to_group[tgt]
                            if tgt_group != src_group:
                                group_dependencies[tgt_group].add(src_group)
        # Assign layer indices to ensure all arrows go down, with back-propagation
        group_layer = {g: 0 for g in all_groups}
        # Add standalone elements as their own groups for layering
        for elem in outgoing:
            if elem not in element_to_group:
                group_layer[elem] = 0
        changed = True
        while changed:
            changed = False
            for src_elem, tgts in outgoing.items():
                if not isinstance(tgts, list):
                    tgts = [tgts]
                src_group = element_to_group[src_elem] if src_elem in element_to_group else src_elem
                src_layer = group_layer[src_group]
                for tgt in tgts:
                    tgt_group = element_to_group[tgt] if tgt in element_to_group else tgt
                    if tgt_group not in group_layer:
                        group_layer[tgt_group] = 0
                    # Enforce: tgt_group must be strictly above src_group
                    if group_layer[tgt_group] <= src_layer:
                        group_layer[tgt_group] = src_layer + 1
                        changed = True
        # Build layers from group_layer mapping
        max_layer = max(group_layer.values())
        # Only include real groups in layers (not standalone elements)
        layers = [[] for _ in range(max_layer + 1)]
        for g in group_input_order:
            if g in group_layer:
                layers[group_layer[g]].append(g)

        num_layers = len(layers)
        y_spacing = 2.0  # Increased vertical spacing between rows
        # Assign y-levels so that the highest layer index is at the top (y=0), lower indices further down
        for layer_idx, layer in enumerate(layers):
            y_level = layer_idx * y_spacing
            best_order = None
            min_crossings = float('inf')
            # Try all orderings if small, else use input order
            if len(layer) <= 8:
                perms = list(itertools.permutations(layer))
            else:
                perms = [layer]
            for ordering in perms:
                # Copy state for trial
                trial_levels = dict(levels)
                trial_positions = dict(positions)
                trial_node_positions = dict(node_positions)
                x = 0.0
                for group in ordering:
                    self.positioner.place_group_at(group, x, y_level, trial_levels, trial_positions, trial_node_positions)
                    x += self.positioner.calculate_group_widths([group])[0] + self.BETWEEN_GROUP_SPACING
                arrows = self._collect_arrows(trial_node_positions, outgoing)
                crossings = conflict_detector.check_arrow_crossings(arrows)
                if len(crossings) < min_crossings:
                    min_crossings = len(crossings)
                    best_order = ordering
                    best_trial = (dict(trial_levels), dict(trial_positions), dict(trial_node_positions))
                    if min_crossings == 0:
                        break
            # After finding best ordering, split into rows if needed
            ordered_groups = list(best_order)
            rows = self._split_groups_into_rows(ordered_groups)
            for row in rows:
                # Use RowPlacer to handle placement and y-levels (including overflow/wrapping)
                self.row_placer.place_groups_on_row(row, y_level, levels, positions, node_positions, force_sequential=True)

        # Check for non-downward (vertical or upward) arrows
        node_y = {}
        for group, (x, elements) in positions.items():
            for elem in elements:
                if elem in node_positions:
                    # node_positions[elem] = (elem, x, y)
                    if isinstance(node_positions[elem], tuple) and len(node_positions[elem]) == 3:
                        node_y[elem] = node_positions[elem][2]

        non_downward_arrows = []
        for src_elem in outgoing:
            tgts = outgoing[src_elem]
            if not isinstance(tgts, list):
                tgts = [tgts]
            for tgt in tgts:
                if src_elem in node_y and tgt in node_y:
                    if node_y[src_elem] >= node_y[tgt]:
                        non_downward_arrows.append((src_elem, node_y[src_elem], tgt, node_y[tgt]))
        if non_downward_arrows:
            msg = ["ERROR: Non-downward arrows detected (vertical or upward):"]
            for src, y1, tgt, y2 in non_downward_arrows:
                msg.append(f"  Arrow from {src} (y={y1}) to {tgt} (y={y2}) is not strictly downward!")
            raise RuntimeError("\n".join(msg))
        return levels, positions

    def _resolve_crossings_recursive(self, node_positions, outgoing, conflict_detector, levels, positions, node_positions_ref, prev_y_level, max_depth=10, shifted_groups=None):
        """Recursively resolve crossings by shifting groups on previous lines, propagating as needed. Improved: shift both groups, try larger shifts, avoid infinite loops."""
        if prev_y_level < 0 or max_depth <= 0:
            return
        if shifted_groups is None:
            shifted_groups = set()
        arrows = self._collect_arrows(node_positions, outgoing)
        crossings = conflict_detector.check_arrow_crossings(arrows)
        if not crossings:
            return
        groups_on_prev = [g for g, y in levels.items() if y == prev_y_level]
        did_shift = False
        for s1, t1, s2, t2, ix, iy in crossings:
            g1 = g2 = None
            for g in groups_on_prev:
                group_elems = positions[g][1] if g in positions else []
                if s1 in group_elems:
                    g1 = g
                if s2 in group_elems:
                    g2 = g
            # Shift both groups apart if possible, and try larger shifts if already shifted
            if g1 and g2 and g1 != g2:
                if (g1, prev_y_level) not in shifted_groups:
                    print(f"  → Shifting {g1} left by 1.5 to resolve crossing")
                    self.positioner.shift_group_horizontally(g1, -1.5, positions, node_positions_ref)
                    shifted_groups.add((g1, prev_y_level))
                    did_shift = True
                if (g2, prev_y_level) not in shifted_groups:
                    print(f"  → Shifting {g2} right by 1.5 to resolve crossing")
                    self.positioner.shift_group_horizontally(g2, 1.5, positions, node_positions_ref)
                    shifted_groups.add((g2, prev_y_level))
                    did_shift = True
            elif g1 and (g1, prev_y_level) not in shifted_groups:
                print(f"  → Shifting {g1} right by 2.0 to resolve crossing")
                self.positioner.shift_group_horizontally(g1, 2.0, positions, node_positions_ref)
                shifted_groups.add((g1, prev_y_level))
                did_shift = True
            elif g2 and (g2, prev_y_level) not in shifted_groups:
                print(f"  → Shifting {g2} left by 2.0 to resolve crossing")
                self.positioner.shift_group_horizontally(g2, -2.0, positions, node_positions_ref)
                shifted_groups.add((g2, prev_y_level))
                did_shift = True
        # Recursively check and resolve further down if any shift was made
        if did_shift:
            self._resolve_crossings_recursive(node_positions, outgoing, conflict_detector, levels, positions, node_positions_ref, prev_y_level-1, max_depth-1, shifted_groups)

    def _collect_arrows(self, node_positions, outgoing):
        """Collect all arrows as (source, sx, sy, target, tx, ty) tuples for crossing detection."""
        arrows = []
        for source, targets in outgoing.items():
            if not isinstance(targets, list):
                targets = [targets]
            for target in targets:
                if source in node_positions and target in node_positions:
                    sx, sy = node_positions[source][1], node_positions[source][2]
                    tx, ty = node_positions[target][1], node_positions[target][2]
                    arrows.append((source, sx, sy, target, tx, ty))
        return arrows

    def _resolve_crossings_by_shifting(self, crossings, levels, positions, node_positions, prev_y_level):
        """Shift groups on the previous row left/right to resolve crossings. Propagate recursively if needed."""
        if prev_y_level < 0:
            return
        # Find groups on previous row
        groups_on_prev = [g for g, y in levels.items() if y == prev_y_level]
        for s1, t1, s2, t2, ix, iy in crossings:
            # Find which group(s) on previous row are involved
            for g in groups_on_prev:
                group_elems = positions[g][1] if g in positions else []
                if s1 in group_elems or s2 in group_elems:
                    # Shift left or right
                    shift = -1.0 if s1 in group_elems else 1.0
                    self.positioner.shift_group_horizontally(g, shift, positions, node_positions)
                    # After shifting, recursively check for new crossings
                    # (In practice, this could be improved to avoid infinite loops)
        # Note: In a robust implementation, we'd re-check for crossings and propagate as needed
        # For now, this is a single pass for simplicity
    def _collect_arrows(self, node_positions, outgoing):
        """Collect all arrows as (source, sx, sy, target, tx, ty) tuples for crossing detection."""
        arrows = []
        for source, targets in outgoing.items():
            if not isinstance(targets, list):
                targets = [targets]
            for target in targets:
                if source in node_positions and target in node_positions:
                    sx, sy = node_positions[source][1], node_positions[source][2]
                    tx, ty = node_positions[target][1], node_positions[target][2]
                    arrows.append((source, sx, sy, target, tx, ty))
        return arrows

    def _resolve_crossings_by_shifting(self, crossings, levels, positions, node_positions, prev_y_level):
        """Shift groups on the previous row left/right to resolve crossings. Propagate recursively if needed."""
        if prev_y_level < 0:
            return
        # Find groups on previous row
        groups_on_prev = [g for g, y in levels.items() if y == prev_y_level]
        for s1, t1, s2, t2, ix, iy in crossings:
            # Find which group(s) on previous row are involved
            for g in groups_on_prev:
                group_elems = positions[g][1] if g in positions else []
                if s1 in group_elems or s2 in group_elems:
                    # Shift left or right
                    shift = -1.0 if s1 in group_elems else 1.0
                    self.positioner.shift_group_horizontally(g, shift, positions, node_positions)
                    # After shifting, recursively check for new crossings
                    # (In practice, this could be improved to avoid infinite loops)
        # Note: In a robust implementation, we'd re-check for crossings and propagate as needed
        # For now, this is a single pass for simplicity
    
    def _place_initial_bottom_groups(self, all_groups, outgoing, incoming, current_y,
                                    levels, positions, node_positions, placed_groups):
        """
        Find and place bottom groups (leaf nodes).
        
        Args:
            all_groups: Set of all group names
            outgoing, incoming: Link dictionaries
            current_y: Current y-level
            levels, positions, node_positions, placed_groups: Dicts to update
            
        Returns:
            Updated current_y (max y-level used)
        """
        bottom_groups = self.analyzer.find_bottom_groups(all_groups, outgoing)
        print(f"\n=== Bottom-Up Layout ===")
        print(f"Bottom groups: {bottom_groups}")
        
        # Find dependencies among bottom groups
        source_to_target = self.analyzer.find_bottom_group_dependencies(bottom_groups, outgoing)
        
        # Place bottom groups intelligently
        max_y_used = self.bottom_placer.place_bottom_groups_intelligently(
            bottom_groups, current_y, levels, positions, node_positions, 
            source_to_target, self.row_placer.place_groups_on_row
        )
        placed_groups.update(bottom_groups)
        return max_y_used
    
    def _process_next_layer(self, iteration, all_groups, placed_groups, outgoing, incoming,
                           current_y, levels, positions, node_positions):
        """
        Process next layer of groups in bottom-up traversal.
        
        Args:
            iteration: Current iteration number
            all_groups: Set of all group names
            placed_groups: Set of already placed groups
            outgoing, incoming: Link dictionaries
            current_y: Current y-level
            levels, positions, node_positions: Dicts to update
            
        Returns:
            List of groups placed in this iteration
        """
        # Find groups linking to placed groups
        next_groups = self.analyzer.find_next_layer_groups(all_groups, placed_groups, outgoing)
        
        if not next_groups:
            # No more groups link to placed groups, place remaining
            next_groups = [g for g in all_groups if g not in placed_groups]
        
        if not next_groups:
            return []
        
        print(f"\nIteration {iteration}: Processing {len(next_groups)} groups")
        
        # Sort groups by destination position and place them
        sorted_groups = self.analyzer.sort_groups_by_destination(next_groups, outgoing, node_positions)
        self.row_placer.place_groups_on_row_with_overflow(
            sorted_groups, current_y, levels, positions, node_positions, 
            incoming, outgoing, placed_groups
        )
        
        return sorted_groups
    
    def compute_layout_bottom_up(self, group_name_to_group, element_to_group, 
                                 outgoing, incoming) -> Tuple[Dict[str, int], Dict[str, Tuple[float, List[str]]]]:
        """
        Compute layout using strict topological layering to eliminate overlaps.
        Each topological layer gets its own row, groups ordered to minimize crossings.
        
        Args:
            group_name_to_group: Dictionary mapping group names to group objects
            element_to_group: Dictionary mapping element names to their containing group
            outgoing: Dictionary of outgoing links (element -> targets)
            incoming: Dictionary of incoming links (element -> sources)
            
        Returns:
            Tuple of (levels dict, positions dict)
        """
        # Initialize data structures
        all_groups, levels, positions, node_positions, placed_groups, current_y = \
            self._initialize_layout(group_name_to_group, element_to_group)
        
        print("\n=== Strict Layered Layout (Zero Overlaps) ===")
        
        # Compute topological layers
        layers = self._compute_topological_layers(all_groups, outgoing, incoming)
        
        print(f"Computed {len(layers)} topological layers:")
        for i, layer in enumerate(layers):
            print(f"  Layer {i}: {layer}")
        
        # Place each layer on its own row with crossing minimization
        # Use larger vertical spacing to accommodate row wrapping within layers
        current_y = 0
        for layer_idx, layer_groups in enumerate(layers):
            num_rows_in_layer = self._place_layer_with_crossing_minimization(
                layer_groups, current_y, levels, positions, node_positions,
                outgoing, incoming, placed_groups
            )
            placed_groups.update(layer_groups)
            # Move to next layer with spacing for arrows to pass cleanly
            current_y += num_rows_in_layer + 1
        
        print(f"\n=== Layout Complete: {len(placed_groups)} groups placed ===")
        return levels, positions
    
    def _compute_topological_layers(self, all_groups, outgoing, incoming):
        """
        Compute topological layers where each layer contains groups with no dependencies on later layers.
        
        Returns:
            List of layers, where each layer is a list of group names
        """
        # Compute longest path from each group (its depth)
        group_depth = {}
        
        # Find groups with no outgoing links (bottom layer)
        bottom_groups = []
        for group in all_groups:
            has_outgoing = False
            group_obj = self.group_name_to_group[group]
            
            # Check if any element in the group has outgoing links
            if 'elements' in group_obj:
                for elem in group_obj['elements']:
                    if elem in outgoing:
                        has_outgoing = True
                        break
            
            # Also check if the group itself has outgoing links
            if group in outgoing:
                has_outgoing = True
            
            if not has_outgoing:
                bottom_groups.append(group)
                group_depth[group] = 0
        
        # BFS to compute depth of each group
        queue = list(bottom_groups)
        visited = set(bottom_groups)
        
        while queue:
            current = queue.pop(0)
            current_depth = group_depth[current]
            
            # Find groups that point to current group
            for group in all_groups:
                if group in visited:
                    continue
                
                group_obj = self.group_name_to_group[group]
                points_to_current = False
                
                # Check element-level outgoing links
                if 'elements' in group_obj:
                    for elem in group_obj['elements']:
                        if elem in outgoing:
                            targets = outgoing[elem]
                            if not isinstance(targets, list):
                                targets = [targets]
                            
                            # Check if any target is in current group
                            current_obj = self.group_name_to_group[current]
                            if 'elements' in current_obj:
                                if any(t in current_obj['elements'] for t in targets):
                                    points_to_current = True
                                    break
                            elif current in targets or any(t == current for t in targets):
                                points_to_current = True
                                break
                
                # Also check group-level outgoing links
                if not points_to_current and group in outgoing:
                    targets = outgoing[group]
                    if not isinstance(targets, list):
                        targets = [targets]
                    current_obj = self.group_name_to_group[current]
                    if 'elements' in current_obj:
                        if any(t in current_obj['elements'] for t in targets):
                            points_to_current = True
                    elif current in targets:
                        points_to_current = True
                
                if points_to_current:
                    new_depth = current_depth + 1
                    if group not in group_depth or group_depth[group] < new_depth:
                        group_depth[group] = new_depth
                    if group not in visited:
                        visited.add(group)
                        queue.append(group)
        
        # Handle circular dependencies: place unvisited groups at depth 0
        for group in all_groups:
            if group not in visited:
                group_depth[group] = 0
        
        # Organize into layers
        max_depth = max(group_depth.values()) if group_depth else 0
        layers = [[] for _ in range(max_depth + 1)]
        
        for group, depth in group_depth.items():
            layers[depth].append(group)
        
        return layers
    
    def _place_layer_with_crossing_minimization(self, layer_groups, y_level, levels, 
                                                positions, node_positions, outgoing, 
                                                incoming, placed_groups):
        """
        Place a layer of groups with crossing minimization.
        Groups are ordered to minimize crossings with their targets.
        Split into multiple rows if needed to respect MAX_X_POSITION.
        
        Returns:
            Number of rows used by this layer
        """
        if not layer_groups:
            return 0
        
        # Order groups by their median target position
        groups_with_target_x = []
        for group in layer_groups:
            target_x = self._compute_median_target_x(group, outgoing, node_positions)
            groups_with_target_x.append((group, target_x))
        
        # Sort by target position
        groups_with_target_x.sort(key=lambda x: x[1])
        ordered_groups = [g for g, _ in groups_with_target_x]
        
        # Split groups into rows that respect MAX_X_POSITION
        rows = self._split_groups_into_rows(ordered_groups)
        
        # Place each row with spacing for arrow passage
        for i, row_groups in enumerate(rows):
            row_y = y_level + i
            self.row_placer.place_groups_on_row(row_groups, row_y, levels, positions, node_positions, force_sequential=True)
            print(f"  Layer {y_level} row {i}: {row_groups} at y={row_y}")
        
        return len(rows)
    
    def _split_groups_into_rows(self, ordered_groups):
        """Split groups into multiple rows respecting MAX_X_POSITION."""
        if not ordered_groups:
            return []
        
        rows = []
        current_row = []
        current_x = 0.0
        
        for group in ordered_groups:
            group_width = self.positioner.calculate_group_widths([group])[0]
            
            # Check if adding this group would exceed MAX_X_POSITION
            if current_row and current_x + self.positioner.BETWEEN_GROUP_SPACING + group_width > self.positioner.MAX_X_POSITION:
                # Start new row
                rows.append(current_row)
                current_row = [group]
                current_x = group_width
            else:
                # Add to current row
                if current_row:
                    current_x += self.positioner.BETWEEN_GROUP_SPACING
                current_row.append(group)
                current_x += group_width
        
        if current_row:
            rows.append(current_row)
        
        return rows
    
    def _compute_median_target_x(self, group, outgoing, node_positions):
        """Compute the median x-position of this group's targets."""
        target_positions = []
        group_obj = self.group_name_to_group[group]
        
        # Collect target positions
        if 'elements' in group_obj:
            for elem in group_obj['elements']:
                if elem in outgoing:
                    targets = outgoing[elem]
                    if not isinstance(targets, list):
                        targets = [targets]
                    for target in targets:
                        if target in node_positions:
                            if isinstance(node_positions[target], tuple):
                                target_positions.append(node_positions[target][1])  # (node_id, x, y)
                            else:
                                target_positions.append(node_positions[target])
        elif group in outgoing:
            targets = outgoing[group]
            if not isinstance(targets, list):
                targets = [targets]
            for target in targets:
                if target in node_positions:
                    if isinstance(node_positions[target], tuple):
                        target_positions.append(node_positions[target][1])
                    else:
                        target_positions.append(node_positions[target])
        
        if target_positions:
            target_positions.sort()
            median_idx = len(target_positions) // 2
            return target_positions[median_idx]
        
        return 0.0  # Default to left
