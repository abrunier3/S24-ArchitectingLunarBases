import networkx as nx
import matplotlib.pyplot as plt

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


def plot_system_graph(G):
    pos = compute_flow_layout(G)

    plt.figure(figsize=(14, 8))

    # -----------------------------
    # EDGE COLOR LOGIC
    # -----------------------------
    edge_colors = []
    for u, v, d in G.edges(data=True):
        src_dirs = d.get("from_dir", [])
        dst_dirs = d.get("to_dir", [])
        flow = d.get("flow")

        is_valid = "out" in src_dirs and "in" in dst_dirs

        if not is_valid:
            edge_colors.append("red")
        elif flow == "LOX":
            edge_colors.append("blue")
        else:
            edge_colors.append("green")

    # -----------------------------
    # DRAW GRAPH
    # -----------------------------
    nx.draw(
        G,
        pos,
        with_labels=True,
        node_size=3000,
        node_color="lightblue",
        font_size=10,
        font_weight="bold",
        arrows=True,
        edge_color=edge_colors,
        width=2,
        arrowsize=20   # 👈 add this
    )

    # -----------------------------
    # EDGE LABELS
    # -----------------------------
    edge_labels = {
        (u, v): f"{d.get('flow', d.get('label'))}"
        for u, v, d in G.edges(data=True)
    }
    nx.draw_networkx_edge_labels(
        G,
        pos,
        edge_labels=edge_labels,
        label_pos=0.6,
        font_size=9,
        rotate=False
    )
    plt.title("System Connectivity Graph")
    plt.show()

def compute_flow_layout(G):
    pos = {}

    # -----------------------------
    # STEP 1: find in-degree of nodes
    # -----------------------------
    in_degree = dict(G.in_degree())

    # start with source nodes (no incoming edges)
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

    # -----------------------------
    # STEP 2: assign positions
    # -----------------------------
    x_spacing = 3
    y_spacing = 2

    for i, layer in enumerate(layers):
        for j, node in enumerate(layer):
            pos[node] = (i * x_spacing, -j * y_spacing)

    # -----------------------------
    # STEP 3: handle isolated nodes
    # -----------------------------
    isolated = set(G.nodes()) - set(pos.keys())
    for k, node in enumerate(isolated):
        pos[node] = (0, -len(layers) * y_spacing - k * y_spacing)

    return pos



    

# def plot_system_graph(G):
#     pos = nx.spring_layout(G, seed=42)

#     plt.figure(figsize=(10, 6))

#     nx.draw(
#         G,
#         pos,
#         with_labels=True,
#         node_size=3000,
#         node_color="lightblue",
#         font_size=10,
#         font_weight="bold",
#         arrows=True,
#     )

#     # edge_labels = {
#     #     (u, v): d["label"]
#     #     for u, v, d in G.edges(data=True)
#     # }
#     edge_labels = {
#     (u, v): f"{d['label']}\n{d['port_from']} → {d['port_to']}"
#     for u, v, d in G.edges(data=True)
#     }

#     nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)

#     plt.title("System Connectivity Graph")
#     plt.show()