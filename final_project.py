import sqlite3
import os
import datetime
import email
from module import config
from flask import Flask, render_template, request, url_for, redirect, session
from flask_mail import Mail, Message
from flask_session import Session
from flask.wrappers import Request
from tempfile import mkdtemp
from itsdangerous.serializer import Serializer
from itsdangerous.url_safe import URLSafeSerializer, URLSafeTimedSerializer
# this is my own library
from support import error, password_check, login_required, success

# SECRET_KEY = os.environ.get("SECRET_KEY")
SECRET_KEY = "SECRET_KEY"
s = Serializer(SECRET_KEY)
SECURITY_PASSWORD_SALT = "im_a_rocket_man"

# create connection to SQL database, and create table if it doesn't exist
connection = sqlite3.connect('final_project.db', check_same_thread=False)
cursor = connection.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS users (
    id integer PRIMARY KEY,
    user_name text NOT NULL,
    email text NOT NULL,
    password text NOT NULL,
    date_joined DATE,
    confirmed boolean DEFAULT False
)""")

app = Flask(__name__)

app.config['MAIL_SERVER']='smtp.googlemail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'musicpractice171@googlemail.com'
app.config['MAIL_PASSWORD'] = '*****!'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)

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
            #  token = generate_confirmation_token(EMAIL)
            # confirm_url = url_for('confirm_email', token=token, _external=True)
            # html = render_template('activate.html', confirm_url=confirm_url)
            # subject = "Please confirm your email"
            # send_email(EMAIL, subject, html)

            # cursor.execute("UPDATE users SET email = ?, confirmed = 0 WHERE id = ?", (request.form.get("update_email"), session["user_id"]))
            # connection.commit()

            # return success("Check your inbox for an email")
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
        if not request.form.get("user_name"):
            return error("You didn't provide a username")
        elif not request.form.get("email"):
            return error("You didn't provide an email")
        elif not request.form.get("password"):
            return error("You didn't provide a password")
        elif not request.form.get("conf_password"):
            return error("You didn't confirm your password")
        else:
            # get the user name, email and passwords
            USER_NAME = request.form.get("user_name")
            EMAIL = request.form.get("email")
            PASSWORD = request.form.get("password")
            CONF_PASSWORD = request.form.get("conf_password")

            # user = User()
           
            # check if email is available
            cursor.execute("SELECT * FROM users WHERE email = ?", (EMAIL,))
            if cursor.fetchall():
                return error("email already in use, maybe you misspelled your email, or you already have an account?")
            else:
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

                # validate the email
                token = generate_confirmation_token(EMAIL)
                confirm_url = url_for('confirm_email', token=token, _external=True)
                html = render_template('activate.html', confirm_url=confirm_url)
                subject = "Please confirm your email"
                send_email(EMAIL, subject, html)
  
                return success("Check your inbox for an email")
    else:
        return render_template("register.html")


@app.route('/confirm/<token>')
# @login_required
def confirm_email(token):
    print("HELLO!!!!!!!!: ", token)
    try:
        email = confirm_token(token)
        print("EMAIL 1!!!!1!!!!!!: ", email)
        if not email:
            return error("Couldn't recognise email: T0DO RESEND VERIFICATION EMAIL")
    except:
        # flash('The confirmation link is invalid or has expired.', 'danger')
        error ("The confirmation link is invalid or has expired")
    # user = User.query.filter_by(email=email).first_or_404()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchall()[0]
    print("USER!!!: ", user)
    if user[5] == 1:
        # flash('Account already confirmed. Please login.', 'success')
        return error("Account already confirmed. Please login")
    else:
        # user.confirmed_on = datetime.datetime.now()
        cursor.execute("UPDATE users SET confirmed = 1 WHERE email = ?", (email,))
        connection.commit()
        # flash('You have confirmed your account. Thanks!', 'success')
        session["user_id"] = user[0]
        session["verified"] = True
        return success("You have confirmed your account. Thanks")
    return redirect('/')


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
        elif user_info[0][5] == False:
            session["user_id"] = user_info[0][0]
            session["verified"] = False
            return render_template("resend_verification.html", email=user_info[0][2])
        else:
            # remember who has logged in
            session["user_id"] = user_info[0][0]
            session["verified"] = True
            return redirect("/")

@app.route("/resend", methods=["GET", "POST"])
def resend():
    # validate the email
    email = cursor.execute("SELECT email FROM users WHERE id = ?", (session["user_id"],))
    token = generate_confirmation_token(email)
    confirm_url = url_for('confirm_email', token=token, _external=True)
    html = render_template('activate.html', confirm_url=confirm_url)
    subject = "Please confirm your email"
    send_email(email, subject, html)

    return success("Check your inbox for an email")           

@app.route("/logout")
def logout():
    """Log user out"""
    # Forget any user_id
    session.clear()
    # Redirect user to login form
    return redirect("/")


# validating emails via unique URLs
def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    print("HERE'S YOUR SERIALIZER BOSS: ", serializer)
    return serializer.dumps(email, salt=SECURITY_PASSWORD_SALT)


def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    try:
        email = serializer.loads(
            token,
            salt=SECURITY_PASSWORD_SALT,
            max_age=expiration
        )
    except:
        return False
    return email

# sending activation email
def send_email(to, subject, template):
    print("DIDN'T CRASH: 1.1")
    msg = Message(
        subject,
        recipients=[to],
        html=template,
        sender=config.BaseConfig.MAIL_DEFAULT_SENDER,
    )
    print("DIDN'T CRASH: 1.7")
    mail.send(msg)
    print("DIDN'T CRASH: 1.8")


