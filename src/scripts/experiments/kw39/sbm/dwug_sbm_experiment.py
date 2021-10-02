import os
import pickle
import numpy as np

from graphs.base_graph import BaseGraph
from graphs.annotated_graph import AnnotatedGraph

from simulation.simulation import Simulation

from simulation.sampling.sampling import Sampling
from simulation.sampling.adv_sampling_strategy import dwug_sampling
from simulation.sampling.annotator import Annotator

from simulation.clustering.clustering import Clustering
from simulation.clustering.clustering_strategy import sbm_clustering

from simulation.utils.metric_listener import MetricListener
from analysis.comparison_metrics import adjusted_rand_index, jensen_shannon_divergence
from analysis.metrics import cluster_number, bootstraping_jsd, bootstraping_perturbation_ari

from simulation.utils.intermediate_save_listener import IntermediateSaveListener

path_true = 'data/graphs/kw32/simulation_graphs'
path_out = 'data/graphs/kw39/sim/dwug/{}'
file_suffix = '.graph'
rounds = 1

# get all graphs paths
paths_to_true = []
for _, _, files in os.walk(path_true):
    file: str
    for file in files:
        if file.endswith(file_suffix):
            paths_to_true.append((file, '{}/{}'.format(path_true, file)))
paths_to_true.sort()

# Run Sim
checkpoints = [10, 20, 30, 40, 50, 100, 200, 300, 400, 500, 1000, 2000, 3000, 4000, 5000]

name: str
path: str
for i, (name, path) in enumerate(paths_to_true):
    for _round in range(rounds):
        print("Graph {}: Round: {}".format(name, _round))
        with open(path, 'rb') as graph_file:
            graph: BaseGraph = pickle.load(graph_file)
        graph_file.close()

        annotated_graph = AnnotatedGraph(graph.get_number_nodes())

        sampling_step = Sampling(annotations_per_edge=1).add_adv_sampling_strategie(dwug_sampling, {'percentage_nodes': 0.1, 'percentage_edges': 0.1, 'min_size_mc': 2}, None)\
            .add_annotator(Annotator().add_error_sampling(np.random.poisson, dict(lam=0.35), 1, 4, 0.5))\
            .add_annotator(Annotator().add_error_sampling(np.random.poisson, dict(lam=0.35), 1, 4, 0.5))\
            .add_annotator(Annotator().add_error_sampling(np.random.poisson, dict(lam=0.35), 1, 4, 0.5))\
            .add_annotator(Annotator().add_error_sampling(np.random.poisson, dict(lam=0.35), 1, 4, 0.5))\
            .add_annotator(Annotator().add_error_sampling(np.random.poisson, dict(lam=0.35), 1, 4, 0.5))\
            .set_annotator_dist('random')

        clustering = Clustering().add_clustering_strategy(sbm_clustering, {})

        metric = MetricListener('{}-{}-dwug_1_sbm'.format(name.replace(file_suffix, ''), _round), path_out.format(
            '{}-{}-dwug_1_sbm'.format(name.replace(file_suffix, ''), _round)), checkpoints, annotated_graph.get_num_added_edges)\
            .add_simple_metric('cluster_number', cluster_number, {})\
            .add_comparison_metric('jsd', jensen_shannon_divergence, {})\
            .add_comparison_metric('ari', adjusted_rand_index, {})\

        listener = IntermediateSaveListener()\
            .add_listener(checkpoints, path_out.format('{}-{}-dwug_1_sbm'.format(name.replace(file_suffix, ''), _round)),
                          '{}-{}-dwug_sbm_1_j'.format(name.replace(file_suffix, ''), _round), annotated_graph.get_num_added_edges)\

        simulation = Simulation(600, verbose=True).add_step(sampling_step).add_step(clustering).add_step(metric).add_step(listener)
        simulation.run(graph, annotated_graph)
