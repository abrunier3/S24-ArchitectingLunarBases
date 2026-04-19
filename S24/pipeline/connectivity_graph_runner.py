from typing import Dict, Any, List, Optional

from S24.sysml.interfaces import build_system_graph
from S24.validation.plotter import plot_system_graph


def run_connectivity_graph(
    data: Dict[str, Any],
    *,
    active_nodes: Optional[List[str]] = None,
    json_asset_paths: Optional[List[str]] = None,
    verbose: int = 2,
) -> Dict[str, Any]:
    """
    Build and optionally filter a system connectivity graph.

    Parameters
    ----------
    data : Dict[str, Any]
        Full system data (output of sysml_to_json_transformer)

    active_nodes : Optional[List[str]]
        Subset of nodes to activate. If None → all nodes are used.

    json_asset_paths : Optional[List[str]]
        Paths to per-part JSON files (used to map active nodes → files)

    verbose : int
        0 → no prints / no plots
        1 → summary prints
        2 → detailed prints + plotting

    Returns
    -------
    Dict containing:
        - active_nodes (dict)
        - graph (networkx.DiGraph)
        - connections (filtered)
        - asset_paths (filtered if provided)
    """

    parts = data["parts"]
    connections = data["connections"]

    if active_nodes is None:
        active_nodes = [p["name"] for p in parts]

    active_set = set(active_nodes)


    filtered_parts = [
        p for p in parts if p["name"] in active_set
    ]

    filtered_connections = [
        c for c in connections
        if c["from"]["part"] in active_set
        and c["to"]["part"] in active_set
    ]

    G = build_system_graph(filtered_parts, filtered_connections)

    filtered_asset_paths = None

    if json_asset_paths is not None:
        filtered_asset_paths = [
            path for path in json_asset_paths
            if any(node in str(path) for node in active_set)
        ]

    if verbose >= 1:
        print(f"[GRAPH] Active nodes: {len(filtered_parts)} / {len(parts)}")
        print(f"[GRAPH] Active connections: {len(filtered_connections)} / {len(connections)}")
        print("\n[ACTIVE CONNECTIONS]")
        for c in filtered_connections:
            print(c)
        print("\n[GRAPH OBJECT]")
        print(G)

    if verbose >= 2:
        plot_system_graph(G)


    return {
        "active_nodes": {
            "list": active_nodes,
            "count": len(filtered_parts),
        },
        "graph": G,
        "connections": filtered_connections,
        "asset_paths": filtered_asset_paths,
    }