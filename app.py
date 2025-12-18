import os
import sqlite3

from datetime import datetime
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from flask import g
from msgspec import field
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_requered, password_check 

# Configure application
app = Flask(__name__)

# Configure session to filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Configure database
DATABASE = "database.db"

def get_db():
    """
    Database configuration to store and retrieve information.

    https://flask.palletsprojects.com/en/stable/tutorial/database/
    """
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_conection(exception):
    """
    Close database connection at the end of request.

    https://flask.palletsprojects.com/en/stable/tutorial/database/
    """
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


@app.after_request
def after_request(response):
    """
    Ensure responses aren't cached

    https://github.com/github-copilot/code_referencing?cursor=9288e6e03285ef2b3d7c56e1074da061,a30cb09eb0ae0020a383ad50b077059d
    """
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Homepage route
@app.route("/")
def home():

    if "user_id" in session:
        # Get username to greet him/her
        db = get_db()
        cursor = db.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],))
        row = cursor.fetchone()
        # Get user last order if has one
        cursor = db.execute("SELECT * FROM users_orders WHERE user_id = ? AND date = (SELECT MAX(date) AS 'max date' FROM users_orders WHERE user_id = ?)" , (session["user_id"], session["user_id"],))
        last_order = cursor.fetchall()
        return render_template("userhomepage.html", username=row["username"], last_order=last_order)
    else:
        return render_template("homepage.html")

# routes for log in, register and logout
@app.route("/register", methods=["GET", "POST"])
def register():

    # Forget any user_id
    session.clear()

    if request.method == "POST":
        # Check username
        if not request.form.get("username"):
            flash("Por favor ingresa un nombre de usuario")
            return render_template("register.html")
        # Check if username already exists in database
        db = get_db()
        cursor = db.execute("SELECT username FROM users WHERE username = ?", (request.form.get("username"),))
        row = cursor.fetchone()
        if row:
            return render_template("register.html", message="El nombre de usuario ya existe!")
        # Check phone
        if not request.form.get("phone"):
            flash("Por favor ingresa tu número de teléfono para poder mantenerte al tanto de tu pedido")
            return render_template("register.html")
        if request.form.get("username") == request.form.get("phone"):
            return render_template("register.html", message="El nombre de usuario y el teléfono no pueden ser iguales!")
        # Validate that phone number is numeric
        if not request.form.get("phone").isdigit():
            return render_template("register.html", message="Por favor ingresa un número de teléfono válido!")
        # Check if phone already exists in database
        cursor = db.execute("SELECT phone FROM users WHERE phone = ?", (request.form.get("phone"),))
        row = cursor.fetchone()
        if row:
            return render_template("register.html", message="El número de teléfono ya esta registrado!")
        # Validate password
        if not request.form.get("password"):
            flash("Por favor ingresa una contraseña, debe tener al menos 6 caracteres y un símbolo")
        # Check that password complies with security requirements
        if not password_check(request.form.get("password")):
            return render_template("register.html", message="La contraseña debe tener al menos 6 caracteres y un símbolo!")
        if not request.form.get("confirmation"):
            flash("Porfavor confirma tu contraseña")
            return render_template("register.html")
        # Check that password and confirmation match
        if request.form.get("password") != request.form.get("confirmation"):
            return render_template("register.html", message="Las contraseñas no coinciden!")
        # hash password
        password = generate_password_hash(request.form.get("password"))
        # Insert new user into database
        db.execute("INSERT INTO users (username, hash, phone) VALUES (?, ?, ?)", (request.form.get("username"), password, request.form.get("phone")))
        db.commit()
        # Remember user session and redirect to homepage
        cursor = db.execute("SELECT id FROM users WHERE username = ?", (request.form.get("username"),))
        row = cursor.fetchone()
        session["user_id"] = row["id"]
        return redirect("/", 200)
    else: 
        return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    # Forget any user_id
    session.clear()

    if request.method == "POST":
        # Check that username or password fields are not empty
        if not request.form.get("username"):
            flash("Porfavor ingresa tu nombre de usuario o teléfono")
            return render_template("login.html")
        if not request.form.get("password"):
            flash("Porfavor ingresa tu contraseña")
            return render_template("login.html")
        # Query database for username or phone
        db =get_db()
        cursor = db.execute("SELECT * FROM users WHERE username = ? OR phone = ?", (request.form.get("username"), request.form.get("username")))
        row = cursor.fetchone()
        # Verify username/phone exists and password is correct
        if row is None or not check_password_hash(row["hash"], request.form.get("password")):
            return render_template("login.html", message="Usuario o contraseña incorrecta!")
        # Remember user session and username. Redirect to homepage
        session["user_id"] = row["id"]
        return redirect("/", 200)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    # Forget user session and redirect user to homepage
    session.clear()
    return redirect("/")

# Route to create orders
@app.route("/orders", methods=["GET", "POST"])
@login_requered
def orders():
    # Get products and types from database
    products = []
    types = []
    db = get_db()
    cursor = db.execute("SELECT DISTINCT(name) FROM products")
    rows = cursor.fetchall()
    for row in rows:
        products.append(row["name"])
    cursor = db.execute("SELECT DISTINCT(TYPE) FROM products")
    rows = cursor.fetchall()
    for row in rows:
        types.append(row["type"])
    # Delete orders that are not completed
    db.execute ("DELETE FROM temp_orders WHERE date < datetime('now', '-5 minutes') ")
    db.commit()
    if request.method == "POST":
        if request.form.get("action") == "save":
            # Check selection of products
            if not request.form.get("product"):
                flash("Por favor selecciona un producto")
                return redirect("/orders")
            # Check valid selection of quantity
            if not request.form.get("quantity"):
                flash("Por favor selecciona la cantidad")
                return redirect("/orders")
            if int(request.form.get("quantity")) <= 0:
                flash("Por favor selecciona una cantidad válida (minimo 1)")
                return redirect("/orders")
            # Check selection of type
            if request.form.get("product") == "cupcake" and request.form.get("type") != "und":
                flash("Los cupcakes solo cuentan con una presentación, por favor solo selecciona und")
                return redirect("/orders")
            if request.form.get("product") != "cupcake" and not request.form.get("type"):
                flash("Por favor selecciona un tamaño")
                return redirect("/orders")
            if request.form.get("product") != "cupcake" and request.form.get("type") == "und":
                flash("Por favor selecciona un tamaño valido")
                return redirect("/orders")
            flash("Producto guardado exitosamente! (recuerda que pasados 5 minutos, si no realizas la compra, los productos añadidos seran eliminados)")
            # Save input and display order 
            product = request.form.get("product")
            quantity = int(request.form.get("quantity"))
            type = request.form.get("type")
            # Retrieve price from database
            if  product != "cupcake":
                cursor = db.execute("SELECT price FROM products WHERE name = ? AND type = ?", (product, type))
                price = cursor.fetchone()
                # Check valid price
                if price is None:
                    flash("Producto no disponible o no existe")
                else:
                    price = int(price["price"])
                    price = round(price * quantity, 2)
            else:
                # For cupcakes price is fixed, take it into consideration
                price = round(quantity * 6000, 2)
            # Delete orders that are not completed
            db.execute ("DELETE FROM temp_orders WHERE date < datetime('now', '-2 minutes') ")
            db.commit()
            # Insert data into temp_orders table
            db.execute("INSERT INTO temp_orders (user_id, product, quantity, type, price) VALUES (?, ?, ?, ?, ?)", 
                    (session["user_id"], product, quantity, type, price))
            db.commit()
            # Retrieve all orders from temp_orders table to display
            cursor = db.execute("SELECT * FROM temp_orders WHERE user_id = ?", (session["user_id"],))
            orders = cursor.fetchall()
            # Retrieve total purchase
            cursor = db.execute("SELECT SUM(price) AS total FROM temp_orders WHERE user_id = ?", (session["user_id"],))
            total = cursor.fetchone()
            total = total["total"]
            return render_template("orders.html", products=products, types=types, orders=orders, total_purchase=total)
        if request.form.get("action") == "checkout":
            # Move order temp_orders to users_orders
            cursor = db.execute ("SELECT * FROM temp_orders WHERE user_id = ?", (session["user_id"],))
            final_orders = cursor.fetchall()
            # Ensure that user knows that tried to sent and empty order
            if not final_orders:
                flash("No has añadido nada a tu orden")
                return redirect("/orders")
            else:
                for order in final_orders:
                    db.execute("INSERT INTO users_orders (user_id, product, quantity, type, price) VALUES (?, ?, ?, ?, ?)", 
                            (order["user_id"], order["product"], order["quantity"], order["type"], order["price"]))
                db.commit()
                # Delete temp_orders
                db.execute ("DELETE FROM temp_orders WHERE user_id = ?", (session["user_id"],))
                db.commit()
                # Return to homepage
                return redirect("/")
    else:
        # Retrive and empty order if the user has one
        cursor = db.execute("SELECT * FROM temp_orders WHERE user_id = ?", (session["user_id"],))
        orders = cursor.fetchall()
        # Retrieve total purchase if the user has one
        cursor = db.execute("SELECT SUM(price) AS total FROM temp_orders WHERE user_id = ?", (session["user_id"],))
        total = cursor.fetchone()
        total = total["total"]
        # Check that total returns a value
        if total is None:
            total = 0
        return render_template("orders.html", products=products, types=types, orders=orders, total_purchase=total)
    
# Orders history route
@app.route("/history")
@login_requered
def user_history():
    #Limit page of histtory (future scalability)
    page = int(request.args.get("page", 1))
    page_rows = 10
    offset = (page - 1) * page_rows
    # Get user orders history
    db = get_db()
    cursor = db.execute("SELECT * FROM users_orders WHERE user_id = ? ORDER BY date DESC LIMIT ? OFFSET ?", (session["user_id"], page_rows, offset))
    orders = cursor.fetchall()
    return render_template("history.html", orders=orders, page=page, page_rows=page_rows)

# Route to password change
@app.route("/password_update", methods=["GET", "POST"])
def password_update():

    # Forget session to ensure security
    session.clear()

    if request.method == "POST":
        # Check that are not empy fields
        if not request.form.get("username"):
            flash("Por favor introduce tu usuario o teléfono")
            return render_template("password_update.html")
        if not request.form.get("password"):
            flash("Por favor introduce tu contraseña actual")
            return render_template("password_update.html")
        if not request.form.get("new_password"):
            flash("Por favor introduce una nueva contraseña")
            return render_template("password_update.html")
        if not request.form.get("confirmation"):
            flash("Por favor confirma tu nueva contraseña")
            return render_template("password_update.html")
        # check that username or phone are in the database and that password matches the one in the database
        db = get_db()
        cursor = db.execute("SELECT * FROM users WHERE username = ? OR phone = ?", (request.form.get("username"),request.form.get("username")))
        row = cursor.fetchone()
        if row is None or not check_password_hash(row["hash"], request.form.get("password")):
            return render_template("password_update.html", message="Usuario o contraseña incorrecta!")
        # Check that new password complies with security requeriments
        if not password_check(request.form.get("new_password")):
            return render_template("password_update.html", message="La contraseña debe tener al menos 6 caracteres y un símbolo!")
        # Check that new password matches confirmation
        if request.form.get("new_password") != request.form.get("confirmation"):
            return render_template("password_update.html", message="Las contraseñas no coinciden!")
        # Hash new password
        password = generate_password_hash(request.form.get("new_password"))
        # Update user password into database
        db.execute("UPDATE users SET hash = ? WHERE id = ?", (password, row["id"]))
        db.commit()
        # Save user session and redirect to homepage
        session["user_id"] = row["id"]
        return redirect("/", 200)
    else:    
        return render_template("password_update.html")

# Routes to products  
@app.route("/cupcakes")
def cupcakes():
    return render_template("cupcakes.html")

@app.route("/cheesecake")
def cheese():
    return render_template("cheesecake.html")

@app.route("/3leches")
def leches():
    return render_template("3leches.html")

@app.route("/otros")
def otros():
    return render_template("otros.html")
