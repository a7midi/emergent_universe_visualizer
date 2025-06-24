Emergent Universe Simulation Suite
This software suite is a computational laboratory designed to explore the theories and predictions presented in the trilogy of papers by A. Alayar on deterministic causal sites. Its primary goal is to provide a practical, empirical test of the central claim: that complex, stable, particle-like structures can spontaneously emerge from a simple, finite, and purely deterministic computational substrate.



Where the papers provide the analytical proofs, this suite provides the means to run controlled experiments, observe emergent phenomena, and discover the specific conditions under which they occur.

Core Concepts & Architecture
The architecture of this program is a direct implementation of the core theoretical objects described in the papers.

The Causal Site (C) → causal_site.py
The foundational structure of the universe, the "finite acyclic causal site", is instantiated by the CausalSite class. It procedurally generates a layered directed graph with path-length interference that respects the key hypotheses of the theory.



The Update Functor (T) → state_manager.py
The deterministic evolution of the universe is handled by the StateManager class. Its tick() method is a single application of the update functor T to the entire system. It contains different fusion_mode implementations, which are the concrete "laws of physics" (ψ_c) that determine how a site's state evolves based on its causal predecessors.


The Particle → particle_detector.py
This is the discovery engine of the simulation. The ParticleDetector class is an algorithm designed to find emergent particles by directly implementing their mathematical definition from Paper 1: a "bounded, indecomposable, T-invariant subobject".

T-invariance (Stability): It hashes the state of local regions (cells) at each tick and maintains a history to find repeating, cyclical patterns (loops).
Indecomposability (Coherence): Once looping cells are found, it uses a graph traversal algorithm (find_connected_clusters) to group adjacent, co-cycling cells into single, coherent objects.
Setup and Installation
1. Prerequisites
Python 3.9 or newer.
git for cloning the repository.
2. Environment Setup
This project uses a Python virtual environment to manage dependencies.

a. Clone the Repository:

Bash

git clone <https://github.com/a7midi/emergent_universe_visualizer>
cd emergent_universe_visualizer
b. Create the Virtual Environment:
Open your terminal in the project's root directory and run:

Bash

python -m venv venv
c. Activate the Environment:

Windows Command Prompt:
DOS

venv\Scripts\activate
Windows PowerShell:
PowerShell

.\venv\Scripts\Activate.ps1
macOS / Linux:
Bash

source venv/bin/activate
After activation, your command prompt should begin with (venv).

d. Install Dependencies:
The required packages are listed in requirements.txt. Install them with:

Bash

pip install -r requirements.txt
Running the Simulation
All simulation parameters are controlled by the config.yaml file. The main entry point is main.py.

To run a simulation, execute the following command from the project's root directory:

Bash

python main.py
Understanding the Output
The simulation produces two forms of output: a real-time console log and an optional graphical visualization.

Console Log
During a run, you will see periodic updates like this:

Tick 2200: 117 looping cells, 3 particles found.

looping cells: This is the total number of grid cells that the detector has identified as being in a stable, periodic loop. This number is a proxy for the overall "complexity" or "structural entropy" of the observable universe at that moment.
particles found: This is the number of distinct, coherent clusters formed by the looping cells. A fluctuating number indicates a dynamic universe where particles are being created and destroyed.
Visualizer
If visualization: enabled: true is set in the config, a window will show:

The Background: A dark gray "vacuum" representing quiescent spacetime.
Colored Nodes: Nodes that are part of a detected particle are colored brightly. The color corresponds to the particle's period, allowing you to distinguish different types of particles visually.
Particle Highlights: A semi-transparent white circle is drawn around the cluster of nodes that form a particle, making it easy to see its size and location.
The Experimental Workflow: Finding Particles
The search for emergent particles is an experimental process. The goal is to tune the parameters in config.yaml to create a "habitable zone" where the dynamics are complex enough to avoid simple, global oscillations but stable enough for localized patterns to persist.

The recommended "first-success" configuration below is an excellent starting point. From there, you can perform parameter sweeps (e.g., varying edge_probability or alphabet_size_q) to explore the space of possible universes.

Recommended "First-Success" Configuration
This configuration is designed to produce multiple, independent particles by creating a complex graph structure and using a non-linear, history-dependent fusion rule.

YAML

# Recommended configuration for generating long-lived particles.

# ------------- General -------------
simulation:
  total_ticks: 60000
  seed: 42
  hide_layer_index: 0
  log_interval: 500
  verbose: true

# ------------- Causal site ----------
causal_site:
  layers: 60
  avg_nodes_per_layer: 30
  edge_probability: 0.15
  max_lookback_layers: 3

# ------------- Tags / state ----------
tags:
  alphabet_size_q: 17
  max_out_degree_R: 3
  fusion_mode: "injective"

# ------------- Detector --------------
detector:
  grid_size: 12
  max_history_length: 30000
  min_loop_period: 3
  min_particle_size: 2

# ------------- Visualisation ---------
visualization:
  enabled: false
  update_interval: 200
  save_frames: false
