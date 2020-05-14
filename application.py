import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    rows = db.execute("SELECT name, symbol, SUM(shares) FROM orders WHERE user_id = :user_id GROUP BY symbol", user_id=session["user_id"])
    cash = usd(db.execute("SELECT cash FROM users WHERE id = :user_id", user_id=session["user_id"])[0]['cash'])

    sumtotal = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id=session["user_id"])[0]['cash']

    for row in rows:
        row['price'] = lookup(row['symbol'])['price']
        row['total'] = float(row['price']) * float(row['SUM(shares)'])
        sumtotal += row['total']

    sumtotal = usd(sumtotal)

    return render_template("index.html", rows=rows, cash=cash, sumtotal=sumtotal)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "GET":
        return render_template("buy.html")

    else:
        if not request.form.get("symbol"):
            return apology("must provide symbol", 403)

        elif not request.form.get("shares"):
            return apology("must buy some shares", 403)

        # Access the data with lookup function
        data = lookup(request.form.get("symbol"))

        if data == None:
            return apology("symbol not found", 403)

        # Store data from Form request in variables
        symbol = data["symbol"]
        name = data["name"]
        price = data["price"]
        shares = request.form.get("shares")
        total = price * float(shares)

        cash = float(db.execute("SELECT cash FROM users WHERE (id = :user_id)", user_id=session["user_id"])[0]['cash'])

        if cash < total:
            return apology("Can't afford", 403)

        order = db.execute("INSERT INTO orders (user_id, name, symbol, price, shares, total, timestamp) VALUES (:user_id, :name, :symbol, :price, :shares, :total, CURRENT_TIMESTAMP)", user_id=session["user_id"], name=name, symbol=symbol, price=price, shares=shares, total=total)

        new_cash = float(cash) - float(total)

        cash_update = db.execute("UPDATE users SET cash = :new_cash WHERE id = :id", new_cash=new_cash, id=session["user_id"])

        return redirect("/")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    rows = db.execute("SELECT symbol, shares, price, timestamp FROM orders WHERE user_id = :user_id", user_id=session["user_id"])
    return render_template("history.html", rows=rows)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    # User reached route via GET
    if request.method == "GET":
        return render_template("quote.html")

    else:
        if not request.form.get("symbol"):
            return apology("must provide symbol", 403)

        else:

            # Access the data with lookup function
            data = lookup(request.form.get("symbol"))

            if data == None:
                return apology("symbol not found", 403)

            else:
                # Convert price to USD with usd function
                price = usd(data["price"])

                # Return to quoted.html page with pushed data
                return render_template("quoted.html", data=data, price=price)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Ensure username was submitted
        if not username:
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not password:
            return apology("must provide password", 403)

        # Ensure password-confirmation was submitted
        elif not confirmation:
            return apology("must provide password", 403)

        # Ensure passwords & password check are the same
        elif not password == confirmation:
            return apology("the passwords must be identical", 403)

        # Ensure username is not yet in database
        namecheck = db.execute("SELECT * FROM users WHERE username = :username",
                          username=username)

        if len(namecheck) == 1:
            return apology(" username already exists", 403)

        #hash the password
        hash = generate_password_hash(password)

        # Insert user into database
        rows = db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)", username=username, hash=hash)

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")



@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    # Query all symbols in wallet
    rows = db.execute("SELECT symbol, SUM(shares) FROM orders WHERE user_id = :user_id GROUP BY symbol", user_id=session["user_id"])

    if request.method == "GET":
        return render_template("sell.html", rows=rows)

    else:
        req_symbol = request.form.get("symbol")
        req_shares = int(request.form.get("shares"))

        if not req_symbol:
            return apology("must provide symbol", 403)

        elif not req_shares:
            return apology("must buy some shares", 403)

        own_shares = db.execute("SELECT SUM(shares) FROM orders WHERE symbol = :symbol", symbol=req_symbol)[0]['SUM(shares)']

        if req_shares > own_shares:
            return apology("Not enough shares", 403)

        # Access the data with lookup function
        data = lookup(request.form.get("symbol"))

        if data == None:
            return apology("symbol not found", 403)

        # Store data from Form request in variables
        symbol = data["symbol"]
        name = data["name"]
        price = data["price"]
        total = price * float(req_shares)

        cash = float(db.execute("SELECT cash FROM users WHERE (id = :user_id)", user_id=session["user_id"])[0]['cash'])

        sell = db.execute("INSERT INTO orders (user_id, name, symbol, price, shares, total, timestamp) VALUES (:user_id, :name, :symbol, :price, :shares, :total, CURRENT_TIMESTAMP)", user_id=session["user_id"], name=name, symbol=symbol, price=price, shares=req_shares*(-1), total=total)

        new_cash = float(cash) + float(total)

        cash_update = db.execute("UPDATE users SET cash = :new_cash WHERE id = :id", new_cash=new_cash, id=session["user_id"])

        return redirect("/")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
