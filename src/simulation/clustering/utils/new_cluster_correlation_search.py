# Assumes that negative edges have weights < 0, and positive edges have weights > 0
# Assumes that edges with nan have been removed
# Assumes that weights are stored under edge attribute G[i][j]['weight']

import sys
from itertools import combinations, product, chain
from collections import defaultdict
import matplotlib.pyplot as plt
import random
import networkx as nx
import numpy as np
from scipy.stats import spearmanr
from networkx.algorithms.dag import transitive_closure
import six
sys.modules['sklearn.externals.six'] = six
import mlrose
import time
from sklearn import metrics
from scipy.optimize import linear_sum_assignment


def cluster_correlation_search(G, s=10, max_attempts=200, max_iters=5000, initial=[], split_flag=True):
    """
    Apply connected_component clustering.
    :param G: graph
    :param s: maximal number of senses a word can have
    :param max_attempts: number of restarts for optimization
    :param max_iters: number of iterations for optimization
    :param initial: optional clustering for initialization
    :param split_flag: optional flag, if non evidence cluster should be splitted
    :return classes, stats: list of clusters, list of stats
    """

    start_time = time.time()
    stats = {}
    G = G.copy()

    if initial == []:  # initialize with connected components unless initial clustering is provided
        classes = cluster_connected_components(G)
    else:
        classes = initial
        # print(initial)

    n2i = {node: i for i, node in enumerate(G.nodes())}
    i2n = {i: node for i, node in enumerate(G.nodes())}
    n2c = {n2i[node]: i for i, cluster in enumerate(
        classes) for node in cluster}

    edges_positive = set([(n2i[i], n2i[j], G[i][j]['weight'])
                         for (i, j) in G.edges() if G[i][j]['weight'] >= 0.0])
    edges_negative = set([(n2i[i], n2i[j], G[i][j]['weight'])
                         for (i, j) in G.edges() if G[i][j]['weight'] < 0.0])

    def conflict_loss(state):
        loss_pos = np.sum(
            [w for (i, j, w) in edges_positive if state[i] != state[j]])
        loss_neg = np.sum(
            [abs(w) for (i, j, w) in edges_negative if state[i] == state[j]])
        loss = loss_pos + loss_neg
        return loss

    # Define initial state
    init_state = np.array([n2c[n] for n in sorted(n2c.keys())])
    loss_init = conflict_loss(init_state)

    if loss_init == 0.0:
        # print('loss_init: ', loss_init)
        classes.sort(key=lambda x: -len(x))  # sort by size
        end_time = time.time()
        stats['runtime'] = (end_time - start_time) / 60
        return classes, stats

    # Initialize custom fitness function object
    conflict_loss_cust = mlrose.CustomFitness(conflict_loss)

    l2s = defaultdict(lambda: [])
    l2s[loss_init].append((init_state, len(classes)))

    for n in range(2, s):

        # With initial state
        max_val = max(n, len(classes))
        problem = mlrose.DiscreteOpt(length=len(
            G.nodes()), fitness_fn=conflict_loss_cust, maximize=False, max_val=max_val)
        # print(n,max_val)

        # Define decay schedule
        schedule = mlrose.ExpDecay()
        # Solve problem using simulated annealing
        best_state, best_fitness = mlrose.simulated_annealing(
            problem, schedule=schedule, init_state=init_state, max_attempts=max_attempts, max_iters=max_iters)

        l2s[best_fitness].append((best_state, max_val))

        # Repeat without initial state
        max_val = n
        problem = mlrose.DiscreteOpt(length=len(
            G.nodes()), fitness_fn=conflict_loss_cust, maximize=False, max_val=max_val)

        schedule = mlrose.ExpDecay()
        best_state, best_fitness = mlrose.simulated_annealing(
            problem, schedule=schedule, max_attempts=max_attempts, max_iters=max_iters)

        l2s[best_fitness].append((best_state, max_val))

    # print(l2s)
    _id = np.random.choice(range(len(l2s[min(l2s.keys())])))
    best_state, best_fitness = l2s[min(l2s.keys())][_id], min(l2s.keys())
    # print('loss: ', best_fitness)

    best_state = best_state[0]

    c2n = defaultdict(lambda: [])
    for i, c in enumerate(best_state):
        c2n[c].append(i2n[i])

    classes = [set(c2n[c]) for c in c2n]

    # Split collapsed clusters without evidence
    if split_flag:
        classes = split_non_evidence_clusters(G, classes)

    classes.sort(key=lambda x: -len(x))  # sort by size

    end_time = time.time()
    stats['runtime'] = (end_time - start_time) / 60

    return classes, stats


def cluster_connected_components(G, is_non_value=lambda x: np.isnan(x)):
    """
    Apply connected_component clustering.
    :param G: graph
    :return classes: list of clusters
    """

    G = G.copy()

    edges_negative = [(i, j) for (i, j) in G.edges() if G[i]
                      [j]['weight'] < 0.0 or is_non_value(G[i][j]['weight'])]
    G.remove_edges_from(edges_negative)
    components = nx.connected_components(G)
    classes = [set(component) for component in components]
    classes.sort(key=lambda x: list(x)[0])

    return classes


def split_non_evidence_clusters(G, clusters, is_non_value=lambda x: np.isnan(x)):
    """
    Split non-positively-connected components.
    :param G: graph
    :param clusters: list of clusters
    :return G:
    """

    G = G.copy()

    nodes_in = [node for cluster in clusters for node in cluster]
    edges_negative = [(i, j) for (i, j) in G.edges() if G[i]
                      [j]['weight'] < 0.0 or is_non_value(G[i][j]['weight'])]
    G.remove_edges_from(edges_negative)  # treat non-edges as non-comparisons

    classes_out = []
    for cluster in clusters:
        subgraph = G.subgraph(cluster)
        components = cluster_connected_components(subgraph)

        for class_ in components:
            classes_out.append(set(class_))

    # check that nodes stayed the same
    nodes_out = [node for class_ in classes_out for node in class_]

    if set(nodes_in) != set(nodes_out):
        sys.exit('Breaking: nodes_in != nodes_out.')
    if len(nodes_in) != len(nodes_out):
        sys.exit('Breaking: len(nodes_in) != len(nodes_out).')

    return classes_out
