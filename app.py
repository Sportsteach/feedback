"""Example flask app that stores passwords hashed with Bcrypt. Yay!"""

from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User, Feedback
from forms import RegisterForm, LoginForm, FeedbackForm

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgres:///feedback"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "abc123"
app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = False

connect_db(app)
db.create_all()

toolbar = DebugToolbarExtension(app)


@app.route("/")
def homepage():
    """Show homepage with links to site areas."""

    return redirect("/register")


@app.route("/users/<username>")
def userhome(username):
    """If logged in takes user to user home"""

    if "username" in session:
        the_user = User.query.get_or_404(username)
        return render_template("users.html/", the_user=the_user)
    else:
        return redirect("/login")


@app.route("/users/<username>/feedback", methods=["GET", "POST"])
def new_feedback(username):
    """User to add feedback"""
    if "username" in session:
        form = FeedbackForm()

    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data

        feed = Feedback(title=title, content=content, username=username)
        db.session.add(feed)
        db.session.commit()

        return redirect(f"/users/{feed.username}")

    else:
        return render_template("feedback.html", form=form)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user: produce form & handle form submission."""

    form = RegisterForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data

        user = User.register(username, password, email, first_name, last_name)
        db.session.add(user)
        db.session.commit()

        session["username"] = user.username

        # on successful login, redirect to secret page
        return redirect(f"/users/{user.username}")

    else:
        return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Produce login form or handle login."""

    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        pwd = form.password.data

        user = User.authenticate(username, pwd)

        if user:
            session["username"] = user.username
            return redirect(f"/users/{user.username}")

        else:
            form.username.errors = ["Bad name/password"]

    return render_template("login.html", form=form)


@app.route("/users/<username>")
def secret(username):
    """Example hidden page for logged-in users only."""

    if "username" not in session:
        flash("You must be logged in to view!")
        return redirect("/register")

    else:
        the_user = User.query.get_or_404(username)
        return render_template("details.html", the_user=the_user)


@app.route("/logout")
def logout():
    """Logs user out and redirects to login."""

    session.pop("username")

    return redirect("/login")


@app.route('/feedback/<int:feedback_id>', methods=["GET", "POST"])
def update_feedback(feedback_id):
    """Edit/update feedback."""
    if "username" not in session:
        flash("You must be logged in to view!")
        return redirect("/login")

    feedback = Feedback.query.get(feedback_id)

    form = FeedbackForm(obj=feedback)

    if form.validate_on_submit():
        feedback.title = form.title.data
        feedback.content = form.content.data

        db.session.commit()

        return redirect(f"/users/{feedback.username}")

    return render_template("/edit.html", form=form, feedback=feedback)


@app.route('/delete/<int:feedback_id>', methods=["GET", "POST"])
def delete_feedback(feedback_id):
    """Delete feedback from database"""
    if "username" not in session:
        flash("You must be logged in to view!")
        return redirect("/login")

    feedback = Feedback.query.get(feedback_id)
    db.session.delete(feedback)
    db.session.commit()
    return redirect(f"/users/{feedback.username}")
