from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from werkzeug.exceptions import abort
import requests

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint("blog", __name__)


@bp.route("/")
@login_required
def index():
    """Show all the posts, most recent first."""
    db = get_db()
    positions = db.execute(
        "SELECT p.id, p.symbol, p.eur_amount, p.date_position, p.author_id, u.username, p.created"
        " FROM positions p JOIN user u ON p.author_id = u.id"
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
            "SELECT p.id, p.author_id, p.created, u.username, p.symbol, p.eur_amount, p.date_position"
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
    """Create a new post for the current user."""
    if request.method == "POST":
        symbol = request.form["symbol"]
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
                "INSERT INTO positions (symbol, eur_amount, date_position, author_id) VALUES (?, ?, ?, ?)",
                (symbol, eur_amount, date_position, g.user["id"]),
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
                "UPDATE positions SET symbol = ?, eur_amount = ?, date_position = ?  WHERE id = ?", (symbol, eur_amount, date_position, id)
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
