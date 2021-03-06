import os
import psycopg2
from cs50 import SQL 
from helpers import login_required
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from flask_session.__init__ import Session

from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from itsdangerous import URLSafeTimedSerializer
from encryption import encrypt, confirm
from flask_mail import Mail, Message
# from sightengine.client import SightengineClient
import re
# Configure application
app = Flask(__name__)
# client = SightengineClient('1430167149', 'HGWoQTvgiFjhZq5tT8uW')

#ASdasd
#Setting up database:

#Need to install "pip install psycopg2-binary"

# pip freeze > requirements.txt
# DATABASE_URL = os.environ['DATABASE_URL']
# app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
# conn = psycopg2.connect(DATABASE_URL, sslmode='require')
# db = SQLAlchemy(app)


db = SQL("postgres://hsabnnjlfxmdwq:651a62eb8a4e7ca6414fb9e9f4e47f4c4d14c2633f009839df088f5beff7f644@ec2-54-235-193-0.compute-1.amazonaws.com:5432/d3kou60qiu4jp5")
# db = SQL("postgres://hsabnnjlfxmdwq:651a62eb8a4e7ca6414fb9e9f4e47f4c4d14c2633f009839df088f5beff7f644@ec2-54-235-193-0.compute-1.amazonaws.com:5432/d3kou60qiu4jp5")

#db = SQL("postgres://hsabnnjlfxmdwq:651a62eb8a4e7ca6414fb9e9f4e47f4c4d14c2633f009839df088f5beff7f644@ec2-54-235-193-0.compute-1.amazonaws.com:5432/d3kou60qiu4jp5")
#DATABASE_URL = os.environ['DATABASE_URL']
#conn = psycopg2.connect(DATABASE_URL, sslmode='require')
#db. = conn.cursor()

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

UPLOAD_FOLDER = '/Users/jameslee/Downloads/hmarket/project/static'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
    return '.' in filename and \
          filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
mail=Mail(app)

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'hmarketinfo@gmail.com'
app.config['MAIL_PASSWORD'] = 'Hmarket123'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)
Session(app)



@app.route("/")
def index():
    if (session.get("user_id") is not None):
        items =db.execute("SELECT * FROM item")
        return render_template("index.html", items=items)
    else:
        items=db.execute("SELECT * FROM item")
        return render_template("homepage.html", items=items)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        result = db.execute("SELECT * FROM users WHERE username = :username",

                            username=request.form.get("username"))
        if result:
             flash("Username is already taken! Please try again.")
             return render_template("register.html")


        username=request.form.get("username")

        if not re.match(r"^[A-Za-z0-9._%+-]+@college.harvard.edu$", username):
            flash("Email Address must be a valid Harvard College email address")
            return render_template("register.html")

        password=request.form.get("password")
        if re.match(r"^([^0-9]*|[^A-Z]*)$", password):
            flash("Password must contain at least 1 uppercase letter and 1 number")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters")
            return render_template("register.html")

        confirm_password = request.form.get("confirm_password")
        if not password == confirm_password:
            flash("Passwords are not identical!")
            return render_template("register.html")
        db.execute("INSERT INTO users(username, hash,status) VALUES (:username, :hash, :status)", username=request.form.get("username"),hash=generate_password_hash(request.form.get("password")), status=0)
        token=encrypt(username)
        email=token
        print(token)
        confirm_url = url_for('confirm_email', token=token, _external=True)
        msg = Message('Confirmation', sender = 'hmarketinfo@gmail.com', recipients = [username])
        msg.body = "Welcome! Thanks for signing up. Please follow this link to activate your account: " + confirm_url
        mail.send(msg)
        print("Sent")
        return redirect(url_for("unconfirmed"))
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET","POST"])
@login_required
def sell():
    if request.method == "POST":
        file=request.files['image']

        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        reference_url=(url_for('static',filename=filename))
        price = '${:,.2f}'.format(float(request.form.get("price")))
        db.execute("INSERT INTO item(category, title, description, price, image, notes, seller_id) VALUES (:category, :title, :description, :price, :image, :notes, :seller_id)",
                        category= request.form.get("category"), title=request.form.get("title"),
                        description= request.form.get("description"), price=price, image = reference_url, notes=request.form.get("notes"), seller_id=session["user_id"])
        # return redirect ("/", invalidImage=invalidImage, init=True)
        return redirect("/")
    else:
        return render_template("sell.html")


@app.route("/buy/<u_id>", methods=["GET", "POST"])
@login_required
def buy(u_id):
    if request.method== "POST":
        print("check")
        u_id=request.view_args["u_id"]
        buyer_email = session["user_id"]
        seller_email_dictionary = db.execute("SELECT seller_id FROM item WHERE id=:u_id", u_id=u_id)
        print(u_id)
        print(buyer_email)
        seller_email=seller_email_dictionary[0]["seller_id"]
        print(seller_email)
    #Sends email to
        msg = Message('Confirmation', sender = 'hmarketinfo@gmail.com', recipients = [buyer_email, seller_email])
        msg.body = "An item has been bought by {} from {}".format(buyer_email,seller_email)
        mail.send(msg)
        return render_template("sold.html")
    else:
        item=db.execute("SELECT * FROM item where id=:u_id", u_id=u_id)
        u_id=u_id
        return render_template("buy.html", item=item)

@app.route("/myitems", methods=["GET", "POST"])
@login_required
def myitems():
    if request.method=="POST":
        item=db.execute("SELECT * FROM item where seller_id=:seller_user", seller_user=session["user_id"])
        print(item)
        selected=request.form.getlist('item')
        for value in selected:
            db.execute("DELETE from item where id=:u_id",u_id=value)
        # for item in item:
        #     if request.form.get('item'):
        #         db.execute("DELETE from item where id=:u_id", u_id=item["id"])
        return redirect("/")
    else:
        item=db.execute("SELECT * FROM item where seller_id=:seller_user", seller_user=session["user_id"])
        return render_template("myitems.html", item=item)

# @app.route("/cart", methods =["GET", "POST"])
# def cart():
#     if request.method=="POST":




@app.route('/<token>')
def confirm_email(token):
    ##user=current_user_id (do through query of SQL)
    try:
        email=confirm(token)
    except:
        redirect(url_for('unconfirmed'))
    print(email)
    user = db.execute("SELECT * FROM users WHERE username = :email::text", email=email)
    print(user)
    #if (user.status=True):
        #print("already confirmed!")
    #else:
        #user.status= True
    user[0]["status"] = 1
    db.execute("UPDATE users SET status = :new_status", new_status = user[0]["status"])
    return redirect(url_for("login"))

@app.route('/unconfirmed')
def unconfirmed():
    # user = db.execute("SELECT * FROM user WHERE username = :email", email=email)
    # print(user)
    # if user[0]["status"]== 1:
    #     return redirect("index")
    # else:
    session.clear()
    return render_template("unconfirmed.html")

# @app.route('/'), methods = ["GET", "POST"]
# def search():
#     if request.method == "POST":
#         search = request.form.get("search")
#         result = db.execute("SELECT * FROM items WHERE title, description, category = :search", search = search)
#         if result:




@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        username=request.form.get("username")

        # Ensure username was submitted
        if not request.form.get("username"):
            #return apology("must provide username", 403)
            flash("Must provide username")
            return render_template("login.html")

        # Ensure password was submitted
        elif not request.form.get("password"):
            #return apology("must provide password", 403)
            flash("Must provide password")
            return render_template("login.html")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            flash("Invalid username or password")
            return render_template("login.html")

        if rows[0]["status"]==0:
            flash("Confirm your status")
            return render_template("login.html")

        # Remember which user has logged in
        session["user_id"] = rows[0]["username"]

        # Redirect user to home page
        return redirect("/")
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/terms")
def terms():
    return render_template("terms.html")

@app.route("/books")
def books():
    items=db.execute("SELECT * from item WHERE category=:category", category="books")
    return render_template("index.html", items=items)

@app.route("/other")
def other():
    items=db.execute("SELECT * FROM item WHERE category=:category", category="other")
    return render_template("index.html",items=items)


@app.route("/technology")
def technology():
    items=db.execute("SELECT * FROM item WHERE category=:category", category="technology")
    return render_template("index.html", items=items)

@app.route("/furniture")
def furniture():
    items=db.execute("SELECT * FROM item WHERE category=:category", category="furniture")
    return render_template("index.html", items=items)

@app.route("/tickets")
def tickets():
    items=db.execute("SELECT * FROM item WHERE category=:category", category="tickets")
    return render_template("index.html", items=items)

@app.route("/apparel")
def apparel():
    items = db.execute("SELECT * FROM item WHERE category=:category", category="apparel")
    return render_template("index.html", items = items)

if __name__ == '__main__':
 app.debug = True
 port = int(os.environ.get('PORT', 5000))
 app.run(host= '0.0.0.0', port=port)
 
 class SQL(object):
    def __init__(self, url):
        try:
            self.engine = sqlalchemy.create_engine(url)
        except Exception as e:
            raise RuntimeError(e)
    def execute(self, text, *multiparams, **params):
        try:
            statement = sqlalchemy.text(text).bindparams(*multiparams, **params)
            result = self.engine.execute(str(statement.compile(compile_kwargs={"literal_binds": True})))
            # SELECT
            if result.returns_rows:
                rows = result.fetchall()
                return [dict(row) for row in rows]
            # INSERT
            elif result.lastrowid is not None:
                return result.lastrowid
            # DELETE, UPDATE
            else:
                return result.rowcount
        except sqlalchemy.exc.IntegrityError:
            return None
        except Exception as e:
            raise RuntimeError(e)



