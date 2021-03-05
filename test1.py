from flask import Flask, render_template, request, redirect, url_for
import json
from textures import get_textures_list, get_maister_list, get_column_names
from datetime import date
import sqlite3


app = Flask(__name__)

texture_list = get_textures_list()
maister_list = get_maister_list()
gen_info = ['2021-02-10', '2', maister_list[0], '1']

column_names = dict()
for i in ['robota_zm']:                     # додати в список інші таблиці
    column_names[i] = get_column_names(i)

def get_pressE(i, thick):
    if i in [1,2,3,4,5,6,7]:
        p = 1
    elif i in [8,9,10,11,12,13,14]: 
        p = 2
    if i in [1,2,3,4,8,9,10,11]:
        e = 1
    elif i in [5,6,7,12,13,14]:
        e = 2
    return [p,e,thick,i]

def update_command(table, names_lst, lst):
    if table == 'robota_zm':   
        command = "UPDATE robota_zm SET"
        for x in range(5,38):
            command += f" {names_lst[x+1]} = '{lst[x]}',"
        command = command[:-1]
        command += f" WHERE zmina_id = {lst[0]} AND textures_id = {lst[1]} AND press = {lst[2]} AND e_quality = {lst[3]} AND thickness={lst[4]}"
        return command


@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html', title='Ламінування')


@app.route("/home2", methods=["POST", "GET"])
@app.route("/home16", methods=["POST","GET"])
@app.route("/home18", methods=["POST","GET"])
def home2():
    global gen_info
    if request.method == "POST":
        t_lists = []
        thick = request.form.get('thickness')
        cur_textures = request.form.getlist("texture")
        zinfo = request.form.getlist("zm_info")
        conn = sqlite3.connect("db/lam1.db")
        cur = conn.cursor()
        cur.execute(f"SELECT maister_id FROM maister WHERE general_name='{zinfo[2]}'")
        maister_id = cur.fetchone()[0]
        nomer_zm = request.form.get('zm_nomer')

        # checking for 'zmina' and insert new if needed       
        cur.execute(f"SELECT zmina_id, nomer_zm, maister_id FROM zmina WHERE zm_date='{zinfo[0]}' AND zm_zmina='{zinfo[1]}'")
        zm_id = cur.fetchone()
        if zm_id:
            if zm_id[2] != maister_id or nomer_zm != zm_id[1]:
                cur.execute(f"UPDATE zmina SET nomer_zm='{nomer_zm}', maister_id='{maister_id}' WHERE zm_date='{zinfo[0]}' AND zm_zmina='{zinfo[1]}'")
        else:
            cur.execute(f"INSERT INTO zmina (zm_date,zm_zmina,nomer_zm,maister_id) VALUES ('{zinfo[0]}', '{zinfo[1]}', '{nomer_zm}', '{maister_id}')")
            cur.execute(f"SELECT zmina_id FROM zmina WHERE zm_date='{zinfo[0]}' AND zm_zmina='{zinfo[1]}'")
            zm_id = cur.fetchone()

        # going through every textures and make lists for non-empty textures 
        for i in range(1,15):
            if cur_textures[i-1] == '':
                continue
            pe = get_pressE(i, thick)
            texture_id = texture_list.index(cur_textures[i-1]) + 1      # id starts from 1 in db table
            t_lists.append([zm_id[0], texture_id] + pe + request.form.getlist(f"t{i}"))

        cur.execute
        rob_zm_names = column_names['robota_zm']
        for i in t_lists:
            try:
                cur.execute(f"INSERT INTO robota_zm {rob_zm_names[1:]} VALUES {tuple(i)}")
            except sqlite3.IntegrityError:
                command = update_command('robota_zm', rob_zm_names, i)
                print(tuple(i))
                cur.execute(command)
        conn.commit()
        conn.close()
        return render_template('home2.html', title='Ламінування', gen_info=gen_info, maister_list=maister_list, texture_list=texture_list)
   
    if request.method == "GET":
        t_lists = []
        cur_textures = []
        rule = request.url_rule
        if rule.rule == "/home16":
            koef, thick = 0.08052, '16'
        else:
            koef, thick = 0.090585, '18'
        tinfo = request.args.getlist("top_info")
        if tinfo:
            gen_info = tinfo + [thick]
        else: 
            gen_info = [date.today().isoformat(), '1', '', '', thick]   #додати ім'я майстра {3}
        print('GETTT')
        conn = sqlite3.connect('db/lam1.db')
        cur = conn.cursor()
        cur.execute(f"SELECT zmina_id, nomer_zm, general_name FROM zmina INNER JOIN maister ON zmina.maister_id=maister.maister_id WHERE zm_date='{gen_info[0]}' AND zm_zmina='{gen_info[1]}'")
        zm_id = cur.fetchone()
        if zm_id:
            cur.execute(f"SELECT * FROM robota_zm WHERE zmina_id='{zm_id[0]}' AND thickness='{thick}'")
            c = cur.fetchall()
            for i in c:
                t_lists.append((texture_list[i[2]-1],) + i[6:])
            gen_info[2], gen_info[3] = zm_id[2], zm_id[1]
        else:
            pass
        conn.close()
        return render_template('home2.html', title="LAMIN", koef=koef, thick=thick, gen_info=gen_info, maister_list=maister_list, texture_list=texture_list, t_lists=json.dumps(t_lists))

    


@app.route("/work", methods=["POST","GET"])
def robota():
    if request.method == 'POST':
        pass
    if request.method == 'GET':
        t_lists = []
        rule = request.url_rule
        if rule.rule == '/work':
            koef, thick, eq = 0.08052, '16', '1'
        tinfo = request.args.getlist("top_info")
        if tinfo:
            gen_info = tinfo + [thick, eq]
        else: 
            gen_info = [date.today().isoformat(), '1', '', '', thick, eq]
        print(gen_info)
        conn = sqlite3.connect('db/lam1.db')
        cur = conn.cursor()
        cur.execute(f"SELECT zmina_id, nomer_zm, general_name FROM zmina INNER JOIN maister ON zmina.maister_id=maister.maister_id WHERE zm_date='{gen_info[0]}' AND zm_zmina='{gen_info[1]}'")
        zm_id = cur.fetchone()
        if zm_id:
           # cur.execute(f"SELECT name,sort1,sort2,sort3,sort4 FROM robota_zm INNER JOIN textures ON robota_zm.textures_id=textures.textures_id WHERE zmina_id='{zm_id[0]}' AND thickness='{thick}' AND e_quality='{eq}'")
            cur.execute(f"""SELECT t.name,zmina_id,thickness,e_quality,sum(zr1),sum(zr2),sum(zr3),sum(zr4),sum(sort1),sum(sort2),sum(sort3),sum(sort4), sum(zs1),sum(zs2),sum(zs3),sum(zs4), sum(zf1),sum(zf2),sum(zf3),sum(zf4)
                FROM (SELECT textures_id,zmina_id,thickness,e_quality,NULL zr1,NULL zr2,NULL zr3,NULL zr4,sort1,sort2,sort3,sort4,NULL zs1,NULL zs2,NULL zs3,NULL zs4,NULL zf1,NULL zf2,NULL zf3,NULL zf4
                FROM remainders
                WHERE source='nas' AND zmina_id={zm_id[0]} AND thickness={thick} AND e_quality={eq}
                UNION ALL
                SELECT textures_id,zmina_id,thickness,e_quality,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,sort1,sort2,sort3,sort4,NULL,NULL,NULL,NULL 
                FROM remainders
                WHERE source='zis' AND zmina_id={zm_id[0]} AND thickness={thick} AND e_quality={eq}
                UNION ALL
                SELECT textures_id,zmina_id,thickness,e_quality,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,sort1,sort2,sort3,sort4
                FROM remainders
                WHERE source='zif' AND zmina_id={zm_id[0]} AND thickness={thick} AND e_quality={eq}
                UNION ALL
                SELECT textures_id,zmina_id,thickness,e_quality,sort1,sort2,sort3,sort4,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL
                FROM robota_zm
                WHERE zmina_id={zm_id[0]} AND thickness={thick} AND e_quality={eq})
                INNER JOIN textures t USING(textures_id)
                GROUP BY t.name
            """)
            c = cur.fetchall()
            for i in c:
                print(i)
                t_lists.append(tuple('' if x==None or x==0.0 else x for x in i))
            gen_info[2], gen_info[3] = zm_id[2], zm_id[1]
        else:
            pass
        conn.close()
    return render_template('work.html', title='Рух плити', koef=koef, thick=thick, gen_info=gen_info, maister_list=maister_list, texture_list=texture_list, t_lists=t_lists)


@app.route("/test", methods=["GET", "POST"])
def test():
    n = request.form.getlist("f1")
    m = request.form.get("f2text")
    return render_template("test.html", n=n, m=m)


@app.route("/about")
def about():
    return render_template('about.html', title='Інструкція')


if __name__ == '__main__':
    app.run(debug=True)
