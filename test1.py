from flask import Flask, render_template, request, redirect, url_for
import json
from textures import get_textures_list, get_maister_list, get_column_names, prev_day
from textures import sql_command_month_rem, sql_command_rem_get, sql_command_remone_get
from check import checklist
from datetime import date, timedelta
import sqlite3


app = Flask(__name__)

texture_list = get_textures_list()
maister_list = get_maister_list()
gen_info = ['2021-02-10', '2', maister_list[0], '1']

column_names = dict()
for i in ['robota_zm','remainders', 'month_rem', 'zm_sklad']:                     # додати в список інші таблиці
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
    if table == 'zm_sklad':
        command = "UPDATE zm_sklad SET"
        for x in range(2,7):
            command += f" {names_lst[x]} = '{lst[x]}',"
        command = command[:-1]
        command += f" WHERE zmina_id='{lst[0]}' AND thickness='{lst[1]}'"
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

def getridofnone(x, val):
    return [val if i==None else i for i in x]

def intNone(x):
    return int(x) if x not in ['',None] else 0

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
            cur.execute(f"SELECT textures_id FROM textures WHERE name='{cur_textures[i-1]}'")
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
        zm_sklad_names = column_names['zm_sklad']
        try:
            val = [zm_id[0], thick] + request.form.getlist('resg')
            cur.execute(f"INSERT INTO zm_sklad {zm_sklad_names[1:]} VALUES {tuple(val)}")
        except sqlite3.IntegrityError:
            command = update_command('zm_sklad', zm_sklad_names[1:], val)
            cur.execute(command)
        conn.commit()
        conn.close()
        return render_template('home2.html', title='Ламінування', gen_info=gen_info, maister_list=maister_list, sklad = [0,0,0,0], texture_list=texture_list)
   
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
        print('GETTT', gen_info)
        try:
            conn = sqlite3.connect('db/lam1.db')
            cur = conn.cursor()
            cur.execute(f"""SELECT zmina_id, nomer_zm, general_name FROM zmina INNER JOIN maister ON zmina.maister_id=maister.maister_id 
                WHERE zm_date='{gen_info[0]}' AND zm_zmina='{gen_info[1]}'""")
            zm_id = cur.fetchone()
            if not zm_id:
                cur.execute(f"INSERT INTO zmina (zm_date,zm_zmina,nomer_zm,maister_id) VALUES ('{gen_info[0]}', '{gen_info[1]}', '', '')")
                cur.execute(f"SELECT zmina_id FROM zmina WHERE zm_date='{gen_info[0]}' AND zm_zmina='{gen_info[1]}'")
                zm_id = cur.fetchone()
            cur.execute(f"""SELECT * FROM robota_zm INNER JOIN textures USING(textures_id) 
                WHERE zmina_id='{zm_id[0]}' AND thickness='{thick}'
                AND NOT (sort1='' AND sort2='' AND sort3='' AND sort4='') """)
            c = cur.fetchall()
        # сумуємо в залежності від класу(Е) і пресу
            t = [[],[],[],[]]
            for i in c:
                if i[3] == 1 and i[4] == 1:
                    j = 0
                elif i[3] == 1 and i[4] == 2:
                    j = 1
                elif i[3] ==2 and i[4] == 1:
                    j = 2
                else:
                    j = 3
                t[j].append(i[-2:-1] + i[6:-2])
            for i in range(4):
                if i%2:
                    t[i] = t[i] + [tuple([''])] * (3 - len(t[i]))
                else:
                    t[i] = t[i] + [tuple([''])] * (4 - len(t[i]))
            t_lists = t[0] + t[1] + t[2] + t[3]
        # кінець сумування
            #print(len(gen_info), len(zm_id))
            gen_info[2], gen_info[3] = ['', ''] if len(zm_id) < 3 else [zm_id[2], zm_id[1]]
            ymd = gen_info[0].split('-')
            prevday = prev_day(gen_info[0])
            cur.execute(f"""SELECT zm1,zm2,zm3,zm4 FROM zm_sklad_month  
                WHERE month='{ymd[1]}' AND year='{ymd[0]}' AND thickness='{thick}'
                AND NOT (zm1='' AND zm2='' AND zm3='' AND zm4='') """)
            c = cur.fetchone()
            sklad = [0,0,0,0] if not c else list(c)
            print(sklad)
            for i in range(4):
                sel = [1, 2, 3, 4]
                sel.remove(i+1)
                try:
                    # sum everything this zmina sklad get
                    cur.execute(f"""SELECT p+zm{sel[0]}+zm{sel[1]}+zm{sel[2]} FROM
                        (SELECT COALESCE(SUM(pget),0) as p, COALESCE(SUM(zm{sel[0]}),0) as zm{sel[0]}, COALESCE(SUM(zm{sel[1]}),0) as zm{sel[1]}, COALESCE(SUM(zm{sel[2]}),0) as zm{sel[2]} 
                        FROM zm_sklad WHERE thickness='{thick}' AND zmina_id IN 
                            (SELECT zmina_id FROM zmina WHERE nomer_zm={i+1} AND zm_date BETWEEN '{ymd[0]}-{ymd[1]}-01' AND '{prevday}')
                        )
                    """)
                    c = cur.fetchone()
                    gain = int(c[0]) if c and c[0] not in ('',None) else 0
                    # sum everything this zmina sklad give
                    cur.execute(f"""SELECT sum(zm{i+1}) FROM zm_sklad WHERE thickness='{thick}' AND zmina_id IN 
                        (SELECT zmina_id FROM zmina WHERE nomer_zm!={i+1} AND zm_date BETWEEN '{ymd[0]}-{ymd[1]}-01' AND '{prevday}')
                    """)
                    c = cur.fetchone()
                    give = int(c[0]) if c and c[0] not in ('',None) else 0
                    # zapr this month on this zmina
                    cur.execute(f"""SELECT s1+s2+s3+s4 as zap FROM
                        (SELECT COALESCE(SUM(sort1),0) as s1, COALESCE(SUM(sort2),0) as s2, COALESCE(SUM(sort3),0) as s3, COALESCE(SUM(sort4),0) as s4
                        FROM robota_zm WHERE thickness={thick} AND zmina_id IN 
                            (SELECT zmina_id FROM zmina WHERE nomer_zm={i+1} AND zm_date BETWEEN '{ymd[0]}-{ymd[1]}-01' AND '{prevday}'))
                    """)
                    c = cur.fetchone()
                    zapr = int(c[0]) if c and c[0] not in ('',None) else 0
                except:
                    print("щось пішло не так")
                sklad[i] += gain - give - zapr
            print('sklad', sklad)
            # заповнюємо клітинки одержано 
            cur.execute(f"""SELECT s.pget,s.zm1,s.zm2,s.zm3,s.zm4, z.zmina_id,z.nomer_zm FROM zm_sklad as s INNER JOIN zmina as z USING(zmina_id)
                WHERE zm_date='{gen_info[0]}' AND zm_zmina='1' AND thickness='{thick}'
            """)
            c = cur.fetchone()
            if c:
                load_get = tuple([i if i not in ['', None] else 0 for i in c])
            else:
                load_get = (0,0,0,0,0,0,0)
            print(load_get)
            
            # для нічної зміни
            if gen_info[1] == '2':
                if load_get[5] not in (0, '', None):
                    cur.execute(f"""SELECT s1+s2+s3+s4 as zap FROM
                            (SELECT COALESCE(SUM(sort1),0) as s1, COALESCE(SUM(sort2),0) as s2, COALESCE(SUM(sort3),0) as s3, COALESCE(SUM(sort4),0) as s4
                            FROM robota_zm WHERE thickness={thick} AND zmina_id IN 
                                (SELECT zmina_id FROM zmina WHERE zm_zmina='1' AND zm_date='{gen_info[0]}'))
                    """)
                    c = cur.fetchone()
                    zapr = c[0] if c and c[0] not in [None, ''] else 0
                    d_zmina = load_get[-1]                  
                    sel = [1,2,3,4]
                    sel.remove(d_zmina)
                    for i in sel:
                        sklad[i - 1] -= load_get[i]
                    sklad[d_zmina - 1] += sum(load_get[x] for x in sel) + load_get[0] - zapr
                    print(sum(load_get[x] for x in sel), load_get[0], zapr, '------', d_zmina - 1)
                    cur.execute(f"""SELECT s.pget,s.zm1,s.zm2,s.zm3,s.zm4 FROM zm_sklad as s INNER JOIN zmina USING(zmina_id)
                    WHERE zm_date='{gen_info[0]}' AND zm_zmina='2' AND thickness={thick}
                    """)
                    c = cur.fetchone()
                    print('c',c)
                    if c:
                        load_get = [i if i not in ['', None] else 0 for i in c]
                    else:
                        load_get = [0,0,0,0,0,0,0]                    
                    print('sklad nich ', sklad)
                    print(load_get)
                    sklad = [int(i) for i in sklad]

        finally:
            conn.close() 
        #print(t_lists)
        return render_template('home2.html', title="LAMIN", koef=koef, thick=thick, gen_info=gen_info, load_get=load_get[:5], sklad=sklad, maister_list=maister_list, texture_list=texture_list, t_lists=json.dumps(t_lists))

    


@app.route("/work", methods=["POST","GET"])
def remainders():
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
        nomer_zm = int(request.form.get('zm_nomer'))

        # checking for 'zmina' and insert new if needed       
        cur.execute(f"SELECT zmina_id, nomer_zm, maister_id FROM zmina WHERE zm_date='{zinfo[0]}' AND zm_zmina='{zinfo[1]}'")
        zm_id = cur.fetchone()
        if zm_id:
            if zm_id[2] != maister_id or nomer_zm != zm_id[1]:
                print('UPDATE')
                cur.execute(f"UPDATE zmina SET nomer_zm='{nomer_zm}', maister_id='{maister_id}' WHERE zm_date='{zinfo[0]}' AND zm_zmina='{zinfo[1]}'")
        else:
            cur.execute(f"INSERT INTO zmina (zm_date,zm_zmina,nomer_zm,maister_id) VALUES ('{zinfo[0]}', '{zinfo[1]}', '{nomer_zm}', '{maister_id}')")
            cur.execute(f"SELECT zmina_id FROM zmina WHERE zm_date='{zinfo[0]}' AND zm_zmina='{zinfo[1]}'")
            zm_id = cur.fetchone()
        conn.commit()
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
        mdate = gen_info[0].split('-')
        conn = sqlite3.connect('db/lam1.db')
        cur = conn.cursor()
        cur.execute(f"SELECT zmina_id, nomer_zm, general_name FROM zmina INNER JOIN maister ON zmina.maister_id=maister.maister_id WHERE zm_date='{gen_info[0]}' AND zm_zmina='{gen_info[1]}'")
        zm_id = cur.fetchone()
        if not zm_id:
            cur.execute(f"INSERT INTO zmina (zm_date,zm_zmina,nomer_zm,maister_id) VALUES ('{gen_info[0]}', '{gen_info[1]}', '{gen_info[3]}', '1')")
            cur.execute(f"SELECT zmina_id, nomer_zm, general_name FROM zmina INNER JOIN maister ON zmina.maister_id=maister.maister_id WHERE zm_date='{gen_info[0]}' AND zm_zmina='{gen_info[1]}'")
            zm_id = cur.fetchone()
        start_date = "{}-{}-{}".format(mdate[0], mdate[1], '01')
        end_date = (date.fromisoformat(gen_info[0]) - timedelta(days=1)).isoformat()
        mon = ('01','02','03','04','05','06','07','08','09','10','11','12')[int(mdate[1])-2]   #previous month
        cur.execute("SELECT MAX(textures_id) FROM textures")
        
        texlist = []
        cur.execute(f"""SELECT textures_id 
                    FROM month_rem
                    WHERE month='{mdate[1]}' AND year='{mdate[0]}' AND thickness='{thick}' AND e_quality='{eq}'""")
        texlist += [i[0] for i in cur.fetchall()]
        cur.execute(f"""SELECT DISTINCT textures_id
                    FROM remainders 
                    INNER JOIN zmina USING(zmina_id)
                    WHERE zm_date between '{start_date}' AND '{date.today().isoformat()}' AND thickness='{thick}' AND e_quality='{eq}' """)
        texlist += [i[0] for i in cur.fetchall()]
        cur.execute(f"""SELECT DISTINCT textures_id
                    FROM robota_zm 
                    INNER JOIN zmina USING(zmina_id)
                    WHERE zm_date between '{start_date}' AND '{date.today().isoformat()}' AND thickness='{thick}' AND e_quality='{eq}' """)
        texlist += [i[0] for i in cur.fetchall()]
        texlist = list(set(texlist))
        print(texlist)

        for tid in texlist:
            #print(i)
            # starting remainders
            #cur.execute(f"SELECT textures_id FROM textures WHERE name='Акація'")
            #tid = cur.fetchone()[0]
            #tid = 1
            try:
                curtex = cur.execute(f"SELECT name FROM textures WHERE textures_id='{tid}'").fetchone()[0]
            except:
                print("EXCEPT  ", tid)
                continue
            prevday_rem = (tid, 0, 0, 0, 0)
            # якщо це перший день місяця то просто дати залишки на початок місяця 
            if mdate[2] != '01':
                # залишки від початку місяця на початок дня
                cur.execute(sql_command_month_rem.format(tid, thick, eq, start_date, end_date, mdate[1], mdate[0]))
                prevday_rem = cur.fetchone() 
            else:
                prevday_rem = cur.execute(f"""SELECT textures_id,sort1,sort2,sort3,sort4 FROM month_rem WHERE month='{mdate[1]}' AND 
                    year='{mdate[0]}' AND textures_id='{tid}' AND thickness='{thick}' AND e_quality='{eq}'""").fetchone()
            if prevday_rem:
                curval = list(prevday_rem[1:])
            else:
                curval = [0,0,0,0]
            # якщо нічна зміна то додати ще рух/залишки в денній зміні
            if gen_info[1] == '2':
                cur.execute(f"SELECT zmina_id, nomer_zm, general_name FROM zmina INNER JOIN maister ON zmina.maister_id=maister.maister_id WHERE zm_date='{gen_info[0]}' AND zm_zmina='1'")
                zm_id1 = cur.fetchone()
                if zm_id1:
                    cur.execute(sql_command_remone_get.format(zm_id1[0], thick, eq, tid))
                    zm1 = cur.fetchone()
                else:
                    zm1 = [0]*16        # якщо не було денної зміни
                print("ZM --- ",zm1)
                print("-- ", curval)
                for n in range(4):
                    curval[n] = curval[n] + zm1[n] - zm1[n+4] + zm1[n+8] - zm1[n+12]
            n = getridofnone(curval, 0)
            cur.execute(sql_command_rem_get.format(zm_id[0], thick, eq, tid))
            curzmina = cur.fetchone()
            if curzmina:
                n = list(curzmina[1:]) + n
            else:
                n = [zm_id[0], thick, eq] + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] + n
            n = ['' if x==None or x==0.0 else int(x) for x in n]
            n.insert(0, curtex)
            print(n)
            if any(n[4:]):
                t_lists.append(tuple(n))
        gen_info[2], gen_info[3] = zm_id[2], zm_id[1]    
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
        mon = ('01','02','03','04','05','06','07','08','09','10','11','12')[int(m[1])-2]   #previous month
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
@app.route("/addtexturesfromfile", methods=["POST"])
@app.route("/addnewtexture", methods=["POST"])
@app.route("/addremaindersfromfile", methods=["POST"])
@app.route("/addremainder", methods=["POST"])
def add_texture():
    if request.method == 'POST':
        rule = request.url_rule
        if rule.rule == "/addremaindersfromfile":
            data = request.form.getlist("newrem")
            chk = checklist(data, ['month','year','thick','eq','txtfile'])
            print(data)
            if not chk[0]:
                message = "Wrong input " + chk[1]
                return render_template("addtexture.html", texture_list=texture_list, message=message)
            message = ""
            try:
                con = sqlite3.connect('db/lam1.db')
                cur = con.cursor()
                txt_filename = 'loadtxt/' + data[-1]
                with open(txt_filename,'r',encoding='utf-8') as f:  
                    text = f.read().split('\n')
                    t = []
                    for i in text[:-1]:
                        i = i.split('\t')
                        c = cur.execute(f"SELECT textures_id FROM textures WHERE name='{i[0].strip()}'").fetchone()
                        if c:
                            t.append([c[0]] + i[1:])
                        else:
                            message += f"текстури '{i[0]}' немає в базі даних"
                for i in t[0:4]:
                    try:
                        cur.execute(f"""INSERT INTO month_rem (month,year,textures_id,thickness,e_quality,sort1,sort2,sort3,sort4)
                            VALUES('{data[0]}','{data[1]}','{i[0]}','{data[2]}','{data[3]}','{i[1]}','{i[2]}','{i[3]}','{i[4]}')""")
                    except sqlite3.IntegrityError:
                        print("неправильні дані в файлі")
                con.commit()
            finally:
                con.close()
            message += ' ---> Complete'
            return render_template("addtexture.html", texture_list=texture_list, message=message)
        if rule.rule == "/addremainder":
            data = request.form.getlist("newrem")
            print(data)
            chk = checklist(data, ['month','year','texturename','thick','eq','s1','s2','s3','s4'])
            if not chk[0]:
                message = "Wrong input " + chk[1]
                return render_template("addtexture.html", texture_list=texture_list, message=message)
            message = ""
            try:
                con = sqlite3.connect('db/lam1.db')
                cur = con.cursor()
                c = cur.execute(f"SELECT textures_id FROM textures WHERE name='{data[2].strip()}'").fetchone()
                if c:
                    try:
                        cur.execute(f"""INSERT INTO month_rem (month,year,textures_id,thickness,e_quality,sort1,sort2,sort3,sort4)
                        VALUES('{data[0]}','{data[1]}','{c[0]}','{data[3]}','{data[4]}','{data[5]}','{data[6]}','{data[7]}','{data[8]}')""")
                    except sqlite3.IntegrityError:
                        print("запис з такими текстурою, місяцем, роком, товщиною і якістю вже є")
                    con.commit()
                else:
                    message += f"текстури '{data[2]}' немає в базі даних"
            finally:
                con.close()
            message += ' ---> Complete'
            return render_template("addtexture.html", texture_list=texture_list, message=message)
        if rule.rule == "/addnewtexture":
            new_t = request.form.getlist("newtex")
            chk = checklist(new_t, ['code','texturename'])
            if not chk[0]:
                message = "Wrong input " + chk[1]
                return render_template("addtexture.html", texture_list=texture_list, message=message)
            message = ""
            try:
                con = sqlite3.connect('db/lam1.db')
                cur = con.cursor()
                try:
                    cur.execute(f"INSERT INTO textures (name, code) VALUES('{new_t[1]}','{new_t[0]}')")
                    message += f' Текстура додана --- {new_t[1]}  {new_t[0]}'
                except sqlite3.IntegrityError:
                    print(' така текстура вже є')
                    message += f'така текстура вже є --- {new_t[1]} '
                con.commit()
            finally:
                con.close()
            return render_template("addtexture.html", texture_list=texture_list, message=message)
        if rule.rule == "/addtexturesfromfile":
            new_t = request.form.getlist("newtex")
            chk = checklist(new_t, ['txtfile'])
            if not chk[0]:
                message = "Wrong input " + chk[1]
                return render_template("addtexture.html", texture_list=texture_list, message=message)
            message = ""
            t = []
            with open('loadtxt/' + new_t[0], 'r', encoding='UTF-8') as f:
                text = f.read().split('\n')[:-1]
                for i in text:
                    t.append(i.split('\t'))
            try:
                con = sqlite3.connect('db/lam1.db')
                cur = con.cursor()
                print(t)
                for i in t:
                    try:
                        cur.execute(f"INSERT INTO textures (name, code) VALUES('{i[0]}','{i[1]}')")
                        message += f' Текстура додана --- {i[0]}  {i[1]}' + '\n'
                    except sqlite3.IntegrityError:
                        print(' така текстура вже є')
                        message += f'така текстура вже є --- {i[0]}' + '\n'
                con.commit()
            finally:
                con.close()
            return render_template("addtexture.html", texture_list=texture_list, message=message)
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
