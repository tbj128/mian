import os
from sqlite3 import dbapi2 as sqlite3

#
# DB helper methods
#

def initDB(DB_PATH, SCHEMA_PATH):
    if not os.path.isfile(DB_PATH):
        print('Database does not exist. Creating new database at ' + DB_PATH)
        connection = sqlite3.connect(DB_PATH)
        cur = connection.cursor()
        with open(SCHEMA_PATH, mode='r') as f:
            cur.executescript(f.read())
        connection.commit()
    else:
        print('Database already exists.')
