import sys
from warnings import Warning

from load import load_all

path = sys.argv[1]


MAPS = load_all()


class State:
    def __init__(self):
        self.keys = set()
        self.chests = set()
        self.previous_room = 1


def check_line(state, line):
    room, actions = line.split(' ')
    if room[-1] != 'F':
        yield ValueError('Invalid floor specifier')
    room = int(room[:-1])
    # floor transition
    if room not in MAPS[state.previous_room]['targets']:
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
            yield Warning(f'Key already collected on {room}F')
        state.keys.add(room)
    elif action == 'c':
        # chest already collected?
        if room in state.chests:
            yield ValueError(f'Chest already collected on {room}F')
        # enough keys available?
        if len(state.chests) >= len(state.keys):
            yield ValueError(f'Not enough keys to collect chest on {room}F')
        state.chests.add(room)


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
for i, line in enumerate(open(path, 'r')):
    if line:
        for problem in check_line(state, line):
            if isinstance(problem, ValueError):
                print(f'Line {i}: {problem}')

for problem in check_final_state(state):
    if isinstance(problem, ValueError):
        print(f'{problem}')
