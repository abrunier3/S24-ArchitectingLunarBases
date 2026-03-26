import networkx as nx
import matplotlib.pyplot as plt

from S24.sysml.interfaces import compute_flow_layout, build_system_graph


def plot_system_graph(G):
    pos = compute_flow_layout(G)

    plt.figure(figsize=(14, 8))

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

    nx.draw(
        G,
        pos,
        with_labels=True,
        node_size=10000,
        node_color="lightblue",
        font_size=10,
        font_weight="bold",
        arrows=True,
        edge_color=edge_colors,
        width=2,
        arrowsize=20 
    )

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

