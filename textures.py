import sqlite3
from datetime import date, timedelta

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

def prev_day(d):
    d = date.fromisoformat(d) - timedelta(days=1)
    return d.isoformat()

sql_command_month_rem = """
        SELECT tt.textures_id, st.s1+pres.s1-nas.s1+zis.s1-zif.s1 sort1, st.s2+pres.s2-nas.s2+zis.s2-zif.s2 sort2, st.s3+pres.s3-nas.s3+zis.s3-zif.s3 sort3, st.s4+pres.s4-nas.s4+zis.s4-zif.s4 sort4
        FROM (SELECT * FROM textures WHERE textures_id={0}) tt
            LEFT JOIN
            (SELECT textures_id,COALESCE(sum(sort1),0) s1,COALESCE(sum(sort2),0) s2,COALESCE(sum(sort3),0) s3,COALESCE(sum(sort4),0) s4
                FROM remainders INNER JOIN zmina z USING(zmina_id)
                WHERE source='nas' AND textures_id='{0}' AND thickness='{1}' AND e_quality='{2}' AND zm_date BETWEEN '{3}' AND '{4}') nas
            LEFT JOIN
            (SELECT COALESCE(sum(sort1),0) s1,COALESCE(sum(sort2),0) s2,COALESCE(sum(sort3),0) s3,COALESCE(sum(sort4),0) s4
                FROM remainders INNER JOIN zmina z USING(zmina_id)
                WHERE source='zis' AND textures_id='{0}' AND thickness='{1}' AND e_quality='{2}' AND zm_date BETWEEN '{3}' AND '{4}') zis
            LEFT JOIN 
            (SELECT COALESCE(sum(sort1),0) s1,COALESCE(sum(sort2),0) s2,COALESCE(sum(sort3),0) s3,COALESCE(sum(sort4),0) s4
                FROM remainders INNER JOIN zmina z USING(zmina_id)
                WHERE source='zif' AND textures_id='{0}' AND thickness='{1}' AND e_quality='{2}' AND zm_date BETWEEN '{3}' AND '{4}') zif
            LEFT JOIN
            (SELECT COALESCE(sum(sort1),0) s1,COALESCE(sum(sort2),0) s2,COALESCE(sum(sort3),0) s3,COALESCE(sum(sort4),0) s4
                FROM month_rem 
                WHERE month='{5}' AND year='{6}' AND textures_id='{0}' AND thickness='{1}' AND e_quality='{2}') st
            LEFT JOIN
            (SELECT COALESCE(sum(sort1),0) s1,COALESCE(sum(sort2),0) s2,COALESCE(sum(sort3),0) s3,COALESCE(sum(sort4),0) s4
                FROM robota_zm INNER JOIN zmina z USING(zmina_id)
                WHERE textures_id='{0}' AND thickness='{1}' AND e_quality='{2}' AND zm_date BETWEEN '{3}' AND '{4}') pres
        """

sql_command_work_get = """SELECT t.name,zmina_id,thickness,e_quality,sum(zr1),sum(zr2),sum(zr3),sum(zr4),sum(sort1),sum(sort2),sum(sort3),sum(sort4), sum(zs1),sum(zs2),sum(zs3),sum(zs4), sum(zf1),sum(zf2),sum(zf3),sum(zf4),sum(ms1),sum(ms2),sum(ms3),sum(ms4)
            FROM (SELECT textures_id,zmina_id,thickness,e_quality,NULL zr1,NULL zr2,NULL zr3,NULL zr4,sort1,sort2,sort3,sort4,NULL zs1,NULL zs2,NULL zs3,NULL zs4,NULL zf1,NULL zf2,NULL zf3,NULL zf4,NULL ms1,NULL ms2,NULL ms3,NULL ms4
                    FROM remainders
                    WHERE source='nas' AND zmina_id={0} AND thickness={1} AND e_quality={2}
                UNION ALL
                SELECT textures_id,zmina_id,thickness,e_quality,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,sort1,sort2,sort3,sort4,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL 
                    FROM remainders
                    WHERE source='zis' AND zmina_id={0} AND thickness={1} AND e_quality={2}
                UNION ALL
                SELECT textures_id,zmina_id,thickness,e_quality,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,sort1,sort2,sort3,sort4,NULL,NULL,NULL,NULL
                    FROM remainders
                    WHERE source='zif' AND zmina_id={0} AND thickness={1} AND e_quality={2}
                UNION ALL
                SELECT textures_id,zmina_id,thickness,e_quality,sort1,sort2,sort3,sort4,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL
                    FROM robota_zm
                    WHERE zmina_id={0} AND thickness={1} AND e_quality={2}
                UNION ALL
                SELECT textures_id,NULL,thickness,e_quality,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,sort1 ms1,sort2 ms2,sort3 ms3,sort4 ms4
                    FROM month_rem
                    WHERE month='{3}' AND year={4} AND thickness={1} AND e_quality={2})
            INNER JOIN textures t USING(textures_id)
            GROUP BY t.name
            """