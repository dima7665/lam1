from flask import Flask, render_template

app = Flask(__name__)

rob_zm = [
    {'t1_s1':'Akacia'},
    {'t1':(12,32)}
]

@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html', title='Ламінування', rob_zm=rob_zm)

@app.route("/robota")
def robota():
    return render_template('robota.html', title='Робота зміни')



@app.route("/about")
def about():
    return render_template('about.html', title='Інструкція')


if __name__ == '__main__':
    app.run(debug=True)
