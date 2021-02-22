from flask import Flask, render_template, request, redirect, url_for
import json
from textures import get_textures_list
from datetime import date

app = Flask(__name__)

texture_list = get_textures_list()
rob_zm = ['22','','asd']
gen_info = ['2021-02-10','2','']

@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html', title='Ламінування', rob_zm=rob_zm)


@app.route("/home2", methods=["POST","GET"])
def home2():
    if request.method == "POST":
        t1 = request.form.getlist("t1")
        #print(request.form.getlist("texture"))
        with open('some.txt', 'a') as f:
            f.write(str(len(t1)) + "\n")
            for i in t1:
                f.write(i + '\n')
    global gen_info
    if request.method == "GET":
        tinfo = request.args.getlist("top_info")
        if tinfo:
            gen_info = tinfo
        else: 
            gen_info = [date.today().isoformat(), '1','']   #додати ім'я майстра {3}
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
