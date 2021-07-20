from flask import Blueprint, render_template, request, url_for
import json
from .tools import update_command, column_names, texture_list, maister_list, info, make_texture_lists_for_remainders, getridofnone
from textures import sql_command_month_rem, sql_command_rem_get, sql_command_remone_get
from .textures import prev_day
from datetime import date
import sqlite3

remain = Blueprint('remain', __name__)

@remain.route("/remain", methods=["POST","GET"])
@remain.route("/remain16e1", methods=["POST","GET"])
@remain.route("/remain16e2", methods=["POST","GET"])
@remain.route("/remain18e1", methods=["POST","GET"])
@remain.route("/remain18e2", methods=["POST","GET"])
def remainders():
    if request.method == 'POST':
        t_list = []
        thick, eq = request.form.get("thickness"), request.form.get("e_quality")
        if int(thick) == 16:
            koef = 0.08052
        else:
            koef = 0.090585
        zinfo = request.form.getlist('zm_info')
        cur_textures = request.form.getlist("tvalues")
        cur_textures, values_list = make_texture_lists_for_remainders(cur_textures)
        try:
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
                print("NOVA ZMINA")
                cur.execute(f"INSERT INTO zmina (zm_date,zm_zmina,nomer_zm,maister_id) VALUES ('{zinfo[0]}', '{zinfo[1]}', '{nomer_zm}', '{maister_id}')")
                cur.execute(f"SELECT zmina_id FROM zmina WHERE zm_date='{zinfo[0]}' AND zm_zmina='{zinfo[1]}'")
                zm_id = cur.fetchone()
            conn.commit()
            for t in values_list:
                cur.execute(f"SELECT textures_id FROM textures WHERE name='{t[0]}'")
                texture_id = cur.fetchone()[0]
                t_list.append([zm_id[0], texture_id, thick, eq] + t[1:])
            
            remainders_names = column_names['remainders']
            for i in t_list:
                try:
                    cur.execute(f"INSERT INTO remainders {remainders_names[1:]} VALUES {tuple(i)}")
                    print("insert--- ", i)
                except sqlite3.IntegrityError:
                    command = update_command('remainders', remainders_names, i)
                    cur.execute(command)
                    print("update--- ", i)
            conn.commit()
            result = 'Finished succesfully'
        except:
            print("POST EXCEPTION REMAINDERS")
            result = 'Error'
        finally:
            conn.close()
        return result
       # return render_template('remain.html', title='Рух плити', gen_info=info.gen_info, koef=koef, thick=thick, maister_list=maister_list, texture_list=texture_list)

    if request.method == 'GET':
        t_lists = []
        rule = request.url_rule
        if rule.rule[-1] == '1':
            eq = '1'
        else:
            eq = '2'
        if rule.rule[-4:-2] == '16':
            koef, thick = 0.08052, '16'
        else:
            koef, thick = 0.090585, '18'
        tinfo = request.args.getlist("top_info")
        if tinfo:
            if len(tinfo)<4:
                tinfo += [''] * (4 - len(tinfo))
            info.gen_info = tinfo
        print("INFO--  ", info.gen_info)
        gen_info = info.gen_info
        mdate = gen_info[0].split('-')
        try:
            conn = sqlite3.connect('db/lam1.db')
            cur = conn.cursor()
            cur.execute(f"SELECT zmina_id, nomer_zm, general_name FROM zmina INNER JOIN maister ON zmina.maister_id=maister.maister_id WHERE zm_date='{gen_info[0]}' AND zm_zmina='{gen_info[1]}'")
            zm_id = cur.fetchone()
            if not zm_id:
                cur.execute(f"SELECT maister_id FROM maister WHERE general_name='{gen_info[2]}'")
                cur.execute(f"INSERT INTO zmina (zm_date,zm_zmina,nomer_zm,maister_id) VALUES ('{gen_info[0]}', '{gen_info[1]}', '{gen_info[3]}', '{cur.fetchone()[0]}')")
                cur.execute(f"SELECT zmina_id, nomer_zm, general_name FROM zmina INNER JOIN maister ON zmina.maister_id=maister.maister_id WHERE zm_date='{gen_info[0]}' AND zm_zmina='{gen_info[1]}'")
                zm_id = cur.fetchone()
            start_date = "{}-{}-{}".format(mdate[0], mdate[1], '01')
            end_date = prev_day(gen_info[0])
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
            title = 'Рух плити ' + thick + ' E' + ('05' if eq=='2' else '1')
        finally:  
            conn.close()
        return render_template('remain.html', title=title, koef=koef, thick=thick, eq=eq, gen_info=info.gen_info, maister_list=maister_list, texture_list=texture_list, t_lists=t_lists)
