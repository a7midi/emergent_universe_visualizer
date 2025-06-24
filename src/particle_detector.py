"""
particle_detector.py

VERSION 4: Archives stale particles instead of deleting them to allow for
the visualization of their full world-lines.
"""
from collections import deque
from dataclasses import dataclass
import numpy as np

from src.causal_site import CausalSite
from src.state_manager import StateManager
from src.utils.hashing import hash_cell_state
from src.utils.graph_algorithms import find_connected_clusters

@dataclass
class Particle:
    id: int
    period: int
    cells: frozenset
    last_seen_tick: int
    first_seen_tick: int
    
    @property
    def lifetime(self):
        return self.last_seen_tick - self.first_seen_tick

class ParticleDetector:
    def __init__(self, causal_site: CausalSite, state_manager: StateManager, config: dict):
        self.causal_site = causal_site
        self.state_manager = state_manager
        self.config = config

        detector_config = self.config.get('detector', {})
        history_len = detector_config.get('max_history_length', 10000)
        self.min_loop_period = detector_config.get('min_loop_period', 5)
        self.min_particle_size = detector_config.get('min_particle_size', 2)

        self.hash_history = {
            cell_id: deque(maxlen=history_len)
            for cell_id in self.causal_site.nodes_by_cell.keys()
        }
        
        self.active_particles = {}
        # --- NEW: Dictionary to store the history of old particles ---
        self.archived_particles = {}
        self._next_particle_id = 0
        self._cluster_to_particle_id = {}
        
        self.looping_cells_last_tick = set()

    def detect(self, current_state: np.ndarray, current_tick: int) -> dict:
        looping_cells_by_period = {}

        for cell_id, node_ids in self.causal_site.nodes_by_cell.items():
            if not node_ids:
                continue

            visible_node_ids = [nid for nid in node_ids if nid not in self.state_manager.hidden_nodes]
            if not visible_node_ids:
                continue

            cell_node_indices = np.array(visible_node_ids, dtype=int)
            cell_tags = current_state[cell_node_indices]
            new_hash = hash_cell_state(cell_tags)
            
            if new_hash is None:
                continue
            
            history = self.hash_history[cell_id]
            if history:
                try:
                    reversed_history = reversed(history)
                    index_from_end = next(i for i, h in enumerate(reversed_history) if h == new_hash)
                    period = index_from_end + 1
                    
                    if period >= self.min_loop_period:
                        if period not in looping_cells_by_period:
                            looping_cells_by_period[period] = set()
                        looping_cells_by_period[period].add(cell_id)
                except StopIteration:
                    pass
            
            self.hash_history[cell_id].append(new_hash)

        all_looping_cells = set()
        for period_group in looping_cells_by_period.values():
            all_looping_cells.update(period_group)
        self.looping_cells_last_tick = all_looping_cells

        self._update_particles(looping_cells_by_period, current_tick)
        return self.active_particles
    
    def _update_particles(self, looping_cells_by_period: dict, current_tick: int):
        active_clusters = set()

        for period, cells in looping_cells_by_period.items():
            clusters = find_connected_clusters(cells, self.causal_site)
            
            for cluster in clusters:
                if len(cluster) < self.min_particle_size:
                    continue
                
                cluster_set = frozenset(cluster)
                active_clusters.add(cluster_set)

                if cluster_set in self._cluster_to_particle_id:
                    particle_id = self._cluster_to_particle_id[cluster_set]
                    self.active_particles[particle_id].last_seen_tick = current_tick
                else:
                    new_id = self._next_particle_id
                    new_particle = Particle(
                        id=new_id, period=period, cells=cluster_set,
                        first_seen_tick=current_tick, last_seen_tick=current_tick
                    )
                    self.active_particles[new_id] = new_particle
                    self._cluster_to_particle_id[cluster_set] = new_id
                    self._next_particle_id += 1
        
        # --- AMENDED: Move stale particles to the archive instead of deleting ---
        stale_clusters = set(self._cluster_to_particle_id.keys()) - active_clusters
        for cluster in stale_clusters:
            particle_id = self._cluster_to_particle_id.pop(cluster)
            if particle_id in self.active_particles:
                # Move from active to archive
                self.archived_particles[particle_id] = self.active_particles.pop(particle_id)