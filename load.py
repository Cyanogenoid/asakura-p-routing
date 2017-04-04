import os
from struct import unpack
from itertools import zip_longest


MAP_DIR = './map'


def load_all():
    doors = load_movedata(os.path.join(MAP_DIR, 'MoveData.dat'))
    maps = {}
    for floor in doors.keys():
        path = '{:03d}.map'.format(floor)
        path = os.path.join(MAP_DIR, path)
        maps[floor] = load_map(path)
    # copy over information from doors to maps
    for floor, map in maps.items():
        ds = doors[floor]
        map['targets'] = ds
    return maps


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


def load_map(path):
    d = {}
    # open specified map
    with open(path, 'rb') as f:
        f.seek(4 * 1, 1)

        # tileset filename
        d['tileset'] = f.read(read_int(f)[0])
        f.seek(1, 1)

        # background filename
        d['bg'] = f.read(read_int(f)[0])
        f.seek(1, 1)

        # background music filename
        d['bgm'] = f.read(read_int(f)[0])
        f.seek(1, 1)

        # tiles
        d['tiles'] = {}
        for row in range(48):
            for column in range(77):
                d['tiles'][column, row] = read_int(f, 2)
            f.seek(4 * 2, 1)
        f.seek(4 * 256, 1)

        # enemies
        d['enemies'] = {}
        enemyCount = read_int(f)[0]
        for x in range(0, enemyCount):
            enemy = read_int(f, 3)
            d['enemies'][enemy[0], enemy[1]] = enemy[2]
        d['enemy_set'] = read_int(f)[0]

        # items
        d['items'] = {}
        itemCount = read_int(f)[0]
        for x in range(itemCount):
            item = read_int(f, 3)
            d['items'][item[0], item[1]] = item[2]

        # bubble key
        if read_int(f)[0] == 1:
            d['bubble_key'] = read_int(f, 3)
        else:
            f.seek(4 * 3, 1)

        # key
        if read_int(f)[0] == 1:
            d['key'] = read_int(f, 3)
        else:
            f.seek(4 * 3, 1)

        # chest
        if read_int(f)[0] == 1:
            d['chest'] = read_int(f, 3)
        else:
            f.seek(4 * 3, 1)
        f.seek(4 * 8, 1)

        # moving platforms
        d['moving'] = {}
        movingCount = read_int(f)[0]
        for x in range(0, movingCount):
            m = read_int(f, 3)
            d['moving'][m[0], m[1]] = m[2]

        # jump reduction
        if read_int(f)[0] == 1:
            d['jump_reduction'] = True
        f.seek(4 * 3, 1)

        # inertia
        if read_int(f)[0] == 1:
            d['inertia'] = True
        f.seek(4 * 2, 1)

        # doors
        d['doors'] = {}
        for i in range(4):
            d['doors'][i] = read_int(f, 2)
        f.seek(4 * 1, 1)

        # time
        d['time'] = read_int(f)[0]

    return d


def grouper(n, iterable, fillvalue=None):
    "grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(fillvalue=fillvalue, *args)


def unpack_ints(b):
    nb_ints = len(b) // 4
    return unpack('i' * nb_ints, b)


def dict_map(f, dict):
    return {k: f(v) for k, v in dict.items()}


def read_int(f, i = 1):
    return unpack('i' * i, f.read(4 * i))
