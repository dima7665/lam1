from flask import Flask, render_template, request, redirect, url_for
import json
from textures import get_textures_list, get_column_names
from datetime import date
import sqlite3


app = Flask(__name__)

texture_list = get_textures_list()
rob_zm = ['22','','asd']
gen_info = ['2021-02-10','2','test maister']

column_names = dict()
for i in ['robota_zm']:                     # додати в список інші таблиці
    column_names[i] = get_column_names(i)

def get_pressE(i):
    if i in [1,2,3,4,5,6,7]:
        p = 1
    elif i in [8,9,10,11,12,13,14]: 
        p = 2
    if i in [1,2,3,4,8,9,10,11]:
        e = 1
    elif i in [5,6,7,12,13,14]:
        e = 2
    return [p,e]

def update_command(table, names_lst, lst):
    if table == 'robota_zm':   
        command = "UPDATE robota_zm SET"
        for x in range(4,37):
            command += f" {names_lst[x+1]} = '{lst[x]}',"
        command = command[:-1]
        command += f" WHERE zmina_id = {lst[0]} AND textures_id = {lst[1]} AND press = {lst[2]} AND e_quality = {lst[3]}"
        return command


@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html', title='Ламінування', rob_zm=rob_zm)


@app.route("/home2", methods=["POST","GET"])
def home2():
    if request.method == "POST":
        t_lists = []
        cur_textures = request.form.getlist("texture")

        zinfo = request.form.getlist("zm_info")
        conn = sqlite3.connect("db/lam1.db")
        cur = conn.cursor()
        cur.execute(f"SELECT maister_id FROM maister WHERE general_name='{zinfo[2]}'")
        maister_id = cur.fetchone()[0]
        nomer_zm = request.form.get('zm_nomer')

        # checking for 'zmina' and insert new if needed       
        cur.execute(f"SELECT zmina_id FROM zmina WHERE zm_date='{zinfo[0]}' AND zm_zmina='{zinfo[1]}'")
        zm_id = cur.fetchone()
        if zm_id:
            zm_id = zm_id[0]
        else:
            cur.execute(f"INSERT INTO zmina (zm_date,zm_zmina,nomer_zm,maister_id) VALUES ('{zinfo[0]}', '{zinfo[1]}', '{nomer_zm}', '{maister_id}')")
            cur.execute(f"SELECT zmina_id FROM zmina WHERE zm_date='{zinfo[0]}' AND zm_zmina='{zinfo[1]}'")
            zm_id = cur.fetchone()[0]

        # going through every textures and make lists for non-empty textures 
        for i in range(1,15):
            if cur_textures[i-1] == '':
                continue
            pe = get_pressE(i)
            texture_id = texture_list.index(cur_textures[i-1]) + 1      # id starts from 1 in db table
            t_lists.append([zm_id, texture_id] + pe + request.form.getlist(f"t{i}"))

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

    global gen_info
    if request.method == "GET":
        tinfo = request.args.getlist("top_info")
        if tinfo:
            gen_info = tinfo
        else: 
            gen_info = [date.today().isoformat(), '1','test maister']   #додати ім'я майстра {3}
        print('GETTT')

    return render_template('home2.html', title='Ламінування', gen_info=gen_info, texture_list=texture_list)


@app.route("/robota")
def robota():
    return render_template('robota.html', title='Робота зміни')


@app.route("/test", methods=["GET", "POST"])
def test():
    n = request.form.getlist("f1")
    m = request.form.get("f2text")
    return render_template("test.html", n=n,m=m)


@app.route("/about")
def about():
    return render_template('about.html', title='Інструкція')


if __name__ == '__main__':
    app.run(debug=True)
