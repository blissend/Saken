import random
import sys
import time
from multiprocessing import Process, Pipe

# Custom modules
import commands
import database

# First form, eliminate and use npc.py instead
class Nemesis:
    def __init__(self):
        pass

    def get_settings(self):
        self.sql = database.Database()
        self.sql.connect()
        self.sql.cursor.execute('SELECT * FROM game_settings')
        row = self.sql.cursor.fetchone()
        self.phor = dict(row)

    def think(self, external, internal):
        # Setup/Get npc/player in commands
        self.cmd = commands.Commands()
        self.table = 'stats_npc_nemesis'
        self.cmd.npc_table = self.table
        self.cmd.mode = 'nemesis'
        self.cmd.get_npc_info()

        # Setup random choices for random module and timers
        room = False # Flag to signal timer starts when in or not in same room
        self.elapsed = {}
        self.elapsed['time'] = time.time()
        self.elapsed['random'] = 0
        self.elapsed['choice'] = []
        self.elapsed['max'] = 15
        self.elapsed['min'] = 3
        for i in range(self.elapsed['min'], self.elapsed['max']+1):
            self.elapsed['choice'].append(i)
        random.shuffle(self.elapsed['choice'])
        self.instant = {}
        self.instant['time'] = time.time()
        self.instant['random'] = 0
        self.instant['choice'] = []
        self.instant['max'] = 4
        self.instant['min'] = 2
        for i in range(self.instant['min'], self.instant['max']+1):
            self.instant['choice'].append(i)
        random.shuffle(self.instant['choice'])
        reseed = time.time()
        self.cmd.debug("Choices: " + str(self.elapsed['choice']))

        # Loop thought
        data = ''
        while True:
            # Only store data in variable if we can
            if external.poll():
                data = external.recv()

            # End pipe when necessary
            if len(data) > 0:
                if data == 'END':
                    self.cmd.debug("Nemesis: Recieved End")
                    try: internal.send('END')
                    except BrokenPipeError: break
                    finally: break

            # Thought should happen every second but not faster
            if time.time() - reseed > 1:
                # random.seed() gets stuck so shuffle every second
                random.seed()
                reseed = time.time()
                # STDOUT gets stuck until end
                sys.stdout.flush()

                self.get_settings()
                if self.phor['pause'] != 1:
                    # Start processing based on whether in room or not and time
                    self.cmd.get_npc_info()
                    if (int(self.cmd.player['ZID']) ==
                        int(self.cmd.npc[self.cmd.NID]['ZID'])):
                        # Gut reactions, process instantly when in same room
                        if room == False:
                            # We're in same room, start timers
                            room = True
                            self.reset_timers(instant=True)
                        if (self.cmd.player['health'] != 0 and
                            self.cmd.player['lock'] != True):
                            try:
                                choice = self.instant['choice'][0]
                            except IndexError:
                                for i in range(
                                    self.instant['min'], self.instant['max']+1):
                                    self.instant['choice'].append(i)
                                random.shuffle(self.instant['choice'])
                                choice = self.instant['choice'][0]
                            if time.time() - self.instant['time'] > choice:
                                self.instant['choice'].pop(
                                    self.instant['choice'].index(choice))
                                self.cmd.process(
                                    'attack player', mode='nemesis')
                                if self.cmd.player['update']:
                                    try: internal.send("update_progress_bars")
                                    except BrokenPipeError: break
                                    self.cmd.player['update'] = False
                                try: internal.send(self.cmd.response)
                                except BrokenPipeError: break
                                self.reset_timers(instant=True)
                    else:
                        # Delayed reactions, process later when not in same room
                        if room == True:
                            # We're NOT in same room, start timers
                            room = False
                            self.reset_timers(elapsed=True)
                        try:
                            choice = self.elapsed['choice'][0]
                        except IndexError:
                            for i in range(
                                self.elapsed['min'], self.elapsed['max']+1):
                                self.elapsed['choice'].append(i)
                            random.shuffle(self.elapsed['choice'])
                            choice = self.elapsed['choice'][0]
                        if time.time() - self.elapsed['time'] > choice:
                            self.cmd.debug("Choice: " + str(choice))
                            self.elapsed['choice'].pop(
                                self.elapsed['choice'].index(choice))
                            self.cmd.debug(
                                "Choices: " + str(self.elapsed['choice']))
                            self.cmd.process('move any', mode='nemesis')
                            try: internal.send(self.cmd.response)
                            except BrokenPipeError: break
                            self.reset_timers(elapsed=True)

            # Always send something so game doesn't freak out
            try: internal.send('EMPTY')
            except BrokenPipeError: break

        self.cmd.debug("Ending Nemesis")
        internal.close()
        external.close()

    def reset_timers(self, instant=False, elapsed=False):
        if instant:
            self.instant['time'] = time.time()
        elif elapsed:
            self.elapsed['time'] = time.time()

if __name__ == '__main__':
    # ERASE! Only kept to show how I learned about pipes
    print("START")
    n = Nemesis()
    pinternal, cinternal = Pipe()
    pexternal, cexternal = Pipe()
    p = Process(target=n.think, args=(cexternal, cinternal))
    p.daemon = True
    p.start()
    data = ''
    count = 0
    while True:
        if pinternal.poll():
            data = pinternal.recv()
        if len(data) > 0:
            print("Parent: " + data)
            time.sleep(2)
            if data == 'END':
                print("Parent: Recieved END")
                break
            else:
                print("Parent: Sending END")
                pexternal.send("END")
            data = '' # wipe as it's already processed
        count += 1
        if count == 1:
            print("Parent: First Loop ")
    print("Officially Ended")