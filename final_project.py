from logging import currentframe
import sqlite3
import os
import datetime
import email
from dotenv import dotenv_values, load_dotenv
from flask import Flask, render_template, request, url_for, redirect, session
from flask_mail import Mail, Message
from flask_session import Session
from flask.wrappers import Request
from tempfile import mkdtemp
from itsdangerous.serializer import Serializer
from itsdangerous.url_safe import URLSafeSerializer, URLSafeTimedSerializer
# this is my own library
from support import error, password_check, login_required, success


# SECRET_KEY = os.environ.get("SECRET_KEY") # TODO FIX SECRET KEY
SECRET_KEY = "SECRET_KEY"
s = Serializer(SECRET_KEY) # TODO WHEN DO I USE S?
SECURITY_PASSWORD_SALT = "im_a_rocket_man" # TODO - IMPROVE THE SECURITY OF SALT


load_dotenv("/Users/thomas/final_project/PASSWORDS.env") # TODO REMIND YOURSELF WHAT THIS DOES AGAIN

# CREATE CONNECTION TO SQL DATABASE - AND CREATE TABLES
connection = sqlite3.connect('final_project.db', check_same_thread=False)
cursor = connection.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS users (
    id integer PRIMARY KEY,
    user_name text NOT NULL,
    email text NOT NULL,
    password text NOT NULL,
    date_joined DATE NOT NULL,
    confirmed boolean DEFAULT False
)""")

# CREATE CONTENT TABLE
cursor.execute("""CREATE TABLE IF NOT EXISTS content (
    id integer PRIMARY KEY,
    title text NOT NULL
)""")

# CREATE LIBRARY TABLE
cursor.execute("""CREATE TABLE IF NOT EXISTS library (
    user_id integer, 
    content_id integer,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (content_id) REFERENCES content(id)
)""")

# CREATE RATING TABLE
cursor.execute("""CREATE TABLE IF NOT EXISTS rating (
    id INTEGER PRIMARY KEY,
    rating TEXT NOT NULL
)""")

# CREATE DIARY TABLE
cursor.execute("""CREATE TABLE IF NOT EXISTS diary (
    id integer PRIMARY KEY,
    user_id integer, 
    content_id integer,
    tempo integer NOT NULL CHECK (30 <= tempo <= 300),
    rating_id integer NOT NULL,
    notes TEXT,
    date DATE NOT NULL, 
    color TEXT NOTE NULL,
    FOREIGN KEY (user_id) references users(id),
    FOREIGN KEY (content_id) references content(id),
    FOREIGN KEY (rating_id) REFERENCES rating(id)
)""")

# POPULATE THE RATING TABLE
for n in range(1, 6):
    rating = f"{n} stars"
    cursor.execute("INSERT INTO rating (rating) VALUES (?)", (rating,))
    connection.commit()


app = Flask(__name__)

# MAIL CONFIGURATION
app.config['MAIL_SERVER']='smtp.googlemail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'musicpractice171@googlemail.com'
app.config['MAIL_PASSWORD'] = os.environ["EMAIL_PASSWORD"]
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# ************
# START OF APP
# ************

# -----------
# HOME ROUTE
# -----------
@app.route("/")
# @login_required
def home():
    #####################################
    # HACK TO LET ME NOT LOGGIN EVERYTIME  # DELETE LATER
    session["user_id"] = 1
    session["verified"] = True
    # HACK TO LET ME NOT LOGGN EVERYTIME # DELETE LATER
    ######################################
   
    return render_template("index.html", user=session["user_id"])

# ----------------------------------------------------
# ROUTE - ADD NEW CONTENT TO CONTENT AND/OR LIBRARY TABLES
# ----------------------------------------------------
@app.route("/add_content", methods=["POST"])
@login_required
def add_content():
    # GET THE INPUT FROM THE FORM
    new_content = request.form.get("new_content").strip()
    print("THIS IS NEW CONTENT ", new_content)
    # CHECK IF THE CONTENT ALREADY EXISTS IN THE CONTENT TABLE
    cursor.execute("SELECT * FROM content WHERE title = ?", (new_content,))
    if cursor.fetchall():
        print("THIS SHOULDN'T REACH HERE FOR TOTALLY NEW TITLES ")
        cursor.execute("SELECT * FROM content WHERE title = ?", (new_content,))
        content_id = cursor.fetchall()[0][0]
        # CONTENT ALREADY IN CONTENT TABLE - NOW CHECKING IF CONTENT IN USER LIBRARY
        cursor.execute("SELECT * FROM library WHERE content_id = ? AND user_id = ?", (content_id, session["user_id"]))
        if cursor.fetchall():
            # CONTENT ALREADY IN USER LIBRARY
            return redirect("/diary")
        else:
            # CONTENT NOT IN USER LIBRARY - ADDING NOW
            cursor.execute("INSERT INTO library (user_id, content_id) VALUES (?,?)", (session["user_id"], content_id))
            connection.commit()
            return redirect("/diary")
    else:
        # INSERT NEW CONTENT INTO CONTENT TABLE
        cursor.execute("INSERT INTO content (title) VALUES (?)", (new_content,))
        connection.commit()
        # GET THE NEW CONTENT'S ID
        cursor.execute("SELECT * FROM content WHERE title = ?", (new_content,))
        content_id = cursor.fetchall()[0][0]
        # ADD CONTENT TO USERS LIBRARY
        cursor.execute("INSERT INTO library (user_id, content_id) VALUES (?, ?)", (session["user_id"], content_id) )
        connection.commit()
        return redirect("/diary")



# ---------------------------------------------------------------------------------
# DIARY ROUTE - DISPLAYS DROPDOWN OF USER'S LIBRARY AND TABLE OF USER'S DIARY TABLE
# --------------------------------------------------------------------------------
@app.route("/diary", methods=["GET", "POST"])
@login_required
def diary():

    if request.method == "POST":
        
        # ####################################################################################################################################
        # THIS WHOLE THING IS WIERD - LETS FIX ONE DAY
        # ############################################
        # get all the values in one go
        a = {}
        a["content"] = request.form.get("content")
        a["tempo"] = request.form.get("tempo")
        a["rating"] = request.form.get("rating")
        a["notes"] = request.form.get("notes")

        # EXTRACT RELEVANT INFO
        # content_id
        cursor.execute("SELECT id FROM content WHERE title = ?", (a["content"],))
        content_id = cursor.fetchall()

        # CHECK SELECTED CONTENT IS IN THE CONTENT TABLE
        if not content_id:
            return error("Problem with the selected content - something weird - I suggest deleting that content and re-uploading")
        content_id = content_id[0][0]
        
        # tempo (as an int)
        tempo = int(a["tempo"][:-4])
        
        # rating_id
        rating_id = int(a["rating"][:-6])
        # ############################################
        # THIS WHOLE THING IS WIERD - LETS FIX ONE DAY
        # ####################################################################################################################################

        # # FIND THE LAST COLOR USED AND CHANGE IF NECESSARY
        # cursor.execute("SELECT color FROM diary ORDER BY id DESC LIMIT 1")
        # color = cursor.fetchall()
        # if color:
        #     # if DATE() != lastRecordedDate:
        #     if 1 != 2:
        #         if color[0] == "blue":
        #             color[0] == "red"
        #         else:
        #             color[0] == "blue"
        # else:
        #     color.append("blue")
        
        # INSERT THE NEW VALUES INTO THE DIARY
        cursor.execute("""INSERT INTO diary (date, user_id, content_id, tempo, rating_id, notes) 
        VALUES (DATE(), ?, ?, ?, ?, ?)""", (session["user_id"], content_id, tempo, rating_id, a["notes"]))
        connection.commit()

       
        # GET INFORMATION NEEDED FOR RENDER TEMPLATE
        cursor.execute("""SELECT title FROM content 
                            JOIN library ON content.id = library.content_id  
                            WHERE library.user_id = ?""", (session["user_id"],))
        CONTENT = cursor.fetchall()
        
        cursor.execute("""SELECT 
                        content.title, diary.tempo, rating.rating, diary.notes, diary.color
                        FROM diary 
                        JOIN content ON content.id = diary.content_id 
                        JOIN rating on rating.id = diary.rating_id
                        ORDER BY diary.id DESC""")
        DIARY = cursor.fetchall()
     
        # RETURN RENDER TEMPLATE
        return render_template("diary.html", content=CONTENT, diary=DIARY,)
    
    else:
        # GET INFORMATION NEEDED FOR RENDER TEMPLATE
        cursor.execute("""SELECT
                        content.title, diary.tempo, rating.rating, diary.notes
                        FROM diary 
                        JOIN content ON content.id = diary.content_id 
                        JOIN rating on rating.id = diary.rating_id
                        ORDER BY diary.id DESC""")
        DIARY = cursor.fetchall()
        
        cursor.execute("""SELECT title FROM content 
                            JOIN library ON content.id = library.content_id  
                            WHERE library.user_id = ?""", (session["user_id"],))
        CONTENT = cursor.fetchall()
        return render_template("diary.html", diary=DIARY, content=CONTENT)


# -------------
# ACCOUNT ROUTE
# -------------
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
                # TODO REIMPLEMENT PASSWORD CHECKS
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


# --------------
# ROUTE REGISTER
# --------------
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
           
            # check if email is available
            cursor.execute("SELECT * FROM users WHERE email = ?", (EMAIL,))
            if cursor.fetchall():
                return error("email already in use, maybe you misspelled your email, or you already have an account?")
            else:
                # TODO REIMPLEMENT PASSWORD CHECK
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

# ---------------------------------
# ROUTE - CONFIRMS THE USER TOKEN
# ---------------------------------
@app.route('/confirm/<token>')
def confirm_email(token):
    # CHECK TOKEN IS VALID
    try:
        email = confirm_token(token)
        if not email:
            return error("Couldn't recognise email - try to login again and resend email when prompted")
    except:
        error ("The confirmation link is invalid or has expired")
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchall()[0]
    # CHECK IF ACCOUNT ALREADY CONFIRMED
    # CONFIRMED
    if user[5] == 1:
        if session.get("user_id"):
            return error("Account already confirmed, and you are already logged in")
        else:
            return error("Account already confirmed. Please login")
    # UNCONFIRMED
    else:
        cursor.execute("UPDATE users SET confirmed = 1 WHERE email = ?", (email,))
        connection.commit()
        session["user_id"] = user[0]
        session["verified"] = True
        return success("You have confirmed your account. Thanks")

# ------------
# LOGIN ROUTE
# ------------
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
            return error("No user registered with this email")
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
    #  if session.get --- REDIRECT WITH ERROR MESSAGE IF THE SESSION[USER ID] IS INVALID SYNTAX
    email = cursor.execute("SELECT email FROM users WHERE id = ?", (session["user_id"],))
    email = email.fetchall()[0][0]
    token = generate_confirmation_token(email)
    confirm_url = url_for('confirm_email', token=token, _external=True)
    html = render_template('activate.html', confirm_url=confirm_url)
    subject = "Please confirm your email"
    send_email(email, subject, html)

    return success("Check your inbox for an email")           

@app.route("/logout")
def logout():
    """Log user out"""
    session.clear()
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
        sender=app.config['MAIL_USERNAME'],
    )
    print("DIDN'T CRASH: 1.7")
    mail.send(msg)
    print("DIDN'T CRASH: 1.8 - EMAIL SENT")


