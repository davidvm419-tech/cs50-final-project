import os
from datetime import datetime

from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash


# Configure application
app = Flask(__name__)

# Configure session to filesystem
app.config["SESSION PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


#Configure database


@app.route("/")
def home():
    return render_template("homepage.html")

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
