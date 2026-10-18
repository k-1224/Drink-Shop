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
        with open('data/addons.json') as file:
            addons = json.load(file)
        return lattes, milk_teas, fruit_teas, addons

# ——— FUNCTION CART ——— #

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    drink = request.form['drink']
    size = request.form['size']
    quantity = int(request.form['quantity'])

    lattes, milk_teas, fruit_teas, addons = load_data()
    drinks = {**lattes, **milk_teas, **fruit_teas}  #the 2 asterisk beside variables are to unpack three dictionaries into one#

    price = None
    for option in drinks[drink]['size_prices']:
        if option['size'] == size:
            price = float(option['price'])
            break 

    if price is None:
        flash("That size isn't available.", "error")
        return redirect(url_for('menu'))

    cart = session.get('cart', {})
    key = f"{drink}|{size}"  

    if key in cart:
        cart[key]['quantity'] += quantity
    else:
        cart[key] = {
            'name': drink,
            'size': size,
            'price': price,
            'quantity': quantity
        }

    session['cart'] = cart
    flash(f"{quantity} x {size} {drink} added to cart.")
    return redirect(url_for('menu'))

 #debug my code from google ai, because mine are very complex#

@app.route("/remove_from_cart/<drink>")
def remove_from_cart(drink):
    cart = session.get('cart', {})

    if drink in cart:
        del cart[drink]
        session['cart'] = cart
        flash(f"Removed {drink} from the cart.", "error")
    else:
        flash("Item not found in cart")

    return redirect(url_for('menu'))

# ——— ROUTE ——— #

@app.route("/")
def index():
    milk_teas = load_data()
    return render_template("index.html", milk_teas=milk_teas)

@app.route("/menu")
def menu(): 
    lattes, milk_teas, fruit_teas, addons = load_data()
    cart = session.get('cart', {})
    
    return render_template("menu.html", lattes=lattes, milk_teas=milk_teas, fruit_teas=fruit_teas, addons=addons, cart=cart)


@app.route("/order_history")
def order_history():
    return render_template("order_history.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

if __name__ == '__main__':
    app.run(debug=True)

