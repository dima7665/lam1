import sqlite3

def get_textures_list():
	textures=[]
	conn = sqlite3.connect('db/lam1.db')
	cursor = conn.cursor()
	cursor.execute("SELECT max(rowid) FROM Textures")
	n = cursor.fetchone()[0] - 1
	cursor.execute("SELECT name FROM Textures")
	for _ in range(n):
		textures.append(cursor.fetchone()[0])
	conn.close()
	return textures



def insert_textures_to_db():
	conn = sqlite3.connect('db/lam1.db')
	cursor = conn.cursor()
	with open("tests/textures.txt", 'r', encoding='utf-8') as f:
		for line in f:
			cursor.execute("INSERT INTO Textures(name,code) VALUES (?,?)",tuple(line.strip().split('\t')))
	conn.commit()
	conn.close()