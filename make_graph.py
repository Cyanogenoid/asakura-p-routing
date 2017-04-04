import pydot_ng as pd

from load import load_all


def apply_style(floor, map):
    style = {}
    chest_style = {
         6: {'color': 'orange'},
        29: {'fillcolor': 'yellow'},
    }.get(map['chest'][-1], {})
    shop_style = {'fillcolor': 'orange'} if floor in [8, 43, 63, 97] else {}

    style.update(chest_style)
    style.update(shop_style)
    return style


def create_graph(maps):
    graph = pd.Dot(graph_type='graph', bgcolor='white')

    nodes = {}
    for floor, map in maps.items():
        node_name = '{}F'.format(floor)
        style = {
            'style': 'filled',
            'fillcolor': 'white',
        }
        style.update(apply_style(floor, map))
        nodes[floor] = pd.Node(node_name, **style)
    nodes[101] = pd.Node('Credits', **style)

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
