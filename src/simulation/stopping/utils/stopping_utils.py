import numpy as np
import random
from collections import Counter
from graphs.base_graph import BaseGraph
from sklearn.metrics import mean_squared_error
from scipy.spatial.distance import jensenshannon


def length_padding(list1: list, list2: list) -> (list, list):
    """
    Pads list with zeros till both have same length.
    Args:
        :param list1: first list
        :param list2: second list
    """
    n_l1, n_l2 = list1.copy(), list2.copy()
    if len(n_l1) == len(n_l2):
        return n_l1, n_l2

    if len(n_l1) < len(n_l2):
        n_l1.extend([0] * (len(n_l2) - len(n_l1)))
        return n_l1, n_l2

    n_l2.extend([0] * (len(n_l1) - len(n_l2)))
    return n_l1, n_l2


def clean_labels(ref_labels: list, current_labels: list) -> (list, list):
    """
    Uses the reference labels and current labels to create two list of the same size,
        only holding labels, where current labels is not -1.

    Args:
        :param ref_labels: containing real labels
        :param current_labels: containing simulated labels
        :return (list, list): new calculated lists, (ref, current)
    """
    assert len(ref_labels) == len(current_labels)

    new_ref = []
    new_crr = []

    for i in range(len(ref_labels)):
        if current_labels[i] != -1 and ref_labels[i] != -1:
            new_ref.append(ref_labels[i])
            new_crr.append(current_labels[i])

    return new_ref, new_crr


def random_sample(graph: BaseGraph, sample_size: int) -> list:
    sampled_edge_list = []
    for _ in range(sample_size):
        u, v = sorted(random.sample(graph.G.nodes(), 2))
        sampled_edge_list.append((u, v, graph.get_edge(u, v)))

    return sampled_edge_list


def check_connectivity_two_clusters(edge_list: list, f_community: list, s_community: list, min_connections: int) -> bool:
    """
    Check if minimum connections between both communities.

    Args:
        :param edge_list: edge list on which to check
        :param f_community: first node list
        :param f_community: second node list
        :param min_connections: minimum connection so that it evaluates to True
    """
    count = 0
    for u in f_community:
        for v in s_community:
            if (u, v) in edge_list:
                count += 1
                if count >= min_connections:
                    return True

    return False


def apd(graph: BaseGraph, sample_size: int) -> float:
    """
    Calculates the APD (Average Pointwise Distance) of a graph (edge weights describing the distance).

    Args:
        :param graph: graph on which to calculate
        :param sample_size: the sample size to take from the graph
        :return float: apd of the sample
    """
    sampled_edge_list = []

    for _ in range(sample_size):
        u, v = sorted(random.sample(graph.G.nodes(), 2))
        sampled_edge_list.append(graph.get_edge(u, v))

    return sum(sampled_edge_list) / sample_size


def entropy_approximation(graph: BaseGraph, threshold: float) -> float:
    """
    Calculates the approximate entropy of an unclustered graph.
    Args:
        :param graph: on which to performe the evaluation
        :param threshold: which edges to consider
        :returns float: value of the metric
    """
    num_nodes = graph.get_number_nodes()
    node_num_edges_over_threshold = Counter([node for k, v in graph.get_weight_edge().items() if k >= threshold for t in v for node in t])

    s_sum = 0
    for i in graph.G.nodes():
        s_sum += np.log2((1 + node_num_edges_over_threshold.get(i, 0)) / num_nodes)

    return -(s_sum / num_nodes)


def mse_mean(time_series: list) -> float:
    _mean = [np.mean(time_series)] * len(time_series)
    return mean_squared_error(time_series, _mean)


def rmse_mean(time_series: list) -> float:
    _mean = [np.mean(time_series)] * len(time_series)
    return mean_squared_error(time_series, _mean, squared=False)


def random_sample_cluster(graph: BaseGraph, sample_size: int) -> list:
    """
    Random samples cluster distribution from provided graph.

    Args:
        :param graph: Clustered Graph
        :param sample_size: Number of nodes to sample with replacement
    """
    community_sizes: list = [0] * graph.get_number_communities()

    for node in np.random.choice(graph.G.nodes(), sample_size):
        community_sizes[graph.get_community_of_node(node)] += 1

    return community_sizes


def jensen_shannon_divergence(reference_graph: BaseGraph, graph: BaseGraph) -> float:
    """
    Calculates the Jensen Shannon Divergence between two clustered graphs

    Args:
        :param reference_graph: reference graph
        :param graph: graph to check against reference
        :returns float: Jensen Shannon Distance value
    """
    # get community probability vec
    ref_cluster_prob = [com / reference_graph.get_number_nodes() for com in reference_graph.get_community_sizes()]
    g_cluster_prob = [com / graph.get_number_nodes() for com in graph.get_community_sizes()]

    # size them to same size
    for _ in range(len(g_cluster_prob), len(ref_cluster_prob)):
        g_cluster_prob.append(0.0)
    for _ in range(len(ref_cluster_prob), len(g_cluster_prob)):
        ref_cluster_prob.append(0.0)

    return jensenshannon(ref_cluster_prob, g_cluster_prob, base=2)**2


def pertubate(graph: BaseGraph, range_judgements: tuple = (1, 4), share: float = 0.1) -> BaseGraph:
    new_graph: BaseGraph = BaseGraph()
    edges = list(graph.G.edges())

    for edge in edges:
        new_graph.add_edge(*edge, graph.get_edge(*edge))

    try:
        mod_edge = [edges[i] for i in np.random.choice(len(edges), int(len(edges) * share), replace=False)]
    except ValueError:
        mod_edge = edges

    for edge in mod_edge:
        we = new_graph.get_edge_weight_history(*edge)
        we.append(random.randint(range_judgements[0], range_judgements[1]))
        new_graph.add_edge(*edge, np.median(we))

    return new_graph


def gen_labels(graph: BaseGraph) -> list:
    labels = [-1] * (max(graph.G.nodes()) + 1)

    for k, v in graph.G.graph['node_community'].items():
        labels[k] = v
    return labels
