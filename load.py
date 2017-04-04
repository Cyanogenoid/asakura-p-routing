from struct import unpack
from itertools import zip_longest


def load_movedata(path):
    with open(path, 'rb') as fd:
        b = fd.read() 
    ints = unpack_ints(b)
    target_floors = ints[0::2]
    target_spawns = ints[1::2]
    all_doors = zip(target_floors, target_spawns)
    doors_grouped_by_floor = grouper(4, all_doors)
    doors_of_floor = dict(enumerate(doors_grouped_by_floor, start=1))
    filter_empty_doors = lambda doors: [d for d in doors if d != (0, 0)]
    doors_of_floor = dict_map(filter_empty_doors, doors_of_floor)
    return doors_of_floor
    

def grouper(n, iterable, fillvalue=None):
    "grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(fillvalue=fillvalue, *args)


def unpack_ints(b):
    nb_ints = len(b) // 4
    return unpack('i' * nb_ints, b)


def dict_map(f, dict):
    return {k: f(v) for k, v in dict.items()}
