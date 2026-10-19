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

# ——— GLOBAL VARIABLES ——— #

sugar_levels = ['100% (Standard)', '50%', '30%', 'No sugar']


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
    sugar = request.form.get('sugar')
    chosen_addons = request.form.getlist('addons')
    quantity = int(request.form['quantity'])

    lattes, milk_teas, fruit_teas, addons = load_data()
    drinks = {**lattes, **milk_teas, **fruit_teas} #the 2 asterisk beside variables are to unpack three dictionaries into one#

    if drink not in drinks:
        flash("Drink not found.", "error")
        return redirect(url_for('menu'))

    if drink in lattes:
        available_addons = addons['latte']
    elif drink in milk_teas:
        available_addons = addons['milk_tea']
    else:
        available_addons = addons['fruit_tea']


    if sugar not in sugar_levels:
        flash("Please choose a sugar level.", "error")
        return redirect(url_for('menu'))

    price = None
    for option in drinks[drink]['size_prices']:
        if option['size'] == size:
            price = float(option['price'])
            break

    if price is None:
        flash("That size isn't available.", "error")
        return redirect(url_for('menu'))

    for name in chosen_addons:
        if name not in available_addons:
            flash("Unknown add-on.", "error")
            return redirect(url_for('menu'))
        price += float(available_addons[name]['price'])

    cart = session.get('cart', {})
    # ——— everything that makes two items different goes in the key ——— #
    key = '|'.join([drink, size, sugar] + sorted(chosen_addons))

    if key in cart:
        cart[key]['quantity'] += quantity
    else:
        cart[key] = {
            'name': drink,
            'size': size,
            'sugar': sugar,
            'addons': chosen_addons,
            'price': price,          # ——— price of one drink, add-ons included ——— #
            'quantity': quantity
        }

    session['cart'] = cart
    flash(f"{quantity} x {drink} added to cart.")
    return redirect(url_for('menu'))

 # ——— debug some my code from google ai, because mine are very complex and not easy to fix ——— #

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

@app.context_processor # ——— use to show the item in a cart to all html templates ——— #
def inject_cart():
    return {'cart': session.get('cart', {})}

# ——— ROUTE ——— #

@app.route("/")
def index():
    lattes, milk_teas, fruit_teas, addons = load_data()
    return render_template("index.html", lattes=lattes, milk_teas=milk_teas, fruit_teas=fruit_teas, addons=addons)

@app.route("/menu")
def menu(): 
    lattes, milk_teas, fruit_teas, addons = load_data()


    
    return render_template("menu.html", lattes=lattes, milk_teas=milk_teas, fruit_teas=fruit_teas, addons=addons, sugar_levels=sugar_levels)


@app.route("/order")
def order():
    return render_template("order.html")

@app.route("/order_history")
def order_history():
    return render_template("order_history.html")
    

@app.route("/contact")
def contact():
    return render_template("contact.html")

if __name__ == '__main__':
    app.run(debug=True)

