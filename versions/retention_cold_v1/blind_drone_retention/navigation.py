"""A finite free-history ablation; only measured pose/ranges enter this module."""
from math import isfinite

from blind_drone.navigation.cadence import AcquisitionGrid
from blind_drone_v4.navigation import FreeRoute, ObservedDetourNavigator


class RetentionGrid(AcquisitionGrid):
    def __init__(self, params, body_size_m, origin_radius_m, ttl_s=None):
        super().__init__(params, body_size_m, origin_radius_m)
        if ttl_s is not None and (not isfinite(ttl_s) or ttl_s <= 0):
            raise ValueError('Positive finite free-history window required')
        self.ttl_s = ttl_s
        self.free_seen = {}
        self.expired_free = self.peak_entries = 0
        self._acquisition_s = None

    def entries(self):
        # Count storage entries, including redundant last-seen metadata in BOTH arms.
        return len(self.free) + len(self.occupied) + len(self.blocked) + len(self.free_seen)

    def retain(self, cell, hit):
        if self.exhausted or not self.inside(cell):
            return
        projected = self.entries()
        if hit and cell not in self.occupied:
            inflation = {(cell[0]+dx, cell[1]+dy) for dx, dy in self.offsets}
            projected += 1 + len(inflation-self.blocked) - 2*int(cell in self.free)
        elif not hit and cell not in self.occupied and cell not in self.free:
            projected += 2
        if projected > self.params['max_cells']:
            self.exhausted = True
            return
        super().retain(cell, hit)
        if hit:
            self.free_seen.pop(cell, None)
        elif cell in self.free:
            self.free_seen[cell] = self._acquisition_s
        self.peak_entries = max(self.peak_entries, self.entries())

    def update(self, observation):
        stamp = observation.sample_time_s
        if not isfinite(stamp) or (self.last_sample is not None and stamp < self.last_sample):
            raise ValueError('Nonfinite or backward acquisition timestamp')
        if self.last_sample == stamp:
            return  # A policy reread cannot refresh or expire evidence.
        self._acquisition_s = stamp
        if self.ttl_s is not None:
            expired = {cell for cell, seen in self.free_seen.items() if stamp-seen > self.ttl_s+1e-9}
            self.free.difference_update(expired)
            for cell in expired:
                del self.free_seen[cell]
            self.expired_free += len(expired)
            if expired:
                self.no_path_key = None  # Expired evidence invalidates cached routes.
        super().update(observation)

    def snapshot(self):
        return {'free': len(self.free), 'occupied': len(self.occupied),
                'blocked': len(self.blocked), 'timestamp_entries': len(self.free_seen),
                'entries': self.entries(), 'peak_entries': self.peak_entries,
                'expired_free': self.expired_free, 'budget_exhausted': self.exhausted}


class RetentionNavigator(ObservedDetourNavigator):
    def __init__(self, mission, config, ttl_s=None):
        super().__init__(mission, config)
        self.grid = RetentionGrid(self.params, config['vehicle']['body_size_m'],
                                  config['sensors']['horizontal_origin_radius_m'], ttl_s)
        self.route_search = FreeRoute(self.grid)

    def diagnostics(self):
        return {**super().diagnostics(), 'free_ttl_s': self.grid.ttl_s,
                'retention': self.grid.snapshot()}
