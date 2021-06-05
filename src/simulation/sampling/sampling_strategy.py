import random
import numpy as np

from graphs.base_graph import BaseGraph
from graphs.wu_annotator_graph import WUAnnotatorGraph
from graphs.wu_annotator_simulation_graph import WUAnnotatorSimulationGraph

from simulation.sampling.utils.dwug_sampling import dwug_sampling as u_dwug_sampling

"""
This module contains different sampling function and can be extended to new ones.
All method signatures should look like this:
    def name(tG: TrueGraph, params: dict) -> list:
Each sampling function should return a list of sampled edges
"""


def random_sampling(trueGraph: BaseGraph, params: dict) -> list:
    """
    Random sampling. 
    As described in TACL paper 'Word Usage Graphs (WUGs):Measuring Changes in Patterns of Contextual Word Meaning'

    This implementation takes n radom edges (:sample_size:) from the TrueGraph and returns it.

    Args:
        :param trueGraph: TrueGraph to sample
        :param sample_size: number of edges to sample
        :return sampled_edge_list: sampled edges with weights as [(u, v, w)...]
    
    """
    assert isinstance(trueGraph, BaseGraph)

    sample_size = params.get('sample_size', None)
    assert sample_size != None and type(sample_size) == int

    sampled_edge_list = []

    for i in range(sample_size):
        u, v = sorted(random.sample(trueGraph.G.nodes(), 2))
        sampled_edge_list.append((u, v, trueGraph.get_edge(u, v)))

    return sampled_edge_list

def page_rank(trueGraph: BaseGraph, params: dict) -> list:
    """
    Page Rank sampling strategy with equal transition probability.

    Important to note:
        - tp_coef == 1: Random Sample
        - tp_coef == 0: Random Walk

    Args:
        :param trueGraph: TrueGraph to sample
        :param sample_size: number of edges to sample per annotator
        :param start: start node (can be None, int, or function)
        :param tp_coef: teleportation coefficient
        :return sampled_edge_list: sampled edges with weights as [(u, v, w)...]

    """
    # ===Guard===
    sample_size = params.get('sample_size', None)
    assert type(sample_size) == int and sample_size > 0

    tp_coef = params.get('tp_coef', None)
    assert type(tp_coef) == float and 0 <= tp_coef <= 1

    last_node = params.get('start', None)
    if callable(last_node):
        last_node = last_node()

    assert type(last_node) == int or last_node == None 

    if last_node == None:
        last_node = random.sample(trueGraph.G.nodes(), 1)[0]
    # ===END Guard===

    sampled_edge_list = []

    for i in range(sample_size):
        # choose next start and following node
        last_node = np.random.choice([last_node, random.sample(trueGraph.G.nodes(), 1)[0]], p=[1 - tp_coef, tp_coef])
        next_node = random.sample(trueGraph.G.nodes(), 1)[0]

        sampled_edge_list.append((last_node, next_node, trueGraph.get_edge(last_node, next_node)))
        last_node = next_node

    return sampled_edge_list

def dwug_sampling(trueGraph: BaseGraph, params: dict) -> list:
    """
    Uses the DWUG sampling strategy, as described in the paper.

    Args:
        :param trueGraph: graph on which to sample edge weight
        :param simulationGraph: simulation graph
        :param percentage_nodes: percentage of nodes to add this round
        :param percentage_edges: percentage of edges to add this round
        :param min_size_mc: minimum size of cluster to be considered as multi-cluster
        :param num_flag: if :percentage_nodes: & :percentage_edges: are the actual number of nodes/edges to be used  (optional)
        :return sampled_edge_list: sampled edges with weights as [(u, v, w)...]
    """
    # ===Guard Phase===
    assert isinstance(trueGraph, BaseGraph)

    simulationGraph = params.get('simulationGraph', None)
    assert simulationGraph != None and isinstance(simulationGraph, BaseGraph)

    percentage_nodes = params.get('percentage_nodes', None)
    assert (type(percentage_nodes) == float and 0.0 <= percentage_nodes <= 1.0) or (type(percentage_nodes) == int and 0 <= percentage_nodes <= trueGraph.get_number_nodes())

    percentage_edges = params.get('percentage_edges', None)
    assert (type(percentage_edges) == float and 0.0 <= percentage_edges <= 1.0) or (type(percentage_edges) == int and 0 <= percentage_edges <= trueGraph.get_number_edges())
    min_size_mc = params.get('min_size_mc', None)
    assert type(min_size_mc) == int

    num_flag = params.get('num_flag', False)
    assert type(num_flag) == bool
    # ===Guard Phase over===

    return u_dwug_sampling(trueGraph, simulationGraph, percentage_nodes, percentage_edges, min_size_mc, num_flag)