from flask import Blueprint, render_template, request, url_for
import json
from .tools import get_pressE, update_command, column_names, texture_list, maister_list, info
from .textures import prev_day
from datetime import date, timedelta
import sqlite3

work = Blueprint('work', __name__)

@work.route('/home', methods=["POST","GET"])
@work.route('/home16', methods=["POST","GET"])
@work.route('/home18', methods=["POST","GET"])
def home():
    if request.method == "POST":
        t_lists = []
        thick = request.form.get('thickness')
        cur_textures = request.form.getlist("texture")
        zinfo = request.form.getlist("zm_info")
        try:
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
        finally:
            conn.close()
        return render_template('work.html', title='Ламінування', gen_info=info.gen_info, maister_list=maister_list, sklad = [0,0,0,0], texture_list=texture_list)
   
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
            info.gen_info = tinfo
        gen_info = info.gen_info
        print('GETTT', gen_info)
        try:
            conn = sqlite3.connect('db/lam1.db')
            cur = conn.cursor()
            cur.execute(f"""SELECT zmina_id, nomer_zm, general_name FROM zmina INNER JOIN maister ON zmina.maister_id=maister.maister_id 
                WHERE zm_date='{gen_info[0]}' AND zm_zmina='{gen_info[1]}'""")
            zm_id = cur.fetchone()
            if not zm_id:
                cur.execute(f"SELECT maister_id FROM maister WHERE general_name='{gen_info[2]}'")
                cur.execute(f"INSERT INTO zmina (zm_date,zm_zmina,nomer_zm,maister_id) VALUES ('{gen_info[0]}', '{gen_info[1]}', '{gen_info[3]}', '{cur.fetchone()[0]}')")
                cur.execute(f"SELECT zmina_id, nomer_zm, general_name FROM zmina INNER JOIN maister ON zmina.maister_id=maister.maister_id WHERE zm_date='{gen_info[0]}' AND zm_zmina='{gen_info[1]}'")
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
        return render_template('work.html', title="LAMIN", koef=koef, thick=thick, gen_info=gen_info, load_get=load_get[:5], sklad=sklad, maister_list=maister_list, texture_list=texture_list, t_lists=json.dumps(t_lists))
