import sqlite3
from flask import Flask, render_template, request, redirect, session
from flask_session import Session
from flask.wrappers import Request
from validate_email_address import validate_email
from tempfile import mkdtemp
# this is my own library
from support import error, password_check, login_required

# create connection to SQL database, and create table if it doesn't exist
connection = sqlite3.connect('final_project.db', check_same_thread=False)
cursor = connection.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS users (
    id integer PRIMARY KEY,
    user_name text NOT NULL,
    email text NOT NULL,
    password text NOT NULL,
    date_joined DATE
)""")

app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.route("/")
@login_required
def home():
    return render_template("index.html", user=session["user_id"])

@app.route("/diary")
@login_required
def diary():
    return render_template("diary.html")

@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    if request.method == "POST":
        # update username
        if request.form.get("change_username"):
            cursor.execute("UPDATE users SET user_name = ? WHERE id = ?", (request.form.get("change_username"), session["user_id"]))
            connection.commit()
            return redirect("/account")

        # update email
        elif request.form.get("update_email"):
            # check if email is available
            cursor.execute("SELECT id FROM users WHERE email = ?", (request.form.get("update_email"),))
            if cursor.fetchall():
                return error("email is not available, double check email address typed correctly, or that you don't already have an account using this email")
            # TO DO validate email
            cursor.execute("UPDATE users SET email = ? WHERE id = ?", (request.form.get("update_email"), session["user_id"]))
            connection.commit()
            return redirect("/account")

        # update password
        elif request.form.get("update_password"):
            if not request.form.get("update_password"):
                # TODO change this error to javascript message
                return error("Password field was blank")
            elif not request.form.get("confirm_update_password"):
                # TODO change this error to javascript message
                return error("Confirm password field was blank")
            elif request.form.get("update_password") != request.form.get("confirm_update_password"):
                # TODO change this error to javascript message
                return error("Passwords do not match")
            # elif not password_check(request.form.get("update_password"))[0]:
            #     return error("Password didn't pass the check")
            else:
                cursor.execute("UPDATE users SET password = ? WHERE id = ?", (request.form.get("update_password"), session["user_id"]))
                connection.commit()
                return redirect("/account")
        else:
            return redirect("/account")

    else:
        cursor.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],))
        USER = cursor.fetchall()[0]
        return render_template("account.html", user_name=USER)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check all fields are completed
        if not request.form.get("user_name"):
            return error("You didn't provide a username")
        elif not request.form.get("email"):
            return error("You didn't provide an email")
        elif not request.form.get("password"):
            return error("You didn't provide a password")
        elif not request.form.get("conf_password"):
            return error("You didn't confirm your password")
        
        # get the user name, email and passwords
        USER_NAME = request.form.get("user_name")
        EMAIL = request.form.get("email")
        PASSWORD = request.form.get("password")
        CONF_PASSWORD = request.form.get("conf_password")
        
        # check if email is available
        cursor.execute("SELECT * FROM users WHERE email = ?", (EMAIL,))
        if cursor.fetchall():
            return error("email already in use, maybe you misspelled your email, or you already have an account?")
        else:
            x = 1
            # check if the email is valid
            # if not validate_email(EMAIL):
            #     return error("Please provide a valid email address")
            # check if password meets criteria
            # valid = password_check(PASSWORD)
            # if not valid[0]:
            #     return valid[1]
            # check if passwords match
            if PASSWORD != CONF_PASSWORD:
                return error("Passwords do not match")
            # hash the password
            
            # add user to database
            cursor.execute("INSERT INTO users (user_name, email, date_joined, password) VALUES(?, ?, DATE(), ?)", (USER_NAME, EMAIL, PASSWORD))
            connection.commit()
            cursor.execute("SELECT * FROM users WHERE email = ?", EMAIL)
            result = cursor.fetchall()
            session["user_id"] = result[0][0]
            return redirect('/')
    else:
        return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    else:
        # check form fields
        if not request.form.get("email"):
            return error("No email provided - redirecting")
        if not request.form.get("password"):
            return error("You must provide a password if you don't want to look like a cunt")
        # check user exists
        cursor.execute("SELECT * FROM users WHERE email = ?", (request.form.get("email"),))
        user_info = cursor.fetchall()
        if len(user_info) != 1:
            return error("no user registered with this email - redirectin")
        # check password is correct
        elif request.form.get("password") != user_info[0][3]:
            return error("Passwords don't match - redirectin")
        else:
            # remember who has logged in
            session["user_id"] = user_info[0][0]
            return redirect("/")
        

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

