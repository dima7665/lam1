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