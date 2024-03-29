import pickle
import numpy as np
import os
from simulation.clustering.clustering_strategy import new_correlation_clustering
from simulation.clustering.clustering_strategy import connected_components_clustering
from simulation.clustering.clustering_strategy import chinese_whisper_clustering
from simulation.clustering.clustering_strategy import louvain_method_clustering

from analysis.comparison_metrics import cluster_num_diff
from analysis.comparison_metrics import jensen_shannon_divergence

from graphs.base_graph import BaseGraph
from visualization.metric_vis import line_ploter
from visualization.graph_visualization import draw_graph_graphviz as draw

path = 'data/graphs/kw29/bigdata/sim/{0}/n100_k{1}_log{2}_0/n100_k{1}_log{2}_0_j{3}.graph'
path_base = 'data/graphs/kw29/bigdata/true/n100_k{0}_log{1}_0.graph'

samplings = ['randomsampling', 'randomwalk', 'pagerank']
logs = [0.1, 0.3, 0.5, 0.7, 0.9]
ks = [1, 3, 5, 7, 10]
steps = [10, 20, 30, 40, 50, 100, 200, 300, 400, 500, 1000, 2000, 3000, 4000, 5000]

for sampling in samplings:
    for k in ks:
        for log in logs:
            dwug_cnd = []
            dwug_csd = []
            ccc_cnd = []
            ccc_csd = []
            cw_cnd = []
            cw_csd = []
            lcd_cnd = []
            lcd_csd = []

            with open(path_base.format(k, log), 'rb') as file:
                base: BaseGraph = pickle.load(file)
            file.close()

            print('sampling: {}, k {}, log {}'.format(sampling, k, log))
            cc = 'data/figs/tmp/graph/{}/cc/k{}/log{}'.format(sampling, k, log)
            ccc = 'data/figs/tmp/graph/{}/ccc/k{}/log{}'.format(sampling, k, log)
            cw = 'data/figs/tmp/graph/{}/cw/k{}/log{}'.format(sampling, k, log)
            lcd = 'data/figs/tmp/graph/{}/lcd/k{}/log{}'.format(sampling, k, log)
            os.makedirs(cc)
            os.makedirs(ccc)
            os.makedirs(cw)
            os.makedirs(lcd)

            for step in steps:
                with open(path.format(sampling, k, log, step), 'rb') as file:
                    graph: BaseGraph = pickle.load(file)
                file.close()

                # print('DWUG Clustering')
                clusters = new_correlation_clustering(graph, {'weights': 'edge_soft_weight', 'max_attempts': 10, 'max_itters': np.inf, 'split_flag': False})
                graph.update_community_nodes_membership(clusters)
                draw(graph, 'Correlation Clustering {}, k{}, log{}, step{}'.format(sampling, k, log, step),
                     save_flag=True, path='{}/k{}_log{}_j{}.png'.format(cc, k, log, step))

                dwug_cnd.append(cluster_num_diff(base, graph, {}))
                dwug_csd.append(jensen_shannon_divergence(base, graph, {}))

                # print('Connected Components Clustering')
                clusters = connected_components_clustering(graph, {'weights': 'edge_soft_weight'})
                graph.update_community_nodes_membership(clusters)
                draw(graph, 'Connected Component Clustering {}, k{}, log{}, step{}'.format(sampling, k, log, step),
                     save_flag=True, path='{}/k{}_log{}_j{}.png'.format(ccc, k, log, step))

                ccc_cnd.append(cluster_num_diff(base, graph, {}))
                ccc_csd.append(jensen_shannon_divergence(base, graph, {}))

                # print('Chinese Whisper Clustering')
                clusters = chinese_whisper_clustering(graph, {'weights': 'edge_soft_weight'})
                graph.update_community_nodes_membership(clusters)
                draw(graph, 'Chinese Whisper Clustering {}, k{}, log{}, step{}'.format(sampling, k, log, step),
                     save_flag=True, path='{}/k{}_log{}_j{}.png'.format(cw, k, log, step))

                cw_cnd.append(cluster_num_diff(base, graph, {}))
                cw_csd.append(jensen_shannon_divergence(base, graph, {}))

                # print('Louvain Community Detection')
                clusters = louvain_method_clustering(graph, {})
                graph.update_community_nodes_membership(clusters)
                draw(graph, 'Louvain Community Detection {}, k{}, log{}, step{}'.format(sampling, k, log, step),
                     save_flag=True, path='{}/k{}_log{}_j{}.png'.format(lcd, k, log, step))

                lcd_cnd.append(cluster_num_diff(base, graph, {}))
                lcd_csd.append(jensen_shannon_divergence(base, graph, {}))

            line_ploter(steps, 'Sampling: {}, k {}, log {}, Cluster # Diff to Base'.format(sampling, k, log), 'Judgements', '#Diff',
                        save_flag=True, save_path='data/figs/tmp/cnd/cnd_{}_k{}_log{}.png'.format(sampling, k, log),
                        dwug=dwug_cnd, ccc=ccc_cnd, cw=cw_cnd, lcd=lcd_cnd)
            line_ploter(steps, 'Sampling: {}, k {}, log {}, JS Divergance'.format(sampling, k, log), 'Judgements', '#Diff',
                        save_flag=True, save_path='data/figs/tmp/csd/csd_{}_k{}_log{}.png'.format(sampling, k, log),
                        dwug=dwug_csd, ccc=ccc_csd, cw=cw_csd, lcd=lcd_csd)
