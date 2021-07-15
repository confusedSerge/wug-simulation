from graphs.base_graph import BaseGraph
from simulation.stopping.utils.stopping_utils import check_connectivity_two_clusters
from simulation.stopping.utils.stopping_utils import random_sample as _rs

import numpy as np

"""
This module contains different stopping criterion functions and can be extended to new ones.
All method signatures should look like this:
    def name(graph: BaseGraph, params: dict) -> bool:
Each stopping criterion function should only return a boolean, that indicates, if the criterion is reached  
"""


def cluster_connected(graph: BaseGraph, params: dict) -> bool:
    """
    Cluster connectivity as described in paper:
     'Word Usage Graphs (WUGs):Measuring Changes in Patterns of Contextual Word Meaning'

    This criterion looks, if all clusters with minimum size m are connected at least with n edges with every other cluster.
    If only 1 community exist, that is bigger than m, and its size is bigger than max_size_one_cluster, this function returns true.

    Args:
        :param graph: Graph to check on
        :param cluster_min_size: minimum size of cluster to consider, default = 5
        :param min_num_edges: minimum number of edges between clusters, 
            can be int for number of edges, or 'fully' for fully connected clusters; default = 1
        :param min_size_one_cluster: int at which this function considers the only cluster as big enough
        :return flag: if stopping criterion is met
    """
    # ===Guard Phase===
    cluster_min_size = params.get('cluster_min_size', 5)
    assert type(cluster_min_size) == int

    min_num_edges = params.get('min_num_edges', 1)
    assert type(min_num_edges) == int or min_num_edges == 'fully'

    min_size_one_cluster = params.get(
        'min_size_one_cluster', graph.get_number_nodes())
    assert type(min_size_one_cluster) == int

    communities = []
    for k, v in graph.get_community_nodes().items():
        if len(v) >= cluster_min_size:
            communities.append(v)
    # ===Guard Phase End===

    if len(communities) == 0:
        return False

    if len(communities) == 1:
        return len(communities[0]) >= min_size_one_cluster

    flag = True

    for i in range(len(communities)):
        for j in range(i + 1, len(communities)):
            min_connections = min_num_edges if min_num_edges != 'fully' else len(
                communities[i]) * len(communities[j])
            flag = flag and check_connectivity_two_clusters(
                graph.G.edges(), communities[i], communities[j], min_connections)

    return flag


def number_edges_found(graph: BaseGraph, params: dict) -> bool:
    """
    Rather simple stopping criterion, where if an number of edges has been discovered,
    this returns true.
    This means, if the graph contains at least n edges, it returns true, else false.
    Args:
        :param graph: Graph to check on
        :param number_edges: number of edges that sG should contain
        :return flag: if sG contains the number of edges
    """
    number_edges = params.get('number_edges', None)
    assert type(number_edges) == int

    return graph.get_number_edges() >= number_edges


def percentage_edges_found(graph: BaseGraph, params: dict) -> bool:
    """
    Rather simple stopping criterion, where if the graph contains a certain percentage of edges
    this returns true.
    Args:
        :param graph: graph to check on
        :param percentage: percentage of edges that sG should contain
        :param number_edges: number of max edges
        :return flag: if sG contains the percentage of edges
    """
    percentage = params.get('percentage', None)
    assert type(percentage) == float

    number_edges = params.get('number_edges', None)
    assert type(number_edges) == int

    return graph.get_number_edges() >= (percentage * number_edges)

def edges_added(graph: BaseGraph, params: dict) -> bool:
    """
    Rather simple stopping criterion, where it checks how many edges were added to the graph.
    Important, duplicate are also included
    Args:
        :param graph: to check on
        :param num_edges: number of max edges added
        :return flag: if sG contains the percentage of edges
    """
    number_edges = params.get('number_edges', None)
    assert type(number_edges) == int

    return graph.get_num_added_edges() >= number_edges

def bootstraping(graph: BaseGraph, params: dict) -> bool:
    """
    Checks if for a given statistic the confidence interval bounds 
        is higher than the target interval bounds.

    Args:
        :param graph: to check on
        :param rounds: rounds to perform sampling
        :param sample_size: samples per round
        :param alpha: percentile
        :param bound: (target lower, target upper) bound
        :param stat_func: statistical function to be used 
        :param stat_params: statistical params
    """
    rounds = params.get('rounds', None)
    assert type(rounds) == int    
    
    sample_size = params.get('sample_size', None)
    assert type(sample_size) == int

    alpha = params.get('alpha', None)
    assert type(alpha) == float

    bound = params.get('bound', None)
    assert type(bound) == tuple and len(bound) == 2

    stat_func = params.get('stat_func', None)
    assert callable(stat_func)

    stat_params = params.get('stat_params', None)
    assert type(stat_params) == dict

    stats = []
    for _ in rounds:
        g = BaseGraph()
        g.add_edges(_rs(graph, sample_size))
        stats.append(stat_func(g, params))

    stats.sort()
    percentile = np.percentile(stats, [((1.0 - alpha) / 2.0) * 100, (alpha + ((1.0 - alpha) / 2.0)) * 100])
    return bound[0] <= percentile[0] and bound[1] <= percentile[1]

    
