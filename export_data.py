"""
export_data.py

VERSION 8 (Cinematic Export): Implements all audit recommendations.
- Exports a comprehensive static data file for the universe structure.
- Calculates and exports true 3D coordinates for all nodes.
- Tracks and exports the centroid history ("world-line") for each particle.
- Logs particle spawn/decay events for narrative-driven animation.
"""
import os
import json
from tqdm import tqdm
import numpy as np
from collections import deque

# Import the core components of our simulation
from src.config import CONFIG
from src.causal_site import CausalSite
from src.state_manager import StateManager
from src.particle_detector import ParticleDetector

def calculate_particle_kinematics(particle, causal_site):
    """Calculates the visual properties of a particle for rendering."""
    if not particle.cells:
        return {'centroid': [0, 0, 0], 'radius': 0}

    particle_nodes = [
        nid for cell in particle.cells 
        for nid in causal_site.get_nodes_in_cell(cell)
    ]
    if not particle_nodes:
        return {'centroid': [0, 0, 0], 'radius': 0}

    positions = np.array([
        causal_site.node_positions[nid] for nid in particle_nodes 
        if nid in causal_site.node_positions
    ])
    if positions.size == 0:
        return {'centroid': [0, 0, 0], 'radius': 0}

    centroid = np.mean(positions, axis=0)
    radius = np.max(np.linalg.norm(positions - centroid, axis=1)) if positions.shape[0] > 1 else 5.0

    return {
        'centroid': centroid.tolist(),
        'radius': float(radius)
    }

def main():
    if CONFIG is None:
        print("Failed to load configuration. Exiting.")
        return

    print("--- Emergent Universe Simulation (Cinematic Data Export) ---")
    os.makedirs("results", exist_ok=True)

    # === Phase 1: Initialization ===
    print("1. Initializing Universe Components...")
    
    causal_site = CausalSite(CONFIG)
    causal_site.generate_graph()
    causal_site.assign_grid_cells()
    state_manager = StateManager(causal_site, CONFIG)
    particle_detector = ParticleDetector(causal_site, state_manager, CONFIG)
    
    # === Phase 2: Pre-calculate 3D Positions & Save Static Data ===
    print("2. Calculating 3D layout and exporting static data...")
    causal_site.node_positions = {}
    cs_config = CONFIG.get('causal_site', {})
    dz = cs_config.get('layer_depth_z', 6.0) # Vertical separation between layers

    for layer_idx, nodes in causal_site.nodes_by_layer.items():
        if not nodes: continue
        num_nodes = len(nodes)
        for i, node_id in enumerate(nodes):
            # FIX: Create true 3D coordinates with depth separation
            x = (i - num_nodes / 2) * 5.0
            y = 0.0 # Lay out nodes on a line within each layer
            z = -layer_idx * dz
            causal_site.node_positions[node_id] = [x, y, z]

    static_data = {
        'nodes': {
            nid: {
                'layer': data['layer'],
                'cell_id': data['cell_id'],
                'position': causal_site.node_positions.get(nid)
            } for nid, data in causal_site.graph.nodes(data=True)
        },
        'edges': list(causal_site.graph.edges()),
        'total_layers': causal_site.num_layers,
        'grid_size': CONFIG.get('detector', {}).get('grid_size', 10)
    }
    with open('results/static_universe.json', 'w') as f:
        json.dump(static_data, f)
    print("Static data saved to results/static_universe.json")

    # === Phase 3: Simulation Loop with World-line Tracking ===
    print("\n3. Starting Simulation Loop for Dynamic Data Export...")
    
    total_ticks = CONFIG['simulation']['total_ticks']
    log_interval = CONFIG.get('simulation', {}).get('log_interval', 100)
    
    last_tick_particle_ids = set()
    # NEW: Data structure to hold the world-line track for each particle
    worldline_history = {} 

    with open('results/simulation_log.jsonl', 'w') as log_file:
        progress_bar = tqdm(range(total_ticks), desc="Simulating", mininterval=1.0)
        
        for tick in progress_bar:
            state_manager.tick()
            
            current_state = state_manager.get_current_state()
            active_particles = particle_detector.detect(current_state, tick)
            
            current_particle_ids = set(active_particles.keys())
            spawned_ids = current_particle_ids - last_tick_particle_ids
            decayed_ids = last_tick_particle_ids - current_particle_ids

            # Update world-line history
            for p_id in decayed_ids:
                if p_id in worldline_history:
                    del worldline_history[p_id] # Clean up memory for decayed particles
            
            for p_id in current_particle_ids:
                if p_id not in worldline_history:
                    worldline_history[p_id] = deque(maxlen=200) # Store last 200 positions
                
                kinematics = calculate_particle_kinematics(active_particles[p_id], causal_site)
                worldline_history[p_id].append(kinematics['centroid'])

            frame_data = {
                'tick': tick,
                'events': {'spawned': list(spawned_ids), 'decayed': list(decayed_ids)},
                'particles': [
                    {
                        'id': p.id, 
                        'period': p.period, 
                        'lifetime': p.lifetime,
                        'num_cells': len(p.cells),
                        # Recalculate kinematics to ensure it's in the frame data
                        'kinematics': calculate_particle_kinematics(p, causal_site),
                        # NEW: Include the world-line track in the export
                        'track': list(worldline_history.get(p.id, []))
                    }
                    for p_id, p in active_particles.items()
                ]
            }
            
            log_file.write(json.dumps(frame_data) + '\n')
            last_tick_particle_ids = current_particle_ids
            
            if tick > 0 and tick % log_interval == 0:
                tqdm.write(f"Tick {tick}: {len(active_particles)} active particles.")

    print("\nSimulation Loop Complete.")
    print("Cinematic simulation history saved to results/simulation_log.jsonl")
    print("\n--- Data Export Finished ---")

if __name__ == '__main__':
    main()
