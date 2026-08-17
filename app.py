from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'drink143'

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/menu")
def menu():
    return render_template("menu.html")

@app.route("/order_history")
def order_history():
    return render_template("order_history.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

if __name__ == '__main__':
    app.run(debug=True)

