from flask import Blueprint, render_template, request
from .tools import update_command, column_names, texture_list, maister_list
from textures import sql_command_month_rem
import sqlite3

monfin = Blueprint('monfin', __name__)

@monfin.route("/mf", methods=["POST", "GET"])
def monthfinisher():
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
