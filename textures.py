import sqlite3

def get_textures_list():
	textures = []
	conn = sqlite3.connect('db/lam1.db')
	cursor = conn.cursor()
	cursor.execute("SELECT max(rowid) FROM Textures")
	n = cursor.fetchone()[0] - 1
	cursor.execute("SELECT name FROM Textures")
	for _ in range(n):
		textures.append(cursor.fetchone()[0])
	conn.close()
	return textures


def get_maister_list():
	maisters = []
	conn = sqlite3.connect('db/lam1.db')
	cursor = conn.cursor()
	cursor.execute("SELECT count(maister_id) FROM maister WHERE active='1'")
	n = cursor.fetchone()[0]
	cursor.execute("SELECT general_name FROM maister WHERE active='1'")
	for _ in range(n):
		maisters.append(cursor.fetchone()[0])
	conn.close()
	return maisters


def insert_textures_to_db():
	conn = sqlite3.connect('db/lam1.db')
	cursor = conn.cursor()
	with open("tests/textures.txt", 'r', encoding='utf-8') as f:
		for line in f:
			cursor.execute("INSERT INTO Textures(name,code) VALUES (?,?)",tuple(line.strip().split('\t')))
	conn.commit()
	conn.close()

def get_column_names(table):
	conn = sqlite3.connect('db/lam1.db')
	cursor = conn.cursor()
	c = cursor.execute(f"SELECT * FROM {table}")
	res = tuple([i[0] for i in c.description])
	conn.close()
	return res
