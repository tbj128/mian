from sqlite3 import dbapi2 as sqlite3

# 
# Initialization including database creation of the project
# 

def init_db():
	connection = sqlite3.connect("mian.db")
	cur = connection.cursor()
	with open('schema.sql', mode='r') as f:
		cur.executescript(f.read())
	connection.commit()

init_db()
print('Initialized the database.')