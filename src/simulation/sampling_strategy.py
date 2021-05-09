import random

from true_graph.true_graph import TrueGraph

"""
This module contains different sampling function and can be extended to new ones.
All method signatures should look like this:
    def name(tG: TrueGraph, params: dict) -> list:
Each sampling function should return a list of sampled edges
"""


def random_sampling(tG: TrueGraph, params: dict) -> list:
    """
    Random sampling. 
    As described in TACL paper 'Word Usage Graphs (WUGs):Measuring Changes in Patterns of Contextual Word Meaning'

    This implementation takes n radom edges (:sample_size:) from the TrueGraph and returns it.

    Args:
        :param tG: TrueGraph to sample
        :param sample_size: number of edges to sample
        :return sampled_edge_list: sampled edges with weights as [(u, v, w)...]
    
    """
    assert type(tG) == TrueGraph

    sample_size = params.get('sample_size', None)
    assert sample_size != None and type(sample_size) == int

    sampled_edge_list = []

    for i in range(sample_size):
        u, v = sorted(random.sample(range(1,len(tG.G)), 2))
        sampled_edge_list.append((u, v, tG.sample_edge(u, v)))

    return sampled_edge_list
