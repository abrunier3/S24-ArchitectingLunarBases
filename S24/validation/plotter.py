import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict

from S24.sysml.interfaces import build_system_graph


def compute_system_layout(G):
    return {
        "SolarPowerSystem": (0, 2),
        "ISRUPlant": (2, 2),
        "Rover": (4, 2),
        "Propellant_Depot": (6, 2),
        "HabitationModule": (2, 0.5),
        "LaunchLandingZone": (2, -1),
    }


def get_edge_color(flow):
    flow = str(flow).strip().upper()
    if flow == "LOX":
        return "blue"
    elif flow == "POWER":
        return "red"
    elif flow == "REGOLITH":
        return "brown"
    return "gray"


def plot_system_graph(G):
    pos = compute_system_layout(G)
    plt.figure(figsize=(14, 8))

    edge_groups = defaultdict(list)
    for u, v, d in G.edges(data=True):
        edge_groups[(u, v)].append((u, v, d))

    for (u, v), group in edge_groups.items():
        n = len(group)
        if n == 1:
            rads = [0.15]
        else:
            rads = [0.25 * (i - (n - 1) / 2) for i in range(n)]

        for (u, v, d), rad in zip(group, rads):
            flow = str(d.get("flow", "")).strip().upper()
            color = get_edge_color(flow)

            nx.draw_networkx_edges(
                G,
                pos,
                edgelist=[(u, v)],
                edge_color=color,
                width=3.2 if flow == "LOX" else 2.4,
                arrows=True,
                arrowstyle='-|>',
                arrowsize=20,
                min_source_margin=25,
                min_target_margin=25,
                connectionstyle=f"arc3,rad={rad}"
            )

    nx.draw_networkx_nodes(
        G,
        pos,
        node_size=6500,
        node_color="lightblue",
        edgecolors="black",
        linewidths=1.5
    )

    nx.draw_networkx_labels(
        G,
        pos,
        font_size=10,
        font_weight="bold"
    )

    for (u, v), group in edge_groups.items():
        n = len(group)
        if n == 1:
            rads = [0.15]
        else:
            rads = [0.25 * (i - (n - 1) / 2) for i in range(n)]

        for (u, v, d), rad in zip(group, rads):
            flow = str(d.get("flow", "")).strip()
            x1, y1 = pos[u]
            x2, y2 = pos[v]

            mx = (x1 + x2) / 2
            my = (y1 + y2) / 2

            dx = x2 - x1
            dy = y2 - y1
            norm = np.hypot(dx, dy)

            if norm != 0:
                nx_perp = -dy / norm
                ny_perp = dx / norm
            else:
                nx_perp, ny_perp = 0, 0

            offset = rad * 2.5

            mx += nx_perp * offset
            my += ny_perp * offset

            plt.text(
                mx,
                my,
                flow,
                fontsize=9,
                ha='center',
                va='center',
                bbox=dict(facecolor='white', edgecolor='none', alpha=0.7)
            )

    plt.title("System Connectivity Graph", fontsize=14)
    plt.axis("off")
    plt.tight_layout()
    plt.show()