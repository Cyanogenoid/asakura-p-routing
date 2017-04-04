import os

import pydot_ng as pd

from load import load_movedata, load_map


MAP_DIR = './map'


def create_graph(doors):
    graph = pd.Dot(graph_type='graph')

    node_format = '{}F'.format
    nodes = [pd.Node(node_format(i)) for i in doors.keys()]
    nodes.append(pd.Node('Credits'))
    for node in nodes:
        graph.add_node(node)

    for floor, ds in doors.items():
        floor_node = nodes[floor - 1]
        for target_floor, _ in ds:
            if target_floor < floor:
                continue
            d_node = nodes[target_floor - 1]
            edge = pd.Edge(floor_node, d_node)
            graph.add_edge(edge)

    return graph


doors = load_movedata(os.path.join(MAP_DIR, 'MoveData.dat'))
maps = []
for floor in doors.keys():
    path = '{:03d}.map'.format(floor)
    path = os.path.join(MAP_DIR, path)
    maps.append(load_map(path))


graph = create_graph(doors)
graph.write_png('test.png')
