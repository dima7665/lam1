from flask import Flask, render_template, request
import json
from textures import get_textures_list

app = Flask(__name__)

texture_list = get_textures_list()
rob_zm = ['22','','asd']

@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html', title='Ламінування', rob_zm=rob_zm)


@app.route("/home2", methods=["POST","GET"])
def home2():
    if request.method == "POST":
        t1 = request.form.getlist("t1")
        print(request.form.getlist("texture"))
        with open('some.txt', 'a') as f:
            f.write(str(len(t1)) + "\n")
            for i in t1:
                f.write(i + '\n')

    if request.method == "GET":
        print('GETTT')

    return render_template('home2.html', title='Ламінування', texture_list=texture_list)

@app.route("/robota")
def robota():
    return render_template('robota.html', title='Робота зміни')


@app.route("/test", methods=["POST"])
def test():
    n = request.form.getlist("f1")
    m = request.form.get("f2text")
    return render_template("test.html", n=n,m=m)



@app.route("/about")
def about():
    return render_template('about.html', title='Інструкція')


if __name__ == '__main__':
    app.run(debug=True)
