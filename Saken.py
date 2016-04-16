import platform
import sys
import time
#import multiprocessing as mp
from multiprocessing import Process, Pipe

# Custom modules
import creatures
import commands
import database
import levelup
#import morph TODO
import nemesis
import settings
import simple
import styles

# GUI modules
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtGui as QtGui
import PyQt5.QtCore as QtCore

# Custom signal for QThread
class Signals(QtCore.QObject):
    update = QtCore.pyqtSignal(str)

class Saken(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        # Build App Variables
        self.sql = database.Database()
        self.sql.connect()
        self.sql.cursor.execute('SELECT * FROM game_settings')
        row = self.sql.cursor.fetchone()
        self.phor = dict(row)

        # Display Pretties & Load
        self.build_ui()
        self.load_game()

    def build_ui(self):
        # Main Frame
        main_frame = QtWidgets.QFrame(self)
        main_frame.setObjectName("main_frame")
        right_frame = QtWidgets.QFrame(main_frame)
        right_frame.setObjectName("right_frame")
        right_frame.setMaximumWidth(200)

        # Left Column Widgets
        self.text_out = QtWidgets.QTextEdit()
        self.text_out.setReadOnly(True)
        self.text_out.setObjectName("text_out")
        self.bar_rt = QtWidgets.QProgressBar()
        self.bar_rt.setObjectName("bar_rt")
        self.bar_rt_value = 0
        self.bar_rt.setValue(self.bar_rt_value)
        self.bar_rt.setFormat("  Round Timer")
        self.round_timer = QtCore.QTimer()
        self.round_timer.timeout.connect(self.update_rt)
        self.text_in = QtWidgets.QLineEdit()
        self.text_in.setObjectName("text_in")
        completer = QtWidgets.QCompleter()
        self.text_in.setCompleter(completer)
        self.text_in_history = QtCore.QStringListModel()
        self.typed_history = []
        completer.setModel(self.text_in_history)
        self.text_in.returnPressed.connect(self.execute_player_command)

        # Right Column Widgets
        def barify(bar, text):
            bar.setValue(100)
            bar.setFormat(" " + text)
        status = QtWidgets.QLabel()
        status.setText("<strong>Status</strong>")
        self.health_bar = QtWidgets.QProgressBar()
        barify(self.health_bar, "Health")
        self.magic_bar = QtWidgets.QProgressBar()
        barify(self.magic_bar, "Magic")
        self.stamina_bar = QtWidgets.QProgressBar()
        barify(self.stamina_bar, "Stamina")
        self.stats = QtWidgets.QLabel()
        self.stats.setObjectName("stats")
        self.stats.setText("Stats (Level: 0)")
        self.bar_aura = QtWidgets.QProgressBar()
        barify(self.bar_aura, "Aura")
        self.bar_appeal = QtWidgets.QProgressBar()
        barify(self.bar_appeal, "Appeal")
        self.bar_condition = QtWidgets.QProgressBar()
        barify(self.bar_condition, "Condition")
        self.bar_endurance = QtWidgets.QProgressBar()
        barify(self.bar_endurance, "Endurance")
        self.bar_luck = QtWidgets.QProgressBar()
        barify(self.bar_luck, "Luck")
        self.bar_mind = QtWidgets.QProgressBar()
        barify(self.bar_mind, "Mind")
        self.bar_strength = QtWidgets.QProgressBar()
        barify(self.bar_strength, "Strength")

        # Layout
        vbox_left = QtWidgets.QVBoxLayout()
        vbox_left.addWidget(self.text_out)
        vbox_left.addWidget(self.bar_rt)
        vbox_left.addWidget(self.text_in)
        vbox_right = QtWidgets.QVBoxLayout(right_frame)
        vbox_right.setContentsMargins(0, 0, 0, 0)
        vbox_right.setSpacing(5)
        vbox_right.addWidget(status)
        vbox_right.addWidget(self.health_bar)
        vbox_right.addWidget(self.magic_bar)
        vbox_right.addWidget(self.stamina_bar)
        vbox_right.addWidget(self.stats)
        vbox_right.addWidget(self.bar_aura)
        vbox_right.addWidget(self.bar_appeal)
        vbox_right.addWidget(self.bar_condition)
        vbox_right.addWidget(self.bar_endurance)
        vbox_right.addWidget(self.bar_luck)
        vbox_right.addWidget(self.bar_mind)
        vbox_right.addWidget(self.bar_strength)
        vbox_right.addStretch(1)
        gbox_main = QtWidgets.QGridLayout(main_frame)
        gbox_main.setSpacing(10)
        gbox_main.addLayout(vbox_left, 0, 0)
        gbox_main.addWidget(right_frame, 0, 1, QtCore.Qt.AlignTop)
        self.setCentralWidget(main_frame)

        # Menu Items
        action_about = QtWidgets.QAction(QtGui.QIcon(""), "About", self)
        #action_about.setShortcut('Ctrl+Q')
        action_about.setStatusTip("About " + self.phor['name'])
        action_about.triggered.connect(self.dialog_about)
        action_settings = QtWidgets.QAction(QtGui.QIcon(""), "Settings", self)
        #action_settings.setShortcut('Ctrl+Q')
        action_settings.setStatusTip("Game Settings")
        action_settings.triggered.connect(self.dialog_settings)
        action_exit = QtWidgets.QAction(QtGui.QIcon(""), "Exit", self)
        action_exit.setShortcut('Ctrl+Q')
        action_exit.setStatusTip("Exit " + self.phor['name'])
        action_exit.triggered.connect(self.close)

        # Menu Layout
        self.phor_menubar = self.menuBar()
        self.phor_menubar.setNativeMenuBar(False)
        self.phor_menubar.setObjectName("phor_menubar")
        menu_file = self.phor_menubar.addMenu('&File')
        menu_file.addAction(action_settings)
        menu_file.addSeparator()
        menu_file.addAction(action_exit)
        menu_help = self.phor_menubar.addMenu('&Help')
        menu_help.addAction(action_about)

        # Window Settings
        self.text_in.setFocus(True)
        self.text_in.setAttribute(QtCore.Qt.WA_MacShowFocusRect, False)
        self.setGeometry(300, 300, 820, 480)
        if self.phor['name']:
            self.setWindowTitle(self.phor['name'])
        else:
            self.setWindowTitle('Saken')
        #self.setWindowFlags(QtCore.Qt.CustomizeWindowHint) # Hides Window Frame
        #self.show()

    def dialog_settings(self):
        config = settings.Settings()
        config.exec_()

    def dialog_levelup(self):
        leveling = levelup.LevelUp()
        if leveling.exec_():
            self.update_bars()

    def dialog_morph(self):
        morphing = morph.Morph()
        if morphing.exec_():
            pass

    def dialog_about(self):
        self.sql.cursor.execute('SELECT * FROM game_settings')
        row = self.sql.cursor.fetchone()
        self.phor = dict(row)
        debug = "False"
        pause = "False"
        if self.phor['debug']:
            debug = "True"
        if self.phor['pause']:
            pause = "True"
        details = ("Name: " + self.phor['name'] + "\n" +
                   "Version: " + self.phor['version'] + "\n" +
                   "Debug: " + debug + "\n" +
                   "Pause: " + pause)
        reply = QtWidgets.QMessageBox.about(
            self, "About " + self.phor['name'], details)
        #if reply = QMessageBox.Ok:
            #pass

    def load_game(self):
        # Initialize the location
        self.cmd = commands.Commands()
        self.update_bars()
        self.cmd.process('look', mode='game')
        for response in self.cmd.response:
            self.text_out.insertHtml(response)

        # PyQT doesn't seem to have python's multiprocessing (mp) capabilities
        # So we are doing things through QThreads instead and then mp

        # Initialize nemesis
        self.npc_nemesis = nemesis.Nemesis()
        self.npc_nemesis_thread = QtCore.QThread()
        self.npc_nemesis_thread.run = self.npc_nemesis_worker
        self.npc_nemesis_thread.close = False
        self.npc_nemesis_thread.start()

        # Initialize simple
        self.npc_simple = simple.Simple()
        self.npc_simple_thread = QtCore.QThread()
        self.npc_simple_thread.run = self.npc_simple_worker
        self.npc_simple_thread.close = False
        self.npc_simple_thread.start()

        # Initialize creatures
        self.npc_creatures = creatures.Creatures()
        self.npc_creatures_thread = QtCore.QThread()
        self.npc_creatures_thread.run = self.npc_creatures_worker
        self.npc_creatures_thread.close = False
        self.npc_creatures_thread.start()

        # Initialize multiprocessing/threads signal to communicate
        self.signals = Signals()
        self.signals.update.connect(self.execute_game_command)

        # Initialize the round timer
        self.round_timer.start(1000)

    def update_rt(self):
        # Keep bringing down to 0
        if self.bar_rt_value > 0:
            self.bar_rt_value -= 25
            if self.bar_rt_value < 0:
                self.bar_rt_value = 0
            self.bar_rt.setValue(self.bar_rt_value)

        # Reset flag when 0
        if self.bar_rt_value == 0:
            self.cmd.player['rt_flag'] = False

    def execute_player_command(self):
        # History for input box
        text = self.text_in.text()
        self.typed_history.append(text)
        if len(self.typed_history) < 20:
            self.text_in_history.setStringList(self.typed_history)
        else:
            self.typed_history.pop()
            self.text_in_history.setStringList(self.typed_history)

        # Begin processing command(s)
        if self.bar_rt_value == 0:
            if "levelup" in text.lower():
                # TODO: break apart and process commands in order with levelup
                self.dialog_levelup()
            else:
                self.cmd.process(text)
                for response in self.cmd.response:
                    self.text_out.moveCursor(QtGui.QTextCursor.End)
                    self.text_out.insertHtml(response)
                    self.text_out.moveCursor(QtGui.QTextCursor.End)
                    # TODO: Control buffer
                    #data = self.text_out.toHtml()
                    #print(len(data))
            self.text_in.setText('')
        else:
            self.text_out.moveCursor(QtGui.QTextCursor.End)
            self.text_out.insertHtml("<br />Round timer in action\n<br />")
            self.text_out.moveCursor(QtGui.QTextCursor.End)
            self.text_in.setText('')

        # Check for value updates
        if self.cmd.player['update']:
            self.cmd.player['update'] = False
            self.update_bars()
        if self.cmd.player['rt_flag'] and self.bar_rt_value == 0:
            self.bar_rt_value = 100
            self.bar_rt.setValue(self.bar_rt_value)

    def execute_game_command(self, event):
        if event != 'update_bars':
            self.text_out.moveCursor(QtGui.QTextCursor.End)
            self.text_out.insertHtml(event)
            self.text_out.moveCursor(QtGui.QTextCursor.End)
        else:
            # Only update progress bars
            self.update_bars()

    def update_bars(self):
        # Get latest stats/status
        self.cmd.get_player_info()

        # Update bar values
        self.health_bar.setValue(
            round((self.cmd.player['health'] /
                   self.cmd.player['max_health']) * 100))
        self.magic_bar.setValue(
            round((self.cmd.player['magic'] /
                   self.cmd.player['max_magic']) * 100))
        self.stamina_bar.setValue(
            round((self.cmd.player['stamina'] /
                   self.cmd.player['max_stamina']) * 100))
        # Alternative way to display bar filling
        #total_pie = (
            #self.cmd.player['aura'] +
            #self.cmd.player['appeal'] +
            #self.cmd.player['condition'] +
            #self.cmd.player['endurance'] +
            #self.cmd.player['luck'] +
            #self.cmd.player['mind'] +
            #self.cmd.player['strength'])
        stat_list = [
            self.cmd.player['aura'],
            self.cmd.player['appeal'],
            self.cmd.player['condition'],
            self.cmd.player['endurance'],
            self.cmd.player['luck'],
            self.cmd.player['mind'],
            self.cmd.player['strength']]
        biggest = 0
        for elem in stat_list:
            if biggest < int(elem):
                biggest = int(elem)
        self.bar_aura.setValue(
            round((self.cmd.player['aura']/biggest) * 100))
        self.bar_appeal.setValue(
            round((self.cmd.player['appeal']/biggest) * 100))
        self.bar_condition.setValue(
            round((self.cmd.player['condition']/biggest) * 100))
        self.bar_endurance.setValue(
            round((self.cmd.player['endurance']/biggest) * 100))
        self.bar_luck.setValue(
            round((self.cmd.player['luck']/biggest) * 100))
        self.bar_mind.setValue(
            round((self.cmd.player['mind']/biggest) * 100))
        self.bar_strength.setValue(
            round((self.cmd.player['strength']/biggest) * 100))

        # Update text values
        levelup = ''
        level_req = (int(self.cmd.player['level']) * 100) * 2
        if self.cmd.player['experience'] > level_req:
            levelup += "Level Up!"
        self.stats.setText(
            "<strong>Stats (Level " + str(self.cmd.player['level']) +
            ") " + levelup + "</strong>")
        self.health_bar.setFormat(
            "  Health: " + str(self.cmd.player['health']))
        self.magic_bar.setFormat(
            "  Magic: " + str(self.cmd.player['magic']))
        self.stamina_bar.setFormat(
            "  Stamina: " + str(self.cmd.player['stamina']))
        self.bar_aura.setFormat(
            "  Aura: " + str(self.cmd.player['aura']))
        self.bar_appeal.setFormat(
            "  Appeal: " + str(self.cmd.player['appeal']))
        self.bar_condition.setFormat(
            "  Condition: " + str(self.cmd.player['condition']))
        self.bar_endurance.setFormat(
            "  Endurance: " + str(self.cmd.player['endurance']))
        self.bar_luck.setFormat(
            "  Luck: " + str(self.cmd.player['luck']))
        self.bar_mind.setFormat(
            "  Mind: " + str(self.cmd.player['mind']))
        self.bar_strength.setFormat(
            "  Strength: " + str(self.cmd.player['strength']))

    def npc_nemesis_worker(self):
        # Pipes because I decided to learn about pipes
        pinternal, cinternal = Pipe()
        pexternal, cexternal = Pipe()
        worker_process = Process(
            target=self.npc_nemesis.think, args=(cexternal, cinternal))
        worker_process.daemon = True
        worker_process.start()
        data = ''

        while True:
            # Do we have data from internal?
            if pinternal.poll():
                data = pinternal.recv()

            # If we do, begin processesing
            if len(data) > 0:
                if data == 'END' or self.npc_nemesis_thread.close == True:
                    pexternal.send('END')
                    break
                elif data == 'EMPTY':
                    # ODDITY: Find out why we have to send something always
                    pass
                else:
                    if type(data) == str:
                        self.signals.update.emit(data)
                    else:
                        # Assume it's a list
                        concatenated = ''
                        for elem in data:
                            if len(concatenated) == 0:
                                concatenated = elem
                            else:
                                concatenated += '\n' + elem
                        self.signals.update.emit(concatenated)

                # wipe so we don't process again
                data = ''

    def npc_simple_worker(self):
        # REDUNDANT code, make REUSABLE
        # Pipes because I decided to learn about pipes
        pinternal, cinternal = Pipe()
        pexternal, cexternal = Pipe()
        worker_process = Process(
            target=self.npc_simple.think, args=(cexternal, cinternal))
        worker_process.daemon = True
        worker_process.start()
        data = ''

        while True:
            # Do we have data from internal?
            if pinternal.poll():
                data = pinternal.recv()

            # If we do, begin processesing
            if len(data) > 0:
                if data == 'END' or self.npc_simple_thread.close == True:
                    pexternal.send('END')
                    break
                elif data == 'EMPTY':
                    # ODDITY: Find out why we have to send something always
                    pass
                else:
                    if type(data) == str:
                        self.signals.update.emit(data)
                    else:
                        # Assume it's a list
                        concatenated = ''
                        for elem in data:
                            if len(concatenated) == 0:
                                concatenated = elem
                            else:
                                concatenated += '\n' + elem
                        self.signals.update.emit(concatenated)

                # wipe so we don't process again
                data = ''

    def npc_creatures_worker(self):
        # REDUNDANT code, make REUSABLE
        # Pipes because I decided to learn about pipes
        pinternal, cinternal = Pipe()
        pexternal, cexternal = Pipe()
        worker_process = Process(
            target=self.npc_creatures.think, args=(cexternal, cinternal))
        worker_process.daemon = True
        worker_process.start()
        data = ''

        while True:
            # Do we have data from internal?
            if pinternal.poll():
                data = pinternal.recv()

            # If we do, begin processesing
            if len(data) > 0:
                if data == 'END' or self.npc_creatures_thread.close == True:
                    pexternal.send('END')
                    break
                elif data == 'EMPTY':
                    # ODDITY: Find out why we have to send something always
                    pass
                else:
                    if type(data) == str:
                        self.signals.update.emit(data)
                    else:
                        # Assume it's a list
                        concatenated = ''
                        for elem in data:
                            if len(concatenated) == 0:
                                concatenated = elem
                            else:
                                concatenated += '\n' + elem
                        self.signals.update.emit(concatenated)

                # wipe so we don't process again
                data = ''

    def closeEvent(self, event):
        # Kill processes
        self.npc_nemesis_thread.close = True
        self.npc_nemesis_thread.wait()
        self.npc_simple_thread.close = True
        self.npc_simple_thread.wait()
        self.npc_creatures_thread.close = True
        self.npc_creatures_thread.wait()

if __name__ == '__main__':
    if platform.system().lower() == "windows":
        styles.APPSTYLE += styles.APPSTYLE + styles.MSSTYLE2
    else:
        styles.APPSTYLE += styles.APPSTYLE + styles.MACSTYLE
    app = QtWidgets.QApplication(sys.argv)
    Phor = Saken()
    Phor.show()
    app.setStyleSheet(styles.APPSTYLE)
    sys.exit(app.exec_())