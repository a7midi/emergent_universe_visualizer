#!/usr/bin/env python3
# Build a compact, un‑lit glTF scene from static_universe.json
# ------------------------------------------------------------
import json, struct, pathlib
import numpy as np
from pygltflib import (
    GLTF2, Scene, Node, Mesh, Primitive, Material, Buffer,
    BufferView, Accessor, Asset, UNSIGNED_INT, FLOAT,
)

ROOT = pathlib.Path(__file__).resolve().parent
SRC  = ROOT / "results" / "static_universe.json"
DST  = ROOT / "results" / "substrate.glb"

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def pack_floats(arr: np.ndarray) -> bytes:
    return struct.pack("<" + "f" * arr.size, *arr.flatten())

def make_accessor(gltf, *, bview, offset, count, ctype, dtype=FLOAT):
    acc = Accessor(
        bufferView=bview,
        byteOffset=offset,
        componentType=dtype,
        count=count,
        type=ctype,
    )
    gltf.accessors.append(acc)
    return len(gltf.accessors) - 1

# ------------------------------------------------------------
# Load JSON exported by export_data.py
# ------------------------------------------------------------
with open(SRC, "r", encoding="utf-8") as f:
    data = json.load(f)
nodes_json = data["nodes"]            # dict  id -> {position:[x,y,z]}
edges_json = data["edges"]            # list [ [srcId, dstId], ... ]

# Build numpy arrays
node_pos  = np.array([nodes_json[k]["position"] for k in nodes_json], dtype=np.float32)
edge_idx  = np.array(edges_json, dtype=np.uint32).flatten()

# ------------------------------------------------------------
# glTF asset skeleton
# ------------------------------------------------------------
gltf = GLTF2(
    asset=Asset(version="2.0"),
    extensionsUsed=["KHR_materials_unlit"],
    scenes=[Scene(nodes=[0, 1])],     # sphere mesh node + line mesh node
    materials=[
        Material(
            name="NodeMaterial",
            doubleSided=True,
            emissiveFactor=[0.05, 0.9, 1.0],   # cyan glow
            extensions={"KHR_materials_unlit": {}},
        ),
        Material(
            name="EdgeMaterial",
            doubleSided=True,
            emissiveFactor=[0.3, 0.3, 0.35],
            extensions={"KHR_materials_unlit": {}},
        ),
    ],
    meshes=[],
    nodes=[],
    buffers=[],
    bufferViews=[],
    accessors=[],
)

# ------------------------------------------------------------
# Buffer 0  –  packed positions + indices
# ------------------------------------------------------------
pos_bytes  = pack_floats(node_pos)
idx_bytes  = edge_idx.tobytes()
buffer_bin = pos_bytes + idx_bytes
gltf.buffers.append(Buffer(byteLength=len(buffer_bin)))

# Views
pos_view = BufferView(buffer=0, byteOffset=0,
                      byteLength=len(pos_bytes), byteStride=12)  # 3 floats
idx_view = BufferView(buffer=0, byteOffset=len(pos_bytes),
                      byteLength=len(idx_bytes))
gltf.bufferViews.extend([pos_view, idx_view])

# Accessors
pos_acc = make_accessor(gltf, bview=0, offset=0,
                        count=len(node_pos), ctype="VEC3")
idx_acc = make_accessor(gltf, bview=1,
                        offset=0, count=len(edge_idx),
                        ctype="SCALAR", dtype=UNSIGNED_INT)

# ------------------------------------------------------------
# Node mesh  –  small icosphere instanced via translations
# ------------------------------------------------------------
sphere_vertices = np.array([
    [ 0,  0,  0], [ .1,  0,  0], [ 0, .1,  0], [ 0,  0, .1]
], dtype=np.float32)
sphere_faces    = np.array([[0,1,2],[0,1,3],[0,2,3],[1,2,3]], dtype=np.uint32)

sv_bytes = pack_floats(sphere_vertices)
sf_bytes = sphere_faces.tobytes()
offs0    = len(buffer_bin)
buffer_bin += sv_bytes + sf_bytes

# Update buffer 0 length
gltf.buffers[0].byteLength = len(buffer_bin)

# Extra views & accessors for the tiny sphere
view_v = BufferView(buffer=0, byteOffset=offs0,
                    byteLength=len(sv_bytes), byteStride=12)
view_i = BufferView(buffer=0, byteOffset=offs0+len(sv_bytes),
                    byteLength=len(sf_bytes))
gltf.bufferViews.extend([view_v, view_i])

acc_v = make_accessor(gltf, bview=len(gltf.bufferViews)-2,
                      offset=0, count=len(sphere_vertices), ctype="VEC3")
acc_i = make_accessor(gltf, bview=len(gltf.bufferViews)-1,
                      offset=0, count=len(sphere_faces)*3,
                      ctype="SCALAR", dtype=UNSIGNED_INT)

# Mesh 0  –  node‑sphere
gltf.meshes.append(
    Mesh(primitives=[Primitive(
        attributes={"POSITION": acc_v},
        indices=acc_i,
        mode=4,                 # TRIANGLES
        material=0
    )])
)

# Mesh 1  –  edges (LINES)
gltf.meshes.append(
    Mesh(primitives=[Primitive(
        attributes={"POSITION": pos_acc},
        indices=idx_acc,
        mode=1,                 # LINES
        material=1
    )])
)

# Scene graph: one node for spheres (instanced in viewer), one for lines
gltf.nodes.extend([
    Node(mesh=0, name="NodeSpheres"),
    Node(mesh=1, name="EdgeLines"),
])

# ------------------------------------------------------------
# Write binary .glb
# ------------------------------------------------------------
bin_uri = buffer_bin
gltf.set_binary_blob(bin_uri)
gltf.save_binary(DST)
print("✓  wrote", DST.relative_to(ROOT))
