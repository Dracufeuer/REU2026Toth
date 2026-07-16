import networkx as nx
from scipy.spatial import distance
def stretch_factor(G):
    t = 0

    lengths = dict(nx.all_pairs_dijkstra_path_length(G))


    for u, targets in lengths.items():
        for v, sp_length in targets.items():
            if u == v or G.nodes[u]["color"] == G.nodes[v]["color"]:
                continue
            t = max(t, sp_length/distance.euclidean(u, v))
    return t
