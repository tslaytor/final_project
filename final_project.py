import sqlite3
import os
import datetime
import email
from module import config
from flask import Flask, render_template, request, url_for
from flask_mail import Mail, Message
from flask.wrappers import Request
from validate_email_address import validate_email
from itsdangerous.serializer import Serializer
from itsdangerous.url_safe import URLSafeSerializer, URLSafeTimedSerializer
# from itsdangerous import URLSafeTimedSerializer

SECRET_KEY = os.environ.get("SECRET_KEY")
s = Serializer(SECRET_KEY)
SECURITY_PASSWORD_SALT = "im_a_rocket_man"

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
mail = Mail(app)


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
            CONF_PASSWORD = request.form.get("conf_password")
            # check if email is available
            cursor.execute("SELECT * FROM users WHERE email = ?", (EMAIL,))
            if cursor.fetchall():
                return error("email already in use, maybe you misspelled your email, or you already have an account?")
            else:
                # check if password meets criteria
                valid = password_check(PASSWORD)
                if not valid[0]:
                    return valid[1]
                # check if passwords match
                if PASSWORD != CONF_PASSWORD:
                    return error("Passwords do not match")
                # hash the password
                
                # add user to database
                cursor.execute("INSERT INTO users (user_name, email, date_joined, password) VALUES(?, ?, DATE(), ?)", (USER_NAME, EMAIL, PASSWORD))
                connection.commit()
                # check if the email is valid and activate the user
                token = generate_confirmation_token(EMAIL)
                confirm_url = url_for('confirm_email', token=token, _external=True)
                html = render_template('activate.html', confirm_url=confirm_url)
                subject = "Please confirm your email"
                send_email(EMAIL, subject, html)

                login_user(user)

                flash('A confirmation email has been sent via email.', 'success')
                
                return error("actually it's not an error, its working")
    else:
        return render_template("register.html")

@app.route('/confirm/<token>')
# @login_required
def confirm_email(token):
    try:
        email = confirm_token(token)
    except:
        flash('The confirmation link is invalid or has expired.', 'danger')
    user = User.query.filter_by(email=email).first_or_404()
    if user.confirmed:
        flash('Account already confirmed. Please login.', 'success')
    else:
        user.confirmed = True
        user.confirmed_on = datetime.datetime.now()
        db.session.add(user)
        db.session.commit()
        flash('You have confirmed your account. Thanks!', 'success')
    return redirect('/')



# function to show an error message
def error(err_mess):
        return render_template("error.html", message=err_mess)


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

# validating emails via unique URLs
def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(SECRET_KEY)
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
    msg = Message(
        subject,
        recipients=[to],
        html=template,
        sender=config.BaseConfig['MAIL_DEFAULT_SENDER']
    )
    mail.send(msg)





        