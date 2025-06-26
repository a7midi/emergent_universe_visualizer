# src/causal_site.py
# VERSION 7: Corrected for lookback=0 edge case.

import networkx as nx
import numpy as np

class CausalSite:
    """
    Represents the finite, acyclic causal site of the universe.
    """

    def __init__(self, config):
        """
        Initializes the CausalSite.
        """
        self.config = config
        self.graph = nx.DiGraph()
        self.nodes_by_layer = {}
        self.nodes_by_cell = {}
        self.node_positions = {} # For 3D visualization export

    def generate_graph(self):
        """
        Procedurally generates the layered causal graph, correctly enforcing the
        out-degree (successor) bound and other theoretical constraints.
        """
        print("Generating causal site graph...")
        node_counter = 0
        
        cs_config = self.config.get('causal_site', {})
        layers = cs_config.get('layers', 50)
        avg_nodes = cs_config.get('avg_nodes_per_layer', 40)
        edge_prob = cs_config.get('edge_probability', 0.1)
        max_lookback = cs_config.get('max_lookback_layers', 1)
        
        self.num_layers = layers
        rng = np.random.default_rng(self.config['simulation']['seed'])
        
        print(f"Using max predecessor lookback of {max_lookback} layers.")

        # --- Step 1: Generate nodes and initial edges ---
        for layer_index in range(self.num_layers):
            num_nodes_in_layer = rng.poisson(avg_nodes) if avg_nodes > 0 else 1
            if num_nodes_in_layer == 0:
                num_nodes_in_layer = 1
            
            self.nodes_by_layer[layer_index] = []

            for i in range(num_nodes_in_layer):
                node_id = node_counter
                # Store 3D position for visualization export
                pos_x = (i - num_nodes_in_layer / 2) * 20
                pos_y = rng.uniform(-5, 5)
                pos_z = -layer_index * 20
                self.node_positions[node_id] = [pos_x, pos_y, pos_z]
                
                self.graph.add_node(node_id, layer=layer_index)
                self.nodes_by_layer[layer_index].append(node_id)
                node_counter += 1

                if layer_index > 0:
                    # The range of previous layers to connect to
                    start_layer = max(0, layer_index - max_lookback) if max_lookback > 0 else layer_index -1
                    if start_layer >= layer_index:
                        continue

                    for lookback_idx in range(start_layer, layer_index):
                        previous_layer_nodes = self.nodes_by_layer.get(lookback_idx, [])
                        for potential_parent in previous_layer_nodes:
                            distance = layer_index - lookback_idx
                            if rng.random() < edge_prob / (distance**0.5): # Use sqrt for less aggressive falloff
                                self.graph.add_edge(potential_parent, node_id)
        
        # --- Step 2: Enforce maximum SUCCESSOR count (out-degree R) ---
        max_r = self.config.get('tags', {}).get('max_out_degree_R', 2)
        print(f"Enforcing maximum successor count (R) of {max_r}...")
        
        for layer_index in range(self.num_layers - 1):
            for node_id in self.nodes_by_layer.get(layer_index, []):
                successors = list(self.graph.successors(node_id))
                if len(successors) > max_r:
                    children_to_prune = rng.choice(
                        successors, 
                        size=len(successors) - max_r, 
                        replace=False
                    )
                    for child_to_prune in children_to_prune:
                        self.graph.remove_edge(node_id, child_to_prune)

        # --- Step 3: Safeguard for non-terminal visible nodes ---
        print("Safeguarding against isolated visible nodes...")
        sim_config = self.config.get('simulation', {})
        hide_layer_index = sim_config.get('hide_layer_index', -1)

        for layer_index in range(1, self.num_layers):
            if layer_index == hide_layer_index:
                continue
            
            for node_id in self.nodes_by_layer.get(layer_index, []):
                if self.graph.in_degree(node_id) == 0:
                    
                    # THE FIX: Handle the lookback=0 edge case
                    start_layer = max(0, layer_index - max_lookback) if max_lookback > 0 else layer_index -1
                    
                    # Ensure the range for selecting a parent layer is valid
                    if start_layer >= layer_index:
                        # This can only happen if layer_index=1 and lookback=0.
                        # In this case, the only valid parent layer is 0.
                        potential_parent_layer_idx = 0
                    else:
                        potential_parent_layer_idx = rng.integers(start_layer, layer_index)

                    potential_parents = self.nodes_by_layer.get(potential_parent_layer_idx, [])
                    if potential_parents:
                        parent_to_add = rng.choice(potential_parents)
                        self.graph.add_edge(parent_to_add, node_id)

        print(f"Graph generation complete. Total nodes: {self.graph.number_of_nodes()}")

    def assign_grid_cells(self):
        """Partitions the graph nodes into a spatial grid for particle detection."""
        print("Assigning nodes to grid cells for particle detection...")
        grid_size = self.config.get('detector', {}).get('grid_size', 12)

        # Find the bounding box of the node positions to normalize grid assignment
        if not self.node_positions: return
        
        all_pos = np.array(list(self.node_positions.values()))
        min_coords = np.min(all_pos, axis=0)
        max_coords = np.max(all_pos, axis=0)
        span = max_coords - min_coords
        span[span==0] = 1 # Avoid division by zero if all nodes are in a line

        for node_id, pos in self.node_positions.items():
            norm_pos = (pos - min_coords) / span
            cell_x = int(norm_pos[0] * grid_size)
            cell_y = int(norm_pos[2] * grid_size) # Use Z for vertical grid position
            cell_id = (min(cell_x, grid_size - 1), min(cell_y, grid_size - 1))
            self.graph.nodes[node_id]['cell_id'] = cell_id

            if cell_id not in self.nodes_by_cell:
                self.nodes_by_cell[cell_id] = []
            self.nodes_by_cell[cell_id].append(node_id)
            
        print("Grid cell assignment complete.")

    def get_predecessors(self, node_id):
        """Returns the immediate causal predecessors of a given site."""
        return list(self.graph.predecessors(node_id))
    
    def get_nodes_in_cell(self, cell_id):
        """Retrieves all node IDs located within a specific grid cell."""
        return self.nodes_by_cell.get(cell_id, [])
