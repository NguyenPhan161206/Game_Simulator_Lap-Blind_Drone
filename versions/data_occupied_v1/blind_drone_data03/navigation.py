"""DATA-03 representation variant: persistent occupied, ephemeral observed-free."""
from blind_drone.navigation.cadence import AcquisitionGrid
from blind_drone_v4.navigation import FreeRoute, ObservedDetourNavigator


class OccupiedOnlyAcquisitionGrid(AcquisitionGrid):
    """Discard old free cells at each new packet; keep occupied hits and inflation.

    The current scan's measured free cells remain available until the next unique
    acquisition. Reused policy reads do not expire them. This is an engineering
    comparison, not a claim that occupancy alone contains enough navigation data.
    """

    def __init__(self, *args):
        super().__init__(*args)
        self.peak_persistent_occupied_cells = 0
        self.peak_ephemeral_free_cells = 0
        self.peak_blocked_cells = 0
        self.peak_retained_cells = 0
        self.peak_map_entries = 0
        self.peak_occupied_json_bytes = 0

    def retain(self, cell, hit):
        if self.exhausted or not self.inside(cell):
            return
        newly_blocked = set()
        if hit and cell not in self.occupied:
            newly_blocked = {(cell[0] + dx, cell[1] + dy) for dx, dy in self.offsets} - self.blocked
        entries = len(self.free) + len(self.occupied) + len(self.blocked)
        if hit:
            projected = entries - int(cell in self.free) + int(cell not in self.occupied) + len(newly_blocked)
        else:
            projected = entries + int(cell not in self.free and cell not in self.occupied)
        if projected > self.params['max_cells']:
            self.exhausted = True
            return
        super().retain(cell, hit)

    def update(self, observation):
        if self.last_sample == observation.sample_time_s:
            return
        self.free.clear()
        super().update(observation)
        self.peak_persistent_occupied_cells = max(
            self.peak_persistent_occupied_cells, len(self.occupied))
        self.peak_ephemeral_free_cells = max(self.peak_ephemeral_free_cells, len(self.free))
        self.peak_blocked_cells = max(self.peak_blocked_cells, len(self.blocked))
        self.peak_retained_cells = max(self.peak_retained_cells,
                                       len(self.free | self.occupied | self.blocked))
        self.peak_map_entries = max(self.peak_map_entries,
                                    len(self.free) + len(self.occupied) + len(self.blocked))


class OccupiedOnlyNavigator(ObservedDetourNavigator):
    """V4 behavior with guarded free evidence limited to the latest scan."""

    def __init__(self, mission, config):
        super().__init__(mission, config)
        self.grid = OccupiedOnlyAcquisitionGrid(
            self.params, config["vehicle"]["body_size_m"],
            config["sensors"]["horizontal_origin_radius_m"])
        self.route_search = FreeRoute(self.grid)

    def diagnostics(self):
        return {**super().diagnostics(),
                "peak_persistent_occupied_cells": self.grid.peak_persistent_occupied_cells,
                "peak_ephemeral_free_cells": self.grid.peak_ephemeral_free_cells,
                "peak_blocked_cells": self.grid.peak_blocked_cells,
                "peak_retained_cells": self.grid.peak_retained_cells,
                "peak_map_entries": self.grid.peak_map_entries,
                "peak_occupied_json_bytes": self.grid.peak_occupied_json_bytes,
                "free_cell_retention": "latest_unique_acquisition_only"}
