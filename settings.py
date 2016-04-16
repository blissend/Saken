import sys

# Custom modules
import database
import styles

# GUI modules
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtGui as QtGui
import PyQt5.QtCore as QtCore

class Settings(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()

        # Get database setup
        self.sql = database.Database()
        self.sql.connect()
        self.sql.cursor.execute("SELECT * FROM game_settings")
        row = self.sql.cursor.fetchone()
        self.phor = dict(row)

        # Build the UI
        self.build_ui()

    def build_ui(self):
        # The main area
        self.setWindowTitle("Game Settings")
        #main_frame = QtWidgets.QFrame(self)
        #main_frame.setObjectName("main_frame")
        debug = QtWidgets.QCheckBox('Debug Game', self)
        debug.setObjectName("toggle")
        pause = QtWidgets.QCheckBox('Pause Game', self)
        pause.setObjectName("toggle")

        # Default states and event connections
        if self.phor['debug'] == 1:
            debug.toggle()
        debug.stateChanged.connect(self.change_debug)
        if self.phor['pause'] == 1:
            pause.toggle()
        pause.stateChanged.connect(self.change_pause)

        # Layout & Sizing
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(debug)
        vbox.addWidget(pause)
        self.setLayout(vbox)
        self.setGeometry(300, 300, 250, 120)
        #self.show()

    def change_debug(self, state):
        if state == QtCore.Qt.Checked:
            self.sql.cursor.execute(
                "UPDATE game_settings SET debug = 1 " +
                "WHERE name = 'Phorsaken (alpha)'")
            self.sql.save()
        else:
            self.sql.cursor.execute(
                "UPDATE game_settings SET debug = 0 " +
                "WHERE name = 'Phorsaken (alpha)'")
            self.sql.save()

    def change_pause(self, state):
        if state == QtCore.Qt.Checked:
            self.sql.cursor.execute(
                "UPDATE game_settings SET pause = 1 " +
                "WHERE name = 'Phorsaken (alpha)'")
            self.sql.save()
        else:
            self.sql.cursor.execute(
                "UPDATE game_settings SET pause = 0 " +
                "WHERE name = 'Phorsaken (alpha)'")
            self.sql.save()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    config = Settings()
    #app.setStyleSheet(APPSTYLE)
    sys.exit(app.exec_())