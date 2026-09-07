import json
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'drink143'

# safe
# capitalize
# lower
# upper 
# title 
# trim
# striptags

# ——— LOADING DATA ——— #
def load_data():
        with open('data/latte.json') as file:
            lattes = json.load(file)
        with open('data/milktea.json') as file:
            milk_teas = json.load(file)
        with open('data/fruittea.json') as file:
            fruit_teas = json.load(file)
        return lattes, milk_teas, fruit_teas

@app.route("/")
def index():
    milk_teas = load_data()
    return render_template("index.html", milk_teas=milk_teas)

@app.route("/menu")
def menu(): 
    lattes, milk_teas, fruit_teas = load_data()
    
    return render_template("menu.html", lattes=lattes, milk_teas=milk_teas, fruit_teas=fruit_teas)

@app.route("/order_history")
def order_history():
    return render_template("order_history.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

if __name__ == '__main__':
    app.run(debug=True)

