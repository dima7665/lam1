from textures import get_textures_list, get_maister_list, get_column_names
from datetime import date

class Geninfo():
    def __init__(self, gen_info):
        self.gen_info = gen_info

default_date = date.today().isoformat()
texture_list = get_textures_list()
maister_list = get_maister_list()
info = Geninfo([default_date, '2', maister_list[0], '1'])

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

#######
chk_dict = {
    'month': ['01','02','03','04','05','06','07','08','09','10','11','12'],
    'thick': ['16','18'],
    'eq': ['1','2']
}

def checklist (lst, names):
    c = True
    err = ''
    for name in names:
        if name in chk_dict:
            if not lst[names.index(name)] in chk_dict[name]:
                c = False
                err += ' - ' + name + ' is incorrect - '
        else:
            if name == 'year' or name == 'code':
                if not lst[names.index(name)].isnumeric():
                    c = False
            if name == 'txtfile':
                pass
            if name == 'name':
                pass
    return [c, err]
###############