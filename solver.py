import re

from z3 import *

from load import load_all


MAPS = load_all()
COIN_FLOORS = {x for x in range(1, 101) if MAPS[x]['chest'][-1] == MAPS[1]['chest'][-1]}
SHOP_COSTS = {
    '15-8': 8,
    8: 8,

    '41-42': 15,
    43: 15,

    '64-63': 13,
    63: 13,

    97: 15,
}

class Section:
    def __init__(self, start_floor, end_floor, start_id, end_id, required_keys, end_keys, required_coins, added_coins):
        self.start_floor = int(start_floor)
        if end_floor[-1] == 'b':
            self.end_postfix = 'b'
            end_floor = end_floor[:-1]
        else:
            self.end_postfix = ''
        self.end_floor = int(end_floor)
        self.start_id = int(start_id)
        self.end_id = int(end_id)
        self.required_keys = int(required_keys)
        self.end_keys = int(end_keys)
        self.required_coins = int(required_coins)
        self.added_coins = int(added_coins)

    def __str__(self):
        return f'{self.start_floor}-{self.end_floor}{self.end_postfix}'

    def __repr__(self):
        return f'{self.start_floor}-{self.end_floor}{self.end_postfix} {self.required_keys}k{self.end_keys} {self.added_coins}c {self.required_coins}s [{self.start_id}-{self.end_id}]'


def parse(s):
    floor_regex = re.compile(r'(\d+)-(\d+\w?)')
    door_id_regex = re.compile(r'\[(\d)-(\d)\]$')

    # split into sections
    sections = []
    current_section = None
    for line in s.splitlines():
        if line.startswith('#'):
            sections.append(current_section)
            current_section = [line]
        else:
            current_section.append(line)
    sections.append(current_section)
    sections = sections[1:]  # remove None element


    objects = []
    for section in sections:
        floors = floor_regex.search(section[0])
        doors = door_id_regex.search(section[0])

        start_floor, end_floor = floors.groups()
        start_id, end_id = doors.groups()

        current_key_delta = 0
        min_delta = 0
        added_coins = 0
        required_coins = 0
        for line in section[1:]:
            main = line.split('#')[0]
            if not main:
                continue
            parts = main.split(' ')
            if len(parts) == 1:
                floor = parts[0]
                actions = ''
            else:
                floor, actions, *_ = parts
            assert floor[-1] == 'F'
            floor = int(floor[:-1])

            for action in actions:
                if action == 'k':
                    current_key_delta += 1
                elif action == 'c':
                    current_key_delta -= 1
                    if floor in COIN_FLOORS:
                        added_coins += 1
                elif action == 's':
                    required_coins = SHOP_COSTS[floor] - added_coins

                min_delta = min(current_key_delta, min_delta)
        required_keys = -min_delta
        end_keys = required_keys + current_key_delta

        objects.append(Section(
            start_floor=start_floor,
            end_floor=end_floor,
            start_id=start_id,
            end_id=end_id,
            required_keys=required_keys,
            end_keys=end_keys,
            required_coins=required_coins,
            added_coins=added_coins,
        ))
    return objects


with open('R2.md', 'r') as fd:
    s = fd.read()
sections = parse(s)
sections.append(Section(
    '98', '96',
    0, 0,
    0, 3,
    0, 2,
))
# sections = sections[-10:]
for section in sections:
    print(section)
print()
sections = {str(section): section for section in sections}


vars = {}
for section_name in sections:
    vars[section_name] = Int(section_name)


opt = Optimize()

# enforce permutation
opt.add(Distinct(*vars.values()))
opt.add([0 <= x for x in vars.values()])
opt.add([x < len(vars) for x in vars.values()])

# start with 98-96, end with 98-100
opt.add(vars['98-96'] == 0)
opt.add(vars['98-100'] == len(vars) - 1)

# key count constraints
for i in range(1, len(vars)):
    # key deltas of all entries assigned to before index i
    before = [If(x < i, sections[s].end_keys - sections[s].required_keys, 0) for s, x in vars.items()]
    # how many keys are required for this floor?
    current = Sum(*[If(x == i, sections[s].required_keys, 0) for s, x in vars.items()])
    opt.add(Sum(*before) >= current)

# shop coin constraints
shop_sections = ['15-8', '41-42', '64-63']
for section in shop_sections:
    var = vars[section]
    coins_already_spent = [If(vars[s] < var, SHOP_COSTS[s], 0) for s in shop_sections if s != section]
    coins_collected = [If(x < var, sections[s].added_coins, 0) for s, x in vars.items()]
    opt.add(Sum(*coins_collected) - sum(coins_already_spent) >= sections[section].required_coins)

# hard constraints
## 34 check flag has to be before starting at 34
opt.add(vars['41-34'] < vars['34-38'])
opt.add(vars['41-34'] < vars['34-33'])
opt.add(vars['34-38'] < vars['34-33'])
# bubble key on 30F comes before key and chest
opt.add(vars['28-30b'] < vars['28-30'])
opt.add(vars['28-30b'] < vars['28-26'])

# wrong warp chaining
for from_section, from_var in vars.items():
    for to_section, to_var in vars.items():
        if sections[to_section].start_id == 0:
            continue
        term = If(
            from_var + 1 == to_var,
            sections[from_section].end_id == sections[to_section].start_id,
            True,
        )
        opt.add(term)

# soft constraints
## stability pendant before sections with inertia
opt.add_soft(vars['64-63'] < vars['56-58'])
opt.add_soft(vars['64-63'] < vars['64-68'])
opt.add_soft(vars['64-63'] < vars['98-94'])
## guard shield before sections with lots of shooting (i.e. mini bosses)
opt.add_soft(vars['76-79'] < vars['98-94'])
opt.add_soft(vars['76-79'] < vars['98-91'])

# cursor distance to minimise
def distance(x, y):
    x2 = x - 1
    y2 = y - 1
    dist_horizontal = abs(x2 % 10 - y2 % 10)
    dist_vertical = abs(x2 // 10 - y2 // 10)
    return dist_horizontal + dist_horizontal

terms = []
for from_section, from_var in vars.items():
    for to_section, to_var in vars.items():
        if from_section == to_section:
            continue
        from_floor = sections[from_section].end_floor
        to_floor = sections[to_section].start_floor
        term = If(from_var + 1 == to_var, distance(from_floor, to_floor), 0)
        terms.append(term)

opt.minimize(Sum(*terms))
print(opt.check())
model = opt.model()
print(model)
print()

best_sequence = sorted(vars.keys(), key=lambda x: model[vars[x]].as_long())
print(best_sequence)