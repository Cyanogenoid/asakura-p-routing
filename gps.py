import argparse
import time

import psutil
import colorama
from colorama import Fore, Back, Style

import inject

colorama.init()


class Game(object):
    def __init__(self, process):
        self.process = process
        self.item_address = 0x5DA6AC
        self.boss_floors = [10, 25, 40, 55, 70, 85, 100]
        self.boss_address = 0x5DABDC

    def floor(self):
        return self._read(0x5D9AFC) + 1

    def door(self):
        return self._read(0x5D21F8)
    
    def is_dead(self):
        return self._read(0x5B3FF4) == 1
    
    def x(self):
        return self.process.read_double(0x5B3FA0)

    def y(self):
        return self.process.read_double(0x5B3FA0)

    def coins(self):
        return self._read(0x5B40B8)

    def keys(self):
        return self._read(0x5B40BC)

    def has_bubble_key(self, floor):
        offset = 4 * ((floor - 1) * 3 + 0)
        return self._read(self.item_address + offset) == 1

    def has_key(self, floor):
        offset = 4 * ((floor - 1) * 3 + 1)
        return self._read(self.item_address + offset) == 1

    def has_chest(self, floor):
        offset = 4 * ((floor - 1) * 3 + 2)
        return self._read(self.item_address + offset) == 1
    
    def boss_beaten(self, floor):
        if floor not in self.boss_floors:
            return False
        offset = self.boss_address + 4 * self.boss_floors.index(floor)
        return self._read(offset) == 1
    
    def menu_open(self):
        return self._read(0x5DAC48) == 1

    def menu_selection(self):
        return self._read(0x5B4150) + 1

    def shop_open(self):
        return self._read(0x5DAC48) == 1

    def _read(self, offset):
        return self.process.read_int32(offset)


class Entry(object):
    def __init__(self, section, floor, actions, comment):
        self.section = section
        self.floor = floor
        self.actions = actions
        self.comment = comment

        self.action_index = 0
        self.menu_success = False
        self.shop_success = False


class GPS(object):
    COLOURS = {
        'k': Fore.YELLOW,
        'c': Fore.CYAN,
        'b': Fore.GREEN,
        'r': Fore.RED,
        't': Fore.GREEN,
        'w': Fore.MAGENTA,
    }

    def __init__(self, game, route, start_from_line=1, context_future=10, context_past=5):
        self.start_from_line = start_from_line
        self.context_past = context_past
        self.context_future = context_future

        self.game = game
        self.route = self._parse(route)

    def _parse(self, route):
        floors = []
        section = ''
        for i, line in enumerate(route):
            if not line:
                continue
            if line.startswith('# '):
                section = line
            elif line.startswith('status'):
                pass
            elif i + 1 >= self.start_from_line:
                parts = line.split('#')
                if len(parts) >= 2:
                    comment = ' '.join(x.strip() for x in parts[1:])
                else:
                    comment = ''
                floor_parts = parts[0].split(' ')
                if len(floor_parts) == 1:
                    actions = ''
                else:
                    actions = floor_parts[1]
                floor = int(floor_parts[0][:-1])
                floors.append(Entry(section, floor, actions, comment))
        return floors
                    
    def run(self):
        entry_index = 0
        last_output = None
        print(f'Waiting for {self.route[0].floor}F')
        while self.game.floor() != self.route[entry_index].floor:
            time.sleep(0.1)
        while True:
            game_floor = self.game.floor()
            if entry_index + 1 < len(self.route) and game_floor == self.route[entry_index + 1].floor:
                entry_index += 1
            entry = self.route[entry_index]
            if game_floor == entry.floor:
                output_lines = []

                output_lines.append(entry.section)
                output_lines.append('')

                entries_before = self.route[max(entry_index - self.context_past, 0):entry_index]
                output_lines += (self.context_past - len(entries_before)) * ['']
                for e in entries_before:
                    output_lines.append(self.format_entry(e))

                next_entry = self.route[entry_index + 1] if entry_index + 1 < len(self.route) else ''
                output_lines.append('')
                output_lines.append(self.format_entry(entry, next_entry=next_entry, style=Style.BRIGHT))
                output_lines.append('')

                current_section = entry.section
                entries_after = self.route[entry_index + 1:entry_index + 1 + self.context_future]
                new_lines = []
                for e in entries_after:
                    if e.section != current_section:
                        current_section = e.section
                        new_lines.append(e.section)
                    new_lines.append(self.format_entry(e, coloured_floor=False))
                output_lines += new_lines[:self.context_future]

                output = '\n'.join(output_lines)
                if output != last_output:
                    last_output = output
                    print(output)

            time.sleep(0.1)

    def format_entry(self, entry, next_entry=None, style=Style.NORMAL, coloured_floor=True):
        b = self.game.has_bubble_key(entry.floor) or self.game.boss_beaten(entry.floor)
        k = self.game.has_key(entry.floor)
        c = self.game.has_chest(entry.floor)
        r = self.game.is_dead()
        entry.menu_success = entry.menu_success or (self.game.menu_open() and next_entry and self.game.menu_selection() == next_entry.floor)
        entry.shop_success = entry.shop_success or self.game.shop_open()
        
        # any actions left?
        if entry.action_index < len(entry.actions):
            next_action = entry.actions[entry.action_index]
            condition = {
                'b': b,
                'c': c,
                'k': k,
                'r': r,
                't': entry.menu_success,
                'w': entry.menu_success,
                's': entry.shop_success,
                '?': True,
            }
            if condition[next_action]:
                entry.action_index += 1
        # floor_complete = (not 'b' in entry.actions or b) and (not 'k' in entry.actions or k) and (not 'c' in entry.actions or c)
        floor_complete = entry.action_index == len(entry.actions)

        floor_colour = Fore.RED if not coloured_floor else Fore.GREEN if floor_complete else Fore.RED
        floor_output = f'{Style.BRIGHT}{floor_colour}{entry.floor}{Fore.WHITE}{style}F'
        action_output = self.format_actions(entry.actions, entry.action_index, b=b, k=k, c=c, force_dim=style != Style.BRIGHT)
        next_floor = f'{Style.BRIGHT} -> {next_entry.floor}F' if next_entry else ''
        comment = f'  # {entry.comment}' if entry.comment else ''
        current_floor_string = f'{Style.BRIGHT}{floor_output}{action_output}{Fore.WHITE}{Back.RESET}{next_floor}{Style.RESET_ALL}{comment}'
        return current_floor_string

    def format_actions(self, actions, num_complete, b, k, c, force_dim=False):
        action_strings = []
        if not actions:
            return ''
        for i, action in enumerate(actions):
            complete = i < num_complete or (action == 'b' and b) or (action == 'k' and k) or (action == 'c' and c)
            if not complete:
                style = f'{GPS.COLOURS.get(action, Fore.WHITE)}{Style.BRIGHT if not force_dim else Style.DIM}{Back.BLACK}'
            else:
                style = f'{GPS.COLOURS.get(action, Fore.WHITE)}{Style.DIM}{Back.GREEN}'
            action_strings.append(f'{style}{action}')
        return ' ' + ''.join(action_strings)


parser = argparse.ArgumentParser()
parser.add_argument('path', help='Path to route')
parser.add_argument('--process', '-p', default='AssaCrip_en.exe', help='Name of process to read from')
parser.add_argument('--context-future', '-cf', type=int, default=10, help='Number of upcoming lines to show')
parser.add_argument('--context-past', '-cp', type=int, default=5, help='Number of past lines to show')
parser.add_argument('--start-from', '-s', type=int, default=1, help='Start the route <n> lines in (1-indexed)')
args = parser.parse_args()


with open(args.path) as fd:
    lines = fd.read().splitlines()
    

with inject.Process(name=args.process) as process:
    game = Game(process)
    gps = GPS(
        game,
        route=lines,
        start_from_line=args.start_from,
        context_future=args.context_future,
        context_past=args.context_past,
    )
    gps.run()
