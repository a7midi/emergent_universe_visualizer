"""
visualization/visualizer.py

VERSION 5 (Definitive): A more robust and scientifically informative visualizer.
- Uses a logarithmic scale for memory density to prevent color saturation.
- Implements a more reliable method for drawing particles as moving,
  fading circles, which correctly shows their dynamics.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.colors as mcolors
import numpy as np

class Visualizer:
    """Handles the advanced visualization of the simulation."""

    def __init__(self, causal_site, config):
        self.causal_site = causal_site
        self.config = config
        self.node_positions = {}
        
        # --- AMENDED: Simplified patch management ---
        self.particle_patches = []

        plt.ion()
        self.fig, self.ax = plt.subplots(figsize=(12, 12))
        self._calculate_node_positions()
        
        self.colormap = plt.cm.get_cmap('inferno')
        
        self.scatter = self._draw_initial_nodes()
        self.ax.set_title("Emergent Universe - Tick: 0")
        self.fig.tight_layout()

    def _calculate_node_positions(self):
        """Calculates and stores the (x, y) coordinates for each node."""
        for layer_idx, nodes in self.causal_site.nodes_by_layer.items():
            if not nodes: continue
            num_nodes = len(nodes)
            for i, node_id in enumerate(nodes):
                x = (i - num_nodes / 2)
                y = -layer_idx 
                self.node_positions[node_id] = (x, y)
    
    def _draw_initial_nodes(self):
        """Draws the initial scatter plot of all nodes."""
        sorted_nodes = sorted(self.node_positions.keys())
        pos_array = np.array([self.node_positions[i] for i in sorted_nodes])
        initial_colors = np.zeros(len(sorted_nodes))
        
        self.ax.set_facecolor('black')
        self.ax.set_xticks([])
        self.ax.set_yticks([])

        for edge in self.causal_site.graph.edges():
            pos_start = self.node_positions.get(edge[0])
            pos_end = self.node_positions.get(edge[1])
            if pos_start and pos_end:
                self.ax.plot([pos_start[0], pos_end[0]], [pos_start[1], pos_end[1]], 
                             color='gray', alpha=0.05, zorder=1)

        return self.ax.scatter(pos_array[:, 0], pos_array[:, 1], s=10, zorder=2, c=initial_colors, cmap=self.colormap, vmin=0, vmax=1)

    def update_plot(self, memory_density, active_particles, tick):
        """
        Updates the plot with curvature and particle highlights.
        NOTE: Does not need archived_particles anymore.
        """
        # 1. Update node colors using a logarithmic scale for better contrast.
        # This prevents the background from saturating to yellow.
        log_density = np.log1p(memory_density)
        max_log_density = np.max(log_density)
        normalized_density = log_density / (max_log_density + 1e-9)
        
        # Ensure we have the right number of colors for our nodes
        sorted_node_ids = sorted(self.node_positions.keys())
        colors = self.colormap(normalized_density[sorted_node_ids])
        self.scatter.set_facecolors(colors)
        
        # 2. Remove all old particle patches from the previous frame.
        for patch in self.particle_patches:
            patch.remove()
        self.particle_patches.clear()

        # 3. Draw a new, semi-transparent circle for each active particle.
        for particle in active_particles.values():
            particle_nodes = [nid for cell in particle.cells for nid in self.causal_site.get_nodes_in_cell(cell)]
            if not particle_nodes: continue
            
            positions = np.array([self.node_positions[nid] for nid in particle_nodes if nid in self.node_positions])
            if positions.size == 0: continue
            
            centroid = np.mean(positions, axis=0)
            # Radius can be based on the spread of the particle's nodes
            radius = np.max(np.linalg.norm(positions - centroid, axis=1)) + 2.0
            
            # Draw a circle instead of a rectangle for a cleaner look
            circle = patches.Circle(centroid, radius,
                                    linewidth=1.5, edgecolor='cyan',
                                    facecolor='cyan', alpha=0.25, zorder=3)
            self.ax.add_patch(circle)
            self.particle_patches.append(circle)
        
        self.ax.set_title(f"Emergent Universe - Tick: {tick}")
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        plt.pause(0.001)
    
    def save_frame(self, tick):
        self.fig.savefig(f"results/images/frame_{tick:05d}.png", dpi=150, facecolor='black')

    def close(self):
        print("Simulation ended. Close the plot window to exit.")
        plt.ioff()
        plt.show()