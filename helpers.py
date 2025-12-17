import requests
import string

from flask import redirect, render_template, session
from functools import wraps

# Enforce that user is logged in
def login_requered(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **Kwargs):
        if session.get("user_id") is None:
            return redirect("/")
        return f(*args, **Kwargs)
    return decorated_function

# Check password requerements
def password_check(password):
    if len(password) < 6:
        return False
    has_symbol = False
    for char in password:
        if char in string.punctuation:
            has_symbol = True
    if not has_symbol:
        return False
    return True

    


