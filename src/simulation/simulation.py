from graphs.base_graph import BaseGraph

"""
This module contains different simulations and can be extended to new ones.


"""

def simulation(trueGraph: BaseGraph, simulationGraph: BaseGraph, max_iter: int = 500, save_flag: bool = False, save_path: str = None, **params) -> (BaseGraph, BaseGraph, bool):
    """
    Runs the simulation for the given iterations.
    Every iteration consists of a sampling phase, clustering (optional) phase, and checking the stopping criterion.

    Args:
        :param tG: True Graph used for sampling
        :param simulationGraph: Simulation graph, if provided starts/continues the simulation based on this graph
        :param max_iter: maximal iterations to prevent non ending simulations, default 500 iterations
        :param save_flag: if results should be saved
        :param save_path: path to save to

        :param sampling_strategy: function to use for sampling
        :param sampling_params: params as dict for sampling function
        :param clustering_strategy: function to use for clustering (optional)
        :param clustering_params: params as dict for clustering function
        :param stopping_criterion: function to use as stopping criterion
        :param stopping_params: params as dict for stopping criterion
        :return tuple: returns a tuple containing the simulation graph, the true graph used, 
            and if maximal iteration was hit
    """
    # ===Guard Phase===
    if len(params) == 1:
        params = params['params']

    sampling_strategy = params.get('sampling_strategy', None)
    assert sampling_strategy != None
    
    sampling_params = params.get('sampling_params', None)
    assert type(sampling_params) == dict

    clustering_flag = False
    clustering_strategy = params.get('clustering_strategy', None)

    if clustering_strategy != None:
        clustering_flag = True

        clustering_params = params.get('clustering_params', None)
        assert type(clustering_params) == dict
    
    stopping_criterion = params.get('stopping_criterion', None)
    assert stopping_criterion != None
    
    stopping_params = params.get('stopping_params', None)
    assert type(stopping_params) == dict
    # ===Guard Phase===

    for _ in range(max_iter):
        # sampling phase
        sampled_edges = sampling_strategy(trueGraph, sampling_params)
        simulationGraph.add_edges(sampled_edges)

        # clustering phase
        if clustering_flag:
            clusters = clustering_strategy(simulationGraph, clustering_params)
            simulationGraph.update_community_nodes_membership(clusters)

        # stopping criterion
        if stopping_criterion(simulationGraph, stopping_params):
            break

    return (trueGraph, simulationGraph, _ + 1 >= max_iter)


def simulation_with_tG_generator(trueGraphs, simulationGraphClass, max_iter: int = 500, save_flag: bool = False, save_path: str = None, **params) -> list:
    """
    See documentation simulation.
    The big difference is, that this function takes in an BaseGraph generator 
        and for each simulation creates a new simulationGraph based on the class given
    """
    results = []
    for trueGraph in trueGraphs:
        simulationGraph = simulationGraphClass()
        results.append(simulation(trueGraph, simulationGraph, max_iter, save_flag, save_path, params=params))

    return results

