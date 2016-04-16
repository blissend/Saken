import sqlite3
import os

DBNAME = 'Saken.db'

class Database:
    def __init__(self):
        if os.path.isfile(DBNAME) == False:
            raise Exception("Could not find: " + DBNAME)

    def connect(self):
        self.connection = sqlite3.connect(
            DBNAME, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()

    def save(self):
        self.connection.commit()

    def close(self, save=False):
        if save:
            self.connection.commit()
        self.cursor.close()
        self.connection.close()