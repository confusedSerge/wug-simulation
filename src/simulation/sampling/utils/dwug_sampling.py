import random
import numpy as np

from graphs.base_graph import BaseGraph
from simulation.sampling.sampling_strategy import random_sampling


def dwug_sampling(sample_graph: BaseGraph, annotated_graph: BaseGraph, percentage_nodes: float or int, percentage_edges: float or int, min_size_mc: int, num_flag: bool = False, random_sample_empty_round: int = 0) -> list:
    """
    Uses the DWUG sampling strategy, as described in the paper.

    Args:
        :param sample_graph: graph on which to sample edge weight
        :param annotated_graph: annotation graph
        :param percentage_nodes: percentage of nodes to add this round
        :param percentage_edges: percentage of edges to add this round
        :param min_size_mc: minimum size of cluster to be considered as multi-cluster
        :param num_flag: if :percentage_nodes: & :percentage_edges: are the actual number of nodes/edges to be used  (optional)
        :param random_sample_empty_round: if set, on empty rounds the amount of edges will be random sampled
    """
    if annotated_graph.get_number_edges() == 0:
        # initial exploration
        return _z_sampling_round(sample_graph, percentage_nodes, percentage_edges, num_flag)
    edges = _n_sampling_round(sample_graph, annotated_graph, min_size_mc, percentage_nodes, percentage_edges, num_flag)

    if len(edges) == 0 and random_sample_empty_round > 0:
        edges = random_sampling(sample_graph, {'sample_size': random_sample_empty_round})

    return edges


def _z_sampling_round(sample_graph: BaseGraph, percentage_nodes: float, percentage_edges: float, num_flag: bool) -> list:
    number_nodes = percentage_nodes if num_flag else round(sample_graph.get_number_nodes() * percentage_nodes)

    try:
        nodes = np.random.choice(sample_graph.G.nodes(), number_nodes, replace=False)
    except ValueError:
        nodes = sample_graph.G.nodes()

    max_edges = percentage_edges if num_flag else len(nodes) * (len(nodes) - 1) * 0.5 * percentage_edges

    return _exploration_phase(sample_graph, nodes, max_edges)


def _n_sampling_round(sample_graph: BaseGraph, annotated_graph: BaseGraph, min_size_mc: int, percentage_nodes: float, percentage_edges: float, num_flag: bool) -> list:
    # Nodes not in cluster size >= min_size_mc
    nodes = [node for k, v in annotated_graph.get_community_nodes().items() if len(v) < min_size_mc for node in v]
    multi_clusters = [v for k, v in annotated_graph.get_community_nodes().items() if len(v) >= min_size_mc]

    # Find nodes to be used in the sample round
    combination_nodes = []
    exploration_nodes = []

    for node in nodes:
        cn_flag = False
        for cluster in multi_clusters:
            cn_flag |= not _check_node_cluster_con(annotated_graph, node, cluster)

        if cn_flag:
            combination_nodes.append(node)
        else:
            exploration_nodes.append(node)

    # add new nodes to combination phase
    not_added_nodes = list(set(sample_graph.G.nodes()) - set(annotated_graph.G.nodes()))
    num_new_nodes_add = percentage_nodes if num_flag else round(sample_graph.get_number_nodes() * percentage_nodes)

    try:
        new_nodes = np.random.choice(not_added_nodes, num_new_nodes_add, replace=False)
    except ValueError:
        new_nodes = not_added_nodes

    combination_nodes.extend(new_nodes)
    max_edges = percentage_edges if num_flag else len(exploration_nodes) * (len(exploration_nodes) - 1) * 0.5 * percentage_edges

    # execute both phases
    sampled_edge_list = []
    sampled_edge_list.extend(_combination_phase(sample_graph, annotated_graph, combination_nodes, multi_clusters))
    sampled_edge_list.extend(_exploration_phase(sample_graph, exploration_nodes, max_edges))

    return sampled_edge_list


def _combination_phase(sample_graph: BaseGraph, annotated_graph: BaseGraph, nodes: list, multi_clusters: list) -> list:
    if len(nodes) == 0:
        return []

    sampled_edge_list = []

    for node in nodes:
        for cluster in multi_clusters:
            if not _check_node_cluster_con(annotated_graph, node, cluster):
                connection = random.choice(cluster)
                sampled_edge_list.append((node, connection, sample_graph.get_edge(node, connection)))

    return sampled_edge_list


def _check_node_cluster_con(graph: BaseGraph, node: int, cluster: list) -> bool:
    for c_node in cluster:
        u, v = sorted([node, c_node])
        if graph.get_edge(u, v) is not None:
            return True

    return False


def _exploration_phase(sample_graph: BaseGraph, nodes: list, max_edges: float) -> list:
    # RandomWalk till percentage edges found
    if len(nodes) == 0 or len(nodes) == 1:
        return []

    sampled_edge_list = []
    last_node = random.choice(nodes)

    while len(sampled_edge_list) < max_edges:
        next_node = random.choice(np.delete(np.array(nodes), np.where(np.array(nodes) == last_node)))
        sampled_edge_list.append((last_node, next_node, sample_graph.get_edge(last_node, next_node)))
        last_node = next_node

    return sampled_edge_list
