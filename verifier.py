import sys

from load import load_all

path = sys.argv[1]


MAPS = load_all()


class State:
    def __init__(self):
        self.coin_floors = {x for x in range(1, 101) if MAPS[x]['chest'][-1] == MAPS[1]['chest'][-1]}
        self.mp_floors = {x for x in range(1, 101) if MAPS[x]['chest'][-1] == MAPS[5]['chest'][-1]}
        self.shop_costs = {
            8: 8,
            43: 15,
            63: 13,
            97: 15,
        }

        self.keys = set()
        self.chests = set()
        self.previous_room = None
        self.coins_used = 0

    @property
    def coins_available(self):
        return len(state.chests & self.coin_floors) - self.coins_used

    @property
    def mp_available(self):
        return 16 + len(state.chests & self.mp_floors) + 2 * (4 - len(self.shop_costs))



def check_line(state, line):
    line = line.split('#')[0].strip()
    if not line:
        return
    if line.startswith('status'):
        print(f'''\
{line}
keys: {len(state.keys)}
chests: {len(state.chests)}
coins: {state.coins_available}
mp: {state.mp_available}''')
        return
    
    components = line.split(' ')
    if len(components) == 1:
        room = components[0]
        actions = ''
    else:
        room, actions = components
        
    if room[-1] != 'F':
        yield ValueError('Invalid floor specifier')
    if room[0] == '?':
        room = None
    else:
        room = int(room[:-1])

    # floor transition
    if room is not None and state.previous_room is not None and room not in {floor for floor, _ in MAPS[state.previous_room]['targets']}:
        if MAPS[room]['chest'][-1] != 29:
            yield ValueError(f'Impossible room transition from {state.previous_room} to {room}')
        elif room not in state.chests:
            yield ValueError(f'Checkpoint not yet collected in {room}')
    # actions
    for action in actions:
        yield from check_action(state, room, action)

    state.previous_room = room


def check_action(state, room, action):
    if action == 'k':
        # key already collected? (possible with glitch, so only warn)
        if room in state.keys:
            yield ValueError(f'Warning, key already collected on {room}F')
        state.keys.add(room)
    elif action == 'c':
        # chest already collected?
        if room in state.chests:
            yield ValueError(f'Chest already collected on {room}F')
        # enough keys available?
        if len(state.chests) >= len(state.keys):
            yield ValueError(f'Not enough keys to collect chest on {room}F')
        state.chests.add(room)
    elif action == 's':
        price = state.shop_costs.get(room)
        if not price:
            yield ValueError(f'Nothing to buy on {room}F')
        if price > state.coins_available:
            yield ValueError(f'Not enough to buy out shop on {room}F')
        state.coins_used += price
        del state.shop_costs[room]



def check_final_state(state):
    all_floors = set(range(1, 101))
    # all chests collected?
    if state.chests != all_floors:
        missed_chests = all_floors - state.chests
        yield ValueError(f"Missing chests on: {missed_chests}")
    # all keys collected?
    if state.keys != all_floors:
        missed_keys = all_floors - state.keys
        yield ValueError(f"Missing keys on: {missed_keys}")
    # last floor is floor 100?
    if state.previous_room != 100:
        yield ValueError("Last floor is not 100F")


state = State()
for i, line in enumerate(open(path, 'r'), start=1):
    for problem in check_line(state, line):
        if isinstance(problem, ValueError):
            print(f'Line {i}: {problem}')

for problem in check_final_state(state):
    if isinstance(problem, ValueError):
        print(f'{problem}')
