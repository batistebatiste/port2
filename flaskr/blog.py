from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from werkzeug.exceptions import abort
from flaskr.api_functions import api_key, get_quote_endpoint
from flaskr.auth import login_required
from flaskr.db import get_db
import requests 
import json 

bp = Blueprint("blog", __name__)

# variables and function to get market data from Alpha Vantage
api_key = 'N9C5WX01O3I1D7F5'
def get_quote_endpoint(symbol): 
    key=api_key
    function='GLOBAL_QUOTE'
    datatype='json' 
    symbol=symbol
    url='https://www.alphavantage.co/query?function={}&symbol={}&datatype={}&apikey={}'.format(function, symbol, datatype, key)
    response = requests.get(url).json()
    # parse the response from API
    symbol = response['Global Quote']['01. symbol']
    price = response['Global Quote']['05. price']
    latest_trading_day = response['Global Quote']['07. latest trading day']
    change_percent = response['Global Quote']['10. change percent']
    return symbol, price, latest_trading_day, change_percent



@bp.route("/")
@login_required
def index():
    """Show all the posts, most recent first."""
    db = get_db()
    positions = db.execute(
        "SELECT p.id, p.symbol, p.shares, p.eur_amount, p.date_position, p.author_id, u.username, p.created, gq.symbol, gq.price, gq.latest_trading_day, gq.one_day_change_percent"
        " FROM positions p JOIN user u ON p.author_id = u.id LEFT JOIN global_quote gq ON p.symbol = gq.symbol"
        " WHERE u.id = ?"
        " ORDER BY date_position DESC", (g.user["id"],)
    ).fetchall()

    return render_template("blog/index.html", positions=positions)


def get_position(id, check_author=True):
    """Get a position and its author by id.

    Checks that the id exists and optionally that the current user is
    the author of the position.

    :param id: id of position to get
    :param check_author: require the current user to be the author
    :return: the position with author information
    :raise 404: if a position with the given id doesn't exist
    :raise 403: if the current user isn't the owner of the position
    """
    db = get_db()
    pos = db.execute(
            "SELECT p.id, p.shares, p.author_id, p.created, u.username, p.symbol, p.eur_amount, p.date_position"
            " FROM positions p JOIN user u ON p.author_id = u.id"
            " WHERE p.id = ?",
            (id,),
        ).fetchone()
    
    if pos is None:
        abort(404, "Position id {0} doesn't exist.".format(id))

    if check_author and pos["author_id"] != g.user["id"]:
        abort(403)

    return pos


@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    """Create a new position for the current user."""
    if request.method == "POST":
        symbol = request.form["symbol"]
        nb_shares = request.form["nb_shares"]
        eur_amount = request.form["eur_amount"]
        date_position = request.form["date"]
        error = None

        if not symbol:
            error = "Title is required."
        if not nb_shares:
            error = "Number of shares is required."
        if not date_position:
            error = "Date of opening the position is required."   

        if error is not None:
            flash(error)
        else:
            # insert the new added position into db
            db = get_db()
            db.execute(
                "INSERT INTO positions (symbol, shares, eur_amount, date_position, author_id) VALUES (?, ?, ?, ?, ?)",
                (symbol, nb_shares, eur_amount, date_position, g.user["id"]),
            )
            db.commit()

            # get the latest global quote for this symbol
            # further work: put this at the "/" or schedule it every hour, or something else
            ticker, price, latest_trading_day, change_percent = get_quote_endpoint(symbol=symbol)
            db.execute(
                "INSERT INTO global_quote (symbol, price, latest_trading_day, one_day_change_percent) VALUES (?,?,?,?)",
                (ticker, price, latest_trading_day, change_percent),
                )
            db.commit()

            return redirect(url_for("blog.index"))

    return render_template("blog/create.html")


@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
def update(id):
    """Update a post if the current user is the author."""
    position = get_position(id)

    if request.method == "POST":
        symbol = request.form["symbol"]
        nb_shares = request.form["nb_shares"]
        eur_amount = request.form["eur_amount"]
        date_position = request.form["date"]
        error = None

        if not symbol:
            error = "Title is required."
        if not eur_amount:
            error = "Eur amount is required."
        if not date_position:
            error = "Date of opening the position is required." 

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "UPDATE positions SET symbol = ?, shares = ?, eur_amount = ?, date_position = ?  WHERE id = ?", (symbol, shares, eur_amount, date_position, id)
            )
            db.commit()
            return redirect(url_for("blog.index"))

    return render_template("blog/update.html", position=position)


@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
def delete(id):
    """Delete a post.

    Ensures that the post exists and that the logged in user is the
    author of the post.
    """
    get_position(id)
    db = get_db()
    db.execute("DELETE FROM positions WHERE id = ?", (id,))
    db.commit()
    return redirect(url_for("blog.index"))
