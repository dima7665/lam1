from flask import Flask, render_template, request, redirect, url_for
import json
from textures import get_textures_list, get_maister_list, get_column_names
from textures import sql_command_month_rem, sql_command_work_get
from datetime import date
import sqlite3


app = Flask(__name__)

texture_list = get_textures_list()
maister_list = get_maister_list()
gen_info = ['2021-02-10', '2', maister_list[0], '1']

column_names = dict()
for i in ['robota_zm','remainders', 'month_rem']:                     # додати в список інші таблиці
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
    if table == 'remainders':
        command = "UPDATE remainders SET"
        print('------ ', names_lst, '-----', lst)
        for x in range(5,9):
            command += f" {names_lst[x+1]} = '{lst[x]}',"
        command = command[:-1]
        command += f" WHERE zmina_id = {lst[0]} AND textures_id = {lst[1]} AND thickness={lst[2]} AND e_quality = {lst[3]} AND source='{lst[4]}'"
        return command
    if table == 'month_rem':
        command = "UPDATE month_rem SET"
        for x in range(5,9):
            command += f" {names_lst[x]} = '{lst[x]}',"
        command = command[:-1]
        command += f" WHERE month = '{lst[0]}' AND year = '{lst[1]}' AND textures_id='{lst[2]}' AND thickness = '{lst[3]}' AND e_quality='{lst[4]}'"
        return command

def make_texture_lists_for_remainders(lst):
    tmp_lst = [lst[i*13:(i+1)*13] for i in range(len(lst)//13)]
    res_lst, tl = [], []
    for i in tmp_lst:
        t = i[0]
        tl.append(t)
        for x in range(3):
            line = i[1+x*4:1+(x+1)*4]
            if all(z=='' or z==None for z in line):
                continue
            if(x==0):
                source = 'nas'
            elif(x==1):
                source = 'zis'
            else:
                source = 'zif'
            res_lst.append([t, source] + line)
            print("***********  ", res_lst[-1])
    return tl, res_lst


@app.route("/home")
def home():
    return render_template('home.html', title='Ламінування')

@app.route("/")
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
            cur.execute(f"SELECT textures_id FROM textures WHERE name={cur_textures[i-1]}")
            texture_id = cur.fetchone()[0]
            t_lists.append([zm_id[0], texture_id] + pe + request.form.getlist(f"t{i}"))

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
            if len(tinfo)<4:
                tinfo += [''] * (4 - len(tinfo))
            gen_info = tinfo + [thick]
        else: 
            gen_info = [date.today().isoformat(), '1', '', '', thick]   #додати ім'я майстра {3}
        print('GETTT')
        conn = sqlite3.connect('db/lam1.db')
        cur = conn.cursor()
        cur.execute(f"SELECT zmina_id, nomer_zm, general_name FROM zmina INNER JOIN maister ON zmina.maister_id=maister.maister_id WHERE zm_date='{gen_info[0]}' AND zm_zmina='{gen_info[1]}'")
        zm_id = cur.fetchone()
        print(tinfo)
        if zm_id:
            cur.execute(f"SELECT * FROM robota_zm INNER JOIN textures USING(textures_id) WHERE zmina_id='{zm_id[0]}' AND thickness='{thick}'")
            c = cur.fetchall()
            for i in c:
                t_lists.append(i[-2:-1] + i[6:-2])
     #           t_lists.append((texture_list[i[2]-1],) + i[6:])
            gen_info[2], gen_info[3] = zm_id[2], zm_id[1]
        else:
            pass
        conn.close() 
        return render_template('home2.html', title="LAMIN", koef=koef, thick=thick, gen_info=gen_info, maister_list=maister_list, texture_list=texture_list, t_lists=json.dumps(t_lists))

    


@app.route("/work", methods=["POST","GET"])
def robota():
    global gen_info
    if request.method == 'POST':
        t_list = []
        thick, eq = request.form.get("thickness"), request.form.get("e_quality")
        koef = 0.08052
        zinfo = request.form.getlist('zm_info')
        cur_textures = request.form.getlist("tvalues")
        print(cur_textures)
        cur_textures, values_list = make_texture_lists_for_remainders(cur_textures)
        print(zinfo)
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

        for t in values_list:
            cur.execute(f"SELECT textures_id FROM textures WHERE name='{t[0]}'")
            print(t[0], t)
            texture_id = cur.fetchone()[0]
            t_list.append([zm_id[0], texture_id, thick, eq] + t[1:])
        
        remainders_names = column_names['remainders']
        for i in t_list:
            try:
                print(tuple(i))
                cur.execute(f"INSERT INTO remainders {remainders_names[1:]} VALUES {tuple(i)}")
            except sqlite3.IntegrityError:
                command = update_command('remainders', remainders_names, i)
                cur.execute(command)
        conn.commit()
        conn.close()
        return render_template('work.html', title='Рух плити', gen_info=gen_info, koef=koef, thick=thick, maister_list=maister_list, texture_list=texture_list)

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
        mdate = gen_info[0].split('-')[0:2]
        conn = sqlite3.connect('db/lam1.db')
        cur = conn.cursor()
        cur.execute(f"SELECT zmina_id, nomer_zm, general_name FROM zmina INNER JOIN maister ON zmina.maister_id=maister.maister_id WHERE zm_date='{gen_info[0]}' AND zm_zmina='{gen_info[1]}'")
        zm_id = cur.fetchone()
        if zm_id:
           # cur.execute(f"SELECT name,sort1,sort2,sort3,sort4 FROM robota_zm INNER JOIN textures ON robota_zm.textures_id=textures.textures_id WHERE zmina_id='{zm_id[0]}' AND thickness='{thick}' AND e_quality='{eq}'")
            cur.execute(sql_command_work_get.format(zm_id[0], thick, eq, mdate[1], mdate[0]))
            c = cur.fetchall()
            for i in c:
                print(i)
                t_lists.append(tuple('' if x==None or x==0.0 else x for x in i))
            gen_info[2], gen_info[3] = zm_id[2], zm_id[1]
        else:
            pass
        conn.close()
        title = 'Рух плити ' + thick + ' E' + ('05' if eq=='2' else '1')
        return render_template('work.html', title=title, koef=koef, thick=thick, gen_info=gen_info, maister_list=maister_list, texture_list=texture_list, t_lists=t_lists)


@app.route("/mf", methods=["POST", "GET"])
def monfin():
    if request.method == "GET":
        return render_template('monthfinisher.html', maister_list=maister_list, texture_list=texture_list) 
    if request.method == "POST":
        m = request.form.getlist('mfin')
        month_rem_names = column_names['month_rem']

        # month and year for select all 
        mon = ('01','02','03','04','05','06','07','08','09','10','11','12')[int(m[1])-2]
        year = m[0] if int(m[1])>1 else int(m[0])-1
        start_date, end_date = f'{year}-{mon}-01', f'{year}-{mon}-31'          
        conn = sqlite3.connect("db/lam1.db")
        cur = conn.cursor()
        thick, eq ='16', '1'
        for tex_name in ['Аляска']:
            cur.execute(f"SELECT textures_id FROM textures WHERE name='{m[2]}'")
            tid = cur.fetchone()[0]

            # textures_id, thickness, e_quality, start_date, end_date, month, year
            cur.execute(sql_command_month_rem.format(tid, thick, eq, start_date, end_date, mon, year))
            res = cur.fetchone()
            currecord = cur.execute(f"SELECT sort1,sort2,sort3,sort4 FROM month_rem WHERE month='{m[1]}' AND year='{m[0]}' AND textures_id='{tid}' AND thickness='{thick}' AND e_quality='{eq}'").fetchone()

            do = False
            if not any(res[1:]):                # if movement record [0,0,0,0]
                if currecord:                   # and current record exist
                    if any(currecord):       # and current record is not [0,0,0,0]
                        do = True
            else:                               # if movement record is not [0,0,0,0]
                do = True
                if currecord:
                    if res[1:] == currecord:
                        do = False
            message = "No update in db"
            if do:
                ins = [m[1], m[0], res[0], thick, eq] + list(res[1:])  # порядок стовпців у таблиці month_rem
                try:
                    cur.execute(f"INSERT INTO month_rem {month_rem_names[1:]} VALUES {tuple(ins)}")
                except sqlite3.IntegrityError:
                    command = update_command('month_rem', month_rem_names[1:], ins)
                    cur.execute(command)
                conn.commit()
                message = f"{m[0]}-{m[1]}  complete --- {m[2]} --- {currecord} ===> {res[1:]}"
        return render_template('monthfinisher.html', maister_list=maister_list, texture_list=texture_list, message=message)   


@app.route("/addtexture", methods=["POST","GET"])
@app.route("/addnewtexture", methods=["POST"])
@app.route("/addremaindersfromfile", methods=["POST"])
def add_texture():
    if request.method == 'POST':
        rule = request.url_rule
        if rule.rule == "/addremaindersfromfile":
            data = request.form.getlist("newrem")
            print(data)

            # try:
            #     con = sqlite3.connect('lam1/db/lam1.db')
            #     cur = con.cursor()
            #     txt_filename = 'rem.txt'
            #     with open(txt_filename,'r',encoding='utf-8') as f:  
            #         text = f.read().split('\n')
            #         t = []
            #         for i in text[:-1]:
            #             i = i.split('\t')
            #             c = cur.execute(f"SELECT textures_id FROM textures WHERE name='{i[0].strip()}'").fetchone()
            #             if c:
            #                 t.append([c[0]] + i[1:])
            #             else:
            #                 print(f"no id for  {i[0]} --- ",c)
            #     for i in t[0:4]:
            #         try:
            #             cur.execute(f"""INSERT INTO month_rem (month,year,textures_id,thickness,e_quality,sort1,sort2,sort3,sort4)
            #                 VALUES('04','2021','{i[0]}','16','1','{i[1]}','{i[2]}','{i[3]}','{i[4]}')""")
            #         except sqlite3.IntegrityError:
            #             continue
            #     con.commit()
            # finally:
            #     con.close()
            message = 'Complete'
            return render_template("addtexture.html", texture_list=texture_list, message=message)
        if rule.rule == "/addnewtexture":
            new_t = request.form.getlist("newtex")
            try:
                con = sqlite3.connect('lam1/db/lam1.db')
                cur = con.cursor()
                try:
                    cur.execute(f"""INSERT INTO textures (name, code)
                        VALUES('{new_t[1]}','{new_t[0]}')""")
                except sqlite3.IntegrityError:
                    pass           # додати UPDATE  або  видати повідомлення що така текстура і код вже є
                con.commit()
            finally:
                con.close()
        if rule.rule == "/addtexturesfromfile":
            pass
    if request.method == 'GET':
        return render_template("addtexture.html", texture_list=texture_list)


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
