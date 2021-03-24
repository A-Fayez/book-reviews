import os
import requests

from flask import Flask, session, render_template, request, redirect, url_for, jsonify
from flask_session import Session

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from functools import wraps
from hashlib import md5


app = Flask(__name__)
# Check for environment variable
if not os.getenv("GOODREADS_API_KEY"):
    raise RuntimeError("GOODREADS_API_KEY is not set")

GOODREADS_API_KEY = os.getenv("GOODREADS_API_KEY")

if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up databasee
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("username"):
            return redirect(url_for("index"))
        return f(*args, **kwargs)

    return decorated_function


@app.route("/")
@app.route("/login", strict_slashes=False)
def index():
    return render_template("index.html")


@app.route("/register", strict_slashes=False)
def register():
    return render_template("register.html")


@app.route(
    "/register/sign-up", methods=["POST"], strict_slashes=False
)  # when to route after signing up?
def sign_up():
    """ Signs the user up """
    # get user info from form
    name = request.form.get("name")
    username = request.form.get("username")
    password = request.form.get("password")

    password = md5(password.encode("utf-8")).hexdigest()

    if name is None or username is None:
        return render_template(
            "error.html", message="You can't leave username or name empty!"
        )

    # check if there exists a user with the same registered username
    if (
        db.execute(
            "SELECT * FROM users WHERE username = :username", {"username": username}
        ).rowcount
        != 0
    ):
        return render_template("error.html", message="This username already exists!")

    db.execute(
        "INSERT INTO users (username, name, password) \
            VALUES(:username, :name, :password)",
        {"username": username, "name": name, "password": password},
    )

    db.commit()
    return render_template("success.html", type="REGISTER")


@app.route("/login", methods=["POST"], strict_slashes=False)
def login():
    """ Authenticate the user """
    # remember to edit when adding hashing to passwords
    username = request.form.get("username")
    password = request.form.get("password")

    hashed_key = md5(password.encode("utf-8")).hexdigest()

    user = db.execute(
        "SELECT * FROM users WHERE username=:username AND password=:password",
        {"username": username, "password": hashed_key},
    ).fetchone()

    if user is None:
        return render_template("error.html", message="Wrong username or password")

    session["user_id"] = user.user_id
    session["username"] = user.username

    return redirect(url_for("search_view"))


@app.route("/search", strict_slashes=False)
@login_required
def search_view():
    return render_template("search.html", username=session.get("username"))


@app.route("/search/books", methods=["POST"], strict_slashes=False)
@login_required
def books():
    """ Make a query to search for user's keywords """
    isbn = request.form.get("isbn") or None
    title = request.form.get("title") or None
    author = request.form.get("author") or None

    if isbn is not None:
        isbn = "%" + isbn + "%"
    if title is not None:
        title = "%" + title + "%"
    if author is not None:
        author = "%" + author + "%"

    books = db.execute(
        "SELECT * FROM books WHERE isbn ILIKE :isbn OR title ILIKE :title \
                OR author ILIKE :author",
        {"isbn": isbn, "title": title, "author": author},
    ).fetchall()

    if len(books) == 0:
        return render_template(
            "search.html", username=session.get("username"), results=""
        )

    return render_template("books.html", books=books)


@app.route("/search/books/<isbn>", strict_slashes=False)
@login_required
def book(isbn):

    book = db.execute(
        "SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}
    ).fetchone()

    # This case will invoke if user typed in a wrong isbn manually in URL
    if book is None:
        return render_template(
            "search.html", username=session.get("username"), results=""
        )
    res = requests.get(
        "https://www.goodreads.com/book/review_counts.json",
        params={"Key": f"{GOODREADS_API_KEY}", "isbns": isbn},
    )

    # goodreads stats
    avg_rating = res.json()["books"][0].get("average_rating")
    ratings_count = res.json()["books"][0].get("work_ratings_count")

    # show the user submitted review if available

    review = db.execute(
        "SELECT * FROM reviews WHERE user_id=:user_id AND isbn=:isbn",
        {"user_id": session.get("user_id"), "isbn": isbn},
    ).fetchone()

    if review is not None:
        return render_template(
            "book.html",
            book=book,
            avg_rating=avg_rating,
            ratings_count=ratings_count,
            reviewed="True",
            rate=review.rating,
            opinion=review.opinion,
        )

    return render_template(
        "book.html", book=book, avg_rating=avg_rating, ratings_count=ratings_count
    )


@app.route("/search/books/<isbn>/review", methods=["POST"], strict_slashes=False)
@login_required
def book_review(isbn):

    rating = int(request.form.get("rating"))
    opinion = request.form.get("opinion")

    if (
        db.execute(
            "SELECT * FROM reviews WHERE user_id=:user_id AND isbn=:isbn",
            {"user_id": session.get("user_id"), "isbn": isbn},
        ).rowcount
        != 0
    ):

        return render_template("error.html", type="REVIEW")

    db.execute(
        "INSERT INTO reviews(user_id, isbn, rating, opinion) VALUES (:user_id, \
                :isbn, :rating, :opinion)",
        {
            "user_id": session.get("user_id"),
            "isbn": isbn,
            "rating": rating,
            "opinion": opinion,
        },
    )

    db.commit()

    return render_template("success.html", type="REVIEW")


@app.route("/api/<isbn>", strict_slashes=False)
def book_api(isbn):

    book = db.execute("SELECT * FROM books WHERE isbn=:isbn", {"isbn": isbn}).fetchone()
    if book is None:
        return jsonify({"error": "No book found"})

    row_proxy = db.execute(
        "SELECT COUNT(*), AVG(rating) FROM reviews WHERE reviews.isbn=:isbn",
        {"isbn": isbn},
    ).fetchone()

    return jsonify(
        {
            "title": book.title,
            "author": book.author,
            "year": book.year,
            "isbn": book.isbn,
            "review_count": row_proxy.count,
            "average_score": row_proxy.avg,
        }
    )


@app.route("/logout")
def log_out():
    try:
        session.pop("username")
    except KeyError:
        print("No user session")

    return redirect(url_for("index"))


def avg_rating(isbn):
    """Returns the average rating of a book submitted by our own users
    not by goodreads"""

    average_rating = db.execute(
        "SELECT AVG(rating) FROM reviews WHERE reviews.isbn=:isbn", {"isbn": isbn}
    ).fetchone()

    assert average_rating <= 5

    return average_rating
