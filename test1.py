from flask import Flask, render_template, request
import json

app = Flask(__name__)

rob_zm = ['22','','asd']

@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html', title='Ламінування', rob_zm=rob_zm)


@app.route("/home2")
def home2():
    return render_template('home2.html', title='Ламінування', rob_zm=rob_zm)

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
