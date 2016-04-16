import copy
import random
import time
import re
import sqlite3

# Custom modules
import database

# TODO: Break this up into classes, rethink OOP here
class Commands:
    def __init__(self):
        # Unique ID
        self.time = time.time()

        # Get settings & SQL connection
        self.sql = database.Database()
        self.sql.connect()
        self.get_settings()

        # Setup basics
        self.prompt = '&gt; '
        self.response = []
        self.command = ''
        self.mode = 'player' # player otherwise based on npc type
        self.levelup = False

        # Get & setup NPC/player's information
        self.dialog = {}
        self.npc = {}
        self.npc_table = '' # NPC database table name
        self.NID = 0 # NPC ID of the NPC we're working with
        self.player = {}
        self.get_player_info()

        # Get available commands
        self.all_commands = []
        self.sql.cursor.execute('SELECT * FROM game_commands')
        rows = self.sql.cursor.fetchall()
        for row in rows:
            self.all_commands.append(row['name'])

        # Get available directions
        self.directions = {}
        self.dir_shorthand = {}
        self.sql.cursor.execute('SELECT * FROM world_directions')
        rows = self.sql.cursor.fetchall()
        for row in rows:
            self.directions[str(row['ID'])] = row['name'].lower()
            self.dir_shorthand[str(row['ID'])] = row['shorthand']

    def get_settings(self):
        self.sql.cursor.execute('SELECT * FROM game_settings')
        row = self.sql.cursor.fetchone()
        self.phor = dict(row)

    def debug(self, message):
        if self.phor['debug']:
            print("[" + self.mode + "] - " + str(message))

    def process(self, commands, mode='player'):
        self.response = []
        self.mode = mode

        self.get_settings()
        if self.phor['pause'] == 1:
            self.response.append("<br />Game is paused!")
            self.response.append("<br />")
            return

        # Sanitize command of html tags
        commands = re.sub('<.*?>', '', commands)

        # Process each command
        self.debug("Commander: " + commands)
        split_commands = commands.split(';')
        for cmd in split_commands:
            self.command = str(cmd)

            # Check if an actual command
            filtered = cmd.strip()
            words = filtered.split(' ')
            if words[0].lower() in self.all_commands:
                if self.mode == 'player':
                    self.response.append(self.prompt + self.command)

                # Concatenate arguments for command and filter command
                args = ''
                if len(words) > 1:
                    for w in words[1:]:
                        if len(args) < 1:
                            args = w
                        else:
                            args = args + ' ' + w
                filtered = words[0].lower()

                # Finally, do the dirty work for the command
                if filtered == 'look':
                    if not args:
                        self.look()
                    else:
                        self.look_at(args)
                elif filtered == 'move' or filtered == 'mv':
                    self.move(args)
                elif filtered == 'attack' or filtered == 'at':
                    self.combat(args)
                elif filtered == 'talk':
                    self.dialog_talk(targets=args)
                elif filtered == 'resp' or filtered == 'respond':
                    self.dialog_response(args)
                elif filtered == 'say':
                    self.say(args)
                elif filtered == 'emote':
                    self.say(args, emote=True)
                elif filtered == 'spawn':
                    if self.mode == 'creatures':
                        self.spawn(args)
            else:
                # Not a command, let player know
                if self.mode == 'player':
                    self.response.append(self.prompt + self.command)
                    self.response.append("Unknown: " + self.command)
                    break

        # Check response formatting
        if self.response:
            max_length = len(self.response) - 1
            for i, row in enumerate(self.response):
                if ("<tr" not in row and
                    "<td" not in row and
                    "<table" not in row and
                    "<br" not in row):
                    # Add line break
                    self.response[i] = "<br />" + row + "\n"
                else:
                    self.response[i] += "\n"
            self.response.append("<br />")
            self.debug("Response: " + str(self.response))

    def say(self, messages, target=False, emote=False):
        # Add messages into says list
        says = []
        if type(messages) == list:
            for message in messages:
                says.append(str(message))
        else:
            says.append(str(messages))

        # Get the full_name
        full_name = ''
        if self.mode == 'player' and target == False:
            full_name = self.player['full_name']
        elif target == False:
            full_name = self.npc[self.NID]['full_name']
        else:
            full_name = self.target['full_name']

        # Finally, spit it all out
        for say in says:
            if emote:
                self.response.append(full_name + " " + say)
            else:
                self.response.append(full_name + " says, \"" + say + "\"")

    def also_here(self):
        # Get names for those also here
        self.names = []

        # Player
        self.get_player_info()
        name = (
            "<span style='color:#FFFFFF;font-weight:bold;'>" +
            self.player['name'])
        surname = self.player['surname'] + "</span>"
        self.names.append(
            {'table': self.player['table'],
             'ID': self.player['ID'],
             'name': name,
             'surname': surname,
             'full_name': name + ' ' + surname})

        # Nemesis
        self.sql.cursor.execute(
            "SELECT * FROM stats_npc_nemesis WHERE ZID = " +
            str(self.player['ZID']))
        row = self.sql.cursor.fetchone()
        if row:
            name = "<span style='color:#FFF3AA'>" + row['name']
            surname = row['surname'] + "</span>"
            self.names.append(
                {'table': 'stats_npc_nemesis',
                 'ID': row['ID'],
                 'name': name,
                 'surname': surname,
                 'full_name': name + ' ' + surname})

        # Simple
        self.sql.cursor.execute(
            "SELECT * FROM stats_npc_simple WHERE ZID = " +
            str(self.player['ZID']) + " AND spawn = 1")
        rows = self.sql.cursor.fetchall()
        if rows:
            for row in rows:
                name = "<span style='color:#8E7F26'>" + row['name']
                surname = row['surname'] + "</span>"
                self.names.append(
                    {'table': 'stats_npc_simple',
                     'ID': row['ID'],
                     'name': name,
                     'surname': surname,
                     'full_name': name + ' ' + surname})

        # Creatures
        self.sql.cursor.execute(
            "SELECT * FROM stats_npc_creatures WHERE ZID = " +
            str(self.player['ZID']) + " AND spawn = 1")
        rows = self.sql.cursor.fetchall()
        if rows:
            for row in rows:
                name = "<span style='color:#C6B54F'>" + row['name']
                surname = row['surname'] + "</span>"
                self.names.append(
                    {'table': 'stats_npc_creatures',
                     'ID': row['ID'],
                     'name': name,
                     'surname': surname,
                     'full_name': name + ' ' + surname})

    def look(self, silent=False):
        # Temporary variable to fill up response only if silent = False
        say = []

        # Get location information
        self.sql.cursor.execute(
            "SELECT * FROM world_zones WHERE ID = " + str(self.player['ZID']))
        row = self.sql.cursor.fetchone()
        say.append( # Location Name
            "<table><tr><td style='background-color:#1C2E40;" +
            "padding:2px 3px 2px 3px' width='100%' colspan='2'><h3><p>" +
            str(row['name']) + "</p></h3></td></tr></table>")
        say.append( # Location Description
            "<tr><td colspan='2'>" + str(row['description']) + "</td></tr>")

        # Get names for those also here
        self.also_here()

        # Display names if any
        if len(self.names) > 0:
            names_formatted = ''
            for data in self.names:
                if len(names_formatted) < 1:
                    names_formatted = data['full_name']
                else:
                    names_formatted += ", " + data['full_name']
            say.append(
                "<tr><td style='background-color:#1C2E40;" +
                "padding:2px 3px 2px 3px;color:yellow'>Also here:</td>"
                "<td style='padding:2px 3px 2px 3px;'>&nbsp;" +
                names_formatted + "</td></tr>")

        # Get location exits
        exits = ''
        self.sql.cursor.execute(
            "SELECT * FROM world_map WHERE CZID = " + str(self.player['ZID']))
        rows = self.sql.cursor.fetchall()
        for row in rows:
            if len(exits) > 1:
                exits = exits + ', ' + self.directions[str(row['DID'])].title()
            else:
                exits = self.directions[str(row['DID'])].title()
        say.append(
            "<tr><td style='background-color:#1C2E40;padding:2px 3px 2px 3px;" +
            "color:#3C9A0A'>Exits:</td><td style='padding:2px 3px 2px 3px;" +
            "color:#2B7C00'>" + exits + "</td></tr></table>")

        if silent == False:
            for s in say:
                self.response.append(s)

    def look_at(self, args):
        # Get the names of those also here
        self.also_here()

        # Find the target name
        find = False
        for data in self.names:
            if data['name'].find(args.lower()):
                find = True
                appearance_numbers = [
                    'age',
                    'height',
                    'nippy_diam',
                    'nippy_len',
                    'anay_diam',
                    'anay_len',
                    'phally_diam',
                    'phally_len',
                    'testy_diam',
                    'vagy_diam',
                    'vagy_len']
                appearance_text = [
                    'hair',
                    'eyes',
                    'nose',
                    'mouth',
                    'ears',
                    'face',
                    'chest',
                    'nippy',
                    'stomach',
                    'waist',
                    'behind',
                    'anay',
                    'phally',
                    'testy',
                    'vagy',
                    'tone',
                    'special']
                self.response.append("<table width='100%'>")
                prefix = (
                    "<tr><td style='padding:0px 3px 0px 3px;" +
                    "text-align:right' width='20%'>")

                # Format for text
                for option in appearance_text:
                    if int(self.player[option]) != 0:
                        self.sql.cursor.execute(
                            "SELECT * FROM appearance_options WHERE ID = '" +
                            str(self.player[option]) + "'")
                        row = self.sql.cursor.fetchone()
                        description = row['description']
                        self.response.append(
                                prefix + option.capitalize() +
                                ": </td><td width='80%'>" +
                                description + "</td></tr>")

                # Format for numbers
                self.sql.cursor.execute(
                    "SELECT * FROM appearance_players WHERE CID = '" +
                    str(self.player['ID']) + "'")
                row = self.sql.cursor.fetchone()
                for option in appearance_numbers:
                    description = str(row[option])
                    if option.find('_') < 0:
                        suffix = ''
                        if option == 'age':
                            suffix = ' cycles'
                        elif option == 'height':
                            suffix = ' inches'
                        self.response.append(
                            prefix + option.capitalize() +
                            ": </td><td width='80%'>" + description +
                            suffix + "</td></tr>")
                    else:
                        suffix = ' inches'
                        opt = option.split('_')
                        middle = opt[0].capitalize()
                        print(opt)
                        if opt[1] == 'diam':
                            middle += " Diameter"
                        else:
                            middle += " Length"
                        self.response.append(
                            prefix + middle + ": </td><td width='80%'>" +
                            description + suffix + "</td></tr>")
                self.response.append("</table>")
                break

        if not find:
            self.response.append("Could not find what you were looking for!")

    def move(self, direction):
        # Update NPC/Player's information
        if self.mode == 'player':
            self.get_player_info()
        else:
            self.get_npc_info()

        # Make sure NPC is allowed to move
        if self.mode != 'player':
            if str(self.npc[self.NID]['zones']) == '-1':
                self.debug(
                    self.npc[self.NID]['full_name'] + " isn't allowed to move!")
                return

        # Make sure it's a direction we can go
        movement = direction.lower()
        if (movement in self.directions.values() or
            movement in self.dir_shorthand.values()):
            # Get direction ID
            move_ID = ''
            if len(movement) < 3:
                for data in self.dir_shorthand.items():
                    if data[1] == movement:
                        move_ID = data[0]
                        break
            if len(move_ID) == 0:
                for data in self.directions.items():
                    if data[1] == movement:
                        move_ID = data[0]
                        break

            # Get directions we are allowed to go
            exits = []
            exits_move_ID = []
            if self.mode == 'player':
                new_xy = str(self.player['ZID'])
            else:
                new_xy = str(self.npc[self.NID]['ZID'])
            self.sql.cursor.execute(
                "SELECT * FROM world_map WHERE CZID = '" + new_xy + "'")
            rows = self.sql.cursor.fetchall()
            for row in rows:
                if movement == 'any' or movement == 'a':
                    exits.append(row['DZID'])
                    exits_move_ID.append(row['DID'])
                else:
                    if str(row['DID']) == str(move_ID):
                        new_xy = str(row['DZID'])
                        break


            # For random movements, get new move_ID and new_xy
            if len(exits) > 0:

                if self.mode == 'creatures':
                    check = False
                    zones = self.npc[self.NID]['zones'].split(' ')
                    for exit in exits:
                        for zone in zones:
                            if int(exit) == int(zone):
                                check = True
                    if check == False:
                        self.debug(
                            self.npc[self.NID]['full_name'] +
                            " is trapped and can't move!")
                        return

                # Finally choose a random direction based on NPC zones
                check = False
                while check == False:
                    index = random.randint(0, len(exits) - 1)
                    new_xy = str(exits[index])
                    move_ID = str(exits_move_ID[index])
                    if self.mode == 'creatures':
                        zones = self.npc[self.NID]['zones'].split(' ')
                        for ZID in zones:
                            if int(ZID) == 0:
                                # Means NPC can go any direction it wants
                                check = True
                                break
                            elif int(ZID) == int(new_xy):
                                # Yay we found a way we can go
                                check = True
                                break
                    else:
                        break

            # And awaaaaaaaaaaaay we go!
            if self.mode == 'player':
                # Have we moved?
                if new_xy != self.player['ZID']:
                    #self.player['ZID'] = str(new_xy)
                    self.sql.cursor.execute(
                        "UPDATE " + self.player['table'] + " SET ZID = " +
                        new_xy + " WHERE ID = '" + str(self.player['ID']) + "'")
                    self.sql.save()
                    self.get_player_info()
                    self.look()
                else:
                    self.response.append("You can not go that way!")
            else:
                # Have we moved?
                if new_xy != str(self.npc[self.NID]['ZID']):
                    if (str(self.npc[self.NID]['ZID']) ==
                        str(self.player['ZID'])):
                        # Are we leaving players room?
                        self.response.append(
                            self.npc[self.NID]['full_name'] +
                            " moves " + self.directions[move_ID].lower())
                    elif new_xy == str(self.player['ZID']):
                        # Are we arriving? Ohhh myy!
                        self.response.append(
                            self.npc[self.NID]['full_name'] +
                            " arrives!")
                    self.npc[self.NID]['ZID'] = new_xy
                    self.set_target_info(self.npc[self.NID])
        else:
            if self.mode == 'player':
                self.response.append("Unknown direction")

    def spawn(self, ID):
        # Setup/Update variables
        self.npc[ID]['spawn'] = 1
        zones = self.npc[ID]['zones'].split(' ')
        self.npc[ID]['ZID'] = zones[random.randint(0, len(zones))]
        self.set_target_info(self.npc[ID])

        # Are we arriving in players room?
        self.get_player_info()
        if str(self.player['ZID']) == str(self.npc[ID]['ZID']):
            self.say("has arrived!", emote=True)

    def dialog_talk(
        self, targets=None, target_table=None, target_ID=None, TID=None):

        # Get ID and init variables
        if self.mode == 'player':
            ID = str(self.player['ID'])
        else:
            ID = str(self.NID)
        message = ''
        emote = False

        # Are we being stupid?
        if targets != None:
            if (targets.lower() == self.player['name'].lower() and
                self.mode == 'player'):
                self.response.append(
                    "You end up looking strange talking to yourself.")
                return

        # Search for talk target by name
        if targets != None:
            words = targets.split(' ')
            if len(words) > 1:
                targets = words[0]

                # If number provided, initiate TID dialog instead of default
                if words[1].isdigit():
                    TID = words[1] # Replace with TID we want
                    words.pop(1) # pop TID
                    words.pop(0) # pop name
                else:
                    words.pop(0) # pop name

                # Are we emoting?
                if words[0] == 'emote':
                    # We are! DRAAAMA! Flag emote variable
                    words.pop(0) # pop emote command
                    emote = True

                # Reconstruct message
                message = ' '.join([word for word in words])

        # Initialize dialog for talk/response
        self.dialog[ID] = {}
        self.dialog[ID]['talk'] = {}
        self.dialog[ID]['response'] = {}

        # Find target and fill up dialog
        if targets != None and target_table == None and target_ID == None:
            # Get all the names in the room right now
            self.look(silent=True)

            # MATCH search name with one in the room (self.names)
            search_target = ''
            if targets:
                for data in self.names:
                    if data['name'].lower().find(targets.lower()) >= 0:
                        # We's founds yous! :D
                        search_target = data
                        break
                if not search_target:
                    self.response.append("Could not find " + targets)
                    return
            else:
                self.response.append("Talk to who/what?")
                return

            # Get NPC's default dialog
            self.get_target_info(
                table=str(search_target['table']), ID=str(search_target['ID']))
            self.dialog[ID]['talk']['table'] = str(search_target['table'])
            self.dialog[ID]['talk']['ID'] = str(self.target['ID'])
            self.dialog[ID]['talk']['name'] = str(self.target['name'])
            if TID != None:
                # This means custom dialog initiated yay!
                self.target['TID'] = str(TID)
            self.dialog[ID]['talk']['TID'] = str(self.target['TID'])

        elif target_table != None and target_ID != None and TID != None:
            # This means dialog_response is calling us!
            self.get_target_info(
                table=str(target_table), ID=str(target_ID))
            self.dialog[ID]['talk']['table'] = str(target_table)
            self.dialog[ID]['talk']['ID'] = str(target_ID)
            self.dialog[ID]['talk']['name'] = str(self.target['name'])
            self.dialog[ID]['talk']['TID'] = str(TID)

        else:
            raise ValueError("Requires table, ID, TID or just name!")

        # If third argument provided (<talk> <name> <message>) spit out message
        if message:
            self.say(message, emote=emote)

            # For nonplayers add extra <br>
            if self.mode != 'player':
                self.response.append('<br />')

        # Loop through all the TIDs in case of extended dialogs
        while True:
            # Fetch the dialog based on TID
            self.sql.cursor.execute(
                "SELECT * FROM dialog_talk WHERE ID = '" +
                str(self.dialog[ID]['talk']['TID']) + "'")
            row = self.sql.cursor.fetchone()

            # Are we emoting?
            emote = False
            words = row['talk'].split(" ")
            if words[0] == 'emote':
                emote = True

            # Time to start talking!
            self.dialog[ID]['talk']['TID'] = str(row['TID'])
            if str(row['ID']) != "1":
                self.say(row['talk'], target=True, emote=emote)
            else:
                # Means no dialog option so don't call say func, just do this
                self.response.append(row['talk'])

            # Is dialog_talk coming to it's end?
            if self.dialog[ID]['talk']['TID'] == "0":
                self.dialog[ID]['talk']['TID'] = str(row['ID'])
                break

        # Get dialog response
        self.sql.cursor.execute(
            "SELECT * FROM dialog_response WHERE TID = '" +
            self.dialog[ID]['talk']['TID'] + "'")
        rows = self.sql.cursor.fetchall()
        if rows:
            count = 0 # Choice number
            end_dialog = {} # For all responses that have end action
            end_count = 0

            # Start building the response list
            for row in rows:
                if row['action'] != 'end':
                    count += 1
                    if self.mode == 'player':
                        self.response.append(
                            str(count) + ". " + row['response'])
                    self.dialog[ID]['response'][str(count)] = {
                        "RID": row['ID'],
                        "text": row['response'],
                        "action": row['action']}
                else:
                    # We have end dialog responses, place in seperate list
                    end_dialog[end_count] = {
                        "RID": row['ID'],
                        "text": row['response'],
                        "action": row['action']}
                    end_count += 1

            # Do we have responses that end dialog?
            if end_count > 0:
                # WE DO! Place those at the end of the response list
                for elem in end_dialog.items():
                    count += 1
                    if self.mode == 'player':
                        self.response.append(
                            str(count) + ". " + elem[1]['text'])
                    self.dialog[ID]['response'][str(count)] = {
                        "RID": elem[1]['RID'],
                        "text": elem[1]['text'],
                        "action": elem[1]['action']}

        # Lock being
        if self.mode == 'player':
            self.player['lock'] = 1
        else:
            self.npc[ID]['lock'] = 1
        self.debug("Dialog: " + str(self.dialog))

    def dialog_response(self, choice):
        if not choice:
            if self.mode == 'player':
                self.response.append("Need a number for choosen response.")
            return

        # Get ID shortcut
        if self.mode == 'player':
            ID = str(self.player['ID'])
        else:
            ID = str(self.NID)

        # Check for finding choice and meeting conditions
        find = False

        # Make sure we have dialog to respond to
        if len(self.dialog) < 1:
            if self.mode == 'player':
                self.response.append("Need to talk to someone first!")
            return
        self.debug("Dialog: " + str(self.dialog))

        # Begin processing the response
        for value in self.dialog[ID]['response'].items():
            # Value is the response choice number
            if str(value[0]) == str(choice):
                message = ''

                # Get updated target info we're talking to
                self.get_target_info(
                    self.target['table'], ID=str(self.target['ID']))

                # Are we emoting?
                emote = False
                words = self.dialog\
                    [ID]['response'][value[0]]['text'].split(' ')
                if words[0] == 'emote':
                    # DRAAAMA! Ok pop out emote keyword and flag emote variable
                    emote = True
                    words.pop(0)
                message = ' '.join(words)

                # Take action and say response based on mode
                if self.mode == 'player':
                    if str(self.player['ZID']) == str(self.target['ZID']):
                        self.say(message, emote=emote)
                        self.dialog_action(
                            self.player,
                            self.dialog[ID]['response'][value[0]]['action'])
                    else:
                        self.response.append("Talk to who/what?")
                else:
                    if (str(self.npc[ID]['ZID']) ==
                        str(self.target['ZID'])):
                        self.say(message, emote=emote)

                        # Add extra <br> spacing for nonplayers
                        if self.dialog\
                           [ID]['response'][value[0]]['action'] != 'end':
                            self.response.append('<br />')
                        self.dialog_action(
                            self.npc[ID],
                            self.dialog[ID]['response'][value[0]]['action'])

                # Flag that we found choice and break loop
                find = True
                break

        # If we didn't find anything, let player know about choice
        if find == False and self.mode == 'player':
            self.response.append("Not available as a response.")

    def dialog_action(self, being, actions):
        ID = str(being['ID'])

        # Process the response action to take
        action_list = actions.split(' ')
        if action_list[0] == 'heal':
            self.heal(being)
            self.set_target_info(being)
            self.dialog[ID]['talk'] = {}
            self.dialog[ID]['response'] = {}

        elif action_list[0] == 'talk':
            self.dialog_talk(
                target_table=action_list[1], target_ID=action_list[2],
                TID=action_list[4])

        elif action_list[0] == 'end':
            # Remove locks and empty dialog
            if self.mode == 'player':
                self.player['lock'] = 0
            else:
                self.npc[self.NID]['lock'] = 0
            self.dialog[ID]['talk'] = {}
            self.dialog[ID]['response'] = {}

    def get_combat_stats(self, being):
        # Max status
        being['max_health'] = round(
            (int(being['condition']) * 10) +
            ((int(being['endurance']) * 10) / 2))
        being['max_magic'] = round(
            (int(being['aura']) * 10) +
            ((int(being['mind']) * 10) / 2))
        being['max_stamina'] = round(
            (int(being['endurance']) * 10) +
            ((int(being['strength']) * 10) / 2))

        # Attack/Defensive capabilities
        health = int(being['health']) / int(being['max_health'])
        stamina = int(being['health']) / int(being['max_health'])
        if health < 0.5:
            health = 0.5
        if stamina < 0.5:
            stamina = 0.5
        being['as'] = round((
            ((int(being['strength']) * 3) + int(being['condition'])) *
            health) * stamina)
        being['ds'] = round((
            ((int(being['condition']) * 2) + int(being['strength'])) *
            health) * stamina)
        being['ma'] = round(
            (int(being['mind']) * 6) + ((int(being['aura']) * 3) / 2))
        being['md'] = round(
            (int(being['aura']) * 4) + ((int(being['mind']) * 3) / 2))

        return being

    def get_npc_info(self):
        # Update player data first
        self.get_player_info()

        # Flag to check if NPC variable was already initiated once
        npc_existance = False
        if len(self.npc) < 1:
            npc_existance = True

        # Get NPC SQL data
        if self.mode == 'nemesis':
            self.sql.cursor.execute(
                "SELECT * FROM " + self.npc_table + " WHERE PID = " +
                str(self.player['ID']))
            rows = self.sql.cursor.fetchall()
        elif self.mode == 'simple':
            self.sql.cursor.execute(
                "SELECT * FROM " + self.npc_table + " WHERE ZID = " +
                str(self.player['ZID']))
            rows = self.sql.cursor.fetchall()
        elif self.mode == 'creatures':
            self.sql.cursor.execute(
                "SELECT * FROM " + self.npc_table +
                " WHERE zones LIKE '%" + str(self.player['ZID']) + "%'")
            rows = self.sql.cursor.fetchall()

        # Setup all NPC data
        for row in rows:
            ID = str(row['ID'])
            self.npc[ID] = dict(row)
            self.npc[ID]['table'] = self.npc_table
            self.npc[ID]['full_name'] = (
                self.npc[ID]['name'] + ' ' +
                self.npc[ID]['surname'])
            self.npc[ID]['lock'] = 0

            # Get random events for NPC
            self.npc[ID]['events'] = {}
            self.sql.cursor.execute(
                "SELECT * FROM random_events WHERE NID = '" + ID +
                "' AND table_name = '" + self.npc_table + "'")
            events = self.sql.cursor.fetchall()
            for event in events:
                event = dict(event) # Convert row object into dict
                self.npc[ID]['events'][event['ID']] = event

            # Add special event for to spawning (currently only creatures)
            if self.mode == 'creatures':
                self.npc[ID]['events']['0'] = {
                    'ID': '0',
                    'table_name': str(self.npc_table),
                    'NID': str(ID),
                    'min': str(row['chance']),
                    'max': str(row['chance']),
                    'action': 'spawn'}

            # Update combat stats
            self.npc[ID] = self.get_combat_stats(self.npc[ID])

            # Set last ID to self.NID
            if npc_existance == False or self.mode == 'nemesis':
                self.NID = ID

        # Remove old NPC data if no longer in zone
        if self.mode == 'creatures' or self.mode == 'simple':

            # Requires zone list
            clones = copy.deepcopy(self.npc)
            for ID, data in clones.items():

                # Get the zones NPC roams
                zones = clones[ID]['zones'].split(' ')

                # Are we bound to one spot?
                if zones[0] == '-1':

                    # If so, just check if in same room as player
                    if int(clones[ID]['ZID']) != int(self.player['ZID']):
                        self.debug(
                            "Deleting " + self.npc[ID]['full_name'] +
                            " because player not in it's zone.")
                        del self.npc[ID]

                else:

                    # Search if player is in any of the NPC zones
                    check = False
                    for ZID in zones:
                        if int(ZID) == int(self.player['ZID']):
                            check = True

                    # Remove NPC if not in one of the NPC zones
                    if check == False:
                        self.debug(
                            "Deleting " + self.npc[ID]['full_name'] +
                            " because player not in it's zone.")
                        del self.npc[ID]

                    # Health check
                    if int(clones[ID]['health']) == 0 and check == True:
                        self.npc[ID]['spawn'] = 0
                        self.npc[ID] = self.heal(self.npc[ID])

    def get_target_info(self, table, ID=None, name=None):
        # Sanitize value that is used often
        ID = str(ID)

        # Get target
        if len(ID) > 0 and len(table) > 0:
            self.sql.cursor.execute(
                "SELECT * FROM " + str(table) + " WHERE ID = '" + str(ID) + "'")
            row = self.sql.cursor.fetchone()
        elif len(name) > 0 and len(table) > 0:
            self.sql.cursor.execute(
                "SELECT * FROM " + str(table) + " WHERE name = '" +
                str(name) + "' COLLATE NOCASE")
            row = self.sql.cursor.fetchone()
        else:
            raise ValueError("Requires SQL table name and target name or ID!")

        # Setup target data
        self.target = dict(row)
        self.target['full_name'] = (
            self.target['name'] + ' ' + self.target['surname'])

        # Update combat stats
        self.target['table'] = str(table)
        self.target = self.get_combat_stats(self.target)

    def get_player_info(self):
        # Database info
        # Investigate: Why is this try needed for npc.py
        try:
            self.sql.cursor.execute('SELECT version FROM game_settings LIMIT 1')
        except sqlite3.ProgrammingError:
            self.sql = database.Database()
            self.sql.connect()
        self.sql.cursor.execute("SELECT * FROM stats_players")
        row = self.sql.cursor.fetchone()
        self.player = dict(row)
        self.sql.cursor.execute("SELECT * FROM appearance_players")
        row = self.sql.cursor.fetchone()
        self.player = dict(self.player, **row)
        del self.player['CID']

        # In memory only
        self.player['full_name'] = (
            self.player['name'] + ' ' + self.player['surname'])
        self.player['table'] = 'stats_players'
        self.player['update'] = False # update GUI progress bars
        self.player['rt_max'] = 5 # Max round time in seconds
        self.player['rt_ts'] = time.time()
        self.player['rt_flag'] = False # To start a timer or not
        leveltotal = (self.player['level'] * 100) * 2
        if self.player['experience'] > leveltotal and self.levelup == False:
            self.levelup = True
            self.response.append("You have leveled up!")

        # Update combat stats
        self.player = self.get_combat_stats(self.player)

    def set_target_info(self, being):
        # Common columns amongst all
        common = (
            "name = '" + str(being['name']) +
            "', surname = '" + str(being['surname']) +
            "', ZID = '" + str(being['ZID']) +
            "', lock = '" + str(being['lock']) +
            "', aura = '" + str(being['aura']) +
            "', appeal = '" + str(being['appeal']) +
            "', condition = '" + str(being['condition']) +
            "', endurance = '" + str(being['endurance']) +
            "', luck = '" + str(being['luck']) +
            "', mind = '" + str(being['mind']) +
            "', strength = '" + str(being['strength']) +
            "', level = '" + str(being['level']) +
            "', health = '" + str(being['health']) +
            "', stamina = '" + str(being['stamina']) +
            "', magic = '" + str(being['magic']) + "'"
        )

        # Determine type
        if being['table'] == 'stats_players':
            self.sql.cursor.execute(
                "UPDATE " + being['table'] +
                " SET " + common +
                ", experience = '" + str(being['experience']) +
                "' WHERE ID = '" + str(being['ID']) + "'")
            self.sql.save()
        elif being['table'] == 'stats_npc_nemesis':
            self.sql.cursor.execute(
                "UPDATE " + being['table'] +
                " SET " + common +
                ", PID = '" + str(being['PID']) +
                "', TID = '" + str(being['TID']) +
                "', chance = '" + str(being['chance']) +
                "', spawn = '" + str(being['spawn']) +
                "' WHERE ID = '" + str(being['ID']) + "'")
            self.sql.save()
        elif being['table'] == 'stats_npc_simple':
            self.sql.cursor.execute(
                "UPDATE " + being['table'] +
                " SET " + common +
                ", TID = '" + str(being['TID']) +
                "', chance = '" + str(being['chance']) +
                "', spawn = '" + str(being['spawn']) +
                "' WHERE ID = '" + str(being['ID']) + "'")
            self.sql.save()
        elif being['table'] == 'stats_npc_creatures':
            self.sql.cursor.execute(
                "UPDATE " + being['table'] +
                " SET " + common +
                ", TID = '" + str(being['TID']) +
                "', chance = '" + str(being['chance']) +
                "', spawn = '" + str(being['spawn']) +
                "' WHERE ID = '" + str(being['ID']) + "'")
            self.sql.save()

    def search_target(self, needle):
        # Search for target in player's room by name
        if self.player['name'].lower().find(needle.lower()) >= 0:
            return self.player

        # Searching all NPCs
        self.also_here()
        for data in self.names:
            if data['name'].lower().find(needle.lower()) >= 0:
                self.get_target_info(data['table'], data['ID'])
                return self.target

        return False

    def combat(self, targets, attack_type='nonmagic'):
        # Check if there are round timers and if so return early
        if self.mode == 'player':
            if self.player['rt_flag'] == True:
                self.response.append("Round timer in action")
                return

        # Determine who the attacker and defender is
        if self.mode != 'player' and targets == 'player':

            self.get_npc_info() # Gets player info too
            defender = self.player
            attacker = self.npc[self.NID]

        else:

            # Find out who/what's available for targetting by getting self.names
            self.look(silent=True)

            # Check if attacker's target matches who/what's available
            search_target = ''
            if len(targets) > 0:
                for name in self.names:
                    if name[2].lower().find(targets.lower()) >= 0:
                        search_target = name
                        break
                if len(search_target) < 1:
                    self.response.append("Could not find " + targets)

            else:
                self.response.append("Who/What?")

            # Get target's details
            if search_target:
                self.get_target_info(
                    name=search_target[2],
                    table=search_target[0],
                    ID=search_target[1])
                defender = self.target
                if self.mode == 'player':
                    self.get_player_info()
                    attacker = self.player
                else:
                    self.get_npc_info()
                    attacker = self.npc[self.NID]

        self.debug(defender)

        # Do combat math
        damage = 0 # default to no damage
        if attack_type == 'magic':

            pass # TODO

        else:

            if defender['ds'] > (attacker['as'] * 2):

                # For those too powerful to do combat with
                if self.mode == 'player':
                    self.response.append(
                        defender['full_name'] + "is too strong!")

            else:

                # Do the dice roll
                attacker_roll = (
                    attacker['as'] - (attacker['as'] *
                    (round(random.uniform(.1, .2), 2) *
                    (1 - (attacker['luck'] / 100)))))
                defender_roll = (
                    defender['as'] - (defender['as'] *
                    (round(random.uniform(.1, .2), 2) *
                    (1 - (defender['luck'] / 100)))))

                if attacker_roll > defender_roll:

                    # Get damage value
                    damage = attacker_roll - defender_roll
                    if damage > defender['health']:
                        defender['health'] = 0
                    else:
                        defender['health'] = int(defender['health'] - damage)

                    # Get experience value
                    if (self.mode == 'player' and
                        attacker['table'] == 'player_stats'):
                        experience = (
                            (defender['level'] / attacker['level']) * 10)
                        attacker['experience'] += int(round(experience))

                    # Update database for state change
                    self.set_target_info(defender)
                    if defender['table'] == 'player_stats':
                        self.player['update'] = True
                    self.response.append(
                        attacker['full_name'] + " (AS: " + str(attacker['as']) +
                        ") attacks " + defender['full_name'] + " (DS: " +
                        str(defender['ds']) + ") for " +
                        str(round(damage, 2)) + " damage (Health: " +
                        str(defender['health']) + ")!")

                else:

                    # Bad roll, didn't succeed in doing damage
                    if self.mode == 'player' and int(attacker['health']) > 0:
                        self.response.append(
                            "You fail to do any damage")
                    elif self.mode == 'player' and int(attacker['health']) == 0:
                        self.response.append(
                            "You can not attack without health!")
                    elif int(attacker['health']) > 0:
                        self.response.append(
                            attacker['full_name'] +
                            " fails to do any damage against " +
                            defender['full_name'] + "!")
                self.debug(
                    "Attacker Health: " + str(attacker['health']) +
                    " Attacker Roll: " + str(attacker_roll) +
                    " Defender Roll: " + str(defender_roll) +
                    " Damage: " + str(damage) +
                    " Defender Health: " + str(defender['health']))

        # Add timers
        if self.mode == 'player':
            #self.player['rt_ts'] = time.time()
            self.player['rt_flag'] = True

    def heal(self, being):
        being['max_health'] = round(
            (int(being['condition']) * 10) +
            ((int(being['endurance']) * 10) / 2))
        being['health'] = being['max_health']
        if being['table'] == 'character_players':
            being['update'] = True
        self.set_target_info(being)

        if self.mode == 'player':
            self.response.append(being['name'] + " has been healed!")

        return being