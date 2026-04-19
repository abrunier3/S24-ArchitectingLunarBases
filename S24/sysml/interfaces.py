import networkx as nx
from typing import Dict, Any, List

def build_system_graph(parts_json, connections):
    G = nx.DiGraph()

    # Build lookup: (part, port) → directions
    port_lookup = {}
    for p in parts_json:
        for port in p.get("ports", []):
            port_lookup[(p["name"], port["name"])] = port.get("direction", [])

    # add nodes
    for p in parts_json:
        G.add_node(p["name"])

    # add edges
    for conn in connections:
        src = conn["from"]["part"]
        dst = conn["to"]["part"]

        src_port = conn["from"]["port"]
        dst_port = conn["to"]["port"]

        G.add_edge(
            src,
            dst,
            label=conn.get("type"),
            flow=conn.get("flow"),
            port_from=src_port,
            port_to=dst_port,
            from_dir=port_lookup.get((src, src_port), []),
            to_dir=port_lookup.get((dst, dst_port), []),
        )

    return G


def compute_flow_layout(G):
    pos = {}

    in_degree = dict(G.in_degree())

    current_layer = [n for n, d in in_degree.items() if d == 0]

    layers = []
    visited = set()

    while current_layer:
        layers.append(current_layer)
        next_layer = []

        for node in current_layer:
            visited.add(node)

            for _, neighbor in G.out_edges(node):
                if neighbor in visited:
                    continue

                # reduce in-degree
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    next_layer.append(neighbor)

        current_layer = next_layer

    x_spacing = 3
    y_spacing = 2

    for i, layer in enumerate(layers):
        for j, node in enumerate(layer):
            pos[node] = (i * x_spacing, -j * y_spacing)

    isolated = set(G.nodes()) - set(pos.keys())
    for k, node in enumerate(isolated):
        pos[node] = (0, -len(layers) * y_spacing - k * y_spacing)

    return pos


# def activate_subsystem(
#     data: Dict[str, Any],
#     active_nodes: List[str],
#     *,
#     verbose: int = 1
# ) -> Dict[str, Any]:
#     """
#     Build a reduced system (JSON + connections) based on active nodes.
#     """

#     parts = data["parts"]
#     connections = data["connections"]

#     active_set = set(active_nodes)

#     filtered_parts = [
#         p for p in parts
#         if p["name"] in active_set
#     ]

#     if verbose >= 1:
#         print(f"[ACTIVATE] Parts: {len(filtered_parts)} / {len(parts)}")

#     filtered_connections = [
#         c for c in connections
#         if c["from"]["part"] in active_set
#         and c["to"]["part"] in active_set
#     ]

#     if verbose >= 1:
#         print(f"[ACTIVATE] Connections: {len(filtered_connections)} / {len(connections)}")

#     new_metadata = {
#         "package": data["metadata"]["package"],
#         "num_parts": len(filtered_parts),
#         "num_connections": len(filtered_connections),
#         "activated_nodes": active_nodes,
#     }

#     return {
#         "metadata": new_metadata,
#         "parts": filtered_parts,
#         "connections": filtered_connections,
#     }


# def build_active_graph(active_data):
#     return build_system_graph(
#         active_data["parts"],
#         active_data["connections"]
#     )