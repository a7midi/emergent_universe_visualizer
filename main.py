"""
main.py

VERSION 5: Updated to support the advanced curvature & world-line visualization.
"""
import os
from tqdm import tqdm

from src.config import CONFIG
from src.causal_site import CausalSite
from src.state_manager import StateManager
from src.particle_detector import ParticleDetector
from visualization.visualizer import Visualizer

def main():
    if CONFIG is None:
        return

    print("--- Emergent Universe Simulation ---")
    
    vis_config = CONFIG.get('visualization', {})
    is_visualizing = vis_config.get('enabled', False)
    if is_visualizing and vis_config.get('save_frames', False):
        os.makedirs("results/images", exist_ok=True)

    print("1. Initializing Universe Components...")
    
    causal_site = CausalSite(CONFIG)
    causal_site.generate_graph()
    causal_site.assign_grid_cells()

    state_manager = StateManager(causal_site, CONFIG)
    particle_detector = ParticleDetector(causal_site, state_manager, CONFIG)
    
    visualizer = None
    if is_visualizing:
        print("Initializing Visualizer...")
        visualizer = Visualizer(causal_site, CONFIG)
    
    print("\nInitialization Complete.\n")
    
    print("2. Starting Simulation Loop...")
    
    total_ticks = CONFIG['simulation']['total_ticks']
    log_interval = CONFIG.get('simulation', {}).get('log_interval', 100)
    
    progress_bar = tqdm(range(total_ticks), desc="Simulating", mininterval=0.5)
    
    for tick in progress_bar:
        state_manager.tick()
        
        # --- AMENDED: Get all necessary data for visualization ---
        current_state = state_manager.get_current_state()
        memory_density = state_manager.get_memory_density()
        active_particles = particle_detector.detect(current_state, tick)
        
        if tick > 0 and tick % log_interval == 0:
            num_looping = len(particle_detector.looping_cells_last_tick)
            tqdm.write(f"Tick {tick}: {num_looping} looping cells, {len(active_particles)} particles found.")

        if visualizer and tick % vis_config.get('update_interval', 100) == 0:
            # --- AMENDED: Pass all data to the new visualizer ---
            visualizer.update_plot(
                memory_density=memory_density,
                active_particles=active_particles,
                tick=tick
            )
            if vis_config.get('save_frames', False):
                visualizer.save_frame(tick)

    print("\nSimulation Loop Complete.\n")

    print("3. Final Simulation Report...")
    
    final_particles = particle_detector.active_particles
    archived_particles = particle_detector.archived_particles
    print(f"Detected {len(final_particles)} active particle(s) at the end.")
    print(f"Archived {len(archived_particles)} total historical particle(s).")
    # You can add more detailed reporting on the archived particles here if desired.
    
    if visualizer:
        visualizer.close()
    
    print("\n--- Simulation Finished ---")


if __name__ == '__main__':
    main()