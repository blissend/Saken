import sys

# Custom modules
import commands
import database
import styles

# GUI modules
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtGui as QtGui
import PyQt5.QtCore as QtCore

class LevelUp(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()

        # Get database setup
        self.sql = database.Database()
        self.sql.connect()
        self.sql.cursor.execute("SELECT * FROM game_settings")
        row = self.sql.cursor.fetchone()
        self.phor = dict(row)

        # Player information
        self.cmd = commands.Commands()
        self.cmd.get_player_info()
        self.points = 0
        self.experience = int(self.cmd.player['experience'])
        self.level = int(self.cmd.player['level'])
        while True:
            level_req = (self.level * 100) * 2
            if self.experience >= level_req:
                self.experience -= level_req
                self.level += 1
                self.points += 10
            else:
                break
        self.all_stats_total = (
            int(self.cmd.player['aura']) +
            int(self.cmd.player['appeal']) +
            int(self.cmd.player['condition']) +
            int(self.cmd.player['endurance']) +
            int(self.cmd.player['luck']) +
            int(self.cmd.player['mind']) +
            int(self.cmd.player['strength']))
        self.last_total = self.all_stats_total # Helps determine to add/sub

        # Build the UI
        self.build_ui()

    def build_ui(self):
        # The main area
        self.setWindowTitle("Level Up")
        #main_frame = QtWidgets.QFrame(self)
        #main_frame.setObjectName("main_frame")
        self.total = QtWidgets.QLabel(self)
        self.total.setText("Total Points " + str(self.points))

        self.aura = QtWidgets.QSpinBox(self)
        self.aura.setMinimum(int(self.cmd.player['aura']))
        self.aura.setMaximum(100)
        self.aura.valueChanged.connect(self.stats_change)
        self.aura.setSuffix(" Aura")
        self.aura.setAttribute(QtCore.Qt.WA_MacShowFocusRect, False)

        self.appeal = QtWidgets.QSpinBox(self)
        self.appeal.setMinimum(int(self.cmd.player['appeal']))
        self.appeal.setMaximum(100)
        self.appeal.valueChanged.connect(self.stats_change)
        self.appeal.setSuffix(" Appeal")
        self.appeal.setAttribute(QtCore.Qt.WA_MacShowFocusRect, False)

        self.condition = QtWidgets.QSpinBox(self)
        self.condition.setMinimum(int(self.cmd.player['condition']))
        self.condition.setMaximum(100)
        self.condition.valueChanged.connect(self.stats_change)
        self.condition.setSuffix(" Condition")
        self.condition.setAttribute(QtCore.Qt.WA_MacShowFocusRect, False)

        self.endurance = QtWidgets.QSpinBox(self)
        self.endurance.setMinimum(int(self.cmd.player['endurance']))
        self.endurance.setMaximum(100)
        self.endurance.valueChanged.connect(self.stats_change)
        self.endurance.setSuffix(" Endurance")
        self.endurance.setAttribute(QtCore.Qt.WA_MacShowFocusRect, False)

        self.luck = QtWidgets.QSpinBox(self)
        self.luck.setMinimum(int(self.cmd.player['luck']))
        self.luck.setMaximum(100)
        self.luck.valueChanged.connect(self.stats_change)
        self.luck.setSuffix(" Luck")
        self.luck.setAttribute(QtCore.Qt.WA_MacShowFocusRect, False)

        self.mind = QtWidgets.QSpinBox(self)
        self.mind.setMinimum(int(self.cmd.player['mind']))
        self.mind.setMaximum(100)
        self.mind.valueChanged.connect(self.stats_change)
        self.mind.setSuffix(" Mind")
        self.mind.setAttribute(QtCore.Qt.WA_MacShowFocusRect, False)

        self.strength = QtWidgets.QSpinBox(self)
        self.strength.setMinimum(int(self.cmd.player['strength']))
        self.strength.setMaximum(100)
        self.strength.valueChanged.connect(self.stats_change)
        self.strength.setSuffix(" Strength")
        self.strength.setAttribute(QtCore.Qt.WA_MacShowFocusRect, False)

        self.save = QtWidgets.QPushButton()
        self.save.setText("Save")
        self.save.clicked.connect(self.stats_save)

        # Layout & Sizing
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.total)
        vbox.addWidget(self.aura)
        vbox.addWidget(self.appeal)
        vbox.addWidget(self.condition)
        vbox.addWidget(self.endurance)
        vbox.addWidget(self.luck)
        vbox.addWidget(self.mind)
        vbox.addWidget(self.strength)
        hbox = QtWidgets.QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(self.save)
        vbox.addLayout(hbox)
        self.setLayout(vbox)
        self.setGeometry(300, 300, 250, 120)
        #self.show()

    def stats_change(self):
        total = (
            self.aura.value() + self.appeal.value() + self.condition.value() +
            self.endurance.value() + self.luck.value() + self.mind.value() +
            self.strength.value())
        total_diff = total - self.all_stats_total
        widget = self.sender().text().split(" ")

        if total_diff <= self.points:
            self.total.setText("Total Points " + str(self.points - total_diff))
        elif widget[1] == 'Aura':
            self.aura.setValue(self.aura.value() - 1)
        elif widget[1] == 'Appeal':
            self.appeal.setValue(self.appeal.value() - 1)
        elif widget[1] == 'Condition':
            self.condition.setValue(self.condition.value() - 1)
        elif widget[1] == 'Endurance':
            self.endurance.setValue(self.endurance.value() - 1)
        elif widget[1] == 'Luck':
            self.luck.setValue(self.luck.value() - 1)
        elif widget[1] == 'Mind':
            self.mind.setValue(self.mind.value() - 1)
        elif widget[1] == 'Strength':
            self.strength.setValue(self.strength.value() - 1)

    def stats_save(self):
        total = (
            self.aura.value() + self.appeal.value() + self.condition.value() +
            self.endurance.value() + self.luck.value() + self.mind.value() +
            self.strength.value())
        total_diff = total - self.all_stats_total
        current_points = self.points - total_diff

        if current_points == 0:
            self.cmd.player['level'] = self.level
            self.cmd.player['experience'] = self.experience
            self.cmd.player['aura'] = self.aura.value()
            self.cmd.player['appeal'] = self.appeal.value()
            self.cmd.player['condition'] = self.condition.value()
            self.cmd.player['endurance'] = self.endurance.value()
            self.cmd.player['luck'] = self.luck.value()
            self.cmd.player['mind'] = self.mind.value()
            self.cmd.player['strength'] = self.strength.value()
            self.cmd.set_target_info(self.cmd.player)
            self.accept()
        else:
            reply = QtWidgets.QMessageBox.warning(
                self, "Notice",
                "You must spend all points!")

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    lvlup = LevelUp()
    #app.setStyleSheet(APPSTYLE)
    sys.exit(app.exec_())