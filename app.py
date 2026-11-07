import json
import datetime
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash, Response
import os
import smtplib
from email.message import EmailMessage

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

sugar_levels = ['Standard Sugar (100%)', 'Half Sugar (50%)', 'Less Sugar (30%)', 'No Sugar']

ice_levels = ['Full Ice (100%)', ' Half Ice (50%)', 'Less Ice (25%)','No Ice']

MAIL_USER = "nomolicious.co@gmail.com"
MAIL_PASSWORD = "pqtbpsssimewklab"


# ——— LOADING DATA ——— #
def initialise_database():
    """Create the orders table if it does not exist yet."""
    with sqlite3.connect('drink_shop.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT,
            customer_name TEXT,
            customer_email TEXT,
            address TEXT,
            payment_method TEXT,
            items TEXT,
            total REAL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        conn.commit()

initialise_database()




def load_data():
    """Load the three drink menus and the add-ons from the data JSON file."""
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
    """Check the chosen drink options, then add the drink to the cart."""
    
    drink = request.form['drink']
    size = request.form['size']
    sugar = request.form.get('sugar')
    chosen_addons = request.form.getlist('addons')
    quantity = int(request.form['quantity'])
    ice = request.form.get('ice')

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

    if ice not in ice_levels:
        flash("Please choose a ice levels,", "error")
        return redirect(url_for('menu'))
        

    drinks_price = None
    for option in drinks[drink]['size_prices']:
        if option['size'] == size:
            drinks_price = float(option['price'])
            break

    if drinks_price is None:
        flash("That size isn't available.", "error")
        return redirect(url_for('menu'))

    addons_price = 0
    for name in chosen_addons:
        if name not in available_addons:
            flash("Unknown add-on.", "error")
            return redirect(url_for('menu'))
        addons_price += float(available_addons[name]['price'])

    if len(chosen_addons) > 3:
        flash(f"You can choose up to 3 add-ons per drink.", "error")
        return redirect(url_for('menu'))        

    price = drinks_price + addons_price

    cart = session.get('cart', {})

    '''DRINK BOUNDARIES/RESTRAINTS '''
    available_stock = drinks[drink]['stock']
    original_quantity = sum(item['quantity'] for item in cart.values()
                            if item['name'] == drink)

    if available_stock <= 0:
        flash(f"Sorry {drink} is out of stock.", "error")
        return redirect(url_for('menu'))

    if original_quantity + quantity > available_stock:
        flash(f"Sorry, only {available_stock} {drink}(s) left in stock.", "error")
        return redirect(url_for('menu'))

    if quantity >= 10:
        flash("You are ordering a lot! Consider calling us for a special deal.", "error")
        return redirect(url_for('menu'))

    key = '|'.join([drink, size, sugar, ice] + sorted(chosen_addons))

    if key in cart:
        cart[key]['quantity'] += quantity
    else:
        cart[key] = {
            'name': drink,
            'image': drinks[drink]['image'],
            'size': size,
            'sugar': sugar,
            'ice': ice,
            'addons': chosen_addons,
            'drinks_price': drinks_price,
            'addons_price': addons_price,
            'price': price,
            'quantity': quantity
        }

    session['cart'] = cart
    flash(f"{quantity} x {drink} added to cart.")
    return redirect(url_for('menu'))

 # ——— debug some of my code from google ai, because mine are very complex and not easy to fix ——— #

@app.route("/remove_from_cart/<drink>")
def remove_from_cart(drink):
    """Remove one item from the cart using the bag popup."""
    cart = session.get('cart', {})

    if drink in cart:
        del cart[drink]
        session['cart'] = cart
        flash(f"Removed {drink} from the cart.", "error")
    else:
        flash("drink not found in cart")

    return redirect(url_for('menu'))


@app.route("/checkout", methods=['POST'])
def invoice():
    """Check the checkout form, then save the order in the database."""
    customer_name = request.form['customer_name'].strip().title()
    customer_email = request.form['customer_email'].strip()
    address = request.form['address'].strip()
    payment_method = request.form['payment']

    cart = session.get('cart', {})

    if not cart:
        flash("Select drink to continue.", "error")
        return redirect(url_for('order'))

    if customer_name == "":
        flash("Customer name is required.", "error")
        return redirect(url_for('order'))

    if payment_method == 'card':
        card_number = request.form['card_number'].replace(' ', '')
        if len(card_number) != 16 or not card_number.isdigit():
            flash("Please enter a valid 16-digit card number.", "error")
            return redirect(url_for('order'))

    total, drinks_subtotal, addon_subtotal, discount_applied, subtotal, discount_amount = calculate_total(cart)

    invoice_date = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    invoice_number = f"INV_{customer_name.replace(' ', '_')}_{invoice_date}"

    with sqlite3.connect('drink_shop.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO orders (invoice_number, customer_name, customer_email, address, payment_method, items, total)
        VALUES (?,?,?,?,?,?,?)
        ''', (invoice_number, customer_name, customer_email, address, payment_method, json.dumps(cart), total))
        conn.commit()

    session.pop('cart', None)
    session['order_placed'] = {'name': customer_name, 'invoice': invoice_number}
    return redirect(url_for('order'))



@app.context_processor # ——— use to show the item in a cart to all html templates ——— #
def inject_cart():
    """Make the cart seen/available in every template"""
    cart = session.get('cart', {})
    total, drinks_subtotal, addon_subtotal, discount_applied, subtotal, discount_amount = calculate_total(cart)
    return {'cart': cart, 'total': total, 'drinks_subtotal': drinks_subtotal,
            'addon_subtotal': addon_subtotal, 'discount_applied': discount_applied,
            'subtotal': subtotal, 'discount_amount': discount_amount}

# ——— FUNCTION ——— #

def calculate_total(cart):
    """Work out the cart totals and apply the discount."""
    drinks_subtotal = sum(item.get('drinks_price', item['price']) * item['quantity'] for item in cart.values())
    addon_subtotal = sum(item.get('addons_price', 0) * item['quantity'] for item in cart.values())

    subtotal = drinks_subtotal + addon_subtotal

    drinks_subtotal = sum(item.get('drinks_price', item['price']) * item['quantity'] for item in cart.values())

    discount_applied = False
    discount_amount = 0
    total = subtotal

    if subtotal > 90:
        discount_amount = subtotal * 0.1
        total = subtotal - discount_amount
        discount_applied = True

    return total, drinks_subtotal, addon_subtotal, discount_applied, subtotal, discount_amount


    # ——— FUNCTION CANCEL ORDER ——— #
@app.route('/cancel_order', methods=['POST'])
def cancel_order():
    """Empty the whole cart when the customer cancels their order."""
    session.pop('cart', None)
    session.pop('selected_addons', None)
    flash("Your order has been cancelled.", "error")

    return redirect(url_for('order'))

@app.route('/update_quantity', methods=['POST'])
def update_quantity():
    """Increase or decrease the quantity of one item on the order page."""
    key = request.form['key']
    action = request.form['action']
    cart = session.get('cart', {})

    if action == 'increase':
        if cart[key]['quantity'] >= 9:
            flash("Maximum 9 per item. Call us for a special deal.", "error")
        else:
            cart[key]['quantity'] += 1

    elif action == 'decrease':
        cart[key]['quantity'] -= 1
        if cart[key]['quantity'] == 0:
            del cart[key]

    session['cart'] = cart
    return redirect(url_for('order'))

@app.route('/remove_item', methods=['POST'])
def remove_item():
    """Remove one item using the Remove button on the order page."""
    key = request.form['key']
    cart = session.get('cart', {})

    if key in cart:
        del cart[key]
        session['cart'] = cart
        flash(f"Removed {key} from the cart.", "error")

    return redirect(url_for('order'))

# ——— ROUTE ——— #

@app.route("/")
def index():
    """Show the home page."""
    lattes, milk_teas, fruit_teas, addons = load_data()
    return render_template("index.html", lattes=lattes, milk_teas=milk_teas, fruit_teas=fruit_teas, addons=addons)

@app.route("/menu")
def menu(): 
    """Show the drink menu page."""
    lattes, milk_teas, fruit_teas, addons = load_data()


    
    return render_template("menu.html", lattes=lattes, milk_teas=milk_teas, fruit_teas=fruit_teas, addons=addons, sugar_levels=sugar_levels, ice_levels=ice_levels)

@app.route("/order")
def order():
    """Show the order page, and the success message after checkout."""
    order_placed = session.pop('order_placed', None)
    return render_template("order.html", order_placed=order_placed)


@app.route('/order_history')
def order_history():
    """Show every saved order. Above newest, Below oldest"""
    with sqlite3.connect('drink_shop.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT order_id, invoice_number, customer_name, customer_email, address, payment_method, items, total, date FROM orders ORDER BY date DESC")
        rows = cursor.fetchall()

    orders = []
    for row in rows:
        orders.append({
            'order_id': row[0],
            'invoice_number': row[1],
            'customer_name': row[2],
            'customer_email': row[3],
            'address': row[4],
            'payment_method': row[5],
            'items': json.loads(row[6]),
            'total': row[7],
            'date': row[8]
        })
    return render_template('order_history.html', orders=orders)

@app.route("/invoice/<invoice_number>/download")
def download_invoice(invoice_number):
    """Send the invoice for one saved order as a text file download."""
    # get the order from the database
    with sqlite3.connect('drink_shop.db') as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT invoice_number, customer_name, items, total, date FROM orders WHERE invoice_number = ?",
            (invoice_number,)
        )
        row = cursor.fetchone()

    if row is None:
        flash("Invoice not found.", "error")
        return redirect(url_for('order_history'))

    items = json.loads(row[2])
    total = row[3]

    # write the invoice text
    text = "---- Nomolicious Invoice ----\n\n"
    text += f"Invoice Number: {row[0]}\n"
    text += f"Customer Name: {row[1]}\n"
    text += f"Date: {row[4]}\n\n"
    text += "Items:\n"

    subtotal = 0
    for key, item in items.items():
        line_total = item['quantity'] * item['price']
        subtotal += line_total
        text += f"-{item['name']} ({item['size']}, {item['sugar']}, {item['ice']}): {item['quantity']} x ${item['price']:.2f} = ${line_total:.2f}\n"
        if item['addons']:
            text += f"   Add-ons: {', '.join(item['addons'])}\n"

    discount = subtotal - total
    text += "\n"
    if discount > 0.01:
        text += f"Subtotal: ${subtotal:.2f}\n"
        text += f"Discount (10%): -${discount:.2f}\n"
    text += f"Total: ${total:.2f}"

    #  send it as a download, response are required to dl it
    return Response(
        text,
        mimetype="text/plain",
        headers={"Content-Disposition": f"attachment; filename={row[0]}.txt"}
    )

@app.route('/cancel_saved_order/<int:order_id>', methods=['POST'])
def cancel_saved_order(order_id):
    """Delete one saved order from the database."""
    with sqlite3.connect('drink_shop.db') as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM orders WHERE order_id = ?", (order_id,))
        conn.commit()
    flash("Order cancelled.", "error")
    return redirect(url_for('order_history'))

# @app.route("/contact")
# def contact():
#     return render_template("contact.html")

@app.route("/contact", methods=["GET", "POST"])
def contact():
    """Show the contact page, and email the message when it is sent."""
    success = False
    name = ""
    if request.method == "POST":
        name = request.form["firstname"]
        lastname = request.form["lastname"]
        email = request.form["email"]
        subject = request.form["subject"]
        feedback = request.form["feedback"]

        # email to the shop 
        msg = EmailMessage()
        msg["Subject"] = f"Nomolicious contact: {subject}"
        msg["From"] = MAIL_USER
        msg["To"] = MAIL_USER
        msg["Reply-To"] = email
        msg.set_content(
            f"Name: {name} {lastname}\n"
            f"Email: {email}\n\n"
            f"{feedback}"
        )

        # auto-reply to the customer
        reply = EmailMessage()
        reply["Subject"] = "We got your message - Nomolicious"
        reply["From"] = MAIL_USER
        reply["To"] = email
        reply.set_content(
            f"Hi {name},\n\n"
            "Thanks for contacting Nomolicious! We've received your message "
            "and will get back to you soon.\n\n"
            f"Your subject:\n{subject}\n\n"
            f"Your message:\n{feedback}\n\n"
            "- The Nomolicious Team"
        )
        
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(MAIL_USER, MAIL_PASSWORD)
            server.send_message(msg)
            server.send_message(reply)

        success = True
    return render_template("contact.html", success=success, name=name)

if __name__ == '__main__':
    app.run(debug=True)

