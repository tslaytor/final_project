import sqlite3
from flask import Flask, render_template, request
from flask.wrappers import Request

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

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/diary")
def diary():
    return render_template("diary.html")

@app.route("/account", methods=["GET", "POST"])
def account():
    if request.method == "POST":
        return render_template("account.html")
    else:
        return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if user name provided
        if not request.form.get("user_name"):
            return error("You didn't provide a username")
        #  check if password provided
        elif not request.form.get("password"):
            return error("You didn't provide a password")
        #  check if conf_password provided
        elif not request.form.get("conf_password"):
            return error("You didn't confirm your password")
        else:
            # get the user name, email and passwords
            USER_NAME = request.form.get("user_name")
            EMAIL = request.form.get("email")
            PASSWORD = request.form.get("password")
            CONF_PASSWORD = request.form.get("password")
            # check if email is available
            cursor.execute("SELECT * FROM users WHERE email = ?", EMAIL)
            if cursor.fetchall():
                return error("email already in use, maybe you misspelled your email, or you already have an account?")
            # check username is available
            cursor.execute("SELECT * FROM users WHERE user_name = ?", USER_NAME)
            if cursor.fetchall():
                return error("Username already in use. Please choose another")
            else:
                # check if password meets criteria
                # check if passwords match
                if PASSWORD != CONF_PASSWORD:
                    return error("Passwords do not match")
                # hash the password
                
                # add user to database
                cursor.execute("INSERT INTO users (user_name, email, date_joined, password) VALUES(?, ?, DATE(), ?)", (USER_NAME, EMAIL, PASSWORD))
                connection.commit()
                return error("actually it's not an error, its working")

            password = request.form.get("password")
            conf_password = request.form.get("conf_password")
    else:
        return render_template("register.html")

def error(err_mess):
        return render_template("error.html", message=err_mess)