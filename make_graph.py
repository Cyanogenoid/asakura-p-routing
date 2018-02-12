import itertools

import pydot_ng as pd

from load import load_all


def apply_style(floor, map, name):
    style = {}
    label_style = {
        'label': '''<
        <table cellborder="0" border="0">
            <tr>
                <td>{floor}</td>
            </tr>
            <tr>
                <td><img src="data/st_itemicon{icon_id}.png" scale="TRUE"/></td>
            </tr>
        </table>
        >'''.format(icon_id=map['chest'][-1], floor=name),
    }
    shop_style = {'fillcolor': 'orange'} if floor in {8, 43, 63, 97} else {}
    checkpoint_style = {'fillcolor': 'yellow'} if map['chest'][-1] == 29 else {}
    boss_style = {'fillcolor': 'gray'} if floor in {10, 25, 40, 55, 70, 85, 100} else {}

    style.update(label_style)
    style.update(shop_style)
    style.update(checkpoint_style)
    style.update(boss_style)
    return style


def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


any_route = set(pairwise([1,2,3,4,5,6,8,9,10,11,12,18,13,18,12,14,15,19,20,21,24,25,26,27,28,31,32,33,34,35,39,40,41,45,46,50,52,51,46,48,49,41,50,52,55,56,58,60,62,60,58,61,65,67,70,71,73,75,76,81,82,84,82,81,76,75,73,85,98,99,86,87,88,98,99,100,101]))
def apply_edge_style(a, b):
    style = {}
    if (a, b) in any_route or (b, a) in any_route:
        any_route.discard((a, b))
        any_route.discard((b, a))
        style['color'] = 'red'
    return style


def create_graph(maps):
    graph_args = {
        'graph_type': 'graph',
        'bgcolor': 'white',
        'overlap': 'prism',
        'overlap_scaling': 10,
        'ratio': 1.5,
    }
    default_style = {
        'style': 'filled',
        'fillcolor': 'white',
        'shape': 'box',
        'margin': 0,
    }
    graph = pd.Dot(**graph_args)

    nodes = {}
    for floor, map in maps.items():
        node_name = '{}F'.format(floor)
        style = dict(default_style)
        style.update(apply_style(floor, map, node_name))
        nodes[floor] = pd.Node(node_name, **style)
    nodes[101] = pd.Node('Credits', **default_style)

    for node in nodes.values():
        graph.add_node(node)

    for floor, map in maps.items():
        floor_node = nodes[floor]
        for target_floor, _ in map['targets']:
            if target_floor < floor:
                continue
            style = {}
            style.update(apply_edge_style(floor, target_floor))
            target_node = nodes[target_floor]
            edge = pd.Edge(floor_node, target_node, **style)
            graph.add_edge(edge)

    return graph


maps = load_all()
graph = create_graph(maps)
graph.write('test.dot')
