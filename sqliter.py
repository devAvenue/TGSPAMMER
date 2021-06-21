import sqlite3
import config

class DBConnection(object):
    def __init__(self):
        self.conn = sqlite3.connect(f'{config.DIR}database.db', check_same_thread=False)
        self.c = self.conn.cursor()

    def add_additional_text(self, id , text):
        table = self.c.execute(f'SELECT ADDITIONAL FROM CHANNELS WHERE CHANNEL = "{id}"').fetchone()
        if table == None:
            self.c.execute(f'INSERT INTO CHANNELS(CHANNEL, ADDITIONAL) VALUES (?,?)', [str(id), str(text)])
        else:
            self.c.execute(f'UPDATE CHANNELS SET ADDITIONAL = (?) WHERE CHANNEL = (?)', [str(text),str(id)])
        self.conn.commit()

    def get_additional_text(self, id):
        table = self.c.execute(f'SELECT ADDITIONAL FROM CHANNELS WHERE CHANNEL = "{id}"').fetchone()
        return table

    def change_text(self, text):
        self.c.execute(f'UPDATE SETTINGS SET TEXT = (?) WHERE ID = (?)', [str(text, 1)])
        self.conn.commit()

    def change_photo(self, name):
        self.c.execute(f'UPDATE SETTINGS SET PHOTO = (?) WHERE ID = (?)', [str(name, 1)])
        self.conn.commit()

    def settings(self):
        table = self.c.execute(f'SELECT * FROM SETTINGS  WHERE ID = (?)', [1]).fetchone()
        return table

    def setSpam(self, spam):
        table = self.c.execute(f'UPDATE SETTINGS SET SPAM = (?) WHERE ID = (?)', [spam,1]).fetchone()
        return table

    def __del__(self):
        self.c.close()
        self.conn.close()