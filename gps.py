import time
import inject

import psutil
import colorama
from colorama import Fore, Back, Style

colorama.init()


class Game(object):
    def __init__(self, process):
        self.process = process
        self.item_address = 0x5DA6AC

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
    
    def boss_explosions_playing(self):
        return self._read(0x5DAC30) > 0

    def _read(self, offset):
        return self.process.read_int32(offset)


class Entry(object):
    def __init__(self, section, floor, actions, comment):
        self.section = section
        self.floor = floor
        self.actions = actions
        self.comment = comment


class GPS(object):
    COLOURS = {
        'k': Fore.YELLOW,
        'c': Fore.CYAN,
        'b': Fore.GREEN,
        'r': Fore.RED,
        't': Fore.GREEN,
        'w': Fore.MAGENTA,
    }

    def __init__(self, game, route):
        self.game = game
        self.route = self._parse(route)
        self.current_line = 0
        self.current_floor = 0

    def _parse(self, route):
        floors = []
        section = ''
        for line in route:
            if not line:
                continue
            if line.startswith('# '):
                section = line
            elif line.startswith('status'):
                pass
            else:
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
        done = False
        prev_items = (None, None, None)
        for entry in self.route:
            # TODO support not advancing when going into the wrong door
            action_index = 0
            while entry.floor == self.game.floor():
                b = self.game.has_bubble_key(entry.floor) or (self.game.boss_explosions_playing() and entry.floor in {10, 25, 40, 55, 70, 85, 100})
                k = self.game.has_key(entry.floor)
                c = self.game.has_chest(entry.floor)
                r = self.game.is_dead()
                
                floor_complete = action_index >= len(entry.actions)
                if not floor_complete:
                    next_action = entry.actions[action_index]
                    conditions = [
                        next_action == 'b' and b,
                        next_action == 'c' and c,
                        next_action == 'k' and k,
                        next_action == 'r' and r,
                    ]
                    if any(conditions):
                        action_index += 1
                        floor_complete = action_index >= len(entry.actions)
                
                floor_output = f'{Fore.GREEN if floor_complete else Fore.RED}{entry.floor}{Fore.WHITE}F'
                action_output = self.format_actions(entry.actions, action_index)
                output = f'{Style.BRIGHT}{floor_output} {action_output}{Style.RESET_ALL}'
                print(output)

                time.sleep(0.1)
        
    def format_actions(self, actions, num_complete):
        action_strings = []
        for i, action in enumerate(actions):
            complete = i < num_complete
            if not complete:
                style = f'{GPS.COLOURS[action]}{Style.BRIGHT}{Back.BLACK}'
            else:
                style = f'{GPS.COLOURS[action]}{Style.DIM}{Back.GREEN}'
            action_strings.append(f'{style}{action}')
        return ''.join(action_strings)




with open('100.md') as fd:
    s = fd.read().splitlines()
    

with inject.Process(name='AssaCrip_en.exe') as process:
    game = Game(process)
    gps = GPS(game, route=s)
    gps.run()