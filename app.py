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
app.config["SESSION PERMANENT"] = False
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
        db = get_db()
        cursor = db.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],))
        row = cursor.fetchone()
        return render_template("userhomepage.html", username=row["username"])
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
            flash("Porfavor ingresa un nombre de usuario")
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
            flash("Por favor ingresa una contraseña, debe tener al menos 6 caracteres y un simbolo")
        # Check that password complies with security requirements
        if not password_check(request.form.get("password")):
            return render_template("register.html", message="La contraseña debe tener al menos 6 caracteres y un simbolo!")
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
        return redirect("/userhomepage", 200)
    else: 
        return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    # Forget any user_id
    session.clear()

    if request.method == "POST":
        # Check that username or password fields are not empty
        if request.method == "POST":
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
        # Remember user session and redirect to homepage
        session["user_id"] = row["id"]
        return redirect("/userhomepage", 200)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    # Forget user session and redirect user to homepage
    session.clear()
    return redirect("/")

# User homepage route
@app.route("/userhomepage")
@login_requered
def userhomepage():
    if "user_id" in session:
        db = get_db()
        cursor = db.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],))
        row = cursor.fetchone()
        return render_template("userhomepage.html", username=row["username"])
    else:
        return redirect("/homepage.html")


# Route to create orders
@app.route("/orders", methods=["GET", "POST"])
@login_requered
def orders():
    # Get products and types from database
    products = []
    db = get_db()
    cursor = db.execute("SELECT DISTINCT(name) FROM products")
    rows = cursor.fetchall()
    for row in rows:
        products.append(row["name"])
    if request.method == "POST":
        # Check selection of products
        if not request.form.get("product"):
            flash("Por favor selecciona un producto")
            return render_template("orders.html", products=products)
        # Check valid selection of quantity
        if not request.form.get("quantity"):
            flash("Por favor selecciona la cantidad")
            return render_template("orders.html", products=products)
        if int(request.form.get("quantity")) <= 0:
            flash("Por favor selecciona una cantidad válida (minimo 1)")
            return render_template("orders.html", products=products)
        # Check selection of type
        if request.form.get("product") == "cupcake" and request.form.get("type"):
            flash("Los cupcakes solo cuentan con una presentación, por favor solo selecciona una cantidad")
            return render_template("orders.html", products=products)
        if request.form.get("product") != "cupcake" and not request.form.get("type"):
            flash("Por favor selecciona un tamaño")
            return render_template("orders.html", products=products)
        if request.form.get("product") != "cupcake" and request.form.get("type") != "mediano" and request.form.get("type") != "grande" and request.form.get("type") != "personalizado":
            flash("Por favor selecciona un tamaño válido (mediano, grande o personalizado)")
            return render_template("orders.html", products=products)
        flash("Pedido guardado exitosamente!")
        # Save input and display order 
        product = request.form.get("product")
        quantity = int(request.form.get("quantity"))
        type = request.form.get("type")
        # Retrieve price from database
        cursor = db.execute("SELECT price FROM products WHERE name = ?, AND ")

        price
        order = {
            "product": product,
            "quantity": quantity,
            "type": type
        }
        return render_template("orders.html", products=products, order=order)

    else:
        return render_template("orders.html", products=products)
    

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
