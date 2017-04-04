import pydot_ng as pd

from load import load_all


def create_graph(maps):
    graph = pd.Dot(graph_type='graph')

    nodes = {}
    for floor, map in maps.items():
        node_name = '{}F'.format(floor)
        nodes[floor] = pd.Node(node_name)
    nodes[101] = pd.Node('Credits')

    for node in nodes.values():
        graph.add_node(node)

    for floor, map in maps.items():
        floor_node = nodes[floor]
        for target_floor, _ in map['targets']:
            if target_floor < floor:
                continue
            target_node = nodes[target_floor]
            edge = pd.Edge(floor_node, target_node)
            graph.add_edge(edge)

    return graph


maps = load_all()
graph = create_graph(maps)
graph.write_png('test.png')
