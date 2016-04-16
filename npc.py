import copy
import random
import sys
import time
from multiprocessing import Process, Pipe

# Custom modules
import commands
import database

class NPC():
    def __init__(self):
        # Initialize NPC in commands
        self.cmd = commands.Commands()
        self.cmd.npc_table = 'stats_npc_creatures'
        self.cmd.mode = 'creatures'
        self.data = ''

    def setup(self):
        # Setup NPC in commands
        self.cmd.get_npc_info()
        NID = self.cmd.NID # Database ID for NPC hence NID

        # Setup timers & events
        self.reseed = time.time()
        self.get_events()
        self.room = False # Flag for timer resets
        self.elapsed = {}
        self.elapsed['time'] = time.time()
        self.elapsed['random'] = 0
        self.elapsed['choice'] = []
        self.elapsed['max'] = 15
        self.elapsed['min'] = 3
        # Not efficient below, done only for fun/learning
        for i in range(self.elapsed['min'], self.elapsed['max']+1):
            self.elapsed['choice'].append(i)
        random.shuffle(self.elapsed['choice'])
        self.cmd.debug("Choices: " + str(self.elapsed['choice']))

    def get_settings(self):
        self.sql = database.Database()
        self.sql.connect()
        self.sql.cursor.execute('SELECT * FROM game_settings')
        row = self.sql.cursor.fetchone()
        self.phor = dict(row)
        self.sql.close()

    def think(self, external, internal):
        # Thought looper
        self.setup()
        while True:
            # Only store self.data in variable if we can
            if external.poll():
                self.data = external.recv()

            # End pipe when necessary
            if len(self.data) > 0:
                if self.data == 'END':
                    self.cmd.debug("PIPE: Recieved End")
                    try: internal.send('END')
                    except BrokenPipeError: break
                    finally: break

            # Thought should happen every second but not faster
            if time.time() - self.reseed > 1:
                # Investigate: random.seed() gets stuck so reseed every second
                random.seed()
                self.reseed = time.time()
                # Investigate: STDOUT gets stuck end of pipe session so flush it
                sys.stdout.flush()

                # Start processing all NPCs
                self.get_settings()
                if self.phor['pause'] != 1:

                    # Update npc/player data
                    self.cmd.get_npc_info()

                    # If npc random events change, reset self.events
                    old_npcs = copy.deepcopy(self.cmd.npc)
                    change = False
                    for ID, npc_context in self.cmd.npc.items():
                        if ID not in old_npcs:
                            self.cmd.debug("ID not in old NPCs")
                            change = True
                            break
                        for EID, event_context in self.cmd.npc\
                            [ID]['events'].items():
                            if EID not in old_npcs[ID]['events']:
                                self.cmd.debug(
                                    "EID not in old NPCs")
                                change = True
                                break
                            for key, value in self.cmd.npc\
                                [ID]['events'][EID].items():
                                if (str(old_npcs[ID]['events'][EID][key]) !=
                                    str(self.cmd.npc\
                                    [ID]['events'][EID][key])):
                                    self.cmd.debug("NID not the same")
                                    change = True
                                    break
                            if change == True:
                                break
                        if change == True:
                            break
                    if change:
                        self.get_events()

                    # Break down processing each npc one at a time
                    # NOTE: Learn about other ways to thread this (pool?)
                    for ID, self.data in self.cmd.npc.items():

                        spawn = int(self.cmd.npc[ID]['spawn'])

                        # Process based on spawned, same room, zones
                        if (spawn and str(self.cmd.npc[ID]['ZID']) !=
                            str(self.cmd.player['ZID']) and
                            str(self.cmd.npc[ID]['zones'] != '-1')):

                            # Restart timers for moving
                            if self.room:
                                self.reset_timers(elapsed=True)
                                self.room = False

                            # Make a movement choice (always choose index 0)
                            if self.elapsed['choice']:
                                choice = self.elapsed['choice'][0]
                            else:
                                for i in range(
                                    self.elapsed['min'], self.elapsed['max']+1):
                                    self.elapsed['choice'].append(i)
                                random.shuffle(self.elapsed['choice'])
                                choice = self.elapsed['choice'][0]

                            # Is it movement time yet? is it is it is it is it?
                            if time.time() - self.elapsed['time'] > choice:
                                self.cmd.debug("Choice: " + str(choice))
                                self.elapsed['choice'].pop(
                                    self.elapsed['choice'].index(choice))
                                self.cmd.debug(
                                    "Choices: " + str(self.elapsed['choice']))
                                self.NID = ID
                                self.cmd.process('move any', mode='creatures')
                                try: internal.send(self.cmd.response)
                                except BrokenPipeError: break
                                self.reset_timers(elapsed=True)

                        elif (spawn and str(self.cmd.npc[ID]['ZID']) ==
                              str(self.cmd.player['ZID'])):

                            # In the same room
                            if self.room == False:
                                self.room = True

                            # Process dialog responses if any
                            if ID in self.cmd.dialog:
                                if len(self.cmd.dialog[ID]['response']) > 0:
                                    self.cmd.debug(
                                        "Response: " +
                                        str(self.cmd.dialog[ID]['response']))
                                    self.cmd.NID = ID
                                    self.cmd.process(
                                        'respond 1', mode='creatures')
                                    try: internal.send(self.cmd.response)
                                    except BrokenPipeError: break

                            # Process attacks
                            if self.cmd.mode == 'creatures':
                                pass

                        # Process random events
                        if self.process_events(str(ID)):
                            try: internal.send(self.cmd.response)
                            except BrokenPipeError: break

            # BUG: Always send something so game doesn't freak out
            try: internal.send('EMPTY')
            except BrokenPipeError: break

        self.cmd.debug("PIPE: Ending Simple")
        internal.close()
        external.close()

    def get_events(self):
        # Build self.events based on npc events but also add elements
        # TODO: Only reset ones that need changing
        self.events = {}
        for ID, npc_context in self.cmd.npc.items():
            for EID, event_context in self.cmd.npc[ID]['events'].items():
                self.events[EID] = event_context
                self.events[EID]['timer_flag'] = True
                self.events[EID]['timer_stamp'] = 0
                self.events[EID]['NID'] = ID
        self.cmd.debug("Events: " + str(self.events))

    def process_events(self, ID):
        # Processes events for one npc
        spawn = int(self.cmd.npc[ID]['spawn'])
        test = False # Return true if there is a message to send
        for EID, event_context in self.events.items():
            if str(event_context['NID']) == ID:

                # Start flag timer if it wasn't started
                if event_context['timer_flag'] == True:
                    event_context['timer_flag'] = False
                    event_context['timer_stamp'] = time.time()
                    self.events[EID]['timer_choice'] = random.randint(
                        int(self.events[EID]['min']),
                        int(self.events[EID]['max']))
                    self.cmd.debug("Event Data: " + str(event_context))

                elif self.cmd.npc[ID]['lock'] == 0:
                    if (time.time() - event_context['timer_choice'] >
                        event_context['timer_stamp']):

                        # Timer's end, process event actions
                        test = True
                        event_context['timer_flag'] = True
                        self.cmd.NID = ID
                        words = event_context['action'].split(' ')
                        if words[0].lower() == 'say' and spawn:
                            self.cmd.process(
                                event_context['action'], mode=self.cmd.mode)
                        elif words[0].lower() == 'talk' and spawn:
                            self.cmd.process(
                                event_context['action'], mode=self.cmd.mode)
                        elif words[0].lower() == 'spawn':
                            if spawn != 1:
                                self.cmd.process(
                                    'spawn ' + ID, mode=self.cmd.mode)
                            else:
                                test = False
                        elif spawn:
                            self.cmd.process(
                                event_context['action'], mode=self.cmd.mode)
                        else:
                            test = False

        return test


    def reset_timers(self, instant=False, elapsed=False):
        if instant:
            self.instant['time'] = time.time()
        elif elapsed:
            self.elapsed['time'] = time.time()

if __name__ == '__main__':
    pass