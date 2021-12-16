from flask import render_template, session, redirect
from functools import wraps

# function to show an error message
def error(err_mess):
        return render_template("error.html", message=err_mess)

def success(succ_mess):
        return render_template("success.html", message=succ_mess), {"Refresh": "2; url=/"}

def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None or session["verified"] is False:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


# function for checking password validity - slightly edit from source code from https://www.geeksforgeeks.org/password-validation-in-python/
def password_check(passwd):
      
    SpecialSym =['$', '@', '#', '%', '!']
      
    if len(passwd) < 6:
        return (False, error('Password length should be at least 6'))
          
    elif len(passwd) > 20:
        return (False, error('Password length should be not be greater than 20'))
          
    elif not any(char.isdigit() for char in passwd):
        return (False, error('Password should have at least one number'))
          
    elif not any(char.isupper() for char in passwd):
        return (False, error('Password should have at least one uppercase letter'))
          
    elif not any(char.islower() for char in passwd):
        return (False, error('Password should have at least one lowercase letter'))
          
    elif not any(char in SpecialSym for char in passwd):
        return (False, error('Password should have at least one of the symbols $ @ # % !'))

    else:
        return (True,)
