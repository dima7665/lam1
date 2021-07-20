from flask import Blueprint, render_template, request
from .tools import texture_list, checklist, info
import sqlite3

support = Blueprint('support', __name__)

@support.route("/addtexture", methods=["POST","GET"])
@support.route("/addtexturesfromfile", methods=["POST"])
@support.route("/addnewtexture", methods=["POST"])
@support.route("/addremaindersfromfile", methods=["POST"])
@support.route("/addremainder", methods=["POST"])
def add_texture():
    print("GENINFO",  info.gen_info)
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
            return render_template("addtexture.html", texture_list=texture_list, message=message, gen_info=info.gen_info)
    if request.method == 'GET':
        return render_template("addtexture.html", texture_list=texture_list, gen_info=info.gen_info)